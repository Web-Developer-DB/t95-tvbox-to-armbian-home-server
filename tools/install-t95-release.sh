#!/usr/bin/env bash
# End-user quickstart: download, verify, personalize and optionally write the
# stable T95 release to a removable SD card. No eMMC operation is performed.
set -Eeuo pipefail

readonly REPO_URL="https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git"
readonly RELEASE_BASE="https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/releases/download/v1.0.1"
readonly IMAGE_NAME="T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img"
readonly IMAGE_XZ_NAME="${IMAGE_NAME}.xz"

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "Werkzeug fehlt: $1"; }

for tool in bash curl git sha256sum xz lsblk; do need "$tool"; done

WORKDIR="${T95_WORKDIR:-$PWD/t95-t95-install}"
REPO="$WORKDIR/t95-tvbox-to-armbian-home-server"
PRIVATE="$WORKDIR/t95-private"
IMAGE_XZ="$WORKDIR/$IMAGE_XZ_NAME"
IMAGE="$WORKDIR/$IMAGE_NAME"
MANIFEST="$WORKDIR/SHA256SUMS"

mkdir -p "$WORKDIR"
cd "$WORKDIR"
if [[ -d "$REPO/.git" ]]; then
  git -C "$REPO" fetch --depth 1 origin "refs/tags/v1.0.1:refs/tags/v1.0.1"
  git -C "$REPO" checkout --detach v1.0.1
else
  git clone --branch v1.0.1 --depth 1 "$REPO_URL" "$REPO"
fi

printf 'Lade und prüfe Release-Image ...\n'
curl -fL --retry 3 -o "$IMAGE_XZ" "$RELEASE_BASE/$IMAGE_XZ_NAME"
curl -fL --retry 3 -o "$MANIFEST" "$RELEASE_BASE/SHA256SUMS"
expected_sha="$(awk -v name="$IMAGE_XZ_NAME" '$2 == name { print $1; exit }' "$MANIFEST")"
actual_sha="$(sha256sum "$IMAGE_XZ" | awk '{ print $1 }')"
[[ -n "$expected_sha" && "$expected_sha" == "$actual_sha" ]] || \
  die 'SHA-256-Prüfung des Release-Images fehlgeschlagen'
printf '%s: OK\n' "$IMAGE_XZ_NAME"
xz -t "$IMAGE_XZ"

if [[ ! -f "$IMAGE" ]]; then
  xz -dk --keep "$IMAGE_XZ"
fi

mkdir -p "$PRIVATE"
printf '%s\n' 'Jetzt wird ein lokales Root-Passwort abgefragt.'
bash "$REPO/tools/provision-t95-release-image.sh" \
  "$IMAGE" "$PRIVATE/t95-personal.img" PROVISION-T95-ROOT-PASSWORD

printf '\nLokale Image-Kopie bereit: %s\n' "$PRIVATE/t95-personal.img"
printf '\nErkannte Blockgeräte:\n'
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS
printf '\nDie folgende Aktion überschreibt das ausgewählte Wechselmedium vollständig.\n'
read -r -p 'Soll die persönliche Kopie jetzt auf eine SD-Karte geschrieben werden? [ja/NEIN] ' write_answer
if [[ "$write_answer" != "ja" ]]; then
  printf 'Vorbereitung beendet. Die SD-Karte wurde nicht verändert.\n'
  exit 0
fi

read -r -p 'Gerät der SD-Karte (z. B. /dev/sda, keine Partition): ' target
[[ "$target" =~ ^/dev/sd[a-z]+$ ]] || die 'Ungültiges Zielgerät; nur USB-SD-Geräte wie /dev/sda sind erlaubt.'
[[ -b "$target" ]] || die "Blockgerät nicht gefunden: $target"

bash "$REPO/tools/write-t95-provisioned-image-to-sd.sh" \
  "$target" \
  "$PRIVATE/t95-personal.img" \
  "$PRIVATE/t95-personal.img.t95-provisioned-manifest" \
  WRITE-T95-PROVISIONED-TO-SDX

printf '\nERFOLG: SD-Karte ist vorbereitet. Erst bei ausgeschalteter T95 einsetzen.\n'
