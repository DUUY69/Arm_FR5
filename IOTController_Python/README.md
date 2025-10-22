# IOTController_Python

Điều khiển thiết bị IoT qua cổng serial (COM) bằng Python và mã hex.

Mặc định giao tiếp 115200, 8N1, không parity (theo tài liệu giao thức).

## Cài đặt

1) Cài Python 3.10+ và pip.
2) Cài thư viện:

```bash
pip install -r IOTController_Python/requirements.txt
```

## Các lệnh cơ bản

- Liệt kê cổng COM:

```bash
python IOTController_Python/cli.py list
```

- Gửi mã hex tới thiết bị (ví dụ COM3, baud 115200):

```bash
python IOTController_Python/cli.py send --port COM3 --baud 115200 --hex "04 07 AA 01 00 B6 FF"
```

- Gửi theo ID hành động trong `actions.json` (đã khai báo sẵn các khung):

```bash
python IOTController_Python/cli.py send-id --id dispense_one --port COM3
```

- Tự dựng khung theo quy tắc: `cmd, len, ins, data..., checksum, FF`:

```bash
python IOTController_Python/cli.py send-frame --cmd-code 0x04 --ins-code 0xAA --data "01 00" --port COM3
```

Các khung mẫu trong `actions.json` (theo tài liệu):

```json
{
  "status_query": "01 06 55 5C FF",
  "param_query": "02 06 55 5D FF",
  "shutdown": "03 05 AA B2 FF",
  "dispense_one": "04 07 AA 01 00 B6 FF"
}
```

- `status_query`: 0x01, query 0x55
- `param_query`: 0x02, query 0x55
- `shutdown`: 0x03, set 0xAA
- `dispense_one`: 0x04, set 0xAA, Beverage=0x01, Data1=0x00 (Reserved)

Tùy chọn đọc sau khi gửi:

```bash
python IOTController_Python/cli.py send-id --id status_query --port COM3 --read 16
```

Hoặc đọc cho đến khi gặp `FF` và đủ độ dài mong đợi:

```bash
python IOTController_Python/cli.py send-id --id status_query --port COM3 --until FF
```

## Lưu ý
- Checksum là tổng 8-bit của toàn bộ bytes trừ checksum và 0xFF.
- Mã ví dụ "Drop one cup": `04 07 aa 01 00 B6 ff`.
- Nếu không thấy COM, kiểm tra driver USB và quyền truy cập.
