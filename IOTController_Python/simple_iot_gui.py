#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple IoT Controller GUI
Chỉ hỗ trợ kết nối thiết bị và gửi mã hex
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import sys
import time
import codecs
from serial.tools import list_ports

# Cấu hình UTF-8 cho Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Thêm đường dẫn hiện tại vào sys.path
sys.path.insert(0, os.path.dirname(__file__))

from iot_controller import IoTController

class SimpleIoTGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 Simple IoT Controller")
        self.root.geometry("600x500")
        self.root.configure(bg='#f0f0f0')
        
        self.controller = IoTController()
        self.devices = {}
        self.is_connected = False
        
        self.setup_ui()
        self.load_devices()
        self.load_com_ports()
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Device selection frame
        device_frame = ttk.Frame(main_frame)
        device_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        device_frame.columnconfigure(1, weight=1)
        
        ttk.Label(device_frame, text="Thiết bị:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.device_var, state="readonly")
        self.device_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        self.device_combo.bind('<<ComboboxSelected>>', self.on_device_selected)
        
        ttk.Button(device_frame, text="+ Thêm thiết bị", command=self.add_device).grid(row=0, column=2, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Kết nối", padding="5")
        conn_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        conn_frame.columnconfigure(1, weight=1)
        
        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.com_var = tk.StringVar()
        self.com_combo = ttk.Combobox(conn_frame, textvariable=self.com_var, state="readonly")
        self.com_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        ttk.Label(conn_frame, text="Baudrate:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.baud_var = tk.StringVar()
        self.baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var, 
                                      values=["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        self.connect_btn = ttk.Button(conn_frame, text="Kết nối", command=self.connect_device)
        self.connect_btn.grid(row=0, column=4, sticky=tk.W, pady=2, padx=(10, 0))
        
        self.status_label = ttk.Label(conn_frame, text="Chưa kết nối", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=5, sticky=tk.W, pady=2)
        
        # Hex input frame
        hex_frame = ttk.LabelFrame(main_frame, text="Gửi lệnh (GO hoặc 5 để chạy thiết bị)", padding="5")
        hex_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        hex_frame.columnconfigure(1, weight=1)
        
        ttk.Label(hex_frame, text="Lệnh:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.hex_var = tk.StringVar()
        self.hex_entry = ttk.Entry(hex_frame, textvariable=self.hex_var, font=("Courier", 10))
        self.hex_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.hex_entry.bind('<Return>', lambda e: self.send_raw_hex())
        
        ttk.Button(hex_frame, text="Gửi", command=self.send_raw_hex).grid(row=0, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        ttk.Button(hex_frame, text="Clear", command=self.clear_log).grid(row=0, column=3, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_output = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED)
        self.log_output.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).grid(row=1, column=0, sticky=tk.E, pady=(5, 0))
    
    def load_devices(self):
        """Load tất cả thiết bị từ config.env (dạng KEY=COM,BAUD)."""
        try:
            self.devices = {}
            config_path = os.path.join(os.path.dirname(__file__), 'config.env')
            if not os.path.exists(config_path):
                # Không có file, coi như chưa có thiết bị
                self.device_combo['values'] = []
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if not value or ',' not in value:
                        continue
                    com_part, baud_part = value.split(',', 1)
                    com_part = com_part.strip()
                    baud_part = baud_part.strip()
                    # Tên hiển thị dùng đúng key người dùng đã lưu (giữ nguyên chữ hoa/thường và dấu cách nếu có)
                    display_name = key
                    self.devices[display_name] = {'com': com_part, 'baud': baud_part}
            
            device_list = list(self.devices.keys())
            self.device_combo['values'] = device_list
            if device_list:
                # Nếu đã chọn trước đó thì giữ nguyên, nếu không chọn phần tử đầu tiên
                current = self.device_var.get()
                if current in self.devices:
                    self.device_combo.set(current)
                else:
                    self.device_combo.set(device_list[0])
                self.on_device_selected()
            
            self.log_message(f"Loaded {len(self.devices)} devices from config.env")
        except Exception as e:
            self.log_message(f"Error loading devices: {e}")
    
    def load_com_ports(self):
        """Load danh sách COM ports"""
        try:
            ports = [port.device for port in list_ports.comports()]
            self.com_combo['values'] = ports
            if ports:
                self.com_combo.set(ports[0])
            self.log_message(f"Found {len(ports)} COM ports: {', '.join(ports)}")
        except Exception as e:
            self.log_message(f"Error loading COM ports: {e}")
    
    def on_device_selected(self, event=None):
        """Xử lý khi chọn thiết bị"""
        device_name = self.device_var.get()
        if device_name in self.devices:
            device_info = self.devices[device_name]
            self.com_var.set(device_info['com'])
            self.baud_var.set(device_info['baud'])
            self.log_message(f"Selected device: {device_name} ({device_info['com']}, {device_info['baud']})")
    
    def connect_device(self):
        """Kết nối thiết bị"""
        if self.is_connected:
            self.disconnect_device()
            return
        
        try:
            com_port = self.com_var.get()
            baudrate = int(self.baud_var.get())
            
            if not com_port:
                messagebox.showerror("Lỗi", "Vui lòng chọn COM port!")
                return
            
            self.log_message(f"Connecting to {com_port} at {baudrate} baud...")
            
            # Kết nối
            self.controller.open(com_port, baudrate)
            
            self.is_connected = True
            self.connect_btn.config(text="Ngắt kết nối")
            self.status_label.config(text=f"Đã kết nối: {com_port}", foreground="green")
            self.log_message(f"✅ Connected to {com_port} at {baudrate} baud")
            
        except Exception as e:
            self.log_message(f"❌ Connection failed: {e}")
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối: {e}")
    
    def disconnect_device(self):
        """Ngắt kết nối thiết bị"""
        try:
            if hasattr(self.controller, 'ser') and self.controller.ser and self.controller.ser.is_open:
                self.controller.close()
            elif hasattr(self.controller, 'close'):
                self.controller.close()
            
            self.is_connected = False
            self.connect_btn.config(text="Kết nối")
            self.status_label.config(text="Chưa kết nối", foreground="red")
            self.log_message("🔌 Disconnected")
            
        except Exception as e:
            self.log_message(f"❌ Disconnect error: {e}")
    
    def send_hex(self):
        """Gửi mã hex"""
        if not self.is_connected:
            messagebox.showerror("Lỗi", "Chưa kết nối thiết bị!")
            return
        
        hex_string = self.hex_var.get().strip()
        if not hex_string:
            messagebox.showerror("Lỗi", "Vui lòng nhập mã hex!")
            return
        
        try:
            # Chuyển hex string thành bytes
            hex_clean = hex_string.replace(' ', '').replace('-', '').upper()
            
            # Kiểm tra ký tự hợp lệ
            valid_chars = set('0123456789ABCDEF')
            if not all(c in valid_chars for c in hex_clean):
                invalid_chars = [c for c in hex_clean if c not in valid_chars]
                raise ValueError(f"Invalid hex characters: {invalid_chars}")
            
            # Xử lý số đơn lẻ (thêm 0 ở đầu)
            original_hex = hex_clean
            if len(hex_clean) == 1:
                hex_clean = '0' + hex_clean
                self.log_message(f"🔧 Auto-padded single digit: {original_hex} → {hex_clean}")
            elif len(hex_clean) % 2 == 1:
                hex_clean = '0' + hex_clean
                self.log_message(f"🔧 Auto-padded odd length: {original_hex} → {hex_clean}")
            
            data = bytes.fromhex(hex_clean)
            
            # Debug: Hiển thị dữ liệu sẽ gửi
            self.log_message(f"🔍 Debug - Raw data: {data.hex().upper()}")
            self.log_message(f"🔍 Debug - Data length: {len(data)} bytes")
            self.log_message(f"🔍 Debug - Data bytes: {[hex(b) for b in data]}")
            
            # Gửi dữ liệu
            if hasattr(self.controller, 'ser') and self.controller.ser:
                written = self.controller.ser.write(data)
                self.controller.ser.flush()
                
                self.log_message(f"📤 Sent {written} bytes: {hex_string}")
                
                # Đọc phản hồi
                time.sleep(0.1)
                if self.controller.ser.in_waiting > 0:
                    response = self.controller.ser.read(self.controller.ser.in_waiting)
                    self.log_message(f"📥 Response: {response.hex().upper()}")
                else:
                    self.log_message("📥 No response")
            else:
                # Fallback: sử dụng send_frame nếu có
                if hasattr(self.controller, 'send_frame'):
                    # Chuyển hex string thành command_code, instruction_code, data
                    if len(data) >= 1:
                        cmd_code = data[0]
                        ins_code = data[1] if len(data) > 1 else 0x55
                        data_bytes = data[2:] if len(data) > 2 else b''
                        written = self.controller.send_frame(cmd_code, ins_code, data_bytes.hex())
                        self.log_message(f"📤 Sent {written} bytes via send_frame: {hex_string}")
                    else:
                        self.log_message("❌ Data too short for send_frame")
                else:
                    self.log_message("❌ No serial connection available")
            
            # Clear input
            self.hex_var.set("")
            
        except ValueError as e:
            self.log_message(f"❌ Invalid hex format: {e}")
            messagebox.showerror("Lỗi", f"Mã hex không hợp lệ: {e}\n\n💡 Chỉ sử dụng: 0-9, A-F\nVí dụ: 01, FF, 1234, ABCD")
        except Exception as e:
            self.log_message(f"❌ Send error: {e}")
            messagebox.showerror("Lỗi", f"Không thể gửi: {e}")
    
    def send_raw_hex(self):
        """Gửi lệnh đến thiết bị"""
        if not self.is_connected:
            messagebox.showerror("Lỗi", "Chưa kết nối thiết bị!")
            return
        
        command = self.hex_var.get().strip().upper()
        if not command:
            messagebox.showerror("Lỗi", "Vui lòng nhập lệnh!")
            return
        
        try:
            # Xử lý lệnh
            if command.upper() == "GO":
                # ASCII "GO"
                data = b"GO"
                self.log_message(f"🔧 Sending ASCII: {command}")
            elif command.isdigit():
                # ASCII số (như "5" -> "5")
                data = command.encode('ascii')
                self.log_message(f"🔧 Sending ASCII: {command}")
            else:
                # ASCII khác
                data = command.encode('ascii')
                self.log_message(f"🔧 Sending ASCII: {command}")
            
            # Debug: Hiển thị dữ liệu sẽ gửi
            self.log_message(f"🔍 Raw Debug - Data: {data.hex().upper()}")
            self.log_message(f"🔍 Raw Debug - Length: {len(data)} bytes")
            self.log_message(f"🔍 Raw Debug - Bytes: {[hex(b) for b in data]}")
            
            # Gửi raw data qua serial
            if hasattr(self.controller, '_ser') and self.controller._ser and self.controller._ser.is_open:
                written = self.controller._ser.write(data)
                self.controller._ser.flush()
                
                self.log_message(f"📤 Raw Sent {written} bytes: {command}")
                
                # Đọc phản hồi với timeout dài hơn
                time.sleep(1.0)  # Chờ lâu hơn để nhận phản hồi
                if self.controller._ser.in_waiting > 0:
                    response = self.controller._ser.read(self.controller._ser.in_waiting)
                    self.log_message(f"📥 Raw Response: {response.hex().upper()}")
                    self.log_message(f"📥 Raw Response Length: {len(response)} bytes")
                    if response:
                        try:
                            response_text = response.decode('utf-8', errors='ignore').strip()
                            self.log_message(f"📥 Raw Response Text: '{response_text}'")
                        except:
                            pass
                else:
                    self.log_message("📥 No raw response")
            else:
                self.log_message("❌ No serial connection for raw send")
                self.log_message(f"🔍 Debug - hasattr _ser: {hasattr(self.controller, '_ser')}")
                if hasattr(self.controller, '_ser'):
                    self.log_message(f"🔍 Debug - _ser is None: {self.controller._ser is None}")
                    if self.controller._ser:
                        self.log_message(f"🔍 Debug - _ser.is_open: {self.controller._ser.is_open}")
            
            # Clear input
            self.hex_var.set("")
            
        except ValueError as e:
            self.log_message(f"❌ Invalid hex format: {e}")
            messagebox.showerror("Lỗi", f"Mã hex không hợp lệ: {e}\n\n💡 Chỉ sử dụng: 0-9, A-F\nVí dụ: 01, FF, 1234, ABCD")
        except Exception as e:
            self.log_message(f"❌ Raw send error: {e}")
            messagebox.showerror("Lỗi", f"Không thể gửi raw: {e}")
    
    def log_message(self, message):
        """Thêm message vào log"""
        timestamp = time.strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {message}\n"
        
        self.log_output.config(state=tk.NORMAL)
        self.log_output.insert(tk.END, log_text)
        self.log_output.see(tk.END)
        self.log_output.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Xóa log"""
        self.log_output.config(state=tk.NORMAL)
        self.log_output.delete(1.0, tk.END)
        self.log_output.config(state=tk.DISABLED)
    
    def add_device(self):
        """Thêm thiết bị mới"""
        # Tạo dialog để nhập thông tin thiết bị
        dialog = tk.Toplevel(self.root)
        dialog.title("Thêm thiết bị mới")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Form fields
        ttk.Label(dialog, text="Tên thiết bị:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=10)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=10)
        
        ttk.Label(dialog, text="COM Port:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=10)
        com_var = tk.StringVar()
        com_combo = ttk.Combobox(dialog, textvariable=com_var, state="readonly", width=27)
        com_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=10)
        
        # Load available COM ports (ẩn các COM đã được sử dụng)
        try:
            all_ports = [port.device for port in list_ports.comports()]
            used_ports = {info['com'].upper() for info in self.devices.values()}
            available_ports = [port for port in all_ports if port.upper() not in used_ports]
            com_combo['values'] = available_ports
            if available_ports:
                com_combo.set(available_ports[0])
        except Exception:
            com_combo['values'] = []
        
        ttk.Label(dialog, text="Baudrate:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=10)
        baud_var = tk.StringVar(value="115200")
        baud_combo = ttk.Combobox(dialog, textvariable=baud_var, 
                                 values=["9600", "19200", "38400", "57600", "115200"], width=27)
        baud_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=10)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        def save_device():
            name = name_var.get().strip()
            com = com_var.get().strip()
            baud = baud_var.get().strip()
            
            if not name or not com or not baud:
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin!")
                return
            
            try:
                # Validate baudrate
                int(baud)
            except ValueError:
                messagebox.showerror("Lỗi", "Baudrate phải là số!")
                return
            
            # Cảnh báo nếu COM đã được dùng bởi thiết bị khác (chỉ khi thực sự trùng)
            for dev_name, dev_info in self.devices.items():
                if dev_info.get('com', '').upper() == com.upper():
                    if not messagebox.askyesno(
                        "Trùng COM",
                        f"COM {com} đang được dùng bởi '{dev_name}'.\nBạn vẫn muốn lưu thiết bị mới?"
                    ):
                        return
                    break  # Chỉ cảnh báo một lần

            # Save to config.env
            try:
                self.save_device_to_config(name, com, baud)
                # Reload toàn bộ danh sách từ file để đồng bộ
                self.load_devices()
                self.log_message(f"✅ Đã thêm thiết bị: {name} ({com}, {baud})")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu thiết bị: {e}")
        
        ttk.Button(button_frame, text="Lưu", command=save_device).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Hủy", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Focus on name entry
        name_entry.focus()
    
    def save_device_to_config(self, name, com, baud):
        """Lưu thiết bị vào config.env"""
        try:
            # Sử dụng đường dẫn tuyệt đối
            config_path = os.path.join(os.path.dirname(__file__), 'config.env')
            
            # Đọc file hiện tại
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # Tìm và cập nhật hoặc thêm thiết bị mới
            device_key = name.upper().replace(' ', '_').replace('-', '_')
            new_line = f"{device_key}={com},{baud}\n"
            
            # Kiểm tra xem thiết bị đã tồn tại chưa
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{device_key}="):
                    lines[i] = new_line
                    updated = True
                    break
            
            # Nếu chưa tồn tại, thêm mới
            if not updated:
                # Đảm bảo dòng cuối có xuống dòng (chỉ 1 lần)
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] = lines[-1] + '\n'
                # Thêm thiết bị mới
                lines.append(new_line)
            
            # Ghi lại file
            with open(config_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            self.log_message(f"💾 Saved to {config_path}")
                
        except Exception as e:
            raise Exception(f"Lỗi ghi file config.env: {e}")
    
    def refresh_device_list(self):
        """Làm mới danh sách thiết bị"""
        device_list = list(self.devices.keys())
        self.device_combo['values'] = device_list
        if device_list:
            self.device_combo.set(device_list[0])
            self.on_device_selected()

def main():
    """Hàm chính"""
    root = tk.Tk()
    app = SimpleIoTGUI(root)
    
    # Xử lý đóng cửa sổ
    def on_closing():
        if app.is_connected:
            app.disconnect_device()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
