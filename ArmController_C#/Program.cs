using System;
using fairino;
using CookComputing.XmlRpc;
using System.Net.Http;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.IO;
using System.Collections.Generic;

namespace My_Arm
{
    class Program
    {
        static void Main(string[] args)
        {
            string robotIp = "192.168.58.2";
            // Always use workspace-rooted lua_scripts
            string workspaceRoot = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", ".."));
            string luaFolder = Path.Combine(workspaceRoot, "lua_scripts");
            string logsPath = Path.Combine(workspaceRoot, "logs");
            if (!Directory.Exists(logsPath)) Directory.CreateDirectory(logsPath);
            List<string> logBuffer = new List<string>();

            while (true)
            {
                Console.WriteLine("\n=== Fairino Robot Console ===");
                Console.WriteLine("1. Upload Lua file");
                Console.WriteLine("2. Run Lua file");
                Console.WriteLine("3. View log");
                Console.WriteLine("0. Exit");
                Console.Write("Select: ");
                var key = Console.ReadLine();
                if (key == "0") break;
                if (key == "1")
                {
                    try
                    {
                        if (!Directory.Exists(luaFolder)) Directory.CreateDirectory(luaFolder);
                        var files = Directory.GetFiles(luaFolder, "*.lua");
                        if (files.Length == 0)
                        {
                            Console.WriteLine("No Lua files found in lua_scripts. Please add .lua files.");
                            continue;
                        }
                        Console.WriteLine("Lua files:");
                        for (int i = 0; i < files.Length; i++)
                            Console.WriteLine($"  {i + 1}. {Path.GetFileName(files[i])}");
                        Console.Write("Select file to upload (number): ");
                        if (!int.TryParse(Console.ReadLine(), out int idx) || idx < 1 || idx > files.Length)
                        {
                            Console.WriteLine("Invalid selection.");
                            continue;
                        }
                        string fileToUpload = files[idx - 1];
                        int res = UploadLuaFile(robotIp, fileToUpload);
                        string msg = $"[Upload] {Path.GetFileName(fileToUpload)}: {(res == 0 ? "OK" : "Fail code " + res)}";
                        Console.WriteLine(msg);
                        logBuffer.Add(msg);
                    }
                    catch (Exception ex)
                    {
                        string msg = "[Upload] Exception: " + ex.Message;
                        Console.WriteLine(msg);
                        logBuffer.Add(msg);
                    }
                }
                else if (key == "2")
                {
                    try
                    {
                        var files = Directory.GetFiles(luaFolder, "*.lua");
                        if (files.Length == 0)
                        {
                            Console.WriteLine("No Lua files found in lua_scripts. Please add .lua files.");
                            continue;
                        }
                        Console.WriteLine("Lua files:");
                        for (int i = 0; i < files.Length; i++)
                            Console.WriteLine($"  {i + 1}. {Path.GetFileName(files[i])}");
                        Console.Write("Select file to run (number): ");
                        if (!int.TryParse(Console.ReadLine(), out int idx) || idx < 1 || idx > files.Length)
                        {
                            Console.WriteLine("Invalid selection.");
                            continue;
                        }
                        string fileToRun = Path.GetFileName(files[idx - 1]);
                        ICallSupervisor proxy = XmlRpcProxyGen.Create<ICallSupervisor>();
                        proxy.Url = $"http://{robotIp}:20003/RPC2";
                        string remotePath = "/fruser/" + fileToRun;
                        int lr = proxy.ProgramLoad(remotePath);
                        string msg1 = $"[Run] ProgramLoad({remotePath}): {lr}";
                        Console.WriteLine(msg1);
                        logBuffer.Add(msg1);
                        if (lr == 0)
                        {
                            int rr = proxy.ProgramRun();
                            string msg2 = $"[Run] ProgramRun: {rr}";
                            Console.WriteLine(msg2);
                            logBuffer.Add(msg2);
                        }
                    }
                    catch (Exception ex)
                    {
                        string msg = "[Run] Exception: " + ex.Message;
                        Console.WriteLine(msg);
                        logBuffer.Add(msg);
                    }
                }
                else if (key == "3")
                {
                    Console.WriteLine("--- Log ---");
                    foreach (var l in logBuffer) Console.WriteLine(l);
                    Console.WriteLine("--- End log ---");
                }
            }
        }

