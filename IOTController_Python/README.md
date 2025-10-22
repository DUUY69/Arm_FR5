# IOTController_Python

Điều khiển thiết bị IoT qua cổng serial (COM) bằng Python, gửi khung HEX theo 115200 8N1.

## Cài đặt

```bash
pip install -r IOTController_Python/requirements.txt
```

## Cấu hình bằng .env

- Khai báo thiết bị và cổng COM qua biến `DEVICES` (danh sách name:COM, phân tách bằng `;`):
```
DEVICES=Cup-Dropping Machine:COM10
```

- Khai báo lệnh cho từng thiết bị bằng JSON trong `<DEVICE_NAME>_COMMANDS` (tên thiết bị đổi thành KEY UPPERCASE và thay khoảng trắng bằng `_`). Ví dụ cho "Cup-Dropping Machine":
```
CUP_DROPPING_MACHINE_COMMANDS={
  "status_query": {"command_code": "0x01", "instruction_code": "0x55", "data_bytes": []},
  "param_query":  {"command_code": "0x02", "instruction_code": "0x55", "data_bytes": []},
  "drop_cup":     {"command_code": "0x04", "instruction_code": "0xAA", "data_bytes": [1,0]},
  "shutdown":     {"command_code": "0x03", "instruction_code": "0xAA", "data_bytes": []}
}
```
- Trường `data_bytes` là mảng số (0-255). `command_code` và `instruction_code` nhận dạng dạng `0x..`.
- Chương trình sẽ tự tính Length và Checksum và thêm byte kết thúc `0xFF`.

## Chạy

```bash
IOTController_Python\run_console.bat
```
- Chọn thiết bị từ danh sách trong `DEVICES`.
- Chọn lệnh từ danh sách key trong `<DEVICE_NAME>_COMMANDS`.
- Chương trình tự build khung và gửi qua COM tương ứng.

## Gửi thủ công (tuỳ chọn)
- CLI gửi khung dựng sẵn:
```bash
python IOTController_Python/cli.py send-frame --cmd-code 0x04 --ins-code 0xAA --data "01 00" --port COM10
```

## Ghi chú
- Giao thức mặc định: 115200, 8N1, không parity.
- Nếu thiết bị khác, chỉ cần thêm vào `DEVICES` và tạo `<DEVICE_NAME>_COMMANDS` tương ứng.
