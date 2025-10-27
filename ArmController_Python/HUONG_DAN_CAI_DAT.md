# 📦 HƯỚNG DẪN CÀI ĐẶT - SETUP GUIDE

## 🚀 CÀI ĐẶT NHANH (Cho người dùng)

### Bước 1: Kiểm tra Python
```bash
python --version
```
**Yêu cầu:** Python 3.7 trở lên

Nếu chưa có Python:
- Tải từ: https://www.python.org/downloads/
- **QUAN TRỌNG:** Tích vào "Add Python to PATH" khi cài đặt!

### Bước 2: Chạy Setup
Chỉ cần **double-click** vào file:
```
SetupEnvironment.bat
```

Script sẽ tự động:
- ✅ Cài đặt dependencies
- ✅ Build SDK 
- ✅ Test kết nối
- ✅ Hoàn tất setup

### Bước 3: Sử dụng
Sau khi setup xong, bạn có thể chạy:
```bash
# GUI
python arm_controller_gui.py

# Hoặc
start_arm_controller.bat
```

---

## 🔧 TROUBLESHOOTING

### ❌ Lỗi: "Python không tìm thấy"
**Giải pháp:**
1. Cài đặt Python từ python.org
2. Nhớ tích "Add Python to PATH"
3. Restart máy sau khi cài Python

### ❌ Lỗi: "Không thể build SDK"
**Giải pháp:**
1. Cài đặt **Microsoft C++ Build Tools**:
   - Download: https://visualstudio.microsoft.com/downloads/
   - Chọn "Build Tools for Visual Studio"
   - Hoặc cài đặt **Visual Studio Community** (có sẵn C++)

2. Sau khi cài đặt:
   - Chạy lại `SetupEnvironment.bat`

### ❌ Lỗi: "SDK không import được"
**Giải pháp:**
```bash
cd fairino_sdk\fairino
python setup.py build_ext --inplace
```

### ❌ Lỗi: "Robot không kết nối được"
**Kiểm tra:**
1. Robot đã bật chưa?
2. IP robot đúng chưa? (Mặc định: 192.168.58.2)
3. Máy tính và robot có chung mạng không?

---

## 📋 YÊU CẦU HỆ THỐNG

- **OS:** Windows 10/11
- **Python:** 3.7 trở lên (khuyến nghị 3.11)
- **Dependencies:**
  - Cython
  - Requests
  - Tkinter (thường có sẵn với Python)
- **Build Tools:** Microsoft C++ Build Tools hoặc Visual Studio

---

## 🔍 KIỂM TRA SETUP

Chạy script test:
```bash
python test_sdk_build.py
```

Nếu thấy "OK: BUILD THANH CONG!" → Setup thành công!

---

## 📁 CẤU TRÚC THỨ MỤC

```
ArmController_Python/
├── SetupEnvironment.bat          ← File setup chính
├── arm_controller_gui.py        ← GUI điều khiển robot
├── robot_with_sdk.py            ← Console điều khiển
├── start_arm_controller.bat      ← Khởi động GUI
├── test_sdk_build.py            ← Test SDK
├── requirements.txt              ← Dependencies
├── fairino_sdk/                 ← SDK gốc
│   └── fairino/
│       ├── Robot.py             ← Source (Cython)
│       └── Robot.cp311-win_amd64.pyd ← Đã compiled
├── lua_scripts/                 ← Script Lua
└── TechPoint_db/                ← Database points
```

---

## 💡 LƯU Ý

1. **File `.pyd` không sync được** qua Git (vì là compiled binary)
   - Mỗi máy cần build lại SDK
   - File setup tự động handle

2. **Python version khác nhau** sẽ cần build lại
   - Script tự động detect và build phù hợp

3. **Lần đầu cài đặt** có thể mất 5-10 phút
   - Download dependencies
   - Build SDK

---

## 🎯 TÓM TẮT

### Setup trên máy mới:
```
1. Cài Python 3.7+
2. Chạy SetupEnvironment.bat
3. Xong!
```

### Sử dụng:
```
1. Chạy arm_controller_gui.py
2. Kết nối robot (IP: 192.168.58.2)
3. Upload và chạy Lua script
```

---

## 🆘 CẦN HỖ TRỢ?

1. Xem file: `SDK_BUILD_FIX.md`
2. Chạy: `python test_sdk_build.py`
3. Kiểm tra log khi chạy `SetupEnvironment.bat`

