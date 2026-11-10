#!/usr/bin/env python3
# "Go nuts" LED + beeper showcase for the Ford VCM II. Runtime-only, reversible.
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM

v = VCM()
def run(c, show=True, **k):
    o, rc = v.run(c, overall=120, idle=30, **k)
    if show:
        head = c.strip().splitlines()[0][:66]
        print(f"[rc={rc}] {head}")
        if o.strip(): print("   ", o.strip().replace("\n","\n    "))
    return o, rc

# ---------- 0. RECON: cleaner interfaces? ----------
print("\n===== RECON =====")
run("ls -la /dev/etas* 2>&1; echo '--- /proc/devices etas ---'; grep -i etas /proc/devices 2>/dev/null; "
    "echo '--- sysfs classes ---'; ls /sys/class/ 2>/dev/null; "
    "echo '--- speaker/led sysfs ---'; find /sys -iname '*speak*' -o -iname '*beep*' 2>/dev/null | head")

# ---------- setup ----------
run("[ -x /tmp/vcimod/setled ] || { mkdir -p /tmp/vcimod; cp /mnt/sd/apps/vci-diags/hwtest-scripts/setled /mnt/sd/apps/vci-diags/hwtest-scripts/memdump.so /tmp/vcimod/; chmod +x /tmp/vcimod/setled; }; "
    "cd /tmp/vcimod && enable -f ./memdump.so mem dump; ./setled 0; mem -a 0x40e0002c 0x3f0; echo ready", show=True)

B_ON  = "mem -a 0x10000048 0x0c0d"
B_OFF = "mem -a 0x10000048 0x0000"
EN    = "mem -a 0x40e0002c 0x3f0"

# ---------- 1. BOOT CHIME (3 ascending notes, screen flash) ----------
print("\n===== 1. chime =====")
run("cd /tmp/vcimod && " + EN + "; "
    "for vv in 0x0c32 0x0c28 0x0c19; do mem -a 0x40e00020 0x3f0; mem -a 0x10000048 $vv; usleep 170000; "
    "mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep 55000; done")

# ---------- 2. LARSON SCANNER (KITT) ----------
print("\n===== 2. larson scanner =====")
run("cd /tmp/vcimod && for n in 1 2 3 4; do "
    "for p in '1 0 0 0 0' '0 1 0 0 0' '0 0 1 0 0' '0 0 0 1 0' '0 0 0 0 1' '0 0 0 1 0' '0 0 1 0 0' '0 1 0 0 0'; do "
    "./setled $p; usleep 50000; done; done; ./setled 0")

# ---------- 3. POLICE LIGHTS + WHOOP SIREN ----------
print("\n===== 3. police + whoop =====")
run("cd /tmp/vcimod && " + EN + "; for n in 1 2 3; do "
    "d=5;  while [ $d -le 64 ]; do mem -a 0x10000048 $(printf 0x0c%02x $d); mem -a 0x40e00020 0x020; usleep 11000; d=$((d+3)); done; "
    "d=64; while [ $d -ge 5 ];  do mem -a 0x10000048 $(printf 0x0c%02x $d); mem -a 0x40e00020 0x300; usleep 11000; d=$((d-3)); done; "
    "done; mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000")

# ---------- 4. R2-D2 DROID CHATTER (random pitch + colour) ----------
print("\n===== 4. droid chatter =====")
run("cd /tmp/vcimod && " + EN + "; i=0; while [ $i -lt 22 ]; do "
    "vv=$(( (RANDOM % 70) + 6 )); "
    "c=$(( RANDOM % 6 )); case $c in 0)col=0x020;;1)col=0x300;;2)col=0x0d0;;3)col=0x350;;4)col=0x100;;5)col=0x010;;esac; "
    "mem -a 0x40e00020 $col; mem -a 0x10000048 $(printf 0x0c%02x $vv); "
    "usleep $(( (RANDOM % 110000) + 25000 )); mem -a 0x10000048 0x0000; usleep $(( (RANDOM % 50000) + 15000 )); "
    "i=$((i+1)); done; mem -a 0x40e00020 0x000")

# ---------- 5. BINARY COUNTER 0..15 ----------
print("\n===== 5. binary counter 0..15 =====")
run("cd /tmp/vcimod && n=0; while [ $n -le 15 ]; do "
    "./setled $((n/8%2)) $((n/4%2)) $((n/2%2)) $((n%2)) 0; "
    "mem -a 0x10000048 0x0c2a; usleep 45000; mem -a 0x10000048 0x0000; usleep 230000; "
    "n=$((n+1)); done; ./setled 0")

v.close()
print("\n(part 1 done)")
