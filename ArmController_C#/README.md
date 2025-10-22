# ArmController_C# - Fairino Robot Control (C#)

## Mô tả
Thư viện và ứng dụng điều khiển robot Fairino bằng C# với giao diện Windows Forms.

## Cấu trúc thư mục
```
ArmController_C#/
├── FRRobot/                 # Thư viện SDK chính
│   ├── FRRobot.cs          # Class chính để điều khiển robot
│   ├── RobotTypes.cs       # Các kiểu dữ liệu robot
│   ├── RPCHandle.cs        # Xử lý RPC
│   ├── TCPClient.cs        # Client TCP
│   └── StatusTCPClient.cs  # Client TCP cho status
├── My_Arm/                 # Ứng dụng Windows Forms
│   ├── Program.cs          # Entry point
│   ├── Form1.cs            # Form chính
│   └── RobotController.cs  # Controller chính
├── lua_scripts/            # Script Lua cho robot
├── dist/                   # File executable và DLL
└── README.md              # Hướng dẫn này
```

## Yêu cầu hệ thống
- Windows 10/11
- .NET Framework 4.7.2 hoặc cao hơn
- Visual Studio 2019+ (để build)
- Robot Fairino với IP có thể truy cập

## Cài đặt và sử dụng

### 1. Build project
```bash
# Mở Visual Studio và build solution
# Hoặc sử dụng command line:
msbuild My_Arm.sln /p:Configuration=Release
```

### 2. Chạy ứng dụng
```bash
# Chạy file executable
cd dist
My_Arm.exe
```

### 3. Cấu hình robot
- Mở ứng dụng
- Nhập IP robot (mặc định: 192.168.58.2)
- Click "Connect" để kết nối
- Upload và chạy script Lua

## Chức năng chính
- ✅ Kết nối robot qua XML-RPC
- ✅ Upload file Lua lên robot
- ✅ Chạy/dừng/tạm dừng script
- ✅ Giao diện Windows Forms thân thiện
- ✅ Logging và error handling
- ✅ Điều khiển robot real-time

## API chính
```csharp
// Kết nối robot
robot = new FRRobot();
robot.Connect("192.168.58.2");

// Upload file Lua
robot.LuaUpload("TakeCup.lua");

// Chạy script
robot.ProgramLoad("/fruser/TakeCup.lua");
robot.ProgramRun();

// Dừng script
robot.ProgramStop();
```

## Troubleshooting
1. **Không kết nối được robot**: Kiểm tra IP và network
2. **Upload Lua thất bại**: Kiểm tra file Lua có hợp lệ không
3. **Robot không chạy**: Kiểm tra robot đã enable chưa

## Liên hệ
Nếu có vấn đề, vui lòng liên hệ KoroKoro.