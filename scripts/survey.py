#!/usr/bin/env python3
import sys, re
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM

v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k); return o.strip(), rc

def hexval(dumpline):
    # "0x41700010: 00000652" -> 0x652
    m = re.search(r":\s*([0-9a-fA-F]+)\s*$", dumpline.strip().splitlines()[-1]) if dumpline.strip() else None
    return int(m.group(1), 16) if m else None

print("="*60)
print(" VCM II  LIVE TELEMETRY SURVEY  (all read-only)")
print("="*60)

# ---------- TEMPERATURE (sysfs, TMP275 @ i2c 0x48) ----------
base = "/sys/class/i2c-adapter/i2c-0/0-0048"
t_raw,_   = run(f"cat {base}/temperature 2>/dev/null")
tl_raw,_  = run(f"cat {base}/talert_low_raw 2>/dev/null")
th_raw,_  = run(f"cat {base}/talert_high_raw 2>/dev/null")
def to_c(s):
    s=s.strip()
    try:
        n=int(s,16) if s.lower().startswith("0x") else int(s)
    except: return None
    return n/256.0
print("\n--- TEMPERATURE (internal, I2C 0x48) ---")
# NOTE: the 'temperature' node is already in whole deg C; only the *_raw
# threshold nodes use the raw register (value/256) format.
try:
    temp_c = int(t_raw.strip())
    print(f"  temperature : {temp_c} C")
except Exception:
    print(f"  temperature : {t_raw!r}")
print(f"  alert low / high (raw) : {tl_raw!r} / {th_raw!r}"
      + (f"  -> {to_c(tl_raw):.0f}C / {to_c(th_raw):.0f}C" if to_c(tl_raw) is not None else ""))

# ---------- SYSTEM ----------
print("\n--- SYSTEM ---")
for label,cmd in [("uname","uname -a"),("uptime","cat /proc/uptime"),("loadavg","cat /proc/loadavg"),
                  ("cmdline","cat /proc/cmdline"),("hostname","hostname")]:
    o,_=run(cmd); print(f"  {label:8s}: {o}")
o,_=run("grep -E 'MemTotal|MemFree' /proc/meminfo"); print(f"  memory  : {o.replace(chr(10),'  ')}")

# ---------- RTC ----------
print("\n--- REAL-TIME CLOCK ---")
o,_=run("date"); print(f"  system date : {o}")
o,_=run("ls /dev/rtc* 2>/dev/null"); print(f"  rtc dev     : {o or '(none)'}")
o,_=run("hwclock -r 2>&1 || hwclock -r -f /dev/rtc0 2>&1"); print(f"  hwclock -r  : {o}")

# ---------- ADC (battery / adapter voltages via SSP2) ----------
print("\n--- ADC VOLTAGES (SSP2) ---")
run("cd /tmp/vcimod && enable -f ./memdump.so mem dump 2>/dev/null")
# turn off all muxes, init SSP2 ADC
run("mem -a 0x10000004 0x0; mem -a 0x10000008 0x0; mem -a 0x1000000c 0x0; mem -a 0x10000010 0x0; "
    "mem -a 0x10000014 0x0; mem -a 0x10000018 0x0; mem -a 0x1000001c 0x0; "
    "mem -a 0x41700000 0x00c0000f; mem -a 0x41700004 0x00001dc8; mem -a 0x41700000 0x00c0008f; "
    "mem -a 0x10000004 0x08000000; mem -a 0x41700010 0x0000; dump -b 0x41700010 -l 4 -4 >/dev/null; echo adc_init=$?")
CH = [("Chan4 VDLC (battery@OBD)",0x0C,7550),("Chan5 VF (filtered batt)",0x0D,7550),
      ("Chan6 ID_V1 (adapter id1)",0x0E,861),("Chan7 ID_V2 (adapter id2)",0x0F,861)]
for name,ch,uv in CH:
    o,_=run(f"mem -a 0x10000014 0x0; usleep 50000; mem -a 0x10000010 0x{ch:02x}; usleep 50000; "
            f"mem -a 0x41700010 0x0000; dump -b 0x41700010 -l 4 -4")
    raw = hexval(o)
    volts = (raw*uv/1e6) if raw is not None else None
    print(f"  {name:26s}: raw=0x{raw:04x} ({raw:5d})  = {volts:6.3f} V" if raw is not None else f"  {name}: (read fail: {o!r})")
# cleanup muxes
run("mem -a 0x10000004 0x0; mem -a 0x10000010 0x0; mem -a 0x10000014 0x0; echo adc_clean=$?")

v.close()
print("\n" + "="*60)
print("NOTE: on USB power (no vehicle at the DLC), VDLC/VF read ~0V;")
print("plug into a car or bench-feed the DLC pins to see real battery V.")
print("="*60)
