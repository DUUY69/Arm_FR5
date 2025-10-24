#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Device Communication
So sánh với Hercules Setup
"""

import serial
import time
import sys
import codecs

# Cấu hình UTF-8 cho Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def test_device():
    """Test thiết bị với các protocol khác nhau"""
    print("="*60)
    print("    🔍 TESTING DEVICE COMMUNICATION")
    print("="*60)
    
    try:
        print("🔌 Connecting to COM15 at 9600 baud...")
        ser = serial.Serial('COM15', 9600, timeout=1.0)
        print("✅ Connected!")
        
        # Test các protocol khác nhau
        tests = [
            ("ASCII '5'", b'5'),
            ("ASCII '5\\r\\n'", b'5\r\n'),
            ("ASCII '5\\n'", b'5\n'),
            ("ASCII '5\\r'", b'5\r'),
            ("Binary 0x05", b'\x05'),
            ("ASCII 'START'", b'START'),
            ("ASCII 'RUN'", b'RUN'),
            ("ASCII 'GO'", b'GO'),
        ]
        
        for name, data in tests:
            print(f"\n🔍 Testing {name}: {data.hex().upper()}")
            try:
                ser.write(data)
                ser.flush()
                time.sleep(0.5)
                
                if ser.in_waiting > 0:
                    response = ser.read(ser.in_waiting)
                    response_hex = response.hex().upper()
                    response_text = response.decode('utf-8', errors='ignore').strip()
                    print(f"📥 Response: {response_hex}")
                    print(f"📥 Text: '{response_text}'")
                    if response_text and "Loi cu phap" not in response_text:
                        print("✅ SUCCESS! This might work!")
                else:
                    print("📥 No response")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            time.sleep(0.2)
        
        ser.close()
        print("\n🔌 Disconnected")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure Hercules is closed and COM15 is available")

if __name__ == "__main__":
    test_device()
