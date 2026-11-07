#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM, reachable

if not reachable():
    sys.exit("device not reachable on 192.168.171.2:23")

v = VCM()
print("=== BANNER ===")
print(v.banner.decode("utf-8", "replace"))
print("=== /BANNER ===")

for cmd in [
    "id",
    "uname -a",
    "cat /proc/version",
    "cat /proc/mtd",
    "echo SHELL=$0 BASH=$BASH_VERSION",
    'for a in busybox base64 md5sum sha256sum sha1sum gzip gunzip tar nc wget tftp ftpput dd cat od xxd uuencode openssl flashcp flash_unlock mount df fw_printenv; do p=$(command -v $a 2>/dev/null); echo "$a=${p:-NO}"; done',
]:
    out, rc = v.run(cmd, overall=40, idle=6)
    print(f"\n$ {cmd}  [rc={rc}]\n{out}")

v.close()
