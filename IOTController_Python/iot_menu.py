import os
import json
import sys
from typing import Any

from iot_controller import IoTController

try:
	from dotenv import load_dotenv  # type: ignore
	load_dotenv()
except Exception:
	pass

BASE_DIR = os.path.dirname(__file__)
DEVICES_FILE = os.path.join(BASE_DIR, "devices.json")
ACTIONS_FILE = os.path.join(BASE_DIR, "actions.json")


def load_json(path: str) -> Any:
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def pick(options: list[str], prompt: str) -> int:
	print(prompt)
	for idx, opt in enumerate(options, start=1):
		print(f"  {idx}. {opt}")
	while True:
		val = input("Chọn số: ").strip()
		if not val.isdigit():
			print("Vui lòng nhập số hợp lệ.")
			continue
		choice = int(val)
		if 1 <= choice <= len(options):
			return choice - 1
		print("Ngoài phạm vi, thử lại.")


def resolve_com(env_key: str | None, default_com: str | None) -> str:
	if env_key:
		val = os.getenv(env_key)
		if val:
			return val
	return default_com or "COM1"


def main() -> int:
	devices = load_json(DEVICES_FILE).get("devices", [])
	if not devices:
		print("Không có thiết bị trong devices.json")
		return 2
	device_names = [d.get("name", d.get("id", "unknown")) for d in devices]
	di = pick(device_names, "Chọn thiết bị:")
	device = devices[di]

	actions_map = load_json(ACTIONS_FILE)
	actions = device.get("actions", [])
	action_labels = [a.get("label", a.get("id", "unknown")) for a in actions]
	ai = pick(action_labels, f"Thiết bị: {device_names[di]} - Chọn lệnh:")
	action_id = actions[ai].get("id")
	if not action_id:
		print("Action không hợp lệ")
		return 2

	# resolve COM and baud
	port = resolve_com(device.get("env_com"), device.get("default_com"))
	baud = int(device.get("baud", 115200))

	hex_str = None
	if action_id in actions_map:
		hex_str = actions_map[action_id]
	else:
		for _, group in actions_map.items():
			if isinstance(group, dict) and action_id in group:
				hex_str = group[action_id]
				break
	if not hex_str:
		print(f"Không tìm thấy mã hex cho action: {action_id}")
		return 2

	print(f"Gửi tới {port} @ {baud}: {hex_str}")
	ctl = IoTController()
	ctl.open(port, baudrate=baud, timeout=1.0)
	try:
		written = ctl.send_hex(hex_str)
		print(f"Đã gửi {written} byte")
		return 0
	finally:
		ctl.close()


if __name__ == "__main__":
	raise SystemExit(main())
