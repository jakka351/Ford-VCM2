# Ford VCM II — Root-Access Capability Map

What this box can do once you have a root shell on it, grounded in what was
actually found on **this unit** during the mod session (2026-11-07/08). Companion
to [README.md](README.md) (platform/backup/recovery) and [mods/](mods/) (installed mods).

**Legend:** ✅ verified live on this unit · 🟡 mechanism confirmed, not yet exercised · ⚪ plausible, not tried

> **Scope / ethics.** This is reverse-engineering, diagnostics and datalogging on
> **hardware you own**. Injecting on a *live* vehicle bus affects the vehicle — use a
> bench rig or a parked car you own. Re-serialising / module-type spoofing to dodge a
> blacklist is a separate, licence-circumvention matter (see README) and is **not** what
> this document is about.

---

## 0. This unit at a glance

| | |
|---|---|
| Model | ETAS/Bosch **6516**, product `6516_20` |
| Serial (`mtd11`) | `1348-88612951` |
| Module type (`mtd9`) | `MODULE_TYPE=13` |
| Stored MAC (`mtd12`) | `00:90:7E:0E:B4:71` (ETAS OUI) |
| Kernel | `2.6.24.4-etas-08apr25`, `armv5tel`, PREEMPT |
| Userland | BusyBox 1.2.2, `bash-3.2`; ~60 MB RAM |
| Recovery FW | `0.1.5.0` |

---

## 1. Access & transfer model ✅

- **Root shell:** passwordless **telnet** at `192.168.171.2` (iface `usb0`, USB-RNDIS, /24). `telnetd -l /bin/bash`.
- **Persistent by default:** this unit **re-enters test mode on every boot** (self-test persistence), so telnet keeps coming back on its own. (Normal units need test mode re-armed each boot.)
- **On the box:** `nc`, `gzip`/`gunzip`, `tar -z`, `md5sum`/`sha1sum`, `dd`, `od`, `uuencode`, `udhcpc`, `wpa_supplicant`/`wpa_cli` (`/usr/local/wpa`), `hostapd.sh`, `crond`, `eject`, `modprobe`/`insmod`.
- **Not present:** `base64`, `wget`, `sha256sum`, `openssl`, `flashcp`, `iwconfig`/`iwlist`.
- **File transfer pattern** (no base64/ftp needed): device `nc -l -p PORT`, PC connects out and streams; `gzip` in transit, `md5sum` to verify. Driver: [scripts/vcm.py](scripts/vcm.py) (Python `telnetlib`).

## 2. Storage & persistence model ✅

| Mount | Device | Type | Persistent? |
|---|---|---|---|
| `/` | `/dev/ram` (initrd1 = `mtd7`) | ext2 | ❌ RAM, rebuilt from flash each boot |
| `/tmp` | tmpfs | — | ❌ RAM |
| `/etc/vci/config` | `mtdblock8` | jffs2 | ✅ flash config |
| `/mnt/sd` | `mmcblk0p1` | ext3 (exec ok) | ✅ SD card |
| `/usr/local/data` | `mmcblk0p2` | ext3 | ✅ SD card |

- **Boot:** `fsboot → U-Boot → kernel → RAM rootfs`. **Never write `mtd0/1/2`** without serial console (hard-brick territory).
- **Boot hook (how to run code every boot):** `/etc/vci/config/dev_hook.sh` on jffs2 is executed by `vci_run_dev_hook_if_present` near the end of **both** `init_script.sh` (normal) and `init_script_testmode.sh:63` (test). It runs **synchronously**, so long-running work must be backgrounded (`&`). Reversible with one `rm`. Example installed: [mods/dev_hook.sh](mods/dev_hook.sh).
- `vci_run_telnet_if_enabled` (a flag) can make telnet come up on a *normal* boot too. 🟡

## 3. Kernel drivers / modules present ✅

Loaded: `etas_led`, `etas_speaker` (beeper), `tmp101` (temp), `bosch_vci_spi`, `i2c_pxa`, `i2c_dev`, `sd_mod`, `usb_storage`, `scsi_mod`.
On SD (`/usr/local/lib/modules/.../net/wireless/`): `r8712u`, `r8192cu`, `r8192eu`, `libertas`.

