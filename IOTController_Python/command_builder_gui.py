#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IoT Command Builder
GUI để xây dựng và test lệnh HEX cho thiết bị IoT
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import threading
import time
from typing import Dict, List, Optional

from iot_controller import IoTController
from protocol import build_frame, verify_frame, normalize_hex_string

class CommandBuilderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("IoT Command Builder")
        self.root.geometry("800x600")
        
        self.controller = IoTController()
        self.device_commands = {}
        self.current_device = None
        
        self.setup_ui()
        self.load_com_ports()
        self.load_commands()
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Device selection
        ttk.Label(main_frame, text="Thiết bị:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(main_frame, textvariable=self.device_var, state="readonly")
        self.device_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        self.device_combo.bind('<<ComboboxSelected>>', self.on_device_selected)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Kết nối", padding="5")
        conn_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        conn_frame.columnconfigure(1, weight=1)
        
        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.com_var = tk.StringVar()
        self.com_combo = ttk.Combobox(conn_frame, textvariable=self.com_var, state="readonly")
        self.com_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        ttk.Label(conn_frame, text="Baudrate:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.baud_var = tk.StringVar(value="115200")
        self.baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var, 
                                      values=["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        self.connect_btn = ttk.Button(conn_frame, text="Kết nối", command=self.connect_device)
        self.connect_btn.grid(row=0, column=4, sticky=tk.W, pady=2, padx=(10, 0))
        
        self.status_label = ttk.Label(conn_frame, text="Chưa kết nối", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=5, sticky=tk.W, pady=2)
        
        # Command frame
        cmd_frame = ttk.LabelFrame(main_frame, text="Xây dựng lệnh", padding="5")
        cmd_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        cmd_frame.columnconfigure(1, weight=1)
        
        ttk.Label(cmd_frame, text="Command Code:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.cmd_code_var = tk.StringVar(value="0x01")
        self.cmd_code_entry = ttk.Entry(cmd_frame, textvariable=self.cmd_code_var)
        self.cmd_code_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        ttk.Label(cmd_frame, text="Instruction Code:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.ins_code_var = tk.StringVar(value="0x55")
        self.ins_code_combo = ttk.Combobox(cmd_frame, textvariable=self.ins_code_var,
                                          values=["0x55 (Query)", "0xAA (Set)"])
        self.ins_code_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        ttk.Label(cmd_frame, text="Data Bytes:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.data_var = tk.StringVar()
        self.data_entry = ttk.Entry(cmd_frame, textvariable=self.data_var)
        self.data_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Label(cmd_frame, text="(ví dụ: 1,0,255 hoặc 01 00 FF)").grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Preset commands frame
        preset_frame = ttk.LabelFrame(cmd_frame, text="Preset Commands", padding="5")
        preset_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        preset_frame.columnconfigure(0, weight=1)
        
        self.preset_buttons_frame = ttk.Frame(preset_frame)
        self.preset_buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Buttons frame
        btn_frame = ttk.Frame(cmd_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(btn_frame, text="Build Frame", command=self.build_frame).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Send Command", command=self.send_command).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT, padx=(0, 5))
        
        # Hex output frame
        hex_frame = ttk.LabelFrame(main_frame, text="Kết quả HEX", padding="5")
        hex_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        hex_frame.columnconfigure(0, weight=1)
        
        self.hex_output = scrolledtext.ScrolledText(hex_frame, height=4, state=tk.DISABLED)
        self.hex_output.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_output = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED)
        self.log_output.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).grid(row=1, column=0, sticky=tk.E, pady=(5, 0))
    
    def load_com_ports(self):
        """Load danh sách COM ports"""
        try:
            from serial.tools import list_ports
            ports = [port.device for port in list_ports.comports()]
            self.com_combo['values'] = ports
            if ports:
                self.com_combo.set(ports[0])
            self.log_message(f"Found {len(ports)} COM ports: {', '.join(ports)}")
        except Exception as e:
            self.log_message(f"Error loading COM ports: {e}")
    
    def load_commands(self):
        """Load lệnh từ config"""
        try:
            # Load từ devices.json
            if os.path.exists('devices.json'):
                with open('devices.json', 'r', encoding='utf-8') as f:
                    devices_data = json.load(f)
                
                device_names = []
                for device in devices_data.get('devices', []):
                    device_name = device['name']
                    device_names.append(device_name)
                    
                    # Load commands từ environment
                    env_key = device_name.upper().replace(' ', '_') + '_COMMANDS'
                    commands_str = os.getenv(env_key, '{}')
                    
                    try:
                        self.device_commands[device_name] = json.loads(commands_str)
                    except json.JSONDecodeError:
                        self.device_commands[device_name] = {}
                
                self.device_combo['values'] = device_names
                if device_names:
                    self.device_combo.set(device_names[0])
                    self.on_device_selected()
            
        except Exception as e:
            self.log_message(f"Error loading commands: {e}")
    
    def on_device_selected(self, event=None):
        """Xử lý khi chọn thiết bị"""
        device_name = self.device_var.get()
        if device_name in self.device_commands:
            commands = self.device_commands[device_name]
            self.log_message(f"Loaded {len(commands)} commands for {device_name}")
            
            # Update COM port based on device
            if device_name == "Cup-Dropping Machine":
                self.com_var.set("COM10")
                self.baud_var.set("115200")
            elif device_name == "Ice Maker":
                self.com_var.set("COM11")
                self.baud_var.set("115200")
            elif device_name == "Sensor Hub":
                self.com_var.set("COM12")
                self.baud_var.set("115200")
            elif device_name == "Máy Khuấy":
                self.com_var.set("COM14")
                self.baud_var.set("9600")
            
            # Create preset buttons
            self.create_preset_buttons(device_name, commands)
    
    def create_preset_buttons(self, device_name, commands):
        """Tạo các nút preset cho thiết bị"""
        # Clear existing buttons
        for widget in self.preset_buttons_frame.winfo_children():
            widget.destroy()
        
        if not commands:
            return
        
        row = 0
        col = 0
        max_cols = 4
        
        for cmd_id, cmd_data in commands.items():
            if isinstance(cmd_data, dict) and 'description' in cmd_data:
                btn_text = cmd_data['description'][:20] + "..." if len(cmd_data['description']) > 20 else cmd_data['description']
                btn = ttk.Button(
                    self.preset_buttons_frame, 
                    text=btn_text,
                    command=lambda cid=cmd_id, cdata=cmd_data: self.load_preset_command(cid, cdata)
                )
                btn.grid(row=row, column=col, padx=2, pady=2, sticky=(tk.W, tk.E))
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        
        # Configure grid weights
        for i in range(max_cols):
            self.preset_buttons_frame.columnconfigure(i, weight=1)
    
    def load_preset_command(self, cmd_id, cmd_data):
        """Load preset command vào form"""
        try:
            self.cmd_code_var.set(cmd_data.get('command_code', '0x01'))
            
            ins_code = cmd_data.get('instruction_code', '0x55')
            if ins_code == '0x55':
                self.ins_code_var.set('0x55 (Query)')
            elif ins_code == '0xAA':
                self.ins_code_var.set('0xAA (Set)')
            else:
                self.ins_code_var.set(ins_code)
            
            data_bytes = cmd_data.get('data_bytes', [])
            if data_bytes:
                data_str = ','.join(map(str, data_bytes))
                self.data_var.set(data_str)
            else:
                self.data_var.set('')
            
            self.log_message(f"Loaded preset command: {cmd_id}")
            
        except Exception as e:
            self.log_message(f"Error loading preset command: {e}")
    
    def connect_device(self):
        """Kết nối đến thiết bị"""
        try:
            com_port = self.com_var.get()
            baudrate = int(self.baud_var.get())
            
            if self.controller.is_open():
                self.controller.close()
            
            self.controller.open(com_port, baudrate=baudrate, timeout=2.0)
            
            if self.controller.is_open():
                self.status_label.config(text=f"Đã kết nối: {com_port}", foreground="green")
                self.connect_btn.config(text="Ngắt kết nối")
                self.log_message(f"Connected to {com_port} at {baudrate} baud")
            else:
                self.status_label.config(text="Kết nối thất bại", foreground="red")
                self.log_message(f"Failed to connect to {com_port}")
                
        except Exception as e:
            self.status_label.config(text=f"Lỗi: {e}", foreground="red")
            self.log_message(f"Connection error: {e}")
    
    def build_frame(self):
        """Xây dựng frame HEX"""
        try:
            cmd_code = int(self.cmd_code_var.get(), 16)
            ins_code_str = self.ins_code_var.get()
            
            # Parse instruction code
            if "0x55" in ins_code_str:
                ins_code = 0x55
            elif "0xAA" in ins_code_str:
                ins_code = 0xAA
            else:
                ins_code = int(ins_code_str, 16)
            
            # Parse data bytes
            data_str = self.data_var.get().strip()
            data_bytes = b""
            
            if data_str:
                # Try different formats
                if ',' in data_str:
                    # Format: 1,0,255
                    data_bytes = bytes([int(x.strip()) for x in data_str.split(',')])
                elif ' ' in data_str:
                    # Format: 01 00 FF
                    data_bytes = bytes.fromhex(data_str.replace(' ', ''))
                else:
                    # Format: 0100FF
                    data_bytes = bytes.fromhex(data_str)
            
            # Build frame
            frame = build_frame(cmd_code, ins_code, data_bytes)
            hex_result = frame.hex().upper()
            
            # Display result
            self.hex_output.config(state=tk.NORMAL)
            self.hex_output.delete(1.0, tk.END)
            self.hex_output.insert(tk.END, f"Command Code: 0x{cmd_code:02X}\n")
            self.hex_output.insert(tk.END, f"Instruction Code: 0x{ins_code:02X}\n")
            self.hex_output.insert(tk.END, f"Data Bytes: {data_bytes.hex().upper() if data_bytes else 'None'}\n")
            self.hex_output.insert(tk.END, f"Full Frame: {hex_result}\n")
            self.hex_output.insert(tk.END, f"Length: {len(frame)} bytes\n")
            self.hex_output.config(state=tk.DISABLED)
            
            self.log_message(f"Built frame: {hex_result}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to build frame: {e}")
            self.log_message(f"Build frame error: {e}")
    
    def send_command(self):
        """Gửi lệnh đến thiết bị"""
        if not self.controller.is_open():
            messagebox.showwarning("Warning", "Please connect to device first!")
            return
        
        try:
            cmd_code = int(self.cmd_code_var.get(), 16)
            ins_code_str = self.ins_code_var.get()
            
            # Parse instruction code
            if "0x55" in ins_code_str:
                ins_code = 0x55
            elif "0xAA" in ins_code_str:
                ins_code = 0xAA
            else:
                ins_code = int(ins_code_str, 16)
            
            # Parse data bytes
            data_str = self.data_var.get().strip()
            data_bytes = b""
            
            if data_str:
                if ',' in data_str:
                    data_bytes = bytes([int(x.strip()) for x in data_str.split(',')])
                elif ' ' in data_str:
                    data_bytes = bytes.fromhex(data_str.replace(' ', ''))
                else:
                    data_bytes = bytes.fromhex(data_str)
            
            # Build và gửi frame
            frame = build_frame(cmd_code, ins_code, data_bytes)
            written = self.controller.send_hex(frame.hex())
            
            self.log_message(f"Sent {written} bytes: {frame.hex().upper()}")
            
            # Đọc phản hồi
            response = self.controller.read_frame(2.0)
            if response:
                self.log_message(f"Response: {response.hex().upper()}")
                
                if verify_frame(response):
                    self.log_message("✅ Frame hợp lệ!")
                else:
                    self.log_message("⚠️ Frame không hợp lệ!")
            else:
                self.log_message("⏰ Không có phản hồi")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {e}")
            self.log_message(f"Send command error: {e}")
    
    def test_connection(self):
        """Test kết nối"""
        if not self.controller.is_open():
            messagebox.showwarning("Warning", "Please connect to device first!")
            return
        
        def test_thread():
            try:
                self.log_message("Testing connection...")
                
                # Send a simple status query
                test_frame = build_frame(0x01, 0x55, b"")
                written = self.controller.send_hex(test_frame.hex())
                
                self.log_message(f"Test frame sent: {written} bytes")
                
                response = self.controller.read_frame(2.0)
                if response:
                    self.log_message(f"Test response: {response.hex().upper()}")
                    self.log_message("✅ Connection test successful!")
                else:
                    self.log_message("❌ Connection test failed - no response")
                    
            except Exception as e:
                self.log_message(f"❌ Connection test error: {e}")
        
        # Run test in separate thread
        threading.Thread(target=test_thread, daemon=True).start()
    
    def log_message(self, message):
        """Thêm message vào log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_output.config(state=tk.NORMAL)
        self.log_output.insert(tk.END, log_entry)
        self.log_output.see(tk.END)
        self.log_output.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Xóa log"""
        self.log_output.config(state=tk.NORMAL)
        self.log_output.delete(1.0, tk.END)
        self.log_output.config(state=tk.DISABLED)


def main():
    """Main function"""
    root = tk.Tk()
    app = CommandBuilderGUI(root)
    
    # Handle window close
    def on_closing():
        if app.controller.is_open():
            app.controller.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
