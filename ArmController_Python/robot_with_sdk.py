#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fairino Robot Control - With SDK
Script điều khiển robot Fairino sử dụng SDK Python đã copy
"""

import os
import sys
import time

# Thêm SDK path vào sys.path
SDK_PATH = os.path.join(os.path.dirname(__file__), 'fairino_sdk')
if os.path.exists(SDK_PATH):
    sys.path.insert(0, SDK_PATH)

# Cấu hình mặc định
DEFAULT_ROBOT_IP = '192.168.58.2'
LUA_DIR = os.path.join(os.path.dirname(__file__), 'lua_scripts')

class FairinoRobotSDK:
    def __init__(self, robot_ip=DEFAULT_ROBOT_IP):
        self.robot_ip = robot_ip
        self.robot = None
        self.connected = False
        self.auto_mode = False
        
    def connect(self):
        """Kết nối đến robot sử dụng SDK"""
        try:
            # Import SDK
            from fairino import Robot
            self.robot = Robot.RPC(self.robot_ip)
            
            # Kiểm tra kết nối
            if hasattr(self.robot, 'is_conect'):
                if self.robot.is_conect:
                    self.connected = True
                    print(f"[OK] Da ket noi den robot tai {self.robot_ip} (SDK)")
                    return True
                else:
                    print("[LOI] SDK ket noi that bai")
                    return False
            else:
                # Fallback: test bằng GetControllerIP
                try:
                    result = self.robot.GetControllerIP()
                    self.connected = True
                    print(f"[OK] Da ket noi den robot tai {self.robot_ip} (SDK)")
                    print(f"Controller IP: {result}")
                    return True
                except:
                    print("[LOI] SDK ket noi that bai")
                    return False
                    
        except ImportError as e:
            print(f"[LOI] Khong the import SDK: {e}")
            print("Dang su dung fallback XML-RPC...")
            return self.connect_fallback()
        except Exception as e:
            print(f"[LOI] Loi khi ket noi SDK: {e}")
            return self.connect_fallback()
    
    def check_auto_mode(self):
        """Kiểm tra chế độ auto của robot"""
        if not self.connected:
            return False
        
        try:
            # Thử kiểm tra chế độ qua HTTP API (vì không có GetRobotMode)
            import requests
            import json
            
            url = f"http://{self.robot_ip}/action/get"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'mode' in data['data']:
                    mode = data['data']['mode']
                    self.auto_mode = (mode == "1")
                    print(f"[DEBUG] Robot mode from HTTP: {mode}")
                    return True
                    
        except Exception as e:
            print(f"[INFO] Khong the kiem tra che do auto: {e}")
        
        # Fallback: giả sử không ở chế độ auto
        self.auto_mode = False
        return False
    
    def set_auto_mode(self):
        """Chuyển robot sang chế độ auto"""
        if not self.connected:
            return False
        
        try:
            # Thử chuyển chế độ qua SDK trước
            if hasattr(self.robot, 'Mode'):
                try:
                    result = self.robot.Mode(0)  # Mode 0 = Automatic mode (theo tài liệu)
                    if int(result) == 0:
                        print("[OK] Da chuyen robot sang che do auto (SDK)")
                        self.auto_mode = True
                        return True
                    else:
                        print(f"[LOI] SDK Mode(0) that bai: {result}")
                except Exception as e:
                    print(f"[DEBUG] SDK Mode(0) failed: {e}")
            
            # Fallback: Thử qua HTTP API
            import requests
            import json
            
            url = f"http://{self.robot_ip}/action/set"
            payload = {"cmd": 303, "data": {"mode": "0"}}  # Mode 0 = Auto
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                print("[OK] Da chuyen robot sang che do auto (HTTP)")
                self.auto_mode = True
                return True
            else:
                print(f"[LOI] Khong the chuyen sang che do auto: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[LOI] Loi khi chuyen sang che do auto: {e}")
            return False
    
    def connect_fallback(self):
        """Fallback sử dụng XML-RPC"""
        try:
            import xmlrpc.client
            self.robot = xmlrpc.client.ServerProxy(f'http://{self.robot_ip}:20003/RPC2')
            result = self.robot.GetControllerIP()
            self.connected = True
            print(f"[OK] Da ket noi den robot tai {self.robot_ip} (XML-RPC fallback)")
            print(f"Controller IP: {result}")
            return True
        except Exception as e:
            print(f"[LOI] Fallback ket noi that bai: {e}")
            return False
    
    def list_lua_files(self):
        """Liệt kê các file Lua có sẵn"""
        if not os.path.exists(LUA_DIR):
            print(f"[LOI] Thu muc {LUA_DIR} khong ton tai")
            return []
        
        files = [f for f in os.listdir(LUA_DIR) if f.endswith('.lua')]
        if files:
            print(f"\nCac file Lua co san:")
            for i, f in enumerate(files, 1):
                print(f"  {i}. {f}")
        else:
            print("\nKhong co file Lua nao trong thu muc lua_scripts")
        
        return files
    
    def upload_lua_simple(self, filename):
        """Upload file Lua đơn giản - chỉ thử LuaUpload"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        filepath = os.path.join(LUA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[LOI] File khong ton tai: {filepath}")
            return False
        
        try:
            print(f"\nDang upload {filename}...")
            full_path = os.path.abspath(filepath)
            
            # Chỉ thử LuaUpload
            if hasattr(self.robot, 'LuaUpload'):
                try:
                    print(f"Thu LuaUpload...")
                    result = self.robot.LuaUpload(full_path)
                    
                    if isinstance(result, tuple):
                        err, msg = result
                        if err == 0:
                            print(f"[OK] Upload thanh cong {filename} (LuaUpload)")
                            return True
                        else:
                            print(f"[LOI] LuaUpload that bai: {err} - {msg}")
                            return False
                    else:
                        if int(result) == 0:
                            print(f"[OK] Upload thanh cong {filename} (LuaUpload)")
                            return True
                        else:
                            print(f"[LOI] LuaUpload that bai: {result}")
                            return False
                            
                except Exception as e:
                    print(f"[LOI] LuaUpload exception: {e}")
                    return False
            else:
                print("[LOI] LuaUpload method khong co san")
                return False
                
        except Exception as e:
            print(f"[LOI] Loi khi upload: {e}")
            return False

    def run_lua(self, filename):
        """Chạy file Lua"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        try:
            print(f"\nDang chay {filename}...")
            
            # Thử SDK ProgramLoad/ProgramRun trước
            if hasattr(self.robot, 'ProgramLoad') and hasattr(self.robot, 'ProgramRun'):
                try:
                    remote_path = f"/fruser/{filename}"
                    load_result = self.robot.ProgramLoad(remote_path)
                    print(f"ProgramLoad ket qua: {load_result}")
                    
                    if int(load_result) == 0:
                        run_result = self.robot.ProgramRun()
                        print(f"ProgramRun ket qua: {run_result}")
                        
                        if int(run_result) == 0:
                            print(f"[OK] Dang chay {filename} (SDK)")
                            return True
                        else:
                            print(f"[LOI] SDK ProgramRun that bai: {run_result}")
                            return False
                    else:
                        print(f"[LOI] SDK ProgramLoad that bai: {load_result}")
                        return False
                        
                except Exception as e:
                    print(f"[LOI] SDK ProgramLoad/Run that bai: {e}")
            
            # Fallback: XML-RPC
            try:
                load_result = self.robot.ProgramLoad(f"/fruser/{filename}")
                print(f"ProgramLoad ket qua: {load_result}")
                
                if int(load_result) == 0:
                    run_result = self.robot.ProgramRun()
                    print(f"ProgramRun ket qua: {run_result}")
                    
                    if int(run_result) == 0:
                        print(f"[OK] Dang chay {filename} (XML-RPC)")
                        return True
                    else:
                        print(f"[LOI] XML-RPC ProgramRun that bai: {run_result}")
                        return False
                else:
                    print(f"[LOI] XML-RPC ProgramLoad that bai: {load_result}")
                    return False
                    
            except Exception as e:
                print(f"[LOI] XML-RPC ProgramLoad/Run that bai: {e}")
                return False
                
        except Exception as e:
            print(f"[LOI] Loi khi chay: {e}")
            return False
    
    def stop_program(self):
        """Dừng chương trình"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        try:
            result = self.robot.ProgramStop()
            print(f"ProgramStop ket qua: {result}")
            return int(result) == 0
        except Exception as e:
            print(f"[LOI] Loi khi dung: {e}")
            return False
    
    def get_robot_info(self):
        """Lấy thông tin robot"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return
        
        try:
            print("\n=== THONG TIN ROBOT ===")
            
            # Get controller IP
            try:
                error, ip = self.robot.GetControllerIP()
                if error == 0:
                    print(f"Controller IP: {ip}")
                else:
                    print(f"Controller IP: Loi {error}")
            except Exception as e:
                print(f"Controller IP: {e}")
            
            # Get SDK version
            try:
                error, version = self.robot.GetSDKVersion()
                if error == 0:
                    print(f"SDK Version: {version}")
                else:
                    print(f"SDK Version: Loi {error}")
            except Exception as e:
                print(f"SDK Version: {e}")
            
            # Get software version
            try:
                error, robotModel, webVersion, controllerVersion = self.robot.GetSoftwareVersion()
                if error == 0:
                    print(f"Robot Model: {robotModel}")
                    print(f"Web Version: {webVersion}")
                    print(f"Controller Version: {controllerVersion}")
                else:
                    print(f"Software Version: Loi {error}")
            except Exception as e:
                print(f"Software Version: {e}")
            
            # Check drag teach state
            try:
                error, state = self.robot.IsInDragTeach()
                if error == 0:
                    drag_state = "Drag Teach" if state == 1 else "Normal"
                    print(f"Drag Teach State: {drag_state}")
                else:
                    print(f"Drag Teach State: Loi {error}")
            except Exception as e:
                print(f"Drag Teach State: {e}")
            
            print("="*30)
                
        except Exception as e:
            print(f"[LOI] Loi khi lay thong tin: {e}")
    
    def robot_enable(self, enable=True):
        """Điều khiển robot enable/disable"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        try:
            state = 1 if enable else 0
            result = self.robot.RobotEnable(state)
            
            if int(result) == 0:
                status = "enable" if enable else "disable"
                print(f"[OK] Robot da {status}")
                return True
            else:
                print(f"[LOI] RobotEnable({state}) that bai: {result}")
                return False
                
        except Exception as e:
            print(f"[LOI] Loi khi enable/disable robot: {e}")
            return False
    
    def drag_teach_switch(self, enable=True):
        """Điều khiển drag teach mode"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        try:
            state = 1 if enable else 0
            result = self.robot.DragTeachSwitch(state)
            
            if int(result) == 0:
                status = "bat" if enable else "tat"
                print(f"[OK] Drag teach da {status}")
                return True
            else:
                print(f"[LOI] DragTeachSwitch({state}) that bai: {result}")
                return False
                
        except Exception as e:
            print(f"[LOI] Loi khi bat/tat drag teach: {e}")
            return False
    
    def upload_system_mode_http(self, filepath):
        """Upload file system mode qua HTTP API multipart/form-data"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        if not os.path.exists(filepath):
            print(f"[LOI] File khong ton tai: {filepath}")
            return False
        
        try:
            print(f"\nDang upload system mode {os.path.basename(filepath)} qua HTTP...")
            
            import requests
            
            url = f"http://{self.robot_ip}/action/upload"
            
            # Chuẩn bị file để upload
            with open(filepath, 'rb') as f:
                files = {
                    'file': (os.path.basename(filepath), f, 'application/octet-stream')
                }
                
                # Headers giống như browser
                headers = {
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                    'Origin': f'http://{self.robot_ip}',
                    'Referer': f'http://{self.robot_ip}/index.html',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0'
                }
                
                response = requests.post(url, files=files, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    print(f"[OK] Upload system mode thanh cong: {os.path.basename(filepath)}")
                    print(f"Response: {response.text}")
                    return True
                else:
                    print(f"[LOI] Upload that bai: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"[LOI] Loi khi upload system mode qua HTTP: {e}")
            return False
    
    def activate_point_table(self, filename):
        """Activate/switch point table sau khi upload"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        try:
            print(f"\nDang activate point table: {filename}...")
            
            # Thử PointTableSwitch để chuyển sang point table mới
            if hasattr(self.robot, 'PointTableSwitch'):
                try:
                    result = self.robot.PointTableSwitch(filename)
                    
                    if int(result) == 0:
                        print(f"[OK] Da activate point table: {filename}")
                        return True
                    else:
                        print(f"[LOI] PointTableSwitch that bai: {result}")
                        return False
                        
                except Exception as e:
                    print(f"[LOI] PointTableSwitch exception: {e}")
                    return False
            else:
                print("[LOI] PointTableSwitch method khong co san")
                return False
                
        except Exception as e:
            print(f"[LOI] Loi khi activate point table: {e}")
            return False
    
    def list_point_tables(self):
        """Liệt kê các point table có sẵn trên robot"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return []
        
        try:
            print("\nDang lay danh sach point table...")
            
            # Thử các phương thức để lấy danh sách point table
            methods_to_try = [
                'GetPointTableList',
                'GetLuaList', 
                'GetFileList',
                'ListPointTables'
            ]
            
            for method_name in methods_to_try:
                if hasattr(self.robot, method_name):
                    try:
                        result = getattr(self.robot, method_name)()
                        print(f"[OK] {method_name}: {result}")
                        return result
                    except Exception as e:
                        print(f"[INFO] {method_name} failed: {e}")
                        continue
            
            print("[INFO] Khong the lay danh sach point table")
            return []
                
        except Exception as e:
            print(f"[LOI] Loi khi lay danh sach point table: {e}")
            return []
    
    def list_database_files(self):
        """Liệt kê các file database có sẵn"""
        db_dir = os.path.join(os.path.dirname(__file__), 'TechPoint_db')
        if not os.path.exists(db_dir):
            print(f"[LOI] Thu muc {db_dir} khong ton tai")
            return []
        
        files = [f for f in os.listdir(db_dir) if f.endswith(('.db', '.sqlite', '.sqlite3'))]
        if files:
            print(f"\nCac file database co san:")
            for i, f in enumerate(files, 1):
                filepath = os.path.join(db_dir, f)
                size = os.path.getsize(filepath)
                print(f"  {i}. {f} ({size} bytes)")
        else:
            print("\nKhong co file database nao trong thu muc TechPoint_db")
        
        return files
    
    def debug_robot_methods(self):
        """Debug - kiểm tra các phương thức có sẵn trong robot"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return
        
        print("\n=== DEBUG: Cac phuong thuc co san trong robot ===")
        
        # Kiểm tra loại robot object
        print(f"Robot object type: {type(self.robot)}")
        
        # Liệt kê các phương thức upload
        upload_methods = ['LuaUpload', 'OpenLuaUpload', 'AxleLuaUpload', 'FileUpload', 'LuaUpLoadUpdate']
        print("\nCac phuong thuc upload:")
        for method in upload_methods:
            has_method = hasattr(self.robot, method)
            print(f"  {method}: {'✓' if has_method else '✗'}")
        
        # Liệt kê tất cả các phương thức bắt đầu bằng 'Lua' hoặc 'File'
        print("\nTat ca cac phuong thuc lien quan:")
        all_methods = [attr for attr in dir(self.robot) if not attr.startswith('_')]
        upload_related = [m for m in all_methods if 'lua' in m.lower() or 'file' in m.lower() or 'upload' in m.lower()]
        for method in sorted(upload_related):
            print(f"  {method}")
        
        # Liệt kê các phương thức liên quan đến mode
        print("\nCac phuong thuc lien quan den mode:")
        mode_related = [m for m in all_methods if 'mode' in m.lower() or 'Mode' in m or 'DragTeach' in m]
        for method in sorted(mode_related):
            print(f"  {method}")
        
        print("="*50)

    def database_manager(self):
        """Database Manager - Upload và activate point table"""
        import glob
        
        print("\n" + "="*70)
        print("    🗄️  DATABASE MANAGER")
        print("="*70)
        
        # Tìm các file .db
        db_files = []
        techpoint_dir = "TechPoint_db"
        if os.path.exists(techpoint_dir):
            pattern = os.path.join(techpoint_dir, "*.db")
            db_files.extend(glob.glob(pattern))
        
        pattern = "*.db"
        db_files.extend(glob.glob(pattern))
        db_files = sorted(list(set(db_files)))
        
        if not db_files:
            print("❌ Không tìm thấy file .db nào!")
            return
        
        print("\n📁 Các database có sẵn:")
        print("-" * 70)
        for i, db_file in enumerate(db_files, 1):
            file_size = os.path.getsize(db_file) if os.path.exists(db_file) else 0
            file_size_kb = file_size / 1024
            print(f"  {i:2d}. 📄 {os.path.basename(db_file)}")
            print(f"      📂 Đường dẫn: {db_file}")
            print(f"      📊 Kích thước: {file_size_kb:.1f} KB ({file_size} bytes)")
            print()
        
        print("-" * 70)
        print(f"  {len(db_files) + 1:2d}. 🚪 Quay lại menu chính")
        print("="*70)
        
        try:
            choice = input(f"\n🔢 Chọn database (1-{len(db_files) + 1}): ").strip()
            
            if not choice.isdigit():
                print("❌ Vui lòng nhập số!")
                return
            
            choice = int(choice)
            
            if choice == len(db_files) + 1:
                print("👋 Quay lại menu chính!")
                return
            elif 1 <= choice <= len(db_files):
                selected_db = db_files[choice - 1]
                print(f"\n✅ Bạn đã chọn: {os.path.basename(selected_db)}")
                print(f"📂 Đường dẫn: {selected_db}")
                
                confirm = input("\n❓ Bạn có chắc chắn muốn upload và activate database này? (y/n): ").strip().lower()
                
                if confirm in ['y', 'yes', 'có', 'c']:
                    print("\n🚀 Bắt đầu quá trình upload và activate...")
                    self.upload_and_activate_database(selected_db)
                else:
                    print("❌ Đã hủy!")
            else:
                print(f"❌ Vui lòng chọn từ 1 đến {len(db_files) + 1}!")
                
        except KeyboardInterrupt:
            print("\n👋 Quay lại menu chính!")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    def upload_and_activate_database(self, db_file):
        """Upload và activate database được chọn"""
        try:
            print(f"\n{'='*70}")
            print(f"    🚀 UPLOAD & ACTIVATE: {os.path.basename(db_file)}")
            print(f"{'='*70}")
            
            # Bước 1: Upload database
            print(f"\n[BƯỚC 1] Upload {os.path.basename(db_file)}...")
            
            try:
                if hasattr(self.robot, 'PointTableUpLoad'):
                    result = self.robot.PointTableUpLoad(db_file)
                    print(f"PointTableUpLoad result: {result}")
                    
                    if int(result) == 0:
                        print(f"[OK] Upload {os.path.basename(db_file)} thành công!")
                    else:
                        print(f"[INFO] PointTableUpLoad trả về: {result}")
                else:
                    print("[INFO] PointTableUpLoad method không có sẵn")
            except Exception as e:
                print(f"[INFO] PointTableUpLoad exception: {e}")
            
            # Bước 2: Activate database
            print(f"\n[BƯỚC 2] Activate {os.path.basename(db_file)}...")
            
            try:
                db_name = os.path.basename(db_file)
                result = self.robot.PointTableSwitch(db_name)
                print(f"PointTableSwitch result: {result}")
                
                if int(result) == 0:
                    print(f"[OK] Database {db_name} đã được activate!")
                else:
                    print(f"[LOI] PointTableSwitch thất bại: {result}")
                    return False
                    
            except Exception as e:
                print(f"[LOI] PointTableSwitch exception: {e}")
                return False
            
            # Bước 3: Kiểm tra các point (nếu là web_point.db)
            if "web_point" in db_name.lower():
                print(f"\n[BƯỚC 3] Kiểm tra các point từ {db_name}...")
                
                point_names = [
                    "Rest_1",
                    "CupDow-safe-1", 
                    "CupDow-safe-2",
                    "CupDow-take",
                    "CupDow-safe-3",
                    "CupDow-safe-4",
                    "CupDow-safe-5"
                ]
                
                success_count = 0
                for name in point_names:
                    try:
                        result = self.robot.GetRobotTeachingPoint(name)
                        if result[0] == 0:  # Success
                            print(f"[OK] {name}: Load thành công")
                            success_count += 1
                            
                            # Hiển thị thông tin chi tiết
                            data = result[1]
                            if len(data) >= 6:
                                print(f"    📍 Vị trí: X={float(data[0]):.2f}, Y={float(data[1]):.2f}, Z={float(data[2]):.2f}")
                                print(f"    🔄 Góc quay: RX={float(data[3]):.2f}, RY={float(data[4]):.2f}, RZ={float(data[5]):.2f}")
                        else:
                            print(f"[LOI] {name}: Lỗi {result[0]}")
                    except Exception as e:
                        print(f"[LOI] {name}: Exception {e}")
                
                print(f"\n[KẾT QUẢ] {success_count}/{len(point_names)} point đã load thành công")
            
            # Bước 4: Test thêm point mới
            print(f"\n[BƯỚC 4] Test thêm point mới...")
            
            try:
                test_point = [100.0, 200.0, 300.0, 0.0, 0.0, 0.0]
                result = self.robot.SetPointToDatabase("test_point_demo", test_point)
                
                if int(result) == 0:
                    print("[OK] Đã thêm point test thành công!")
                else:
                    print(f"[LOI] SetPointToDatabase thất bại: {result}")
            except Exception as e:
                print(f"[LOI] Exception khi thêm point: {e}")
            
            print(f"\n{'='*70}")
            print(f"    🎉 HOÀN THÀNH: {os.path.basename(db_file)}")
            print(f"{'='*70}")
            print("✅ Bây giờ bạn có thể kiểm tra trên controller!")
            print("📋 Các point đã sẵn sàng sử dụng trong lập trình robot.")
            
            return True
            
        except Exception as e:
            print(f"[LOI] Lỗi: {e}")
            return False

def print_menu():
    """In menu chính"""
    print("\n" + "="*50)
    print("    🦾 FAIRINO ROBOT CONTROL - WITH SDK")
    print("="*50)
    print("0. Upload file Lua")
    print("1. Database Manager (Upload & Activate)")
    print("2. Chay file Lua")
    print("3. Thong tin robot")
    print("4. Thoat")
    print("="*50)

def main():
    """Hàm chính"""
    print("Fairino Robot Control - With SDK")
    print("Phien ban: 2.0 (With SDK)")
    
    # Tạo controller và tự động kết nối
    robot = FairinoRobotSDK()
    
    print(f"\nDang ket noi den robot tai {DEFAULT_ROBOT_IP}...")
    if robot.connect():
        print(f"[OK] Ket noi thanh cong den robot tai {robot.robot_ip}")
        
        # Kiểm tra chế độ auto
        print("Dang kiem tra che do auto...")
        if robot.check_auto_mode():
            if robot.auto_mode:
                print("[INFO] Robot dang o che do auto")
            else:
                print("[INFO] Robot khong o che do auto, dang chuyen sang che do auto...")
                robot.set_auto_mode()
        else:
            print("[INFO] Khong the kiem tra che do auto")
        
        print(f"\nTrang thai robot:")
        print(f"  - Ket noi: {'OK' if robot.connected else 'FAIL'}")
        print(f"  - Che do auto: {'OK' if robot.auto_mode else 'FAIL'}")
        print(f"  - IP: {robot.robot_ip}")
        
    else:
        print(f"[LOI] Khong the ket noi den robot tai {robot.robot_ip}")
        print("Chuong trinh se thoat...")
        return
    
    while True:
        print_menu()
        try:
            choice = input("Chon chuc nang (0-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThoat chuong trinh...")
            break
        
        if choice == '0':
            files = robot.list_lua_files()
            if files:
                try:
                    idx = int(input("Chon file de upload (so): ")) - 1
                    if 0 <= idx < len(files):
                        robot.upload_lua_simple(files[idx])
                    else:
                        print("[LOI] So khong hop le")
                except ValueError:
                    print("[LOI] Vui long nhap so")
            
        elif choice == '1':
            robot.database_manager()
            
        elif choice == '2':
            files = robot.list_lua_files()
            if files:
                try:
                    idx = int(input("Chon file de chay (so): ")) - 1
                    if 0 <= idx < len(files):
                        robot.run_lua(files[idx])
                    else:
                        print("[LOI] So khong hop le")
                except ValueError:
                    print("[LOI] Vui long nhap so")
            
        elif choice == '3':
            robot.get_robot_info()
            
        elif choice == '4':
            print("Tam biet!")
            break
            
        else:
            print("[LOI] Chuc nang khong hop le")
        
        input("\nNhan Enter de tiep tuc...")

if __name__ == '__main__':
    # Tạo thư mục lua_scripts nếu chưa có
    if not os.path.exists(LUA_DIR):
        os.makedirs(LUA_DIR)
        print(f"Da tao thu muc: {LUA_DIR}")
    
    main()
