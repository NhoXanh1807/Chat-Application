function Sec1() {
    return (
        <div className="h-screen bg-[#2B2D31] w-1/4 text-white flex flex-col justify-between p-4 text-2xl border-4 border-solid border-[#6D34AF]">
            <div className="list_channels">
            <ul className="w-full flex flex-col gap-[10px]">
                    <li className="flex justify-between items-center">
                        <div className="channel-name">Channel1</div>
                        <div className="flex items-center gap-2">
                            <div className="channel-owner text-2xl">Peer1</div>
                            <i className="fa-solid fa-bell text-white text-2xl"></i>
                        </div>
                    </li>
                    <li className="flex justify-between items-center">
                        <div className="channel-name">Channel2</div>
                        <div className="flex items-center gap-2">
                            <div className="channel-owner text-2xl"></div>
                            <i className="fa-regular fa-bell text-white"></i>
                        </div>
                        
                    </li>
                </ul>
            </div>
            <div className="peer_name w-full">
                Peer1
            </div>
        </div>
    );
}
export default Sec1;
