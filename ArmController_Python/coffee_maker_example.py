#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coffee Maker Example - Ví dụ sử dụng workflow coordinator
Sử dụng để pha cà phê tuần tự với đảm bảo mỗi bước hoàn thành trước khi sang bước tiếp theo
"""

import os
import sys
import time

# Thêm đường dẫn các module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ArmController_Python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ArmController_Python', 'fairino_sdk'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IOTController_Python'))

from coffee_workflow_coordinator import CoffeeWorkflowCoordinator, robot_run_lua, iot_send_command, iot_wait_response

try:
    from fairino import Robot
except ImportError:
    print("⚠️ Không tìm thấy fairino SDK. Cần cài đặt SDK trước.")
    sys.exit(1)

from iot_controller import IoTController


def main():
    """Ví dụ workflow pha cà phê"""
    
    print("☕ COFFEE MAKER WORKFLOW EXAMPLE")
    print("=" * 70)
    print()
    
    # 1. Khởi tạo coordinator
    workflow = CoffeeWorkflowCoordinator()
    
    # 2. Kết nối Robot
    print("🔌 Kết nối Robot...")
    robot_ip = '192.168.58.2'  # Thay đổi IP nếu cần
    try:
        robot = Robot.RPC(robot_ip)
        workflow.connect_robot(robot)
        print("✅ Đã kết nối Robot")
    except Exception as e:
        print(f"❌ Lỗi kết nối Robot: {e}")
        return
    
    # 3. Kết nối thiết bị IoT (máy pha cà phê)
    print("🔌 Kết nối Máy pha cà phê...")
    try:
        coffee_maker = IoTController()
        coffee_maker.open('COM8', baudrate=115200)  # Thay đổi COM port nếu cần
        
        if coffee_maker.is_open():
            workflow.connect_iot_device('CoffeeMaker', coffee_maker)
            print("✅ Đã kết nối Máy pha cà phê")
        else:
            print("❌ Không thể mở COM port")
            return
    except Exception as e:
        print(f"❌ Lỗi kết nối Máy pha cà phê: {e}")
        # Tiếp tục demo mà không có IoT nếu cần
    
    print()
    
    # 4. Định nghĩa workflow các bước
    # BƯỚC 1: Robot di chuyển đến vị trí lấy cốc
    workflow.add_step(
        step_name="Robot lấy cốc",
        step_type='robot',
        action_func=robot_run_lua(robot, 'TakeCup.lua'),
        timeout=30.0
    )
    
    # BƯỚC 2: Robot đặt cốc vào máy pha cà phê
    workflow.add_step(
        step_name="Robot đặt cốc vào máy",
        step_type='robot',
        action_func=robot_run_lua(robot, 'MoveToMotor.lua'),
        timeout=30.0
    )
    
    # BƯỚC 3: Chờ robot hoàn thành đặt cốc (thêm delay)
    def wait_robot_position():
        """Đợi robot đặt cốc hoàn toàn"""
        time.sleep(2)  # Chờ 2 giây để robot ổn định vị trí
        return workflow.check_robot_complete(timeout=5)
    
    workflow.add_step(
        step_name="Xác nhận cốc đã đặt xong",
        step_type='robot',
        action_func=lambda: True,  # Không làm gì, chỉ đợi
        wait_func=lambda step_info: wait_robot_position(),
        timeout=5.0  # Giảm từ 10s xuống 5s
    )
    
    # BƯỚC 4: Bật máy pha cà phê
    if 'CoffeeMaker' in workflow.iot_devices:
        workflow.add_step(
            step_name="Bật máy pha cà phê",
            step_type='iot',
            action_func=iot_send_command('CoffeeMaker', '5'),  # Gửi lệnh "5"
            wait_func=iot_wait_response('CoffeeMaker', timeout=10.0),
            timeout=15.0
        )
        
        # BƯỚC 5: Chờ máy pha xong (đọc phản hồi từ máy)
        workflow.add_step(
            step_name="Đợi máy pha xong",
            step_type='iot',
            action_func=lambda: True,  # Không gửi gì, chỉ đợi response
            wait_func=iot_wait_response('CoffeeMaker', timeout=120.0),  # Chờ tối đa 2 phút
            timeout=130.0
        )
        
        # BƯỚC 6: Robot lấy cốc ra khỏi máy
        workflow.add_step(
            step_name="Robot lấy cốc ra khỏi máy",
            step_type='robot',
            action_func=robot_run_lua(robot, 'OutMotor.lua'),
            timeout=5.0  # Giảm từ 30s xuống 5s
        )
        
        # BƯỚC 7: Robot đưa cốc đến vị trí phục vụ
        workflow.add_step(
            step_name="Robot đưa cốc đến vị trí phục vụ",
            step_type='robot',
            action_func=robot_run_lua(robot, 'SpiralNNgang.lua'),
            timeout=5.0  # Giảm từ 30s xuống 5s
        )
    
    # 5. Chạy workflow
    print("🚀 Bắt đầu chạy workflow...")
    print()
    
    success = workflow.run_workflow()
    
    # 6. Hiển thị kết quả
    print()
    print("=" * 70)
    if success:
        print("🎉 THÀNH CÔNG! Đã pha xong cà phê!")
    else:
        print("❌ THẤT BẠI! Workflow bị dừng giữa chừng.")
    print("=" * 70)
    
    # 7. Hiển thị trạng thái
    status = workflow.get_status()
    print(f"\n📊 Trạng thái: {status['progress']} bước hoàn thành")
    print(f"✅ Các bước đã hoàn thành: {', '.join(status['completed_step_names'])}")
    
    # 8. Cleanup
    print("\n🧹 Đang dọn dẹp...")
    if robot:
        try:
            robot.CloseRPC()
        except:
            pass
    
    for device_name, controller in workflow.iot_devices.items():
        try:
            controller.close()
        except:
            pass
    
    print("✅ Hoàn thành!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Đã hủy workflow!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
