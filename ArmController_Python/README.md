# ArmController_Python - Fairino Robot Control (Python)

## Mô tả
Thư viện và script điều khiển robot Fairino bằng Python với giao diện console đơn giản.

## Cấu trúc thư mục
```
ArmController_Python/
├── robot_control.py        # Script chính với menu console
├── myarm.py               # Script gốc (advanced)
├── simple_robot_control.py # Script đơn giản
├── test_robot.py          # Script test kết nối
├── run_robot.py           # Script chạy nhanh
├── start_robot.bat        # Batch file để chạy dễ dàng
├── lua_scripts/           # Script Lua cho robot
│   ├── TakeCup.lua
│   ├── MoveToCupDownMachine.lua
│   └── testCupDown.lua
├── vendor/                # Thư viện Python SDK
└── README.md             # Hướng dẫn này
```

## Yêu cầu hệ thống
- Windows 10/11
- Python 3.7+ 
- Robot Fairino với IP có thể truy cập

## Cài đặt và sử dụng

### 1. Cài đặt Python
```bash
# Tải và cài đặt Python từ python.org
# Hoặc sử dụng Anaconda/Miniconda
```

### 2. Chạy ứng dụng
```bash
# Cách 1: Sử dụng batch file (dễ nhất)
run_console.bat

# Cách 2: Chạy trực tiếp
python robot_control.py

# Cách 3: Script đơn giản
python run_robot.py
```

### 3. Cấu hình robot
- Mở script Python
- Nhập IP robot (mặc định: 192.168.58.2)
- Chọn menu để upload và chạy script Lua

## Chức năng chính
- ✅ Kết nối robot qua XML-RPC
- ✅ Upload file Lua lên robot
- ✅ Chạy/dừng/tạm dừng script
- ✅ Giao diện console thân thiện
- ✅ Error handling và logging
- ✅ Test kết nối tự động

## Menu chính
```
=== Fairino Robot Console (Python) ===
0. Test connection (RPC/TCP diagnostics)
1. Upload Lua file
2. Run Lua file
3. View log
4. Exit
Select option:

==========================================
```

## API chính
```python
# Kết nối robot
robot = FairinoRobotController("192.168.58.2")
robot.connect()

# Upload file Lua
robot.upload_lua("TakeCup.lua")

# Chạy script
robot.run_lua("TakeCup.lua")

# Dừng script
robot.stop_program()
```

## Script có sẵn
1. **robot_control.py**: Script chính với menu đầy đủ
2. **run_robot.py**: Script đơn giản, chạy tất cả Lua files
3. **test_robot.py**: Script test kết nối và chức năng
4. **simple_robot_control.py**: Script với class wrapper

## Troubleshooting
1. **Không kết nối được robot**: Kiểm tra IP và network
2. **Python không tìm thấy**: Thêm Python vào PATH
3. **Upload Lua thất bại**: Kiểm tra file Lua có hợp lệ không
4. **Encoding error**: Sử dụng Python 3.7+ với UTF-8

## Ví dụ sử dụng
```python
from robot_control import FairinoRobotController

# Tạo controller
robot = FairinoRobotController("192.168.58.2")

# Kết nối
if robot.connect():
    # Upload và chạy Lua
    robot.upload_lua("TakeCup.lua")
    robot.run_lua("TakeCup.lua")
    
    # Dừng khi xong
    robot.stop_program()
```

## Liên hệ
Nếu có vấn đề, vui lòng liên hệ KoroKoro.