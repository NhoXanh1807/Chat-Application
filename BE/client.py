# client.py
import socket
import threading
import requests
import datetime
import json
import os

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    s.close()
    return ip

SERVER_FLASK_URL = f"http://{get_my_ip()}:8000"

def send_to_flask(message):
    try:
        requests.post(f"{SERVER_FLASK_URL}/update_message", json={"message": message})
    except:
        pass

def log_message(message_dict):
    channel = message_dict.get("channel", "general")
    with open(f"log_{channel}.txt", "a", encoding="utf-8") as f:
        ts = message_dict.get("timestamp")
        sender = message_dict.get("sender")
        content = message_dict.get("content")
        f.write(f"[{ts}] {sender}: {content}\n")

def upload_missing_logs():
    try:
        channels = requests.get(f"{SERVER_FLASK_URL}/channels").json().get("channels", [])
        for ch in channels:
            name = ch['name']
            log_file = f"log_{name}.txt"
            if not os.path.exists(log_file):
                continue
            with open(log_file, "r", encoding="utf-8") as f:
                log_lines = f.readlines()

            firebase_msgs = requests.get(f"{SERVER_FLASK_URL}/get_message").json().get("message")
            firebase_data = str(firebase_msgs)
            for line in log_lines:
                if line.strip() not in firebase_data:
                    parts = line.strip().split(' ', 2)
                    if len(parts) >= 3:
                        ts = parts[0].strip('[]')
                        sender = parts[1].strip(':')
                        content = parts[2]
                        msg = {
                            "channel": name,
                            "sender": sender,
                            "content": content,
                            "timestamp": ts
                        }
                        send_to_flask(msg)
    except Exception as e:
        print("❌ Lỗi khi upload log:", e)

def handle_client(conn, addr):
    data = conn.recv(2048)
    if data:
        try:
            message = data.decode("utf-8")
            message_dict = eval(message)
            print(f"🔔 Tin nhắn từ {message_dict.get('sender')}: {message_dict.get('content')}")
            send_to_flask(message_dict)
            log_message(message_dict)
        except Exception as e:
            print("❌ Lỗi đọc tin nhắn:", e)
    conn.close()

def start_server(host='0.0.0.0', port=6000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen()
    print(f"🎧 Lắng nghe TCP tại {host}:{port}")
    if host == '127.0.0.1':
        print("📥 Chế độ offline - log lại tin nhắn")
    else:
        upload_missing_logs()

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == '__main__':
    start_server()