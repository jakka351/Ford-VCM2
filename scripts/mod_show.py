#!/usr/bin/env python3
import sys, time
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM

v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k)
    print(f"$ {c}\n{o}  [rc={rc}]")
    return o, rc

# ---- recon: find the factory tools ----
run("ls -la /mnt/sd/apps/vci-diags/hwtest-scripts/setled /mnt/sd/apps/vci-diags/hwtest-scripts/memdump.so 2>/dev/null; "
    "ls -la /etc/vci/config/diagnostics/hwtest-scripts/memdump.so 2>/dev/null; "
    "grep -E 'mnt/sd' /proc/mounts")

# ---- stage into tmpfs (RAM, exec-ok, gone on reboot) ----
run("mkdir -p /tmp/vcimod && "
    "cp /mnt/sd/apps/vci-diags/hwtest-scripts/setled /tmp/vcimod/ && "
    "cp /mnt/sd/apps/vci-diags/hwtest-scripts/memdump.so /tmp/vcimod/ && "
    "chmod +x /tmp/vcimod/setled && ls -la /tmp/vcimod/")

# ---- verify setled executes (all off) ----
o, rc = run("cd /tmp/vcimod && ./setled 0 ; echo rc=$?")
setled_ok = "rc=0" in o

# ---- enable the mem builtin + one tiny beeper blip to verify ----
run("cd /tmp/vcimod && enable -f ./memdump.so mem dump 2>&1; type -t mem")
run("cd /tmp/vcimod && mem -a 0x10000048 0x0c0d ; usleep 120000 ; mem -a 0x10000048 0x0000 ; echo beeptest=$?")

print("\n=== setled_ok:", setled_ok, "===")

if setled_ok:
    # ---- identify the 5 LEDs one at a time ----
    print("\n--- LED identification sweep ---")
    for i in range(5):
        pat = ["0","0","0","0","0"]; pat[i] = "1"
        run(f"cd /tmp/vcimod && ./setled {' '.join(pat)} ; sleep 1 ; ./setled 0")

    # ---- Knight-Rider sweep x3 ----
    print("\n--- sweep ---")
    run("cd /tmp/vcimod && for n in 1 2 3; do "
        "for p in '1 0 0 0 0' '0 1 0 0 0' '0 0 1 0 0' '0 0 0 1 0' '0 0 0 0 1' '0 0 0 1 0' '0 0 1 0 0' '0 1 0 0 0'; do "
        "./setled $p; usleep 90000; done; done; ./setled 0", overall=60)

    # ---- grand finale: all blink x4 with a beep each ----
    print("\n--- finale: blink + beep x4 ---")
    run("cd /tmp/vcimod && enable -f ./memdump.so mem dump; "
        "for n in 1 2 3 4; do "
        "./setled 1 1 1 1 1; mem -a 0x10000048 0x0c0d; usleep 160000; "
        "mem -a 0x10000048 0x0000; ./setled 0; usleep 200000; done; ./setled 0", overall=60)

# ---- cleanup: LEDs off, beeper off ----
run("cd /tmp/vcimod && ./setled 0 2>/dev/null; enable -f ./memdump.so mem dump 2>/dev/null; mem -a 0x10000048 0x0000 2>/dev/null; echo cleaned=$?")
v.close()
print("\nDONE")
