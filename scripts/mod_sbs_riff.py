#!/usr/bin/env python3
# SBS intro guitar riff, from the user's number notation "432 3 232 030 3 030 3"
# (D-major scale degrees; 0 = low D drone). Staccato, looped. Runtime-only.
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM

def val(freq):
    div = max(6, min(255, round(26000.0/freq)))
    return 0x0c00 | div

DEG = {  # D major
 '1':293.66,'2':329.63,'3':369.99,'4':392.00,'5':440.00,'6':493.88,'7':554.37,
 '0':293.66,                    # open D drone
}
def warm(f):
    if f < 330: return 0x020     # deep red (drone/low)
    if f < 390: return 0x370     # red+amber
    return 0x350                 # amber

SEQ = "432 3 232 030 3 030 3"
E = 150000                       # eighth-note (us)
ON, GAP = int(E*0.68), E-int(E*0.68)

def build_once():
    out = []
    first = True
    for ch in SEQ:
        if ch == ' ':
            out.append(f"mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep {E//2}")   # phrase gap
            continue
        if ch not in DEG:
            continue
        f = DEG[ch]
        col = 0x3f0 if first else warm(f)     # flash all on the downbeat of each loop
        first = False
        out.append(f"mem -a 0x40e00020 {hex(col)}; mem -a 0x10000048 {hex(val(f))}; usleep {ON}; "
                   f"mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep {GAP}")
    return out

cmds = []
for _ in range(4):               # loop the riff 4x
    cmds += build_once()
    cmds.append(f"usleep {E}")    # breath between loops

v = VCM()
o,rc = v.run("[ -x /tmp/vcimod/memdump.so ] || { mkdir -p /tmp/vcimod; cp /mnt/sd/apps/vci-diags/hwtest-scripts/memdump.so /tmp/vcimod/; }; "
             "cd /tmp/vcimod && enable -f ./memdump.so mem dump; mem -a 0x40e0002c 0x3f0; echo ready", overall=30)
print(o, rc)
print("riff events:", len(cmds))
o,rc = v.run("cd /tmp/vcimod && mem -a 0x40e0002c 0x3f0; " + " ; ".join(cmds) +
             "; mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; echo done=$?", overall=120, idle=40)
print(o, "[rc=%s]" % rc)
v.close()
