
# How to Run and Test the Chat Application

## 🧪 Test Strategy Overview

To thoroughly verify the application functionality and meet all requirements, we recommend testing on **at least 4 virtual machines** with:

- Static IP setup  
- NAT network mode  
- Wireshark installed for network traffic inspection  

> ✅ This setup ensures all test cases can be executed efficiently and with full visibility into peer-to-peer and client-server communication.

---

## 🚀 Environment Setup

### 1. Backend Setup

Open a terminal and:

```bash
cd Chat-Application/BE
```

Make sure your system has `python3` and `pip3` installed. Then install the dependencies:

```bash
pip3 install -r requirements.txt
```

---

### 2. Frontend Setup

You need Node.js installed. Then run the following commands:

```bash
npm install
npm install next react react-dom
```

---

## 🔍 Testing Procedure

We will test both **live stream period**, **client-server**, and **peer-to-peer** behavior.

### Step 1: Run the Tracker

> ⚠️ All BE files are **auto-configured** to fetch the current machine IP — absolutely no hardcoded IPs.  
> The ports mentioned below are placeholders; you can change them if needed.

On the **first machine**, run:

```bash
python3 tracker.py --port-ip 5000
```

👉 After starting, check and **note the IP address** of the tracker to use in the next steps.

The tracker terminal will log real-time updates: peer submissions, connections, and disconnections.

---

### Step 2: Start Servers and Clients

On each of the **remaining 3 machines**, run the following:

```bash
python3 server.py --tracker-ip <your-tracker-ip> --tracker-port 5000 --tcp-port 6000 --service-port 8000
python3 client.py --tcp-port 6000 --flask-port 8000
```

---

### Step 3: Frontend Configuration and Launch

> ❗Currently, automatic environment fetching in FE is not supported due to technical limitations. You must manually set the `.env` file.

Edit `.env`:

```
NEXT_PUBLIC_BACKEND_URL=http://<your-server-ip>:8000
```

Then build and run the frontend:

```bash
npm run build
npm run start
```

Visit the application in the browser at:

```
http://<your-network-ip>:3000
```

---

### Step 4: Login and Peer-to-Peer Messaging

Login on 3 different machines with the following test accounts:

```json
"accounts": {
  "alice": {
    "password": "qwert"
  },
  "bob": {
    "password": "huhu"
  },
  "user1": {
    "password": "abc"
  }
}
```

Use the chat interface to send messages.  
While chatting, you can use **Wireshark** to verify if peer-to-peer transmission and logic behave correctly.

---

## 🔄 Test: Offline Mode and Synchronization

To simulate a peer going offline but still functional:

1. **Stop `server.py` and `client.py`**
2. Start `server-offline.py`:

```bash
python3 server-offline.py --service-port 8000
```

> ⚠️ Due to static IP settings in VM, disconnecting the Ethernet does not fallback to localhost — so offline logic is handled in a separate file.

Edit `.env`:

```
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

Then run:

```bash
npm run build
npm run start
```

Now you can log in and send messages — they are stored directly in a local log.  
Note: Login and messages fetched on screen are cached from the last online session with the peer.

---

## 🔁 Re-Synchronization

To re-sync after going offline:

- Stop `server-offline.py`
- Restart the original:

```bash
python3 server.py --tracker-ip <your-tracker-ip> --tracker-port 5000 --tcp-port 6000 --service-port 8000
python3 client.py --tcp-port 6000 --flask-port 8000
```

Now synchronization will complete automatically.

---

## 📞 Instructor Access

If the instructor would like access for testing or observation, please contact the submitter (Quang).  
I will add your machine to the tracker and walk you through the logic and database operations directly.

---
