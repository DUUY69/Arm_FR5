import os
import sys
import socket
import hashlib
import xmlrpc.client
import time

LUA_DIR = os.path.join(os.path.dirname(__file__), 'lua_scripts')
ROBOT_IP = '192.168.58.2'  # Đổi IP robot tại đây nếu cần
XMLRPC_PORT = 20003
TCP_PORT = 20010

# Framing bytes (used by older/path fallback)
FRAME_START = b'/f/b'
FRAME_END = b'/b/f'

# SDK robot instance cache
_robot_instance = None


def get_robot():
    """Return an object that can be used to control the robot.
    Prefer the Windows SDK `fairino.Robot.RPC` if available (adds higher-level helpers
    like LuaUpload, ProgramLoad, ProgramRun). If not available, fall back to a
    plain xmlrpc.ServerProxy so the tool still works.
    """
    global _robot_instance
    if _robot_instance is not None:
        return _robot_instance

    # Try vendored package first: MyArm_Python/vendor/fairino
    try:
        try:
            # Import the vendored package if available
            from vendor import fairino as vf  # type: ignore
            # The vendored package exposes Robot (module or class). Try to get RPC
            if hasattr(vf, 'Robot'):
                SDK_Robot = vf.Robot
                try:
                    _robot_instance = SDK_Robot.RPC(ROBOT_IP)
                    print(f"Using vendored fairino.Robot to connect to {ROBOT_IP}")
                    return _robot_instance
                except Exception as e:
                    print(f"Vendored fairino.Robot import succeeded but RPC() failed: {e}")
        except Exception:
            # vendored package not present or failed; continue to other options
            pass

        # Next, try the repo SDK path (older behavior)
        sdk_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'fairino-python-sdk-main', 'fairino-python-sdk-main', 'windows'))
        sdk_path = os.path.abspath(sdk_path)
        if os.path.isdir(sdk_path):
            if sdk_path not in sys.path:
                sys.path.insert(0, sdk_path)
            # import the SDK Robot wrapper
            try:
                from fairino import Robot as SDK_Robot
                print(f"Using fairino SDK Robot (from {sdk_path}) to connect to {ROBOT_IP}")
                inst = SDK_Robot.RPC(ROBOT_IP)
                # SDK sets a connection flag (RPC.is_conect). If the SDK failed to
                # establish XML-RPC communication it sets this to False and most
                # high-level calls will return error -4. In that case prefer the
                # xmlrpc.ServerProxy fallback so the tool can still operate.
                conn_ok = True
                try:
                    # prefer instance attribute if available
                    conn_ok = bool(getattr(inst, 'is_conect', True))
                except Exception:
                    conn_ok = True

                if conn_ok:
                    _robot_instance = inst
                    return _robot_instance
                else:
                    print("SDK RPC instance created but XML-RPC connection failed (is_conect=False); falling back to xmlrpc.ServerProxy")
                    # don't return the SDK instance; fall through to xmlrpc fallback
            except Exception as ie:
                print(f"Failed to import SDK from {sdk_path}: {ie}")
                # list directory to help debugging
                try:
                    print("SDK folder listing:")
                    for entry in os.listdir(sdk_path):
                        print("  ", entry)
                except Exception:
                    pass

        else:
            print(f"SDK path not found at {sdk_path}")

        # fallback to xmlrpc proxy (legacy) - prefer /RPC2 path used by C#
        print("Falling back to xmlrpc.ServerProxy (using /RPC2)")
        _robot_instance = xmlrpc.client.ServerProxy(f'http://{ROBOT_IP}:{XMLRPC_PORT}/RPC2')
        return _robot_instance
    except Exception as e:
        print(f"Unexpected error locating SDK: {e}; falling back to xmlrpc.ServerProxy")
        _robot_instance = xmlrpc.client.ServerProxy(f'http://{ROBOT_IP}:{XMLRPC_PORT}/RPC2')
        return _robot_instance


def print_menu():
    print("\n=== Fairino Robot Console (Python) ===")
    print("0. Test connection (RPC/TCP diagnostics)")
    print("1. Upload Lua file")
    print("2. Run Lua file")
    print("3. View log")
    print("4. Exit")


def list_lua_files():
    files = [f for f in os.listdir(LUA_DIR) if f.endswith('.lua')]
    for i, f in enumerate(files):
        print(f"{i+1}. {f}")
    return files


