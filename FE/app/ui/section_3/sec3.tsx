"use client";
import { useEffect, useState } from 'react';

type UserStatus = {
  username: string;
  isOnline: boolean;
};

function Sec3() {
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);
  const [offlineUsers, setOfflineUsers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserStatus = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${backendUrl}/channels`);
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json() as { channels?: Array<{
          online_users: string[];
          offline_users: string[];
        }> };

        // Tổng hợp tất cả user từ các channel
        const allUsers: UserStatus[] = [];
        
        data.channels?.forEach(channel => {
          channel.online_users?.forEach(user => {
            allUsers.push({ username: user, isOnline: true });
          });
          channel.offline_users?.forEach(user => {
            allUsers.push({ username: user, isOnline: false });
          });
        });

        // Loại bỏ trùng lặp và phân loại
        const uniqueUsers = allUsers.reduce((acc, user) => {
          // Ưu tiên trạng thái online nếu user xuất hiện ở cả hai
          if (!acc[user.username] || user.isOnline) {
            acc[user.username] = user.isOnline;
          }
          return acc;
        }, {} as Record<string, boolean>);

        // Tách thành 2 danh sách
        const online: string[] = [];
        const offline: string[] = [];
        
        Object.entries(uniqueUsers).forEach(([username, isOnline]) => {
          if (isOnline) {
            online.push(username);
          } else {
            offline.push(username);
          }
        });

        setOnlineUsers(online);
        setOfflineUsers(offline);

      } catch (error) {
        console.error('Fetch user status error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserStatus();
    const interval = setInterval(fetchUserStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen bg-[#2B2D31] w-1/4 text-white flex flex-col text-2xl border-4 border-solid border-[#6D34AF] p-4 gap-4">
      <div className="online-sec">
        <div className="font-bold mb-2">Online ({onlineUsers.length})</div>
        <ul className="flex flex-col gap-1 pl-4">
          {loading ? (
            <li className="text-gray-400">Đang tải...</li>
          ) : onlineUsers.length === 0 ? (
            <li className="text-gray-400">Không có user online</li>
          ) : (
            onlineUsers.map((user, index) => (
              <li key={`online-${index}`} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                {user}
              </li>
            ))
          )}
        </ul>
      </div>
      
      <div className="offline-sec">
        <div className="font-bold mb-2">Offline ({offlineUsers.length})</div>
        <ul className="flex flex-col gap-1 pl-4">
          {loading ? (
            <li className="text-gray-400">Đang tải...</li>
          ) : offlineUsers.length === 0 ? (
            <li className="text-gray-400">Không có user offline</li>
          ) : (
            offlineUsers.map((user, index) => (
              <li key={`offline-${index}`} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-gray-500"></div>
                {user}
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}

export default Sec3;