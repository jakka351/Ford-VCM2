#!/usr/bin/env python3
import sys, os
sys.path.insert(0, r"C:/Users/admin/AppData/Local/Temp/claude/e89906dea6c63738/26a8e897-7300-4074-97d2-5fa47f828fb0/scratchpad")
from vcm import VCM

BASE = r"C:/Users/admin/Desktop/Ford-VCM2/backups/2026-11-07"
INFO = os.path.join(BASE, "info")
os.makedirs(INFO, exist_ok=True)

CMDS = {
 "proc_mtd":        "cat /proc/mtd",
 "proc_cmdline":    "cat /proc/cmdline",
 "proc_partitions": "cat /proc/partitions",
 "uname":           "uname -a; echo; cat /proc/version",
 "mount":           "mount; echo '--- /proc/mounts ---'; cat /proc/mounts",
 "df":              "df -h; echo '---'; df",
 "ps":              "ps w 2>/dev/null || ps",
 "ifconfig":        "ifconfig -a",
 "netstat":         "netstat -tlnp 2>/dev/null; echo '--- all ---'; netstat -an 2>/dev/null",
 "modules":         "lsmod 2>/dev/null; echo '--- /proc/modules ---'; cat /proc/modules",
 "dmesg":           "dmesg",
 "meminfo":         "free 2>/dev/null; echo '--- meminfo ---'; cat /proc/meminfo",
 "cpuinfo":         "cat /proc/cpuinfo",
 "env":             "env; echo '--- set ---'; set",
 "passwd_group":    "echo '--- passwd ---'; cat /etc/passwd 2>/dev/null; echo '--- shadow ---'; cat /etc/shadow 2>/dev/null; echo '--- group ---'; cat /etc/group 2>/dev/null",
 "hostname_id":     "hostname; echo; id; echo; cat /etc/hostname 2>/dev/null",
 "inittab_rc":      "echo '=== inittab ==='; cat /etc/inittab 2>/dev/null; echo; echo '=== init.d ==='; ls -la /etc/init.d 2>/dev/null; echo; for f in /etc/init.d/* /etc/rc* /etc/profile; do echo \"===== $f =====\"; cat \"$f\" 2>/dev/null; done",
 "ls_root":         "ls -la /",
 "ls_etc":          "ls -la /etc; echo; ls -laR /etc/vci 2>/dev/null",
 "ls_usr_local":    "ls -laR /usr/local 2>/dev/null",
 "ls_mnt_sd":       "ls -laR /mnt/sd 2>/dev/null",
 "find_scripts":    "echo '=== self-test ==='; find / -name 'self-test*' 2>/dev/null; echo '=== cgi ==='; find / \\( -name '*.cgi' -o -path '*cgi-bin*' \\) 2>/dev/null; echo '=== httpd ==='; find / -name 'httpd*' 2>/dev/null; echo '=== hwtest ==='; find / -path '*hwtest*' 2>/dev/null",
 "find_apps":       "echo '=== apps dirs ==='; find / -type d -name 'vci-diags' 2>/dev/null; find / -type d -name 'apps' 2>/dev/null; echo '=== *.sh ==='; find / -name '*.sh' 2>/dev/null",
 "vci_config":      "echo '=== /etc/vci/config tree ==='; ls -laR /etc/vci/config 2>/dev/null; echo '=== testmode flag? ==='; ls -la /etc/vci/config/testmode 2>/dev/null; echo '=== cat small cfgs ==='; for f in $(find /etc/vci/config -type f 2>/dev/null); do echo \"----- $f -----\"; (head -c 400 \"$f\"; echo) 2>/dev/null; done",
 "serial_mac":      "echo '=== mtd11 serialnum (od) ==='; dd if=/dev/mtd11 bs=256 count=1 2>/dev/null | od -c | head -20; echo '=== mtd12 macaddress (od) ==='; dd if=/dev/mtd12 bs=256 count=1 2>/dev/null | od -c | head -20; echo '=== mtd9 linuxvars1 ==='; dd if=/dev/mtd9 bs=512 count=1 2>/dev/null | od -c | head -30; echo '=== mtd10 linuxvars2 ==='; dd if=/dev/mtd10 bs=512 count=1 2>/dev/null | od -c | head -30; echo '=== mtd2 bootvars ==='; dd if=/dev/mtd2 bs=512 count=2 2>/dev/null | od -c | head -40",
 "version_files":   "for f in /etc/version /etc/issue /etc/os-release /usr/local/etc/version /etc/vci/version; do echo \"===== $f =====\"; cat \"$f\" 2>/dev/null; done; echo '=== find version-ish ==='; find / \\( -iname '*version*' -o -iname '*release*' \\) -type f 2>/dev/null | head -40",
 "tar_help":        "tar 2>&1 | head -40; echo '=== busybox applets ==='; busybox 2>&1 | tail -30",
}

v = VCM()
index = []
for name, cmd in CMDS.items():
    out, rc = v.run(cmd, overall=90, idle=8)
    path = os.path.join(INFO, name + ".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# cmd: {cmd}\n# rc: {rc}\n\n{out}\n")
    index.append((name, rc, len(out)))
    print(f"[saved] {name:16s} rc={rc} bytes={len(out)}")
v.close()

print("\n=== quick peeks ===")
for n in ["proc_mtd","proc_cmdline","ls_root","find_scripts","tar_help","version_files","serial_mac"]:
    p = os.path.join(INFO, n+".txt")
    print(f"\n----- {n} -----")
    print(open(p, encoding="utf-8").read()[:2000])
