# 📋 HƯỚNG DẪN SỬ DỤNG IoT GUI

## 🎯 Thả 5 Viên Đá Từ Máy Làm Đá

### Bước 1: Mở GUI
```bash
start_simple_iot_gui.bat
```

### Bước 2: Kết nối
1. Chọn thiết bị: **ICE_MAKER**
2. COM Port: **COM17**
3. Baudrate: **115200**
4. Click "Kết nối"

### Bước 3: Chọn Chế Độ
Trong phần "Chế độ:", chọn:
- ✅ **"Hex Binary"** (quan trọng!)

### Bước 4: Nhập Lệnh
Nhập (không có space, không có dash):
```
0407AA0105BBFF
```

### Bước 5: Gửi
Click nút "Gửi"

### Bước 6: Kiểm Tra Log
Bạn sẽ thấy trong log:
```
🔧 [HEX MODE] Sending as HEX BINARY: 0407AA0105BBFF
📤 Đã gửi 7 bytes (NOT 14 bytes!)
📥 Response: 0407AA0101B7FF
✅ Thành công!
```

## ⚠️ LƯU Ý QUAN TRỌNG

### Phải chọn "Hex Binary" mode!
- ❌ Nếu chọn "ASCII": Sẽ gửi 14 bytes ASCII string
- ❌ Nếu chọn "Tự động": Có thể detect sai
- ✅ Chọn "Hex Binary": Sẽ gửi đúng 7 bytes binary

### Các lệnh khác:

**Thả 5 viên đá:**
```
Chế độ: Hex Binary
Lệnh: 0407AA0105BBFF
```

**Thả nước 20ml:**
```
Chế độ: Hex Binary  
Lệnh: 0407AA0202B5FF
```

**Thả đá nước:**
```
Chế độ: Hex Binary
Lệnh: 0407AA0302B6FF
```

## 🔧 Troubleshooting

### Vẫn gửi 14 bytes?
- Đảm bảo chọn "Hex Binary" mode
- Không có space trong hex string
- Nhập liên tục: `0407AA0105BBFF`

### Không nhận response?
- Kiểm tra máy đã bật chưa
- Kiểm tra kết nối cable
- Kiểm tra COM port đúng chưa

### Response "Loi cu phap"?
- Có thể đang gửi ASCII thay vì binary
- Chọn lại "Hex Binary" mode
- Nhập lại hex string

---

**Date**: 2025  
**Version**: 1.0
