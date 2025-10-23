import binascii
from typing import Optional, List
import time

import serial
from serial.tools import list_ports


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


def compute_checksum(payload_without_checksum_and_end: bytes) -> int:
	return sum(payload_without_checksum_and_end) & 0xFF


def build_frame(command_code: int, instruction_code: int, data_bytes: bytes | None = None) -> bytes:
	if data_bytes is None:
		data_bytes = b""
	# length = total bytes including checksum and end
	length_value = 3 + len(data_bytes) + 2  # cmd + len + ins + data... + checksum + end
	frame_wo_cs_end = bytes([command_code, length_value, instruction_code]) + data_bytes
	checksum = compute_checksum(frame_wo_cs_end)
	return frame_wo_cs_end + bytes([checksum, 0xFF])


class IoTController:
	def __init__(self) -> None:
		self._ser: Optional[serial.Serial] = None

	@staticmethod
	def list_ports() -> list[str]:
		return [p.device for p in list_ports.comports()]

	def open(self, port: str, baudrate: int = 115200, timeout: float = 1.0, rtscts: bool = False, xonxoff: bool = False) -> None:
		if self._ser and self._ser.is_open:
			self.close()
		self._ser = serial.Serial(
			port=port,
			baudrate=baudrate,
			timeout=timeout,
			rtscts=rtscts,
			xonxoff=xonxoff,
			bytesize=serial.EIGHTBITS,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
		)

	def is_open(self) -> bool:
		return bool(self._ser and self._ser.is_open)

	def close(self) -> None:
		if self._ser and self._ser.is_open:
			self._ser.close()

	def send_hex(self, hex_string: str) -> int:
		if not self.is_open():
			raise RuntimeError("Serial port is not open")
		payload = normalize_hex_string(hex_string)
		written = self._ser.write(payload)
		self._ser.flush()
		return written

	def send_frame(self, command_code: int, instruction_code: int, data_hex: str | None = None) -> int:
		if not self.is_open():
			raise RuntimeError("Serial port is not open")
		data_bytes = normalize_hex_string(data_hex) if data_hex else b""
		frame = build_frame(command_code, instruction_code, data_bytes)
		written = self._ser.write(frame)
		self._ser.flush()
		return written

	def read_bytes(self, num_bytes: int = 1) -> bytes:
		if not self.is_open():
			raise RuntimeError("Serial port is not open")
		return self._ser.read(num_bytes)

	def read_until_hex(self, hex_pattern: str, max_bytes: int = 4096) -> bytes:
		if not self.is_open():
			raise RuntimeError("Serial port is not open")
		pattern = normalize_hex_string(hex_pattern)
		if not pattern:
			return b""
		buffer = bytearray()
		while len(buffer) < max_bytes:
			b = self._ser.read(1)
			if not b:
				break
			buffer += b
			if buffer.endswith(pattern):
				break
		return bytes(buffer)

	def read_frame(self, overall_timeout: float = 2.0) -> bytes:
		"""Read one framed reply: [cmd][len][ins][data...][checksum][0xFF]."""
		if not self.is_open():
			raise RuntimeError("Serial port is not open")
		start = time.time()
		buf = bytearray()
		# Read first two bytes (cmd, len)
		while len(buf) < 2:
			b = self._ser.read(1)
			if b:
				buf += b
			else:
				if time.time() - start > overall_timeout:
					return bytes(buf)
		# Determine remaining bytes based on length
		if len(buf) < 2:
			return bytes(buf)
		total_len = buf[1]
		remaining = max(total_len - len(buf), 0)
		while remaining > 0:
			chunk = self._ser.read(remaining)
			if chunk:
				buf += chunk
				remaining = max(total_len - len(buf), 0)
			else:
				if time.time() - start > overall_timeout:
					break
		return bytes(buf)


__all__ = ["IoTController", "normalize_hex_string", "build_frame", "compute_checksum"]
