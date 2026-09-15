#!/usr/bin/env bash
# Read-only audit of a hardened generic T95 release artifact.  No block device
# is opened and no input image is changed.
set -euo pipefail
umask 077

artifact=${1:-}
source_artifact=${2:-}
die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
[[ $# -ge 1 && $# -le 2 && -d "$artifact" && -f "$artifact/HARDENING-METADATA.txt" && -f "$artifact/SHA256SUMS" ]] \
    || die "Aufruf: $0 ARTEFAKT_ORDNER [PRIVATES_QUELLARTEFAKT]"
for tool in awk chmod dd debugfs e2fsck grep mktemp rm sed sha256sum stat; do
    command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done
(cd "$artifact" && sha256sum -c SHA256SUMS) >/dev/null || die 'Artefakt-Prüfsummen fehlerhaft'

metadata="$artifact/HARDENING-METADATA.txt"
field() { sed -n "s/^$1=//p" "$metadata"; }
image_name=$(field image_filename)
image_size=$(field image_size)
[[ "$image_name" =~ ^[A-Za-z0-9._-]+\.img$ && "$image_size" =~ ^[0-9]+$ ]] || die 'Ungültige Härtungsmetadaten'
[[ $(field root_account) == locked_generic ]] || die 'Rootkonto ist nicht als gesperrt dokumentiert'
[[ $(field ssh_host_keys) == absent_from_image ]] || die 'Hostkeys sind nicht als entfernt dokumentiert'
[[ $(field ssh_hostkey_generation) == before_ssh_service ]] || die 'Vor-SSH-Schlüsselerzeugung fehlt im Manifest'
image="$artifact/$image_name"
[[ -f "$image" && ! -b "$image" && $(stat -c %s "$image") == "$image_size" ]] || die 'Generisches Rohimage fehlt oder hat eine falsche Größe'
[[ $((image_size % 4194304)) -eq 0 && "$image_size" -gt 4194304 ]] || die 'Image ist nicht passend ausgerichtet'

work=$(mktemp -d "${TMPDIR:-/tmp}/t95-generic-audit.XXXXXX")
cleanup() { rm -rf -- "$work"; }
trap cleanup EXIT
rootfs="$work/rootfs.ext4"
blocks=$(((image_size - 4194304) / 4194304))
dd if="$image" of="$rootfs" bs=4M skip=1 count="$blocks" status=none
e2fsck -fn "$rootfs" >/dev/null || die 'Generische Rootpartition ist nicht prüfbar'

debugfs -R 'cat /etc/shadow' "$rootfs" 2>/dev/null > "$work/shadow"
awk -F: 'BEGIN { ok=0 } $1 == "root" { ok=($2 == "!"); exit } END { exit ok ? 0 : 1 }' "$work/shadow" \
    || die 'Rootkonto ist im Rohimage nicht gesperrt'
[[ ! -s "$work/shadow" || $(grep -c '^root:' "$work/shadow") == 1 ]] || die 'Rootkonto ist mehrdeutig'
debugfs -R 'cat /etc/default/armbian-firstrun' "$rootfs" 2>/dev/null \
    | grep -Fxq 'OPENSSHD_REGENERATE_HOST_KEYS=false' || die 'Armbian würde Hostkeys nach SSH ersetzen'
debugfs -R 'cat /etc/systemd/system/ssh.service.d/10-t95-hostkeys.conf' "$rootfs" 2>/dev/null \
    | grep -Fxq 'Requires=t95-hostkeys.service' || die 'SSH hat keine Hostkey-Abhängigkeit'
debugfs -R 'cat /etc/systemd/system/ssh.service.d/10-t95-hostkeys.conf' "$rootfs" 2>/dev/null \
    | grep -Fxq 'After=t95-hostkeys.service' || die 'SSH-Reihenfolge ist nicht gesichert'
debugfs -R 'stat /usr/lib/t95-release/t95-initialize-ssh-hostkeys' "$rootfs" 2>/dev/null \
    | grep -Fq 'Mode:  0755' || die 'Hostkey-Generator ist nicht ausführbar'

for key in \
    /etc/ssh/ssh_host_rsa_key /etc/ssh/ssh_host_rsa_key.pub \
    /etc/ssh/ssh_host_ecdsa_key /etc/ssh/ssh_host_ecdsa_key.pub \
    /etc/ssh/ssh_host_ed25519_key /etc/ssh/ssh_host_ed25519_key.pub \
    /etc/shadow-; do
    if debugfs -R "stat $key" "$rootfs" 2>/dev/null | grep -Fq 'Inode:'; then
        die "Entfernte Datei ist im generischen Image noch vorhanden: $key"
    fi
done
machine_id=$(debugfs -R 'cat /etc/machine-id' "$rootfs" 2>/dev/null || true)
[[ -z "$machine_id" ]] || die 'machine-id ist im generischen Image nicht leer'
if [[ -n "$source_artifact" ]]; then
    [[ -d "$source_artifact" && -f "$source_artifact/SHA256SUMS" ]] \
        || die 'Privates Quellartefakt oder Manifest fehlt'
    (cd "$source_artifact" && sha256sum -c SHA256SUMS) >/dev/null \
        || die 'Privates Quellartefakt hat ungültige Prüfsummen'
    source_rootfs="$source_artifact/t95-tanix-6.18-rootfs.ext4"
    [[ -f "$source_rootfs" && ! -b "$source_rootfs" ]] || die 'Private Quellrootpartition fehlt'
    debugfs -R 'cat /etc/shadow' "$source_rootfs" 2>/dev/null > "$work/source-shadow"
    source_root_hash=$(awk -F: '$1 == "root" { print $2; exit }' "$work/source-shadow")
    [[ ${#source_root_hash} -ge 20 ]] || die 'Quell-Root-Hash ist nicht prüfbar'
    printf '%s' "$source_root_hash" > "$work/source-root-hash.pattern"
    if LC_ALL=C grep -aFq -f "$work/source-root-hash.pattern" "$image"; then
        die 'Der geerbte Root-Hash ist noch im generischen Rohimage auffindbar'
    fi
    for source_key in /etc/ssh/ssh_host_rsa_key /etc/ssh/ssh_host_ecdsa_key /etc/ssh/ssh_host_ed25519_key; do
        key_file="$work/$(basename "$source_key")"
        debugfs -R "dump -p $source_key $key_file" "$source_rootfs" 2>/dev/null \
            || die "Privater Quellhostkey fehlt: $source_key"
        chmod 0600 "$key_file"
        awk 'length($0) >= 48' "$key_file" > "$key_file.payload-lines"
        [[ -s "$key_file.payload-lines" ]] || die "Quellhostkey ist nicht prüfbar: $source_key"
        if LC_ALL=C grep -aFq -f "$key_file.payload-lines" "$image"; then
            die 'Privates Quellhostkey-Material ist noch im generischen Rohimage auffindbar'
        fi
    done
fi

printf 'ERFOLG: generisches Image besteht den Sicherheitsaudit.\n'
printf '  Rootkonto: gesperrt; kein veröffentlichter Anfangshash\n'
printf '  SSH-Hostkeys: nicht im Image; Generierung vor ssh.service\n'
printf '  machine-id: leer; ext4: prüfbar\n'
if [[ -n "$source_artifact" ]]; then
    printf '  Quellreste: Root-Hash und drei private Hostkey-Payloads nicht auffindbar\n'
else
    printf '  Quellreste: nicht vollständig ohne privates Quellartefakt prüfbar\n'
fi
