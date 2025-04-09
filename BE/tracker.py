import socket
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db

# Khởi tạo Flask server
app = Flask(__name__)

# Kết nối Firebase
cred = credentials.Certificate("C:/Users/nguye/Downloads/chat-application--assign-1-firebase-adminsdk-fbsvc-c2e8ce253b.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://chat-application--assign-1-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

# 📌 1️⃣ Đăng ký peer mới
@app.route('/submit_info', methods=['POST'])
def submit_info():
    data = request.json
    ip = data.get("ip")
    port = data.get("port")

    if not ip or not port:
        return jsonify({"error": "Thiếu thông tin IP hoặc Port"}), 400

    peer_key = f"{ip.replace('.', '-')}_{port}"
    
    ref = db.reference("peers")
    ref.child(peer_key).set({
        "ip": ip,
        "port": port
    })
    
    return jsonify({"message": "Peer đã đăng ký thành công"}), 200


# 📌 2️⃣ Tracker thêm peer vào danh sách theo yêu cầu
@app.route('/add_list', methods=['POST'])
def add_list():
    data = request.json
    ip = data.get("ip")
    port = data.get("port")

    if not ip or not port:
        return jsonify({"error": "Thiếu IP hoặc port"}), 400

    peer_key = f"{ip.replace('.', '-')}_{port}"
    ref = db.reference("peers")
    ref.child(peer_key).set({
        "ip": ip,
        "port": port
    })

    return jsonify({"message": "Peer đã được thêm vào danh sách"}), 200

# 📌 3️⃣ Lấy danh sách peer online
@app.route('/get_list', methods=['GET'])
def get_list():
    ref = db.reference("peers")
    peers = ref.get()

    if not peers:
        return jsonify([])

    return jsonify(list(peers.values()))


# 📌 5️⃣ Kết nối giữa các peers (Peer-to-Peer)
@app.route('/peer_connect', methods=['POST'])
def peer_connect():
    data = request.json
    my_ip = data.get("ip")
    my_port = data.get("port")

    if not my_ip or not my_port:
        return jsonify({"error": "Thiếu thông tin IP hoặc Port"}), 400

    ref = db.reference("peers")
    peers = ref.get()

    if not peers:
        return jsonify({"error": "Không có peer nào khác"}), 400

    peer_list = list(peers.values())

    # Tìm peer để kết nối (bỏ qua chính nó)
    available_peers = [p for p in peer_list if p["ip"] != my_ip or p["port"] != my_port]

    if not available_peers:
        return jsonify({"error": "Không tìm thấy peer nào để kết nối"}), 400

    return jsonify({"connect_to": available_peers}), 200

 
# Chạy server Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
