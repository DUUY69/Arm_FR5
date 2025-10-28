# 🚀 Workflow System - Hệ Thống Quản Lý Workflow Nâng Cao

## 📋 Tổng Quan

Hệ thống Workflow cho phép tạo, quản lý và thực thi các quy trình phức tạp với khả năng:
- ✅ Thêm/Sửa/Xóa các bước workflow
- ✅ Export/Import JSON
- ✅ Error handling và retry
- ✅ Conditional steps
- ✅ Parallel execution
- ✅ Workflow registry
- ✅ Status tracking chi tiết

## 🎯 Tính Năng Chính

### 1. **Quản Lý Bước Workflow**

#### Thêm Bước Mới:
```python
workflow.add_step_advanced(
    step_id="grab_cup",
    step_name="Robot lấy cốc",
    step_type="robot",
    action_config={'type': 'run_lua', 'file': 'TakeCup.lua'},
    wait_config={'type': 'robot_complete', 'timeout': 3.0},
    timeout=5.0
)
```

#### Sửa Bước:
```python
workflow.update_step("grab_cup", name="grab_cup_v2", timeout=10.0)
```

#### Xóa Bước:
```python
workflow.delete_step("grab_cup")
```

#### Di Chuyển Bước:
```python
workflow.move_step("grab_cup", 0)  # Di chuyển lên đầu
```

#### Nhân Bản Bước:
```python
workflow.duplicate_step("grab_cup", "grab_cup_2")
```

### 2. **Các Loại Action Hỗ Trợ**

#### Robot Actions:
- `run_lua`: Chạy file Lua script
- `move_to_position`: Di chuyển đến vị trí cụ thể
- `gripper_open`: Mở gripper
- `gripper_close`: Đóng gripper

#### IoT Actions:
- `send_command`: Gửi lệnh đến thiết bị IoT
- `read_sensor`: Đọc giá trị sensor
- `set_parameter`: Thiết lập tham số

#### Utility Actions:
- `delay`: Chờ một khoảng thời gian

### 3. **Wait Types**

- `robot_complete`: Đợi robot hoàn thành
- `iot_response`: Đợi response từ IoT
- `time_delay`: Đợi thời gian cố định
- `condition_check`: Kiểm tra điều kiện

### 4. **Conditional Steps**

Cho phép chuyển hướng workflow dựa trên điều kiện:

```python
workflow.add_step_advanced(
    step_id="check_cup",
    step_name="Kiểm tra cốc",
    step_type="condition",
    action_config={'type': 'default'},
    wait_config={
        'type': 'condition_check',
        'condition': {
            'type': 'sensor_value',
            'device': 'CoffeeMaker',
            'sensor': 'cup_detector',
            'operator': '>',
            'value': 0
        }
    },
    timeout=3.0
)
```

Trong JSON:
```json
{
  "id": "check_cup",
  "type": "condition",
  "condition": {
    "type": "sensor_value",
    "device": "CoffeeMaker",
    "sensor": "cup_detector",
    "operator": ">",
    "value": 0
  },
  "if_true": "start_brewing",
  "if_false": "adjust_cup"
}
```

### 5. **Parallel Execution**

Chạy nhiều bước song song:

```python
workflow.add_step_advanced(
    step_id="parallel_actions",
    step_name="Chạy song song",
    step_type="parallel",
    action_config={'type': 'default'},
    wait_config={'type': 'default'},
    timeout=30.0
)
```

Trong JSON:
```json
{
  "id": "parallel_actions",
  "type": "parallel",
  "parallel_steps": ["step_1", "step_2", "step_3"]
}
```

### 6. **Error Handling**

Retry và fallback khi gặp lỗi:

```python
# Trong JSON
{
  "on_error": {
    "retry_count": 3,
    "retry_delay": 2.0,
    "fallback_step": "emergency_stop"
  }
}

# Khi chạy workflow
workflow.run_workflow(stop_on_error=False, retry_count=3)
```

### 7. **JSON Export/Import**

#### Export:
```python
# Export ra string
json_data = workflow.export_workflow_to_json()

# Save ra file
workflow.save_workflow_to_file("my_workflow.json")
```

#### Import:
```python
# Từ file
workflow.load_workflow_from_file("my_workflow.json")

# Từ string
workflow.import_workflow_from_json(json_data)
```

### 8. **Workflow Registry**

Đăng ký và quản lý nhiều workflow:

```python
# Đăng ký workflow
workflow.register_workflow("Coffee Basic")

# List workflows
workflows = workflow.list_registered_workflows()

# Load workflow đã đăng ký
workflow.load_registered_workflow("Coffee Basic")

# Hủy đăng ký
workflow.unregister_workflow("Coffee Basic")
```

### 9. **Status Tracking**

Theo dõi tiến độ workflow chi tiết:

