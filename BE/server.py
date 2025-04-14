# server.py
import socket
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import requests

app = Flask(__name__)

TRACKER_URL = 'http://localhost:5000'
MY_TCP_PORT = 6000

if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/nguye/Downloads/chat-application--assign-1-firebase-adminsdk-fbsvc-c2e8ce253b.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://chat-application--assign-1-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })

latest_message = None

@app.route('/auth', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Thiếu username hoặc password"}), 400

    ref = db.reference(f"accounts/{username}")
    user_data = ref.get()
    if not user_data:
        return jsonify({"error": "Tài khoản không tồn tại"}), 404
    if user_data.get("password") != password:
        return jsonify({"error": "Sai mật khẩu"}), 401

    my_ip = get_my_ip()
    db.reference("peers_auth_online").child(username).set({
        "username": username,
        "ip": my_ip,
        "port": MY_TCP_PORT
    })

    visitor_ref = db.reference("peers_visitor_online")
    for key, value in (visitor_ref.get() or {}).items():
        if value.get("ip") == my_ip and int(value.get("port")) == MY_TCP_PORT:
            visitor_ref.child(key).delete()
            break

    channel_ref = db.reference("channels")
    channels_data = channel_ref.get()
    user_channel = None
    if channels_data:
        for channel_name, info in channels_data.items():
            if info.get("host") == username:
                user_channel = channel_name
                break

    if user_channel:
        joined_users = channels_data[user_channel].get("joined_users", [])
        auth_peers = db.reference("peers_auth_online").get() or {}
        for u in joined_users:
            if u == username:
                continue
            peer_info = auth_peers.get(u)
            if peer_info:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((peer_info["ip"], int(peer_info["port"])))
                        s.sendall(f"[PEER CONNECTED FROM HOST]".encode())
                except: pass

    return jsonify({"message": "Đăng nhập thành công", "username": username, "is_host": user_channel is not None, "channel": user_channel}), 200

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    s.close()
    return ip

@app.route('/update_message', methods=['POST'])
def update_message():
    global latest_message
    latest_message = request.json.get("message")
    return jsonify({"message": "Updated"})

@app.route('/get_message', methods=['GET'])
def get_message():
    return jsonify({"message": latest_message or "Không có tin nhắn mới"})

@app.route('/send_to_channel', methods=['POST'])
def send_to_channel():
    data = request.json
    channel = data.get("channel")
    sender = data.get("sender")
    content = data.get("content")

    if not channel or not sender or not content:
        return jsonify({"error": "Thiếu thông tin"}), 400

    timestamp = datetime.utcnow().isoformat()

    channel_ref = db.reference(f"channels/{channel}")
    channel_info = channel_ref.get()
    if not channel_info:
        return jsonify({"error": "Channel không tồn tại"}), 404

    joined_users = channel_info.get("joined_users", [])
    if sender not in joined_users:
        joined_users.append(sender)
        channel_ref.update({"joined_users": joined_users})

    auth_peers = db.reference("peers_auth_online").get() or {}
    msg_data = {
        "channel": channel,
        "sender": sender,
        "content": content,
        "timestamp": timestamp
    }

    for user in joined_users:
        if user == sender:
            continue
        peer = auth_peers.get(user)
        if peer:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer["ip"], int(peer["port"])))
                    s.sendall(str(msg_data).encode())
            except: pass
        else:
            db.reference(f"pending_messages/{user}").push(msg_data)

    db.reference(f"messages/{channel}").push(msg_data)
    return jsonify({"message": "Đã gửi thành công", "data": msg_data}), 200

@app.route('/channels', methods=['GET'])
def get_channels():
    ref = db.reference("channels")
    channels_data = ref.get() or {}

    auth_peers = db.reference("peers_auth_online").get() or {}
    auth_usernames = set(auth_peers.keys())

    channel_list = []
    for name, info in channels_data.items():
        joined_users = info.get("joined_users", [])
        online_users = [u for u in joined_users if u in auth_usernames]
        offline_users = [u for u in joined_users if u not in auth_usernames]
        channel_list.append({
            "name": name,
            "host": info.get("host", "Không rõ"),
            "online_users": online_users,
            "offline_users": offline_users
        })

    return jsonify({"channels": channel_list}), 200

if __name__ == '__main__':
    requests.post(f"{TRACKER_URL}/submit_info", json={"ip": get_my_ip(), "port": MY_TCP_PORT})
    app.run(host='0.0.0.0', port=8000)