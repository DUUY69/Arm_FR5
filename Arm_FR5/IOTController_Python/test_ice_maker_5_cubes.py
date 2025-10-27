#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để thả 5 viên đá từ máy làm đá (Ice Maker)
Dựa trên protocol: Ice Maker Serial Communication Protocol V0.0.3
"""

import sys
import codecs
import serial
import time

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


def compute_checksum(data):
    """Tính checksum"""
    return sum(data) & 0xFF


def send_dispense_ice_command(ser, quantity=5):
    """
    Gửi lệnh thả đá
    
    Args:
        ser: Serial port object
        quantity: Số viên đá (1-120)
    
    Frame theo protocol:
    0x04 (Command Code - Dispense Beverage)
    0x07 (Length Code)
    0xAA (Instruction Code - Set)
    0x01 (Beverage Number - Ice)
    0x05 (Data 1 - Quantity)
    Checksum
    0xFF (End Code)
    """
    print(f"\n❄️ Đang thả {quantity} viên đá...")
    
    # Build frame
    cmd_code = 0x04
    instruction_code = 0xAA
    beverage_number = 0x01  # 1 = ice
    data1 = quantity
    
    # Calculate length: cmd + len + instruction + beverage + data1 + checksum + end = 7
    length = 7
    
    # Frame without checksum and end
    frame_wo_cs = bytes([cmd_code, length, instruction_code, beverage_number, data1])
    
    # Calculate checksum
    checksum = compute_checksum(frame_wo_cs)
    
    # Full frame
    frame = frame_wo_cs + bytes([checksum, 0xFF])
    
    print(f"📤 Gửi frame: {frame.hex().upper()}")
    print(f"   Breakdown:")
    print(f"   - Command Code: 0x{cmd_code:02X}")
    print(f"   - Length: 0x{length:02X}")
    print(f"   - Instruction: 0x{instruction_code:02X}")
    print(f"   - Beverage: 0x{beverage_number:02X} (Ice)")
    print(f"   - Quantity: {data1}")
    print(f"   - Checksum: 0x{checksum:02X}")
    print(f"   - End: 0xFF")
    
    # Send
    ser.write(frame)
    ser.flush()
    
    # Wait for response
    print("\n⏳ Đang đợi response...")
    time.sleep(0.5)
    
    # Read response
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting)
        print(f"📥 Nhận: {response.hex().upper()}")
        
        # Parse response
        if len(response) >= 6:
            if response[3] == 0x01:  # Setting successful
                print("✅ Thành công! Máy đang thả đá...")
                return True
            else:
                print("❌ Thiết lập thất bại!")
                return False
    else:
        print("⚠️ Không nhận được response")
        return False


def main():
    print("=" * 70)
    print("ICE MAKER - THA 5 VIEN DA")
    print("=" * 70)
    
    # COM port của máy làm đá
    COM_PORT = 'COM17'  # Máy làm đá
    BAUDRATE = 115200
    
    print(f"\n🔌 Kết nối đến {COM_PORT}...")
    
    try:
        # Mở serial port
        ser = serial.Serial(
            port=COM_PORT,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2.0
        )
        
        print(f"✅ Đã kết nối đến {COM_PORT}")
        
        # Gửi lệnh thả 5 viên đá
        success = send_dispense_ice_command(ser, quantity=5)
        
        if success:
            print("\n✅ Hoàn thành! Máy sẽ thả 5 viên đá.")
        else:
            print("\n❌ Không thành công!")
        
        # Đóng serial port
        ser.close()
        print("\n👋 Đã đóng kết nối")
        
    except serial.SerialException as e:
        print(f"❌ Lỗi serial: {e}")
        print("\n💡 Hãy kiểm tra:")
        print("   1. COM port đúng chưa?")
        print("   2. Máy làm đá đã bật chưa?")
        print("   3. Cable kết nối đúng chưa?")
    except Exception as e:
        print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    main()
