# ❄️ Ice Maker Control Guide

## 📋 Protocol Overview

Máy làm đá sử dụng **Ice Maker Serial Communication Protocol V0.0.3**:

- **Serial**: RS232 hoặc RS485
- **Baud Rate**: 115200
- **Data Format**: 1 start bit, 8 data bits, 1 stop bit, no parity
- **End Code**: 0xFF

## 🎯 Thả 5 Viên Đá

### Frame Structure:

```
Command Code: 0x04 (Dispense Beverage)
Length Code: 0x07
Instruction Code: 0xAA (Set)
Beverage Number: 0x01 (Ice)
Data 1: 0x05 (Quantity = 5)
Checksum: Tính tự động
End Code: 0xFF
```

### Ví dụ:

**Frame hex**: `04 07 AA 01 05 [checksum] FF`

### Tính checksum:

```python
checksum = (0x04 + 0x07 + 0xAA + 0x01 + 0x05) & 0xFF
         = 0xBB
```

**Frame hoàn chỉnh**: `04 07 AA 01 05 BB FF`

## 🚀 Cách sử dụng

### Option 1: Dùng script Python

```bash
cd IOTController_Python
python test_ice_maker_5_cubes.py
```

### Option 2: Dùng Python script

```python
from ice_maker_commands import IceMakerController

ice_maker = IceMakerController('COM11', baudrate=115200)
ice_maker.open()

# Thả 5 viên đá
ice_maker.dispense_ice(quantity=5)

ice_maker.close()
```

### Option 3: Dùng IoT GUI

1. Mở `start_simple_iot_gui.bat`
2. Kết nối đến Ice Maker (COM port)
3. Gửi hex: `04 07 AA 01 05 BB FF`

### Option 4: Dùng Serial Monitor

1. Mở serial monitor (115200 baud)
2. Gửi: `04 07 AA 01 05 BB FF`

## 📝 Các lệnh khác

### 1. Query Status (0x01)

**Query**:
```
01 05 55 [checksum] FF
```

**Response**:
```
01 08 55 [status bits] [working status] [extended status] [checksum] FF
```

### 2. Query Parameters (0x02)

**Query**:
```
02 05 55 [checksum] FF
```

**Response**: 13 data bytes về nhiệt độ, số lượng, version, etc.

### 3. Dispense Water (0x04)

**Command**: 
```
04 07 AA 02 05 [checksum] FF
```
- `02` = water
- `05` = quantity

### 4. Dispense Ice Water (0x04)

**Command**:
```
04 07 AA 03 05 [checksum] FF
```
- `03` = ice water
- `05` = quantity

## 🔧 Troubleshooting

### Không nhận được response?

1. **Kiểm tra COM port**: Đúng port chưa?
2. **Kiểm tra baud rate**: Phải là 115200
3. **Kiểm tra kết nối**: Cable, power
4. **Kiểm tra slave**: Máy có đang hoạt động không?

### Checksum sai?

Sử dụng function:
```python
def compute_checksum(data):
    return sum(data) & 0xFF
```

### Máy không thả đá?

1. Query status trước để xem máy có lỗi không
2. Kiểm tra số lượng đá trong máy
3. Kiểm tra máy có đang trong trạng thái standby không

## 📊 Example Commands

### Query Status:
```
Sent:   01 05 55 5B FF
Receive: 01 08 55 00 00 00 08 FF
         - Data 1: 0x00 (No faults)
         - Data 2: 0x00 (Standby)
         - Data 3: 0x00 (Not filling, not short of ice)
```

### Dispense 5 Cubes:
```
Sent:   04 07 AA 01 05 BB FF
Receive: 04 05 AA 01 01 EC FF
         - Data 1: 0x01 (Success!)
```

## 📁 Files

- `ice_maker_commands.py` - Full controller class
- `test_ice_maker_5_cubes.py` - Script để thả 5 viên đá
- `config.env` - COM port configuration

## ⚙️ Configuration

Trong `config.env`:

```
ICE_MAKER=COM11,115200
```

---

**Version**: 1.0  
**Protocol**: Ice Maker Serial Communication Protocol V0.0.3  
**Date**: 2025
