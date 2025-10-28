#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chạy Stirrer Workflow - Chạy máy khuấy tự động
"""

import os
import sys
import time

# Thêm đường dẫn các module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'ArmController_Python'))
sys.path.insert(0, os.path.join(current_dir, 'ArmController_Python', 'fairino_sdk'))
sys.path.insert(0, os.path.join(current_dir, 'IOTController_Python'))

# Import từ current directory (có load_workflow_from_file)
from coffee_workflow_coordinator import CoffeeWorkflowCoordinator
from config_loader import get_robot_ip, get_iot_device_config, get_workflow_folder

try:
    from fairino import Robot
    ROBOT_AVAILABLE = True
except ImportError:
    ROBOT_AVAILABLE = False
    print("⚠️ Không tìm thấy fairino SDK. Robot sẽ không chạy.")

from iot_controller import IoTController


def main():
    """Chạy Stirrer Workflow"""
    
    print("=" * 70)
    print("🌀 STIRRER WORKFLOW - Máy Khuấy Tự Động")
    print("=" * 70)
    print()
    
    # 1. Khởi tạo workflow coordinator
    workflow = CoffeeWorkflowCoordinator()
    
    # 2. Load workflow
    workflow_folder = get_workflow_folder()
    workflow_file = os.path.join(workflow_folder, "stirrer_workflow.json")
    
    print(f"📂 Đang load workflow từ: {workflow_file}")
    if not workflow.load_workflow_from_file(workflow_file):
        print("❌ Không thể load workflow!")
        return
    print(f"✅ Đã load workflow: {workflow.workflow_name}")
    print()
    
    # 3. Kết nối Robot
    if ROBOT_AVAILABLE:
        print("🤖 Kết nối Robot...")
        robot_ip = get_robot_ip()
        try:
            robot = Robot.RPC(robot_ip)
            workflow.connect_robot(robot)
            print(f"✅ Đã kết nối Robot: {robot_ip}")
        except Exception as e:
            print(f"❌ Lỗi kết nối Robot: {e}")
            return
    else:
        print("⚠️ Robot không khả dụng, bỏ qua bước robot")
    print()
    
    # 4. Kết nối thiết bị IoT (Stirrer)
    print("📡 Kết nối thiết bị Stirrer...")
    try:
        stirrer_config = get_iot_device_config('STIRRER')
        stirrer = IoTController()
        stirrer.open(stirrer_config['port'], baudrate=stirrer_config['baudrate'])
        
        if stirrer.is_open():
            workflow.connect_iot_device(stirrer_config['name'], stirrer)
            print(f"✅ Đã kết nối Stirrer: {stirrer_config['port']}")
        else:
            print(f"❌ Không thể mở COM port: {stirrer_config['port']}")
            return
    except Exception as e:
        print(f"❌ Lỗi kết nối Stirrer: {e}")
        return
    
    print()
    print("=" * 70)
    
    # 5. Chạy workflow
    print("🚀 BẮT ĐẦU CHẠY WORKFLOW")
    print("=" * 70)
    print()
    
    success = workflow.run_workflow()
    
    print()
    print("=" * 70)
    if success:
        print("🎉 WORKFLOW HOÀN THÀNH THÀNH CÔNG!")
    else:
        print("❌ WORKFLOW THẤT BẠI!")
    print("=" * 70)
    
    # 6. Hiển thị status cuối cùng
    status = workflow.get_status()
    print(f"📊 Tổng cộng: {status['completed_steps']}/{status['total_steps']} bước")
    print(f"⏱️ Thời gian: {status['elapsed_time']:.2f} giây")
    print()


if __name__ == "__main__":
    main()

