#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arm Controller GUI - Giao diện đồ họa cho điều khiển robot Fairino
Author: Generated for Arm_FR5 project
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import glob
import math

# Thêm SDK path vào sys.path
SDK_PATH = os.path.join(os.path.dirname(__file__), 'fairino_sdk')
if os.path.exists(SDK_PATH):
    sys.path.insert(0, SDK_PATH)

try:
    from fairino import Robot
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

class ArmControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🦾 FAIRINO ROBOT CONTROL - GUI")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Thiết lập icon con trỏ thành cánh tay robot
        try:
            self.setup_robot_cursor()
        except Exception as e:
            print(f"Không thể thiết lập cursor: {e}")
        
        # Robot connection
        self.robot = None
        self.connected = False
        self.auto_mode = False
        
        # Lua files
        self.lua_files = []
        self.db_files = []
        
        self.setup_ui()
        self.load_files()
        
    def setup_ui(self):
        """Thiết lập giao diện"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🦾 FAIRINO ROBOT CONTROL", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Connection frame
        self.setup_connection_frame(main_frame)
        
        # Control frame
        self.setup_control_frame(main_frame)
        
        # Status frame
        self.setup_status_frame(main_frame)
        
    def setup_connection_frame(self, parent):
        """Thiết lập frame kết nối"""
        conn_frame = ttk.LabelFrame(parent, text="🔌 Kết nối Robot", padding="10")
        conn_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # IP Address
        ttk.Label(conn_frame, text="IP Address:").grid(row=0, column=0, padx=(0, 5))
        self.ip_var = tk.StringVar(value="192.168.58.2")
        ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=15)
        ip_entry.grid(row=0, column=1, padx=(0, 10))
        
        # Connect button
        self.connect_btn = ttk.Button(conn_frame, text="🔗 Kết nối", 
                                     command=self.connect_robot)
        self.connect_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Disconnect button
        self.disconnect_btn = ttk.Button(conn_frame, text="❌ Ngắt kết nối", 
                                        command=self.disconnect_robot, state='disabled')
        self.disconnect_btn.grid(row=0, column=3, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(conn_frame, text="⚪ Chưa kết nối", 
                                     foreground='red')
        self.status_label.grid(row=0, column=4, padx=(10, 0))
        
    def setup_control_frame(self, parent):
        """Thiết lập frame điều khiển"""
        control_frame = ttk.LabelFrame(parent, text="🎮 Điều khiển Robot", padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Lua files section
        lua_frame = ttk.LabelFrame(control_frame, text="📄 File Lua", padding="5")
        lua_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Lua files listbox
        self.lua_listbox = tk.Listbox(lua_frame, height=6)
        self.lua_listbox.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Lua buttons
        ttk.Button(lua_frame, text="🔄 Làm mới", 
                   command=self.load_lua_files).grid(row=1, column=0, pady=(5, 0))
        ttk.Button(lua_frame, text="📤 Upload", 
                   command=self.upload_lua).grid(row=1, column=1, pady=(5, 0))
        ttk.Button(lua_frame, text="📁 Import Lua", 
                   command=self.import_lua_file).grid(row=1, column=2, pady=(5, 0))
        ttk.Button(lua_frame, text="▶️ Chạy", 
                   command=self.run_lua).grid(row=2, column=0, pady=(5, 0))
        
        # Database files section
        db_frame = ttk.LabelFrame(control_frame, text="🗄️ Database Files", padding="5")
        db_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # DB files listbox
        self.db_listbox = tk.Listbox(db_frame, height=6)
        self.db_listbox.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # DB buttons
        ttk.Button(db_frame, text="🔄 Làm mới", 
                   command=self.load_db_files).grid(row=1, column=0, pady=(5, 0))
        ttk.Button(db_frame, text="📤 Upload & Activate", 
                   command=self.upload_activate_db).grid(row=1, column=1, pady=(5, 0))
        ttk.Button(db_frame, text="📁 Import DB", 
                   command=self.import_db_file).grid(row=1, column=2, pady=(5, 0))
        
        # Robot control section
        robot_frame = ttk.LabelFrame(control_frame, text="🦾 Điều khiển Robot", padding="5")
        robot_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Robot info button
        ttk.Button(robot_frame, text="ℹ️ Thông tin Robot", 
                   command=self.get_robot_info).grid(row=0, column=0, pady=5)
        
        
        # Debug methods button
        ttk.Button(robot_frame, text="🔍 Debug Methods", 
                   command=self.debug_robot_methods).grid(row=1, column=0, pady=5)
        
    def setup_status_frame(self, parent):
        """Thiết lập frame trạng thái"""
        status_frame = ttk.LabelFrame(parent, text="📊 Trạng thái & Log", padding="10")
        status_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        # Status text
        self.status_text = scrolledtext.ScrolledText(status_frame, height=20, width=50)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear button
        ttk.Button(status_frame, text="🗑️ Xóa Log", 
                   command=self.clear_log).grid(row=1, column=0, pady=(5, 0))
        
    def log_message(self, message):
        """Ghi log message"""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """Xóa log"""
        self.status_text.delete(1.0, tk.END)
        
    def load_files(self):
        """Tải danh sách files"""
        self.load_lua_files()
        self.load_db_files()
    
    def setup_robot_cursor(self):
        """Thiết lập cursor thành cánh tay robot"""
        try:
            # Sử dụng cursor hand2 làm thay thế cho cánh tay robot
            self.root.configure(cursor="hand2")
        except Exception as e:
            # Fallback: sử dụng cursor mặc định
            self.root.configure(cursor="arrow")
        
    def load_lua_files(self):
        """Tải danh sách file Lua"""
        self.lua_files = []
        self.lua_listbox.delete(0, tk.END)
        
        # Sử dụng thư mục lua_scripts như console version với đường dẫn đầy đủ
        lua_dir = os.path.join(os.path.dirname(__file__), 'lua_scripts')
        if os.path.exists(lua_dir):
            files = [f for f in os.listdir(lua_dir) if f.endswith('.lua')]
            for file in sorted(files):
                full_path = os.path.join(lua_dir, file)
                self.lua_files.append(full_path)
                self.lua_listbox.insert(tk.END, file)
        else:
            # Fallback: tìm file .lua ở thư mục hiện tại
            files = glob.glob("*.lua")
            for file in sorted(files):
                self.lua_files.append(file)
                self.lua_listbox.insert(tk.END, os.path.basename(file))
            
        self.log_message(f"Đã tải {len(self.lua_files)} file Lua từ {lua_dir if os.path.exists(lua_dir) else 'thư mục hiện tại'}")
        
    def load_db_files(self):
        """Tải danh sách file Database - sử dụng code từ console version"""
        self.db_files = []
        self.db_listbox.delete(0, tk.END)
        
        # Sử dụng thư mục TechPoint_db như console version với đường dẫn đầy đủ
        techpoint_dir = os.path.join(os.path.dirname(__file__), 'TechPoint_db')
        if os.path.exists(techpoint_dir):
            files = [f for f in os.listdir(techpoint_dir) if f.endswith(('.db', '.sqlite', '.sqlite3'))]
            for file in sorted(files):
                full_path = os.path.join(techpoint_dir, file)
                self.db_files.append(full_path)
                self.db_listbox.insert(tk.END, file)
        else:
            # Fallback: tìm file .db ở thư mục hiện tại
            files = glob.glob("*.db")
            for file in sorted(files):
                self.db_files.append(file)
                self.db_listbox.insert(tk.END, os.path.basename(file))
            
        self.log_message(f"Đã tải {len(self.db_files)} file Database từ {techpoint_dir if os.path.exists(techpoint_dir) else 'thư mục hiện tại'}")
        
    def connect_robot(self):
        """Kết nối robot"""
        if not SDK_AVAILABLE:
            messagebox.showerror("Lỗi", "SDK không khả dụng!")
            return
            
        def connect_thread():
            try:
                self.log_message("🔌 Đang kết nối robot...")
                ip = self.ip_var.get()
                self.robot = Robot.RPC(ip)
                
                # Kiểm tra kết nối
                try:
                    version = self.robot.GetSDKVersion()
                    self.log_message(f"✅ Kết nối thành công! SDK Version: {version}")
                    
                    # Kiểm tra chế độ auto
                    try:
                        mode = self.robot.GetRobotMode()
                        if mode[0] == 0:  # Auto mode
                            self.auto_mode = True
                            self.log_message("✅ Robot đang ở chế độ Auto")
                        else:
                            self.log_message("⚠️ Robot không ở chế độ Auto")
                            # Thử chuyển sang auto mode
                            self.robot.Mode(0)
                            self.auto_mode = True
                            self.log_message("✅ Đã chuyển robot sang chế độ Auto")
                    except:
                        self.log_message("⚠️ Không thể kiểm tra chế độ robot")
                    
                    self.connected = True
                    self.root.after(0, self.update_connection_status)
                    
                except Exception as e:
                    self.log_message(f"❌ Lỗi kết nối: {e}")
                    
            except Exception as e:
                self.log_message(f"❌ Lỗi kết nối: {e}")
                
        threading.Thread(target=connect_thread, daemon=True).start()
        
    def disconnect_robot(self):
        """Ngắt kết nối robot"""
        if self.robot:
            try:
                self.robot.CloseRPC()
                self.log_message("👋 Đã ngắt kết nối robot")
            except:
                pass
        self.robot = None
        self.connected = False
        self.auto_mode = False
        self.update_connection_status()
        
    def update_connection_status(self):
        """Cập nhật trạng thái kết nối"""
        if self.connected:
            self.status_label.config(text="🟢 Đã kết nối", foreground='green')
            self.connect_btn.config(state='disabled')
            self.disconnect_btn.config(state='normal')
        else:
            self.status_label.config(text="🔴 Chưa kết nối", foreground='red')
            self.connect_btn.config(state='normal')
            self.disconnect_btn.config(state='disabled')
            
    def upload_lua(self):
        """Upload file Lua"""
        if not self.connected:
            messagebox.showerror("Lỗi", "Chưa kết nối robot!")
            return
            
        selection = self.lua_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file Lua!")
            return
            
        file_path = self.lua_files[selection[0]]
        
        def upload_thread():
            try:
                self.log_message(f"📤 Đang upload {os.path.basename(file_path)}...")
                
                # Upload file Lua - sử dụng method từ console version
                try:
                    full_path = os.path.abspath(file_path)
                    self.log_message(f"📁 Upload file: {full_path}")
                    self.log_message(f"📁 File tồn tại: {os.path.exists(full_path)}")
                    
                    # Thử LuaUpload
                    if hasattr(self.robot, 'LuaUpload'):
                        try:
                            self.log_message("🔄 Đang gọi LuaUpload...")
                            result = self.robot.LuaUpload(full_path)
                            self.log_message(f"📋 LuaUpload result: {result} (type: {type(result)})")
                            
                            if isinstance(result, tuple):
                                err, msg = result
                                if err == 0:
                                    self.log_message("✅ Upload thành công! (LuaUpload)")
                                else:
                                    self.log_message(f"❌ LuaUpload thất bại: {err} - {msg}")
                            else:
                                if int(result) == 0:
                                    self.log_message("✅ Upload thành công! (LuaUpload)")
                                else:
                                    self.log_message(f"❌ LuaUpload thất bại: {result}")
                                    
                        except Exception as e:
                            self.log_message(f"❌ LuaUpload exception: {e}")
                    else:
                        self.log_message("❌ LuaUpload method không có sẵn")
                        
                except Exception as e:
                    self.log_message(f"❌ Lỗi upload: {e}")
                    
            except Exception as e:
                self.log_message(f"❌ Lỗi upload: {e}")
                
        threading.Thread(target=upload_thread, daemon=True).start()
        
    def run_lua(self):
        """Chạy file Lua"""
        if not self.connected:
            messagebox.showerror("Lỗi", "Chưa kết nối robot!")
            return
            
        selection = self.lua_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file Lua!")
            return
            
        file_path = self.lua_files[selection[0]]
        
        def run_thread():
            try:
                self.log_message(f"▶️ Đang chạy {os.path.basename(file_path)}...")
                
                # Chạy file Lua - sử dụng method từ console version
                try:
                    filename = os.path.basename(file_path)
                    remote_path = f"/fruser/{filename}"
                    
                    # Thử SDK ProgramLoad/ProgramRun trước
                    if hasattr(self.robot, 'ProgramLoad') and hasattr(self.robot, 'ProgramRun'):
                        try:
                            load_result = self.robot.ProgramLoad(remote_path)
                            self.log_message(f"ProgramLoad kết quả: {load_result}")
                            
                            if int(load_result) == 0:
                                run_result = self.robot.ProgramRun()
                                self.log_message(f"ProgramRun kết quả: {run_result}")
                                
                                if int(run_result) == 0:
                                    self.log_message("✅ Chạy thành công! (SDK)")
                                else:
                                    self.log_message(f"❌ SDK ProgramRun thất bại: {run_result}")
                            else:
                                self.log_message(f"❌ SDK ProgramLoad thất bại: {load_result}")
                                
                        except Exception as e:
                            self.log_message(f"❌ SDK ProgramLoad/Run thất bại: {e}")
                    
                    # Fallback: XML-RPC
                    else:
                        try:
                            load_result = self.robot.ProgramLoad(remote_path)
                            self.log_message(f"ProgramLoad kết quả: {load_result}")
                            
                            if int(load_result) == 0:
                                run_result = self.robot.ProgramRun()
                                self.log_message(f"ProgramRun kết quả: {run_result}")
                                
                                if int(run_result) == 0:
                                    self.log_message("✅ Chạy thành công! (XML-RPC)")
                                else:
                                    self.log_message(f"❌ XML-RPC ProgramRun thất bại: {run_result}")
                            else:
                                self.log_message(f"❌ XML-RPC ProgramLoad thất bại: {load_result}")
                                
                        except Exception as e:
                            self.log_message(f"❌ XML-RPC ProgramLoad/Run thất bại: {e}")
                        
                except Exception as e:
                    self.log_message(f"❌ Lỗi chạy Lua: {e}")
                    
            except Exception as e:
                self.log_message(f"❌ Lỗi chạy: {e}")
                
        threading.Thread(target=run_thread, daemon=True).start()
        
    def upload_activate_db(self):
        """Upload và activate database"""
        if not self.connected:
            messagebox.showerror("Lỗi", "Chưa kết nối robot!")
            return
            
        selection = self.db_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file Database!")
            return
            
        file_path = self.db_files[selection[0]]
        
        def upload_activate_thread():
            try:
                self.log_message(f"📤 Đang upload {os.path.basename(file_path)}...")
                
                # Upload database
                try:
                    result = self.robot.PointTableUpLoad(file_path)
                    self.log_message(f"📤 Upload result: {result}")
                except Exception as e:
                    self.log_message(f"⚠️ Upload lỗi: {e}")
                
                # Activate database
                try:
                    db_name = os.path.basename(file_path)
                    result = self.robot.PointTableSwitch(db_name)
                    if int(result) == 0:
                        self.log_message("✅ Database đã được activate!")
                    else:
                        self.log_message(f"⚠️ Activate result: {result}")
                except Exception as e:
                    self.log_message(f"❌ Activate lỗi: {e}")
                    
            except Exception as e:
                self.log_message(f"❌ Lỗi: {e}")
                
        threading.Thread(target=upload_activate_thread, daemon=True).start()
        
    def get_robot_info(self):
        """Lấy thông tin robot - sử dụng code từ console version"""
        if not self.connected:
            messagebox.showerror("Lỗi", "Chưa kết nối robot!")
            return
            
        def info_thread():
            try:
                self.log_message("ℹ️ Đang lấy thông tin robot...")
                
                # SDK Version - sử dụng code từ console
                try:
                    version = self.robot.GetSDKVersion()
                    if isinstance(version, tuple):
                        err, version_info = version
                        if err == 0:
                            self.log_message(f"📋 SDK Version: {version_info}")
                        else:
                            self.log_message(f"⚠️ SDK Version lỗi: {err}")
                    else:
                        self.log_message(f"📋 SDK Version: {version}")
                except Exception as e:
                    self.log_message(f"⚠️ Không thể lấy SDK version: {e}")
                
                # Controller IP - sử dụng code từ console
                try:
                    ip = self.robot.GetControllerIP()
                    if isinstance(ip, tuple):
                        err, ip_info = ip
                        if err == 0:
                            self.log_message(f"🌐 Controller IP: {ip_info}")
                        else:
                            self.log_message(f"⚠️ Controller IP lỗi: {err}")
                    else:
                        self.log_message(f"🌐 Controller IP: {ip}")
                except Exception as e:
                    self.log_message(f"⚠️ Không thể lấy IP: {e}")
                
                # Robot Mode - sử dụng code từ console
                try:
                    mode = self.robot.GetRobotMode()
                    if isinstance(mode, tuple):
                        err, mode_info = mode
                        if err == 0:
                            mode_text = "Auto" if mode_info == 0 else "Manual"
                            self.log_message(f"🎮 Robot Mode: {mode_text} ({mode_info})")
                        else:
                            self.log_message(f"⚠️ Robot Mode lỗi: {err}")
                    else:
                        mode_text = "Auto" if mode == 0 else "Manual"
                        self.log_message(f"🎮 Robot Mode: {mode_text} ({mode})")
                except Exception as e:
                    self.log_message(f"⚠️ Không thể lấy mode: {e}")
                
                # Software Version - thêm từ console
                try:
                    software = self.robot.GetSoftwareVersion()
                    if isinstance(software, tuple):
                        err, software_info = software
                        if err == 0:
                            self.log_message(f"💻 Software Version: {software_info}")
                        else:
                            self.log_message(f"⚠️ Software Version lỗi: {err}")
                    else:
                        self.log_message(f"💻 Software Version: {software}")
                except Exception as e:
                    self.log_message(f"⚠️ Không thể lấy software version: {e}")
                    
            except Exception as e:
                self.log_message(f"❌ Lỗi: {e}")
                
        threading.Thread(target=info_thread, daemon=True).start()
    
    def import_lua_file(self):
        """Import file Lua mới vào thư mục lua_scripts"""
        try:
            # Mở dialog chọn file
            file_path = filedialog.askopenfilename(
                title="Chọn file Lua để import",
                filetypes=[("Lua files", "*.lua"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Tạo thư mục lua_scripts nếu chưa có
            lua_dir = os.path.join(os.path.dirname(__file__), 'lua_scripts')
            if not os.path.exists(lua_dir):
                os.makedirs(lua_dir)
                self.log_message(f"📁 Đã tạo thư mục: {lua_dir}")
            
            # Copy file vào thư mục lua_scripts
            import shutil
            filename = os.path.basename(file_path)
            dest_path = os.path.join(lua_dir, filename)
            
            shutil.copy2(file_path, dest_path)
            self.log_message(f"✅ Đã import file Lua: {filename}")
            
            # Làm mới danh sách
            self.load_lua_files()
            
        except Exception as e:
            self.log_message(f"❌ Lỗi import Lua: {e}")
            messagebox.showerror("Lỗi", f"Không thể import file Lua: {e}")
    
    def import_db_file(self):
        """Import file Database mới vào thư mục TechPoint_db"""
        try:
            # Mở dialog chọn file
            file_path = filedialog.askopenfilename(
                title="Chọn file Database để import",
                filetypes=[("Database files", "*.db"), ("SQLite files", "*.sqlite"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Tạo thư mục TechPoint_db nếu chưa có
            db_dir = os.path.join(os.path.dirname(__file__), 'TechPoint_db')
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
                self.log_message(f"📁 Đã tạo thư mục: {db_dir}")
            
            # Copy file vào thư mục TechPoint_db
            import shutil
            filename = os.path.basename(file_path)
            dest_path = os.path.join(db_dir, filename)
            
            shutil.copy2(file_path, dest_path)
            self.log_message(f"✅ Đã import file Database: {filename}")
            
            # Làm mới danh sách
            self.load_db_files()
            
        except Exception as e:
            self.log_message(f"❌ Lỗi import Database: {e}")
            messagebox.showerror("Lỗi", f"Không thể import file Database: {e}")
        
    def debug_robot_methods(self):
        """Debug các method có sẵn trong robot"""
        if not self.connected:
            messagebox.showerror("Lỗi", "Chưa kết nối robot!")
            return
            
        def debug_thread():
            try:
                self.log_message("🔍 Đang debug các method có sẵn...")
                
                # Lấy tất cả method có sẵn
                methods = [method for method in dir(self.robot) if not method.startswith('_')]
                
                self.log_message(f"📋 Tổng cộng {len(methods)} methods:")
                
                # Tìm các method liên quan đến Lua
                lua_methods = [m for m in methods if 'lua' in m.lower() or 'run' in m.lower()]
                if lua_methods:
                    self.log_message("🎯 Methods liên quan đến Lua:")
                    for method in lua_methods:
                        self.log_message(f"  - {method}")
                else:
                    self.log_message("⚠️ Không tìm thấy method Lua nào")
                
                # Tìm các method liên quan đến file
                file_methods = [m for m in methods if 'file' in m.lower() or 'upload' in m.lower()]
                if file_methods:
                    self.log_message("📄 Methods liên quan đến file:")
                    for method in file_methods:
                        self.log_message(f"  - {method}")
                
                # Tìm các method liên quan đến mode
                mode_methods = [m for m in methods if 'mode' in m.lower()]
                if mode_methods:
                    self.log_message("🎮 Methods liên quan đến mode:")
                    for method in mode_methods:
                        self.log_message(f"  - {method}")
                
                self.log_message("✅ Debug hoàn thành!")
                
            except Exception as e:
                self.log_message(f"❌ Lỗi debug: {e}")
                
        threading.Thread(target=debug_thread, daemon=True).start()

def main():
    """Hàm chính"""
    root = tk.Tk()
    app = ArmControllerGUI(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
