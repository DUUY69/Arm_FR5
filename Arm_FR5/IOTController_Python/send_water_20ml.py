#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gửi lệnh thả nước 20ml từ máy làm đá
"""

import serial
import time
import sys
import codecs

# Fix encoding
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# COM17, 115200
ser = serial.Serial('COM17', 115200, timeout=2.0)

# Binary hex command: 04 07 AA 02 02 B5 FF
# Dispense water (02), quantity=2 (20ml)
command = bytes([0x04, 0x07, 0xAA, 0x02, 0x02, 0xB5, 0xFF])

print("=" * 70)
print("THA NUOC 20ML - ICE MAKER")
print("=" * 70)
print(f"\nSending: {command.hex().upper()}")
print("Bytes:", [hex(b) for b in command])
print("\nBreakdown:")
print("  - Command Code: 0x04 (Dispense Beverage)")
print("  - Length: 0x07")
print("  - Instruction: 0xAA (Set)")
print("  - Beverage: 0x02 (Water)")
print("  - Quantity: 0x02 (2 units = 20ml)")
print("  - Checksum: 0xB5")
print("  - End: 0xFF")

ser.write(command)
ser.flush()

print("\nWaiting for response...")
time.sleep(0.5)

if ser.in_waiting:
    response = ser.read(ser.in_waiting)
    print(f"\nResponse: {response.hex().upper()}")
    
    if len(response) >= 6 and response[3] == 0x01:
        print("✅ SUCCESS! Máy sẽ thả nước 20ml...")
    else:
        print("❌ FAILED!")
else:
    print("No response")

ser.close()
print("\nDone!")
