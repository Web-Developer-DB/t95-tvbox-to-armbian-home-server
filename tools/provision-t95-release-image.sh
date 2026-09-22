#!/usr/bin/env bash
# Create a local, non-public copy of a generic T95 image with a user-chosen
# root password hash. It modifies regular image files only; no SD, FEL or
# eMMC device is opened here.
# CHANGE-ID: HARDEN
# T95-CHANGE: personalize the locked generic image only in a local file.
# PORTING-NOTE: never publish the resulting image or its password manifest.
set -euo pipefail
umask 077

generic_image=${1:-}
personal_image=${2:-}
confirmation=${3:-}
expected_confirmation='PROVISION-T95-ROOT-PASSWORD'
partition_offset=4194304

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
[[ $# -eq 3 ]] || die "Aufruf: $0 GENERISCHES_IMAGE.img PERSOENLICHES_IMAGE.img $expected_confirmation"
[[ "$confirmation" == "$expected_confirmation" ]] || die 'Bestätigungstoken stimmt nicht'
[[ -f "$generic_image" && ! -b "$generic_image" && ! -L "$generic_image" ]] || die 'Generisches Image muss eine reguläre Datei sein'
[[ ! -e "$personal_image" && ! -b "$personal_image" && ! -L "$personal_image" ]] || die 'Persönliches Zielimage existiert bereits. Neuen Dateinamen wählen oder die vorhandene Kopie im Ein-Skript-Installer wiederverwenden.'
for tool in awk chmod cmp cp dd debugfs e2fsck head mktemp openssl rm sha256sum stat sync; do
    command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done

image_size=$(stat -c %s "$generic_image")
[[ "$image_size" =~ ^[0-9]+$ && "$image_size" -gt "$partition_offset" && $((image_size % 4194304)) -eq 0 ]] \
    || die 'Generisches Image hat keine erwartete T95-Ausrichtung'
[[ $(head -c 8 <(dd if="$generic_image" bs=1 skip=8192 count=8 status=none)) == TOC0.GLH ]] \
    || die 'Generisches Image enthält keinen erwarteten TOC0-Loader'
rootfs_size=$((image_size - partition_offset))
rootfs_blocks=$((rootfs_size / 4194304))

if { : < /dev/tty; } 2>/dev/null; then
    prompt_input=/dev/tty
elif [[ -t 0 ]]; then
    # Some terminal emulators expose no /dev/tty but keep stdin interactive.
    prompt_input=/dev/stdin
else
    die 'Passwortabfrage benötigt ein interaktives Terminal; keine Passwort-Pipe verwenden'
fi
printf 'Neues Root-Passwort für die lokale SD-Kopie eingeben (beliebige Länge, nicht leer).\n' >&2
IFS= read -r -s -p 'Passwort: ' password < "$prompt_input"
printf '\n' >&2
IFS= read -r -s -p 'Passwort wiederholen: ' password_confirm < "$prompt_input"
printf '\n' >&2
[[ -n "$password" ]] || die 'Passwort darf nicht leer sein'
[[ "$password" == "$password_confirm" ]] || die 'Passwörter stimmen nicht überein'
root_hash=$(printf '%s' "$password" | openssl passwd -6 -stdin)
unset password password_confirm
[[ "$root_hash" == \$6\$* ]] || die 'SHA-512-Passworthash konnte nicht erzeugt werden'

work=$(mktemp -d "${TMPDIR:-/tmp}/t95-provision.XXXXXX")
cleanup() { rm -rf -- "$work"; }
trap cleanup EXIT
rootfs="$work/rootfs.ext4"
cp --reflink=auto "$generic_image" "$personal_image"
chmod 0600 "$personal_image"
dd if="$personal_image" of="$rootfs" bs=4M skip=1 count="$rootfs_blocks" conv=fsync status=none
e2fsck -fn "$rootfs" >/dev/null || die 'Generische Rootpartition ist nicht prüfbar'

debugfs -R 'cat /etc/shadow' "$rootfs" 2>/dev/null > "$work/shadow.before"
awk -F: 'BEGIN { ok=0 } $1 == "root" { ok=($2 == "!"); exit } END { exit ok ? 0 : 1 }' "$work/shadow.before" \
    || die 'Eingabe ist kein gesperrtes generisches Release-Image'
printf '%s' "$root_hash" > "$work/root-hash"
chmod 0600 "$work/shadow.before" "$work/root-hash"
awk -F: 'NR == FNR { hash=$0; next } BEGIN { OFS=":"; found=0 } $1 == "root" { $2=hash; found=1 } { print } END { exit found ? 0 : 1 }' \
    "$work/root-hash" "$work/shadow.before" > "$work/shadow.personalized"
chmod 0600 "$work/shadow.personalized"
debugfs -w -R 'rm /etc/shadow' "$rootfs" >/dev/null 2>&1
debugfs -w -R "write $work/shadow.personalized /etc/shadow" "$rootfs" >/dev/null 2>&1
debugfs -R 'cat /etc/shadow' "$rootfs" 2>/dev/null > "$work/shadow.after"
awk -F: 'BEGIN { ok=0 } $1 == "root" { ok=($2 ~ /^\$6\$/); exit } END { exit ok ? 0 : 1 }' "$work/shadow.after" \
    || die 'Persönlicher Root-Passworthash wurde nicht korrekt eingesetzt'

dd if="$rootfs" of="$personal_image" bs=4M seek=1 count="$rootfs_blocks" conv=notrunc,fsync status=none
cmp "$rootfs" <(dd if="$personal_image" bs=4M skip=1 count="$rootfs_blocks" status=none) \
    || die 'Persönliche Rootpartition wurde nicht korrekt zurückgelesen'
e2fsck -fn "$rootfs" >/dev/null || die 'Personalisierte Rootpartition ist nicht prüfbar'
personal_sha=$(sha256sum "$personal_image" | awk '{print $1}')
generic_sha=$(sha256sum "$generic_image" | awk '{print $1}')
manifest="$personal_image.t95-provisioned-manifest"
{
    printf '%s\n' 'format=T95-PROVISIONED-IMAGE-1'
    printf 'generic_image_sha256=%s\n' "$generic_sha"
    printf 'personalized_image_filename=%s\n' "$(basename "$personal_image")"
    printf 'personalized_image_size=%s\n' "$image_size"
    printf 'personalized_image_sha256=%s\n' "$personal_sha"
    printf '%s\n' 'root_password_hash=excluded'
    printf '%s\n' 'ssh_host_keys=generated_on_target_before_ssh_service'
    printf '%s\n' 'purpose=local_only_not_a_public_release_asset'
} > "$manifest"
chmod 0600 "$manifest"
sync
printf 'ERFOLG: persönliche lokale Image-Kopie erzeugt.\n'
printf 'Image: %s\nManifest: %s\n' "$personal_image" "$manifest"
printf 'Diese zwei Dateien nicht veröffentlichen oder in Git einchecken.\n'
