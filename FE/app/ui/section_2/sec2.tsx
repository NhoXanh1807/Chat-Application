import { useEffect, useState } from "react";
import Link from "next/link";

type Message = {
  sender: string;
  content: string;
  timestamp: string;
};

function Sec2() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentChannel, setCurrentChannel] = useState("Channel 2");
  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    const checkLoginStatus = () => {
      const userData = localStorage.getItem('user');
      setShowLogin(!userData);
    };

    checkLoginStatus();

    const fetchMessages = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${backendUrl}/get_all_messages?channel=${encodeURIComponent(currentChannel)}`);
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json() as { messages?: Message[] };
        setMessages(data.messages || []);
      } catch (error) {
        console.error('Fetch messages error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [currentChannel]);

  return (
    <div className="h-screen bg-[#2B2D31] w-1/2 text-white flex flex-col text-2xl border-4 border-solid border-[#6D34AF]">
      <div className="channel_name bg-[#6D34AF] p-4 font-bold flex justify-between">
        {currentChannel}
        <button>
          <i className="fa-solid fa-eye"></i>
        </button>
      </div>
      
      <div className="channel_chat p-4 flex flex-col gap-[20px] h-full overflow-y-auto">
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

      {showLogin && (
        <Link 
          href="/login" 
          className="loginbtn w-auto m-[10px] bg-[#F221DE] text-white rounded-[8px] p-1 text-center hover:bg-[#D11BC7] transition-colors"
        >
          <span>Login</span>
        </Link>
      )}
    </div>
  );
}

export default Sec2;