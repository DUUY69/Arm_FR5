from __future__ import annotations

"""
Cup-Dropping Machine serial protocol helpers.

Frame layout (all values are bytes):
  [CommandCode][LengthCode][InstructionCode][Data...][Checksum][EndCode]

- InstructionCode: 0x55 (query) or 0xAA (set)
- LengthCode: total number of bytes in the entire frame (including Checksum and EndCode)
- Checksum: lower 8 bits of the sum of all bytes except Checksum and EndCode
- EndCode: fixed 0xFF

Serial defaults:
- 115200 baud, 8 data bits, 1 stop bit, no parity
"""

import binascii
from typing import Optional

import serial

# Serial defaults
DEFAULT_BAUDRATE: int = 115200
DEFAULT_BYTESIZE = serial.EIGHTBITS
DEFAULT_PARITY = serial.PARITY_NONE
DEFAULT_STOPBITS = serial.STOPBITS_ONE

# Protocol constants
INSTRUCTION_QUERY: int = 0x55
INSTRUCTION_SET: int = 0xAA
END_CODE: int = 0xFF


def compute_checksum_without_end(frame_without_checksum_and_end: bytes) -> int:
	return sum(frame_without_checksum_and_end) & 0xFF


def verify_frame(frame: bytes) -> bool:
	"""Return True if frame passes length and checksum validation and ends with 0xFF."""
	if not frame or len(frame) < 5:
		return False
	length_field = frame[1]
	if length_field != len(frame):
		return False
	if frame[-1] != END_CODE:
		return False
	checksum_in_frame = frame[-2]
	calc = compute_checksum_without_end(frame[:-2])
	return checksum_in_frame == calc


def normalize_hex_string(hex_string: str) -> bytes:
	cleaned = hex_string.replace(" ", "").replace("0x", "").replace("-", "").replace("_", "")
	if len(cleaned) == 0:
		return b""
	if len(cleaned) % 2 != 0:
		cleaned = "0" + cleaned
	try:
		return binascii.unhexlify(cleaned)
	except binascii.Error as exc:
		raise ValueError(f"Invalid hex string: {hex_string}") from exc


