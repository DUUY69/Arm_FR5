#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kết nối và điều khiển robot Fairino qua Python
"""

import os
import sys
import socket
import xmlrpc.client
import time

# Cấu hình robot
ROBOT_IP = '192.168.58.2'  # Đổi IP robot tại đây nếu cần
XMLRPC_PORT = 20003
TCP_PORT = 20010

def test_connection():
    """Test kết nối TCP và XML-RPC"""
    print(f"=== Testing connection to robot {ROBOT_IP} ===")
    
    # Test TCP port
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((ROBOT_IP, TCP_PORT))
        print(f"[OK] TCP port {TCP_PORT}: Connected")
        s.close()
    except Exception as e:
        print(f"[FAIL] TCP port {TCP_PORT}: {e}")
    
    # Test XML-RPC
    try:
        proxy = xmlrpc.client.ServerProxy(f'http://{ROBOT_IP}:{XMLRPC_PORT}/RPC2')
        # Test basic RPC call
        result = proxy.GetControllerIP()
        print(f"[OK] XML-RPC: Connected - Controller IP: {result}")
        return proxy
    except Exception as e:
        print(f"[FAIL] XML-RPC: {e}")
        return None

def test_robot_control():
    """Test các lệnh điều khiển robot cơ bản"""
    print("\n=== Testing robot control ===")
    
    proxy = test_connection()
    if not proxy:
        print("Cannot connect to robot. Please check IP and network.")
        return False
    
    try:
        # Test robot enable
        print("Testing robot enable...")
        result = proxy.RobotEnable(state=1)
        print(f"RobotEnable result: {result}")
        
        # Test get robot state
        print("Getting robot state...")
        try:
            state = proxy.GetRobotState()
            print(f"Robot state: {state}")
        except:
            print("GetRobotState not available")
        
        # Test get joint positions
        print("Getting joint positions...")
        try:
            pos = proxy.GetActualJointPosDegree()
            print(f"Joint positions: {pos}")
        except:
            print("GetActualJointPosDegree not available")
            
        return True
        
    except Exception as e:
        print(f"Robot control test failed: {e}")
        return False

def upload_and_run_lua():
    """Upload và chạy file Lua"""
    print("\n=== Upload and run Lua script ===")
    
    proxy = test_connection()
    if not proxy:
        return False
    
    # Kiểm tra file Lua có sẵn
    lua_dir = os.path.join(os.path.dirname(__file__), 'lua_scripts')
    lua_files = [f for f in os.listdir(lua_dir) if f.endswith('.lua')]
    
    if not lua_files:
        print("No Lua files found in lua_scripts directory")
        return False
    
    print(f"Found Lua files: {lua_files}")
    
    # Chọn file đầu tiên để test
    lua_file = lua_files[0]
    print(f"Testing with file: {lua_file}")
    
    try:
        # Upload file Lua
        print(f"Uploading {lua_file}...")
        upload_result = proxy.FileUpload(0, lua_file)
        print(f"FileUpload result: {upload_result}")
        
        # Finalize upload
        update_result = proxy.LuaUpLoadUpdate(lua_file)
        print(f"LuaUpLoadUpdate result: {update_result}")
        
        # Load và run program
        print(f"Loading program: /fruser/{lua_file}")
        load_result = proxy.ProgramLoad(f"/fruser/{lua_file}")
        print(f"ProgramLoad result: {load_result}")
        
        if int(load_result) == 0:
            print("Running program...")
            run_result = proxy.ProgramRun()
            print(f"ProgramRun result: {run_result}")
        else:
            print("ProgramLoad failed, cannot run")
            
        return True
        
    except Exception as e:
        print(f"Lua upload/run failed: {e}")
        return False

def main():
    """Main function"""
    print("=== Fairino Robot Python Test ===")
    print(f"Robot IP: {ROBOT_IP}")
    print(f"XML-RPC Port: {XMLRPC_PORT}")
    print(f"TCP Port: {TCP_PORT}")
    
    # Test kết nối
    if not test_connection():
        print("\n[FAILED] Connection test failed!")
        return
    
    print("\n[SUCCESS] Connection test passed!")
    
    # Test điều khiển robot
    if test_robot_control():
        print("\n[SUCCESS] Robot control test passed!")
    else:
        print("\n[FAILED] Robot control test failed!")
    
    # Test upload và chạy Lua
    if upload_and_run_lua():
        print("\n[SUCCESS] Lua script test passed!")
    else:
        print("\n[FAILED] Lua script test failed!")
    
    print("\n=== Test completed ===")

if __name__ == '__main__':
    main()
