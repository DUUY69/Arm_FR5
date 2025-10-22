#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fairino Robot Control - Simplified Python Script
Script đơn giản để điều khiển robot Fairino chỉ sử dụng XML-RPC
Không phụ thuộc vào SDK phức tạp
"""

import os
import sys
import socket
import xmlrpc.client
import time
import hashlib

# Cấu hình mặc định
DEFAULT_ROBOT_IP = '192.168.58.2'
DEFAULT_PORT = 20003
TCP_PORT = 20010
LUA_DIR = os.path.join(os.path.dirname(__file__), 'lua_scripts')

class SimpleRobotController:
    def __init__(self, robot_ip=DEFAULT_ROBOT_IP, port=DEFAULT_PORT):
        self.robot_ip = robot_ip
        self.port = port
        self.proxy = None
        self.connected = False
        
    def connect(self):
        """Kết nối đến robot qua XML-RPC"""
        try:
            self.proxy = xmlrpc.client.ServerProxy(f'http://{self.robot_ip}:{self.port}/RPC2')
            # Test connection
            result = self.proxy.GetControllerIP()
            self.connected = True
            print(f"[OK] Da ket noi den robot tai {self.robot_ip}")
            print(f"Controller IP: {result}")
            return True
        except Exception as e:
            print(f"[LOI] Khong the ket noi den robot: {e}")
            self.connected = False
            return False
    
    def test_connection(self):
        """Test kết nối TCP và XML-RPC"""
        print(f"\n=== Kiem tra ket noi robot {self.robot_ip} ===")
        
        # Test TCP port
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((self.robot_ip, TCP_PORT))
            print(f"[OK] TCP port {TCP_PORT}: Mo")
            s.close()
        except Exception as e:
            print(f"[FAIL] TCP port {TCP_PORT}: Dong ({e})")
        
        # Test XML-RPC
        try:
            proxy = xmlrpc.client.ServerProxy(f'http://{self.robot_ip}:{self.port}/RPC2')
            result = proxy.GetControllerIP()
            print(f"[OK] XML-RPC: Ket noi thanh cong")
            print(f"Controller IP: {result}")
            return True
        except Exception as e:
            print(f"[FAIL] XML-RPC: Ket noi that bai ({e})")
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
        """Upload file Lua sử dụng phương pháp đơn giản"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        filepath = os.path.join(LUA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[LOI] File khong ton tai: {filepath}")
            return False
        
        try:
            print(f"\nDang upload {filename}...")
            
            # Đọc file Lua
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            file_size = len(file_data)
            print(f"File size: {file_size} bytes")
            
            # Upload qua XML-RPC (phương pháp đơn giản)
            try:
                # Thử phương pháp upload trực tiếp
                upload_result = self.proxy.FileUpload(0, filename)
                print(f"FileUpload ket qua: {upload_result}")
                
                if int(upload_result) == 0:
                    # Finalize upload
                    update_result = self.proxy.LuaUpLoadUpdate(filename)
                    print(f"LuaUpLoadUpdate ket qua: {update_result}")
                    
                    if int(update_result[0]) == 0:
                        print(f"[OK] Upload thanh cong {filename}")
                        return True
                    else:
                        print(f"[LOI] LuaUpLoadUpdate that bai: {update_result}")
                        return False
                else:
                    print(f"[LOI] FileUpload that bai: {upload_result}")
                    return False
                    
            except Exception as e:
                print(f"[LOI] Upload qua XML-RPC that bai: {e}")
                return False
                
        except Exception as e:
            print(f"[LOI] Loi khi doc file: {e}")
            return False
    
    def run_lua(self, filename):
        """Chạy file Lua trên robot"""
        if not self.connected:
            print("[LOI] Chua ket noi den robot")
            return False
        
        try:
            print(f"\nDang chay {filename}...")
            
            # Load program
            load_result = self.proxy.ProgramLoad(f"/fruser/{filename}")
            print(f"ProgramLoad ket qua: {load_result}")
            
            if int(load_result) == 0:
                # Run program
                run_result = self.proxy.ProgramRun()
                print(f"ProgramRun ket qua: {run_result}")
                
                if int(run_result) == 0:
                    print(f"[OK] Dang chay {filename}")
                    return True
                else:
                    print(f"[LOI] Khong the chay {filename}")
                    return False
            else:
                print(f"[LOI] Khong the load {filename}")
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
            result = self.proxy.ProgramStop()
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
            ip_result = self.proxy.GetControllerIP()
            print(f"Controller IP: {ip_result}")
            
            # Get SDK version if available
            try:
                version_result = self.proxy.GetSDKVersion()
                print(f"SDK Version: {version_result}")
            except:
                print("SDK Version: Khong co thong tin")
                
        except Exception as e:
            print(f"[LOI] Loi khi lay thong tin: {e}")

def print_menu():
    """In menu chính"""
    print("\n" + "="*50)
    print("    FAIRINO ROBOT CONTROL - SIMPLIFIED")
    print("="*50)
    print("0. Kiem tra ket noi")
    print("1. Ket noi robot")
    print("2. Upload file Lua")
    print("3. Chay file Lua")
    print("4. Dung chuong trinh")
    print("5. Thong tin robot")
    print("6. Thoat")
    print("="*50)

def main():
    """Hàm chính"""
    print("Fairino Robot Control - Simplified Python")
    print("Phien ban: 2.0 (Simplified)")
    print("Chi su dung XML-RPC, khong phu thuoc SDK")
    
    # Tạo controller
    robot = SimpleRobotController()
    
    while True:
        print_menu()
        try:
            choice = input("Chon chuc nang (0-6): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThoat chuong trinh...")
            break
        
        if choice == '0':
            robot.test_connection()
            
        elif choice == '1':
            ip = input(f"Nhap IP robot (Enter de dung {DEFAULT_ROBOT_IP}): ").strip()
            if ip:
                robot.robot_ip = ip
            robot.connect()
            
        elif choice == '2':
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
            
        elif choice == '3':
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
            
        elif choice == '4':
            robot.stop_program()
            
        elif choice == '5':
            robot.get_robot_info()
            
        elif choice == '6':
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
