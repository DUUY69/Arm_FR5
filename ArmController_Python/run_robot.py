#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script đơn giản để điều khiển robot Fairino qua Python
Chỉ cần thay đổi IP robot và chạy file Lua
"""

import xmlrpc.client
import os
import time

# ===== CẤU HÌNH =====
ROBOT_IP = '192.168.58.2'  # Thay đổi IP robot tại đây
ROBOT_PORT = 20003

def connect_robot():
    """Kết nối đến robot"""
    try:
        proxy = xmlrpc.client.ServerProxy(f'http://{ROBOT_IP}:{ROBOT_PORT}/RPC2')
        # Test connection
        result = proxy.GetControllerIP()
        print(f"[OK] Đã kết nối đến robot tại {ROBOT_IP}")
        return proxy
    except Exception as e:
        print(f"[LỖI] Không thể kết nối đến robot: {e}")
        return None

def upload_and_run_lua(proxy, lua_filename):
    """Upload và chạy file Lua"""
    try:
        print(f"\n=== Upload và chạy {lua_filename} ===")
        
        # Upload file
        upload_result = proxy.FileUpload(0, lua_filename)
        print(f"Upload kết quả: {upload_result}")
        
        # Finalize upload
        update_result = proxy.LuaUpLoadUpdate(lua_filename)
        print(f"Update kết quả: {update_result}")
        
        if int(upload_result) == 0 and int(update_result[0]) == 0:
            print(f"[OK] Upload thành công {lua_filename}")
            
            # Load và chạy program
            load_result = proxy.ProgramLoad(f"/fruser/{lua_filename}")
            print(f"Load kết quả: {load_result}")
            
            if int(load_result) == 0:
                run_result = proxy.ProgramRun()
                print(f"Run kết quả: {run_result}")
                
                if int(run_result) == 0:
                    print(f"[OK] Đang chạy {lua_filename}")
                    return True
                else:
                    print(f"[LỖI] Không thể chạy {lua_filename}")
                    return False
            else:
                print(f"[LỖI] Không thể load {lua_filename}")
                return False
        else:
            print(f"[LỖI] Upload thất bại {lua_filename}")
            return False
            
    except Exception as e:
        print(f"[LỖI] Lỗi khi upload/chạy: {e}")
        return False

def main():
    """Hàm chính"""
    print("=== Điều khiển Robot Fairino qua Python ===")
    print(f"Robot IP: {ROBOT_IP}")
    
    # Kết nối robot
    robot = connect_robot()
    if not robot:
        return
    
    # Lấy danh sách file Lua
    lua_dir = os.path.join(os.path.dirname(__file__), 'lua_scripts')
    if not os.path.exists(lua_dir):
        print(f"[LỖI] Thư mục {lua_dir} không tồn tại")
        return
    
    lua_files = [f for f in os.listdir(lua_dir) if f.endswith('.lua')]
    print(f"\nCác file Lua có sẵn: {lua_files}")
    
    # Chạy các file Lua
    for lua_file in lua_files:
        lua_path = os.path.join(lua_dir, lua_file)
        if os.path.exists(lua_path):
            upload_and_run_lua(robot, lua_file)
            time.sleep(1)  # Đợi giữa các lệnh
    
    print("\n=== Hoàn thành ===")

if __name__ == '__main__':
    main()
