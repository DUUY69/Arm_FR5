#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find Protocol for Device
Tìm protocol đúng cho thiết bị
"""

import serial
import time
import sys
import codecs

# Cấu hình UTF-8 cho Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def test_protocol(ser, name, data):
    """Test một protocol"""
    print(f"\n🔍 Testing {name}: {data.hex().upper()}")
    try:
        ser.write(data)
        ser.flush()
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            response_hex = response.hex().upper()
            response_text = response.decode('utf-8', errors='ignore')
            print(f"📥 Response: {response_hex}")
            print(f"📥 Text: '{response_text.strip()}'")
            return response_hex, response_text
        else:
            print("📥 No response")
            return None, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

def find_protocol():
    """Tìm protocol đúng"""
    print("="*60)
    print("    🔍 FINDING DEVICE PROTOCOL")
    print("="*60)
    
    port = "COM15"
    baudrate = 9600
    
    try:
        print(f"🔌 Connecting to {port} at {baudrate} baud...")
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=1.0)
        print("✅ Connected!")
        
        # Test các protocol phổ biến
        protocols = [
            # ASCII Commands
            ("ASCII 'START'", b'START\r\n'),
            ("ASCII 'RUN'", b'RUN\r\n'),
            ("ASCII 'ON'", b'ON\r\n'),
            ("ASCII '1'", b'1\r\n'),
            ("ASCII '5'", b'5\r\n'),
            ("ASCII 'GO'", b'GO\r\n'),
            
            # Modbus-like
            ("Modbus 01 05", b'\x01\x05'),
            ("Modbus 01 06", b'\x01\x06'),
            ("Modbus 01 10", b'\x01\x10'),
            
            # Simple Binary
            ("Binary 01", b'\x01'),
            ("Binary 05", b'\x05'),
            ("Binary FF", b'\xFF'),
            ("Binary 00", b'\x00'),
            
            # With Checksum
            ("01 55 + checksum", b'\x01\x55\x56'),
            ("05 55 + checksum", b'\x05\x55\x5A'),
            ("01 00 + checksum", b'\x01\x00\x01'),
            
            # With Start/End
            ("STX 01 ETX", b'\x02\x01\x03'),
            ("STX 05 ETX", b'\x02\x05\x03'),
            ("0xAA 01 0x55", b'\xAA\x01\x55'),
            ("0xAA 05 0x55", b'\xAA\x05\x55'),
            
            # Motor Control
            ("Motor Start", b'\x01\x01'),
            ("Motor Stop", b'\x01\x00'),
            ("Motor Run 5s", b'\x01\x05'),
            ("Motor Speed", b'\x02\x05'),
            
            # Custom protocols
            ("Custom 1", b'\x01\x55\x00\x56'),
            ("Custom 2", b'\x05\x55\x00\x5A'),
            ("Custom 3", b'\x01\x02\x03\x04'),
            ("Custom 4", b'\xAA\x01\x55\x00'),
        ]
        
        results = []
        
        for name, data in protocols:
            response_hex, response_text = test_protocol(ser, name, data)
            if response_hex and "Loi cu phap" not in response_text:
                results.append((name, data.hex().upper(), response_hex, response_text))
                print("✅ SUCCESS! This might be the right protocol!")
            elif response_hex:
                print("❌ Still getting syntax error")
            
            time.sleep(0.2)  # Pause between tests
        
        # Tóm tắt kết quả
        print("\n" + "="*60)
        print("    📊 RESULTS SUMMARY")
        print("="*60)
        
        if results:
            print("✅ Found potential working protocols:")
            for i, (name, sent, received, text) in enumerate(results, 1):
                print(f"{i}. {name}")
                print(f"   Sent: {sent}")
                print(f"   Received: {received}")
                print(f"   Text: '{text.strip()}'")
                print()
        else:
            print("❌ No working protocols found")
            print("💡 Try checking device documentation or Hercules settings")
        
        ser.close()
        print("🔌 Disconnected")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_protocol()
