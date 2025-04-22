"use client";
import Sec1 from "./ui/section_1/sec1";
import "@fortawesome/fontawesome-free/css/all.min.css";
import Sec2 from "./ui/section_2/sec2";
import Sec3 from "./ui/section_3/sec3";
import { useState } from "react";

export default function Home() {
  const [currentChannel, setCurrentChannel] = useState<string | null>(null);

  return (
    <div className="flex w-screen h-screen justify-center items-center">
      <Sec1 onChannelSelect={setCurrentChannel} />
      <Sec2 currentChannel={currentChannel || ""} />
      <Sec3 />
    </div>
  );
}