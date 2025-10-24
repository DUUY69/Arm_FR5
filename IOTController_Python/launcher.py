#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IoT Controller Launcher
Script để khởi chạy các chương trình IoT Controller khác nhau
"""

import os
import sys
import subprocess
import argparse

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def run_menu_system():
    """Chạy hệ thống menu"""
    print("🚀 Khởi chạy IoT Menu System...")
    try:
        subprocess.run([sys.executable, "iot_menu_system.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi chạy menu system: {e}")
    except FileNotFoundError:
        print("❌ Không tìm thấy file iot_menu_system.py")

def run_device_manager():
    """Chạy device manager"""
    print("🚀 Khởi chạy IoT Device Manager...")
    try:
        subprocess.run([sys.executable, "iot_device_manager.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi chạy device manager: {e}")
    except FileNotFoundError:
        print("❌ Không tìm thấy file iot_device_manager.py")

def run_command_builder():
    """Chạy command builder GUI"""
    print("🚀 Khởi chạy Command Builder GUI...")
    try:
        subprocess.run([sys.executable, "command_builder_gui.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi chạy command builder: {e}")
    except FileNotFoundError:
        print("❌ Không tìm thấy file command_builder_gui.py")

def run_arm_controller_gui():
    """Chạy Arm Controller GUI"""
    print("\n🚀 Khởi chạy Arm Controller GUI...")
    try:
        # Chuyển đến thư mục ArmController_Python
        arm_controller_path = os.path.join(os.path.dirname(__file__), '..', 'ArmController_Python')
        if os.path.exists(arm_controller_path):
            subprocess.run([sys.executable, 'arm_controller_gui.py'],
                         cwd=arm_controller_path, check=True)
        else:
            print("❌ Không tìm thấy thư mục ArmController_Python")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi chạy Arm Controller GUI: {e}")
    except FileNotFoundError:
        print("❌ Không tìm thấy file arm_controller_gui.py")

def run_simple_iot_gui():
    """Chạy Simple IoT GUI"""
    print("\n🚀 Khởi chạy Simple IoT GUI...")
    try:
        subprocess.run([sys.executable, 'simple_iot_gui.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi chạy Simple IoT GUI: {e}")
    except FileNotFoundError:
        print("❌ Không tìm thấy file simple_iot_gui.py")

def run_cli():
    """Hiển thị hướng dẫn sử dụng CLI"""
    print("\n" + "="*60)
    print("    💻 IOT CONTROLLER CLI - HUONG DAN SU DUNG")
    print("="*60)
    print("\n📋 CAC LENH CO BAN:")
    print("1. python cli.py list                    # Liet ke COM ports")
    print("2. python cli.py send-frame --cmd-code 0x01 --ins-code 0x55 --port COM11")
    print("3. python cli.py send-id --device ice_maker --command status_query --port COM11")
    
    print("\n🎯 VI DU CU THE:")
    print("• python cli.py list")
    print("• python cli.py send-frame --cmd-code 0x01 --ins-code 0x55 --port COM11")
    print("• python cli.py send-frame --cmd-code 0x04 --ins-code 0xAA --data-bytes 1,10 --port COM11")
    print("• python cli.py send-id --device ice_maker --command dispense_ice --port COM11")
    
    print("\n📖 CHI TIET:")
    print("• --cmd-code: Ma lenh (0x01, 0x02, 0x03, 0x04, 0x05)")
    print("• --ins-code: Ma chi thi (0x55 = query, 0xAA = set)")
    print("• --data-bytes: Du lieu (cach nhau boi dau phay)")
    print("• --port: Cong COM (COM11, COM12, etc.)")
    print("• --device: Thiet bi (ice_maker, cup_dropping, sensor_hub)")
    print("• --command: Ten lenh (status_query, dispense_ice, etc.)")
    
    print("\n" + "="*60)
    print("💡 TIP: Su dung Menu System (chuc nang 1) de de dang hon!")
    print("="*60)

def show_menu():
    """Hiển thị menu lựa chọn"""
    print("\n" + "="*60)
    print("    🌐 IOT CONTROLLER LAUNCHER")
    print("="*60)
        print("1. 📋 Menu System (Tương tác)")
        print("2. 🎮 Device Manager (Quản lý nhiều thiết bị)")
        print("3. 🖥️ Command Builder GUI (Giao diện đồ họa)")
        print("4. 💻 CLI (Dòng lệnh)")
        print("5. 📋 Danh sách COM ports")
        print("6. 🦾 Arm Controller GUI (Robot Fairino)")
        print("7. 🎯 Simple IoT GUI (Đơn giản)")
        print("8. 🚪 Thoát")
    print("="*60)
    
    while True:
        try:
            choice = input("🔢 Chọn chương trình (1-8): ").strip()
            
            if choice == '1':
                run_menu_system()
            elif choice == '2':
                run_device_manager()
            elif choice == '3':
                run_command_builder()
            elif choice == '4':
                run_cli()
            elif choice == '5':
                list_com_ports()
            elif choice == '6':
                run_arm_controller_gui()
            elif choice == '7':
                run_simple_iot_gui()
            elif choice == '8':
                print("👋 Tạm biệt!")
                break
            else:
                print("❌ Lựa chọn không hợp lệ!")
            
            # Quay lại menu sau khi hoàn thành chương trình
            if choice in ['1', '2', '3', '4', '5', '6', '7']:
                print("\n⏸️ Chương trình đã hoàn thành!")
                input("Nhấn Enter để quay lại menu...")
                print()  # Thêm dòng trống
                show_menu()  # Hiện lại menu
                
        except KeyboardInterrupt:
            print("\n👋 Tạm biệt!")
            break
        except EOFError:
            print("\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")

def list_com_ports():
    """Liệt kê COM ports"""
    try:
        from iot_controller import IoTController
        ports = IoTController.list_ports()
        
        print("\n📋 DANH SÁCH COM PORTS:")
        print("-" * 50)
        
        if not ports:
            print("❌ Không tìm thấy COM port nào!")
        else:
            for i, port in enumerate(ports, 1):
                print(f"  {i:2d}. {port}")
        
        print("-" * 50)
        
    except ImportError:
        print("❌ Không thể import IoTController")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="IoT Controller Launcher")
    parser.add_argument("--menu", action="store_true", help="Chạy menu system")
    parser.add_argument("--manager", action="store_true", help="Chạy device manager")
    parser.add_argument("--gui", action="store_true", help="Chạy command builder GUI")
    parser.add_argument("--simple-gui", action="store_true", help="Chạy Simple IoT GUI")
    parser.add_argument("--cli", action="store_true", help="Chạy CLI")
    parser.add_argument("--list-ports", action="store_true", help="Liệt kê COM ports")
    
    args = parser.parse_args()
    
    if args.menu:
        run_menu_system()
    elif args.manager:
        run_device_manager()
    elif args.gui:
        run_command_builder()
    elif args.simple_gui:
        run_simple_iot_gui()
    elif args.cli:
        run_cli()
    elif args.list_ports:
        list_com_ports()
    else:
        show_menu()

if __name__ == "__main__":
    main()
