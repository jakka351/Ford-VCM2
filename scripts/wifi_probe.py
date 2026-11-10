#!/usr/bin/env python3
import sys
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM
v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k); print(f"\n$ {c}\n{o}  [rc={rc}]"); return o, rc

run("echo '=== USB devices (vendor:product) ==='; "
    "for d in /sys/bus/usb/devices/*; do "
    "  if [ -e $d/idProduct ]; then "
    "    echo \"$(basename $d): $(cat $d/idVendor 2>/dev/null):$(cat $d/idProduct 2>/dev/null)  $(cat $d/manufacturer 2>/dev/null) $(cat $d/product 2>/dev/null)\"; "
    "  fi; done")
run("echo '=== net interfaces ==='; ls -la /sys/class/net/ 2>/dev/null; echo '--- ifconfig -a ---'; ifconfig -a 2>/dev/null | grep -E '^[a-z]'")
run("echo '=== wifi modules loaded ==='; lsmod | grep -iE '8712|8192|libertas|rtl|cfg80211|mac80211|wlan|wext' || echo '(none loaded)'")
run("echo '=== wifi driver modules available on SD ==='; ls -la /usr/local/lib/modules/2.6.24.4-etas-08apr25/kernel/drivers/net/wireless/ 2>/dev/null; "
    "echo '--- search ---'; find / \\( -name 'r8712u*' -o -name 'r8192*' -o -name 'libertas*' \\) 2>/dev/null | head")
run("echo '=== wifi userspace tools ==='; for t in wpa_supplicant iwconfig iwlist iw wpa_cli udhcpc; do p=$(command -v $t 2>/dev/null); echo \"$t=${p:-NO}\"; done; echo '--- /usr/local/wpa ---'; ls -la /usr/local/wpa 2>/dev/null")
run("echo '=== wifi status flags / eeprom cache ==='; ls -la /tmp/wifi_present /tmp/wireless_uninit /tmp/wifi_type_usb /etc/vci/config/802.11n-eeprom 2>&1")
run("echo '=== usb/realtek in dmesg ==='; dmesg | grep -iE 'usb [0-9]|realtek|8712|wlan|rtl|new.*device' | tail -25")
v.close()
