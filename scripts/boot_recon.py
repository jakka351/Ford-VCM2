#!/usr/bin/env python3
import tarfile, re
ROOT = r"C:/Users/admin/Desktop/Ford-VCM2/backups/2026-11-07/fs/rootfs.tar.gz"
SD   = r"C:/Users/admin/Desktop/Ford-VCM2/backups/2026-11-07/fs/sd-p1-mnt-sd.tar.gz"

def cat(tar, endings):
    tf = tarfile.open(tar, "r:gz")
    for m in tf.getmembers():
        if m.isfile() and any(m.name.endswith(e) for e in endings):
            try: d = tf.extractfile(m).read().decode("utf-8","replace")
            except: continue
            print(f"\n################ {m.name} ({m.size} B) ################\n{d}")
    tf.close()

def grep(tar, pat, label):
    rx = re.compile(pat, re.I)
    tf = tarfile.open(tar, "r:gz")
    print(f"\n===== GREP {label}: /{pat}/ =====")
    for m in tf.getmembers():
        if not m.isfile() or m.size > 60000: continue
        try: d = tf.extractfile(m).read().decode("utf-8","replace")
        except: continue
        for i,ln in enumerate(d.splitlines()):
            if rx.search(ln):
                print(f"{m.name}:{i+1}: {ln.strip()[:150]}")
    tf.close()

print("########## ROOTFS: loadsdrc ##########")
cat(ROOT, ["/loadsdrc"])
grep(ROOT, r"loadsdrc|/mnt/sd|sdrc|autorun|auto-run|mmcblk|sd_?mount", "rootfs sd-boot refs")

print("\n\n########## SD p1: top-level + self-test + any rc/autorun ##########")
tf = tarfile.open(SD, "r:gz")
tops = sorted(set(n.split("/")[1] for n in tf.getnames() if n.startswith("./") and len(n.split("/"))>1))
print("SD top-level:", tops)
tf.close()
cat(SD, ["/self-test.sh", "/boot.sh", "autorun", "/sdrc", "/start-httpd"])
grep(SD, r"testmode|self-test|boot\.sh|loadsdrc|run-parts|source |^\. ", "sd boot refs")
