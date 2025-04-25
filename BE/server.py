# server.py
import socket
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import requests
from flask_cors import CORS
import json
import os
app = Flask(__name__)

TRACKER_URL = 'http://208.100.26.100:5000'
MY_TCP_PORT = 6000

if not firebase_admin._apps:
    cred = credentials.Certificate("chat-application--assign-1-firebase-adminsdk-fbsvc-c2e8ce253b.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://chat-application--assign-1-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })

latest_message = None
CORS(app, origins="*")  # Chấp nhận từ tất cả các domain/IP
@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Thiếu username hoặc password"}), 400

    # Kiểm tra nếu đã đăng nhập ở nơi khác
    auth_peers = db.reference("peers_auth_online").get() or {}
    if username in auth_peers:
        existing = auth_peers[username]
        if existing["ip"] != my_ip or int(existing["port"]) != MY_TCP_PORT:
            return jsonify({"error": "Tài khoản đã đăng nhập ở máy khác"}), 403


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

    # Xóa khỏi danh sách visitor nếu có
    visitor_ref = db.reference("peers_visitor_online")
    for key, value in (visitor_ref.get() or {}).items():
        if value.get("ip") == my_ip and int(value.get("port")) == MY_TCP_PORT:
            visitor_ref.child(key).delete()
            break

    # Lấy thông tin channel
    channel_ref = db.reference("channels")
    channels_data = channel_ref.get() or {}

    channels_hosted = []
    channels_joined = []

    for channel_name, info in channels_data.items():
        joined_users = info.get("joined_users", info.get("join_users", []))
        if info.get("host") == username:
            channels_hosted.append(channel_name)
        elif username in joined_users:
            channels_joined.append(channel_name)

    # Thông báo cho các user khác trong channel host
    for channel in channels_hosted:
        joined_users = channels_data[channel].get("joined_users", [])
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
                    requests.post(f"{TRACKER_URL}/peer_connect", json={
                        "source": my_ip,
                        "dest": peer_info["ip"]
                    })
                except:
                    pass

    # Đồng bộ pending_messages vào log local
    pending_ref = db.reference(f"pending_messages/{username}")
    pending_msgs = pending_ref.get() or {}
    for _, msg_data in pending_msgs.items():
        log_message(msg_data)
    pending_ref.delete()

        # --- Đồng bộ lại các log offline sau khi online ---
    import glob
    log_dir = "logs"
    pattern = re.compile(r"^\[(.*?)\] (.*?) \(offline\): (.*)$")

    if os.path.isdir(log_dir):
        for log_file in glob.glob(os.path.join(log_dir, "log_*.txt")):
            channel = log_file.split("_")[-1].replace(".txt", "")
            lines = []
            new_lines = []
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                match = pattern.match(line)
                if match:
                    ts, sender_log, content = match.groups()
                    msg_data = {
                        "channel": channel,
                        "sender": sender_log,
                        "content": content.strip(),
                        "timestamp": ts
                    }
                    db.reference(f"messages/{channel}").push(msg_data)
                    log_message(msg_data, offline=False)
                else:
                    new_lines.append(line)

            with open(log_file, "w", encoding="utf-8") as f:
                for line in new_lines:
                    f.write(line)

    
    return jsonify({
        "message": "Đăng nhập thành công",
        "username": username,
        "channels_hosted": channels_hosted,
        "channels_joined": channels_joined,
        "is_host": len(channels_hosted) > 0
    }), 200

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

    host_username = channel_info.get("host")
    is_sender_host = sender == host_username
    my_ip = get_my_ip()

    if is_sender_host:
        # HOST gửi trực tiếp tới joined_users
        for user in joined_users:
            if user == sender:
                continue
            peer = auth_peers.get(user)
            if peer:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((peer["ip"], int(peer["port"])))
                        s.sendall(str(msg_data).encode())
                    requests.post(f"{TRACKER_URL}/peer_connect", json={
                        "source": my_ip,
                        "dest": peer["ip"]
                    })
                except:
                    pass
            else:
                db.reference(f"pending_messages/{user}").push(msg_data)

        log_message(msg_data)
        db.reference(f"messages/{channel}").push(msg_data)

    else:
        # JOINED_USER gửi cho host
        host_peer = auth_peers.get(host_username)
        if host_peer:
            try:
                # Gửi TCP đến host
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host_peer["ip"], int(host_peer["port"])))
                    s.sendall(str(msg_data).encode())
                requests.post(f"{TRACKER_URL}/peer_connect", json={
                    "source": my_ip,
                    "dest": host_peer["ip"]
                })

                # Sau đó HOST relay lại tới các joined_users khác
                for user in joined_users:
                    if user in (sender, host_username):
                        continue
                    peer = auth_peers.get(user)
                    if peer:
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.connect((peer["ip"], int(peer["port"])))
                                s.sendall(str(msg_data).encode())
                            requests.post(f"{TRACKER_URL}/peer_connect", json={
                                "source": host_peer["ip"],  # ✅ CHỈNH CHUẨN Ở ĐÂY
                                "dest": peer["ip"]
                            })
                        except:
                            pass
                    else:
                        db.reference(f"pending_messages/{user}").push(msg_data)

                log_message(msg_data)
                db.reference(f"messages/{channel}").push(msg_data)

            except:
                log_message(msg_data)
                db.reference(f"messages/{channel}").push(msg_data)
        else:
            # Host offline: tự log và lưu luôn
            log_message(msg_data)
            db.reference(f"messages/{channel}").push(msg_data)

    return jsonify({"message": "Đã gửi thành công", "data": msg_data}), 200