---

## 4. Hardware control — verified register maps

All register access via the `mem`/`dump` bash builtins:
`enable -f /mnt/sd/apps/vci-diags/hwtest-scripts/memdump.so mem dump`
(`mem -a <addr> <val>` writes; `dump -b <addr> -l 4 -4` reads).

### 4.1 LEDs ✅
- On/off via `setled` → `/dev/etas-led`: `./setled 0` (all off), `./setled a b c d e` = Power / PC / Error / Vehicle / Status.
- **Colour** via FPGA regs: enable `0x40e0002c` (set `0x3f0` = all), colour bitfield `0x40e00020`:

| bit | LED / colour |
|---|---|
| `0x080` | Power — green |
| `0x040` / `0x100` | PC — green / yellow |
| `0x020` | **Error — RED** |
| `0x010` / `0x200` | Vehicle — green / yellow |

Palette = red → orange(green+yellow) → yellow → green (no blue/RGB). Combine bits for amber/white.

### 4.2 Beeper ✅
- Reg `0x10000048`: `0x0c0d` = 2000 Hz on, `0x0000` = off. (Reads back `0x0001` = status bit; write `0x0000` to silence.) Kernel driver `etas_speaker` is an alternative front-end. 🟡

### 4.3 Temperature ✅
- `cat /sys/class/i2c-adapter/i2c-0/0-0048/temperature` → whole °C (read **35 °C**). `talert_low_raw`/`talert_high_raw` are raw (÷256 = 75/80 °C). TMP101 @ I²C `0x48`.

### 4.4 Analog / ADC ✅
- SSP2 init, select channel at `0x10000010`, read counts at `0x41700010`:

| Chan | signal | scale | note |
|---|---|---|---|
| 4 | VDLC — battery @ OBD | 7550 µV/bit | read 0.33 V (no car) |
| 5 | VF — filtered battery | 7550 µV/bit | read 4.65 V (USB rail) |
| 6 / 7 | adapter ID 1 / 2 | 861 µV/bit | floating |
| 0 / 1 | K-line A/B transceiver | 7550 µV/bit | |

- **Vpp** programming-voltage output and threshold DACs exist (factory `Vpp-Test`). ⚪

### 4.5 CAN ✅ (controllers) / 🟡 (TX/RX not yet exercised)
Three **SJA1000 / PeliCAN**-style controllers — confirmed present, idle (reset mode), and **uncontended in test mode** (`vci-service` not running):

| Controller | Base |
|---|---|
| CAN-A | `0x10000100` |
| CAN-B | `0x10000200` |
| CAN-C | `0x10000300` |

Register offsets (32-bit stride) from base:

| off | reg |
|---|---|
| `+0x00` | mode (`0x01` reset, `0x00` run, STM bit for self-test, `0x0d/0x0c` filter-cfg) |
| `+0x04` | command (`0x01` transmit, `0x12` transmit+self-reception, `0x04` release RX) |
| `+0x08` / `+0x0c` | status / IRQ status |
| `+0x10` | IRQ enable (`0x01` = RX IRQ) |
| `+0x18` / `+0x1c` | bit timing (BTR) |
| `+0x40` / `+0x50` / `+0x60` | TX/RX descriptor (ID+DLC) / data / data |
| `+0x78` | per-frame timestamp |
| `+0x7c` | clock divider |

Bitrates: **500 kbps** → cdr `0x80`, BTR `0x43` / `0x18`. **33.3 kbps** (FT/low-speed) → BTR `0x6c` / `0x1c`.
Pass-all filter: `+0x40..+0x4c = 0`, `+0x50..+0x5c = 0xff`, mode `0x0c`.
TX example (from factory loopback): desc `0x1100fc08`, data `0x55443322` / `0x00887766`, command `0x12`.