```python
status = workflow.get_status()
# {
#   'workflow_name': 'Coffee Making',
#   'total_steps': 6,
#   'completed_steps': 3,
#   'current_step': 3,
#   'progress': '3/6',
#   'progress_percentage': 50.0,
#   'elapsed_time': 45.2,
#   'status': 'running',
#   'completed_step_names': ['Step 1', 'Step 2', 'Step 3'],
#   'current_step_name': 'Bật máy'
# }
```

## 📖 Ví Dụ Sử Dụng

### Ví Dụ 1: Tạo Workflow Đơn Giản

```python
from coffee_workflow_coordinator import CoffeeWorkflowCoordinator

# 1. Tạo workflow
workflow = CoffeeWorkflowCoordinator()
workflow.set_workflow_metadata("Coffee Making", "1.0", "Pha cà phê tự động")

# 2. Kết nối thiết bị
# workflow.connect_robot(robot)
# workflow.connect_iot_device("CoffeeMaker", iot_controller)

# 3. Thêm các bước
import uuid

workflow.add_step_advanced(
    step_id=str(uuid.uuid4()),
    step_name="Lấy cốc",
    step_type="robot",
    action_config={'type': 'run_lua', 'file': 'TakeCup.lua'},
    wait_config={'type': 'robot_complete', 'timeout': 3.0},
    timeout=5.0
)

workflow.add_step_advanced(
    step_id=str(uuid.uuid4()),
    step_name="Bật máy pha",
    step_type="iot",
    action_config={'type': 'send_command', 'device': 'CoffeeMaker', 'command': 'START'},
    wait_config={'type': 'iot_response', 'device': 'CoffeeMaker', 'timeout': 15.0},
    timeout=20.0
)

# 4. Chạy workflow
# workflow.run_workflow()

# 5. Export workflow
workflow.save_workflow_to_file("coffee_workflow.json")
```

### Ví Dụ 2: Sử Dụng Template

```python
workflow = CoffeeWorkflowCoordinator()

# Tạo workflow từ template
workflow.create_coffee_workflow_template()

# Hoặc tạo ice coffee workflow
# workflow.create_ice_coffee_workflow_template()

# Đăng ký và save
workflow.register_workflow("My Coffee Workflow")

# Load lại sau đó
workflow.load_registered_workflow("My Coffee Workflow")
```

### Ví Dụ 3: Load từ JSON

```python
workflow = CoffeeWorkflowCoordinator()

# Load workflow từ file JSON
workflow.load_workflow_from_file("example_workflow_coffee.json")

# Hoặc từ JSON string
json_string = '''
{
  "workflow_name": "My Workflow",
  "steps": [
    {
      "id": "step1",
      "name": "Step 1",
      "type": "delay",
      "action_config": {"type": "delay", "delay": 2.0},
      "wait_config": {"type": "default"},
      "timeout": 5.0
    }
  ]
}
'''
workflow.import_workflow_from_json(json_string)
```

## 📊 Cấu Trúc JSON Workflow

```json
{
  "workflow_id": "unique-id",
  "workflow_name": "Workflow Name",
  "workflow_version": "1.0",
  "workflow_description": "Description",
  "steps": [
    {
      "id": "step_id",
      "name": "Step Name",
      "type": "robot|iot|condition|parallel",
      "action_config": {
        "type": "run_lua|send_command|delay|...",
        // ... các tham số khác
      },
      "wait_config": {
        "type": "robot_complete|iot_response|condition_check|...",
        "timeout": 5.0
      },
      "timeout": 10.0,
      "on_error": {
        "retry_count": 3,
        "retry_delay": 2.0,
        "fallback_step": "emergency_stop"
      },
      "condition": {  // Cho conditional step
        "type": "sensor_value",
        "device": "CoffeeMaker",
        "sensor": "sensor_name",
        "operator": ">",
        "value": 0
      },
      "if_true": "next_step_id",
      "if_false": "other_step_id",
      "parallel_steps": ["step1", "step2"]  // Cho parallel step
    }
  ]
}
```

## 🔧 Cấu Hình Timeout

- **Robot simple motion**: 3-5 giây
- **Robot complex path**: 10-15 giây
- **IoT device response**: 10 giây
- **Long operations**: 60-120 giây

## ⚠️ Lưu Ý

1. **UUID cho Step ID**: Sử dụng `uuid.uuid4()` để tạo ID duy nhất
2. **Error Handling**: Luôn set `retry_count` và `fallback_step` cho critical steps
3. **Parallel Steps**: Đảm bảo các steps chạy song song không conflict với nhau
4. **Conditional Logic**: Test kỹ logic điều kiện trước khi deploy

## 🎉 Kết Luận

Hệ thống Workflow này cung cấp một framework mạnh mẽ và linh hoạt để quản lý các quy trình phức tạp, với khả năng tái sử dụng, mở rộng và maintain dễ dàng!

