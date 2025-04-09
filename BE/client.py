import socket
import threading
import requests

SERVER_FLASK_URL = "http://localhost:8000"  # địa chỉ Flask server

def send_to_flask(message):
    try:
        response = requests.post(f"{SERVER_FLASK_URL}/update_message", json={"message": message})
        if response.status_code == 200:
            print("📨 Tin nhắn đã gửi lên Flask server thành công.")
        else:
            print("❌ Gửi message thất bại:", response.json())
    except Exception as e:
        print("❌ Lỗi khi gửi message đến Flask server:", e)

def handle_client(conn, addr):
    print(f"🔗 Kết nối từ {addr}")

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode("utf-8")
            print(f"[{addr}] {message}")
            send_to_flask(message)
        except:
            break

    conn.close()
    print(f"❌ Kết nối {addr} đã đóng")

def start_server(host='0.0.0.0', port=6000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"🚀 Đang lắng nghe tại {host}:{port}")

    while True:
        conn, addr = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
