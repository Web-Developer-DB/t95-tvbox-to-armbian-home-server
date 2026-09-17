#!/usr/bin/env bash
# Create a public, generic T95 release image from a private pre-first-boot
# artifact.  All writes target regular files below build/artifacts and
# build/work; this script never opens a block device, FEL or the T95 eMMC.
# CHANGE-ID: HARDEN
# T95-CHANGE: remove machine-specific credentials and enforce first-boot key setup.
# PORTING-NOTE: repeat the read-only audit after every rootfs or init-system change.
set -euo pipefail
umask 077

project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_artifact=${T95_HARDEN_SOURCE_ARTIFACT:-"$project/build/artifacts/t95-tanix-6.18-ext4-image-20260914-101300"}
source_image_name='t95-tanix-6.18-ext4-diagnostic.img'
image_name='t95-tanix-6.18-hardened-generic.img'
partition_offset=4194304
build_id=${1:-"t95-tanix-6.18-hardened-$(date +%Y%m%d-%H%M%S)"}
artifact="$project/build/artifacts/$build_id"
work_root="$project/build/work"

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
[[ "$build_id" =~ ^t95-tanix-6\.18-hardened-[0-9]{8}-[0-9]{6}$ ]] || die 'Build-ID ist ungültig'
[[ -d "$source_artifact" && -f "$source_artifact/SHA256SUMS" ]] || die 'Quellartefakt oder Manifest fehlt'
[[ ! -e "$artifact" ]] || die "Ausgabe existiert bereits: $artifact"

for tool in awk chmod cmp cp dd debugfs dumpe2fs e2fsck find grep head install mkdir mktemp rm sed sha256sum sort stat tune2fs xargs; do
    command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done

(cd "$source_artifact" && sha256sum -c SHA256SUMS) >/dev/null || die 'Quellartefakt-Prüfsummen fehlerhaft'
source_image="$source_artifact/$source_image_name"
loader="$source_artifact/u-boot-sunxi-with-spl.bin"
dtb="$source_artifact/sun50i-h616-t95-axp313-tanix-6.18.dtb"
for input in "$source_image" "$loader" "$dtb"; do
    [[ -f "$input" && ! -b "$input" ]] || die "Reguläre Eingabedatei fehlt: $input"
done
[[ $(head -c 8 "$loader") == TOC0.GLH ]] || die 'Quellloader hat keinen TOC0-Header'

source_size=$(stat -c %s "$source_image")
[[ "$source_size" =~ ^[0-9]+$ && "$source_size" -gt "$partition_offset" ]] || die 'Quellimagegröße ist ungültig'
[[ $((source_size % 4194304)) -eq 0 ]] || die 'Quellimage ist nicht 4-MiB-ausgerichtet'
rootfs_size=$((source_size - partition_offset))
[[ $((rootfs_size % 4194304)) -eq 0 ]] || die 'Rootpartition ist nicht 4-MiB-ausgerichtet'
rootfs_blocks=$((rootfs_size / 4194304))

mkdir -p "$artifact" "$work_root"
work=$(mktemp -d "$work_root/t95-release-hardening.XXXXXX")
cleanup() { rm -rf -- "$work"; }
trap cleanup EXIT

image="$artifact/$image_name"
rootfs="$work/rootfs.ext4"
cp --reflink=auto "$source_image" "$image"
dd if="$image" of="$rootfs" bs=4M skip=1 count="$rootfs_blocks" conv=fsync status=none
[[ -f "$image" && ! -b "$image" && -f "$rootfs" && ! -b "$rootfs" ]] || die 'Arbeitsdatei ist kein reguläres Image'
e2fsck -fn "$rootfs" >/dev/null || die 'Quell-Rootpartition ist nicht prüfbar'

