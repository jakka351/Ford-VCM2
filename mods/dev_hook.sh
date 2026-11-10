#!/bin/bash
#
# dev_hook.sh - rainbow boot greeting for Ford VCM II (ETAS 6516)
# Installed by VCM2 mod session on 2026-11-07.
#
# Runs at the end of every NORMAL boot via init_script.sh ->
# vci_run_dev_hook_if_present().  Plays a short LED + beeper show in the
# BACKGROUND (so it never stalls boot), then releases the LEDs back to
# vci-service so normal status indication is unaffected.
#
# REMOVE:   rm /etc/vci/config/dev_hook.sh
# DISABLE:  touch /etc/vci/config/no_rainbow     (keeps the hook, skips the show)
#
# Hardware: FPGA LED enable reg 0x40e0002c, colour bitfield 0x40e00020,
#           beeper reg 0x10000048 (0x0c0d = 2000 Hz on, 0x0000 = off).
#           Colour bits: 0x080 Power-grn 0x040 PCgrn 0x100 PCyel
#                        0x020 Error-RED 0x010 Veh-grn 0x200 Veh-yel
#
[ -e /etc/vci/config/no_rainbow ] && exit 0

D=/tmp/vcimod
SRC=/etc/vci/config/diagnostics/hwtest-scripts
[ -x "$SRC/setled" ] || SRC=/mnt/sd/apps/vci-diags/hwtest-scripts
mkdir -p "$D"
cp "$SRC/setled" "$SRC/memdump.so" "$D"/ 2>/dev/null
chmod +x "$D/setled" 2>/dev/null
[ -x "$D/setled" ] || exit 0

(
  cd "$D" || exit 0
  enable -f ./memdump.so mem dump 2>/dev/null
  ./setled 0 2>/dev/null
  mem -a 0x40e0002c 0x3f0
  # rainbow fade up & down x2
  for n in 1 2; do
    for c in 0x020 0x370 0x350 0x300 0x3d0 0x0d0 0x3d0 0x300 0x350 0x370; do
      mem -a 0x40e00020 $c; usleep 90000
    done
  done
  # colour comet x2
  for n in 1 2; do
    for c in 0x080 0x040 0x100 0x020 0x200 0x010; do
      mem -a 0x40e00020 $c; usleep 60000
    done
  done
  # strobe + two beeps
  for b in 1 2; do
    mem -a 0x40e00020 0x3f0; mem -a 0x10000048 0x0c0d; usleep 110000
    mem -a 0x10000048 0x0000; mem -a 0x40e00020 0x000; usleep 80000
  done
  # clean release: beeper off, colours off, hand LEDs back to vci-service
  mem -a 0x10000048 0x0000
  mem -a 0x40e00020 0x000
  ./setled 0 2>/dev/null
) >/dev/null 2>&1 &

exit 0
