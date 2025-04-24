// page.tsx
"use client";
import Sec1 from "./ui/section_1/sec1";
import "@fortawesome/fontawesome-free/css/all.min.css";
import Sec2 from "./ui/section_2/sec2";
import Sec3 from "./ui/section_3/sec3";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [currentChannel, setCurrentChannel] = useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      const parsed = JSON.parse(userStr);
      setUser(parsed);
      setIsLoggedIn(true);
    }
  }, []);

  const handleLogout = async () => {
    if (user) {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ username: user.username }),
        });

        if (!response.ok) {
          console.error("Logout API failed");
        }
      } catch (err) {
        console.error("Logout error:", err);
      }
    }

    localStorage.removeItem("user");
    setIsLoggedIn(false);
    router.push("/login");
  };

  return (
    <div className="flex w-screen h-screen justify-center items-center relative">
      {isLoggedIn && (
        <div className="absolute top-4 right-4 z-10">
          <button
            onClick={handleLogout}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-500 transition-colors"
          >
            Logout
          </button>
        </div>
      )}
      <Sec1 onChannelSelect={setCurrentChannel} />
      <Sec2 currentChannel={currentChannel || ""} currentUser={user} />
      <Sec3 />
    </div>
  );
}
