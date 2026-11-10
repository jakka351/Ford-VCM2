#!/usr/bin/env python3
import tarfile, re
SD = r"C:/Users/admin/Desktop/Ford-VCM2/backups/2026-11-07/fs/sd-p1-mnt-sd.tar.gz"
WANT = ["setled.c", "flashLEDs", "User-Interface-Test.STD", "GPIO1-Test.6516"]
tf = tarfile.open(SD, "r:gz")
for m in tf.getmembers():
    if m.isfile() and any(m.name.endswith(w) for w in WANT):
        data = tf.extractfile(m).read().decode("utf-8","replace")
        print(f"\n################ {m.name} ({m.size} B) ################")
        print(data)
# also search every file for beeper / beep / Power_button references
print("\n\n================ GREP: beep/beeper/Power_button across SD ================")
pat = re.compile(r"(beep|beeper|Power_button|buzzer|setled|/dev/vci|ioctl|tone)", re.I)
for m in tf.getmembers():
    if not m.isfile() or m.size > 40000: continue
    try: data = tf.extractfile(m).read().decode("utf-8","replace")
    except Exception: continue
    for i,line in enumerate(data.splitlines()):
        if pat.search(line):
            print(f"{m.name}:{i+1}: {line.strip()[:160]}")
tf.close()
