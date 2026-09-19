#!/usr/bin/env bash
# Build a RAM-only eGON FEL diagnostic loader for the documented T95 profile.
# This script never invokes sunxi-fel and never accesses any block device.
# CHANGE-ID: BOOT TFA AXP313
# T95-CHANGE: apply T95 AXP313/DDR3-600 board parameters to the diagnostic SPL.
# PORTING-NOTE: PMIC and DRAM values must be independently proven on another board.
set -Eeuo pipefail
umask 022

project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
uboot_source="$project/build/sources/u-boot"
tfa_source="$project/build/sources/trusted-firmware-a"
patch_file="$project/build/patches/0001-t95-axp313-h616-fel-bringup.patch"
build_id=${T95_BUILD_ID:-h616-fel-egon-$(date +%Y%m%d-%H%M%S)}
work="$project/build/work/$build_id"
artifact="$project/build/artifacts/$build_id"
uboot_work="$work/u-boot"
tfa_build="$work/tf-a"
jobs=${JOBS:-$(nproc)}
readonly uboot_commit=25049ad560826f7dc1c4740883b0016014a59789
readonly tfa_commit=b6c0948400594e3cc4dbb5a4ef04b815d2675808

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
for tool in git make aarch64-linux-gnu-gcc dtc bison flex swig openssl sha256sum cmp dd; do
  command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done
[[ -d "$uboot_source/.git" && -d "$tfa_source/.git" ]] || die 'Quellen fehlen; zuerst build/fetch-h616-porting-sources.sh ausführen.'
[[ -f "$patch_file" ]] || die 'T95-Patch fehlt.'
[[ $(git -C "$uboot_source" rev-parse HEAD) == "$uboot_commit" ]] || die 'U-Boot-Revision stimmt nicht.'
[[ $(git -C "$tfa_source" rev-parse HEAD) == "$tfa_commit" ]] || die 'TF-A-Revision stimmt nicht.'
[[ -z $(git -C "$uboot_source" status --porcelain) ]] || die 'U-Boot-Quellbaum ist nicht sauber.'
[[ -z $(git -C "$tfa_source" status --porcelain) ]] || die 'TF-A-Quellbaum ist nicht sauber.'
[[ ! -e "$artifact" ]] || die "Artefakt existiert bereits: $artifact"

mkdir -p "$work" "$artifact"
cleanup() { [[ -d "$uboot_work" ]] && git -C "$uboot_source" worktree remove --force "$uboot_work" >/dev/null 2>&1 || true; }
trap cleanup EXIT
git -C "$uboot_source" worktree add --detach "$uboot_work" "$uboot_commit"
git -C "$uboot_work" apply "$patch_file"

make -s -C "$tfa_source" CROSS_COMPILE=aarch64-linux-gnu- PLAT=sun50i_h616 \
  BUILD_BASE="$tfa_build" -j"$jobs" bl31
bl31="$tfa_build/sun50i_h616/release/bl31.bin"
[[ -f "$bl31" ]] || die 'TF-A erzeugte kein bl31.bin.'
make -s -C "$uboot_work" CROSS_COMPILE=aarch64-linux-gnu- BL31="$bl31" t95_axp313_fel_defconfig
make -s -C "$uboot_work" CROSS_COMPILE=aarch64-linux-gnu- BL31="$bl31" -j"$jobs"

image="$uboot_work/u-boot-sunxi-with-spl.bin"
[[ -f "$image" ]] && printf 'eGON.BT0' | \
  cmp -s - <(dd if="$image" bs=1 skip=4 count=8 status=none) \
  || die 'Kein eGON.BT0-FEL-Image erzeugt.'
grep -Fxq 'CONFIG_SPL_IMAGE_TYPE_SUNXI_EGON=y' "$uboot_work/.config" || die 'eGON-Konfiguration fehlt.'
! grep -Fxq 'CONFIG_MMC_WRITE=y' "$uboot_work/.config" || die 'MMC-Schreiben darf nicht aktiviert sein.'

install -m 0644 "$image" "$artifact/u-boot-sunxi-with-spl.bin"
install -m 0644 "$uboot_work/.config" "$artifact/u-boot.config"
install -m 0644 "$bl31" "$artifact/bl31.bin"
install -m 0644 "$patch_file" "$artifact/0001-t95-axp313-h616-fel-bringup.patch"
printf '%s\n' "$uboot_commit" > "$artifact/u-boot.commit"
printf '%s\n' "$tfa_commit" > "$artifact/tf-a.commit"
cat > "$artifact/BUILD-METADATA.txt" <<EOF
purpose=RAM-only eGON FEL diagnostic
profile=T95 H616 / AXP313A / DDR3 600 MHz / DCDC3 1360 mV
media_write=not performed by this build
fel_upload=not performed by this build
toc0_key=not used
hardware_status=not tested by this build
EOF
(cd "$artifact" && sha256sum -- * > SHA256SUMS && sha256sum -c SHA256SUMS)
printf 'ERFOLG: eGON-FEL-Artefakt: %s\n' "$artifact"
