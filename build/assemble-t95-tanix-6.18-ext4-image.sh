#!/usr/bin/env bash
# Assemble a host-only T95/Tanix 6.18 SD candidate image.
# Every dd destination below is a regular file inside build/artifacts.  This
# script intentionally rejects block devices and does not access T95 eMMC.
set -euo pipefail
umask 022

project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
compare_dir="$project/build/work/tanix-26.8.4-compare"
source_image="$compare_dir/tanix-26.8.4-minimal.img"
source_image_sha='30aa502bec70232af756a9be3cd39d0672a03157b156e7421e4080d97411fe27'
source_rootfs="$compare_dir/tanix-rootfs.ext4"
source_rootfs_sha='b19cde604d656071b8a1084acd94fe9f9c2a14606073ce351af78a6d5ec456f2'
loader_artifact="${T95_LOADER_ARTIFACT:-$project/build/artifacts/t95-ac300-ext4boot-20260914-100400}"
dtb_artifact="${T95_DTB_ARTIFACT:-$project/build/artifacts/t95-tanix-6.18-dtb-20260914-095500}"
loader="$loader_artifact/u-boot-sunxi-with-spl.bin"
dtb_name='sun50i-h616-t95-axp313-tanix-6.18.dtb'
dtb="$dtb_artifact/$dtb_name"
dtb_target="/boot/dtb-6.18.48-current-sunxi64/allwinner/$dtb_name"
partition_offset=4194304
build_id="${T95_BUILD_ID:-t95-tanix-6.18-ext4-image-$(date +%Y%m%d-%H%M%S)}"

[[ "$build_id" =~ ^t95-tanix-6\.18-ext4-image-[0-9]{8}-[0-9]{6}$ ]] || exit 2
artifact="$project/build/artifacts/$build_id"
image="$artifact/t95-tanix-6.18-ext4-diagnostic.img"
rootfs="$artifact/t95-tanix-6.18-rootfs.ext4"
die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
for tool in cp dd debugfs e2fsck fdtget fdisk sfdisk cmp sha256sum stat strings; do
    command -v "$tool" >/dev/null || die "Fehlt: $tool"
done
for input in "$source_image" "$source_rootfs" "$loader" "$dtb"; do
    [[ -f "$input" ]] || die "Eingabe fehlt: $input"
done
[[ $(sha256sum "$source_image" | cut -d' ' -f1) == "$source_image_sha" ]] || die 'Tanix-Rohimage-Hash falsch'
[[ $(sha256sum "$source_rootfs" | cut -d' ' -f1) == "$source_rootfs_sha" ]] || die 'Tanix-Rootfs-Hash falsch'
for input in "$loader_artifact" "$dtb_artifact"; do
    (cd "$input" && sha256sum -c SHA256SUMS >/dev/null) || die "Manifest fehlerhaft: $input"
done
[[ $(head -c 8 "$loader") == TOC0.GLH ]] || die 'Kein T95-TOC0-Loader'
strings -a "$loader" | grep -F 'ext4load mmc 0:1 ${scriptaddr} /boot/boot.scr' >/dev/null || die 'Loader hat keinen ext4-Bootvertrag'
fdtget -ts "$dtb" / model | grep -Fxq 'T95 H616 AXP313A (Tanix 6.18 candidate)' || die 'Kein T95-6.18-DTB-Kandidat'

mkdir -p "$artifact"
[[ ! -e "$artifact/SHA256SUMS" ]] || die 'Fertiges Artefakt wird nicht überschrieben'

# Copies first: all later writes are to artifact-local regular files.
cp --reflink=auto "$source_image" "$image"
cp --reflink=auto "$source_rootfs" "$rootfs"
[[ -f "$image" && ! -b "$image" ]] || die 'Zielimage ist keine reguläre Datei'
[[ -f "$rootfs" && ! -b "$rootfs" ]] || die 'Zielrootfs ist keine reguläre Datei'

debugfs -R "dump -p /boot/boot.scr $artifact/source-boot.scr" "$source_rootfs" 2>/dev/null
debugfs -R "dump -p /boot/armbianEnv.txt $artifact/source-armbianEnv.txt" "$source_rootfs" 2>/dev/null
rootdev=$(sed -n 's/^rootdev=UUID=//p' "$artifact/source-armbianEnv.txt")
[[ "$rootdev" =~ ^[0-9a-fA-F-]{36}$ ]] || die 'Unerwartete Root-UUID im Tanix-Image'

