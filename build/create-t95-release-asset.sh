#!/usr/bin/env bash
# Package an already audited, hardened generic image as GitHub release assets.
# This is host-only: it never opens a block device or the T95 eMMC.
# CHANGE-ID: RELEASE HARDEN
# T95-CHANGE: publish only manifest-backed, audited release assets.
# PORTING-NOTE: keep asset naming, release IDs and hashes synchronized.
set -euo pipefail
umask 022

project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
release_id=${1:-}
artifact=${T95_RELEASE_ARTIFACT:-}
asset_prefix='T95-H616-AXP313A-Armbian-26.8.4-6.18.48'

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
[[ "$release_id" =~ ^v[0-9]+\.[0-9]+\.[0-9]+-[a-z0-9.-]+$ ]] \
    || die 'Aufruf: T95_RELEASE_ARTIFACT=/pfad/zum/gehärteten_artefakt $0 vX.Y.Z-kennzeichnung'
[[ -n "$artifact" && -d "$artifact" && -f "$artifact/HARDENING-METADATA.txt" && -f "$artifact/SHA256SUMS" ]] \
    || die 'T95_RELEASE_ARTIFACT muss auf ein geprüftes Härtungsartefakt zeigen'
for tool in awk basename cp head mkdir mv rm sed sha256sum stat xz; do
    command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done

metadata="$artifact/HARDENING-METADATA.txt"
field() { sed -n "s/^$1=//p" "$metadata"; }
image_name=$(field image_filename)
expected_image_size=$(field image_size)
expected_image_sha=$(field image_sha256)
[[ "$image_name" =~ ^[A-Za-z0-9._-]+\.img$ ]] || die 'Härtungsmetadaten enthalten keinen sicheren Imagenamen'
[[ "$expected_image_size" =~ ^[0-9]+$ && "$expected_image_sha" =~ ^[0-9a-f]{64}$ ]] \
    || die 'Härtungsmetadaten enthalten keine gültige Imagegröße oder Prüfsumme'
[[ $(field root_account) == locked_generic ]] || die 'Nur ein generisch gesperrtes Rootkonto darf veröffentlicht werden'
[[ $(field ssh_host_keys) == absent_from_image ]] || die 'Release-Image enthält laut Metadaten noch Hostkeys'
[[ $(field ssh_hostkey_generation) == before_ssh_service ]] || die 'Vor-SSH-Hostkey-Erzeugung fehlt'
[[ $(field armbian_firstrun_hostkey_regeneration) == disabled ]] || die 'Armbian-Hostkey-Konfiguration ist nicht gehärtet'
[[ $(field sensitive_free_blocks) == scrubbed ]] || die 'Freie Ext4-Blöcke wurden nicht als bereinigt nachgewiesen'

(cd "$artifact" && sha256sum -c SHA256SUMS) >/dev/null || die 'Härtungsartefakt-Prüfsummen fehlerhaft'
image="$artifact/$image_name"
[[ -f "$image" && ! -b "$image" ]] || die 'Generisches Rohimage fehlt'
[[ $(stat -c %s "$image") == "$expected_image_size" ]] || die 'Rohimage hat unerwartete Größe'
[[ $(sha256sum "$image" | awk '{print $1}') == "$expected_image_sha" ]] || die 'Rohimage hat unerwarteten Hash'
[[ $((expected_image_size % 4194304)) -eq 0 ]] || die 'Rohimage ist nicht 4-MiB-ausgerichtet'

loader="$artifact/u-boot-sunxi-with-spl.bin"
dtb="$artifact/sun50i-h616-t95-axp313-tanix-6.18.dtb"
[[ -f "$loader" && -f "$dtb" ]] || die 'Loader oder DTB fehlt im Härtungsartefakt'
[[ $(head -c 8 "$loader") == TOC0.GLH ]] || die 'Loader hat keinen TOC0-Header'

output="$project/release-assets/$release_id"
[[ ! -e "$output" ]] || die "Ausgabe existiert bereits: $output"
mkdir -p "$output"
tmp="$output/.image.img.xz.partial"
asset_image="$output/$asset_prefix-$release_id.img.xz"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

printf 'Komprimiere das geprüfte, gesperrte generische Image.\n'
xz -T0 -6 --check=sha256 -c -- "$image" > "$tmp"
xz -t "$tmp"
mv "$tmp" "$asset_image"

cp "$artifact/SHA256SUMS" "$output/HARDENED-ARTIFACT-SHA256SUMS"
cp "$artifact/HARDENING-METADATA.txt" "$output/HARDENING-METADATA.txt"
cp "$loader" "$output/T95-H616-AXP313A-u-boot-sunxi-with-spl.bin"
cp "$dtb" "$output/T95-H616-AXP313A-tanix-6.18.dtb"
{
    printf 'release_id=%s\n' "$release_id"
    printf '%s\n' 'channel=experimental'
    printf '%s\n' 'board=H616-T95MAX-AXP313A-V3.0'
    printf '%s\n' 'system=Armbian 26.8.4 Trixie'
    printf '%s\n' 'kernel_release=6.18.48-current-sunxi64'
    printf 'image_compressed=%s\n' "$(basename "$asset_image")"
    printf 'image_uncompressed=%s\n' "$image_name"
    printf 'image_uncompressed_size=%s\n' "$expected_image_size"
    printf 'image_uncompressed_sha256=%s\n' "$expected_image_sha"
    printf '%s\n' 'image_state=generic_root_locked; personalize locally before writing to microSD'
    printf '%s\n' 'personalization_tool=tools/provision-t95-release-image.sh'
    printf '%s\n' 'ssh_host_keys=absent_from_image; generated before ssh.service on first target start'
    printf '%s\n' 'loader_offset_bytes=8192'
    printf '%s\n' 'loader_header=TOC0.GLH'
    printf 'loader_sha256=%s\n' "$(sha256sum "$loader" | awk '{print $1}')"
    printf 'dtb_sha256=%s\n' "$(sha256sum "$dtb" | awk '{print $1}')"
    printf '%s\n' 'rootfs=ext4, one partition at byte 4194304'
    printf '%s\n' 'boot_diagnostic_args=clk_ignore_unused nohz=off'
    printf '%s\n' 'hardware_status=boot, AC300 Ethernet, DHCP and SSH verified before generic-image hardening'
    printf '%s\n' 'emmc_access=none; never read or written by asset generation'
    printf '%s\n' 'signing_note=TOC0 loader is signed; private experiment key is intentionally excluded'
} > "$output/RELEASE-MANIFEST.txt"
(cd "$output" && sha256sum "$(basename "$asset_image")" RELEASE-MANIFEST.txt HARDENING-METADATA.txt \
    HARDENED-ARTIFACT-SHA256SUMS T95-H616-AXP313A-u-boot-sunxi-with-spl.bin \
    T95-H616-AXP313A-tanix-6.18.dtb > SHA256SUMS && sha256sum -c SHA256SUMS)
trap - EXIT
printf 'ERFOLG: GitHub-Release-Assets erzeugt: %s\n' "$output"
printf 'Vor Upload ausführen: (cd %q && sha256sum -c SHA256SUMS)\n' "$output"
