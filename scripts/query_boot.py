#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM
v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k); print(f"\n$ {c}\n{o}  [rc={rc}]"); return o, rc

run("mount")
run("ls -l /usr/local/bin/init_script.sh /usr/local/bin/init_script_helper.sh /usr/local/bin/init_script_testmode.sh 2>&1")
run("readlink /mnt/sd ; readlink /usr/local ; echo '--- is /usr/local a mount? ---'; mount | grep -E 'usr/local|mmcblk'")
run("echo '=== where is boot.sh invoked? ==='; grep -rn 'boot.sh\\|app-components\\|app_components' /usr/local/bin/*.sh 2>/dev/null | head -40")
run("echo '=== head init_script.sh ==='; head -50 /usr/local/bin/init_script.sh 2>&1")
run("echo '=== SD writable test dir (no write yet) ==='; ls -ld /mnt/sd /mnt/sd/app-components 2>&1; echo 'free:'; df -h /mnt/sd | tail -1")
run("echo '=== does anything source app-components boot.sh ? grep whole rootfs bins ==='; grep -rln 'app-components' /usr/local /sbin /bin /etc 2>/dev/null | head")
v.close()
