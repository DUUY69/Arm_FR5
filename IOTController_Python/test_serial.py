#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Serial Communication
Kiểm tra kết nối serial và gửi lệnh
"""

import serial
import time
import sys
import codecs

# Cấu hình UTF-8 cho Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def test_serial():
    """Test kết nối serial"""
    print("="*50)
    print("    🔧 SERIAL COMMUNICATION TEST")
    print("="*50)
    
    # Test COM15 với 9600 baud
    port = "COM15"
    baudrate = 9600
    
    try:
        print(f"🔌 Connecting to {port} at {baudrate} baud...")
        
        # Mở kết nối serial
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1.0,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        
        print(f"✅ Connected successfully!")
        print(f"📊 Port info: {ser.name}")
        print(f"📊 Baudrate: {ser.baudrate}")
        print(f"📊 Timeout: {ser.timeout}")
        
        # Test gửi lệnh
        print("\n🎯 Testing commands:")
        
        # Test 1: Gửi 0x05
        print("\n1️⃣ Sending 0x05...")
        ser.write(b'\x05')
        ser.flush()
        print("📤 Sent: 05")
        
        # Đọc phản hồi
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"📥 Response: {response.hex().upper()}")
            print(f"📥 Length: {len(response)} bytes")
        else:
            print("📥 No response")
        
        # Test 2: Gửi 0x01
        print("\n2️⃣ Sending 0x01...")
        ser.write(b'\x01')
        ser.flush()
        print("📤 Sent: 01")
        
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"📥 Response: {response.hex().upper()}")
            print(f"📥 Length: {len(response)} bytes")
        else:
            print("📥 No response")
        
        # Test 3: Gửi 0xFF
        print("\n3️⃣ Sending 0xFF...")
        ser.write(b'\xFF')
        ser.flush()
        print("📤 Sent: FF")
        
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"📥 Response: {response.hex().upper()}")
            print(f"📥 Length: {len(response)} bytes")
        else:
            print("📥 No response")
        
        # Đóng kết nối
        ser.close()
        print("\n🔌 Disconnected")
        
    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
        print("💡 Check if COM15 is available and not used by other programs")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_serial()
