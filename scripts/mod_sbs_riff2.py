#!/usr/bin/env python3
# SBS intro riff via a COMPACT device-side loop (avoids the long-command-line limit).
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM
v = VCM()
def run(c, **k):
    o, rc = v.run(c, overall=120, idle=40, **k); print(f"[rc={rc}] {o.strip()[-60:]}"); return o, rc

# 1) SILENCE anything left over from the mangled attempt
run("cd /tmp/vcimod && enable -f ./memdump.so mem dump 2>/dev/null; "
    "mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; ./setled 0 2>/dev/null; echo silenced=$?")

# 2) riff as a device-side loop. tokens: digits=D-major degree, x=phrase gap.
#    0=D4(0xc59) 2=E4(0xc4f) 3=F#4(0xc46) 4=G4(0xc42)
riff = (
 "cd /tmp/vcimod && enable -f ./memdump.so mem dump 2>/dev/null; mem -a 0x40e0002c 0x3f0; "
 "for rep in 1 2 3 4; do "
 "for t in 4 3 2 x 3 x 2 3 2 x 0 3 0 x 3 x 0 3 0 x 3; do "
 "if [ \"$t\" = x ]; then usleep 70000; continue; fi; "
 "case $t in 0)val=0xc59;col=0x020;; 2)val=0xc4f;col=0x020;; 3)val=0xc46;col=0x370;; 4)val=0xc42;col=0x350;; esac; "
 "mem -a 0x40e00020 $col; mem -a 0x10000048 $val; usleep 100000; "
 "mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep 48000; "
 "done; usleep 150000; done; "
 "mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; echo done=$?"
)
print("riff cmd length:", len(riff), "chars")
run(riff)
v.close()
