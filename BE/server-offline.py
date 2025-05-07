# ✅ ĐÃ CẬP NHẬT server-offline.py để ghi log giống client.py và đồng bộ tin nhắn vào database_backup.json
import json
import socket
from flask import Flask, request, jsonify
from datetime import datetime
import os
import re
from flask_cors import CORS
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--service-port', type=int, required=True, help='Port to run the offline server')
args = parser.parse_args()

app = Flask(__name__)
CORS(app, origins="*")

with open("database_backup.json", "r", encoding="utf-8") as f:
    db_data = json.load(f)

latest_message = None

@app.route('/auth', methods=['POST'])
def auth_offline():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    account = db_data.get("accounts", {}).get(username)
    if not account:
        return jsonify({"error": "Tài khoản không tồn tại"}), 404
    if account.get("password") != password:
        return jsonify({"error": "Sai mật khẩu"}), 401

    pending = db_data.get("pending_messages", {}).get(username, {})
    for _, msg in pending.items():
        log_message(msg)

    return jsonify({
        "message": "Đăng nhập offline thành công",
        "username": username,
        "channels_hosted": [ch for ch, info in db_data.get("channels", {}).items() if info.get("host") == username],
        "channels_joined": [ch for ch, info in db_data.get("channels", {}).items() if username in info.get("joined_users", [])],
        "is_host": any(info.get("host") == username for info in db_data.get("channels", {}).values())
    }), 200

@app.route('/send_to_channel', methods=['POST'])
def send_offline():
    data = request.json
    channel = data.get("channel")
    sender = data.get("sender")
    content = data.get("content")
    timestamp = datetime.utcnow().isoformat()

    msg_data = {
        "channel": channel,
        "sender": sender,
        "content": content,
        "timestamp": timestamp
    }

    log_message(msg_data)
    # Lưu tin nhắn vào database_backup.json
    if "messages" not in db_data:
        db_data["messages"] = {}
    if channel not in db_data["messages"]:
        db_data["messages"][channel] = []
    db_data["messages"][channel].append(msg_data)

    with open("database_backup.json", "w", encoding="utf-8") as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

    return jsonify({"message": "Đã ghi log cục bộ (offline)", "data": msg_data}), 200

@app.route('/update_message', methods=['POST'])
def update_message():
    global latest_message
    latest_message = request.json.get("message")
    return jsonify({"message": "Updated"})

@app.route('/get_message', methods=['GET'])
def get_message():
    return jsonify({"message": latest_message or "Không có tin nhắn mới"})

@app.route('/channels', methods=['GET'])
def get_channels_offline():
    channels_data = db_data.get("channels", {})
    channel_list = []
    for name, info in channels_data.items():
        joined_users = info.get("joined_users", [])
        channel_list.append({
            "name": name,
            "host": info.get("host", "Không rõ"),
            "online_users": [],
            "offline_users": joined_users
        })
    return jsonify({"channels": channel_list}), 200

@app.route('/get_all_messages', methods=['GET'])
def get_all_messages_offline():
    channel = request.args.get("channel")
    if not channel:
        return jsonify({"error": "Thiếu channel"}), 400

    messages = []

    # 1. Lấy từ database_backup.json
    try:
        with open("database_backup.json", "r", encoding="utf-8") as f:
            db_data = json.load(f)
        msg_dict = db_data.get("messages", {}).get(channel, {})
        for msg in msg_dict.values():
            messages.append(msg)
    except Exception as e:
        print(f"[ERR] Không thể đọc database_backup.json: {e}")

    # 2. Lấy từ file log nếu có
    log_path = f"log_{channel}.txt"
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    match = re.match(r"\[(.*?)\] (.*?): (.*)", line)
                    if match:
                        ts, sender, content = match.groups()
                        if not any(m.get("timestamp") == ts and m.get("sender") == sender and m.get("content") == content.strip() for m in messages):
                            messages.append({
                                "sender": sender.replace(" (offline)", ""),
                                "content": content.strip(),
                                "timestamp": ts
                            })
        except Exception as e:
            print(f"[ERR] Không thể đọc log file {log_path}: {e}")

    # Sắp xếp theo thời gian
    messages.sort(key=lambda x: x.get("timestamp", ""))

    return jsonify({"messages": messages}), 200

@app.route('/get_join_users', methods=['GET'])
def get_join_users_offline():
    channel = request.args.get("channel")
    if not channel:
        return jsonify({"error": "Thiếu tên channel"}), 400

    channel_info = db_data.get("channels", {}).get(channel)
    if not channel_info:
        return jsonify({"error": "Channel không tồn tại"}), 404

    joined_users = channel_info.get("joined_users", [])
    return jsonify({"joined_users": joined_users}), 200

@app.route('/get_all_accounts', methods=['GET'])
def get_all_accounts_offline():
    accounts = db_data.get("accounts", {})
    return jsonify({"usernames": list(accounts.keys())}), 200

def log_message(message_dict, offline=True):
    channel = message_dict.get("channel", "general")
    flag = " (offline)" if offline else ""
    with open(f"log_{channel}.txt", "a", encoding="utf-8") as f:
        ts = message_dict.get("timestamp")
        sender = message_dict.get("sender")
        content = message_dict.get("content")
        f.write(f"[{ts}] {sender}{flag}: {content}\n")

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=args.service_port)