        // If there is a Lua file in the lua_scripts folder named TakeCup.lua, attempt upload without calling Robot.RPC()
        static void TryUploadTakeCup()
        {
            try
            {
                string exeFolder = AppDomain.CurrentDomain.BaseDirectory;
                string luaFolder = Path.Combine(exeFolder, "lua_scripts");
                string luaFile = Path.Combine(luaFolder, "TakeCup.lua");
                if (File.Exists(luaFile))
                {
                    Console.WriteLine($"Found Lua file: {luaFile}. Attempting upload via XML-RPC + raw TCP file-transfer...");
                    string robotIp = "192.168.58.2";
                    int err = UploadLuaFile(robotIp, luaFile);
                    Console.WriteLine($"UploadLuaFile returned: {err}");
                }
                else
                {
                    Console.WriteLine("No TakeCup.lua found in lua_scripts folder.");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("Exception during TryUploadTakeCup:");
                PrintExceptionDetails(ex);
            }
        }

        static void PrintExceptionDetails(Exception ex)
        {
            if (ex == null) return;
            Console.WriteLine("Exception: " + ex.GetType().FullName);
            Console.WriteLine("Message: " + ex.Message);
            Console.WriteLine("StackTrace: " + ex.StackTrace);
            if (ex.InnerException != null)
            {
                Console.WriteLine("--- Inner Exception ---");
                PrintExceptionDetails(ex.InnerException);
            }
        }

        static string GetRobotErrorName(int code)
        {
            try
            {
                // Use RobotError enum defined in RobotTypes.cs
                Type t = typeof(fairino.Robot).Assembly.GetType("fairino.RobotTypes");
                // Fallback: try RobotError enum type directly
                Type enumType = typeof(fairino.Robot).Assembly.GetType("fairino.RobotError");
                if (enumType == null)
                {
                    // search for RobotError in assembly
                    foreach (Type ty in typeof(fairino.Robot).Assembly.GetTypes())
                    {
                        if (ty.Name == "RobotError")
                        {
                            enumType = ty;
                            break;
                        }
                    }
                }
                if (enumType != null && enumType.IsEnum)
                {
                    if (Enum.IsDefined(enumType, code))
                    {
                        object val = Enum.ToObject(enumType, code);
                        return val.ToString();
                    }
                }
            }
            catch { }
            return "UNKNOWN_ERROR";
        }

        static void ProbePorts(string ip, int[] ports)
        {
            Console.WriteLine("--- Port probe ---");
            foreach (int p in ports)
            {
                Console.WriteLine($"Probing {ip}:{p} ...");
                bool tcpOpen = TcpConnectTest(ip, p, 1000);
                Console.WriteLine($" TCP connect: {(tcpOpen ? "open" : "closed/filtered")}");
                    if (tcpOpen)
                    {
                        // If it's the XML-RPC port, try a simple XML-RPC RPC() call to see server response
                        try
                        {
                            ICallSupervisor proxy = XmlRpcProxyGen.Create<ICallSupervisor>();
                            proxy.Url = $"http://{ip}:{p}/RPC2";
                            int r = proxy.RPC(ip);
                            Console.WriteLine($" XML-RPC call returned: {r}");
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($" XML-RPC probe exception on port {p}:");
                            PrintExceptionDetails(ex);
                        }
                    }
            }
            Console.WriteLine("--- End probe ---");
        }

        static bool TcpConnectTest(string ip, int port, int timeoutMs)
        {
            try
            {
                using (var client = new System.Net.Sockets.TcpClient())
                {
                    var ar = client.BeginConnect(ip, port, null, null);
                    var wh = ar.AsyncWaitHandle;
                    try
                    {
                        if (!ar.AsyncWaitHandle.WaitOne(TimeSpan.FromMilliseconds(timeoutMs), false))
                        {
                            return false;
                        }
                        client.EndConnect(ar);
                        return true;
                    }
                    finally
                    {
                        wh.Close();
                    }
                }
            }
            catch
            {
                return false;
            }
        }

        static string PostActionGet(string ip, string jsonBody, string cookie, int timeoutMs)
        {
            string url = $"http://{ip}/action/get";
            using (var handler = new System.Net.Http.HttpClientHandler())
            {
                handler.AllowAutoRedirect = true;
                using (var client = new System.Net.Http.HttpClient(handler))
                {
                    client.Timeout = TimeSpan.FromMilliseconds(timeoutMs);
                    var req = new System.Net.Http.HttpRequestMessage(System.Net.Http.HttpMethod.Post, url);
                    req.Content = new System.Net.Http.StringContent(jsonBody, System.Text.Encoding.UTF8, "application/json");
                    if (!string.IsNullOrEmpty(cookie))
                    {
                        req.Headers.Add("Cookie", cookie);
                    }
                    req.Headers.Add("Accept", "application/json, text/plain, */*");
                    var resp = client.SendAsync(req).Result;
                    resp.EnsureSuccessStatusCode();
                    return resp.Content.ReadAsStringAsync().Result;
                }
            }
        }

        static int UploadLuaFile(string ip, string localLuaPath)
        {
            try
            {
                if (!File.Exists(localLuaPath))
                {
                    Console.WriteLine("Lua file not found: " + localLuaPath);
                    return -1;
                }

                // create XmlRpc proxy and call FileUpload(fileType=0, fileName)
                ICallSupervisor proxy = XmlRpcProxyGen.Create<ICallSupervisor>();
                proxy.Url = $"http://{ip}:20003/RPC2";

                string fileName = Path.GetFileName(localLuaPath);
                Console.WriteLine($"Calling FileUpload for {fileName}...");
                int r = proxy.FileUpload(0, fileName);
                Console.WriteLine($"FileUpload RPC returned: {r}");
                if (r != 0)
                {
                    return r;
                }

                // open TCP to port 20010 and send framed file
                IPAddress ipAddr = IPAddress.Parse(ip);
                IPEndPoint ep = new IPEndPoint(ipAddr, 20010);
                using (Socket client = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp))
                {
                    var ar = client.BeginConnect(ep, null, null);
                    ar.AsyncWaitHandle.WaitOne(2000, true);
                    if (!ar.IsCompleted)
                    {
                        client.Close();
                        Console.WriteLine("TCP connect to 20010 failed");
                        return -1; // ERR_OTHER
                    }

                    client.ReceiveTimeout = 10000;
                    client.SendTimeout = 2000;

                    string sendMd5 = GetFileMD5(localLuaPath).ToLower();
                    int totalSize = GetFileSize(localLuaPath) + 4 + 46; // follow SDK's calculation
                    string header = "/f/b" + totalSize.ToString("D10") + sendMd5;
                    int sent = client.Send(System.Text.Encoding.Default.GetBytes(header));
                    if (sent < 1)
                    {
                        Console.WriteLine("Failed to send header");
                        return -1;
                    }

                    using (FileStream fs = new FileStream(localLuaPath, FileMode.Open, FileAccess.Read))
                    {
                        byte[] buf = new byte[2 * 1024 * 1024];
                        int read = 0;
                        while ((read = fs.Read(buf, 0, buf.Length)) > 0)
                        {
                            int s = client.Send(buf, read, SocketFlags.None);
                                if (s < 1)
                                {
                                    Console.WriteLine("Failed to send file chunk");
                                    return -1;
                                }
                        }
                    }

                    sent = client.Send(System.Text.Encoding.Default.GetBytes("/b/f"));
                    if (sent < 1)
                    {
                        Console.WriteLine("Failed to send footer");
                        return -1;
                    }

                    byte[] resultBuf = new byte[1024];
                    int num = client.Receive(resultBuf);
                    if (num < 1)
                    {
                        Console.WriteLine("No response after upload");
                        return -1;
                    }
                    string resp = System.Text.Encoding.UTF8.GetString(resultBuf, 0, num);
                    Console.WriteLine("Upload response: " + resp);
                    if (!resp.StartsWith("SUCCESS"))
                    {
                        return -1;
                    }
                }

                // call LuaUpLoadUpdate to finalize
                object[] rr = proxy.LuaUpLoadUpdate(fileName);
                Console.WriteLine($"LuaUpLoadUpdate returned: {(int)rr[0]}, message: {rr[1]}");
                return (int)rr[0];
            }
            catch (Exception ex)
            {
                Console.WriteLine("Exception during UploadLuaFile:");
                PrintExceptionDetails(ex);
                return -1;
            }
        }

        static string GetFileMD5(string path)
        {
            using (var fs = File.OpenRead(path))
            using (var md5 = MD5.Create())
            {
                byte[] hash = md5.ComputeHash(fs);
                return BitConverter.ToString(hash).Replace("-", "").ToLower();
            }
        }

        static int GetFileSize(string path)
        {
            var fi = new FileInfo(path);
            return (int)fi.Length;
        }
    }
}
