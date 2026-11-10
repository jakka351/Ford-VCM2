#!/usr/bin/env python3
import sys, time
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM
v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k); print(f"\n$ {c}\n{o}  [rc={rc}]"); return o, rc

WL = "/usr/local/lib/modules/2.6.24.4-etas-08apr25/kernel/drivers/net/wireless"

# make sure dongle is in WiFi mode (c811), re-switch if it reverted to 1a2b
o,_ = run("cat /sys/bus/usb/devices/2-1.2/idProduct 2>/dev/null")
if "1a2b" in o:
    run("for d in /dev/sr0 /dev/scd0 /dev/sda; do [ -b $d ] && eject $d; done")
    time.sleep(4)
    run("cat /sys/bus/usb/devices/2-1.2/idProduct 2>/dev/null")

run("mkdir -p /tmp/wifi")
# driver module file -> sysfs driver name registered with usbcore
DRV = [("rtl8192eu","rtl8192eu/r8192eu"),("rtl8192cu","rtl8192cu/r8192cu"),("r8712u","rtl8712/r8712u")]

bound = None
for sysname, path in DRV:
    name = path.split("/")[1]
    print(f"\n########## force-bind via {sysname} (module {name}) ##########")
    run(f"cp {WL}/{path}.ko.gz /tmp/wifi/ 2>/dev/null; cd /tmp/wifi && gzip -df {name}.ko.gz 2>/dev/null; "
        f"insmod /tmp/wifi/{name}.ko ifname=wlan0 2>/dev/null || insmod /tmp/wifi/{name}.ko 2>/dev/null; "
        f"ls -d /sys/bus/usb/drivers/{sysname} 2>&1")
    # force the driver to try our device's id
    run(f"echo '0bda c811' > /sys/bus/usb/drivers/{sysname}/new_id 2>&1; echo newid_rc=$?")
    time.sleep(3)
    o,_ = run("ls /sys/class/net/; echo '--- dmesg ---'; dmesg | tail -12")
    if any(x in o for x in ("wlan0","wlan1","ra0")):
        print(f"  >>> interface appeared under {sysname}!")
        bound = sysname
        break
    run(f"rmmod {name} 2>&1")
    time.sleep(1)

print("\n########## RESULT ##########")
o,_ = run("ls /sys/class/net/; ifconfig -a 2>/dev/null | grep -E '^[a-z]'")
print("BOUND DRIVER:", bound)

if bound:
    run("ifconfig wlan0 up 2>&1; sleep 1; ifconfig wlan0 2>&1 | head -3")
    # quick scan via wpa_supplicant/wpa_cli
    run("killall wpa_supplicant 2>/dev/null; /usr/local/wpa/wpa_supplicant -B -i wlan0 -c /dev/null -Dwext 2>&1; sleep 2; "
        "/usr/local/wpa/wpa_cli -i wlan0 scan 2>&1; sleep 4; echo '=== SCAN RESULTS ==='; /usr/local/wpa/wpa_cli -i wlan0 scan_results 2>&1", overall=40)
v.close()
