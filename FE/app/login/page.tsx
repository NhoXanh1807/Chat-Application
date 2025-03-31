function Login() {
    return (
        <div className="flex w-screen h-screen justify-center items-center bg-[#dddddd]">
            <div className="Loginform text-white border-box w-[20%] h-[30%]" >
                <div className="Name text-3xl p-4 bg-[#6D34AF] rounded-t-[8px]">
                    Login
                </div>
                <div className="details bg-[#2B2D31] text-white p-4 text-xl flex flex-col gap-[5px] rounded-b-[8px]">
                    <div className="ip flex flex-col gap-[5px]">
                        IP:
                        <input type="text" className="bg-[#8E8787] rounded-[8px]" />
                    </div>
                    <div className="password flex flex-col gap-[5px]" >
                        PASSWORD:
                        <input type="text " className="bg-[#8E8787] rounded-[8px]" />
                    </div>

                </div>
            </div>
        </div>

    );
}
export default Login;