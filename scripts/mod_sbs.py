#!/usr/bin/env python3
# "Sunday Bloody Sunday" (U2) - monophonic beeper cover on the VCM II.
# Runtime only (beeper reg 0x10000048 + LED colour 0x40e00020). Reversible.
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM

# --- pitch model: beeper value = 0x0c00 | round(26000/freq) (low byte = divisor) ---
def val(freq):
    div = max(6, min(255, round(26000.0/freq)))
    return 0x0c00 | div

F = {  # D-major-ish set
 "D4":293.66,"E4":329.63,"Fs4":369.99,"G4":392.00,"A4":440.00,"B4":493.88,
 "Cs5":554.37,"D5":587.33,"E5":659.25,"Fs5":739.99,"G5":783.99,"A5":880.00,"R":0
}
def warm(freq):  # warm colour by pitch (reds/ambers, the 'bloody' theme)
    if freq == 0: return 0x000
    if freq < 360: return 0x020          # deep red
    if freq < 470: return 0x370          # red+amber
    if freq < 600: return 0x350          # amber
    return 0x300                          # yellow

Q = 300000      # quarter note (us)
def dur(beats): return int(Q*beats)

# (note, beats) - best-effort evocation of the hook + verse contour
INTRO = [("D4",0.5)]*6                                   # martial drum-ish pulse
MELODY = [
 ("A4",0.5),("A4",0.5),("B4",0.5),("A4",0.5),("Fs4",1.0),("R",0.5),   # Sun-day bloo-dy Sun-day
 ("A4",0.5),("A4",0.5),("B4",0.5),("A4",0.5),("D5",1.0),("R",0.5),    # Sun-day bloo-dy Sun-day
 ("D5",0.5),("Cs5",0.5),("B4",0.5),("A4",0.5),("B4",0.5),("A4",0.5),("Fs4",1.0),("R",0.5),
 ("A4",0.5),("B4",0.5),("D5",0.5),("Cs5",0.5),("B4",1.0),("A4",1.0),("R",0.5),
]
SONG = INTRO + MELODY

cmds = []
for name, beats in SONG:
    f = F[name]
    total = dur(beats)
    if f == 0:
        cmds.append(f"mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep {total}")
    else:
        on = int(total*0.82); gap = total-on
        cmds.append(f"mem -a 0x40e00020 {hex(warm(f))}; mem -a 0x10000048 {hex(val(f))}; usleep {on}; "
                    f"mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep {gap}")

v = VCM()
o,rc = v.run("[ -x /tmp/vcimod/setled ] || { mkdir -p /tmp/vcimod; cp /mnt/sd/apps/vci-diags/hwtest-scripts/memdump.so /tmp/vcimod/; }; "
             "cd /tmp/vcimod && enable -f ./memdump.so mem dump; mem -a 0x40e0002c 0x3f0; echo ready", overall=30)
print(o, rc)
print("playing Sunday Bloody Sunday ...  (%d events)" % len(cmds))
o,rc = v.run("cd /tmp/vcimod && mem -a 0x40e0002c 0x3f0; " + " ; ".join(cmds) +
             "; mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; echo done=$?",
             overall=120, idle=40)
print(o, "[rc=%s]" % rc)
v.close()
