# client.py
import socket
import threading
import requests
import datetime
import json

SERVER_FLASK_URL = "http://localhost:8000"


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


def handle_client(conn, addr):
    data = conn.recv(2048)
    if data:
        try:
            message = data.decode("utf-8")
            message_dict = eval(message)
            print(f"🔔 Tin nhắn từ {message_dict.get('sender')}: {message_dict.get('content')}")
            send_to_flask(message)
            log_message(message_dict)
        except Exception as e:
            print("❌ Lỗi đọc tin nhắn:", e)
    conn.close()


def start_server(host='0.0.0.0', port=6000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen()
    print(f"🎧 Lắng nghe TCP tại {host}:{port}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == '__main__':
    start_server()