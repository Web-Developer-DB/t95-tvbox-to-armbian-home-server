#!/usr/bin/env bash
# Write a verified public T95 release asset to one removable USB SD card.
# The script deliberately has no eMMC, FEL or Android path.
set -euo pipefail
umask 022

device=${1:-}
release_dir=${2:-}
confirmation=${3:-}
expected_confirmation='WRITE-T95-RELEASE-TO-SDX'
asset_prefix='T95-H616-AXP313A-Armbian-26.8.4-6.18.48-'

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
[[ $# -eq 3 ]] || die "Aufruf: $0 /dev/sdX RELEASE_ORDNER $expected_confirmation"
[[ "$device" =~ ^/dev/sd[a-z]+$ ]] || die 'Ziel muss genau /dev/sdX sein'
[[ -b "$device" ]] || die 'Zielblockgerät fehlt'
[[ -d "$release_dir" && -f "$release_dir/RELEASE-MANIFEST.txt" && -f "$release_dir/SHA256SUMS" ]] || die 'Release-Ordner oder Manifest fehlt'
[[ "$confirmation" == "$expected_confirmation" ]] || die 'Bestätigungstoken stimmt nicht'

for tool in awk dd e2fsck findmnt grep lsblk partprobe sed sha256sum sudo sync udevadm umount wc xz; do
    command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done

manifest="$release_dir/RELEASE-MANIFEST.txt"
release_id=$(sed -n 's/^release_id=//p' "$manifest")
compressed_name=$(sed -n 's/^image_compressed=//p' "$manifest")
expected_raw_size=$(sed -n 's/^image_uncompressed_size=//p' "$manifest")
expected_raw_sha=$(sed -n 's/^image_uncompressed_sha256=//p' "$manifest")
expected_header=$(sed -n 's/^loader_header=//p' "$manifest")
image_state=$(sed -n 's/^image_state=//p' "$manifest")
[[ "$release_id" =~ ^v[0-9]+\.[0-9]+\.[0-9]+-[a-z0-9.-]+$ ]] || die 'Ungültige Release-ID im Manifest'
[[ "$compressed_name" == "$asset_prefix"*".img.xz" ]] || die 'Unerwarteter Asset-Dateiname im Manifest'
[[ "$expected_raw_size" =~ ^[0-9]+$ && "$expected_raw_sha" =~ ^[0-9a-f]{64}$ && "$expected_header" == TOC0.GLH ]] || die 'Unvollständiges oder ungültiges Manifest'
[[ $((expected_raw_size % 4194304)) == 0 ]] || die 'Imagegröße ist nicht 4-MiB-ausgerichtet'
[[ "$image_state" != generic_root_locked* ]] || die 'Dieses öffentliche Image ist absichtlich root-gesperrt. Erst lokal mit tools/provision-t95-release-image.sh personalisieren und danach tools/write-t95-provisioned-image-to-sd.sh verwenden.'
image="$release_dir/$compressed_name"
[[ -f "$image" ]] || die 'Komprimiertes Release-Image fehlt'

(cd "$release_dir" && sha256sum -c SHA256SUMS) || die 'Release-Prüfsummen fehlerhaft'
xz -t "$image"
actual_raw_sha=$(xz -dc -- "$image" | sha256sum | awk '{print $1}')
[[ "$actual_raw_sha" == "$expected_raw_sha" ]] || die 'Entpacktes Release-Image hat falschen Hash'
actual_raw_size=$(xz -dc -- "$image" | wc -c | awk '{print $1}')
[[ "$actual_raw_size" == "$expected_raw_size" ]] || die 'Entpacktes Release-Image hat falsche Größe'

size=$(lsblk -dnbo SIZE "$device")
transport=$(lsblk -dno TRAN "$device" | sed 's/[[:space:]]*$//')
removable=$(lsblk -dno RM "$device" | sed 's/[[:space:]]*$//')
kind=$(lsblk -dno TYPE "$device" | sed 's/[[:space:]]*$//')
[[ "$size" =~ ^[0-9]+$ && "$size" -gt "$expected_raw_size" ]] || die 'Ziel ist kleiner als das Release-Image'
[[ "$transport" == usb && "$removable" == 1 && "$kind" == disk ]] || die 'Ziel ist keine wechselbare USB-SD-Karte'

while IFS= read -r partition; do
    [[ "$partition" == "$device" ]] && continue
    if findmnt -rn -S "$partition" -o TARGET | grep -Fxq /; then
        die 'Das Ziel enthält das laufende Root-Dateisystem'
    fi
done < <(lsblk -nrpo NAME "$device")

printf '%s\n' 'Sicherheitsprüfung bestanden:'
printf '  Release:     %s\n' "$release_id"
printf '  Image:       %s\n' "$compressed_name"
printf '  Ziel:        %s (%s Byte, USB, wechselbar)\n' "$device" "$size"
printf '  Wirkung:     Der bisherige Inhalt von %s wird vollständig überschrieben.\n' "$device"
printf '  Ausgeschlossen: interne T95-eMMC, FEL und Android-Speicher.\n'

sudo -v
while IFS= read -r partition; do
    [[ "$partition" == "$device" ]] && continue
    if findmnt -nr -S "$partition" >/dev/null; then
        printf 'Hänge %s aus.\n' "$partition"
        sudo umount "$partition"
    fi
done < <(lsblk -nrpo NAME "$device")

printf 'Schreibe das vorab vollständig geprüfte Image nach %s.\n' "$device"
xz -dc -- "$image" | sudo dd of="$device" bs=4M conv=fsync status=progress
sync
sudo partprobe "$device"
sudo udevadm settle

blocks=$((expected_raw_size / 4194304))
readback_sha=$(sudo dd if="$device" bs=4M count="$blocks" status=none | sha256sum | awk '{print $1}')
[[ "$readback_sha" == "$expected_raw_sha" ]] || die 'Rückgelesenes SD-Image hat falschen Hash'
[[ $(sudo dd if="$device" bs=1 skip=8192 count=8 status=none) == "$expected_header" ]] || die 'TOC0-Header fehlt nach Schreiben'
sudo e2fsck -fn "${device}1" >/dev/null || die 'Geschriebenes ext4-Dateisystem ist nicht prüfbar'

printf '\nERFOLG: Release-Image wurde vollständig zurückgelesen und geprüft.\n'
printf 'Karte nur bei ausgeschalteter T95 einsetzen oder entnehmen.\n'
