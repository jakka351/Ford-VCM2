#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM
v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k); print(f"$ {c}\n{o}  [rc={rc}]\n"); return o, rc

# READ-ONLY: confirm the three CAN controllers exist and read mode/status (no writes)
script = (
 "cd /tmp/vcimod && enable -f ./memdump.so mem dump 2>/dev/null; "
 "for b in 100 200 300; do "
 "  echo \"=== CAN @ 0x10000$b ===\"; "
 "  echo -n '  mode  (+00): '; dump -b 0x10000$b -l 4 -4 | sed 's/.*: //'; "
 "  echo -n '  status(+08): '; dump -b 0x10000${b%00}308 -l 4 -4 >/dev/null 2>&1; "
 "done"
)
# simpler explicit reads (avoid arithmetic quirks)
run("cd /tmp/vcimod && enable -f ./memdump.so mem dump 2>/dev/null; echo ready")
for base in ["0x10000100","0x10000200","0x10000300"]:
    b=int(base,16)
    run(f"echo '=== CAN {base} ==='; "
        f"echo -n 'mode(+00)  : '; dump -b {hex(b+0x00)} -l 4 -4 | sed 's/.*: //'; "
        f"echo -n 'status(+08): '; dump -b {hex(b+0x08)} -l 4 -4 | sed 's/.*: //'; "
        f"echo -n 'irqst(+0c) : '; dump -b {hex(b+0x0c)} -l 4 -4 | sed 's/.*: //'; "
        f"echo -n 'cdr(+7c)   : '; dump -b {hex(b+0x7c)} -l 4 -4 | sed 's/.*: //'")
run("echo -n 'GPIO/IRQ level 0x40e00008 = '; dump -b 0x40e00008 -l 4 -4 | sed 's/.*: //'; "
    "echo -n 'vci-service procs: '; ps w 2>/dev/null | grep -c '[v]ci-service'")
v.close()
