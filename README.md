# Ford VCM II — Internals, Recovery & Firmware Backup

Working notes and operating procedures for the **Ford/Rotunda VCM II** (genuine units: ETAS/Bosch **6516** family). 

> The VCM II is an **embedded-Linux device**, not a dumb USB-to-OBD adapter. It boots a kernel, mounts a RAM-disk rootfs off NOR flash + microSD, and runs a web server and a telnet daemon. Recovery mode, test mode and the root shell all hang off that.

---

## Platform overview

- **What it is:** Ford's OEM vehicle communication module — the pass-thru interface IDS drives to reach Ford/Lincoln/Mercury and Mazda vehicles over the 16-pin DLC.
- **Userland:** small embedded Linux, BusyBox-style, `bash-3.2`.
- **Boots a RAM disk** (`root=/dev/ram`, `init=/linuxrc`) — the SD card is **data/config, not rootfs**.
- **Console:** `ttyS0` @ **38400 8N1**.

### Physical landmarks

| Landmark | Location / detail |
|---|---|
| **Recovery Mode switch** | Plastic tab under the rubber boot on the **end opposite the DLC** connector |
| **microSD slot** | Under the boot on the **USB side**. Paired to the unit's serial — won't run in another VCM II |
| **Front DC power port** | Bench-supply input; keep powered during all firmware work |
| **Internal HDL26-PL-B connector** | Serial console / bootloader on **pins 24 & 25** (`ttyS0`, 38400 8N1) |
| **Connectivity** | Wired USB (mandatory for firmware loading + CFR setup) + optional WiFi add-on card |

---

## Flash layout & boot chain

On-board NOR flash is carved into MTD partitions. Bootloader `mtdparts` line (from a recovery image — sizes/names are authoritative):

```
root=/dev/ram init=/linuxrc console=ttyS0,38400 rw ramdisk_size=24576
mtdparts=flash0:256k(fsboot),256k(boot),128k(bootvars),640k(fpga),
1536k(linux2),6144k(initrd2),3072k(linux1),19328k(initrd1),
1024k(jffs2),128k@32384k(linuxvars1),128k(linuxvars2),128k(snmac)
board_id=0x1
```

### MTD partition table

| Device | Name | Size | Role | Safe to restore? |
|---|---|---|---|---|
| `mtd0` | fsboot | 256k | First-stage boot | ❌ **do not touch** |
| `mtd1` | boot | 256k | Bootloader (U-Boot) | ❌ **do not touch** |
| `mtd2` | bootvars | 128k | Boot environment | ❌ **do not touch** |
| `mtd3` | fpga | 640k | FPGA bitstream | ⚠️ with care |
| `mtd4` | linux2 | 1536k | **Recovery kernel** | ✅ (custom recovery pair) |
| `mtd5` | initrd2 | 6144k | **Recovery ramdisk** | ✅ (custom recovery pair) |
| `mtd6` | linux1 | 3072k | Production kernel | ⚠️ |
| `mtd7` | initrd1 | 19328k | Production ramdisk | ⚠️ |
| `mtd8` | jffs2 | 1024k | RW config, mounted `/etc/vci/config` | ✅ |
| `mtd9` | linuxvars1 | 128k @0x7E80000 | Linux env vars | ⚠️ |
| `mtd10` | linuxvars2 | 128k | Linux env vars | ⚠️ |
| `mtd11` | snmac | 128k | **Serial number / MAC** | ⚠️ |

### Boot path

```
fsboot (mtd0) → U-Boot (mtd1) → kernel → Linux
                                  ├─ production: linux1 (mtd6) / initrd1 (mtd7)
                                  └─ recovery:   linux2 (mtd4) / initrd2 (mtd5)
```

- Serial number + module type resolve to the **`snmac` region (`mtd11`)**. Newer IDS firmware deliberately **shifts the `mtd11` offset** so old rewrite tricks land in the wrong place.
- `mtd4` + `mtd5` are the **recovery firmware pair**; a custom recovery image replaces exactly these two and **leaves the production kernel alone**.

