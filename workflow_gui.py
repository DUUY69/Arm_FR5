#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow GUI - Giao diện đồ họa cho quản lý workflow
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import uuid
import time
import xmlrpc.client
import socket

# Thêm đường dẫn - priority cho current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(1, os.path.join(current_dir, 'IOTController_Python'))
sys.path.insert(2, os.path.join(current_dir, 'ArmController_Python'))
# Prefer the same SDK path as Arm Controller GUI
SDK_PATH = os.path.join(current_dir, 'ArmController_Python', 'fairino_sdk')
if os.path.exists(SDK_PATH):
    sys.path.insert(0, SDK_PATH)
sys.path.insert(3, os.path.join(current_dir, 'ArmController_Python', 'vendor'))

# Import từ current directory đầu tiên (có load_workflow_from_file)
from coffee_workflow_coordinator import CoffeeWorkflowCoordinator
from config_loader import get_robot_ip

try:
    from fairino import Robot
    ROBOT_AVAILABLE = True
except ImportError:
    try:
        from vendor.fairino import Robot
        ROBOT_AVAILABLE = True
    except ImportError:
        Robot = None
        ROBOT_AVAILABLE = False

from iot_controller import IoTController


class WorkflowGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Workflow Manager")
        self.root.geometry("1000x700")
        
        self.workflow = CoffeeWorkflowCoordinator()
        self.robot_connected = False
        self.iot_devices = {}
        self.running = False
        self.auto_save_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🚀 WORKFLOW MANAGER", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Left panel - Controls
        left_panel = ttk.LabelFrame(main_frame, text="⚙️ Điều Khiển", padding="10")
        left_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Right panel - Log
        right_panel = ttk.LabelFrame(main_frame, text="📝 Log", padding="10")
        right_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Setup left panel
        self.setup_left_panel(left_panel)
        
        # Setup right panel
        self.setup_right_panel(right_panel)
        
        # Auto connect devices
        self.auto_connect_devices()
        
    def auto_connect_devices(self):
        """Tự động kết nối robot và IoT devices"""
        self.log("🔄 Đang tự động kết nối thiết bị...")
        
        # Connect Robot
        if ROBOT_AVAILABLE:
            try:
                robot_ip = get_robot_ip()
                robot = self._connect_robot_sdk(robot_ip)
                if robot is None:
                    raise RuntimeError("Không thể khởi tạo kết nối Robot SDK")
                self.workflow.connect_robot(robot)
                self.robot_connected = True
                self.log(f"✅ Đã kết nối Robot: {robot_ip}")
            except Exception as e:
                self.log(f"⚠️ Không thể kết nối Robot: {e}")
        
        # Connect IoT devices
        try:
            from config_loader import ConfigLoader
            config = ConfigLoader()
            
            for key in config.config.keys():
                if key.endswith('_PORT'):
                    device_name = key.replace('_PORT', '')
                    self.connect_single_iot(device_name)
                    
        except Exception as e:
            self.log(f"⚠️ Lỗi kết nối IoT: {e}")
    
    def connect_single_iot(self, device_name):
        """Kết nối một IoT device"""
        try:
            from config_loader import get_iot_device_config
            config = get_iot_device_config(device_name.upper())
            
            if not config or not config.get('port'):
                return
            
            controller = IoTController()
            controller.open(config['port'], baudrate=config['baudrate'])
            
            if controller.is_open():
                self.workflow.connect_iot_device(config['name'], controller)
                self.iot_devices[device_name] = controller
                self.log(f"✅ {device_name} ({config['port']})")
            else:
                self.log(f"⚠️ Không thể mở {device_name}: {config['port']}")
                
        except Exception as e:
            self.log(f"⚠️ Lỗi {device_name}: {e}")
        
    def setup_left_panel(self, parent):
        # Workflow management
        workflow_frame = ttk.LabelFrame(parent, text="📋 Quản Lý Workflow", padding="10")
        workflow_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(workflow_frame, text="🆕 New Workflow",
                  command=self.new_workflow).pack(fill=tk.X, pady=2)
        ttk.Button(workflow_frame, text="➕ Add Step",
                  command=self.add_step_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(workflow_frame, text="📂 Load Workflow",
                  command=self.load_workflow).pack(fill=tk.X, pady=2)
        ttk.Button(workflow_frame, text="💾 Save Workflow As",
                  command=self.save_workflow).pack(fill=tk.X, pady=2)
        ttk.Button(workflow_frame, text="🤖 Kết Nối Robot",
                  command=self.connect_robot).pack(fill=tk.X, pady=2)
        
        # Workflow info
        self.workflow_info = ttk.Label(workflow_frame, text="Chưa có workflow")
        self.workflow_info.pack(fill=tk.X, pady=5)
        
        # Execution
        exec_frame = ttk.LabelFrame(parent, text="▶️ Thực Thi", padding="10")
        exec_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.run_btn = ttk.Button(exec_frame, text="▶️ Chạy Workflow", 
                                  command=self.run_workflow, state='disabled')
        self.run_btn.pack(fill=tk.X, pady=2)
        
        ttk.Button(exec_frame, text="⏸️ Dừng Workflow", 
                  command=self.stop_workflow).pack(fill=tk.X, pady=2)
        
        # Status
        status_frame = ttk.LabelFrame(parent, text="📊 Trạng Thái", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=10, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_right_panel(self, parent):
        self.log_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Copy button
        ttk.Button(parent, text="📋 Copy Log", 
                  command=self.copy_log).pack(pady=5)
    
    def log(self, message):
        """Thêm log vào text area"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def copy_log(self):
        """Copy log to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_text.get("1.0", tk.END))
        messagebox.showinfo("Info", "Đã copy log!")
    
    def load_workflow(self):
        """Load workflow từ file"""
        file_path = filedialog.askopenfilename(
            title="Chọn file workflow",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.workflow.load_workflow_from_file(file_path)
                info = f"{self.workflow.workflow_name}\n{len(self.workflow.steps)} bước"
                self.workflow_info.config(text=info)
                self.log(f"✅ Đã load workflow: {self.workflow.workflow_name}")
                # Ensure subsequent auto-saves go to the loaded file
                self.auto_save_path = file_path
                self.run_btn.config(state='normal')
            except Exception as e:
                messagebox.showerror("Error", f"Lỗi load workflow: {e}")
                self.log(f"❌ Lỗi: {e}")
    
    def save_workflow(self):
        """Save workflow ra file"""
        file_path = filedialog.asksaveasfilename(
            title="Save workflow",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.workflow.save_workflow_to_file(file_path)
                self.log(f"💾 Đã save workflow: {file_path}")
                self.auto_save_path = file_path
            except Exception as e:
                messagebox.showerror("Error", f"Lỗi save: {e}")

    def _sanitize_filename(self, name: str) -> str:
        keep = [c if c.isalnum() or c in ('-', '_') else '_' for c in name.strip()]
        return ''.join(keep) or 'workflow'

    def _ensure_workflows_dir(self) -> str:
        target_dir = os.path.join(os.path.dirname(__file__), 'workflows')
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    def _auto_save(self):
        if not self.auto_save_path:
            # derive from workflow name
            target_dir = self._ensure_workflows_dir()
            fname = self._sanitize_filename(getattr(self.workflow, 'workflow_name', 'workflow')) + '.json'
            self.auto_save_path = os.path.join(target_dir, fname)
        try:
            self.workflow.save_workflow_to_file(self.auto_save_path)
            self.log(f"💾 Auto-saved: {os.path.relpath(self.auto_save_path, os.path.dirname(__file__))}")
        except Exception as e:
            self.log(f"⚠️ Auto-save lỗi: {e}")

    def new_workflow(self):
        """Tạo workflow mới (rỗng)"""
        dlg = tk.Toplevel(self.root)
        dlg.title("New Workflow")
        dlg.geometry("360x220")

        name_var = tk.StringVar(value="New Workflow")
        ver_var = tk.StringVar(value="1.0")
        desc_var = tk.StringVar(value="")

        ttk.Label(dlg, text="Name").pack(anchor='w', padx=10, pady=(10, 2))
        ttk.Entry(dlg, textvariable=name_var).pack(fill=tk.X, padx=10)
        ttk.Label(dlg, text="Version").pack(anchor='w', padx=10, pady=(8, 2))
        ttk.Entry(dlg, textvariable=ver_var).pack(fill=tk.X, padx=10)
        ttk.Label(dlg, text="Description").pack(anchor='w', padx=10, pady=(8, 2))
        ttk.Entry(dlg, textvariable=desc_var).pack(fill=tk.X, padx=10)

        def do_create():
            self.workflow.clear_workflow()
            self.workflow.set_workflow_metadata(name_var.get(), ver_var.get(), desc_var.get())
            self.workflow_info.config(text=f"{name_var.get()}\n0 bước")
            self.log(f"✅ Tạo workflow mới: {name_var.get()}")
            # setup auto save path and save immediately
            target_dir = self._ensure_workflows_dir()
            fname = self._sanitize_filename(name_var.get()) + '.json'
            self.auto_save_path = os.path.join(target_dir, fname)
            self._auto_save()
            dlg.destroy()

        ttk.Button(dlg, text="Create", command=do_create).pack(pady=12)

    def add_step_dialog(self):
        """Thêm một bước mới vào workflow"""
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Step")
        dlg.geometry("420x560")

        step_name = tk.StringVar(value="New Step")
        step_type = tk.StringVar(value="iot")
        timeout_var = tk.StringVar(value="")  # blank = default

        # Action config
        action_type = tk.StringVar(value="send_command")
        lua_file = tk.StringVar(value="")

        # Load Lua files from ArmController_Python/lua_scripts
        def list_lua_files():
            try:
                scripts_dir = os.path.join(current_dir, 'ArmController_Python', 'lua_scripts')
                files = []
                if os.path.isdir(scripts_dir):
                    for name in os.listdir(scripts_dir):
                        if name.lower().endswith('.lua'):
                            files.append(name)
                return sorted(files)
            except Exception:
                return []
        lua_files = list_lua_files()
        # Build device list from config (if available)
        device_list = []
        try:
            from config_loader import ConfigLoader
            cfg = ConfigLoader()
            for k in cfg.config.keys():
                if k.endswith('_PORT'):
                    device_list.append(k.replace('_PORT', ''))
        except Exception:
            pass
        default_device = device_list[0] if device_list else 'STIRRER'
        device_name = tk.StringVar(value=default_device)
        command_var = tk.StringVar(value="10")
        delay_var = tk.StringVar(value="1.0")

        # Wait config
        wait_type = tk.StringVar(value="iot_response")
        wait_device = tk.StringVar(value=default_device)
        wait_timeout = tk.StringVar(value="")  # blank = no-timeout
        wait_delay = tk.StringVar(value="1.0")

        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # Basic
        ttk.Label(frm, text="Step name").grid(row=0, column=0, sticky='w')
        ttk.Entry(frm, textvariable=step_name).grid(row=0, column=1, sticky='ew')
        ttk.Label(frm, text="Step type").grid(row=1, column=0, sticky='w', pady=(6, 0))
        ttk.Combobox(frm, textvariable=step_type, values=["robot", "iot", "delay", "condition", "parallel"], state='readonly').grid(row=1, column=1, sticky='ew', pady=(6, 0))
        ttk.Label(frm, text="Timeout (s)").grid(row=2, column=0, sticky='w', pady=(6, 0))
        ttk.Entry(frm, textvariable=timeout_var).grid(row=2, column=1, sticky='ew', pady=(6, 0))

        # Action
        ttk.Separator(frm).grid(row=3, column=0, columnspan=2, sticky='ew', pady=8)
        ttk.Label(frm, text="Action type").grid(row=4, column=0, sticky='w')
        action_combo = ttk.Combobox(frm, textvariable=action_type, values=["run_lua", "send_command", "delay"], state='readonly')
        action_combo.grid(row=4, column=1, sticky='ew')

        lua_label = ttk.Label(frm, text="Lua file")
        lua_label.grid(row=5, column=0, sticky='w', pady=(6, 0))
        if lua_files:
            lua_combo = ttk.Combobox(frm, textvariable=lua_file, values=lua_files, state='readonly')
            lua_combo.grid(row=5, column=1, sticky='ew', pady=(6, 0))
            if not lua_file.get() and lua_files:
                lua_file.set(lua_files[0])
        else:
            lua_entry = ttk.Entry(frm, textvariable=lua_file)
            lua_entry.grid(row=5, column=1, sticky='ew', pady=(6, 0))

        ttk.Label(frm, text="Device").grid(row=6, column=0, sticky='w', pady=(6, 0))
        if device_list:
            device_combo = ttk.Combobox(frm, textvariable=device_name, values=device_list, state='readonly')
            device_combo.grid(row=6, column=1, sticky='ew', pady=(6, 0))
        else:
            device_entry = ttk.Entry(frm, textvariable=device_name)
            device_entry.grid(row=6, column=1, sticky='ew', pady=(6, 0))

        ttk.Label(frm, text="Command").grid(row=7, column=0, sticky='w', pady=(6, 0))
        command_entry = ttk.Entry(frm, textvariable=command_var)
        command_entry.grid(row=7, column=1, sticky='ew', pady=(6, 0))

        ttk.Label(frm, text="Delay (s)").grid(row=8, column=0, sticky='w', pady=(6, 0))
        ttk.Entry(frm, textvariable=delay_var).grid(row=8, column=1, sticky='ew', pady=(6, 0))

        # Wait
        ttk.Separator(frm).grid(row=9, column=0, columnspan=2, sticky='ew', pady=8)
        ttk.Label(frm, text="Wait type").grid(row=10, column=0, sticky='w')
        wait_combo = ttk.Combobox(frm, textvariable=wait_type, values=["robot_complete", "iot_response", "time_delay", "default"], state='readonly')
        wait_combo.grid(row=10, column=1, sticky='ew')

        ttk.Label(frm, text="Wait device").grid(row=11, column=0, sticky='w', pady=(6, 0))
        if device_list:
            wait_device_combo = ttk.Combobox(frm, textvariable=wait_device, values=device_list, state='readonly')
            wait_device_combo.grid(row=11, column=1, sticky='ew', pady=(6, 0))
        else:
            wait_device_entry = ttk.Entry(frm, textvariable=wait_device)
            wait_device_entry.grid(row=11, column=1, sticky='ew', pady=(6, 0))

        ttk.Label(frm, text="Wait timeout (blank = none)").grid(row=12, column=0, sticky='w', pady=(6, 0))
        wait_timeout_entry = ttk.Entry(frm, textvariable=wait_timeout)
        wait_timeout_entry.grid(row=12, column=1, sticky='ew', pady=(6, 0))

        ttk.Label(frm, text="Wait delay (s)").grid(row=13, column=0, sticky='w', pady=(6, 0))
        wait_delay_entry = ttk.Entry(frm, textvariable=wait_delay)
        wait_delay_entry.grid(row=13, column=1, sticky='ew', pady=(6, 0))

        # Toggle visibility helpers
        def grid_widgets(*widgets):
            for w in widgets:
                if w is not None:
                    w.grid()
        def remove_widgets(*widgets):
            for w in widgets:
                if w is not None:
                    w.grid_remove()

        # Determine actual widgets for toggling (depending on availability of combos/entries)
        lua_widget = None
        try:
            lua_widget = locals().get('lua_combo', None) or locals().get('lua_entry', None)
        except Exception:
            lua_widget = None

        device_widget = locals().get('device_combo', None) or locals().get('device_entry', None)

        wait_device_widget = locals().get('wait_device_combo', None) or locals().get('wait_device_entry', None)

        def refresh_visibility(*_):
            stype = step_type.get()
            atype = action_type.get()

            robot_mode = (stype == 'robot') or (atype == 'run_lua')

            # If robot mode: show Lua, hide IoT device/command and iot wait device
            if robot_mode:
                # Defaults for robot
                action_type.set('run_lua')
                wait_type.set('robot_complete')
                if lua_label: lua_label.grid()
                if lua_widget: lua_widget.grid()
                remove_widgets(device_widget, command_entry, wait_device_widget)
            else:
                # IoT mode
                action_type.set('send_command')
                if lua_label: lua_label.grid_remove()
                if lua_widget: lua_widget.grid_remove()
                grid_widgets(device_widget, command_entry, wait_device_widget)

            # Wait field visibility: only show wait_device when wait_type is iot_response
            if wait_type.get() == 'iot_response':
                if wait_device_widget: wait_device_widget.grid()
            else:
                if wait_device_widget: wait_device_widget.grid_remove()

        # Bind changes
        step_type_combo = None
        for child in frm.grid_slaves():
            # find the combobox at row=1, column=1 (step_type)
            info = child.grid_info()
            if int(info.get('row', -1)) == 1 and int(info.get('column', -1)) == 1 and isinstance(child, ttk.Combobox):
                step_type_combo = child
                break
        if step_type_combo:
            step_type_combo.bind('<<ComboboxSelected>>', refresh_visibility)
        action_combo.bind('<<ComboboxSelected>>', refresh_visibility)
        wait_combo.bind('<<ComboboxSelected>>', refresh_visibility)

        # Initialize visibility based on defaults
        refresh_visibility()

        frm.columnconfigure(1, weight=1)

        def do_add():
            try:
                step_id = str(uuid.uuid4())
                # action_config
                if action_type.get() == 'run_lua':
                    if not lua_file.get().strip():
                        messagebox.showerror("Error", "Vui lòng chọn Lua file")
                        return
                    action_config = {'type': 'run_lua', 'file': lua_file.get().strip()}
                elif action_type.get() == 'send_command':
                    # Bao gồm đầy đủ trường theo chuẩn mong muốn
                    action_config = {
                        'type': 'send_command',
                        'device': device_name.get().strip(),
                        'command': command_var.get().strip(),
                        'mode': 'ascii',
                        'terminator': 'none'
                    }
                else:
                    action_config = {'type': 'delay', 'delay': float(delay_var.get() or '1.0')}

                # wait_config
                if wait_type.get() == 'robot_complete':
                    wc = {'type': 'robot_complete', 'timeout': float(timeout_var.get() or '8.0')}
                elif wait_type.get() == 'iot_response':
                    # Bao gồm prefer_raw và timeout nếu có
                    wc = {
                        'type': 'iot_response',
                        'device': wait_device.get().strip(),
                        'prefer_raw': True
                    }
                    if wait_timeout.get().strip() != '':
                        wc['timeout'] = float(wait_timeout.get())
                elif wait_type.get() == 'time_delay':
                    wc = {'type': 'time_delay', 'delay': float(wait_delay.get() or '1.0')}
                else:
                    wc = {'type': 'default'}

                overall_timeout = float(timeout_var.get()) if timeout_var.get().strip() != '' else 30.0

                self.workflow.add_step_advanced(
                    step_id=step_id,
                    step_name=step_name.get().strip(),
                    step_type=step_type.get().strip(),
                    action_config=action_config,
                    wait_config=wc,
                    timeout=overall_timeout
                )

                self.workflow_info.config(text=f"{self.workflow.workflow_name}\n{len(self.workflow.steps)} bước")
                self.log(f"✅ Đã thêm bước: {step_name.get().strip()}")
                # auto-save after add
                self._auto_save()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Lỗi thêm bước: {e}")

        ttk.Button(dlg, text="Add Step", command=do_add).pack(pady=10)
    
    def connect_robot(self):
        """Kết nối robot"""
        if not ROBOT_AVAILABLE:
            messagebox.showwarning("Warning", "Robot SDK không khả dụng!")
            return
        
        try:
            robot_ip = get_robot_ip()
            robot = self._connect_robot_sdk(robot_ip)
            if robot is None:
                raise RuntimeError("Không thể khởi tạo kết nối Robot SDK")
            self.workflow.connect_robot(robot)
            self.robot_connected = True
            self.log(f"✅ Đã kết nối Robot: {robot_ip}")
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi kết nối Robot: {e}")
            self.log(f"❌ Lỗi: {e}")
    
    def connect_iot(self):
        """Kết nối IoT device"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Kết Nối IoT Device")
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="COM Port:").pack(pady=5)
        com_var = tk.StringVar(value="COM8")
        ttk.Entry(dialog, textvariable=com_var, width=20).pack(pady=5)
        
        ttk.Label(dialog, text="Device Name:").pack(pady=5)
        device_var = tk.StringVar(value="Stirrer")
        ttk.Entry(dialog, textvariable=device_var, width=20).pack(pady=5)
        
        def connect():
            try:
                controller = IoTController()
                controller.open(com_var.get(), baudrate=115200)
                if controller.is_open():
                    self.workflow.connect_iot_device(device_var.get(), controller)
                    self.iot_devices[device_var.get()] = controller
                    self.log(f"✅ Đã kết nối: {device_var.get()}")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Không thể mở COM port!")
            except Exception as e:
                messagebox.showerror("Error", f"Lỗi: {e}")
        
        ttk.Button(dialog, text="Kết Nối", command=connect).pack(pady=10)
    
    def run_workflow(self):
        """Chạy workflow trong thread"""
        if self.running:
            messagebox.showwarning("Warning", "Workflow đang chạy!")
            return
        
        self.running = True
        self.run_btn.config(state='disabled')
        self.log("🚀 Bắt đầu chạy workflow...")
        
        def run_thread():
            try:
                success = self.workflow.run_workflow()
                if success:
                    self.log("🎉 Workflow hoàn thành!")
                else:
                    self.log("❌ Workflow thất bại!")
                
                status = self.workflow.get_status()
                self.log(f"📊 {status['completed_steps']}/{status['total_steps']} bước")
                self.log(f"⏱️ {status['elapsed_time']:.2f} giây")
            except Exception as e:
                self.log(f"❌ Lỗi: {e}")
            finally:
                self.running = False
                self.root.after(0, lambda: self.run_btn.config(state='normal'))
        
        threading.Thread(target=run_thread, daemon=True).start()
    
    def stop_workflow(self):
        """Dừng workflow"""
        if not self.running:
            messagebox.showinfo("Info", "Workflow không đang chạy")
            return
        
        self.log("⏸️ Đang dừng workflow...")
        # TODO: Implement stop mechanism

    # ==================== Robot connection helpers ====================
    def _connect_robot_sdk(self, robot_ip: str):
        """Kết nối SDK Robot.RPC với health check đơn giản.
        Trả về robot instance nếu OK, None nếu lỗi.
        """
        try:
            robot = Robot.RPC(robot_ip)
        except AttributeError:
            try:
                from vendor.fairino import Robot as VendorRobot
                self.log("⚠️ Lỗi SDK hiện tại, thử vendor.fairino.Robot")
                robot = VendorRobot.RPC(robot_ip)
            except Exception as e:
                self.log(f"❌ Vendor SDK lỗi: {e}")
                robot = None
        except Exception as e:
            self.log(f"❌ RPC lỗi: {e}")
            robot = None

        # Nếu SDK đều lỗi, fallback XML-RPC thuần
        if robot is None:
            # XML-RPC fallback: try multiple paths and brief timeout
            paths = ["/RPC2", "/RPC", "/"]
            ports = [20003]
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(2.0)
            try:
                for p in ports:
                    for path in paths:
                        url = f"http://{robot_ip}:{p}{path}"
                        try:
                            self.log(f"ℹ️ Fallback XML-RPC thử {url}")
                            proxy = xmlrpc.client.ServerProxy(url)
                            # Health check quick call
                            try:
                                _ = proxy.GetControllerIP()
                            except Exception:
                                _ = proxy.GetLuaList()
                            return proxy
                        except Exception as e:
                            self.log(f"⚠️ XML-RPC không phản hồi tại {url}: {e}")
                            continue
                # As a hint, probe TCP 20010 (data upload) to give user feedback
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1.5)
                    s.connect((robot_ip, 20010))
                    s.close()
                except Exception as e:
                    self.log(f"ℹ️ TCP 20010 không mở: {e}")
                return None
            finally:
                socket.setdefaulttimeout(old_timeout)

        # Health check: ưu tiên GetSDKVersion / GetControllerIP cho SDK
        try:
            if hasattr(robot, 'GetSDKVersion'):
                _ = robot.GetSDKVersion()
            elif hasattr(robot, 'GetControllerIP'):
                _ = robot.GetControllerIP()
        except Exception as e:
            self.log(f"⚠️ Health check cảnh báo: {e}")

        # Thử chuyển sang Auto mode (không fail nếu lỗi)
        try:
            if hasattr(robot, 'GetRobotMode'):
                mode = robot.GetRobotMode()
                mode_val = mode[1] if isinstance(mode, tuple) and len(mode) > 1 else (mode[0] if isinstance(mode, tuple) else mode)
                if mode_val != 0 and hasattr(robot, 'Mode'):
                    robot.Mode(0)
            elif hasattr(robot, 'Mode'):
                robot.Mode(0)
        except Exception:
            pass

        return robot


def main():
    root = tk.Tk()
    app = WorkflowGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

