#!/usr/bin/env python3
import sys, time
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM
v = VCM()
def run(c, **k):
    o, rc = v.run(c, **k); print(f"\n$ {c}\n{o}  [rc={rc}]"); return o, rc

print("##### STATE BEFORE #####")
run("echo '--- scsi ---'; cat /proc/scsi/scsi 2>/dev/null; echo '--- block devs ---'; ls -la /dev/sd* /dev/sr* /dev/scd* 2>/dev/null")
run("echo '--- 2-1.2 now ---'; cat /sys/bus/usb/devices/2-1.2/idVendor /sys/bus/usb/devices/2-1.2/idProduct 2>/dev/null")
run("echo '--- modprobe infra ---'; command -v modprobe insmod; ls -la /lib/modules 2>/dev/null; "
    "ls /usr/local/lib/modules/2.6.24.4-etas-08apr25/modules.dep 2>&1 | head -1; "
    "ls /usr/local/lib/modules/2.6.24.4-etas-08apr25/kernel/drivers/net/wireless/rtl8712/ 2>/dev/null")
run("echo '--- eject applet? ---'; command -v eject; busybox eject --help 2>&1 | head -3")

print("\n##### MODE-SWITCH ATTEMPT (eject the Realtek pseudo-disk) #####")
# find the realtek block device (usually /dev/sda) and eject it to trigger switch
run("for dev in /dev/sr0 /dev/scd0 /dev/sda; do "
    "  if [ -b $dev ]; then echo \"ejecting $dev\"; eject $dev 2>&1; fi; done; echo eject_rc=$?")
time.sleep(4)

print("\n##### STATE AFTER #####")
run("echo '--- 2-1.2 idProduct now ---'; cat /sys/bus/usb/devices/2-1.2/idProduct 2>/dev/null; "
    "echo '--- all usb pids ---'; for d in /sys/bus/usb/devices/*; do [ -e $d/idProduct ] && echo \"$(basename $d): $(cat $d/idVendor):$(cat $d/idProduct)\"; done")
run("echo '--- net ifaces ---'; ls /sys/class/net/; echo '--- dmesg tail ---'; dmesg | tail -15")
v.close()
