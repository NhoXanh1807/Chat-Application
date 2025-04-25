import json
import socket
from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Load database từ file JSON export
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

    # Đồng bộ pending tin nhắn vào log
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
    return jsonify({"message": "Đã ghi log cục bộ (offline)", "data": msg_data}), 200

@app.route('/update_message', methods=['POST'])
def update_message():
    global latest_message
    latest_message = request.json.get("message")
    return jsonify({"message": "Updated"})

@app.route('/get_message', methods=['GET'])
def get_message():
    return jsonify({"message": latest_message or "Không có tin nhắn mới"})

def log_message(message_dict, offline=True):
    channel = message_dict.get("channel", "general")
    os.makedirs("logs", exist_ok=True)
    flag = " (offline)" if offline else ""
    with open(f"logs/log_{channel}.txt", "a", encoding="utf-8") as f:
        ts = message_dict.get("timestamp")
        sender = message_dict.get("sender")
        content = message_dict.get("content")
        f.write(f"[{ts}] {sender}{flag}: {content}\n")


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000)