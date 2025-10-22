import binascii
from typing import Optional

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


class IoTController:
	def __init__(self) -> None:
		self._ser: Optional[serial.Serial] = None

	@staticmethod
	def list_ports() -> list[str]:
		return [p.device for p in list_ports.comports()]

	def open(self, port: str, baudrate: int = 9600, timeout: float = 1.0, rtscts: bool = False, xonxoff: bool = False) -> None:
		if self._ser and self._ser.is_open:
			self.close()
		self._ser = serial.Serial(
			port=port,
			baudrate=baudrate,
			timeout=timeout,
			rtscts=rtscts,
			xonxoff=xonxoff,
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


__all__ = ["IoTController", "normalize_hex_string"]
