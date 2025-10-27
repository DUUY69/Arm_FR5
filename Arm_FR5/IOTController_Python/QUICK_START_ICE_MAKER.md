# ❄️ Quick Start - Thả 5 Viên Đá (Ice Maker)

## 🚀 Cách nhanh nhất

Chỉ cần double-click file này:
```
test_dispense_ice.bat
```

## 📋 Thông tin

- **COM Port**: COM17
- **Baud Rate**: 115200
- **Command**: Dispense 5 ice cubes
- **Protocol**: Ice Maker Serial Communication Protocol V0.0.3

## 📤 Command Frame

```
04 07 AA 01 05 BB FF
```

Breakdown:
- `04` = Dispense Beverage
- `07` = Length
- `AA` = Set Instruction
- `01` = Ice
- `05` = 5 cubes
- `BB` = Checksum
- `FF` = End

## 🔧 Manual Steps

Nếu script không chạy:

1. **Kiểm tra Python**
```bash
python --version
```

2. **Chạy script**
```bash
cd IOTController_Python
python test_ice_maker_5_cubes.py
```

3. **Hoặc dùng IoT GUI**
- Mở `start_simple_iot_gui.bat`
- Kết nối COM17
- Gửi: `04 07 AA 01 05 BB FF`

## ⚠️ Troubleshooting

- **COM port not found**: Kiểm tra cable kết nối
- **No response**: Kiểm tra máy đã bật chưa
- **Permission denied**: Chạy as Administrator

---

**COM Port**: COM17  
**Device**: Ice Maker  
**Date**: 2025
