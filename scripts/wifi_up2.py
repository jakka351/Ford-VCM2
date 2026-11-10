#!/usr/bin/env python3
import sys, time
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM
v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k); print(f"\n$ {c}\n{o}  [rc={rc}]"); return o, rc

WL = "/usr/local/lib/modules/2.6.24.4-etas-08apr25/kernel/drivers/net/wireless"
DRIVERS = [
    ("r8712u",  f"{WL}/rtl8712/r8712u.ko.gz"),
    ("r8192eu", f"{WL}/rtl8192eu/r8192eu.ko.gz"),
    ("r8192cu", f"{WL}/rtl8192cu/r8192cu.ko.gz"),
]
run("mkdir -p /tmp/wifi; echo '--- baseline ifaces ---'; ls /sys/class/net/; echo 'pid:'; cat /sys/bus/usb/devices/2-1.2/idProduct")

loaded = None
for name, gz in DRIVERS:
    print(f"\n########## trying {name} ##########")
    o,_ = run(f"cp {gz} /tmp/wifi/ 2>&1; cd /tmp/wifi && gzip -df {name}.ko.gz 2>&1; ls -la {name}.ko 2>&1")
    if f"{name}.ko" not in o:
        print(f"  (could not stage {name})"); continue
    # try with ifname param, fall back to no param
    run(f"insmod /tmp/wifi/{name}.ko ifname=wlan0 2>&1 || insmod /tmp/wifi/{name}.ko 2>&1; echo ins_rc=$?")
    time.sleep(2)
    o,_ = run("ls /sys/class/net/; echo '--- dmesg ---'; dmesg | tail -8")
    if "wlan0" in o or "ra0" in o or "wlan1" in o:
        print(f"  >>> {name} created a wireless interface!")
        loaded = name
        break
    # no iface: unload and try next
    run(f"rmmod {name} 2>&1; echo rmmod_rc=$?")
    time.sleep(1)

print("\n########## RESULT ##########")
run("lsmod | head; echo '--- ifaces ---'; ls /sys/class/net/; echo '--- iface detail ---'; ifconfig -a 2>/dev/null | grep -E '^[a-z]'")
print("LOADED DRIVER:", loaded)
v.close()
