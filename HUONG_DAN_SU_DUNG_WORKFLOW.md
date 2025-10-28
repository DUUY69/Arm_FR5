# 📖 Hướng Dẫn Sử Dụng Workflow System

## 🎯 2 Cách Chạy Workflow

### 1️⃣ **Chạy GUI (Giao Diện Đồ Họa)**

Dễ sử dụng nhất, phù hợp cho người mới bắt đầu:

```batch
# Double click file này
start_workflow_gui.bat
```

**Tính năng GUI:**
- ✅ Load/Save workflow từ file JSON
- ✅ Kết nối Robot và IoT devices
- ✅ Chạy workflow trực quan
- ✅ Xem log realtime
- ✅ Hiển thị trạng thái workflow

### 2️⃣ **Chạy Command Line**

Chạy trực tiếp từ terminal:

```batch
# Chạy workflow máy khuấy
run_stirrer_workflow.bat

# Hoặc chạy Python script trực tiếp
python run_stirrer_workflow.py
```

## 📋 Chuẩn Bị

### 1. Kiểm Tra Python

```batch
python --version
```

Nếu chưa có, cài Python 3.8+ từ [python.org](https://www.python.org)

### 2. Cài Đặt Dependencies

```batch
pip install -r requirements.txt
```

### 3. Chuẩn Bị Workflow File

File JSON workflow nằm trong thư mục `Arm_FR5/`:
- `stirrer_workflow.json` - Workflow máy khuấy (đã có sẵn)
- `example_workflow_coffee.json` - Ví dụ workflow cà phê

## 🚀 Sử Dụng GUI

### Bước 1: Mở GUI

```batch
start_workflow_gui.bat
```

### Bước 2: Load Workflow

1. Click **"📂 Load Workflow"**
2. Chọn file JSON (ví dụ: `stirrer_workflow.json`)
3. Kiểm tra thông tin workflow hiển thị

### Bước 3: Kết Nối Thiết Bị

**Kết nối Robot:**
1. Click **"🤖 Kết Nối Robot"**
2. Robot tự động kết nối IP: 192.168.58.2
3. Đợi thông báo "✅ Đã kết nối Robot"

**Kết nối IoT Device:**
1. Click **"📡 Kết Nối IoT Device"**
2. Nhập COM port (ví dụ: COM8)
3. Nhập tên device (ví dụ: Stirrer)
4. Click **"Kết Nối"**

### Bước 4: Chạy Workflow

1. Click **"▶️ Chạy Workflow"**
2. Xem log realtime trong khung bên phải
3. Đợi workflow hoàn thành

## 📝 Cấu Trúc Workflow

Workflow máy khuấy có 3 bước:

```json
{
  "steps": [
    {
      "name": "Robot di chuyển đến máy khuấy",
      "action": "run_lua: MoveToMotor.lua"
    },
    {
      "name": "Bật máy khuấy tốc độ 10 (5 giây)",
      "action": "send_command: 10"
    },
    {
      "name": "Robot lấy cốc ra",
      "action": "run_lua: OutMotor.lua"
    }
  ]
}
```

## ⚙️ Cấu Hình

### Thay Đổi Robot IP

Sửa trong file Python:
```python
robot_ip = '192.168.58.2'  # Sửa IP ở đây
```

### Thay Đổi COM Port

Trong GUI: Nhập COM port khi kết nối IoT device

Trong Command Line: Sửa trong file Python:
```python
stirrer.open('COM8', baudrate=115200)  # Sửa COM port ở đây
```

## 🐛 Troubleshooting

### Lỗi: "Python không được tìm thấy"
- Cài đặt Python và thêm vào PATH
- Hoặc chạy trực tiếp: `python.exe workflow_gui.py`

### Lỗi: "Không thể kết nối Robot"
- Kiểm tra IP robot
- Kiểm tra network connection
- Kiểm tra robot đã bật chưa

### Lỗi: "Không thể mở COM port"
- Kiểm tra COM port có đúng không
- Kiểm tra thiết bị đã cắm USB chưa
- Thử COM port khác
- Đóng các ứng dụng khác đang dùng COM port

### Lỗi: "Module not found"
- Chạy: `pip install -r requirements.txt`
- Kiểm tra Python path

## 📊 Files Của Dự Án

```
Arm_FR5/
├── workflow_gui.py                    # GUI chính
├── run_stirrer_workflow.py           # Script chạy workflow
├── stirrer_workflow.json              # Workflow máy khuấy
├── coffee_workflow_coordinator.py     # Workflow engine
├── start_workflow_gui.bat             # 🖱️ Chạy GUI
├── run_stirrer_workflow.bat           # 🖱️ Chạy CLI
└── HUONG_DAN_SU_DUNG_WORKFLOW.md     # 📖 File này
```

## ✅ Test Nhanh

Chạy workflow test không cần robot/iot:

```python
python -c "from coffee_workflow_coordinator import CoffeeWorkflowCoordinator; w = CoffeeWorkflowCoordinator(); w.create_coffee_workflow_template(); print('OK!')"
```

## 🎉 Kết Luận

Bây giờ bạn có đầy đủ tools để:
- ✅ Tạo workflow mới
- ✅ Load/save workflow JSON
- ✅ Chạy workflow bằng GUI hoặc command line
- ✅ Quản lý và theo dõi workflow

Happy workflow! 🚀

