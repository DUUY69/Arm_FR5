#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IOTController Menu System
Hệ thống menu tương tác cho điều khiển thiết bị IoT
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from iot_controller import IoTController
from protocol import normalize_hex_string, build_frame, verify_frame

# Load environment variables
load_dotenv('config.env')

class IoTMenuSystem:
    def __init__(self):
        self.controller = IoTController()
        self.devices = self._load_devices()
        self.commands = self._load_commands()
        self.current_device = None
        self.setup_logging()
        
    def setup_logging(self):
        """Thiết lập logging"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        enable_logging = os.getenv('ENABLE_LOGGING', 'true').lower() == 'true'
        
        if enable_logging:
            logging.basicConfig(
                level=getattr(logging, log_level),
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('iot_controller.log'),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.disable(logging.CRITICAL)
    
    def _load_devices(self) -> Dict[str, str]:
        """Load danh sách thiết bị từ DEVICES"""
        devices_str = os.getenv('DEVICES', '')
        devices = {}
        
        if devices_str:
            for device_info in devices_str.split(';'):
                if ':' in device_info:
                    name, com_port = device_info.strip().split(':', 1)
                    devices[name] = com_port
                    
        return devices
    
    def _load_commands(self) -> Dict[str, Dict]:
        """Load lệnh cho từng thiết bị"""
        commands = {}
        
        for device_name in self.devices.keys():
            # Chuyển tên thiết bị thành key environment
            env_key = device_name.upper().replace(' ', '_') + '_COMMANDS'
            commands_str = os.getenv(env_key, '{}')
            
            try:
                commands[device_name] = json.loads(commands_str)
            except json.JSONDecodeError as e:
                print(f"⚠️ Lỗi parse JSON cho {device_name}: {e}")
                commands[device_name] = {}
                
        return commands
    
    def print_header(self):
        """In header của chương trình"""
        print("\n" + "="*70)
        print("    🌐 IOT CONTROLLER - MENU SYSTEM")
        print("="*70)
        print(f"📡 Thiết bị đã cấu hình: {len(self.devices)}")
        print(f"🔧 Lệnh có sẵn: {sum(len(cmds) for cmds in self.commands.values())}")
        print("="*70)
    
    def print_main_menu(self):
        """In menu chính"""
        print("\n📋 MENU CHÍNH:")
        print("1. 🔌 Quản lý kết nối")
        print("2. 🎮 Điều khiển thiết bị")
        print("3. 📊 Monitor thiết bị")
        print("4. ⚙️ Cấu hình")
        print("5. 📝 Logs")
        print("6. 🚪 Thoát")
        print("-" * 50)
    
    def print_connection_menu(self):
        """Menu quản lý kết nối"""
        print("\n🔌 QUẢN LÝ KẾT NỐI:")
        print("1. 📋 Danh sách COM ports")
        print("2. 🔗 Kết nối thiết bị")
        print("3. ❌ Ngắt kết nối")
        print("4. 🔄 Kiểm tra kết nối")
        print("5. ⬅️ Quay lại")
        print("-" * 50)
    
    def print_device_menu(self):
        """Menu điều khiển thiết bị"""
        print("\n🎮 ĐIỀU KHIỂN THIẾT BỊ:")
        print("1. 📋 Chọn thiết bị")
        print("2. 🚀 Gửi lệnh")
        print("3. 📤 Gửi HEX tùy chỉnh")
        print("4. 🔄 Test kết nối")
        print("5. ⬅️ Quay lại")
        print("-" * 50)
    
    def list_com_ports(self):
        """Liệt kê các COM port có sẵn"""
        print("\n📋 DANH SÁCH COM PORTS:")
        ports = self.controller.list_ports()
        
        if not ports:
            print("❌ Không tìm thấy COM port nào!")
            return
        
        print("-" * 50)
        for i, port in enumerate(ports, 1):
            status = "🔗 Đã kết nối" if self.controller.is_open() and port == getattr(self.controller._ser, 'port', None) else "⚪ Chưa kết nối"
            print(f"  {i:2d}. {port} - {status}")
        print("-" * 50)
    
    def list_devices(self):
        """Liệt kê các thiết bị đã cấu hình"""
        print("\n📋 THIẾT BỊ ĐÃ CẤU HÌNH:")
        print("-" * 70)
        
        for i, (name, com_port) in enumerate(self.devices.items(), 1):
            status = "🔗 Kết nối" if self.controller.is_open() and com_port == getattr(self.controller._ser, 'port', None) else "⚪ Chưa kết nối"
            commands_count = len(self.commands.get(name, {}))
            print(f"  {i:2d}. 📱 {name}")
            print(f"      🔌 COM: {com_port}")
            print(f"      📊 Trạng thái: {status}")
            print(f"      🎮 Lệnh: {commands_count} lệnh")
            print()
        print("-" * 70)
    
    def connect_device(self):
        """Kết nối đến thiết bị"""
        self.list_devices()
        
        try:
            choice = input(f"\n🔢 Chọn thiết bị (1-{len(self.devices)}): ").strip()
            
            if not choice.isdigit():
                print("❌ Vui lòng nhập số!")
                return
            
            choice = int(choice)
            device_names = list(self.devices.keys())
            
            if 1 <= choice <= len(device_names):
                device_name = device_names[choice - 1]
                com_port = self.devices[device_name]
                
                print(f"\n🔌 Đang kết nối đến {device_name} ({com_port})...")
                
                try:
                    baudrate = int(os.getenv('DEFAULT_BAUDRATE', '115200'))
                    timeout = float(os.getenv('DEFAULT_TIMEOUT', '2.0'))
                    
                    self.controller.open(com_port, baudrate=baudrate, timeout=timeout)
                    
                    if self.controller.is_open():
                        self.current_device = device_name
                        print(f"✅ Kết nối thành công đến {device_name}!")
                        logging.info(f"Connected to {device_name} on {com_port}")
                    else:
                        print(f"❌ Không thể kết nối đến {device_name}")
                        
                except Exception as e:
                    print(f"❌ Lỗi kết nối: {e}")
                    logging.error(f"Connection error: {e}")
            else:
                print(f"❌ Vui lòng chọn từ 1 đến {len(device_names)}!")
                
        except KeyboardInterrupt:
            print("\n👋 Đã hủy!")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    def disconnect_device(self):
        """Ngắt kết nối thiết bị"""
        if not self.controller.is_open():
            print("❌ Không có kết nối nào đang hoạt động!")
            return
        
        device_name = self.current_device or "Thiết bị"
        print(f"\n❌ Đang ngắt kết nối {device_name}...")
        
        self.controller.close()
        self.current_device = None
        
        print("✅ Đã ngắt kết nối!")
        logging.info(f"Disconnected from {device_name}")
    
    def check_connection(self):
        """Kiểm tra kết nối"""
        if not self.controller.is_open():
            print("❌ Không có kết nối nào!")
            return
        
        device_name = self.current_device or "Thiết bị"
        com_port = getattr(self.controller._ser, 'port', 'Unknown')
        
        print(f"\n🔍 KIỂM TRA KẾT NỐI:")
        print(f"📱 Thiết bị: {device_name}")
        print(f"🔌 COM Port: {com_port}")
        print(f"📊 Trạng thái: {'✅ Hoạt động' if self.controller.is_open() else '❌ Không hoạt động'}")
        
        # Test gửi lệnh ping (nếu có)
        if device_name in self.commands:
            ping_cmd = self.commands[device_name].get('status_query')
            if ping_cmd:
                print(f"\n🧪 Test ping...")
                try:
                    self.send_command(ping_cmd)
                    print("✅ Ping thành công!")
                except Exception as e:
                    print(f"❌ Ping thất bại: {e}")
    
    def send_command(self, command: Dict) -> bool:
        """Gửi lệnh đến thiết bị"""
        if not self.controller.is_open():
            raise RuntimeError("Không có kết nối!")
        
        try:
            cmd_code = int(command['command_code'], 16)
            ins_code = int(command['instruction_code'], 16)
            data_bytes = command.get('data_bytes', [])
            
            # Convert data_bytes to bytes
            data_hex = ''.join(f'{b:02X}' for b in data_bytes) if data_bytes else ''
            
            # Build và gửi frame
            frame = build_frame(cmd_code, ins_code, bytes.fromhex(data_hex) if data_hex else b'')
            written = self.controller.send_hex(frame.hex())
            
            logging.info(f"Sent command: {command} -> {written} bytes")
            return True
            
        except Exception as e:
            logging.error(f"Command send error: {e}")
            raise
    
    def send_custom_hex(self):
        """Gửi HEX tùy chỉnh"""
        if not self.controller.is_open():
            print("❌ Không có kết nối!")
            return
        
        print(f"\n📤 GỬI HEX TÙY CHỈNH:")
        print("💡 Ví dụ: A1 01 FF hoặc 0xA101FF")
        
        try:
            hex_input = input("🔢 Nhập HEX: ").strip()
            
            if not hex_input:
                print("❌ HEX không được để trống!")
                return
            
            print(f"📤 Đang gửi: {hex_input}")
            written = self.controller.send_hex(hex_input)
            print(f"✅ Đã gửi {written} bytes!")
            
            # Hỏi có muốn đọc phản hồi không
            read_response = input("\n❓ Có muốn đọc phản hồi? (y/n): ").strip().lower()
            if read_response in ['y', 'yes', 'có', 'c']:
                try:
                    timeout = float(os.getenv('DEFAULT_TIMEOUT', '2.0'))
                    response = self.controller.read_frame(timeout)
                    if response:
                        print(f"📥 Phản hồi: {response.hex().upper()}")
                    else:
                        print("📥 Không có phản hồi")
                except Exception as e:
                    print(f"❌ Lỗi đọc phản hồi: {e}")
            
            logging.info(f"Sent custom hex: {hex_input} -> {written} bytes")
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            logging.error(f"Custom hex error: {e}")
    
    def run(self):
        """Chạy hệ thống menu"""
        self.print_header()
        
        while True:
            try:
                self.print_main_menu()
                choice = input("🔢 Chọn chức năng (1-6): ").strip()
                
                if choice == '1':
                    self.connection_menu()
                elif choice == '2':
                    self.device_control_menu()
                elif choice == '3':
                    self.monitor_menu()
                elif choice == '4':
                    self.config_menu()
                elif choice == '5':
                    self.logs_menu()
                elif choice == '6':
                    print("\n👋 Tạm biệt!")
                    break
                else:
                    print("❌ Chức năng không hợp lệ!")
                
                input("\n⏸️ Nhấn Enter để tiếp tục...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
                logging.error(f"Menu error: {e}")
        
        # Đóng kết nối khi thoát
        if self.controller.is_open():
            self.controller.close()
    
    def connection_menu(self):
        """Xử lý menu kết nối"""
        while True:
            self.print_connection_menu()
            choice = input("🔢 Chọn (1-5): ").strip()
            
            if choice == '1':
                self.list_com_ports()
            elif choice == '2':
                self.connect_device()
            elif choice == '3':
                self.disconnect_device()
            elif choice == '4':
                self.check_connection()
            elif choice == '5':
                break
            else:
                print("❌ Lựa chọn không hợp lệ!")
            
            input("\n⏸️ Nhấn Enter để tiếp tục...")
    
    def device_control_menu(self):
        """Xử lý menu điều khiển thiết bị"""
        while True:
            self.print_device_menu()
            choice = input("🔢 Chọn (1-5): ").strip()
            
            if choice == '1':
                self.select_device()
            elif choice == '2':
                self.send_device_command()
            elif choice == '3':
                self.send_custom_hex()
            elif choice == '4':
                self.check_connection()
            elif choice == '5':
                break
            else:
                print("❌ Lựa chọn không hợp lệ!")
            
            input("\n⏸️ Nhấn Enter để tiếp tục...")
    
    def select_device(self):
        """Chọn thiết bị để điều khiển"""
        if not self.devices:
            print("❌ Không có thiết bị nào được cấu hình!")
            return
        
        self.list_devices()
        
        try:
            choice = input(f"\n🔢 Chọn thiết bị (1-{len(self.devices)}): ").strip()
            
            if not choice.isdigit():
                print("❌ Vui lòng nhập số!")
                return
            
            choice = int(choice)
            device_names = list(self.devices.keys())
            
            if 1 <= choice <= len(device_names):
                device_name = device_names[choice - 1]
                self.current_device = device_name
                print(f"✅ Đã chọn thiết bị: {device_name}")
            else:
                print(f"❌ Vui lòng chọn từ 1 đến {len(device_names)}!")
                
        except KeyboardInterrupt:
            print("\n👋 Đã hủy!")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    def send_device_command(self):
        """Gửi lệnh đến thiết bị đã chọn"""
        if not self.current_device:
            print("❌ Vui lòng chọn thiết bị trước!")
            return
        
        if not self.controller.is_open():
            print("❌ Vui lòng kết nối đến thiết bị trước!")
            return
        
        device_commands = self.commands.get(self.current_device, {})
        if not device_commands:
            print(f"❌ Không có lệnh nào cho {self.current_device}!")
            return
        
        print(f"\n🎮 LỆNH CHO {self.current_device.upper()}:")
        print("-" * 70)
        
        command_list = list(device_commands.items())
        for i, (cmd_id, cmd_info) in enumerate(command_list, 1):
            print(f"  {i:2d}. 🎯 {cmd_id}")
            print(f"      📋 CMD: {cmd_info['command_code']}")
            print(f"      📋 INS: {cmd_info['instruction_code']}")
            if cmd_info.get('data_bytes'):
                print(f"      📋 DATA: {cmd_info['data_bytes']}")
            print()
        
        print("-" * 70)
        
        try:
            choice = input(f"🔢 Chọn lệnh (1-{len(command_list)}): ").strip()
            
            if not choice.isdigit():
                print("❌ Vui lòng nhập số!")
                return
            
            choice = int(choice)
            
            if 1 <= choice <= len(command_list):
                cmd_id, cmd_info = command_list[choice - 1]
                
                print(f"\n🚀 Đang gửi lệnh: {cmd_id}")
                
                try:
                    self.send_command(cmd_info)
                    print(f"✅ Đã gửi lệnh {cmd_id} thành công!")
                    
                    # Hỏi có muốn đọc phản hồi không
                    read_response = input("\n❓ Có muốn đọc phản hồi? (y/n): ").strip().lower()
                    if read_response in ['y', 'yes', 'có', 'c']:
                        try:
                            timeout = float(os.getenv('DEFAULT_TIMEOUT', '2.0'))
                            response = self.controller.read_frame(timeout)
                            if response:
                                print(f"📥 Phản hồi: {response.hex().upper()}")
                                
                                # Verify frame
                                if verify_frame(response):
                                    print("✅ Frame hợp lệ!")
                                else:
                                    print("⚠️ Frame không hợp lệ!")
                            else:
                                print("📥 Không có phản hồi")
                        except Exception as e:
                            print(f"❌ Lỗi đọc phản hồi: {e}")
                    
                except Exception as e:
                    print(f"❌ Lỗi gửi lệnh: {e}")
            else:
                print(f"❌ Vui lòng chọn từ 1 đến {len(command_list)}!")
                
        except KeyboardInterrupt:
            print("\n👋 Đã hủy!")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    def monitor_menu(self):
        """Menu monitor thiết bị"""
        print("\n📊 MONITOR THIẾT BỊ:")
        print("1. 📈 Real-time monitoring")
        print("2. 📋 Log thiết bị")
        print("3. ⬅️ Quay lại")
        print("-" * 50)
        
        choice = input("🔢 Chọn (1-3): ").strip()
        
        if choice == '1':
            self.real_time_monitoring()
        elif choice == '2':
            self.device_logs()
        elif choice == '3':
            return
        else:
            print("❌ Lựa chọn không hợp lệ!")
    
    def real_time_monitoring(self):
        """Real-time monitoring"""
        if not self.controller.is_open():
            print("❌ Vui lòng kết nối đến thiết bị trước!")
            return
        
        print(f"\n📈 REAL-TIME MONITORING:")
        print("💡 Nhấn Ctrl+C để dừng")
        print("-" * 50)
        
        try:
            while True:
                # Gửi lệnh status query
                if self.current_device and self.current_device in self.commands:
                    status_cmd = self.commands[self.current_device].get('status_query')
                    if status_cmd:
                        try:
                            self.send_command(status_cmd)
                            response = self.controller.read_frame(1.0)
                            if response:
                                timestamp = time.strftime("%H:%M:%S")
                                print(f"[{timestamp}] 📥 {response.hex().upper()}")
                            else:
                                print(f"[{time.strftime('%H:%M:%S')}] ⏰ Timeout")
                        except Exception as e:
                            print(f"[{time.strftime('%H:%M:%S')}] ❌ {e}")
                
                time.sleep(2)  # Monitor mỗi 2 giây
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Đã dừng monitoring")
    
    def device_logs(self):
        """Xem log thiết bị"""
        print(f"\n📋 LOG THIẾT BỊ:")
        
        if os.path.exists('iot_controller.log'):
            try:
                with open('iot_controller.log', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Hiển thị 20 dòng cuối
                recent_lines = lines[-20:] if len(lines) > 20 else lines
                
                print("-" * 70)
                for line in recent_lines:
                    print(line.strip())
                print("-" * 70)
                
            except Exception as e:
                print(f"❌ Lỗi đọc log: {e}")
        else:
            print("❌ Không tìm thấy file log!")
    
    def config_menu(self):
        """Menu cấu hình"""
        print("\n⚙️ CẤU HÌNH:")
        print("1. 📋 Xem cấu hình hiện tại")
        print("2. 🔧 Thay đổi COM port")
        print("3. 📝 Thêm thiết bị mới")
        print("4. ⬅️ Quay lại")
        print("-" * 50)
        
        choice = input("🔢 Chọn (1-4): ").strip()
        
        if choice == '1':
            self.show_config()
        elif choice == '2':
            self.change_com_port()
        elif choice == '3':
            self.add_new_device()
        elif choice == '4':
            return
        else:
            print("❌ Lựa chọn không hợp lệ!")
    
    def show_config(self):
        """Hiển thị cấu hình hiện tại"""
        print(f"\n📋 CẤU HÌNH HIỆN TẠI:")
        print("-" * 70)
        
        print(f"🔌 Thiết bị:")
        for name, com_port in self.devices.items():
            print(f"  📱 {name}: {com_port}")
        
        print(f"\n🎮 Lệnh:")
        for device_name, commands in self.commands.items():
            print(f"  📱 {device_name}: {len(commands)} lệnh")
            for cmd_id, cmd_info in commands.items():
                print(f"    🎯 {cmd_id}: {cmd_info['command_code']} {cmd_info['instruction_code']}")
        
        print(f"\n⚙️ Mặc định:")
        print(f"  📊 Baudrate: {os.getenv('DEFAULT_BAUDRATE', '115200')}")
        print(f"  ⏱️ Timeout: {os.getenv('DEFAULT_TIMEOUT', '2.0')}s")
        print(f"  🔄 Retry: {os.getenv('DEFAULT_RETRY_COUNT', '3')}")
        print(f"  📝 Logging: {os.getenv('ENABLE_LOGGING', 'true')}")
        print("-" * 70)
    
    def change_com_port(self):
        """Thay đổi COM port"""
        print(f"\n🔧 THAY ĐỔI COM PORT:")
        
        self.list_devices()
        
        try:
            choice = input(f"\n🔢 Chọn thiết bị (1-{len(self.devices)}): ").strip()
            
            if not choice.isdigit():
                print("❌ Vui lòng nhập số!")
                return
            
            choice = int(choice)
            device_names = list(self.devices.keys())
            
            if 1 <= choice <= len(device_names):
                device_name = device_names[choice - 1]
                current_port = self.devices[device_name]
                
                print(f"\n📱 Thiết bị: {device_name}")
                print(f"🔌 COM hiện tại: {current_port}")
                
                new_port = input("🔌 COM mới: ").strip()
                
                if new_port:
                    self.devices[device_name] = new_port
                    print(f"✅ Đã thay đổi {device_name} từ {current_port} sang {new_port}")
                    logging.info(f"Changed {device_name} COM port from {current_port} to {new_port}")
                else:
                    print("❌ COM port không được để trống!")
            else:
                print(f"❌ Vui lòng chọn từ 1 đến {len(device_names)}!")
                
        except KeyboardInterrupt:
            print("\n👋 Đã hủy!")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    def add_new_device(self):
        """Thêm thiết bị mới"""
        print(f"\n📝 THÊM THIẾT BỊ MỚI:")
        
        try:
            device_name = input("📱 Tên thiết bị: ").strip()
            if not device_name:
                print("❌ Tên thiết bị không được để trống!")
                return
            
            com_port = input("🔌 COM port: ").strip()
            if not com_port:
                print("❌ COM port không được để trống!")
                return
            
            self.devices[device_name] = com_port
            self.commands[device_name] = {}
            
            print(f"✅ Đã thêm thiết bị: {device_name} ({com_port})")
            logging.info(f"Added new device: {device_name} on {com_port}")
            
        except KeyboardInterrupt:
            print("\n👋 Đã hủy!")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    def logs_menu(self):
        """Menu logs"""
        print("\n📝 LOGS:")
        print("1. 📋 Xem log gần đây")
        print("2. 🗑️ Xóa log")
        print("3. 📊 Thống kê log")
        print("4. ⬅️ Quay lại")
        print("-" * 50)
        
        choice = input("🔢 Chọn (1-4): ").strip()
        
        if choice == '1':
            self.device_logs()
        elif choice == '2':
            self.clear_logs()
        elif choice == '3':
            self.log_statistics()
        elif choice == '4':
            return
        else:
            print("❌ Lựa chọn không hợp lệ!")
    
    def clear_logs(self):
        """Xóa logs"""
        if os.path.exists('iot_controller.log'):
            try:
                os.remove('iot_controller.log')
                print("✅ Đã xóa log!")
            except Exception as e:
                print(f"❌ Lỗi xóa log: {e}")
        else:
            print("❌ Không tìm thấy file log!")
    
    def log_statistics(self):
        """Thống kê log"""
        if not os.path.exists('iot_controller.log'):
            print("❌ Không tìm thấy file log!")
            return
        
        try:
            with open('iot_controller.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"\n📊 THỐNG KÊ LOG:")
            print("-" * 50)
            print(f"📝 Tổng số dòng: {len(lines)}")
            
            # Đếm theo level
            levels = {}
            for line in lines:
                if ' - ' in line:
                    level = line.split(' - ')[1].split(' - ')[0]
                    levels[level] = levels.get(level, 0) + 1
            
            print(f"\n📊 Theo mức độ:")
            for level, count in levels.items():
                print(f"  {level}: {count}")
            
            print(f"\n📅 Thời gian:")
            if lines:
                first_line = lines[0]
                last_line = lines[-1]
                print(f"  🕐 Bắt đầu: {first_line.split(' - ')[0] if ' - ' in first_line else 'Unknown'}")
                print(f"  🕐 Kết thúc: {last_line.split(' - ')[0] if ' - ' in last_line else 'Unknown'}")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Lỗi đọc thống kê: {e}")


def main():
    """Hàm main"""
    try:
        menu_system = IoTMenuSystem()
        menu_system.run()
    except Exception as e:
        print(f"❌ Lỗi khởi động: {e}")
        logging.error(f"Startup error: {e}")


if __name__ == "__main__":
    main()