# Read the inherited root hash only to prove later that no trace is left in the
# finished raw image.  It is never printed or copied into the public artifact.
debugfs -R 'cat /etc/shadow' "$rootfs" 2>/dev/null > "$work/shadow.before"
source_root_hash=$(awk -F: '$1 == "root" { print $2; exit }' "$work/shadow.before")
[[ ${#source_root_hash} -ge 20 && "$source_root_hash" != '!' && "$source_root_hash" != '*' ]] || die 'Quellimage enthält keinen erwarteten sperrbaren Root-Hash'
awk -F: 'BEGIN { OFS=":"; found=0 } $1 == "root" { $2="!"; found=1 } { print } END { exit found ? 0 : 1 }' \
    "$work/shadow.before" > "$work/shadow.locked"
chmod 0600 "$work/shadow.before" "$work/shadow.locked"

# Retain source-key payloads only in the private temporary directory.  Header
# text alone also occurs in the OpenSSH executable, so random base64 payload
# lines are the precise, non-ambiguous scrub needles.
source_private_key_patterns=()
for source_key in /etc/ssh/ssh_host_rsa_key /etc/ssh/ssh_host_ecdsa_key /etc/ssh/ssh_host_ed25519_key; do
    key_file="$work/$(basename "$source_key")"
    debugfs -R "dump -p $source_key $key_file" "$rootfs" 2>/dev/null \
        || die "Privater Quellhostkey fehlt: $source_key"
    chmod 0600 "$key_file"
    patterns_file="$key_file.payload-lines"
    awk 'length($0) >= 48' "$key_file" > "$patterns_file"
    [[ -s "$patterns_file" ]] || die "Quellhostkey enthält keine prüfbaren Payload-Zeilen: $source_key"
    chmod 0600 "$patterns_file"
    source_private_key_patterns+=("$patterns_file")
done

debugfs -R "dump -p /etc/default/armbian-firstrun $work/armbian-firstrun.before" "$rootfs" 2>/dev/null \
    || die 'Armbian-Erststartkonfiguration fehlt'
[[ $(grep -Fxc 'OPENSSHD_REGENERATE_HOST_KEYS=true' "$work/armbian-firstrun.before") == 1 ]] \
    || die 'Unerwartete Armbian-Hostkey-Konfiguration'
sed 's/^OPENSSHD_REGENERATE_HOST_KEYS=true$/OPENSSHD_REGENERATE_HOST_KEYS=false/' \
    "$work/armbian-firstrun.before" > "$work/armbian-firstrun.hardened"

cat > "$work/t95-initialize-ssh-hostkeys" <<'EOF'
#!/bin/sh
# This runs as an ssh.service requirement.  A public image therefore contains
# no reusable server identity; each target generates its own keys before sshd
# is allowed to start.
set -eu
state=/var/lib/t95-release/ssh-hostkeys-initialized

if [ -e "$state" ]; then
    exit 0
fi

rm -f /etc/ssh/ssh_host_*
umask 077
/usr/bin/ssh-keygen -A
test -s /etc/ssh/ssh_host_ed25519_key
install -d -m 0700 /var/lib/t95-release
: > "$state"
EOF
cat > "$work/t95-hostkeys.service" <<'EOF'
[Unit]
Description=Generate unique SSH host keys for T95 release image
After=local-fs.target
Before=ssh.service

[Service]
Type=oneshot
ExecStart=/usr/lib/t95-release/t95-initialize-ssh-hostkeys
EOF
cat > "$work/10-t95-hostkeys.conf" <<'EOF'
[Unit]
Requires=t95-hostkeys.service
After=t95-hostkeys.service
EOF
chmod 0755 "$work/t95-initialize-ssh-hostkeys"
chmod 0644 "$work/t95-hostkeys.service" "$work/10-t95-hostkeys.conf" "$work/armbian-firstrun.hardened"

remove_path() {
    debugfs -w -R "rm $1" "$rootfs" >/dev/null 2>&1 || true
}
write_path() {
    local source=$1 destination=$2
    remove_path "$destination"
    debugfs -w -R "write $source $destination" "$rootfs" >/dev/null 2>&1
}
ensure_directory() {
    local directory=$1
    if ! debugfs -R "stat $directory" "$rootfs" 2>/dev/null | grep -Fq 'Inode:'; then
        debugfs -w -R "mkdir $directory" "$rootfs" >/dev/null 2>&1
    fi
    debugfs -R "stat $directory" "$rootfs" 2>/dev/null | grep -Fq 'Inode:' \
        || die "Arbeitsverzeichnis fehlt: $directory"
}

# Remove every source key, the account backup that still contains the old
# root hash, then add the pre-sshd generator and its strict dependency.
for key in \
    /etc/ssh/ssh_host_rsa_key /etc/ssh/ssh_host_rsa_key.pub \
    /etc/ssh/ssh_host_ecdsa_key /etc/ssh/ssh_host_ecdsa_key.pub \
    /etc/ssh/ssh_host_ed25519_key /etc/ssh/ssh_host_ed25519_key.pub \
    /etc/shadow- /etc/gshadow-; do
    remove_path "$key"
done
ensure_directory /usr/lib/t95-release
ensure_directory /etc/systemd/system/ssh.service.d
write_path "$work/shadow.locked" /etc/shadow
write_path "$work/armbian-firstrun.hardened" /etc/default/armbian-firstrun
write_path "$work/t95-initialize-ssh-hostkeys" /usr/lib/t95-release/t95-initialize-ssh-hostkeys
write_path "$work/t95-hostkeys.service" /etc/systemd/system/t95-hostkeys.service
write_path "$work/10-t95-hostkeys.conf" /etc/systemd/system/ssh.service.d/10-t95-hostkeys.conf
debugfs -w -R 'sif /usr/lib/t95-release/t95-initialize-ssh-hostkeys mode 0100755' "$rootfs" >/dev/null 2>&1

# Recreate the journal, then fill and unlink almost all currently free blocks.
# This prevents unlinked source host keys and the inherited password hash from
# surviving in a publicly distributed raw filesystem image.
e2fsck -fy "$rootfs" >/dev/null
tune2fs -O ^has_journal "$rootfs" >/dev/null
e2fsck -fy "$rootfs" >/dev/null
tune2fs -j "$rootfs" >/dev/null
e2fsck -fy "$rootfs" >/dev/null
block_size=$(dumpe2fs -h "$rootfs" 2>/dev/null | awk -F: '/Block size:/ { gsub(/ /, "", $2); print $2; exit }')
free_blocks=$(dumpe2fs -h "$rootfs" 2>/dev/null | awk -F: '/Free blocks:/ { gsub(/ /, "", $2); print $2; exit }')
[[ "$block_size" =~ ^[0-9]+$ && "$free_blocks" =~ ^[0-9]+$ && "$free_blocks" -gt 1024 ]] \
    || die 'Freie Ext4-Blöcke konnten nicht sicher bestimmt werden'
filler_blocks=$((free_blocks - 512))
dd if=/dev/zero of="$work/zero-fill" bs="$block_size" count="$filler_blocks" status=none
debugfs -w -R "write $work/zero-fill /t95-release-free-space-scrub" "$rootfs" >/dev/null 2>&1
debugfs -w -R 'rm /t95-release-free-space-scrub' "$rootfs" >/dev/null 2>&1
rm -f "$work/zero-fill"

# Ext4 may choose a small set of free blocks outside a bulk fill.  Locate each
# known inherited secret without displaying it, ensure its block is free, and
# zero the exact blocks.  This is intentionally followed by a raw-image scan.
scrub_free_blocks_containing() {
    local marker=$1 label=$2 marker_length=${#1} offset first_block last_block block state
    printf '%s' "$marker" > "$work/one-secret-pattern"
    LC_ALL=C grep -aboF -f "$work/one-secret-pattern" "$rootfs" | cut -d: -f1 > "$work/secret-offsets" || true
    while IFS= read -r offset; do
        [[ "$offset" =~ ^[0-9]+$ ]] || continue
        first_block=$((offset / block_size))
        last_block=$(((offset + marker_length - 1) / block_size))
        for ((block=first_block; block<=last_block; block++)); do
            state=$(debugfs -R "testb $block" "$rootfs" 2>/dev/null || true)
            [[ "$state" == *'not in use'* ]] || die "Sensibles Quellmaterial ($label) liegt unerwartet in einem belegten Ext4-Block"
            dd if=/dev/zero of="$rootfs" bs="$block_size" seek="$block" count=1 conv=notrunc status=none
        done
    done < "$work/secret-offsets"
    : > "$work/secret-offsets"
}
scrub_free_blocks_matching_patterns() {
    local pattern_file=$1 label=$2 offset first_block block state
    LC_ALL=C grep -aboF -f "$pattern_file" "$rootfs" | cut -d: -f1 > "$work/secret-offsets" || true
    while IFS= read -r offset; do
        [[ "$offset" =~ ^[0-9]+$ ]] || continue
        first_block=$((offset / block_size))
        state=$(debugfs -R "testb $first_block" "$rootfs" 2>/dev/null || true)
        [[ "$state" == *'not in use'* ]] || die "Sensibles Quellmaterial ($label) liegt unerwartet in einem belegten Ext4-Block"
        dd if=/dev/zero of="$rootfs" bs="$block_size" seek="$first_block" count=1 conv=notrunc status=none
    done < "$work/secret-offsets"
    : > "$work/secret-offsets"
}
scrub_free_blocks_containing "$source_root_hash" root-hash
for patterns_file in "${source_private_key_patterns[@]}"; do
    scrub_free_blocks_matching_patterns "$patterns_file" private-hostkey-payload
done
e2fsck -fy "$rootfs" >/dev/null

# Functional checks do not print the inherited credential or any source keys.
debugfs -R 'cat /etc/shadow' "$rootfs" 2>/dev/null > "$work/shadow.after"
awk -F: 'BEGIN { ok=0 } $1 == "root" { ok=($2 == "!"); exit } END { exit ok ? 0 : 1 }' \
    "$work/shadow.after" || die 'Rootkonto ist im generischen Image nicht gesperrt'
grep -Fqx 'OPENSSHD_REGENERATE_HOST_KEYS=false' "$work/armbian-firstrun.hardened" \
    || die 'Armbian darf die Vor-SSH-Hostkeys nicht ersetzen'
debugfs -R 'stat /usr/lib/t95-release/t95-initialize-ssh-hostkeys' "$rootfs" 2>/dev/null | grep -Fq 'Mode:  0755' \
    || die 'Hostkey-Generator ist nicht ausführbar'
for key in \
    /etc/ssh/ssh_host_rsa_key /etc/ssh/ssh_host_rsa_key.pub \
    /etc/ssh/ssh_host_ecdsa_key /etc/ssh/ssh_host_ecdsa_key.pub \
    /etc/ssh/ssh_host_ed25519_key /etc/ssh/ssh_host_ed25519_key.pub \
    /etc/shadow-; do
    if debugfs -R "stat $key" "$rootfs" 2>/dev/null | grep -Fq 'Inode:'; then
        die "Bereinigte Datei ist noch vorhanden: $key"
    fi
done
debugfs -R 'cat /etc/systemd/system/ssh.service.d/10-t95-hostkeys.conf' "$rootfs" 2>/dev/null \
    | grep -Fxq 'Requires=t95-hostkeys.service' || die 'SSH-Abhängigkeit fehlt'
debugfs -R 'cat /etc/systemd/system/ssh.service.d/10-t95-hostkeys.conf' "$rootfs" 2>/dev/null \
    | grep -Fxq 'After=t95-hostkeys.service' || die 'SSH-Reihenfolge fehlt'

# Insert only the sanitized filesystem into the copied image.  The MBR and
# signed TOC0 loader are compared afterwards and therefore cannot change here.
dd if="$rootfs" of="$image" bs=4M seek=1 count="$rootfs_blocks" conv=notrunc,fsync status=none
cmp <(dd if="$source_image" bs=512 count=1 status=none) <(dd if="$image" bs=512 count=1 status=none) \
    || die 'MBR wurde verändert'
cmp "$loader" <(dd if="$image" bs=1 skip=8192 count="$(stat -c %s "$loader")" status=none) \
    || die 'TOC0-Loader weicht nach Härtung ab'
cmp "$rootfs" <(dd if="$image" bs=4M skip=1 count="$rootfs_blocks" status=none) \
    || die 'Harte Rootpartition-Rücklesung fehlgeschlagen'
if LC_ALL=C grep -aFq -- "$source_root_hash" "$image"; then
    die 'Der geerbte Root-Hash ist noch im fertigen Rohimage auffindbar'
fi
for patterns_file in "${source_private_key_patterns[@]}"; do
    if LC_ALL=C grep -aFq -f "$patterns_file" "$image"; then
        die 'Privates Quellhostkey-Material ist noch im fertigen Rohimage auffindbar'
    fi
done

install -m 0644 "$loader" "$artifact/u-boot-sunxi-with-spl.bin"
install -m 0644 "$dtb" "$artifact/sun50i-h616-t95-axp313-tanix-6.18.dtb"
install -m 0644 "${BASH_SOURCE[0]}" "$artifact/build-recipe.sh"
{
    printf 'format=T95-HARDENING-1\n'
    printf 'source_artifact=%s\n' "$(basename "$source_artifact")"
    printf 'source_image_sha256=%s\n' "$(sha256sum "$source_image" | awk '{print $1}')"
    printf 'image_filename=%s\n' "$image_name"
    printf 'image_size=%s\n' "$(stat -c %s "$image")"
    printf 'image_sha256=%s\n' "$(sha256sum "$image" | awk '{print $1}')"
    printf 'root_account=locked_generic\n'
    printf 'ssh_host_keys=absent_from_image\n'
    printf 'ssh_hostkey_generation=before_ssh_service\n'
    printf 'armbian_firstrun_hostkey_regeneration=disabled\n'
    printf 'sensitive_free_blocks=scrubbed\n'
    printf 'scope=host_only_regular_files; no_SD_or_eMMC_write\n'
    printf 'loader_offset_bytes=8192\n'
    printf 'loader_header=TOC0.GLH\n'
} > "$artifact/HARDENING-METADATA.txt"
{
    printf 'board=H616-T95MAX-AXP313A-V3.0\n'
    printf 'kernel_release=6.18.48-current-sunxi64\n'
    printf 'status=GENERIC_RELEASE_CANDIDATE_NOT_REBOOTED_AFTER_HARDENING\n'
    printf 'sd_write=not_performed\nemmc_write=not_performed\n'
} > "$artifact/BUILD-METADATA.txt"
(
    cd "$artifact"
    find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%f\0' \
        | sort -z | xargs -0 sha256sum -- > SHA256SUMS
    sha256sum -c SHA256SUMS
)
printf 'ERFOLG: gehärtetes, generisches Release-Artefakt: %s\n' "$artifact"
printf 'Nächster Pflichtschritt: bash build/audit-t95-generic-release-image.sh %q\n' "$artifact"