---

## Recovery 

Use when: a firmware update failed, the SD is corrupt, the Error LED is red at boot, or the unit is stuck beeping once a second in a boot loop.

1. Unplug the **DLC cable** from the vehicle.
2. Unplug the **USB cable** from the VCM II and the PC.
3. Pull the rubber boot on the end **opposite the DLC** to expose the Recovery Mode switch (tab).
4. Launch VCI Manager.
5. **Press and hold the tab** — don't release until step 8.
6. With the tab still held, **connect USB** to the PC.
7. Keep holding until the **Power LED stays solid** and the unit **beeps** (~20–30 s).
8. **Release the tab** → unit is in Recovery Mode; IDS/VCI Manager pops the "new firmware available / Recover" dialog.
9. Click **Recover → Start Update**. Do **not** pull power or USB during the write.
10. It rewrites firmware, reboots, and beeps when done. Relaunch IDS; the normal icon means it recovered.

## Repair Mode

In VCI Manager, keyboard combo `CTRL`+`SHIFT`+`W` will show a hidden tab, `VCI Tools`. Use it to set repair mode, and enable the webserver and root `telnet` access to the filesystem.

1. Set repair mode
2. Note the IP address
3. Unplug the VCM2 from power and USB
4. Replug in via USB.
5. `telnet` into the ip address as root
6. You have root access
---

Set your PC to a **static IP on `192.168.171.x`** (e.g. `.1`, mask `/24`):

- **Web server:** `http://192.168.171.2` — ~15 s after the beep. Menu: *Set New Serial Number*, *Set Repair Test Mode* (stay in test mode next boot), and — on modded firmware — *Set Module Type* and a web firmware update.
- **Root shell:** `telnet 192.168.171.2` — ~10–15 s after the beep (PuTTY/ExtraPuTTY, type **Telnet**, port **23**). Lands straight on a root prompt (`bash-3.2#`), **no credentials** on stock test-mode firmware.

> *Set Repair Test Mode* must be re-armed each boot unless you persist it (the self-test hook above, or an always-testmode custom firmware).

---

## Firmware backup 

From the root shell, dump every MTD partition to the SD "VCM Backups" partition:

```sh
dd bs=512 if=/dev/mtd0  of=/mnt/sd/mtd0
dd bs=512 if=/dev/mtd1  of=/mnt/sd/mtd1
dd bs=512 if=/dev/mtd2  of=/mnt/sd/mtd2
dd bs=512 if=/dev/mtd3  of=/mnt/sd/mtd3
dd bs=512 if=/dev/mtd4  of=/mnt/sd/mtd4
dd bs=512 if=/dev/mtd5  of=/mnt/sd/mtd5
dd bs=512 if=/dev/mtd6  of=/mnt/sd/mtd6
dd bs=512 if=/dev/mtd7  of=/mnt/sd/mtd7
dd bs=512 if=/dev/mtd8  of=/mnt/sd/mtd8
dd bs=512 if=/dev/mtd9  of=/mnt/sd/mtd9
dd bs=512 if=/dev/mtd10 of=/mnt/sd/mtd10
dd bs=512 if=/dev/mtd11 of=/mnt/sd/mtd11
```

Then power down, copy the `mtd*` files somewhere safe, and you have a **known-good image**. Verify sizes against the MTD table above before trusting the dump.

> When we run this in-session we'll also capture `cat /proc/mtd`, `dmesg`, `mount`, `cat /etc/vci/config/*`, and the U-Boot environment so the backup is self-describing.

### Restore 

```sh
/usr/local/mtd/flash_unlock /dev/mtd11
flashcp -v mtd11-128k.new /dev/mtd11
```

**Golden rule (again):** when restoring, **skip `mtd0`, `mtd1`, `mtd2`** unless you have serial-console recovery ready.

---

## Modding reference

What the scene has built on top of test mode + a root shell:

