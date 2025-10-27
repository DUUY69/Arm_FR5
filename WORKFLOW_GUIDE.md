# 📋 WORKFLOW GUIDE - Hướng dẫn sử dụng Coffee Workflow Coordinator

## 🎯 Mục đích

Giải quyết vấn đề: **Đảm bảo mỗi bước hoàn thành trước khi chuyển sang bước tiếp theo**

Trong hệ thống pha cà phê tự động:
- ✅ Cánh tay robot lấy cốc xong **TRƯỚC KHI** máy pha chạy
- ✅ Máy pha pha xong **TRƯỚC KHI** robot lấy cốc ra
- ✅ Tránh tình trạng: Robot chưa đặt cốc mà máy đã chạy

## 🛠️ Cài đặt

Không cần cài đặt thêm, chỉ cần có các module sau:
- `coffee_workflow_coordinator.py` - Module chính
- `ArmController_Python/` - Điều khiển robot
- `IOTController_Python/` - Điều khiển thiết bị IoT

## 📖 Cách sử dụng

### 1. Import module

```python
from coffee_workflow_coordinator import CoffeeWorkflowCoordinator
```

### 2. Khởi tạo coordinator

```python
workflow = CoffeeWorkflowCoordinator()
```

### 3. Kết nối Robot và IoT

```python
# Kết nối Robot
from fairino import Robot
robot = Robot.RPC('192.168.58.2')
workflow.connect_robot(robot)

# Kết nối thiết bị IoT
from iot_controller import IoTController
iot_device = IoTController()
iot_device.open('COM8', baudrate=115200)
workflow.connect_iot_device('CoffeeMaker', iot_device)
```

### 4. Định nghĩa các bước

#### 4.1. Bước Robot (chạy Zoo scripts)

```python
from coffee_workflow_coordinator import robot_run_lua

workflow.add_step(
    step_name="Robot lấy cốc",
    step_type='robot',
    action_func=robot_run_lua(robot, 'TakeCup.lua'),
    timeout=30.0  # Timeout 30 giây
)
```

#### 4.2. Bước IoT (gửi lệnh đến thiết bị)

```python
from coffee_workflow_coordinator import iot_send_command, iot_wait_response

workflow.add_step(
    step_name="Bật máy pha cà phê",
    step_type='iot',
    action_func=iot_send_command('CoffeeMaker', '5'),  # Gửi lệnh "5"
    wait_func=iot_wait_response('CoffeeMaker', timeout=10.0),
    timeout=15.0
)
```

#### 4.3. Bước tùy chỉnh

```python
def my_custom_action():
    """Hành động tùy chỉnh"""
    # Làm gì đó
    return True  # True = thành công, False = thất bại

def my_custom_wait(step_info):
    """Đợi completion"""
    time.sleep(2)
    return True

workflow.add_step(
    step_name="Bước tùy chỉnh",
    step_type='robot',  # hoặc 'iot'
    action_func=my_custom_action,
    wait_func=my_custom_wait,
    timeout=30.0
)
```

### 5. Chạy workflow

```python
success = workflow.run_workflow()

if success:
    print("✅ Hoàn thành!")
else:
    print("❌ Thất bại!")
```

## 🔍 Kiểm tra trạng thái

### Robot State Check

Coordinator tự động Dùng nhiều method để kiểm tra:

1. **robot_state_pkg.program_state** - Kiểm tra program state
   - 0 = Idle (không chạy)
   - 1 = Running (đang chạy)
   - 2 = Paused (tạm dừng)
   - 3 = Error (lỗi)
   - 4 = Finished (hoàn thành)

2. **GetProgramState()** - Method RPC check program state

3. **CheckCommandFinish()** - Method check motion complete

4. **GetRobotMotionState()** - Method check motion state

### IoT Response Check

Coordinator đọc response từ thiết bị IoT qua serial port:

```python
# Tự động đọc frame response
response = controller.read_frame(timeout=10.0)
```

## 📝 Ví dụ hoàn chỉnh

Xem file `coffee_maker_example.py` để xem ví dụ đầy đủ.

### Workflow mẫu:

1. Robot lấy cốc (`TakeCup.lua`)
2. Robot đặt cốc vào máy (`MoveToMotor.lua`)
3. Xác nhận cốc đã đặt xong
4. Bật máy pha cà phê (gửi lệnh "5" qua IoT)
5. Đợi máy pha xong (đọc response từ IoT)
6. Robot lấy cốc ra (`OutMotor.lua`)
7. Robot đưa cốc đến vị trí phục vụ (`SpiralNNgang.lua`)

## 🐛 Debug

### Enable logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Xem trạng thái

```python
status = workflow.get_status()
print(status)
# Output:
# {
#     'total_steps': 7,
#     'completed_steps': 3,
#     'current_step': 3,
#     'progress': '3/7',
#     'completed_step_names': ['Robot lấy cốc', 'Robot đặt cốc vào máy', ...]
# }
```

### Lỗi thường gặp

1. **Timeout**: Tăng `timeout` trong `add_step()`
2. **Robot không connect**: Kiểm tra IP và kết nối mạng
3. **IoT không có response**: Kiểm tra COM port và baudrate
4. **Lua file không tìm thấy**: Upload file lên robot trước

## 🎓 Best Practices

1. **Luôn set timeout phù hợp**: 
   - Robot motion: 10-30 giây
   - IoT response: 5-15 giây
   - Long operations: 60-120 giây

2. **Test từng bước trước**: 
   ```python
   # Test chỉ bước đầu tiên
   workflow.run_step(0)
   ```

3. **Handle errors**:
   ```python
   try:
       success = workflow.run_workflow()
   except Exception as e:
       print(f"Error: {e}")
   ```

4. **Logging**: Bật logging để track tiến trình

5. **Cleanup**: Luôn đóng kết nối sau khi xong
   ```python
   robot.CloseRPC()
   iot_device.close()
   ```

## 🚀 Nâng cao

### Custom wait function

```python
def smart_wait(step_info):
    """Wait function thông minh"""
    max_attempts = 10
    for i in range(max_attempts):
        if workflow.check_robot_complete(timeout=1):
            return True
        # Thử lại
        time.sleep(0.5)
    return False

workflow.add_step(
    step_name="Smart step",
    step_type='robot',
    action_func=my_action,
    wait_func=smart_wait,
    timeout=60.0
)
```

### Parallel operations (nâng cao)

```python
# Nếu cần chạy nhiều thiết bị IoT cùng lúc
import threading

def run_parallel():
    results = []
    threads = []
    
    for device in devices:
        t = threading.Thread(target=device.start)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        results.append(True)
    
    return all(results)
```

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra log messages
2. Kiểm tra kết nối Robot/IoT
3. Kiểm tra timeout settings
4. Xem ví dụ trong `coffee_maker_example.py`

---

**Tác giả**: Generated for Arm_FR5 Coffee Maker Project  
**Version**: 1.0  
**Date**: 2025
