"use client";
import { useEffect, useState } from 'react';

type Channel = {
  name: string;
  host: string;
  offline_users: string[];
  online_users: string[];
};

type User = {
  username: string;
  status: 'Online' | 'Offline';
};

function Sec1({ onChannelSelect }: { onChannelSelect: (channelName: string) => void }) {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [currentUser, setCurrentUser] = useState<User>({ 
    username: 'Visitor', 
    status: 'Online'
  });
  const [loading, setLoading] = useState(true);
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      try {
        const user = JSON.parse(userData) as { username: string };
        setCurrentUser({
          username: user.username,
          status: 'Online'
        });
      } catch (error) {
        console.error('Lỗi parse user data:', error);
      }
    }

    const fetchChannels = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${backendUrl}/channels`);
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json() as { channels?: Channel[] };
        
        setChannels(data.channels || []);

        if (backendUrl.includes('127.0.0.1') || backendUrl.includes('localhost')) {
          setCurrentUser(prev => ({ ...prev, status: 'Offline' }));
        }
      } catch (error) {
        console.error('Fetch channels error:', error);
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
        if (backendUrl.includes('127.0.0.1') || backendUrl.includes('localhost')) {
          setCurrentUser(prev => ({ ...prev, status: 'Offline' }));
        }
      } finally {
        setLoading(false);
      }
    };

    fetchChannels();
    const interval = setInterval(fetchChannels, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleChannelClick = (channelName: string) => {
    setSelectedChannel(channelName);
    onChannelSelect(channelName);
  };

  return (
    <div className="h-screen bg-[#2B2D31] w-1/4 text-white flex flex-col justify-between p-4 text-2xl border-4 border-solid border-[#6D34AF]">
      <div className="list_channels">
        {loading ? (
          <div className="text-center">Đang tải...</div>
        ) : channels.length === 0 ? (
          <div className="text-center">Không có channel nào</div>
        ) : (
          <ul className="w-full flex flex-col gap-[10px]">
            {channels.map((channel, index) => (
              <li 
                key={`${channel.name}-${index}`} 
                className={`flex justify-between items-center p-2 rounded cursor-pointer ${selectedChannel === channel.name ? 'bg-[#6D34AF]' : 'hover:bg-[#3E4053]'}`}
                onClick={() => handleChannelClick(channel.name)}
              >
                <div className="channel-name">{channel.name}</div>
                <div className="flex items-center gap-2">
                  <div className="channel-owner text-2xl">{channel.host}</div>
                  <i 
                    className={`fa-${channel.online_users.length > 0 ? 'solid' : 'regular'} fa-bell text-white text-2xl`}
                  ></i>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="peer_name w-full flex justify-between items-center">
        <span>{currentUser.username}</span>
        <div className={`status ${currentUser.status === 'Online' ? 'text-green-500' : 'text-gray-500'}`}>
          {currentUser.status}
        </div>
      </div>
    </div>
  );
}

export default Sec1;