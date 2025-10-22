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

## Cách sử dụng đơn giản

### Chạy ứng dụng
```bash
# Chỉ cần double-click file này:
run.bat
```

### Chạy trực tiếp (nếu cần)
```bash
# Với SDK (khuyến nghị)
python robot_with_sdk.py

# Đơn giản (fallback)
python simple_robot.py
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
==================================================
    FAIRINO ROBOT CONTROL - PYTHON
==================================================
0. Kiem tra ket noi
1. Ket noi robot
2. Ngat ket noi
3. Upload file Lua
4. Chay file Lua
5. Dung chuong trinh
6. Tam dung chuong trinh
7. Tiep tuc chuong trinh
8. Thong tin robot
9. Thoat
==================================================
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
1. **robot_with_sdk.py**: Script chính sử dụng SDK Python (khuyến nghị)
2. **simple_robot.py**: Script đơn giản chỉ dùng XML-RPC (fallback)
3. **robot_control.py**: Script với menu đầy đủ
4. **run_robot.py**: Script đơn giản, chạy tất cả Lua files
5. **test_robot.py**: Script test kết nối và chức năng

## Batch files để chạy dễ dàng
1. **start_robot.bat**: Chạy script với SDK (robot_with_sdk.py)
2. **start_simple.bat**: Chạy script đơn giản (simple_robot.py)

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
Nếu có vấn đề, vui lòng liên hệ team phát triển.