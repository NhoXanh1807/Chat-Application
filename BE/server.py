# server.py
import socket
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db

import requests

app = Flask(__name__)

# Thông tin cấu hình
TRACKER_URL = 'http://localhost:5000'  # Thay đổi nếu tracker chạy trên máy khác
MY_TCP_PORT = 6000  # Port để client.py lắng nghe TCP
# Kết nối Firebase
cred = credentials.Certificate("C:/Users/nguye/Downloads/chat-application--assign-1-firebase-adminsdk-fbsvc-c2e8ce253b.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://chat-application--assign-1-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

# Biến toàn cục lưu tin nhắn mới nhất
latest_message = None


@app.route('/auth', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Thiếu username hoặc password"}), 400

    try:
        ref = db.reference(f"accounts/{username}")
        user_data = ref.get()

        if not user_data:
            return jsonify({"error": "Tài khoản không tồn tại"}), 404

        if user_data.get("password") != password:
            return jsonify({"error": "Sai mật khẩu"}), 401

        # 📌 Kiểm tra xem user có sở hữu channel nào không
        channel_ref = db.reference("channels")
        channels_data = channel_ref.get()

        user_channel = None
        if channels_data:
            for channel_name, info in channels_data.items():
                if info.get("host") == username:
                    user_channel = channel_name
                    break

        return jsonify({
            "message": "Đăng nhập thành công",
            "username": username,
            "is_host": user_channel is not None,
            "channel": user_channel
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_my_ip():
    # Lấy địa chỉ IP thật
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Google DNS
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def register_to_tracker():
    my_ip = get_my_ip()
    data = {
        "ip": my_ip,
        "port": str(MY_TCP_PORT)
    }
    try:
        res = requests.post(f"{TRACKER_URL}/submit_info", json=data)
        print("Kết quả đăng ký tracker:", res.json())
    except Exception as e:
        print("Lỗi khi kết nối tới tracker:", e)


# 📌 Gửi tin nhắn TCP đến peer
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    target_ip = data.get("ip")
    target_port = int(data.get("port"))
    message = data.get("message")

    if not target_ip or not target_port or not message:
        return jsonify({"error": "Thiếu thông tin"}), 400

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_ip, target_port))
            s.sendall(message.encode())
        return jsonify({"message": "Gửi thành công"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 📌 4️⃣ Cập nhật message từ client TCP
@app.route('/update_message', methods=['POST'])
def update_message():
    global latest_message
    data = request.json
    message = data.get("message")
    if not message:
        return jsonify({"error": "Thiếu message"}), 400
    latest_message = message
    return jsonify({"message": "Đã cập nhật message thành công"}), 200


# 📌 5️⃣ Trả về message mới nhất (cho giao diện gọi)
@app.route('/get_message', methods=['GET'])
def get_message():
    global latest_message
    if not latest_message:
        return jsonify({"message": "Không có tin nhắn mới"}), 200
    msg = latest_message
    latest_message = None  # reset
    return jsonify({"message": msg}), 200



@app.route('/channels', methods=['GET'])
def get_channels():
    try:
        ref = db.reference("channels")
        channels_data = ref.get()

        if not channels_data:
            return jsonify({"channels": []}), 200

        channel_list = []
        for name, info in channels_data.items():
            channel_list.append({
                "name": name,
                "host": info.get("host", "Không rõ"),
                "joined_users": info.get("joined_users", [])  # <-- Lấy danh sách nếu có
            })

        return jsonify({"channels": channel_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    register_to_tracker()
    app.run(host='0.0.0.0', port=8000)
