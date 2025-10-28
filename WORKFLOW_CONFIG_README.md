# ⚙️ Workflow Configuration

## 📁 File Structure

```
Arm_FR5/
├── workflow_config.env          # ⚙️ Config cho Workflow System
├── workflows/                    # 📂 Folder chứa workflow JSON files
│   ├── stirrer_workflow.json
│   └── example_workflow_coffee.json
├── config_loader.py             # 🔧 Module đọc config
└── WORKFLOW_CONFIG_README.md    # 📖 File này
```

## 🔧 Configuration File

File `workflow_config.env` chứa cấu hình cho Workflow System:

### IoT Devices:
```env
STIRRER_PORT=COM8
STIRRER_BAUDRATE=115200
STIRRER_NAME=Stirrer

COFFEE_MAKER_PORT=COM7
COFFEE_MAKER_BAUDRATE=115200
COFFEE_MAKER_NAME=CoffeeMaker
```

### Robot:
```env
WORKFLOW_ROBOT_IP=192.168.58.2
```

### Workflow Settings:
```env
WORKFLOW_FOLDER=workflows
DEFAULT_TIMEOUT=5.0
DEFAULT_RETRY_COUNT=1
```

## 📝 Cách Sử Dụng

### Sửa Config:

Mở file `workflow_config.env` và thay đổi các giá trị:

```env
# Thay đổi COM port
STIRRER_PORT=COM9

# Thay đổi robot IP
WORKFLOW_ROBOT_IP=192.168.1.100

# Thay đổi folder workflows
WORKFLOW_FOLDER=my_workflows
```

### Trong Code:

```python
from config_loader import get_robot_ip, get_iot_device_config

# Lấy robot IP
robot_ip = get_robot_ip()

# Lấy cấu hình device
stirrer_config = get_iot_device_config('STIRRER')
port = stirrer_config['port']
baudrate = stirrer_config['baudrate']
name = stirrer_config['name']
```

## ⚠️ Lưu Ý

- **KHÔNG sửa file `config.env` của Arm Controller**
- Chỉ sửa file `workflow_config.env` cho Workflow System
- Hai file config độc lập với nhau

## 📂 Workflow Files

Đặt tất cả các file workflow JSON vào folder `workflows/`:

```
workflows/
├── stirrer_workflow.json
├── coffee_workflow.json
└── ice_coffee_workflow.json
```

Load workflow từ folder:

```python
workflow_file = os.path.join('workflows', 'stirrer_workflow.json')
workflow.load_workflow_from_file(workflow_file)
```

## ✅ Hoàn Tất

Bây giờ Workflow System có:
- ✅ Config file riêng: `workflow_config.env`
- ✅ Folder riêng cho workflows: `workflows/`
- ✅ Không conflict với Arm Controller config

