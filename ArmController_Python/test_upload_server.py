from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import threading, socket, time, os

# Ensure lua_scripts exists and create a small test lua file
root = os.path.dirname(__file__)
lua_dir = os.path.join(root, 'lua_scripts')
if not os.path.exists(lua_dir):
    os.makedirs(lua_dir)
lua_file = os.path.join(lua_dir, 'test_sim.lua')
with open(lua_file, 'w', encoding='utf-8') as f:
    f.write('print("hello from lua test")\n')

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2', '/RPC', '/')


def start_xmlrpc(host='127.0.0.1', port=20003):
    server = SimpleXMLRPCServer((host, port), requestHandler=RequestHandler, logRequests=True, allow_none=True)
    # Minimal RPC functions the client expects
    def FileUpload(ftype, fname):
        print(f"[xmlrpc] FileUpload called: ftype={ftype}, fname={fname}")
        return 0
    def LuaUpLoadUpdate(fname):
        print(f"[xmlrpc] LuaUpLoadUpdate called: {fname}")
        return (0, 'ok')
    def GetControllerIP():
        return host
    def GetLuaList():
        return []

    server.register_function(FileUpload, 'FileUpload')
    server.register_function(LuaUpLoadUpdate, 'LuaUpLoadUpdate')
    server.register_function(GetControllerIP, 'GetControllerIP')
    server.register_function(GetLuaList, 'GetLuaList')

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"XML-RPC server listening on {host}:{port} (paths /RPC2,/RPC,/)")
    return server


def start_tcp_server(host='127.0.0.1', port=20010):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    print(f"TCP server listening on {host}:{port}")

    def accept_once():
        conn, addr = srv.accept()
        print('[tcp] Accepted connection from', addr)
        conn.settimeout(5)
        data = b''
        try:
            while True:
                part = conn.recv(4096)
                if not part:
                    break
                data += part
                if b'/b/f' in data:
                    break
        except Exception as e:
            print('[tcp] recv exception:', e)

        print('[tcp] received bytes:', len(data))
        # print a short preview of header
        preview = data[:128].decode(errors='ignore')
        print('[tcp] preview:', preview)
        # respond as the real robot would
        try:
            conn.sendall(b"SUCCESS")
        except Exception as e:
            print('[tcp] send exception:', e)
        try:
            conn.close()
        except:
            pass
        try:
            srv.close()
        except:
            pass

    t = threading.Thread(target=accept_once, daemon=True)
    t.start()
    return srv


if __name__ == '__main__':
    xml = start_xmlrpc()
    tcp = start_tcp_server()
    # Run the client code from myarm
    import sys
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    import myarm
    # Point myarm to localhost
    myarm.ROBOT_IP = '127.0.0.1'
    myarm.XMLRPC_PORT = 20003
    myarm.TCP_PORT = 20010

    print('\n--- Starting upload test ---')
    ok = myarm.upload_lua('test_sim.lua')
    print('upload_lua returned ->', ok)
    # give servers time to finish
    time.sleep(1)
    print('Test complete')
