import socket
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
import argparse
from datetime import datetime
import threading
import os
import time

# --- Cấu hình ---
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, required=True, help='Port to run tracker on')
args = parser.parse_args()

app = Flask(__name__)

cred = credentials.Certificate("chat-application--assign-1-firebase-adminsdk-fbsvc-c2e8ce253b.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://chat-application--assign-1-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

for path in ["peers", "peers_visitor_online", "peers_auth_online"]:
    db.reference(path).delete()

# --- Biến log ---
LOG_FILE = "tracker_log.txt"
MAX_LOG_LINES = 10000
peer_last_seen = {}

def write_log(msg: str):
    timestamp = datetime.utcnow().isoformat()
    line = f"[{timestamp}] {msg}"
    print(line)

    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) >= MAX_LOG_LINES:
                with open(LOG_FILE, "w", encoding="utf-8") as f:
                    f.write("")

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[ERROR] Không ghi được log: {e}")

# --- Các endpoint chính ---
@app.route('/submit_info', methods=['POST'])
def submit_info():
    data = request.json
    ip = data.get("ip")
    port = data.get("port")
    if not ip or not port:
        return jsonify({"error": "Thiếu IP hoặc port"}), 400

    key = f"{ip.replace('.', '-')}_{port}"
    db.reference("peers").child(key).set({"ip": ip, "port": port})
    db.reference("peers_visitor_online").child(key).set({"ip": ip, "port": port})
    write_log(f"[REGISTER] {ip}:{port} đã submit thông tin vào tracker.")
    return jsonify({"message": "Peer đã đăng ký visitor"}), 200

@app.route('/peer_connect', methods=['POST'])
def peer_connect():
    data = request.json
    source_ip = data.get("source")
    dest_ip = data.get("dest")

    if not source_ip or not dest_ip:
        return jsonify({"error": "Thiếu thông tin"}), 400

    if source_ip == dest_ip:
        write_log(f"[SELF-CONNECT] Peer tự kết nối: {source_ip}")
        return jsonify({"message": "Peer tự kết nối"}), 200

    write_log(f"[CONNECT] {source_ip} -> {dest_ip}")
    db.reference("peer_connections").push({
        "source": source_ip,
        "dest": dest_ip,
        "timestamp": datetime.utcnow().isoformat()
    })

    return jsonify({"message": "Đã log kết nối thành công"}), 200

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    ip = data.get("ip")
    port = data.get("port")
    key = f"{ip.replace('.', '-')}_{port}"
    peer_last_seen[key] = datetime.utcnow()
    write_log(f"[HEARTBEAT] {ip}:{port} vẫn đang hoạt động.")
    return jsonify({"message": "Heartbeat OK"}), 200

@app.route('/disconnect', methods=['POST'])
def disconnect():
    data = request.json
    ip = data.get("ip")
    port = data.get("port")
    key = f"{ip.replace('.', '-')}_{port}"
    write_log(f"[DISCONNECT] {ip}:{port} đã yêu cầu ngắt kết nối.")

    db.reference("peers").child(key).delete()
    db.reference("peers_visitor_online").child(key).delete()

    auth_online = db.reference("peers_auth_online").get() or {}
    for uname, info in auth_online.items():
        check_key = f"{info['ip'].replace('.', '-')}_{info['port']}"
        if check_key == key:
            db.reference("peers_auth_online").child(uname).delete()
            break

    if key in peer_last_seen:
        del peer_last_seen[key]

    return jsonify({"message": "Đã xoá khỏi hệ thống"}), 200

@app.route('/get_list', methods=['GET'])
def get_list():
    peers = db.reference("peers").get()
    return jsonify(list(peers.values()) if peers else [])

# --- Hàm kiểm tra timeout ---
def monitor_peers():
    while True:
        now = datetime.utcnow()
        to_remove = []
        for key, last_seen in peer_last_seen.items():
            if (now - last_seen).total_seconds() > 30:
                to_remove.append(key)

        for key in to_remove:
            write_log(f"[TIMEOUT] Peer không phản hồi: {key} (xoá khỏi tracker)")
            db.reference("peers").child(key).delete()
            db.reference("peers_visitor_online").child(key).delete()

            auth_online = db.reference("peers_auth_online").get() or {}
            for uname, info in auth_online.items():
                check_key = f"{info['ip'].replace('.', '-')}_{info['port']}"
                if check_key == key:
                    db.reference("peers_auth_online").child(uname).delete()
                    break

            del peer_last_seen[key]

        time.sleep(10)

# --- Khởi động ---
if __name__ == '__main__':
    threading.Thread(target=monitor_peers, daemon=True).start()
    app.run(host='0.0.0.0', port=args.port)
