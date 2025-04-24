"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const Modal = ({ title, children, onClose, onSubmit, submitLabel = "Xác nhận" }: any) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
    <div className="bg-white text-black p-6 rounded-lg min-w-[300px] max-w-[400px]">
      <h2 className="text-xl font-bold mb-4">{title}</h2>
      {children}
      <div className="mt-4 flex justify-between">
        <button onClick={onClose} className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400">Đóng</button>
        <button onClick={onSubmit} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">{submitLabel}</button>
      </div>
    </div>
  </div>
);

type Message = {
  sender: string;
  content: string;
  timestamp: string;
};

type Sec2Props = {
  currentChannel: string;
  currentUser: any;
};

function Sec2({ currentChannel, currentUser }: Sec2Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [newMessage, setNewMessage] = useState("");
  const [showLogin, setShowLogin] = useState(false);
  const [isHost, setIsHost] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showRemoveModal, setShowRemoveModal] = useState(false);
  const [allAccounts, setAllAccounts] = useState<string[]>([]);
  const [joinedUsers, setJoinedUsers] = useState<string[]>([]);
  const [selectedAddUser, setSelectedAddUser] = useState<string | null>(null);
  const [selectedRemoveUsers, setSelectedRemoveUsers] = useState<Set<string>>(new Set());

  useEffect(() => {
    const userData = localStorage.getItem('user');
    setShowLogin(!userData);
    if (userData) {
      const parsed = JSON.parse(userData);
      setIsHost(parsed.channels_hosted.includes(currentChannel));
    }
  }, [currentChannel]);

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        if (!currentChannel) return;
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

        const [msgRes, userRes] = await Promise.all([
          fetch(`${backendUrl}/get_all_messages?channel=${encodeURIComponent(currentChannel)}`),
          fetch(`${backendUrl}/get_join_users?channel=${encodeURIComponent(currentChannel)}`)
        ]);

        if (!msgRes.ok || !userRes.ok) throw new Error("Failed to fetch data");

        const msgData = await msgRes.json();
        const userData = await userRes.json();

        setMessages(msgData.messages || []);
        setJoinedUsers(userData.joined_users || []);
      } catch (err) {
        console.error("Error loading messages or users", err);
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [currentChannel]);

  const fetchAllAccounts = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/get_all_accounts`);
    const data = await res.json();
    setAllAccounts(data.usernames);
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !currentChannel) return;

    try {
      const userData = localStorage.getItem('user');
      if (!userData) {
        setShowLogin(true);
        return;
      }

      const user = JSON.parse(userData);
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${backendUrl}/send_to_channel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: currentChannel,
          sender: user.username,
          content: newMessage
        })
      });

      if (!response.ok) throw new Error('Gửi tin nhắn thất bại');
      setNewMessage("");
    } catch (error) {
      console.error('Gửi tin nhắn lỗi:', error);
    }
  };

  const handleAddMember = async () => {
    if (!selectedAddUser) return;
    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/add_member`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        channel: currentChannel,
        username: selectedAddUser,
        adder: currentUser.username
      })
    });
    if (response.ok) {
      alert("Đã thêm thành viên thành công");
      setShowAddModal(false);
    } else {
      alert("Thêm thành viên thất bại");
    }
  };

  const handleRemoveMembers = async () => {
    for (const username of selectedRemoveUsers) {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/remove_member`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: currentChannel,
          username: username,
          remover: currentUser.username
        })
      });
      if (!response.ok) alert(`Xóa ${username} thất bại`);
    }
    alert("Đã xóa các thành viên được chọn");
    setShowRemoveModal(false);
  };

  return (
    <div className="h-screen bg-[#2B2D31] w-1/2 text-white flex flex-col text-2xl border-4 border-solid border-[#6D34AF]">
      <div className="channel_name bg-[#6D34AF] p-4 font-bold flex justify-between items-center">
        <span>{currentChannel || "Chọn một channel"}</span>
        <div className="flex gap-2">
          {isHost && (
            <>
              <button
                onClick={() => { setShowAddModal(true); fetchAllAccounts(); }}
                className="bg-green-600 px-2 py-1 rounded text-sm hover:bg-green-700"
              >Add Member</button>
              <button
                onClick={() => setShowRemoveModal(true)}
                className="bg-red-600 px-2 py-1 rounded text-sm hover:bg-red-700"
              >Remove Member</button>
            </>
          )}
        </div>
      </div>

      <div className="channel_chat p-4 flex flex-col gap-[20px] h-[80%] overflow-y-auto">
        {loading ? (
          <div className="text-center text-gray-400">Đang tải tin nhắn...</div>
        ) : messages.length === 0 ? (
          <div className="text-center text-gray-400">Không có tin nhắn nào</div>
        ) : (
          <ul className="flex flex-col gap-[10px]">
            {messages.map((message, index) => (
              <li key={`msg-${index}`} className="flex gap-[10px]">
                <div className="peer-name font-semibold">{message.sender}:</div>
                <div className="peer-content">{message.content}</div>
                <div className="text-sm text-gray-400 ml-auto">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {!showLogin && (
        <div className="p-4 flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            className="flex-1 bg-[#3E4053] rounded px-4 py-2 text-white"
            placeholder="Nhập tin nhắn..."
          />
          <button
            onClick={handleSendMessage}
            className="bg-[#6D34AF] px-4 py-2 rounded hover:bg-[#5D2B9F] transition-colors"
          >Gửi</button>
        </div>
      )}

      {showLogin && (
        <Link href="/login" className="loginbtn w-auto m-[10px] bg-[#F221DE] text-white rounded-[8px] p-1 text-center hover:bg-[#D11BC7] transition-colors">
          <span>Login</span>
        </Link>
      )}

      {showAddModal && (
        <Modal title="Thêm thành viên" onClose={() => setShowAddModal(false)} onSubmit={handleAddMember}>
          <select onChange={(e) => setSelectedAddUser(e.target.value)} className="w-full p-2 border">
            <option value="">-- Chọn người dùng --</option>
            {allAccounts.map((username, idx) => (
              <option key={idx} value={username}>{username}</option>
            ))}
          </select>
        </Modal>
      )}

      {showRemoveModal && (
        <Modal title="Xóa thành viên" onClose={() => setShowRemoveModal(false)} onSubmit={handleRemoveMembers}>
          <ul className="max-h-40 overflow-y-auto">
            {joinedUsers.map((username, idx) => (
              <li key={idx} className="flex gap-2 items-center">
                <input
                  type="checkbox"
                  onChange={(e) => {
                    const newSet = new Set(selectedRemoveUsers);
                    if (e.target.checked) newSet.add(username);
                    else newSet.delete(username);
                    setSelectedRemoveUsers(newSet);
                  }}
                />
                <label>{username}</label>
              </li>
            ))}
          </ul>
        </Modal>
      )}
    </div>
  );
}

export default Sec2;