def log_message(message_dict):
    channel = message_dict.get("channel", "general")
    with open(f"log_{channel}.txt", "a", encoding="utf-8") as f:
        ts = message_dict.get("timestamp")
        sender = message_dict.get("sender")
        content = message_dict.get("content")
        f.write(f"[{ts}] {sender}: {content}\n")

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
@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.json
    channel = data.get("channel")
    username = data.get("username")
    adder = data.get("adder")  # Người thêm
    
    if not channel or not username or not adder:
        return jsonify({"error": "Thiếu thông tin"}), 400
    
    channel_ref = db.reference(f"channels/{channel}")
    channel_info = channel_ref.get()
    
    if not channel_info:
        return jsonify({"error": "Channel không tồn tại"}), 404
    
    if channel_info.get("host") != adder:
        return jsonify({"error": "Chỉ host mới có quyền thêm thành viên"}), 403
    
    joined_users = channel_info.get("joined_users", [])
    if username not in joined_users:
        joined_users.append(username)
        channel_ref.update({"joined_users": joined_users})
    
    return jsonify({"message": "Đã thêm thành viên", "channel": channel, "user": username}), 200

@app.route('/remove_member', methods=['POST'])
def remove_member():
    data = request.json
    channel = data.get("channel")
    username = data.get("username")
    remover = data.get("remover")  # Người xóa
    
    if not channel or not username or not remover:
        return jsonify({"error": "Thiếu thông tin"}), 400
    
    channel_ref = db.reference(f"channels/{channel}")
    channel_info = channel_ref.get()
    
    if not channel_info:
        return jsonify({"error": "Channel không tồn tại"}), 404
    
    if channel_info.get("host") != remover:
        return jsonify({"error": "Chỉ host mới có quyền xóa thành viên"}), 403
    
    joined_users = channel_info.get("joined_users", [])
    if username in joined_users:
        joined_users.remove(username)
        channel_ref.update({"joined_users": joined_users})
    
    return jsonify({"message": "Đã xóa thành viên", "channel": channel, "user": username}), 200


@app.route('/get_all_messages', methods=['GET'])
def get_all_messages():
    channel = request.args.get("channel")
    if not channel:
        return jsonify({"error": "Thiếu channel"}), 400
    
    # Kiểm tra channel tồn tại
    channel_ref = db.reference(f"channels/{channel}")
    if not channel_ref.get():
        return jsonify({"error": "Channel không tồn tại"}), 404
    
    # Lấy tất cả tin nhắn và sắp xếp theo timestamp
    messages_ref = db.reference(f"messages/{channel}")
    messages = messages_ref.get() or {}
    
    # Chuyển thành list và sắp xếp
    messages_list = []
    for msg_id, msg_data in messages.items():
        messages_list.append(msg_data)
    
    messages_list.sort(key=lambda x: x.get("timestamp", ""))
    
    return jsonify({"messages": messages_list}), 200

@app.route('/get_pending_messages', methods=['GET'])
def get_pending_messages():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Thiếu username"}), 400
    
    pending_ref = db.reference(f"pending_messages/{username}")
    pending_msgs = pending_ref.get() or {}
    
    # Lấy và xóa tin nhắn pending
    messages = []
    for msg_id, msg_data in pending_msgs.items():
        messages.append(msg_data)
    
    pending_ref.delete()
    
    # Sắp xếp theo timestamp
    messages.sort(key=lambda x: x.get("timestamp", ""))
    
    return jsonify({"messages": messages}), 200
@app.route('/logout', methods=['POST'])
def logout():
    data = request.json
    username = data.get("username")
    if not username:
        return jsonify({"error": "Thiếu username"}), 400

    my_ip = get_my_ip()

    # Xóa khỏi peers_auth_online
    db.reference("peers_auth_online").child(username).delete()

    # Thêm lại vào peers_visitor_online nếu chưa tồn tại (theo IP và PORT)
    visitor_ref = db.reference("peers_visitor_online")
    already_exists = False
    for key, value in (visitor_ref.get() or {}).items():
        if value.get("ip") == my_ip and int(value.get("port")) == MY_TCP_PORT:
            already_exists = True
            break

    if not already_exists:
        visitor_ref.push({
            "ip": my_ip,
            "port": MY_TCP_PORT
        })

    return jsonify({"message": "Đăng xuất thành công"}), 200
@app.route('/get_all_accounts', methods=['GET'])
def get_all_accounts():
    ref = db.reference("accounts")
    data = ref.get() or {}
    usernames = list(data.keys())
    return jsonify({"usernames": usernames})
@app.route('/get_join_users', methods=['GET'])
def get_join_users():
    channel = request.args.get("channel")
    if not channel:
        return jsonify({"error": "Thiếu tên channel"}), 400

    channel_ref = db.reference(f"channels/{channel}")
    channel_info = channel_ref.get()
    if not channel_info:
        return jsonify({"error": "Channel không tồn tại"}), 404

    joined_users = channel_info.get("joined_users", [])
    return jsonify({"joined_users": joined_users}), 200


@app.route('/export_database', methods=['GET'])
def export_database():
    full_data = db.reference("/").get()
    with open("database_backup.json", "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
        
if __name__ == '__main__':
    try:
        requests.post(f"{TRACKER_URL}/submit_info", json={"ip": get_my_ip(), "port": MY_TCP_PORT})
        app.run(host='0.0.0.0', port=8000)
    except KeyboardInterrupt:
        print("\n🛑 Server dừng, gọi export_database...")
        export_database()
        print("✅ Đã sao lưu vào database_backup.json")
