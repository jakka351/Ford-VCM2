#!/usr/bin/env python3
import sys, socket, time
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")

# quick reachability
ok = False
for i in range(5):
    try:
        s = socket.create_connection(("192.168.171.2", 23), timeout=3); s.close(); ok = True; break
    except OSError as e:
        print(f"[{i+1}] telnet 23 not open: {e.__class__.__name__}", flush=True); time.sleep(2)
if not ok:
    print("\nTELNET CLOSED -> device is in normal mode (telnet off) or still settling.")
    sys.exit(0)

print("TELNET OPEN -> connecting\n", flush=True)
from vcm import VCM
v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k); print(f"$ {c}\n{o}  [rc={rc}]\n", flush=True); return o, rc

run("id; hostname; echo uptime:; cat /proc/uptime")
run("echo '=== mode ==='; ls -l /tmp/testmode /etc/vci/config/testmode 2>&1; echo '--- which init ran ---'; ps w 2>/dev/null | grep -E 'init_script|vci-service|telnet' | grep -v grep")
run("echo '=== did dev_hook run? ==='; (logread 2>/dev/null | grep -iE 'dev hook|dev_hook') ; grep -iE 'dev hook|dev_hook' /var/log/messages 2>/dev/null; ls -l /tmp/vcimod 2>&1")
run("echo '=== wifi state ==='; echo 'usb 2-1.2 pid:'; cat /sys/bus/usb/devices/2-1.2/idProduct 2>/dev/null; echo 'ifaces:'; ls /sys/class/net/; echo '--- ifconfig ---'; ifconfig -a 2>/dev/null | grep -E '^[a-z]|inet'; echo '--- wifi modules ---'; lsmod | grep -iE '8712|8192|rtl|wlan|cfg80211' || echo none; echo '--- wpa procs ---'; ps w 2>/dev/null | grep -E 'wpa|udhcpc|hostapd' | grep -v grep")
run("echo '=== wifi flags ==='; ls -l /tmp/wifi_present /tmp/wireless_uninit /tmp/wifi_type_usb 2>&1")
v.close()
