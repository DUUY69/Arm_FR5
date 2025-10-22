import argparse
import sys
import binascii

from iot_controller import IoTController


def cmd_list(args: argparse.Namespace) -> int:
	ports = IoTController.list_ports()
	for p in ports:
		print(p)
	if not ports:
		print("No COM ports found")
	return 0


def cmd_send(args: argparse.Namespace) -> int:
	ctl = IoTController()
	ctl.open(args.port, baudrate=args.baud, timeout=args.timeout, rtscts=args.rtscts, xonxoff=args.xonxoff)
	try:
		written = ctl.send_hex(args.hex)
		print(f"Wrote {written} bytes")
		if args.read is not None:
			data = ctl.read_bytes(args.read)
			print(binascii.hexlify(data).decode())
		if args.until:
			data = ctl.read_until_hex(args.until, max_bytes=args.max_bytes)
			print(binascii.hexlify(data).decode())
		return 0
	finally:
		ctl.close()


def build_parser() -> argparse.ArgumentParser:
	p = argparse.ArgumentParser(description="IoT Serial Controller over COM using hex payloads")
	sub = p.add_subparsers(dest="cmd", required=True)

	p_list = sub.add_parser("list", help="List available COM ports")
	p_list.set_defaults(func=cmd_list)

	p_send = sub.add_parser("send", help="Send hex to a COM port")
	p_send.add_argument("--port", required=True, help="COM port e.g. COM3")
	p_send.add_argument("--baud", type=int, default=9600, help="Baud rate (default 9600)")
	p_send.add_argument("--timeout", type=float, default=1.0, help="Read timeout seconds")
	p_send.add_argument("--rtscts", action="store_true", help="Enable RTS/CTS flow control")
	p_send.add_argument("--xonxoff", action="store_true", help="Enable XON/XOFF flow control")
	p_send.add_argument("--hex", required=True, help="Hex string e.g. 'A1 01 FF' or '0xA101FF'")
	p_send.add_argument("--read", type=int, default=None, help="Read N bytes after send")
	p_send.add_argument("--until", default=None, help="Read until hex pattern matched e.g. 'FF0D'")
	p_send.add_argument("--max-bytes", type=int, default=4096, help="Max bytes to read when using --until")
	p_send.set_defaults(func=cmd_send)

	return p


def main(argv: list[str] | None = None) -> int:
	parser = build_parser()
	args = parser.parse_args(argv)
	try:
		return args.func(args)
	except Exception as exc:
		print(f"Error: {exc}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
