#!/usr/bin/env python3
import tarfile, io, re

SD   = r"C:/Users/admin/Desktop/Ford-VCM2/backups/2026-11-07/fs/sd-p1-mnt-sd.tar.gz"
ROOT = r"C:/Users/admin/Desktop/Ford-VCM2/backups/2026-11-07/fs/rootfs.tar.gz"

KW = re.compile(rb"led|beep|buzz|tone|piezo|gpio|wifi|wlan|iwconfig|wpa|ifconfig|/dev/|sysfs|class/leds", re.I)

def scan(path, label, cat_substr=None, max_cat=6000):
    print(f"\n########## {label}: {path} ##########")
    tf = tarfile.open(path, "r:gz")
    names = tf.getnames()
    # show hwtest + led/beep/wifi-ish file names
    hits = [n for n in names if re.search(r"hwtest|led|beep|buzz|tone|wifi|wlan|self-test|diag", n, re.I)]
    print("---- name hits ----")
    for n in hits:
        print("  ", n)
    # content scan small text files
    print("---- content keyword hits (small files) ----")
    for m in tf.getmembers():
        if not m.isfile() or m.size > 65536:
            continue
        try:
            data = tf.extractfile(m).read()
        except Exception:
            continue
        if KW.search(data):
            # count distinct keyword classes
            print(f"  [{m.size:6d}] {m.name}")
    # optionally cat specific files
    if cat_substr:
        for m in tf.getmembers():
            if m.isfile() and any(s in m.name for s in cat_substr) and m.size <= max_cat:
                try:
                    data = tf.extractfile(m).read().decode("utf-8","replace")
                except Exception:
                    continue
                print(f"\n===== CAT {m.name} ({m.size} B) =====")
                print(data)
    tf.close()

scan(SD, "SD p1", cat_substr=["self-test", "hwtest", "led", "beep", "buzz", "tone"])
scan(ROOT, "ROOTFS")
