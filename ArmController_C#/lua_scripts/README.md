Drop your Lua script(s) here to have them uploaded to the robot.

Workflow:
1. Place your .lua file in this folder.
2. Name it with a simple ASCII filename (no spaces) like `my_script.lua`.
3. When you're ready, tell me the filename and I will implement/upload it from `My_Arm` using the SDK file-transfer routine (or using the raw TCP file-transfer protocol if needed).

Notes:
- The SDK expects a specific file-transfer framing on ports 20010/20011 (header `/f/b`, padded length, MD5 digest, footer `/b/f`).
- Uploading will likely require the robot to accept file writes; if authentication is required we will need credentials or a logged-in session.

Example:
- `example.lua` is included as a small test script.