cat > "$artifact/armbianEnv.txt" <<EOF
verbosity=7
bootlogo=false
console=serial
overlay_prefix=sun50i-h616
rootdev=UUID=$rootdev
rootfstype=ext4
fdtfile=$dtb_name
extraargs=clk_ignore_unused nohz=off
EOF

# The target directory exists in the verified source rootfs.  debugfs only
# changes our copied ext4 file, then the complete partition copy is inserted
# into our copied regular image file.
debugfs -w -R "write $dtb $dtb_target" "$rootfs" >/dev/null 2>&1
debugfs -w -R 'rm /boot/armbianEnv.txt' "$rootfs" >/dev/null 2>&1
debugfs -w -R "write $artifact/armbianEnv.txt /boot/armbianEnv.txt" "$rootfs" >/dev/null 2>&1

debugfs -R "stat $dtb_target" "$rootfs" 2>/dev/null | grep 'Type: regular' >/dev/null || die 'Kandidaten-DTB fehlt im Rootfs'
debugfs -R 'cat /boot/armbianEnv.txt' "$rootfs" 2>/dev/null | cmp -s - "$artifact/armbianEnv.txt" || die 'armbianEnv-Ruecklesung weicht ab'
e2fsck -fn "$rootfs" >/dev/null || die 'Lokale zusammengesetzte Rootpartition ist nicht pruefbar'

rootfs_size=$(stat -c %s "$rootfs")
[[ $rootfs_size -eq 1530920960 ]] || die 'Unerwartete Rootfs-Groesse'
[[ $((rootfs_size % 4194304)) -eq 0 ]] || die 'Rootfs ist nicht MiB-ausgerichtet'
rootfs_mib_blocks=$((rootfs_size / 4194304))
dd if="$rootfs" of="$image" bs=4M seek=1 count="$rootfs_mib_blocks" conv=notrunc,fsync status=none
dd if="$loader" of="$image" bs=1 seek=8192 conv=notrunc,fsync status=none

# Read every changed range back from the candidate image.
cmp "$loader" <(dd if="$image" bs=1 skip=8192 count="$(stat -c %s "$loader")" status=none) || die 'TOC0-Ruecklesung fehlgeschlagen'
cmp "$rootfs" <(dd if="$image" bs=4M skip=1 count="$rootfs_mib_blocks" status=none) || die 'Rootpartition-Ruecklesung fehlgeschlagen'
# sfdisk -d includes the different regular-file names in its textual output;
# compare the actual MBR sector rather than that presentation-only field.
cmp <(dd if="$source_image" bs=512 count=1 status=none) <(dd if="$image" bs=512 count=1 status=none) || die 'MBR wurde veraendert'

install -m 0644 "$loader" "$artifact/u-boot-sunxi-with-spl.bin"
install -m 0644 "$dtb" "$artifact/$dtb_name"
cat > "$artifact/ASSEMBLY.txt" <<EOF
scope=host_only_regular_files; no_SD_or_eMMC_write
base_image=$(basename "$source_image")
base_image_sha256=$source_image_sha
loader=u-boot-sunxi-with-spl.bin
loader_offset_bytes=8192
loader_header=TOC0.GLH
partition_1_offset_bytes=$partition_offset
partition_1_filesystem=ext4
boot_script=/boot/boot.scr
dtb_target=$dtb_target
rootfs_uuid=$rootdev
diagnostic_kernel_args=clk_ignore_unused nohz=off
EOF
install -m 0644 "${BASH_SOURCE[0]}" "$artifact/build-recipe.sh"
{
    printf 'board=H616-T95MAX-AXP313A-V3.0\n'
    printf 'kernel_release=6.18.48-current-sunxi64\n'
    printf 'status=BUILT_NOT_HARDWARE_TESTED\n'
    printf 'scope=host-only T95 TOC0 loader + T95-labelled 6.18 DTB + Tanix rootfs\n'
    printf 'source_image_sha256=%s\nsource_rootfs_sha256=%s\n' "$source_image_sha" "$source_rootfs_sha"
    printf 'loader_sha256=%s\ndtb_sha256=%s\n' "$(sha256sum "$loader" | cut -d' ' -f1)" "$(sha256sum "$dtb" | cut -d' ' -f1)"
    printf 'sd_write=not_performed\nemmc_write=not_performed\n'
} > "$artifact/BUILD-METADATA.txt"
(cd "$artifact" && sha256sum -- * > SHA256SUMS && sha256sum -c SHA256SUMS)
printf 'Artefakt: %s\n' "$artifact"
