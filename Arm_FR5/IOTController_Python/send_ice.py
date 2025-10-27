#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gửi hex binary đến máy làm đá
"""

import serial
import time

# COM17, 115200
ser = serial.Serial('COM17', 115200, timeout=2.0)

# Binary hex command: 04 07 AA 01 05 BB FF
# Dispense 5 ice cubes
command = bytes([0x04, 0x07, 0xAA, 0x01, 0x05, 0xBB, 0xFF])

print("Sending:", command.hex().upper())
print("Bytes:", [hex(b) for b in command])

ser.write(command)
ser.flush()

print("\nWaiting for response...")
time.sleep(0.5)

if ser.in_waiting:
    response = ser.read(ser.in_waiting)
    print("Response:", response.hex().upper())
else:
    print("No response")

ser.close()
print("Done!")
