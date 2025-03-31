import Link from "next/link";
function Sec2() {
    return (
        <div className="h-screen bg-[#2B2D31] w-1/2 text-white flex flex-col  text-2xl border-4 border-solid border-[#6D34AF]">
            <div className="channel_name bg-[#6D34AF] p-4 font-bold flex justify-between">
                Channel 2
                <button><i className="fa-solid fa-eye"></i></button>
                {/* <i className="fa-solid fa-eye-slash"></i> */}
            </div>
            <div className="channel_chat p-4 flex flex-col gap-[50px] h-full">
                <ul>
                    <li className="flex gap-[10px]">
                        <div className="peer-name">Peer 1:</div>
                        <div className="peer-content">Hello</div>
                    </li>
                    <li className="flex gap-[10px]">
                        <div className="peer-name">Peer 2:</div>
                        <div className="peer-content">Hello</div>
                    </li>
                </ul>
            </div>
            <Link href="/login" className="loginbtn w-auto m-[10px] bg-[#F221DE] text-white rounded-[8px] p-1 text-center">
                <span>Login</span>
            </Link>

        </div>
    );
}
export default Sec2;