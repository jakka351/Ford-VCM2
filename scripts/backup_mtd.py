#!/usr/bin/env python3
import sys, os, time, socket, hashlib, gzip, io
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM, HOST

OUT = r"C:/Users/admin/Desktop/Ford-VCM2/backups/2026-11-07/mtd"
os.makedirs(OUT, exist_ok=True)

# (index, name, expected_size_bytes)
MTD = [
 (0,"fsboot",262144),(1,"boot",262144),(2,"bootvars",131072),(3,"fpga",655360),
 (4,"linux2",1572864),(5,"initrd2",6291456),(6,"linux1",3145728),(7,"initrd1",19857408),
 (8,"jffs2",1048576),(9,"linuxvars1",131072),(10,"linuxvars2",131072),
 (11,"serialnum",32768),(12,"macaddress",32768),
]

def pull_port(port, overall=600, idle=30):
    data = bytearray()
    s = None
    deadline = time.time() + 15
    while time.time() < deadline and s is None:
        try:
            s = socket.create_connection((HOST, port), timeout=3)
        except OSError:
            time.sleep(0.25)
    if s is None:
        raise RuntimeError(f"could not connect to listener :{port}")
    s.settimeout(idle)
    last = time.time()
    try:
        while True:
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

v = VCM()
manifest = []
port = 9100
print(f"{'part':14s} {'exp':>9s} {'got':>9s} {'devmd5':32s} {'locmd5':32s}  OK")
for idx, name, exp in MTD:
    dev = f"/dev/mtd{idx}"
    # expected device md5 of the RAW partition
    dmd5, _ = v.run(f"md5sum {dev} | cut -d' ' -f1", overall=60, idle=10)
    dmd5 = dmd5.strip().split()[-1] if dmd5.strip() else ""
    # serve gzip of the raw partition
    v.tn.write(f"dd if={dev} bs=65536 2>/dev/null | gzip -c | nc -l -p {port} -w 30\n".encode())
    time.sleep(1.0)
    gz = pull_port(port, overall=600, idle=30)
    raw = gzip.GzipFile(fileobj=io.BytesIO(gz)).read()
    lmd5 = hashlib.md5(raw).hexdigest()
    fn = os.path.join(OUT, f"mtd{idx:02d}-{name}.bin")
    with open(fn, "wb") as f:
        f.write(raw)
    ok = (lmd5 == dmd5) and (len(raw) == exp)
    print(f"mtd{idx:02d}-{name:10s} {exp:9d} {len(raw):9d} {dmd5:32s} {lmd5:32s}  {'YES' if ok else 'NO!'}")
    manifest.append((f"mtd{idx:02d}-{name}.bin", idx, name, exp, len(raw), dmd5, lmd5, ok))
    v._drain(0.8)
    port += 1

v.close()

# write checksum/manifest
with open(os.path.join(OUT, "MTD-CHECKSUMS.txt"), "w", encoding="utf-8") as f:
    f.write("file\tmtd\tname\texp_size\tgot_size\tdevice_md5\tlocal_md5\tverified\n")
    for row in manifest:
        f.write("\t".join(str(x) for x in row) + "\n")

bad = [m for m in manifest if not m[-1]]
print("\nALL VERIFIED" if not bad else f"\n!!! {len(bad)} MISMATCH: {[m[0] for m in bad]}")
