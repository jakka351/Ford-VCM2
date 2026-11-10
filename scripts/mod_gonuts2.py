#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM
v = VCM()
def run(c, **k):
    o, rc = v.run(c, overall=120, idle=30, **k)
    print(f"[rc={rc}] {c.strip().splitlines()[0][:60]}")
    if o.strip(): print("   ", o.strip())
    return o, rc

run("[ -x /tmp/vcimod/setled ] || { mkdir -p /tmp/vcimod; cp /mnt/sd/apps/vci-diags/hwtest-scripts/setled /mnt/sd/apps/vci-diags/hwtest-scripts/memdump.so /tmp/vcimod/; chmod +x /tmp/vcimod/setled; }; "
    "cd /tmp/vcimod && enable -f ./memdump.so mem dump; mem -a 0x40e0002c 0x3f0; echo ready")

# ---------- 6. MORSE: "JAKKA" on beeper + red LED ----------
MORSE = {'J':'.---','A':'.-','K':'-.-'}
U = 110000
parts = []
for letter in "JAKKA":
    for sym in MORSE[letter]:
        on = U if sym == '.' else U*3
        parts.append(f"mem -a 0x40e00020 0x020; mem -a 0x10000048 0x0c2a; usleep {on}; "
                     f"mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep {U}")
    parts.append(f"usleep {U*2}")   # letter gap
print("\n===== 6. morse 'JAKKA' =====")
run("cd /tmp/vcimod && mem -a 0x40e0002c 0x3f0; " + " ; ".join(parts))

# ---------- 7. MUSICAL SCALE (pitch-encoding experiment) ----------
# hypothesis: value 0x0c00 | div, freq ~= 26000/div  -> ascending = decreasing div
notes_up = [0x0c32,0x0c2c,0x0c27,0x0c25,0x0c21,0x0c1e,0x0c1a,0x0c19]   # C D E F G A B C
cols     = [0x020,0x370,0x350,0x300,0x3d0,0x0d0,0x010,0x3f0]
seq = []
for val,col in zip(notes_up, cols):
    seq.append(f"mem -a 0x40e00020 {hex(col)}; mem -a 0x10000048 {hex(val)}; usleep 280000; mem -a 0x10000048 0x0000; usleep 40000")
for val,col in zip(reversed(notes_up), reversed(cols)):   # back down
    seq.append(f"mem -a 0x40e00020 {hex(col)}; mem -a 0x10000048 {hex(val)}; usleep 200000; mem -a 0x10000048 0x0000; usleep 30000")
print("\n===== 7. musical scale (up then down) =====")
run("cd /tmp/vcimod && mem -a 0x40e0002c 0x3f0; " + " ; ".join(seq) + "; mem -a 0x40e00020 0x000")

# ---------- 8. GRAND FINALE: rainbow fade + triple chime ----------
print("\n===== 8. finale =====")
run("cd /tmp/vcimod && mem -a 0x40e0002c 0x3f0; "
    "for n in 1 2 3; do for c in 0x020 0x370 0x350 0x300 0x3d0 0x0d0 0x3d0 0x300 0x350 0x370; do mem -a 0x40e00020 $c; usleep 55000; done; done; "
    "for vv in 0x0c19 0x0c19 0x0c19; do mem -a 0x40e00020 0x3f0; mem -a 0x10000048 $vv; usleep 150000; mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep 90000; done")

# ---------- cleanup ----------
run("cd /tmp/vcimod && mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; ./setled 0; echo cleaned=$?")
v.close()
print("\nSHOW COMPLETE")
