import os
import json
import sys
from typing import Any, Dict

from iot_controller import IoTController, build_frame

# Load environment from multiple common files if available
try:
	from dotenv import load_dotenv  # type: ignore
	for env_name in (".env", ".env.local", ".env.example", ".env.sample", "sample.env"):
		path = os.path.join(os.path.dirname(__file__), env_name)
		if os.path.exists(path):
			load_dotenv(dotenv_path=path, override=False)
except Exception:
	pass

BASE_DIR = os.path.dirname(__file__)
DEVICES_FILE = os.path.join(BASE_DIR, "devices.json")


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


def to_env_key_from_name(name: str) -> str:
	key = ''.join(ch if ch.isalnum() else '_' for ch in name).upper()
	return key


def parse_devices_env() -> Dict[str, str]:
	"""Parse DEVICES env like: "Cup-Dropping Machine:COM10;Other:COM3"""
	result: Dict[str, str] = {}
	val = os.getenv("DEVICES")
	if not val:
		return result
	pairs = [p.strip() for p in val.replace(',', ';').split(';') if p.strip()]
	for pair in pairs:
		if ':' in pair:
			name, com = pair.split(':', 1)
			result[name.strip()] = com.strip()
	return result


def resolve_com(default_com: str | None, device_name: str | None) -> str:
	devices_map = parse_devices_env()
	if device_name and device_name in devices_map:
		return devices_map[device_name]
	return default_com or "COM1"


def get_commands_for_device(device_name: str, fallback_actions: list[dict] | None) -> Dict[str, dict]:
	commands_key = f"{to_env_key_from_name(device_name)}_COMMANDS"
	commands_json = os.getenv(commands_key)
	if commands_json:
		try:
			data = json.loads(commands_json)
			if isinstance(data, dict):
				return data
		except Exception:
			pass
	# Fallback: derive from devices.json actions list as labels only (no building info)
	cmds: Dict[str, dict] = {}
	if fallback_actions:
		for a in fallback_actions:
			aid = a.get("id")
			if aid:
				cmds[aid] = {"label": a.get("label", aid)}
	return cmds


def build_frame_from_command(command: dict) -> bytes:
	cc = int(command.get("command_code"), 0)
	ic = int(command.get("instruction_code"), 0)
	data_list = command.get("data_bytes") or []
	data_bytes = bytes(data_list)
	return build_frame(cc, ic, data_bytes)


def main() -> int:
	devices_data = load_json(DEVICES_FILE)
	devices = devices_data.get("devices", [])
	if not devices:
		print("Không có thiết bị trong devices.json")
		return 2
	device_names = [d.get("name", d.get("id", "unknown")) for d in devices]
	di = pick(device_names, "Chọn thiết bị:")
	device = devices[di]

	device_name = device.get("name", device.get("id"))
	port = resolve_com(device.get("default_com"), device_name)
	baud = int(device.get("baud", 115200))

	commands = get_commands_for_device(device_name, device.get("actions"))
	if not commands:
		print("Không có lệnh cho thiết bị. Khai báo <DEVICE_NAME>_COMMANDS trong .env")
		return 2
	action_ids = list(commands.keys())
	labels = [commands[a].get("label", a) for a in action_ids]
	ai = pick(labels, f"Thiết bị: {device_name} - Chọn lệnh:")
	action_id = action_ids[ai]
	cmd_def = commands.get(action_id)

	# If full frame spec provided, build; else try hex string fallback
	frame_hex = cmd_def.get("hex") if isinstance(cmd_def, dict) else None
	if frame_hex:
		payload = bytes.fromhex(frame_hex.replace(' ', ''))
		hex_str = payload.hex()
	else:
		if not all(k in cmd_def for k in ("command_code", "instruction_code")):
			print("Lệnh không đủ thông tin. Cần command_code và instruction_code hoặc hex.")
			return 2
		frame = build_frame_from_command(cmd_def)
		hex_str = frame.hex()

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
