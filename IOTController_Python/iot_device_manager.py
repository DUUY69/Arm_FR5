#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IoT Device Manager
Quản lý và điều khiển nhiều thiết bị IoT đồng thời
"""

import os
import sys
import json
import time
import threading
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

from iot_controller import IoTController
from protocol import normalize_hex_string, build_frame, verify_frame

# Load environment variables
load_dotenv('config.env')

@dataclass
class DeviceStatus:
    """Trạng thái thiết bị"""
    name: str
    com_port: str
    connected: bool
    last_seen: Optional[datetime]
    response_count: int
    error_count: int
    commands_sent: int

class IoTDeviceManager:
    def __init__(self):
        self.devices: Dict[str, IoTController] = {}
        self.device_status: Dict[str, DeviceStatus] = {}
        self.device_commands: Dict[str, Dict] = {}
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        self.running = False
        self.setup_logging()
        self.load_configuration()
    
    def setup_logging(self):
        """Thiết lập logging"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        enable_logging = os.getenv('ENABLE_LOGGING', 'true').lower() == 'true'
        
        if enable_logging:
            logging.basicConfig(
                level=getattr(logging, log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('iot_device_manager.log'),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.disable(logging.CRITICAL)
    
    def load_configuration(self):
        """Load cấu hình từ environment"""
        # Load devices
        devices_str = os.getenv('DEVICES', '')
        if devices_str:
            for device_info in devices_str.split(';'):
                if ':' in device_info:
                    name, com_port = device_info.strip().split(':', 1)
                    self.device_status[name] = DeviceStatus(
                        name=name,
                        com_port=com_port,
                        connected=False,
                        last_seen=None,
                        response_count=0,
                        error_count=0,
                        commands_sent=0
                    )
        
        # Load commands
        for device_name in self.device_status.keys():
            env_key = device_name.upper().replace(' ', '_') + '_COMMANDS'
            commands_str = os.getenv(env_key, '{}')
            
            try:
                self.device_commands[device_name] = json.loads(commands_str)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse commands for {device_name}: {e}")
                self.device_commands[device_name] = {}
    
    def connect_device(self, device_name: str) -> bool:
        """Kết nối đến thiết bị"""
        if device_name not in self.device_status:
            logging.error(f"Device {device_name} not found in configuration")
            return False
        
        if device_name in self.devices and self.devices[device_name].is_open():
            logging.info(f"Device {device_name} already connected")
            return True
        
        try:
            controller = IoTController()
            status = self.device_status[device_name]
            
            baudrate = int(os.getenv('DEFAULT_BAUDRATE', '115200'))
            timeout = float(os.getenv('DEFAULT_TIMEOUT', '2.0'))
            
            controller.open(status.com_port, baudrate=baudrate, timeout=timeout)
            
            if controller.is_open():
                self.devices[device_name] = controller
                status.connected = True
                status.last_seen = datetime.now()
                logging.info(f"Successfully connected to {device_name} on {status.com_port}")
                return True
            else:
                logging.error(f"Failed to connect to {device_name}")
                return False
                
        except Exception as e:
            logging.error(f"Connection error for {device_name}: {e}")
            return False
    
    def disconnect_device(self, device_name: str) -> bool:
        """Ngắt kết nối thiết bị"""
        if device_name not in self.devices:
            return False
        
        try:
            self.devices[device_name].close()
            del self.devices[device_name]
            
            if device_name in self.device_status:
                self.device_status[device_name].connected = False
            
            # Stop monitoring thread if exists
            if device_name in self.monitoring_threads:
                self.monitoring_threads[device_name].join(timeout=1.0)
                del self.monitoring_threads[device_name]
            
            logging.info(f"Disconnected from {device_name}")
            return True
            
        except Exception as e:
            logging.error(f"Disconnection error for {device_name}: {e}")
            return False
    
    def send_command(self, device_name: str, command: Dict) -> Tuple[bool, Optional[bytes]]:
        """Gửi lệnh đến thiết bị và nhận phản hồi"""
        if device_name not in self.devices or not self.devices[device_name].is_open():
            logging.error(f"Device {device_name} not connected")
            return False, None
        
        try:
            controller = self.devices[device_name]
            status = self.device_status[device_name]
            
            cmd_code = int(command['command_code'], 16)
            ins_code = int(command['instruction_code'], 16)
            data_bytes = command.get('data_bytes', [])
            
            # Convert data_bytes to bytes
            data_hex = ''.join(f'{b:02X}' for b in data_bytes) if data_bytes else ''
            
            # Build và gửi frame
            frame = build_frame(cmd_code, ins_code, bytes.fromhex(data_hex) if data_hex else b'')
            written = controller.send_hex(frame.hex())
            
            status.commands_sent += 1
            
            # Đọc phản hồi
            timeout = float(os.getenv('DEFAULT_TIMEOUT', '2.0'))
            response = controller.read_frame(timeout)
            
            if response:
                status.response_count += 1
                status.last_seen = datetime.now()
                
                if verify_frame(response):
                    logging.info(f"Command sent to {device_name}: {written} bytes, response: {response.hex().upper()}")
                    return True, response
                else:
                    logging.warning(f"Invalid frame received from {device_name}: {response.hex().upper()}")
                    return True, response
            else:
                logging.warning(f"No response from {device_name}")
                return True, None
                
        except Exception as e:
            if device_name in self.device_status:
                self.device_status[device_name].error_count += 1
            logging.error(f"Command error for {device_name}: {e}")
            return False, None
    
    def start_monitoring(self, device_name: str, interval: float = 5.0):
        """Bắt đầu monitoring thiết bị"""
        if device_name in self.monitoring_threads:
            logging.warning(f"Monitoring already started for {device_name}")
            return
        
        def monitor_loop():
            while self.running and device_name in self.devices:
                try:
                    if device_name in self.device_commands:
                        status_cmd = self.device_commands[device_name].get('status_query')
                        if status_cmd:
                            success, response = self.send_command(device_name, status_cmd)
                            if not success:
                                logging.warning(f"Monitoring failed for {device_name}")
                
                except Exception as e:
                    logging.error(f"Monitoring error for {device_name}: {e}")
                
                time.sleep(interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        self.monitoring_threads[device_name] = thread
        logging.info(f"Started monitoring for {device_name}")
    
    def stop_monitoring(self, device_name: str):
        """Dừng monitoring thiết bị"""
        if device_name in self.monitoring_threads:
            self.monitoring_threads[device_name].join(timeout=2.0)
            del self.monitoring_threads[device_name]
            logging.info(f"Stopped monitoring for {device_name}")
    
    def get_device_status(self, device_name: str) -> Optional[DeviceStatus]:
        """Lấy trạng thái thiết bị"""
        return self.device_status.get(device_name)
    
    def get_all_status(self) -> Dict[str, DeviceStatus]:
        """Lấy trạng thái tất cả thiết bị"""
        return self.device_status.copy()
    
    def broadcast_command(self, command: Dict) -> Dict[str, Tuple[bool, Optional[bytes]]]:
        """Gửi lệnh đến tất cả thiết bị đã kết nối"""
        results = {}
        
        for device_name in self.devices:
            if self.devices[device_name].is_open():
                results[device_name] = self.send_command(device_name, command)
        
        return results
    
    def get_device_health(self, device_name: str) -> Dict:
        """Lấy thông tin sức khỏe thiết bị"""
        if device_name not in self.device_status:
            return {}
        
        status = self.device_status[device_name]
        
        health = {
            'name': status.name,
            'com_port': status.com_port,
            'connected': status.connected,
            'last_seen': status.last_seen.isoformat() if status.last_seen else None,
            'response_count': status.response_count,
            'error_count': status.error_count,
            'commands_sent': status.commands_sent,
            'success_rate': (status.response_count / max(status.commands_sent, 1)) * 100,
            'monitoring': device_name in self.monitoring_threads
        }
        
        return health
    
    def get_system_overview(self) -> Dict:
        """Lấy tổng quan hệ thống"""
        total_devices = len(self.device_status)
        connected_devices = sum(1 for status in self.device_status.values() if status.connected)
        monitoring_devices = len(self.monitoring_threads)
        
        total_commands = sum(status.commands_sent for status in self.device_status.values())
        total_responses = sum(status.response_count for status in self.device_status.values())
        total_errors = sum(status.error_count for status in self.device_status.values())
        
        overview = {
            'total_devices': total_devices,
            'connected_devices': connected_devices,
            'monitoring_devices': monitoring_devices,
            'total_commands': total_commands,
            'total_responses': total_responses,
            'total_errors': total_errors,
            'overall_success_rate': (total_responses / max(total_commands, 1)) * 100,
            'uptime': time.time() - getattr(self, '_start_time', time.time())
        }
        
        return overview
    
    def start(self):
        """Khởi động device manager"""
        self.running = True
        self._start_time = time.time()
        logging.info("IoT Device Manager started")
    
    def stop(self):
        """Dừng device manager"""
        self.running = False
        
        # Dừng tất cả monitoring threads
        for device_name in list(self.monitoring_threads.keys()):
            self.stop_monitoring(device_name)
        
        # Ngắt kết nối tất cả thiết bị
        for device_name in list(self.devices.keys()):
            self.disconnect_device(device_name)
        
        logging.info("IoT Device Manager stopped")
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def main():
    """Test function"""
    with IoTDeviceManager() as manager:
        print("IoT Device Manager started")
        
        # Connect to all devices
        for device_name in manager.device_status.keys():
            if manager.connect_device(device_name):
                print(f"Connected to {device_name}")
                manager.start_monitoring(device_name)
        
        # Run for 30 seconds
        time.sleep(30)
        
        # Print status
        print("\nDevice Status:")
        for device_name, status in manager.get_all_status().items():
            health = manager.get_device_health(device_name)
            print(f"{device_name}: {health}")
        
        print("\nSystem Overview:")
        overview = manager.get_system_overview()
        for key, value in overview.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
