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
import json
import uuid
from typing import Dict, List, Callable, Optional, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CoffeeWorkflowCoordinator:
    """Quản lý workflow pha cà phê tuần tự với khả năng thêm/sửa/xóa bước"""
    
    def __init__(self):
        self.steps: List[Dict] = []
        self.current_step = 0
        self.robot_connected = False
        self.iot_devices = {}
        self.completed_steps = []
        
        # Workflow metadata
        self.workflow_name = "Default Workflow"
        self.workflow_version = "1.0"
        self.workflow_description = ""
        self.workflow_id = str(uuid.uuid4())
        
        # Workflow registry để lưu các workflow đã tạo
        self.workflow_registry = {}
        
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
        # Lưu với nhiều biến thể tên để tránh lỗi hoa/thường
        self.iot_devices[device_name] = iot_controller
        self.iot_devices[device_name.upper()] = iot_controller
        self.iot_devices[device_name.lower()] = iot_controller
        logger.info(f"✅ Đã kết nối thiết bị IoT: {device_name}")
    
    def check_robot_complete(self, timeout: float = 12.0) -> bool:
        """
        Kiểm tra xem robot có hoàn thành chương trình/motion không (timeout mặc định 3 giây)
        
        Returns:
            True nếu robot đã hoàn thành, False nếu timeout hoặc lỗi
        """
        if not self.robot_connected:
            logger.error("❌ Robot chưa được kết nối!")
            return False
        
        logger.info(f"⏳ Đang kiểm tra robot hoàn thành (timeout: {timeout}s)...")
        # Detect XML-RPC ServerProxy (mọi thuộc tính đều 'tồn tại')
        is_xmlrpc_proxy = 'ServerProxy' in type(self.robot).__name__
        # Pre-detect capability: nếu không có bất kỳ API trạng thái nào callable, fallback chờ
        has_state_pkg = (not is_xmlrpc_proxy) and hasattr(self.robot, 'robot_state_pkg')
        has_get_program_state = callable(getattr(self.robot, 'GetProgramState', None))
        has_check_finish = callable(getattr(self.robot, 'CheckCommandFinish', None))
        has_motion_state = callable(getattr(self.robot, 'GetRobotMotionState', None))
        has_alternatives = any(callable(getattr(self.robot, n, None)) for n in ("ProgramState", "GetProgramRunState", "IsProgramRunning"))
        if not (has_state_pkg or has_get_program_state or has_check_finish or has_motion_state or has_alternatives):
            logger.info("ℹ️ Không có API trạng thái chương trình trên controller (XML-RPC tối giản). Fallback: chờ timeout rồi coi như hoàn thành.")
            try:
                time.sleep(max(0.5, float(timeout)))
            except Exception:
                pass
            return True
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Method 1: Kiểm tra robot_state_pkg.program_state
                if has_state_pkg:
                    try:
                        program_state = self.robot.robot_state_pkg.program_state
                        logger.info(f"📊 Program State: {program_state}")
                        # program_state: 0 = idle, 1 = running, 2 = paused, 3 = error, 4 = finished
                        if program_state in (0, 4):
                            logger.info("✅ Robot đã hoàn thành! (robot_state_pkg)")
                            return True
                        if program_state == 3:
                            logger.error("❌ Robot gặp lỗi!")
                            return False
                    except Exception:
                        # Nếu truy cập không hợp lệ, bỏ qua phương pháp này
                        pass
                
                # Method 2: GetProgramState
                if has_get_program_state:
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
                # Method 2b: Một số firmware khác tên API
                for alt_name in ('ProgramState', 'GetProgramRunState', 'IsProgramRunning'):
                    if callable(getattr(self.robot, alt_name, None)):
                        try:
                            val = getattr(self.robot, alt_name)()
                            # Heuristics: bool False or int 0 => not running => complete
                            if isinstance(val, tuple):
                                # (err, state)
                                err, state = val[0], val[1] if len(val) > 1 else None
                                if err == 0 and (state in (0, False, None)):
                                    logger.info(f"✅ Robot đã hoàn thành! ({alt_name})")
                                    return True
                            else:
                                if val in (0, False, None):
                                    logger.info(f"✅ Robot đã hoàn thành! ({alt_name})")
                                    return True
                        except Exception:
                            pass
                
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
                if has_motion_state:
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
        # Nếu là XML-RPC proxy (không có API trạng thái đáng tin), coi như hoàn thành
        if 'ServerProxy' in type(self.robot).__name__:
            logger.info("ℹ️ XML-RPC proxy không cung cấp trạng thái tin cậy → coi như hoàn thành")
            return True
        return False
    
    def check_iot_complete(self, device_name: str, expected_response: bytes = None, 
                         timeout: Optional[float] = 10.0, prefer_raw: bool = False) -> bool:
        """
        Kiểm tra xem thiết bị IoT có gửi phản hồi hoàn thành không
        
        Args:
            device_name: Tên thiết bị IoT
            expected_response: Byte response mong đợi (None = bất kỳ response nào)
            timeout: Timeout (giây)
        
        Returns:
            True nếu nhận được response, False nếu timeout
        """
        controller = (
            self.iot_devices.get(device_name)
            or self.iot_devices.get(device_name.upper())
            or self.iot_devices.get(device_name.lower())
        )
        if not controller:
            logger.error(f"❌ Thiết bị IoT '{device_name}' chưa được kết nối!")
            return False
        if not controller.is_open():
            logger.error(f"❌ Thiết bị IoT '{device_name}' chưa mở port!")
            return False
        
        if timeout is None:
            logger.info(f"⏳ Đang đợi response từ {device_name} (không timeout)...")
        else:
            logger.info(f"⏳ Đang đợi response từ {device_name} (timeout: {timeout}s)...")
        
        try:
            # Chế độ ưu tiên RAW: không yêu cầu frame, chỉ cần bất kỳ bytes (hoặc khớp expected)
            if prefer_raw and hasattr(controller, '_ser') and getattr(controller, '_ser') and controller._ser.is_open:
                ser = controller._ser
                start_time = time.time()
                while True:
                    if ser.in_waiting > 0:
                        response = ser.read(ser.in_waiting)
                        if response:
                            logger.info(f"📥 Nhận RAW response từ {device_name}: {response.hex().upper()}")
                            if expected_response:
                                if response == expected_response:
                                    logger.info("✅ RAW response khớp expected")
                                    return True
                                else:
                                    logger.warning("⚠️ RAW response không khớp expected")
                                    return False
                            return True
                    if timeout is not None and (time.time() - start_time) > timeout:
                        logger.warning("⚠️ RAW wait timeout")
                        return False
                    time.sleep(0.1)

            # Đọc frame phản hồi (có fallback RAW ngắn)
            if timeout is None:
                # Chờ vô hạn cho đến khi có frame
                while True:
                    response = controller.read_frame(2.0)
                    # Fallback: nếu không có frame, kiểm tra raw bytes
                    if (not response) and hasattr(controller, '_ser') and getattr(controller, '_ser') and controller._ser.is_open:
                        if controller._ser.in_waiting > 0:
                            response = controller._ser.read(controller._ser.in_waiting)
                    if response:
                        break
                    time.sleep(0.1)
            else:
                response = controller.read_frame(timeout)
                if (not response) and hasattr(controller, '_ser') and getattr(controller, '_ser') and controller._ser.is_open:
                    if controller._ser.in_waiting > 0:
                        response = controller._ser.read(controller._ser.in_waiting)
            
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
        Chạy toàn bộ workflow tuần tự (phiên bản đơn giản, ổn định)
        """
        if not self.steps:
            logger.error("❌ Workflow trống!")
            return False
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎬 BẮT ĐẦU WORKFLOW: {self.workflow_name}")
        logger.info(f"📋 Tổng cộng {len(self.steps)} bước")
        logger.info(f"{'='*70}\n")
        
        self.current_step = 0
        self.completed_steps = []
        self.workflow_start_time = time.time()
        
        for i, _ in enumerate(self.steps):
            self.current_step = i
            success = self.run_step(i)
            if not success:
                step_name = self.steps[i].get('name', f'Step_{i}')
                logger.error(f"\n❌ WORKFLOW THẤT BẠI tại bước {i + 1}: {step_name}")
                return False
            logger.info(f"✅ Bước {i + 1} hoàn thành. Tiếp tục...\n")
        
        elapsed_time = time.time() - self.workflow_start_time
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 WORKFLOW HOÀN THÀNH!")
        logger.info(f"✅ Đã hoàn thành {len(self.completed_steps)}/{len(self.steps)} bước")
        logger.info(f"⏱️ Thời gian thực hiện: {elapsed_time:.2f} giây")
        logger.info(f"{'='*70}\n")
        
        return True
    
    def _handle_conditional_step(self, step: Dict, step_index: int) -> str:
        """Xử lý conditional step"""
        condition_config = step.get('condition', {})
        if_true = step.get('if_true')
        if_false = step.get('if_false')
        
        # Kiểm tra điều kiện
        condition_result = self._check_condition(condition_config)
        
        if condition_result:
            logger.info(f"✅ Điều kiện đúng, chuyển sang: {if_true}")
            # Tìm và chuyển đến step if_true
            if if_true:
                target_index = self._find_step_by_id(if_true)
                if target_index != -1:
                    self.current_step = target_index - 1  # -1 vì loop sẽ tăng lên 1
            return 'success'
        else:
            logger.info(f"❌ Điều kiện sai, chuyển sang: {if_false}")
            # Tìm và chuyển đến step if_false
            if if_false:
                target_index = self._find_step_by_id(if_false)
                if target_index != -1:
                    self.current_step = target_index - 1
            return 'skip'
    
    def _handle_parallel_step(self, step: Dict, step_index: int) -> bool:
        """Xử lý parallel step - chạy nhiều bước song song"""
        parallel_step_ids = step.get('parallel_steps', [])
        
        if not parallel_step_ids:
            logger.warning("⚠️ Parallel step không có step nào để chạy")
            return True
        
        logger.info(f"🔄 Chạy song song {len(parallel_step_ids)} bước...")
        
        # Tìm các step cần chạy
        steps_to_run = []
        for step_id in parallel_step_ids:
            target_index = self._find_step_by_id(step_id)
            if target_index != -1:
                steps_to_run.append(target_index)
        
        # Chạy song song bằng threading
        results = {}
        
        def run_step_thread(step_idx):
            results[step_idx] = self.run_step(step_idx)
        
        threads = []
        for step_idx in steps_to_run:
            thread = threading.Thread(target=run_step_thread, args=(step_idx,))
            thread.start()
            threads.append(thread)
        
        # Đợi tất cả threads hoàn thành
        for thread in threads:
            thread.join(timeout=300)  # Timeout 5 phút
        
        # Kiểm tra kết quả
        all_success = all(results.values())
        
        if all_success:
            logger.info("✅ Tất cả parallel steps đã hoàn thành")
        else:
            logger.error("❌ Một số parallel steps thất bại")
        
        return all_success
    
    def _execute_fallback(self, fallback_step_id: str) -> bool:
        """Thực thi fallback step khi có lỗi"""
        fallback_index = self._find_step_by_id(fallback_step_id)
        if fallback_index == -1:
            logger.error(f"❌ Không tìm thấy fallback step: {fallback_step_id}")
            return False
        
        logger.info(f"🔄 Đang thực thi fallback step: {fallback_step_id}")
        return self.run_step(fallback_index)
    
    def get_status(self) -> Dict:
        """Lấy trạng thái hiện tại của workflow chi tiết"""
        elapsed_time = 0
        if hasattr(self, 'workflow_start_time'):
            elapsed_time = time.time() - self.workflow_start_time
        
        progress_percentage = 0
        if len(self.steps) > 0:
            progress_percentage = (len(self.completed_steps) / len(self.steps)) * 100
        
        return {
            'workflow_name': self.workflow_name,
            'workflow_version': self.workflow_version,
            'total_steps': len(self.steps),
            'completed_steps': len(self.completed_steps),
            'current_step': self.current_step,
            'progress': f"{len(self.completed_steps)}/{len(self.steps)}",
            'progress_percentage': progress_percentage,
            'elapsed_time': elapsed_time,
            'status': 'running' if self.current_step < len(self.steps) else 'completed',
            'completed_step_names': [s['name'] for s in self.completed_steps],
            'current_step_name': self.steps[self.current_step]['name'] if self.current_step < len(self.steps) else None
        }
    
    # ==================== WORKFLOW MANAGEMENT ====================
    
    def set_workflow_metadata(self, name: str, version: str = "1.0", description: str = ""):
        """Thiết lập metadata cho workflow"""
        self.workflow_name = name
        self.workflow_version = version
        self.workflow_description = description
        logger.info(f"📝 Đã cập nhật metadata: {name} v{version}")
    
    def add_step_advanced(self, step_id: str, step_name: str, step_type: str, 
                         action_config: Dict, wait_config: Dict = None, 
                         timeout: float = 30.0, position: int = None):
        """
        Thêm bước vào workflow với cấu hình chi tiết
        
        Args:
            step_id: ID duy nhất của bước
            step_name: Tên mô tả bước
            step_type: 'robot', 'iot', 'delay', 'condition'
            action_config: Cấu hình action (dict)
            wait_config: Cấu hình wait (dict)
            timeout: Timeout (giây)
            position: Vị trí chèn (None = cuối)
        """
        step = {
            'id': step_id,
            'name': step_name,
            'type': step_type,
            'action_config': action_config,
            'wait_config': wait_config or {'type': 'default'},
            'timeout': timeout,
            'created_at': time.time()
        }
        
        # Tạo action function từ config
        step['action'] = self._create_action_from_config(action_config)
        
        # Tạo wait function từ config
        step['wait'] = self._create_wait_from_config(wait_config or {'type': 'default'})
        
        if position is None:
            self.steps.append(step)
        else:
            self.steps.insert(position, step)
        
        logger.info(f"✅ Đã thêm bước: {step_name} (ID: {step_id})")
        return step_id
    
    def update_step(self, step_id: str, **kwargs):
        """
        Cập nhật bước workflow
        
        Args:
            step_id: ID của bước cần cập nhật
            **kwargs: Các tham số cần cập nhật
        """
        step_index = self._find_step_by_id(step_id)
        if step_index == -1:
            logger.error(f"❌ Không tìm thấy bước với ID: {step_id}")
            return False
        
        step = self.steps[step_index]
        
        # Cập nhật các field
        for key, value in kwargs.items():
            if key in ['name', 'type', 'timeout']:
                step[key] = value
            elif key == 'action_config':
                step['action_config'] = value
                step['action'] = self._create_action_from_config(value)
            elif key == 'wait_config':
                step['wait_config'] = value
                step['wait'] = self._create_wait_from_config(value)
        
        step['updated_at'] = time.time()
        logger.info(f"✅ Đã cập nhật bước: {step_id}")
        return True
    
    def delete_step(self, step_id: str):
        """
        Xóa bước khỏi workflow
        
        Args:
            step_id: ID của bước cần xóa
        """
        step_index = self._find_step_by_id(step_id)
        if step_index == -1:
            logger.error(f"❌ Không tìm thấy bước với ID: {step_id}")
            return False
        
        step_name = self.steps[step_index]['name']
        del self.steps[step_index]
        logger.info(f"✅ Đã xóa bước: {step_name} (ID: {step_id})")
        return True
    
    def move_step(self, step_id: str, new_position: int):
        """
        Di chuyển bước đến vị trí mới
        
        Args:
            step_id: ID của bước cần di chuyển
            new_position: Vị trí mới (0-based index)
        """
        step_index = self._find_step_by_id(step_id)
        if step_index == -1:
            logger.error(f"❌ Không tìm thấy bước với ID: {step_id}")
            return False
        
        if new_position < 0 or new_position >= len(self.steps):
            logger.error(f"❌ Vị trí không hợp lệ: {new_position}")
            return False
        
        # Di chuyển bước
        step = self.steps.pop(step_index)
        self.steps.insert(new_position, step)
        
        logger.info(f"✅ Đã di chuyển bước '{step['name']}' đến vị trí {new_position + 1}")
        return True
    
    def duplicate_step(self, step_id: str, new_name: str = None):
        """
        Nhân bản một bước
        
        Args:
            step_id: ID của bước cần nhân bản
            new_name: Tên mới cho bước nhân bản
        """
        step_index = self._find_step_by_id(step_id)
        if step_index == -1:
            logger.error(f"❌ Không tìm thấy bước với ID: {step_id}")
            return None
        
        original_step = self.steps[step_index]
        new_step_id = str(uuid.uuid4())
        
        # Tạo bản sao
        new_step = original_step.copy()
        new_step['id'] = new_step_id
        new_step['name'] = new_name or f"{original_step['name']} (Copy)"
        new_step['created_at'] = time.time()
        
        # Chèn sau bước gốc
        self.steps.insert(step_index + 1, new_step)
        
        logger.info(f"✅ Đã nhân bản bước: {new_step['name']} (ID: {new_step_id})")
        return new_step_id
    
    def get_step(self, step_id: str) -> Optional[Dict]:
        """Lấy thông tin bước theo ID"""
        step_index = self._find_step_by_id(step_id)
        if step_index == -1:
            return None
        return self.steps[step_index]
    
    def list_steps(self) -> List[Dict]:
        """Lấy danh sách tất cả bước"""
        return [
            {
                'id': step['id'],
                'name': step['name'],
                'type': step['type'],
                'timeout': step['timeout'],
                'position': i
            }
            for i, step in enumerate(self.steps)
        ]
    
    def clear_workflow(self):
        """Xóa tất cả bước trong workflow"""
        self.steps.clear()
        self.completed_steps.clear()
        self.current_step = 0
        logger.info("🗑️ Đã xóa tất cả bước trong workflow")
    
    def _find_step_by_id(self, step_id: str) -> int:
        """Tìm index của bước theo ID"""
        for i, step in enumerate(self.steps):
            if step.get('id') == step_id:
                return i
        return -1
    
    def _create_action_from_config(self, action_config: Dict) -> Callable:
        """Tạo action function từ config"""
        action_type = action_config.get('type', 'default')
        
        if action_type == 'run_lua':
            lua_file = action_config.get('file', '')
            def action():
                return self._run_lua_action(lua_file)
            return action
        
        elif action_type == 'move_to_position':
            # Di chuyển robot đến vị trí cụ thể
            pos = action_config.get('position', {})
            def action():
                return self._move_to_position_action(pos)
            return action
        
        elif action_type == 'gripper_open':
            def action():
                return self._gripper_control_action(True)
            return action
        
        elif action_type == 'gripper_close':
            def action():
                return self._gripper_control_action(False)
            return action
            
        elif action_type == 'send_command':
            device = action_config.get('device', '')
            command = action_config.get('command', '')
            mode = action_config.get('mode')  # 'ascii' | 'hex' | None(auto)
            terminator = action_config.get('terminator')  # 'CR'|'LF'|'CRLF'|'none'|None
            def action():
                return self._send_iot_command(device, command, mode=mode, terminator=terminator)
            return action
        
        elif action_type == 'read_sensor':
            device = action_config.get('device', '')
            sensor = action_config.get('sensor', '')
            def action():
                return self._read_sensor_action(device, sensor)
            return action
        
        elif action_type == 'set_parameter':
            device = action_config.get('device', '')
            parameter = action_config.get('parameter', '')
            value = action_config.get('value', '')
            def action():
                return self._set_parameter_action(device, parameter, value)
            return action
            
        elif action_type == 'delay':
            delay_time = action_config.get('delay', 1.0)
            def action():
                time.sleep(delay_time)
                return True
            return action
            
        else:
            # Default action
            def action():
                logger.info("🔄 Thực hiện action mặc định")
                return True
            return action
    
    def _create_wait_from_config(self, wait_config: Dict) -> Callable:
        """Tạo wait function từ config"""
        wait_type = wait_config.get('type', 'default')
        
        if wait_type == 'robot_complete':
            # Run & Wait Completion đã được tích hợp ngay trong action run_lua,
            # nên phần wait ở đây luôn coi như hoàn thành để tránh đợi trùng lặp.
            def wait(step_info):
                logger.info("ℹ️ Bỏ qua wait 'robot_complete' vì action đã chờ hoàn thành")
                return True
            return wait
            
        elif wait_type == 'iot_response':
            device = wait_config.get('device', '')
            # Nếu không cấu hình timeout -> chờ vô hạn
            timeout = wait_config.get('timeout', None)
            prefer_raw = bool(wait_config.get('prefer_raw', False))
            # Hỗ trợ expected ở dạng ascii hoặc hex
            expected_ascii = wait_config.get('expected_ascii')
            expected_hex = wait_config.get('expected_hex')
            expected_bytes = None
            if expected_ascii is not None:
                try:
                    expected_bytes = str(expected_ascii).encode('ascii')
                except Exception:
                    expected_bytes = None
            elif expected_hex is not None:
                try:
                    clean = str(expected_hex).replace(' ', '').replace('-', '').replace('0x', '').replace('0X', '')
                    expected_bytes = bytes.fromhex(clean)
                except Exception:
                    expected_bytes = None
            def wait(step_info):
                return self.check_iot_complete(device, expected_response=expected_bytes, timeout=timeout, prefer_raw=prefer_raw)
            return wait
        
        elif wait_type == 'condition_check':
            # Kiểm tra điều kiện
            condition_config = wait_config.get('condition', {})
            def wait(step_info):
                return self._check_condition(condition_config)
            return wait
            
        elif wait_type == 'time_delay':
            delay = wait_config.get('delay', 1.0)
            def wait(step_info):
                time.sleep(delay)
                return True
            return wait
            
        else:
            # Default wait
            def wait(step_info):
                return self._default_wait(step_info)
            return wait
    
    def _run_lua_action(self, lua_file: str) -> bool:
        """Chạy Lua file và ĐỢI HOÀN THÀNH (Run & Wait Completion)."""
        if not self.robot_connected:
            logger.error("❌ Robot chưa kết nối!")
            return False
        
        try:
            logger.info(f"🤖 Chạy Lua script: {lua_file}")
            remote_path = f"/fruser/{lua_file}"
            
            if hasattr(self.robot, 'ProgramLoad'):
                load_result = self.robot.ProgramLoad(remote_path)
                if int(load_result) == 0:
                    run_result = self.robot.ProgramRun()
                    if int(run_result) != 0:
                        logger.error(f"ProgramRun failed: {run_result}")
                        return False
                    # Run & Wait Completion inside action (default 8s)
                    logger.info("⏳ Đang đợi robot hoàn thành (Run & Wait Completion)...")
                    done = self.check_robot_complete(timeout=8.0)
                    if not done:
                        logger.warning("⚠️ Timeout đợi robot hoàn thành")
                    return done
                else:
                    logger.error(f"ProgramLoad failed: {load_result}")
                    return False
            else:
                logger.error("Robot không có method ProgramLoad!")
                return False
        except Exception as e:
            logger.error(f"Lỗi chạy Lua: {e}")
            return False
    
    def _send_iot_command(self, device_name: str, command: str, mode: Optional[str] = None, terminator: Optional[str] = None) -> bool:
        """Gửi lệnh IoT action"""
        controller = (
            self.iot_devices.get(device_name)
            or self.iot_devices.get(device_name.upper())
            or self.iot_devices.get(device_name.lower())
        )
        if not controller:
            logger.error(f"❌ Thiết bị '{device_name}' chưa kết nối!")
            return False
        
        try:
            logger.info(f"📤 Gửi lệnh đến {device_name}: {command}")
            
            # Xây dựng payload theo mode/terminator:
            # - HEX string: "AA 55 01" hoặc "AA5501" → bytes.fromhex
            # - Số: giữ ASCII (thiết bị nhận số tốc độ v.v.)
            # - Khác: ASCII
            cmd_str = str(command).strip()
            hex_candidate = cmd_str.replace(' ', '').replace('-', '').replace('0x', '').replace('0X', '')
            is_hex = len(hex_candidate) >= 2 and all(c in '0123456789abcdefABCDEF' for c in hex_candidate)

            def apply_terminator(b: bytes) -> bytes:
                if not terminator or terminator.lower() == 'none':
                    return b
                t = terminator.upper()
                if t == 'CR':
                    return b + b'\r'
                if t == 'LF':
                    return b + b'\n'
                if t == 'CRLF':
                    return b + b'\r\n'
                return b

            if mode == 'hex':
                data = bytes.fromhex(hex_candidate)
                logger.info("🔧 [MODE=HEX] Sending HEX bytes")
                data = apply_terminator(data)
            elif mode == 'ascii':
                data = apply_terminator(cmd_str.encode('ascii'))
                logger.info("🔧 [MODE=ASCII] Sending ASCII")
            else:
                # Auto mode giữ ngược tương thích như GUI
                if is_hex and len(hex_candidate) % 2 == 0:
                    try:
                        data = bytes.fromhex(hex_candidate)
                        logger.info("🔧 [AUTO] Detected HEX BINARY")
                    except Exception:
                        data = cmd_str.encode('ascii')
                elif cmd_str.isdigit() or cmd_str.upper() == 'GO':
                    data = cmd_str.encode('ascii')
                    logger.info("🔧 [AUTO] Sending ASCII (digit/GO)")
                else:
                    data = cmd_str.encode('ascii')
                    logger.info("🔧 [AUTO] Sending ASCII")
                data = apply_terminator(data)
            if hasattr(controller, '_ser') and controller._ser and controller._ser.is_open:
                written = controller._ser.write(data)
                controller._ser.flush()
                return written > 0
            else:
                logger.error("❌ Serial port chưa mở!")
                return False
        except Exception as e:
            logger.error(f"Lỗi gửi IoT command: {e}")
            return False
    
    def _move_to_position_action(self, position: Dict) -> bool:
        """Di chuyển robot đến vị trí cụ thể"""
        if not self.robot_connected:
            logger.error("❌ Robot chưa kết nối!")
            return False
        
        try:
            logger.info(f"🔄 Di chuyển robot đến vị trí: {position}")
            
            if hasattr(self.robot, 'MovL') or hasattr(self.robot, 'moveL'):
                # Ví dụ di chuyển đến vị trí [x, y, z, a, b, c]
                pos = position.get('xyz', [0, 0, 0, 0, 0, 0])
                mode = position.get('mode', 0)  # 0 = MovL, 1 = MovJ
            
            if hasattr(self.robot, 'MovL'):
                result = self.robot.MovL(pos[0], pos[1], pos[2], pos[3], pos[4], pos[5])
                return int(result) == 0
            elif hasattr(self.robot, 'moveL'):
                result = self.robot.moveL(pos[0], pos[1], pos[2], pos[3], pos[4], pos[5])
                return int(result) == 0
            else:
                logger.error("❌ Robot không hỗ trợ chức năng di chuyển!")
                return False
        except Exception as e:
            logger.error(f"Lỗi di chuyển robot: {e}")
            return False
    
    def _gripper_control_action(self, open_gripper: bool) -> bool:
        """Điều khiển gripper"""
        if not self.robot_connected:
            logger.error("❌ Robot chưa kết nối!")
            return False
        
        try:
            action = "mở" if open_gripper else "đóng"
            logger.info(f"🤏 {action.capitalize()} gripper")
            
            if hasattr(self.robot, 'DO'):
                # Digital Output command
                dio_value = 1 if open_gripper else 0
                result = self.robot.DO(dio_value)
                return int(result) == 0
            elif hasattr(self.robot, 'setGripperState'):
                result = self.robot.setGripperState(open_gripper)
                return bool(result)
            else:
                logger.warning("⚠️ Robot không hỗ trợ điều khiển gripper")
                return True  # Không fail vì có thể robot không có gripper
        except Exception as e:
            logger.error(f"Lỗi điều khiển gripper: {e}")
            return False
    
    def _read_sensor_action(self, device_name: str, sensor: str) -> bool:
        """Đọc giá trị sensor"""
        if device_name not in self.iot_devices:
            logger.error(f"❌ Thiết bị '{device_name}' chưa kết nối!")
            return False
        
        try:
            logger.info(f"📊 Đọc sensor {sensor} từ {device_name}")
            
            controller = self.iot_devices[device_name]
            
            # Gửi command để đọc sensor
            read_command = f"READ_{sensor.upper()}"
            
            if hasattr(controller, '_ser') and controller._ser and controller._ser.is_open:
                # Gửi command
                controller._ser.write(read_command.encode('ascii'))
                controller._ser.flush()
                
                # Đọc response
                time.sleep(0.5)  # Chờ response
                if controller._ser.in_waiting > 0:
                    response = controller._ser.read(controller._ser.in_waiting)
                    logger.info(f"📥 Sensor value: {response.decode('ascii', errors='ignore')}")
                    return True
                else:
                    logger.warning("⚠️ Không nhận được response từ sensor")
                    return False
            else:
                logger.error("❌ Serial port chưa mở!")
                return False
        except Exception as e:
            logger.error(f"Lỗi đọc sensor: {e}")
            return False
    
    def _set_parameter_action(self, device_name: str, parameter: str, value: Any) -> bool:
        """Thiết lập tham số cho thiết bị"""
        if device_name not in self.iot_devices:
            logger.error(f"❌ Thiết bị '{device_name}' chưa kết nối!")
            return False
        
        try:
            logger.info(f"⚙️ Thiết lập {parameter}={value} cho {device_name}")
            
            controller = self.iot_devices[device_name]
            
            # Gửi command để thiết lập tham số
            set_command = f"SET_{parameter.upper()}_{value}"
            
            if hasattr(controller, '_ser') and controller._ser and controller._ser.is_open:
                written = controller._ser.write(set_command.encode('ascii'))
                controller._ser.flush()
                return written > 0
            else:
                logger.error("❌ Serial port chưa mở!")
                return False
        except Exception as e:
            logger.error(f"Lỗi thiết lập tham số: {e}")
            return False
    
    def _check_condition(self, condition_config: Dict) -> bool:
        """Kiểm tra điều kiện"""
        condition_type = condition_config.get('type', 'sensor_value')
        
        if condition_type == 'sensor_value':
            device = condition_config.get('device', '')
            sensor = condition_config.get('sensor', '')
            operator = condition_config.get('operator', '>')
            expected_value = condition_config.get('value', 0)
            
            # Đọc giá trị sensor
            if device not in self.iot_devices:
                logger.error(f"❌ Thiết bị '{device}' chưa kết nối!")
                return False
            
            controller = self.iot_devices[device]
            if hasattr(controller, '_ser') and controller._ser and controller._ser.is_open:
                # Gửi command đọc sensor
                controller._ser.write(f"READ_{sensor.upper()}".encode('ascii'))
                controller._ser.flush()
                
                time.sleep(0.3)
                if controller._ser.in_waiting > 0:
                    response = controller._ser.read(controller._ser.in_waiting)
                    try:
                        sensor_value = float(response.decode('ascii', errors='ignore').strip())
                        
                        # So sánh
                        if operator == '>':
                            result = sensor_value > expected_value
                        elif operator == '<':
                            result = sensor_value < expected_value
                        elif operator == '==':
                            result = sensor_value == expected_value
                        elif operator == '>=':
                            result = sensor_value >= expected_value
                        elif operator == '<=':
                            result = sensor_value <= expected_value
                        else:
                            result = False
                        
                        logger.info(f"🔍 Kiểm tra điều kiện: {sensor_value} {operator} {expected_value} = {result}")
                        return result
                    except ValueError:
                        logger.error("❌ Không thể parse sensor value")
                        return False
                else:
                    logger.warning("⚠️ Không nhận được response")
                    return False
            else:
                logger.error("❌ Serial port chưa mở!")
                return False
        
        elif condition_type == 'always_true':
            return True
        
        elif condition_type == 'always_false':
            return False
        
        else:
            logger.warning(f"⚠️ Không hỗ trợ condition type: {condition_type}")
            return True
    
    # ==================== JSON EXPORT/IMPORT ====================
    
    def export_workflow_to_json(self, file_path: str = None) -> str:
        """
        Export workflow ra file JSON
        
        Args:
            file_path: Đường dẫn file (None = tự động tạo tên)
        
        Returns:
            JSON string hoặc file path
        """
        workflow_data = {
            'workflow_id': self.workflow_id,
            'workflow_name': self.workflow_name,
            'workflow_version': self.workflow_version,
            'workflow_description': self.workflow_description,
            'created_at': time.time(),
            'steps': []
        }
        
        # Export các bước (loại bỏ function objects)
        for step in self.steps:
            step_data = {
                'id': step['id'],
                'name': step['name'],
                'type': step['type'],
                'action_config': step['action_config'],
                'wait_config': step['wait_config'],
                'timeout': step['timeout'],
                'created_at': step.get('created_at', time.time())
            }
            workflow_data['steps'].append(step_data)
        
        json_str = json.dumps(workflow_data, indent=2, ensure_ascii=False)
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"💾 Đã export workflow ra file: {file_path}")
            return file_path
        else:
            return json_str
    
    def import_workflow_from_json(self, json_data: str, file_path: str = None):
        """
        Import workflow từ JSON
        
        Args:
            json_data: JSON string (None nếu dùng file_path)
            file_path: Đường dẫn file JSON
        """
        try:
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
            else:
                workflow_data = json.loads(json_data)
            
            # Clear workflow hiện tại
            self.clear_workflow()
            
            # Import metadata
            self.workflow_id = workflow_data.get('workflow_id', str(uuid.uuid4()))
            self.workflow_name = workflow_data.get('workflow_name', 'Imported Workflow')
            self.workflow_version = workflow_data.get('workflow_version', '1.0')
            self.workflow_description = workflow_data.get('workflow_description', '')
            
            # Import các bước
            for step_data in workflow_data.get('steps', []):
                self.add_step_advanced(
                    step_id=step_data['id'],
                    step_name=step_data['name'],
                    step_type=step_data['type'],
                    action_config=step_data['action_config'],
                    wait_config=step_data['wait_config'],
                    timeout=step_data['timeout']
                )
            
            logger.info(f"📥 Đã import workflow: {self.workflow_name} ({len(self.steps)} bước)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi import workflow: {e}")
            return False
    
    def load_workflow_from_file(self, file_path: str):
        """Load workflow từ file JSON"""
        return self.import_workflow_from_json(None, file_path)
    
    def save_workflow_to_file(self, file_path: str):
        """Save workflow ra file JSON"""
        return self.export_workflow_to_json(file_path)
    
    # ==================== WORKFLOW REGISTRY ====================
    
    def register_workflow(self, name: str, file_path: str = None):
        """
        Đăng ký workflow vào registry
        
        Args:
            name: Tên workflow
            file_path: Đường dẫn file (None = tự động tạo)
        """
        if file_path is None:
            file_path = f"workflows/{name.replace(' ', '_').lower()}.json"
        
        # Tạo thư mục nếu chưa có
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Export workflow
        self.export_workflow_to_json(file_path)
        
        # Đăng ký vào registry
        self.workflow_registry[name] = {
            'file_path': file_path,
            'workflow_id': self.workflow_id,
            'name': self.workflow_name,
            'version': self.workflow_version,
            'step_count': len(self.steps),
            'registered_at': time.time()
        }
        
        logger.info(f"📚 Đã đăng ký workflow: {name} -> {file_path}")
    
    def list_registered_workflows(self) -> Dict:
        """Lấy danh sách workflow đã đăng ký"""
        return self.workflow_registry.copy()
    
    def load_registered_workflow(self, name: str):
        """
        Load workflow đã đăng ký
        
        Args:
            name: Tên workflow trong registry
        """
        if name not in self.workflow_registry:
            logger.error(f"❌ Workflow '{name}' chưa được đăng ký!")
            return False
        
        file_path = self.workflow_registry[name]['file_path']
        return self.load_workflow_from_file(file_path)
    
    def unregister_workflow(self, name: str):
        """Hủy đăng ký workflow"""
        if name in self.workflow_registry:
            del self.workflow_registry[name]
            logger.info(f"🗑️ Đã hủy đăng ký workflow: {name}")
            return True
        else:
            logger.warning(f"⚠️ Workflow '{name}' không tồn tại trong registry")
            return False
    
    # ==================== WORKFLOW TEMPLATES ====================
    
    def create_coffee_workflow_template(self):
        """Tạo template workflow pha cà phê cơ bản"""
        self.clear_workflow()
        self.set_workflow_metadata("Coffee Making Basic", "1.0", "Workflow pha cà phê cơ bản")
        
        # Bước 1: Robot lấy cốc
        self.add_step_advanced(
            step_id="grab_cup",
            step_name="Robot lấy cốc",
            step_type="robot",
            action_config={'type': 'run_lua', 'file': 'TakeCup.lua'},
            wait_config={'type': 'robot_complete', 'timeout': 3.0},
            timeout=5.0
        )
        
        # Bước 2: Robot đặt cốc vào máy
        self.add_step_advanced(
            step_id="place_cup",
            step_name="Robot đặt cốc vào máy",
            step_type="robot",
            action_config={'type': 'run_lua', 'file': 'MoveToMotor.lua'},
            wait_config={'type': 'robot_complete', 'timeout': 3.0},
            timeout=5.0
        )
        
        # Bước 3: Bật máy pha cà phê
        self.add_step_advanced(
            step_id="start_brewing",
            step_name="Bật máy pha cà phê",
            step_type="iot",
            action_config={'type': 'send_command', 'device': 'CoffeeMaker', 'command': 'START_BREWING'},
            wait_config={'type': 'iot_response', 'device': 'CoffeeMaker', 'timeout': 15.0},
            timeout=20.0
        )
        
        # Bước 4: Chờ máy pha xong
        self.add_step_advanced(
            step_id="wait_brewing",
            step_name="Chờ máy pha xong",
            step_type="iot",
            action_config={'type': 'delay', 'delay': 120.0},
            wait_config={'type': 'iot_response', 'device': 'CoffeeMaker', 'timeout': 120.0},
            timeout=130.0
        )
        
        # Bước 5: Robot lấy cốc ra
        self.add_step_advanced(
            step_id="take_cup_out",
            step_name="Robot lấy cốc ra",
            step_type="robot",
            action_config={'type': 'run_lua', 'file': 'TakeCupOut.lua'},
            wait_config={'type': 'robot_complete', 'timeout': 3.0},
            timeout=5.0
        )
        
        # Bước 6: Robot đưa cốc đến vị trí phục vụ
        self.add_step_advanced(
            step_id="serve_cup",
            step_name="Robot đưa cốc đến vị trí phục vụ",
            step_type="robot",
            action_config={'type': 'run_lua', 'file': 'ServeCup.lua'},
            wait_config={'type': 'robot_complete', 'timeout': 3.0},
            timeout=5.0
        )
        
        logger.info("☕ Đã tạo template workflow pha cà phê cơ bản")
    
    def create_ice_coffee_workflow_template(self):
        """Tạo template workflow pha cà phê đá"""
        self.clear_workflow()
        self.set_workflow_metadata("Ice Coffee Making", "1.0", "Workflow pha cà phê đá")
        
        # Bước 1-6: Giống coffee basic
        self.create_coffee_workflow_template()
        
        # Bước 7: Thêm đá
        self.add_step_advanced(
            step_id="add_ice",
            step_name="Thêm đá vào cốc",
            step_type="iot",
            action_config={'type': 'send_command', 'device': 'IceMaker', 'command': 'DISPENSE_ICE'},
            wait_config={'type': 'iot_response', 'device': 'IceMaker', 'timeout': 10.0},
            timeout=15.0
        )
        
        logger.info("🧊 Đã tạo template workflow pha cà phê đá")
    
    def create_cleaning_workflow_template(self):
        """Tạo template workflow vệ sinh"""
        self.clear_workflow()
        self.set_workflow_metadata("Cleaning Cycle", "1.0", "Workflow vệ sinh hệ thống")
        
        # Bước 1: Robot lấy cốc cũ
        self.add_step_advanced(
            step_id="grab_old_cup",
            step_name="Robot lấy cốc cũ",
            step_type="robot",
            action_config={'type': 'run_lua', 'file': 'GrabOldCup.lua'},
            wait_config={'type': 'robot_complete', 'timeout': 3.0},
            timeout=5.0
        )
        
        # Bước 2: Đổ cốc cũ
        self.add_step_advanced(
            step_id="dump_old_cup",
            step_name="Đổ cốc cũ",
            step_type="robot",
            action_config={'type': 'run_lua', 'file': 'DumpOldCup.lua'},
            wait_config={'type': 'robot_complete', 'timeout': 3.0},
            timeout=5.0
        )
        
        # Bước 3: Rửa cốc
        self.add_step_advanced(
            step_id="wash_cup",
            step_name="Rửa cốc",
            step_type="iot",
            action_config={'type': 'send_command', 'device': 'WashingStation', 'command': 'WASH_CUP'},
            wait_config={'type': 'iot_response', 'device': 'WashingStation', 'timeout': 30.0},
            timeout=35.0
        )
        
        # Bước 4: Đặt cốc sạch về vị trí
        self.add_step_advanced(
            step_id="place_clean_cup",
            step_name="Đặt cốc sạch về vị trí",
            step_type="robot",
            action_config={'type': 'run_lua', 'file': 'PlaceCleanCup.lua'},
            wait_config={'type': 'robot_complete', 'timeout': 3.0},
            timeout=5.0
        )
        
        logger.info("🧽 Đã tạo template workflow vệ sinh")


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


# ==================== EXAMPLE USAGE ====================

def example_workflow_management():
    """Ví dụ sử dụng workflow management"""
    
    # 1. Tạo workflow coordinator
    workflow = CoffeeWorkflowCoordinator()
    
    # 2. Kết nối robot và IoT
    # workflow.connect_robot(robot_instance)
    # workflow.connect_iot_device("CoffeeMaker", iot_controller)
    
    # 3. Tạo workflow từ template
    workflow.create_coffee_workflow_template()
    
    # 4. Thêm bước tùy chỉnh
    workflow.add_step_advanced(
        step_id="custom_step",
        step_name="Bước tùy chỉnh",
        step_type="delay",
        action_config={'type': 'delay', 'delay': 2.0},
        wait_config={'type': 'time_delay', 'delay': 1.0},
        timeout=5.0
    )
    
    # 5. Chỉnh sửa bước
    workflow.update_step("custom_step", name="Bước đã sửa", timeout=10.0)
    
    # 6. Di chuyển bước
    workflow.move_step("custom_step", 0)  # Di chuyển lên đầu
    
    # 7. Nhân bản bước
    workflow.duplicate_step("custom_step", "Bước nhân bản")
    
    # 8. Xóa bước
    # workflow.delete_step("custom_step")
    
    # 9. Export ra JSON
    json_data = workflow.export_workflow_to_json()
    print("JSON Workflow:")
    print(json_data)
    
    # 10. Save ra file
    workflow.save_workflow_to_file("my_workflow.json")
    
    # 11. Đăng ký workflow
    workflow.register_workflow("My Coffee Workflow")
    
    # 12. Load workflow đã đăng ký
    # workflow.load_registered_workflow("My Coffee Workflow")
    
    # 13. Chạy workflow
    # workflow.run_workflow()


if __name__ == "__main__":
    # Chạy ví dụ
    example_workflow_management()


# Export
__all__ = [
    'CoffeeWorkflowCoordinator', 
    'robot_run_lua', 
    'iot_send_command', 
    'iot_wait_response',
    'example_workflow_management'
]
