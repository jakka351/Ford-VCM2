#!/usr/bin/env python3
import sys, time, socket, hashlib, gzip, io
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM, HOST

def pull_port(port, overall=30):
    data = bytearray()
    end = time.time() + overall
    s = None
    while time.time() < end and s is None:
        try:
            s = socket.create_connection((HOST, port), timeout=3)
        except OSError:
            time.sleep(0.25)
    if s is None:
        raise RuntimeError("could not connect to listener")
    s.settimeout(overall)
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
    finally:
        s.close()
    return bytes(data)

v = VCM()

# device network view (enumeration bonus)
for c in ["ifconfig 2>/dev/null | head -40", "df -h 2>/dev/null", "nc 2>&1 | head -20"]:
    out, rc = v.run(c, overall=30, idle=5)
    print(f"\n$ {c} [rc={rc}]\n{out}")

# --- small transfer test: serve 'HELLO_VCM' on :9000 ---
print("\n=== nc transfer test (plain) ===")
v.tn.write(b"printf 'HELLO_VCM_12345\\n' | nc -l -p 9000\n")
time.sleep(1.0)
try:
    got = pull_port(9000, overall=15)
    print("GOT:", repr(got))
except Exception as e:
    print("PLAIN TEST FAILED:", e)
v._drain(1.0)

# --- gzip transfer test: serve gzip of /proc/mtd on :9001, verify md5 ---
print("\n=== nc transfer test (gzip + md5) ===")
exp, _ = v.run("md5sum /proc/mtd | cut -d' ' -f1", overall=20, idle=5)
exp = exp.strip()
v.tn.write(b"gzip -c /proc/mtd | nc -l -p 9001\n")
time.sleep(1.0)
try:
    gz = pull_port(9001, overall=15)
    raw = gzip.GzipFile(fileobj=io.BytesIO(gz)).read()
    got_md5 = hashlib.md5(raw).hexdigest()
    print(f"device md5={exp}  local md5={got_md5}  match={exp==got_md5}")
    print("decoded bytes:", len(raw))
except Exception as e:
    print("GZIP TEST FAILED:", e)
v._drain(1.0)

v.close()
