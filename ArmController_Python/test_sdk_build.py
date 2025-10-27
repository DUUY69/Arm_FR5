#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test SDK Build - Kiểm tra xem SDK đã được build đúng chưa
"""

import os
import sys

def test_sdk_build():
    """Test xem SDK đã được build và import được chưa"""
    
    print("=" * 60)
    print("KIEM TRA SDK BUILD")
    print("=" * 60)
    
    # Test 1: Kiểm tra file .pyd có tồn tại không
    sdk_dir = os.path.join(os.path.dirname(__file__), 'fairino_sdk', 'fairino')
    pyd_file = os.path.join(sdk_dir, 'Robot.cp311-win_amd64.pyd')
    
    print(f"\n1. Kiem tra file .pyd:")
    if os.path.exists(pyd_file):
        print(f"   OK: Tim thay: {pyd_file}")
        size = os.path.getsize(pyd_file) / (1024 * 1024)
        print(f"   Kich thuoc: {size:.2f} MB")
    else:
        print(f"   LOI: KHONG tim thay file .pyd")
        print(f"   Can chay: python setup.py build_ext --inplace")
        return False
    
    # Test 2: Import SDK
    print(f"\n2. Kiem tra import SDK:")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fairino_sdk'))
        from fairino import Robot
        print(f"   OK: Import SDK thanh cong!")
    except ImportError as e:
        print(f"   LOI: Loi import SDK: {e}")
        return False
    except Exception as e:
        print(f"   LOI: Loi: {e}")
        return False
    
    # Test 3: Kiểm tra class Robot
    print(f"\n3. Kiem tra class Robot:")
    try:
        if hasattr(Robot, 'RPC'):
            print(f"   OK: Tim thay class Robot.RPC")
        else:
            print(f"   Canh bao: Khong tim thay Robot.RPC")
        
        # Liệt kê các method
        methods = [m for m in dir(Robot) if not m.startswith('_')]
        print(f"   Tim thay {len(methods)} attributes")
        
    except Exception as e:
        print(f"   LOI: Loi: {e}")
        return False
    
    # Test 4: Tạo robot instance
    print(f"\n4. Kiem tra tao robot instance:")
    try:
        robot = Robot.RPC('192.168.58.2')
        print(f"   OK: Tao robot instance thanh cong!")
        print(f"   Robot proxy: {robot}")
        
        # Test kết nối
        print(f"\n5. Kiem tra ket noi robot:")
        try:
            # Thử ping robot
            print(f"   Dang thu ket noi den robot...")
            # Không thử kết nối thật để tránh lỗi nếu robot không online
            print(f"   Bo qua test ket noi (can robot that de test)")
            
        except Exception as e:
            print(f"   LOI: Loi ket noi: {e}")
    except Exception as e:
        print(f"   LOI: Loi tao instance: {e}")
        return False
    
    print(f"\n" + "=" * 60)
    print(f"OK: BUILD THANH CONG!")
    print(f"=" * 60)
    print(f"\nKET LUAN:")
    print(f"   - SDK da duoc build dung cach")
    print(f"   - SDK co the import duoc")
    print(f"   - Robot instance co the tao duoc")
    print(f"\nBAN CO THE:")
    print(f"   1. Chay GUI: python arm_controller_gui.py")
    print(f"   2. Chay console: python robot_with_sdk.py")
    print(f"   3. Hoac chay file .bat: start_arm_controller.bat")
    
    return True

if __name__ == "__main__":
    try:
        test_sdk_build()
    except KeyboardInterrupt:
        print("\n\nNgười dùng đã dừng test")
    except Exception as e:
        print(f"\nLOI: {e}")
        import traceback
        traceback.print_exc()

