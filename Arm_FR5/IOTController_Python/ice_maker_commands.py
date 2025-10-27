#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ice Maker Commands
Lệnh để điều khiển máy làm đá (Ice Maker) theo protocol Z01/Z02/Z03
"""

import serial
import time


class IceMakerController:
    """Controller cho máy làm đá"""
    
    def __init__(self, port, baudrate=115200):
        """
        Args:
            port: COM port (ví dụ: 'COM10')
            baudrate: Baud rate (mặc định 115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
    def open(self):
        """Mở serial port"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            print(f"✅ Đã mở {self.port}")
            return True
        except Exception as e:
            print(f"❌ Lỗi mở {self.port}: {e}")
            return False
    
    def close(self):
        """Đóng serial port"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"✅ Đã đóng {self.port}")
    
    def compute_checksum(self, data):
        """Tính checksum theo protocol"""
        return sum(data) & 0xFF
    
    def send_command(self, cmd_code, instruction_code, data=None):
        """
        Gửi lệnh đến máy làm đá
        
        Args:
            cmd_code: Command code (0x01-0x04)
            instruction_code: 0x55 (query) hoặc 0xAA (set)
            data: List of data bytes
        """
        if not self.ser or not self.ser.is_open:
            print("❌ Serial port chưa mở!")
            return False
        
        # Build frame
        if data is None:
            data = []
        
        # Length = cmd + len + instruction + data + checksum + end
        length = 3 + len(data) + 2
        
        # Frame without checksum and end
        frame_wo_cs = bytes([cmd_code, length, instruction_code] + data)
        
        # Calculate checksum
        checksum = self.compute_checksum(frame_wo_cs)
        
        # Full frame
        frame = frame_wo_cs + bytes([checksum, 0xFF])
        
        try:
            # Send
            self.ser.write(frame)
            self.ser.flush()
            
            print(f"📤 Đã gửi: {frame.hex().upper()}")
            
            # Wait for response
            time.sleep(0.1)
            
            # Read response
            if self.ser.in_waiting > 0:
                response = self.ser.read(self.ser.in_waiting)
                print(f"📥 Nhận: {response.hex().upper()}")
                return response
            else:
                print("⚠️ Không có response")
                return None
                
        except Exception as e:
            print(f"❌ Lỗi gửi: {e}")
            return None
    
    def query_status(self):
        """Query status (0x01)"""
        print("\n🔍 Đang query status...")
        return self.send_command(0x01, 0x55)
    
    def query_parameters(self):
        """Query parameters (0x02)"""
        print("\n🔍 Đang query parameters...")
        return self.send_command(0x02, 0x55)
    
    def dispense_ice(self, quantity=5):
        """
        Thả đá (dispense ice)
        
        Args:
            quantity: Số lượng đá (1-120)
        """
        print(f"\n❄️ Đang thả {quantity} viên đá...")
        
        # 0x04: Dispense Beverage
        # Beverage Number: 0x01 (ice)
        # Data 1: quantity
        return self.send_command(0x04, 0xAA, [0x01, quantity])
    
    def dispense_water(self, quantity=1):
        """
        Thả nước (dispense water)
        
        Args:
            quantity: Số lượng (1-10)
        """
        print(f"\n💧 Đang thả nước {quantity}...")
        
        # 0x04: Dispense Beverage
        # Beverage Number: 0x02 (water)
        # Data 1: quantity
        return self.send_command(0x04, 0xAA, [0x02, quantity])
    
    def dispense_ice_water(self, quantity=1):
        """
        Thả đá nước (dispense ice water)
        
        Args:
            quantity: Số lượng (1-10)
        """
        print(f"\n❄️💧 Đang thả đá nước {quantity}...")
        
        # 0x04: Dispense Beverage
        # Beverage Number: 0x03 (ice water)
        # Data 1: quantity
        return self.send_command(0x04, 0xAA, [0x03, quantity])


def main():
    """Test function"""
    print("=" * 70)
    print("❄️ ICE MAKER CONTROLLER")
    print("=" * 70)
    
    # COM port của máy làm đá
    ice_maker = IceMakerController('COM17', baudrate=115200)
    
    if not ice_maker.open():
        print("❌ Không thể mở serial port!")
        return
    
    try:
        # Query status
        ice_maker.query_status()
        time.sleep(1)
        
        # Query parameters
        ice_maker.query_parameters()
        time.sleep(1)
        
        # Thả 5 viên đá
        ice_maker.dispense_ice(quantity=5)
        time.sleep(1)
        
        print("\n✅ Hoàn thành!")
        
    except KeyboardInterrupt:
        print("\n👋 Đã hủy!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
    finally:
        ice_maker.close()


if __name__ == "__main__":
    main()
