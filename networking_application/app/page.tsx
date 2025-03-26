import Image from "next/image";
import Sec1 from "./ui/section_1/sec1";
import "@fortawesome/fontawesome-free/css/all.min.css";
import Sec2 from "./ui/section_2/sec2";
import Sec3 from "./ui/section_3/sec3";
import Login from "./login/page";

export default function Home() {
  return (
    <div className="flex w-screen h-screen justify-center items-center ">
      <Sec1 />
      <Sec2 />
      <Sec3 />
    </div>

  );
}
