#!/usr/bin/env python3
import tarfile
SD = r"C:/Users/admin/Desktop/Ford-VCM2/backups/2026-11-07/fs/sd-p1-mnt-sd.tar.gz"
WANT = ["setled.c", "User-Interface-Test.STD", "Temp_Sensor_Test.6516",
        "ADC-Tests-Misc.6516", "GPIO1-Test.6516", "RTC-read", "poll_power_button"]
tf = tarfile.open(SD, "r:gz")
for w in WANT:
    for m in tf.getmembers():
        if m.isfile() and m.name.endswith(w):
            data = tf.extractfile(m).read().decode("utf-8","replace")
            print(f"\n################ {m.name} ({m.size} B) ################")
            print(data)
            break
tf.close()
