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
    
    def upload_lua(self, filename):
        """Upload file Lua sử dụng SDK hoặc fallback"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        filepath = os.path.join(LUA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[LOI] File khong ton tai: {filepath}")
            return False
        
        try:
            print(f"\nDang upload {filename}...")
            
            # Thử SDK LuaUpload trước
            if hasattr(self.robot, 'LuaUpload'):
                try:
                    full_path = os.path.abspath(filepath)
                    result = self.robot.LuaUpload(full_path)
                    
                    if isinstance(result, tuple):
                        err, msg = result
                        if err == 0:
                            print(f"[OK] Upload thanh cong {filename} (SDK)")
                            return True
                        else:
                            print(f"[LOI] SDK Upload that bai: {err} - {msg}")
                    else:
                        if int(result) == 0:
                            print(f"[OK] Upload thanh cong {filename} (SDK)")
                            return True
                        else:
                            print(f"[LOI] SDK Upload that bai: {result}")
                            
                except Exception as e:
                    print(f"[LOI] SDK LuaUpload that bai: {e}")
            
            # Fallback: XML-RPC upload
            print("Dang su dung XML-RPC fallback...")
            try:
                upload_result = self.robot.FileUpload(0, filename)
                print(f"FileUpload ket qua: {upload_result}")
                
                if int(upload_result) == 0:
                    update_result = self.robot.LuaUpLoadUpdate(filename)
                    print(f"LuaUpLoadUpdate ket qua: {update_result}")
                    
                    if int(update_result[0]) == 0:
                        print(f"[OK] Upload thanh cong {filename} (XML-RPC)")
                        return True
                    else:
                        print(f"[LOI] LuaUpLoadUpdate that bai: {update_result}")
                        return False
                else:
                    print(f"[LOI] FileUpload that bai: {upload_result}")
                    return False
                    
            except Exception as e:
                print(f"[LOI] XML-RPC upload that bai: {e}")
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
            # Get controller IP
            ip_result = self.robot.GetControllerIP()
            print(f"Controller IP: {ip_result}")
            
            # Get SDK version if available
            try:
                version_result = self.robot.GetSDKVersion()
                print(f"SDK Version: {version_result}")
            except:
                print("SDK Version: Khong co thong tin")
                
        except Exception as e:
            print(f"[LOI] Loi khi lay thong tin: {e}")

def print_menu():
    """In menu chính"""
    print("\n" + "="*50)
    print("    FAIRINO ROBOT CONTROL - WITH SDK")
    print("="*50)
    print("0. Ket noi robot")
    print("1. Upload file Lua")
    print("2. Chay file Lua")
    print("3. Dung chuong trinh")
    print("4. Thong tin robot")
    print("5. Thoat")
    print("="*50)

def main():
    """Hàm chính"""
    print("Fairino Robot Control - With SDK")
    print("Phien ban: 2.0 (With SDK)")
    
    # Tạo controller
    robot = FairinoRobotSDK()
    
    while True:
        print_menu()
        try:
            choice = input("Chon chuc nang (0-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThoat chuong trinh...")
            break
        
        if choice == '0':
            ip = input(f"Nhap IP robot (Enter de dung {DEFAULT_ROBOT_IP}): ").strip()
            if ip:
                robot.robot_ip = ip
            robot.connect()
            
        elif choice == '1':
            files = robot.list_lua_files()
            if files:
                try:
                    idx = int(input("Chon file de upload (so): ")) - 1
                    if 0 <= idx < len(files):
                        robot.upload_lua(files[idx])
                    else:
                        print("[LOI] So khong hop le")
                except ValueError:
                    print("[LOI] Vui long nhap so")
            
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
            robot.stop_program()
            
        elif choice == '4':
            robot.get_robot_info()
            
        elif choice == '5':
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
