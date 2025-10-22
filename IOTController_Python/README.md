# IOTController_Python

Điều khiển thiết bị IoT qua cổng serial (COM) bằng Python và mã hex.

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

- Gửi mã hex tới thiết bị (ví dụ COM3, baud 9600):

```bash
python IOTController_Python/cli.py send --port COM3 --baud 9600 --hex "A1 01 FF"
```

- Gửi và đọc lại 8 byte phản hồi:

```bash
python IOTController_Python/cli.py send --port COM3 --hex "A1 01 FF" --read 8
```

- Gửi và đọc cho đến khi gặp mẫu hex (ví dụ FF0D):

```bash
python IOTController_Python/cli.py send --port COM3 --hex "A1 01 FF" --until FF0D
```

Tùy chọn thêm:
- `--timeout 1.0` thời gian chờ đọc (giây)
- `--rtscts` bật RTS/CTS
- `--xonxoff` bật XON/XOFF

## Dùng trong code Python

```python
from IOTController_Python.iot_controller import IoTController

ctl = IoTController()
ctl.open("COM3", baudrate=9600, timeout=1.0)
ctl.send_hex("A1 01 FF")
data = ctl.read_bytes(8)
print(data.hex())
ctl.close()
```

## Lưu ý
- Hex có thể viết dạng `A1 01 FF` hoặc `0xA101FF`.
- Nếu không thấy COM, hãy kiểm tra driver USB và quyền truy cập.