- **Serial-number change** — from the web server's *Set New Serial Number*, or by writing the `snmac`/`mtd11` region directly. Default stock serial after a recover: `1211-31605352`. Well-known public clone serials (`1211-31605352`, `31606235`) get **blacklisted** by newer IDS.
- **Module-type change** — flip the unit's declared identity (Ford ↔ Mazda ↔ Suzuki 6516, etc.) so one interface drives multiple OEM apps (SDT II, Mazda IDS, JLR). Modded firmware exposes it under *Other Functions → Set Module Type*. **Gotcha:** Mazda IDS reverts serial/type to original on its own VCI update.
- **Custom recovery firmware ("ColtB45" image)** — the canonical modded recovery build. Keeps every stock test-mode function and adds: telnet server, FTP server, always-on test-mode web server, module-type change in the web UI, WiFi in recovery (disabled by default). Mounts SD RW at `/mnt/sd` and JFFS2 config RW at `/etc/vci/config`; ships with a **known fixed root password**. Installed by pushing `mtd4.new` / `mtd5.new` into `/tmp` over FTP/telnet and `flashcp`-ing onto `mtd4`/`mtd5` — **recovery pair only, production boot untouched**.

### Clones & the IDS blacklist (context)

- Ford/Bosch ship firmware via IDS that blacklists known clone serials — clones most likely banned from **v92.05** onward. Some clones work as late as IDS 122; others stop after IDS 96.
- Common community counter-moves: **freeze the VCI firmware folder** (replace `C:\Program Files\Bosch\...` with an older **2.115 / 2.119** set so IDS can't push the banning firmware — kill the `vtxi`/launcher process first if files are locked); run **old IDS (v86–v91)**; pin firmware per app (JLR → 2.115; Mazda 94xx → 2.119). The stable config most settle on: a clone **frozen on 2.119**, never allowed to update online.

---

## Bricking & recovery of last resort

- **Classic brick:** running `cgi-bin/total-reflash` from the test-mode web server **wipes the unit**.
- **Boot-partition brick:** a bad write to `mtd0`/`mtd1`/`mtd2` with no console → no Linux, no telnet, nothing to recover from in software.

**Last-resort ladder (easiest → hardest):**

1. **Still have a shell, bad bootvars?** Edit the boot environment from within Linux and reboot — no console hardware needed.
2. **Serial console** on HDL26-PL-B pins 24 & 25 (`ttyS0`, 38400 8N1) → drop to U-Boot, fix `bootargs`, tftp a kernel, re-flash. The real recovery path once Linux won't boot but U-Boot is alive.
3. **Bootloader gone?** JTAG, or desolder and read the NOR chip, reprogram from a known-good dump with an external programmer — or clone the chip from a working unit.

---

## Session checklist

Order of operations for this session once I have root telnet access:

- [ ] Confirm link: `telnet 192.168.171.2` → `bash-3.2#` prompt
- [ ] Capture environment: `cat /proc/mtd`, `uname -a`, `cat /proc/version`, `mount`, `dmesg`, `fw_printenv` (or U-Boot env), module type + serial
- [ ] Verify SD backup target is mounted RW (`/mnt/sd`) with free space
- [ ] **Full MTD backup** (`dd` all of mtd0–mtd11 → `/mnt/sd`)
- [ ] Pull `mtd*` images off the device, checksum (`md5sum`/`sha256sum`), verify sizes vs. MTD table
- [ ] Stash a labelled, read-only copy of the known-good image in this repo / offline
- [ ] Only then proceed to any mods — one change at a time, re-image between steps, bench power on

---

## Scope & legal note

This is **reference / repair / reverse-engineering material on hardware you own**: imaging the flash, backing up firmware, un-bricking, and learning the platform are all defensible on your own gear, and that's the primary purpose of this repo.

**Re-serialising to a non-blacklisted number so a counterfeit interface keeps running licensed OEM software is licence circumvention** — legally a different thing from the repair/RE work above, and named as such here rather than folded in under "repair." Keep that distinction in mind for anything beyond backing up and recovering your own unit.

Also I used to work for Bosch. So I know these fucking very well. The Serial number is only relevant to licensing on a Mazda VCM2, not with a Ford VCM2. 