### 4.6 Other vehicle interfaces 🟡
- **K-line / ISO 9141 / KWP2000** (UART MUX A/B + pull-ups).
- **J1850 VPW & PWM** (factory loopback tests present).
- **FT-CAN / low-speed single-wire-ish CAN** on pins 1 & 9.
- **RTC** — readable via SPI-poke (`RTC-read`); kernel RTC driver only loads on *normal* boot, so `hwclock` is unavailable in test mode.

---

## 5. The plethora — what you can build

### Vehicle / bus
- **CAN sniffer** (3 buses, pass-all, timestamped) 🟡
- **CAN injector / frame sender** 🟡
- **Bus fingerprinter** — passive ID + periodicity map, then active OBD-II PID / UDS tester-present probing to identify ECUs & vehicle 🟡
- **Logger → SD**, **replay**, **multi-bus bridge/gateway**, **fuzzer** 🟡
- **UDS / OBD-II scanner** over CAN; **KWP2000 / ISO9141 / J1850** for older vehicles ⚪

### Instrumentation
- Live **battery/ignition voltage** readout ✅, **internal temperature** ✅, **Vpp** programming voltage ⚪

### It's a Linux computer
- **Standalone SD datalogger** — boots, logs CAN to the 2 GB SD, no PC (persist via `dev_hook`) 🟡
- **CAN-over-WiFi** to laptop/phone (needs a supported dongle, §7); **AP mode** via `hostapd.sh` 🟡
- **Live web dashboard** — `lighttpd` is already on the box — CAN/voltage/temp ⚪
- `crond` scheduling; **LED/beeper** as status indicators for your own apps ✅

## 6. "USB2CAN" / J2534 🟡

- **Don't extend J2534.** It's served by the proprietary `vci-service` (device) + Ford/ETAS DLL (Windows); extending it means editing closed binaries. Root + raw registers already give you *more* than J2534's verbs.
- **Recommended: CAN↔TCP bridge.** The PC link is USB-ethernet (`usb0`). Run a small daemon on the VCM that pumps SJA1000 RX → TCP socket and socket → TX. PC side drives it with `python-can`, SavvyCAN, or a tiny custom client → a CAN-over-USB adapter in all but name, with **zero** risk to the stock IDS function.
- A *true* USB-CAN-class gadget (slcan/gs_usb) is possible but means reworking the USB gadget (currently RNDIS) — higher effort, risks the IDS link. ⚪

## 7. WiFi status 🟡

- A dongle **is** plugged in (USB `2-1.2`). It enumerates as **Realtek CD-ROM `0bda:1a2b`** and **mode-switches to WiFi mode `0bda:c811` on `eject /dev/sda`** ✅.
- `0bda:c811` = **RTL8811CU (802.11ac)** — **unsupported** by this firmware's drivers (`r8712u`/`r8192cu`/`r8192eu`/`libertas`). They register but none binds.
- ⚠️ **Do not `new_id` force-bind** a mismatched Realtek driver — it oops'd the kernel and dropped the USB link (recovered by power-cycle; nothing was written to flash).
- **To get WiFi:** use an **RTL8712 / RTL8192CU / RTL8192EU** dongle (e.g. older D-Link DWA-130 / DWA-131 B1/E1). Then: eject-switch → `insmod` driver → `ifconfig wlan0 up` → `wpa_supplicant -Dwext -c <conf>` → `udhcpc`. Static-IP target from `mtd9`: `WIFI_1_Address=192.168.174.2`.

---

## 8. Session status

- **Backups** ([backups/2026-11-07/](backups/2026-11-07)): all 13 MTD partitions md5-verified ✅; `rootfs.tar.gz` + SD p1 ✅; **SD p2 (`/usr/local/data`) + master manifest still TODO**.
- **Mods installed:** rainbow boot greeting ([mods/dev_hook.sh](mods/dev_hook.sh)) ✅.
- **Not yet done:** live CAN TX/RX proof (self-test mode), CAN sniffer/bridge, SD p2 backup.
- **Golden rules:** image before writing; never touch `mtd0/1/2`; external DC power for flash writes; don't run `/web/cgi-bin/total-reflash` (wipes the SD). See README.
