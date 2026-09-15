#!/usr/bin/env bash
# Prepare the exact, verified Armbian input as regular host files. It never
# opens a block device and never accesses a T95/eMMC.
set -euo pipefail
umask 022

project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_image=${1:-"$project/images/Armbian_26.8.4_Tanix-tx6s-axp313_trixie_current_6.18.48_minimal.img.xz"}
source_xz_sha='f08a37afef45bca2b2a727b2d5e48d1d7521ff533f7ebc0ec03f52ada677870c'
source_raw_sha='30aa502bec70232af756a9be3cd39d0672a03157b156e7421e4080d97411fe27'
rootfs_sha='b19cde604d656071b8a1084acd94fe9f9c2a14606073ce351af78a6d5ec456f2'
raw_bytes=1535115264
partition_start=8192
partition_sectors=2990080
work="${T95_TANIX_WORKDIR:-$project/build/work/tanix-26.8.4-compare}"
raw="$work/tanix-26.8.4-minimal.img"
rootfs="$work/tanix-rootfs.ext4"

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
for tool in awk dd e2fsck mkdir mv rm sha256sum stat xz; do
    command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done
[[ -f "$source_image" ]] || die "Armbian-Eingabe fehlt: $source_image"
[[ $(sha256sum "$source_image" | awk '{print $1}') == "$source_xz_sha" ]] || die 'XZ-Eingabehash stimmt nicht'
xz -t "$source_image"

mkdir -p "$work"
if [[ -e "$raw" || -e "$rootfs" ]]; then
    [[ -f "$raw" && -f "$rootfs" ]] || die 'Unvollständiger vorhandener Arbeitsstand'
    [[ $(sha256sum "$raw" | awk '{print $1}') == "$source_raw_sha" ]] || die 'Vorhandenes Rohimage hat falschen Hash'
    [[ $(sha256sum "$rootfs" | awk '{print $1}') == "$rootfs_sha" ]] || die 'Vorhandenes Rootfs hat falschen Hash'
    printf 'ERFOLG: Bereits vorbereitete, verifizierte Eingabe: %s\n' "$work"
    exit 0
fi

tmp_raw="$raw.partial"
tmp_rootfs="$rootfs.partial"
cleanup() { rm -f "$tmp_raw" "$tmp_rootfs"; }
trap cleanup EXIT

printf 'Entpacke die geprüfte Armbian-Eingabe ausschließlich in %s.\n' "$work"
xz -dc -- "$source_image" > "$tmp_raw"
[[ $(stat -c %s "$tmp_raw") == "$raw_bytes" ]] || die 'Entpacktes Rohimage hat unerwartete Größe'
[[ $(sha256sum "$tmp_raw" | awk '{print $1}') == "$source_raw_sha" ]] || die 'Entpacktes Rohimage hat falschen Hash'

printf 'Extrahiere die einzelne ext4-Partition ausschließlich in eine reguläre Datei.\n'
dd if="$tmp_raw" of="$tmp_rootfs" bs=512 skip="$partition_start" count="$partition_sectors" status=none
[[ $(sha256sum "$tmp_rootfs" | awk '{print $1}') == "$rootfs_sha" ]] || die 'Extrahierte Rootpartition hat falschen Hash'
e2fsck -fn "$tmp_rootfs" >/dev/null || die 'Extrahierte Rootpartition ist nicht lesbar'

mv "$tmp_raw" "$raw"
mv "$tmp_rootfs" "$rootfs"
trap - EXIT
printf 'ERFOLG: Rohimage und Rootpartition sind mit festem Hash vorbereitet.\n'
printf 'Rohimage: %s\nRootfs:   %s\n' "$raw" "$rootfs"
