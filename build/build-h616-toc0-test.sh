#!/usr/bin/env bash
# Build an optional SD TOC0 diagnostic loader with a user-owned key.
# This is a host-only build: it does not write a card, eMMC, or target RAM.
# CHANGE-ID: BOOT TFA AXP313
# T95-CHANGE: the container uses the T95 reference configuration.
# PORTING-NOTE: a caller-owned key does not establish Secure-Boot compatibility.
set -Eeuo pipefail
umask 022

usage() {
  cat <<'EOF'
Aufruf: build/build-h616-toc0-test.sh --key /absoluter/pfad/zum/lokalen-key.pem

Der Schlüssel wird weder erzeugt, kopiert noch veröffentlicht. Ein erzeugter
TOC0-Container kann auf einer fremden H616-Box wegen Secure Boot abgelehnt
werden. Erst docs/FEL_BRINGUP.md und docs/DRAM_PMIC.md vollständig abarbeiten.
EOF
}

[[ ${1:-} == --key && -n ${2:-} && $# == 2 ]] || { usage >&2; exit 2; }
key=$2
[[ $key = /* && -f $key ]] || { echo 'ABBRUCH: --key muss eine vorhandene absolute Datei sein.' >&2; exit 2; }
[[ $(stat -c '%a' "$key") == 600 ]] || { echo 'ABBRUCH: Schlüssel muss Modus 600 haben.' >&2; exit 2; }

project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
uboot_source="$project/build/sources/u-boot"
tfa_source="$project/build/sources/trusted-firmware-a"
patch_file="$project/build/patches/0001-t95-axp313-h616-fel-bringup.patch"
build_id=${T95_BUILD_ID:-h616-toc0-test-$(date +%Y%m%d-%H%M%S)}
work="$project/build/work/$build_id"
artifact="$project/build/artifacts/$build_id"
uboot_work="$work/u-boot"
tfa_build="$work/tf-a"
jobs=${JOBS:-$(nproc)}
readonly uboot_commit=25049ad560826f7dc1c4740883b0016014a59789
readonly tfa_commit=b6c0948400594e3cc4dbb5a4ef04b815d2675808

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
for tool in git make aarch64-linux-gnu-gcc dtc bison flex swig openssl sha256sum cmp; do
  command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done
[[ -d "$uboot_source/.git" && -d "$tfa_source/.git" ]] || die 'Quellen fehlen; zuerst build/fetch-h616-porting-sources.sh ausführen.'
[[ $(git -C "$uboot_source" rev-parse HEAD) == "$uboot_commit" ]] || die 'U-Boot-Revision stimmt nicht.'
[[ $(git -C "$tfa_source" rev-parse HEAD) == "$tfa_commit" ]] || die 'TF-A-Revision stimmt nicht.'
[[ ! -e "$artifact" ]] || die "Artefakt existiert bereits: $artifact"
openssl pkey -in "$key" -check -noout >/dev/null

mkdir -p "$work" "$artifact"
cleanup() { [[ -d "$uboot_work" ]] && git -C "$uboot_source" worktree remove --force "$uboot_work" >/dev/null 2>&1 || true; }
trap cleanup EXIT
git -C "$uboot_source" worktree add --detach "$uboot_work" "$uboot_commit"
git -C "$uboot_work" apply "$patch_file"
install -m 0600 "$key" "$uboot_work/root_key.pem"

make -s -C "$tfa_source" CROSS_COMPILE=aarch64-linux-gnu- PLAT=sun50i_h616 \
  BUILD_BASE="$tfa_build" -j"$jobs" bl31
bl31="$tfa_build/sun50i_h616/release/bl31.bin"
make -s -C "$uboot_work" CROSS_COMPILE=aarch64-linux-gnu- BL31="$bl31" t95_axp313_defconfig
make -s -C "$uboot_work" CROSS_COMPILE=aarch64-linux-gnu- BL31="$bl31" -j"$jobs"

image="$uboot_work/u-boot-sunxi-with-spl.bin"
[[ -f "$image" ]] && printf 'TOC0.GLH' | cmp -n 8 -s - "$image" \
  || die 'Kein TOC0.GLH-Image erzeugt.'
grep -Fxq 'CONFIG_SPL_IMAGE_TYPE_SUNXI_TOC0=y' "$uboot_work/.config" || die 'TOC0-Konfiguration fehlt.'
! grep -Fxq 'CONFIG_MMC_WRITE=y' "$uboot_work/.config" || die 'MMC-Schreiben darf nicht aktiviert sein.'

install -m 0644 "$image" "$artifact/u-boot-sunxi-with-spl.bin"
install -m 0644 "$uboot_work/.config" "$artifact/u-boot.config"
install -m 0644 "$bl31" "$artifact/bl31.bin"
install -m 0644 "$patch_file" "$artifact/0001-t95-axp313-h616-fel-bringup.patch"
openssl pkey -in "$key" -pubout -outform DER 2>/dev/null | sha256sum | awk '{print $1}' > "$artifact/local-key-public-der.sha256"
cat > "$artifact/BUILD-METADATA.txt" <<EOF
purpose=optional autonomous SD TOC0 diagnostic
profile=T95 H616 / AXP313A / DDR3 600 MHz / DCDC3 1360 mV
key=caller-supplied local key; private key excluded
secure_boot_compatibility=unknown; no boot claim
media_write=not performed by this build
hardware_status=not tested by this build
EOF
(cd "$artifact" && sha256sum -- * > SHA256SUMS && sha256sum -c SHA256SUMS)
printf 'ERFOLG: TOC0-Testartefakt: %s\n' "$artifact"
