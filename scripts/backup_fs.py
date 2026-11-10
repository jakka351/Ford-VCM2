#!/usr/bin/env python3
import sys, os, time, socket, io, tarfile, hashlib
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM, HOST

OUT = r"C:/Users/admin/Desktop/Ford-VCM2/backups/2026-11-07/fs"
os.makedirs(OUT, exist_ok=True)

def pull_port(port, overall=1200, idle=40):
    data = bytearray()
    s = None
    deadline = time.time() + 20
    while time.time() < deadline and s is None:
        try:
            s = socket.create_connection((HOST, port), timeout=3)
        except OSError:
            time.sleep(0.3)
    if s is None:
        raise RuntimeError(f"could not connect to listener :{port}")
    s.settimeout(idle)
    last = time.time(); start = time.time()
    try:
        while True:
            if time.time() - start > overall:
                break
            try:
                chunk = s.recv(262144)
            except socket.timeout:
                if time.time() - last > idle:
                    break
                continue
            if not chunk:
                break
            data += chunk
            last = time.time()
    finally:
        s.close()
    return bytes(data)

# label -> (producer tar cmd, device sanity-count cmd)
JOBS = [
 ("rootfs.tar.gz",
  "tar -czf - -C / bin build etc lib libexec sbin usr public web var loadsdrc linuxrc oldroot lost+found .bash_history 2>/dev/null",
  "find /bin /build /etc /lib /libexec /sbin /usr /public /web /var /oldroot 2>/dev/null | wc -l"),
 ("sd-p1-mnt-sd.tar.gz",
  "tar -czf - -C /mnt/sd . 2>/dev/null",
  "find /mnt/sd 2>/dev/null | wc -l"),
]

v = VCM()
report = []
port = 9200
for label, producer, countcmd in JOBS:
    devcount, _ = v.run(countcmd, overall=120, idle=15)
    devcount = devcount.strip().split()[-1] if devcount.strip() else "?"
    print(f"[{label}] device entry count ~ {devcount} ; transferring...")
    v.tn.write(f"{producer} | nc -l -p {port} -w 40\n".encode())
    time.sleep(1.2)
    blob = pull_port(port, overall=1800, idle=40)
    path = os.path.join(OUT, label)
    with open(path, "wb") as f:
        f.write(blob)
    md5 = hashlib.md5(blob).hexdigest()
    # integrity: can we open & list it?
    members = 0; totsz = 0; err = ""
    try:
        tf = tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz")
        for m in tf:
            members += 1
            totsz += m.size
        tf.close()
    except Exception as e:
        err = repr(e)
    ok = (err == "" and members > 0)
    print(f"  saved {len(blob):,} B  md5={md5}  members={members}  uncompressed~{totsz:,} B  dev~{devcount}  {'OK' if ok else 'ERR '+err}")
    report.append((label, len(blob), md5, members, totsz, devcount, ok, err))
    v._drain(1.0)
    port += 1

v.close()

with open(os.path.join(OUT, "FS-MANIFEST.txt"), "w", encoding="utf-8") as f:
    f.write("file\tgz_bytes\tmd5\ttar_members\tuncompressed_bytes\tdevice_find_count\tok\terror\n")
    for r in report:
        f.write("\t".join(str(x) for x in r) + "\n")
print("\nDONE")
