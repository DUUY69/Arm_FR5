#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Đơn giản nhất - Gửi hex để thả 5 viên đá
"""

import serial

# Hex command to dispense 5 ice cubes
hex_command = "04 07 AA 01 05 BB FF"
hex_bytes = bytes.fromhex(hex_command.replace(" ", ""))

# Connect to COM17
ser = serial.Serial('COM17', 115200, timeout=1.0)

print("Sending:", hex_command)
ser.write(hex_bytes)
ser.close()

print("Done!")
