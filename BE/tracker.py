# tracker.py
import socket
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

cred = credentials.Certificate("C:/Users/nguye/Downloads/chat-application--assign-1-firebase-adminsdk-fbsvc-c2e8ce253b.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://chat-application--assign-1-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

# Dọn sạch peers khi tracker khởi động lại
for path in ["peers", "peers_visitor_online", "peers_auth_online"]:
    db.reference(path).delete()

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
    return jsonify({"message": "Peer đã đăng ký visitor"}), 200

@app.route('/get_list', methods=['GET'])
def get_list():
    peers = db.reference("peers").get()
    return jsonify(list(peers.values()) if peers else [])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)