def test_connection():
    """Run quick diagnostics: TCP connect to TCP_PORT and probe RPC ports."""
    print(f"Testing robot {ROBOT_IP}")
    # TCP port test
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((ROBOT_IP, TCP_PORT))
        print(f"TCP port {TCP_PORT}: OPEN")
        s.close()
    except Exception as e:
        print(f"TCP port {TCP_PORT}: CLOSED or unreachable ({e})")

    # Probe RPC ports
    paths = ['', 'RPC2', 'RPC']
    for p in (20003, XMLRPC_PORT):
        for path in paths:
            url_path = f"/{path}" if path else '/'
            try:
                proxy = xmlrpc.client.ServerProxy(f'http://{ROBOT_IP}:{p}{url_path}')
                # quick call
                try:
                    ret = proxy.GetLuaList()
                    print(f"XML-RPC {p}{url_path}: reachable, GetLuaList() returned")
                except Exception as e:
                    print(f"XML-RPC {p}{url_path}: reachable but RPC call failed ({e})")
            except Exception as e:
                print(f"XML-RPC {p}{url_path}: not reachable ({e})")



def upload_lua(filename):
    path = os.path.join(LUA_DIR, filename)
    if not os.path.exists(path):
        print("File not found.")
        return False

    robot = get_robot()

    # If we have the SDK Robot object and it appears connected, use its high-level LuaUpload helper
    if hasattr(robot, 'LuaUpload'):
        # Some SDK instances expose an 'is_conect' flag indicating XML-RPC health
        try:
            sdk_conn_ok = bool(getattr(robot, 'is_conect', True))
        except Exception:
            sdk_conn_ok = True

        if not sdk_conn_ok:
            print("SDK instance reports XML-RPC disconnected (is_conect=False). Using xmlrpc fallback for upload.")
        else:
            try:
                print(f"Uploading {filename} via SDK LuaUpload...")
                full_path = os.path.abspath(path)
                res = robot.LuaUpload(full_path)
                # LuaUpload returns 0 on success or an error code; some wrappers may
                # return (err, msg) if LuaUpLoadUpdate contains a message
                if isinstance(res, tuple):
                    err, msg = res
                    if err == 0:
                        print(f"[Upload] {filename}: OK")
                        return True
                    else:
                        print(f"[Upload] {filename}: FAIL ({err}) - {msg}")
                        return False
                else:
                    # integer result
                    if int(res) == 0:
                        print(f"[Upload] {filename}: OK")
                        return True
                    else:
                        print(f"[Upload] {filename}: FAIL ({res})")
                        return False
            except Exception as e:
                print(f"SDK LuaUpload failed: {e}")
                # fall through to xmlrpc fallback below

    # Fallback: use xmlrpc + manual TCP upload implementing the SDK sequence:
    # 1) proxy.FileUpload(fileType, file_name)  (prepare for upload)
    # 2) open TCP to port TCP_PORT and send framed data:
    #    head = f"/f/b{total_size:10d}{md5}" (ASCII), then file bytes in chunks, then "/b/f"
    # 3) proxy.LuaUpLoadUpdate(file_name)
    def find_working_proxy(ports=(20003, XMLRPC_PORT), timeout=2.0):
        paths = ['', 'RPC2', 'RPC']
        for p in ports:
            for path in paths:
                try:
                    url_path = f"/{path}" if path else '/'
                    proxy = xmlrpc.client.ServerProxy(f'http://{ROBOT_IP}:{p}{url_path}')
                    # quick health check
                    proxy_timeout = socket.getdefaulttimeout()
                    socket.setdefaulttimeout(timeout)
                    try:
                        # many controllers expose GetControllerIP; fall back to GetLuaList if unavailable
                        try:
                            _ = proxy.GetControllerIP()
                        except Exception:
                            _ = proxy.GetLuaList()
                    finally:
                        socket.setdefaulttimeout(proxy_timeout)
                    print(f"Using XML-RPC on port {p} path '{url_path}'")
                    return proxy
                except Exception as exc:
                    # continue trying other paths
                    # (we'll print debug info elsewhere if needed)
                    continue
        return None

    proxy = find_working_proxy()
    if not proxy:
        print("XML-RPC upload failed: could not reach robot on known RPC ports")
        return False

    try:
        # prepare upload via RPC (fileType 0 = lua file in SDK)
        print(f"Calling FileUpload for {filename} via xmlrpc fallback (prepare)...")
        # some RPC implementations expect (fileType, fileName)
        try:
            r = proxy.FileUpload(0, filename)
        except Exception as e:
            # try alternative signature (legacy)
            r = proxy.FileUpload(filename)
        # now stream file over TCP to TCP_PORT
        with open(path, 'rb') as f:
            total_data = f.read()

        # Match C# SDK calculation: total_size = file_size + 4 + 46
        # (the SDK adds an internal header/footer length; keep parity)
        file_size = len(total_data)
        total_size = file_size + 4 + 46
        send_md5 = hashlib.md5(total_data).hexdigest()

        # C# used Encoding.Default when sending header/footer; on Windows this
        # is typically a legacy code page. Use locale preferred encoding to
        # mimic behavior when sending the ASCII header/footer bytes.
        try:
            default_enc = sys.getdefaultencoding() or 'utf-8'
        except Exception:
            default_enc = 'utf-8'

        head = f"/f/b{total_size:10d}{send_md5}"
        head_data = head.encode(default_enc, errors='replace')
        end_data = "/b/f".encode(default_enc)

        print(f"Opening TCP to {ROBOT_IP}:{TCP_PORT} to stream {total_size} bytes...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        try:
            sock.connect((ROBOT_IP, TCP_PORT))
            sock.sendall(head_data)
            # send in chunks
            sent = 0
            CHUNK = 2 * 1024 * 1024
            while sent < total_size:
                chunk = total_data[sent:sent+CHUNK]
                sock.sendall(chunk)
                sent += len(chunk)
            sock.sendall(end_data)
            # give controller a moment to process
            time.sleep(0.5)
            # try to receive response (may block briefly)
            try:
                resp = sock.recv(4096)
                resp_text = resp.decode(errors='ignore') if resp else ''
            except Exception:
                resp_text = ''
        finally:
            try:
                sock.close()
            except Exception:
                pass

        print(f"TCP upload response: {resp_text}")
        # Finalize via RPC
        update = proxy.LuaUpLoadUpdate(filename)
        try:
            update_result, update_msg = update
        except Exception:
            update_result, update_msg = update, ''
        print(f"LuaUpLoadUpdate returned: {update_result}, message: {update_msg}")
        return int(update_result) == 0
    except Exception as e:
        print(f"XML-RPC upload failed: {e}")
        return False


def run_lua(filename):
    robot = get_robot()
    # Prefer SDK ProgramLoad + ProgramRun
    if hasattr(robot, 'ProgramLoad') and hasattr(robot, 'ProgramRun'):
        try:
            remote_path = f"/fruser/{filename}"
            lr = robot.ProgramLoad(remote_path)
            print(f"ProgramLoad({remote_path}): {lr}")
            if int(lr) == 0:
                rr = robot.ProgramRun()
                print(f"ProgramRun: {rr}")
            else:
                print(f"ProgramLoad failed: {lr}")
        except Exception as e:
            print(f"SDK ProgramLoad/ProgramRun failed: {e}")
    else:
        # fallback to xmlrpc ProgramLoad/ProgramRun if available
        try:
            proxy = xmlrpc.client.ServerProxy(f'http://{ROBOT_IP}:{XMLRPC_PORT}/RPC2')
            remote_path = f"/fruser/{filename}"
            lr = proxy.ProgramLoad(remote_path)
            print(f"ProgramLoad({remote_path}): {lr}")
            if int(lr) == 0:
                rr = proxy.ProgramRun()
                print(f"ProgramRun: {rr}")
        except Exception as e:
            print(f"XML-RPC ProgramRun failed: {e}")


def view_log():
    robot = get_robot()
    # SDK may not expose GetLog; try SDK first then fallback to xmlrpc proxy
    if hasattr(robot, 'GetLog'):
        try:
            log = robot.GetLog()
            print("--- Robot Log ---")
            print(log)
            return
        except Exception as e:
            print(f"SDK GetLog failed: {e}")

    try:
        proxy = xmlrpc.client.ServerProxy(f'http://{ROBOT_IP}:{XMLRPC_PORT}/RPC2')
        log = proxy.GetLog()
        print("--- Robot Log ---")
        print(log)
    except Exception as e:
        print(f"XML-RPC GetLog failed: {e}")


def main():
    while True:
        print_menu()
        choice = input("Select option: ").strip()
        if choice == '0':
            test_connection()
            continue
        if choice == '1':
            files = list_lua_files()
            if not files:
                print("No Lua files found in lua_scripts.")
                continue
            idx = input("Select file number to upload: ").strip()
            if not idx.isdigit() or int(idx) < 1 or int(idx) > len(files):
                print("Invalid selection.")
                continue
            upload_lua(files[int(idx)-1])
        elif choice == '2':
            files = list_lua_files()
            if not files:
                print("No Lua files found in lua_scripts.")
                continue
            idx = input("Select file number to run: ").strip()
            if not idx.isdigit() or int(idx) < 1 or int(idx) > len(files):
                print("Invalid selection.")
                continue
            run_lua(files[int(idx)-1])
        elif choice == '3':
            view_log()
        elif choice == '4':
            print("Exiting.")
            break
        else:
            print("Invalid option.")

if __name__ == '__main__':
    if not os.path.exists(LUA_DIR):
        os.makedirs(LUA_DIR)
    main()
