#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM

v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k)
    print(f"[rc={rc}] {c.splitlines()[0][:70]}...")
    if o.strip():
        print("   ", o.strip().replace("\n", "\n    "))
    return o, rc

# ensure tools staged (tmpfs survives within this boot); re-enable builtins this session
run("[ -x /tmp/vcimod/setled ] || { mkdir -p /tmp/vcimod; cp /mnt/sd/apps/vci-diags/hwtest-scripts/setled /mnt/sd/apps/vci-diags/hwtest-scripts/memdump.so /tmp/vcimod/; chmod +x /tmp/vcimod/setled; }; "
    "cd /tmp/vcimod && enable -f ./memdump.so mem dump; type -t mem dump; ./setled 0; mem -a 0x40e0002c 0x3f0; echo setup=$?")

# --- PHASE 0: slow color check (red / yellow / green, 1s each) ---
run("cd /tmp/vcimod && "
    "mem -a 0x40e00020 0x020; sleep 1; "   # RED (error)
    "mem -a 0x40e00020 0x300; sleep 1; "   # YELLOW (both duals)
    "mem -a 0x40e00020 0x0d0; sleep 1; "   # GREEN (power+pc+veh)
    "mem -a 0x40e00020 0x000; echo check=$?", overall=20)

# --- PHASE 1: RAINBOW FADE (warm spectrum up & down) x3 ---
run("cd /tmp/vcimod && mem -a 0x40e0002c 0x3f0; "
    "for n in 1 2 3; do for c in 0x020 0x370 0x350 0x340 0x300 0x3d0 0x0d0 0x3d0 0x300 0x340 0x350 0x370; do "
    "mem -a 0x40e00020 $c; usleep 100000; done; done; mem -a 0x40e00020 0x000; echo fade=$?", overall=60)

# --- PHASE 2: ROLLING COLOR COMET (per-LED native colors) x5 ---
run("cd /tmp/vcimod && mem -a 0x40e0002c 0x3f0; "
    "for n in 1 2 3 4 5; do for c in 0x080 0x040 0x100 0x020 0x200 0x010 0x200 0x020 0x100 0x040; do "
    "mem -a 0x40e00020 $c; usleep 65000; done; done; mem -a 0x40e00020 0x000; echo comet=$?", overall=60)

# --- PHASE 3: SIREN sweep (vary beeper low-byte divisor) + color follow ---
run("cd /tmp/vcimod && mem -a 0x40e0002c 0x3f0; "
    "for n in 1 2 3; do "
    "  for d in 6 10 16 24 40 64 40 24 16 10; do "
    "    mem -a 0x10000048 $(printf 0x0c%02x $d); "
    "    case $d in 6) col=0x020;; 10) col=0x370;; 16) col=0x350;; 24) col=0x300;; 40) col=0x3d0;; 64) col=0x0d0;; *) col=0x300;; esac; "
    "    mem -a 0x40e00020 $col; usleep 90000; done; "
    "done; mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; echo siren=$?", overall=60)

# --- PHASE 4: FINALE: rainbow strobe + triple beep ---
run("cd /tmp/vcimod && mem -a 0x40e0002c 0x3f0; "
    "for c in 0x020 0x300 0x0d0 0x3f0 0x020 0x300 0x0d0 0x3f0; do mem -a 0x40e00020 $c; usleep 70000; mem -a 0x40e00020 0x000; usleep 40000; done; "
    "for b in 1 2 3; do mem -a 0x40e00020 0x3f0; mem -a 0x10000048 0x0c0d; usleep 130000; mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep 80000; done; echo finale=$?", overall=40)

# --- CLEANUP ---
run("cd /tmp/vcimod && mem -a 0x40e00020 0x000; mem -a 0x10000048 0x0000; ./setled 0; echo cleaned=$?")
v.close()
print("\nRAINBOW DONE")
