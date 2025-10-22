#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script đơn giản để điều khiển robot Fairino qua Python
Sử dụng XML-RPC để kết nối và chạy file Lua
"""

import xmlrpc.client
import os
import time

class FairinoRobot:
    def __init__(self, ip='192.168.58.2', port=20003):
        self.ip = ip
        self.port = port
        self.proxy = None
        self.connect()
    
    def connect(self):
        """Kết nối đến robot"""
        try:
            self.proxy = xmlrpc.client.ServerProxy(f'http://{self.ip}:{self.port}/RPC2')
            # Test connection
            result = self.proxy.GetControllerIP()
            print(f"[OK] Connected to robot at {self.ip}")
            print(f"Controller IP: {result}")
            return True
        except Exception as e:
            print(f"[FAIL] Cannot connect to robot: {e}")
            return False
    
    def upload_lua(self, lua_file_path):
        """Upload file Lua lên robot"""
        if not os.path.exists(lua_file_path):
            print(f"[FAIL] File not found: {lua_file_path}")
            return False
        
        filename = os.path.basename(lua_file_path)
        try:
            # Upload file
            upload_result = self.proxy.FileUpload(0, filename)
            print(f"FileUpload result: {upload_result}")
            
            # Finalize upload
            update_result = self.proxy.LuaUpLoadUpdate(filename)
            print(f"LuaUpLoadUpdate result: {update_result}")
            
            if int(upload_result) == 0 and int(update_result[0]) == 0:
                print(f"[OK] Successfully uploaded {filename}")
                return True
            else:
                print(f"[FAIL] Upload failed for {filename}")
                return False
                
        except Exception as e:
            print(f"[FAIL] Upload error: {e}")
            return False
    
    def run_lua(self, filename):
        """Chạy file Lua trên robot"""
        try:
            # Load program
            load_result = self.proxy.ProgramLoad(f"/fruser/{filename}")
            print(f"ProgramLoad result: {load_result}")
            
            if int(load_result) == 0:
                # Run program
                run_result = self.proxy.ProgramRun()
                print(f"ProgramRun result: {run_result}")
                
                if int(run_result) == 0:
                    print(f"[OK] Successfully running {filename}")
                    return True
                else:
                    print(f"[FAIL] ProgramRun failed for {filename}")
                    return False
            else:
                print(f"[FAIL] ProgramLoad failed for {filename}")
                return False
                
        except Exception as e:
            print(f"[FAIL] Run error: {e}")
            return False
    
    def stop_program(self):
        """Dừng chương trình đang chạy"""
        try:
            result = self.proxy.ProgramStop()
            print(f"ProgramStop result: {result}")
            return int(result) == 0
        except Exception as e:
            print(f"[FAIL] Stop error: {e}")
            return False
    
    def pause_program(self):
        """Tạm dừng chương trình"""
        try:
            result = self.proxy.ProgramPause()
            print(f"ProgramPause result: {result}")
            return int(result) == 0
        except Exception as e:
            print(f"[FAIL] Pause error: {e}")
            return False
    
    def resume_program(self):
        """Tiếp tục chương trình"""
        try:
            result = self.proxy.ProgramResume()
            print(f"ProgramResume result: {result}")
            return int(result) == 0
        except Exception as e:
            print(f"[FAIL] Resume error: {e}")
            return False
    
    def get_robot_state(self):
        """Lấy trạng thái robot"""
        try:
            state = self.proxy.GetRobotState()
            print(f"Robot state: {state}")
            return state
        except Exception as e:
            print(f"[FAIL] Get state error: {e}")
            return None
    
    def get_joint_positions(self):
        """Lấy vị trí các khớp"""
        try:
            pos = self.proxy.GetActualJointPosDegree()
            print(f"Joint positions: {pos}")
            return pos
        except Exception as e:
            print(f"[FAIL] Get positions error: {e}")
            return None

def main():
    """Ví dụ sử dụng"""
    print("=== Fairino Robot Control (Python) ===")
    
    # Tạo robot instance
    robot = FairinoRobot('192.168.58.2')
    
    if not robot.proxy:
        print("Cannot connect to robot. Exiting.")
        return
    
    # Lấy danh sách file Lua
    lua_dir = os.path.join(os.path.dirname(__file__), 'lua_scripts')
    lua_files = [f for f in os.listdir(lua_dir) if f.endswith('.lua')]
    
    print(f"\nAvailable Lua files: {lua_files}")
    
    # Test với file TakeCup.lua
    if 'TakeCup.lua' in lua_files:
        print("\n=== Testing TakeCup.lua ===")
        lua_path = os.path.join(lua_dir, 'TakeCup.lua')
        
        # Upload file
        if robot.upload_lua(lua_path):
            # Chạy file
            robot.run_lua('TakeCup.lua')
            
            # Đợi một chút
            time.sleep(2)
            
            # Kiểm tra trạng thái
            robot.get_robot_state()
            robot.get_joint_positions()
    
    # Test với file MoveToCupDownMachine.lua
    if 'MoveToCupDownMachine.lua' in lua_files:
        print("\n=== Testing MoveToCupDownMachine.lua ===")
        lua_path = os.path.join(lua_dir, 'MoveToCupDownMachine.lua')
        
        # Upload file
        if robot.upload_lua(lua_path):
            # Chạy file
            robot.run_lua('MoveToCupDownMachine.lua')
            
            # Đợi một chút
            time.sleep(2)
            
            # Kiểm tra trạng thái
            robot.get_robot_state()
            robot.get_joint_positions()
    
    print("\n=== Test completed ===")

if __name__ == '__main__':
    main()
