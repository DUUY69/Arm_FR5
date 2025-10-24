#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Motor Commands
Tìm lệnh đúng để chạy động cơ
"""

import serial
import time
import sys
import codecs

# Cấu hình UTF-8 cho Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def test_motor_commands():
    """Test các lệnh chạy động cơ"""
    print("="*60)
    print("    🔍 TESTING MOTOR COMMANDS")
    print("="*60)
    
    try:
        print("🔌 Connecting to COM15 at 9600 baud...")
        ser = serial.Serial('COM15', 9600, timeout=1.0)
        print("✅ Connected!")
        
        # Test các lệnh có thể chạy động cơ
        tests = [
            # ASCII với \r\n
            ("ASCII '5\\r\\n'", b'5\r\n'),
            ("ASCII '5\\n'", b'5\n'),
            ("ASCII '5\\r'", b'5\r'),
            ("ASCII 'START\\r\\n'", b'START\r\n'),
            ("ASCII 'RUN\\r\\n'", b'RUN\r\n'),
            ("ASCII 'MOTOR\\r\\n'", b'MOTOR\r\n'),
            
            # Binary protocols
            ("Binary 0x05", b'\x05'),
            ("Binary 0x01 0x05", b'\x01\x05'),
            ("Binary 0x05 0x00", b'\x05\x00'),
            ("Binary 0x01 0x01", b'\x01\x01'),
            
            # With checksum
            ("0x05 + checksum", b'\x05\x05'),
            ("0x01 0x05 + checksum", b'\x01\x05\x06'),
            
            # With start/end
            ("STX 0x05 ETX", b'\x02\x05\x03'),
            ("0xAA 0x05 0x55", b'\xAA\x05\x55'),
            ("0x55 0x05 0xAA", b'\x55\x05\xAA'),
            
            # Motor specific
            ("Motor Start", b'\x01\x01'),
            ("Motor Run 5s", b'\x01\x05'),
            ("Motor Speed 5", b'\x02\x05'),
            ("Motor Control", b'\x03\x05'),
        ]
        
        results = []
        
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
                    
                    # Kiểm tra nếu không phải "Loi cu phap"
                    if "Loi cu phap" not in response_text and response_text:
                        results.append((name, data.hex().upper(), response_hex, response_text))
                        print("✅ SUCCESS! This might work!")
                    else:
                        print("❌ Still getting syntax error")
                else:
                    print("📥 No response")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            time.sleep(0.2)
        
        # Tóm tắt kết quả
        print("\n" + "="*60)
        print("    📊 RESULTS SUMMARY")
        print("="*60)
        
        if results:
            print("✅ Found potential working commands:")
            for i, (name, sent, received, text) in enumerate(results, 1):
                print(f"{i}. {name}")
                print(f"   Sent: {sent}")
                print(f"   Received: {received}")
                print(f"   Text: '{text.strip()}'")
                print()
        else:
            print("❌ No working commands found")
            print("💡 Check device documentation or try different protocols")
        
        ser.close()
        print("🔌 Disconnected")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure GUI is closed and COM15 is available")

if __name__ == "__main__":
    test_motor_commands()
