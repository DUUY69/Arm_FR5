#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coffee Workflow Coordinator
Quản lý workflow pha cà phê tuần tự với kiểm tra trạng thái hoàn thành

Giải quyết vấn đề: Đảm bảo mỗi bước hoàn thành trước khi chuyển sang bước tiếp theo
- Robot arm: Kiểm tra program/motion completed
- IoT devices: Đợi response/confirmation trước khi tiếp tục
"""

import os
import sys
import time
import threading
from typing import Dict, List, Callable, Optional, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CoffeeWorkflowCoordinator:
    """Quản lý workflow pha cà phê tuần tự"""
    
    def __init__(self):
        self.steps: List[Dict] = []
        self.current_step = 0
        self.robot_connected = False
        self.iot_devices = {}
        self.completed_steps = []
        
    def add_step(self, step_name: str, step_type: str, action_func: Callable, 
                 wait_func: Optional[Callable] = None, timeout: float = 30.0):
        """
        Thêm một bước vào workflow
        
        Args:
            step_name: Tên mô tả bước
            step_type: 'robot' hoặc 'iot'
            action_func: Function để thực hiện bước (trả về True nếu thành công)
            wait_func: Function để kiểm tra hoàn thành (trả về True khi hoàn thành)
            timeout: Thời gian timeout (giây)
        """
        step = {
            'name': step_name,
            'type': step_type,
            'action': action_func,
            'wait': wait_func or self._default_wait,
            'timeout': timeout
        }
        self.steps.append(step)
        logger.info(f"✅ Đã thêm bước: {step_name} (type: {step_type})")
    
    def connect_robot(self, robot_instance):
        """Kết nối robot instance"""
        self.robot = robot_instance
        self.robot_connected = True
        logger.info("✅ Đã kết nối robot")
    
    def connect_iot_device(self, device_name: str, iot_controller):
        """Kết nối thiết bị IoT"""
        self.iot_devices[device_name] = iot_controller
        logger.info(f"✅ Đã kết nối thiết bị IoT: {device_name}")
    
    def check_robot_complete(self, timeout: float = 3.0) -> bool:
        """
        Kiểm tra xem robot có hoàn thành chương trình/motion không (timeout mặc định 3 giây)
        
        Returns:
            True nếu robot đã hoàn thành, False nếu timeout hoặc lỗi
        """
        if not self.robot_connected:
            logger.error("❌ Robot chưa được kết nối!")
            return False
        
        logger.info(f"⏳ Đang kiểm tra robot hoàn thành (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Method 1: Kiểm tra robot_state_pkg.program_state
                if hasattr(self.robot, 'robot_state_pkg'):
                    program_state = self.robot.robot_state_pkg.program_state
                    logger.info(f"📊 Program State: {program_state}")
                    
                    # program_state: 0 = idle, 1 = running, 2 = paused, 3 = error, 4 = finished
                    if program_state == 0 or program_state == 4:
                        logger.info("✅ Robot đã hoàn thành! (robot_state_pkg)")
                        return True
                    
                    # Nếu state là 3 (error), báo lỗi
                    if program_state == 3:
                        logger.error("❌ Robot gặp lỗi!")
                        return False
                
                # Method 2: GetProgramState
                if hasattr(self.robot, 'GetProgramState'):
                    try:
                        result = self.robot.GetProgramState()
                        if isinstance(result, tuple):
                            err, state = result
                            if err == 0 and state == 0:  # 0 = finished/idle
                                logger.info("✅ Robot đã hoàn thành! (GetProgramState)")
                                return True
                        elif int(result) == 0:
                            logger.info("✅ Robot đã hoàn thành! (GetProgramState)")
                            return True
                    except Exception as e:
                        logger.debug(f"GetProgramState error: {e}")
                
                # Method 3: CheckCommandFinish
                if hasattr(self.robot, 'CheckCommandFinish'):
                    try:
                        result = self.robot.CheckCommandFinish()
                        if isinstance(result, tuple):
                            err, finished = result
                            if err == 0 and finished:
                                logger.info("✅ Robot đã hoàn thành! (CheckCommandFinish)")
                                return True
                        elif result:
                            logger.info("✅ Robot đã hoàn thành! (CheckCommandFinish)")
                            return True
                    except Exception as e:
                        logger.debug(f"CheckCommandFinish error: {e}")
                
                # Method 4: GetRobotMotionState (nếu có)
                if hasattr(self.robot, 'GetRobotMotionState'):
                    try:
                        result = self.robot.GetRobotMotionState()
                        logger.info(f"📊 Motion State: {result}")
                        # Nếu motion state == 0 (idle), có thể robot đã xong
                        # (Tùy implementation của SDK)
                    except Exception as e:
                        logger.debug(f"GetRobotMotionState error: {e}")
                
                # Chờ một chút trước khi kiểm tra lại (giảm từ 0.3s xuống 0.1s để nhanh hơn)
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Lỗi kiểm tra robot: {e}")
                return False
        
        # Timeout
        logger.warning(f"⚠️ Timeout kiểm tra robot ({timeout}s)")
        return False
    
    def check_iot_complete(self, device_name: str, expected_response: bytes = None, 
                          timeout: float = 10.0) -> bool:
        """
        Kiểm tra xem thiết bị IoT có gửi phản hồi hoàn thành không
        
        Args:
            device_name: Tên thiết bị IoT
            expected_response: Byte response mong đợi (None = bất kỳ response nào)
            timeout: Timeout (giây)
        
        Returns:
            True nếu nhận được response, False nếu timeout
        """
        if device_name not in self.iot_devices:
            logger.error(f"❌ Thiết bị IoT '{device_name}' chưa được kết nối!")
            return False
        
        controller = self.iot_devices[device_name]
        if not controller.is_open():
            logger.error(f"❌ Thiết bị IoT '{device_name}' chưa mở port!")
            return False
        
        logger.info(f"⏳ Đang đợi response từ {device_name} (timeout: {timeout}s)...")
        
        try:
            # Đọc frame phản hồi
            response = controller.read_frame(timeout)
            
            if response:
                logger.info(f"📥 Nhận response từ {device_name}: {response.hex().upper()}")
                
                # Nếu có expected_response, kiểm tra khớp
                if expected_response:
                    if response == expected_response:
                        logger.info("✅ Response khớp với mong đợi!")
                        return True
                    else:
                        logger.warning(f"⚠️ Response không khớp. Expected: {expected_response.hex().upper()}")
                        return False
                
                # Nếu không có expected_response, coi như hoàn thành khi có response bất kỳ
                return True
            else:
                logger.warning("⚠️ Không nhận được response")
                return False
                
        except Exception as e:
            logger.error(f"❌ Lỗi đọc IoT response: {e}")
            return False
    
    def _default_wait(self, step_info: Dict) -> bool:
        """Default wait function nếu không có wait_func cụ thể"""
        if step_info['type'] == 'robot':
            return self.check_robot_complete(step_info['timeout'])
        elif step_info['type'] == 'iot':
            # Tìm device name từ step_info
            device_name = step_info.get('device', 'default')
            return self.check_iot_complete(device_name, step_info.get('expected_response'), 
                                         step_info['timeout'])
        return True
    
    def run_step(self, step_index: int) -> bool:
        """
        Chạy một bước cụ thể
        
        Args:
            step_index: Index của bước cần chạy
        
        Returns:
            True nếu bước hoàn thành, False nếu lỗi
        """
        if step_index >= len(self.steps):
            logger.error(f"❌ Bước {step_index} không tồn tại!")
            return False
        
        step = self.steps[step_index]
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 BƯỚC {step_index + 1}/{len(self.steps)}: {step['name']}")
        logger.info(f"{'='*70}")
        
        try:
            # 1. Thực hiện action
            logger.info(f"▶️ Đang thực hiện: {step['name']}...")
            action_result = step['action']()
            
            if not action_result:
                logger.error(f"❌ Action '{step['name']}' thất bại!")
                return False
            
            logger.info(f"✅ Action '{step['name']}' đã hoàn thành")
            
            # 2. Đợi confirmation
            logger.info(f"⏳ Đang đợi confirmation cho '{step['name']}'...")
            wait_result = step['wait'](step)
            
            if not wait_result:
                logger.error(f"❌ Không nhận được confirmation cho '{step['name']}'!")
                return False
            
            logger.info(f"✅ Confirmation nhận được cho '{step['name']}'")
            
            # 3. Đánh dấu hoàn thành
            self.completed_steps.append({
                'index': step_index,
                'name': step['name'],
                'timestamp': time.time()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi trong bước '{step['name']}': {e}")
            return False
    
    def run_workflow(self) -> bool:
        """
        Chạy toàn bộ workflow tuần tự
        
        Returns:
            True nếu toàn bộ workflow thành công, False aix error
            
        """
        if not self.steps:
            logger.error("❌ Workflow trống!")
            return False
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎬 BẮT ĐẦU WORKFLOW PHA CÀ PHÊ")
        logger.info(f"📋 Tổng cộng {len(self.steps)} bước")
        logger.info(f"{'='*70}\n")
        
        self.current_step = 0
        self.completed_steps = []
        
        for i, step in enumerate(self.steps):
            self.current_step = i
            success = self.run_step(i)
            
            if not success:
                logger.error(f"\n❌ WORKFLOW THẤT BẠI tại bước {i + 1}: {step['name']}")
                return False
            
            logger.info(f"✅ Bước {i + 1} hoàn thành. Tiếp tục...\n")
            time.sleep(1)  # Chờ 1 giây giữa các bước
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 WORKFLOW HOÀN THÀNH!")
        logger.info(f"✅ Đã hoàn thành {len(self.completed_steps)}/{len(self.steps)} bước")
        logger.info(f"{'='*70}\n")
        
        return True
    
    def get_status(self) -> Dict:
        """Lấy trạng thái hiện tại của workflow"""
        return {
            'total_steps': len(self.steps),
            'completed_steps': len(self.completed_steps),
            'current_step': self.current_step,
            'progress': f"{len(self.completed_steps)}/{len(self.steps)}",
            'completed_step_names': [s['name'] for s in self.completed_steps]
        }


# Helper functions cho các bước thường dùng
def robot_run_lua(robot, lua_filename: str):
    """Helper: Chạy file Lua trên robot"""
    def action():
        try:
            logger.info(f"🤖 Chạy Lua script: {lua_filename}")
            remote_path = f"/fruser/{lua_filename}"
            
            # Load program
            if hasattr(robot, 'ProgramLoad'):
                load_result = robot.ProgramLoad(remote_path)
                logger.info(f"ProgramLoad result: {load_result}")
                
                if int(load_result) == 0:
                    # Run program
                    run_result = robot.ProgramRun()
                    logger.info(f"ProgramRun result: {run_result}")
                    return int(run_result) == 0
                else:
                    logger.error(f"ProgramLoad failed: {load_result}")
                    return False
            else:
                logger.error("Robot không có method ProgramLoad!")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi chạy Lua: {e}")
            return False
    
    return action


def iot_send_command(device_name: str, command: str):
    """Helper: Gửi lệnh đến thiết bị IoT"""
    def action():
        try:
            # Get coordinator instance from current scope
            coordinator = None
            if device_name not in coordinator.iot_devices:
                logger.error(f"❌ Thiết bị '{device_name}' chưa kết nối!")
                return False
            
            controller = coordinator.iot_devices[device_name]
            logger.info(f"📤 Gửi lệnh đến {device_name}: {command}")
            
            # Chuyển command thành bytes
            if command.upper() == "GO":
                data = b"GO"
            elif command.isdigit():
                data = command.encode('ascii')
            else:
                data = command.encode('ascii')
            
            if hasattr(controller, '_ser') and controller._ser and controller._ser.is_open:
                written = controller._ser.write(data)
                controller._ser.flush()
                logger.info(f"📤 Đã gửi {written} bytes")
                return written > 0
            else:
                logger.error("❌ Serial port chưa mở!")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi gửi IoT command: {e}")
            return False
    
    return action


def iot_wait_response(device_name: str, timeout: float = 10.0):
    """Helper: Đợi response từ thiết bị IoT"""
    def wait(step_info):
        step_info['device'] = device_name
        step_info['timeout'] = timeout
        coordinator = CoffeeWorkflowCoordinator.__instance if hasattr(CoffeeWorkflowCoordinator, '__instance') else None
        if coordinator:
            return coordinator.check_iot_complete(device_name, timeout=timeout)
        return True
    
    return wait


# Export
__all__ = ['CoffeeWorkflowCoordinator', 'robot_run_lua', 'iot_send_command', 'iot_wait_response']
