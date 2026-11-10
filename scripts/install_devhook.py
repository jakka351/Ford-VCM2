#!/usr/bin/env python3
import sys, time, socket, hashlib
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM, HOST

LOCAL = r"C:/Users/admin/Desktop/Ford-VCM2/mods/dev_hook.sh"
REMOTE = "/etc/vci/config/dev_hook.sh"

# read file, normalize to LF
data = open(LOCAL, "rb").read().replace(b"\r\n", b"\n")
local_md5 = hashlib.md5(data).hexdigest()
print(f"local bytes={len(data)} md5={local_md5}")

def run(c, **k):
    o, rc = v.run(c, **k); print(f"$ {c}\n{o}  [rc={rc}]"); return o, rc

v = VCM()

# 0) does one already exist?
run(f"if [ -e {REMOTE} ]; then echo EXISTS; md5sum {REMOTE}; else echo none; fi")

# 1) push bytes: device listens, writes stdin to the file
v.tn.write(f"nc -l -p 9300 > {REMOTE}\n".encode())
time.sleep(1.0)
s = None
for _ in range(40):
    try:
        s = socket.create_connection((HOST, 9300), timeout=3); break
    except OSError:
        time.sleep(0.25)
if s is None:
    raise SystemExit("could not connect to device receiver :9300")
s.sendall(data)
s.shutdown(socket.SHUT_WR)
time.sleep(0.5)
s.close()
v._drain(1.2)

# 2) perms + flush jffs2
run(f"chmod +x {REMOTE}; sync; echo set=$?")

# 3) verify round-trip
o, _ = run(f"wc -c {REMOTE}; md5sum {REMOTE}")
dev_md5 = ""
for tok in o.replace("\n", " ").split():
    if len(tok) == 32 and all(c in "0123456789abcdef" for c in tok):
        dev_md5 = tok; break
print(f"\n==> md5 match: {dev_md5 == local_md5}  (device={dev_md5} local={local_md5})")

# 4) show it back
run(f"echo '----- installed dev_hook.sh -----'; cat {REMOTE}; echo '----- end -----'; ls -l {REMOTE}", overall=30)

# 5) prove it works now (runs show in background, returns immediately)
print("\n### executing hook once (show runs in background ~6s) ###")
run(f"{REMOTE}; echo ran=$?")
time.sleep(7)
# confirm beeper + colour registers were released
run("cd /tmp/vcimod && enable -f ./memdump.so mem dump 2>/dev/null; echo 'beeper reg:'; dump -b 0x10000048 -l 2 -2 2>/dev/null; echo 'colour reg:'; dump -b 0x40e00020 -l 2 -2 2>/dev/null")

v.close()
print("\nINSTALL DONE")
