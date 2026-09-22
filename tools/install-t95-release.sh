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
lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

timestamp() { date +%Y%m%d-%H%M%S; }

ask_existing_copy() {
  local answer
  while :; do
    read -r -p 'Vorhandene persönliche Kopie verwenden? [W]iederverwenden/[N]eu mit Zeitstempel/[A]bbrechen (W): ' answer
    case "$(lower "$answer")" in
      ''|w|weiter|wiederverwenden|reuse) return 0 ;;
      n|neu|new) return 1 ;;
      a|abbrechen|q|quit) die 'Vom Benutzer abgebrochen' ;;
      *) printf 'Bitte W, N oder A eingeben. Die vorhandene Datei wird nicht überschrieben.\n' >&2 ;;
    esac
  done
}

ask_write_confirmation() {
  local answer
  while :; do
    read -r -p 'Soll die persönliche Kopie jetzt auf eine SD-Karte geschrieben werden? [J]a/[N]ein (N): ' answer
    case "$(lower "$answer")" in
      j|ja|y|yes) return 0 ;;
      ''|n|nein|no) return 1 ;;
      *) printf 'Bitte J/Ja oder N/Nein eingeben. Die SD-Karte bleibt unverändert.\n' >&2 ;;
    esac
  done
}

choose_removable_sd() {
  local -a candidates=()
  local selection confirmation index

  mapfile -t candidates < <(
    lsblk -dnpo PATH,TRAN,RM,TYPE |
      awk '$2 == "usb" && $3 == "1" && $4 == "disk" { print $1 }'
  )
  ((${#candidates[@]} > 0)) || die 'Keine wechselbare USB-SD-Karte erkannt. Karte oder Kartenleser einstecken und erneut starten.'

  printf '\nErkannte wechselbare USB-Datenträger:\n'
  for index in "${!candidates[@]}"; do
    printf '  [%d] ' "$((index + 1))"
    lsblk -dn -o PATH,SIZE,MODEL,SERIAL,TRAN,RM,TYPE "${candidates[$index]}"
  done

  if ((${#candidates[@]} == 1)); then
    target="${candidates[0]}"
    printf 'Es wurde genau ein mögliches Ziel gefunden: %s\n' "$target"
  else
    while :; do
      read -r -p 'Nummer des gewünschten SD-Kartenlesers eingeben (leer = Abbruch): ' selection
      [[ -n "$selection" ]] || die 'Vom Benutzer abgebrochen; keine SD-Karte wurde verändert'
      if [[ "$selection" =~ ^[1-9][0-9]*$ ]]; then
        selection=$((10#$selection))
        if ((selection <= ${#candidates[@]})); then
          target="${candidates[$((selection - 1))]}"
          break
        fi
      fi
      printf 'Bitte eine Nummer aus der angezeigten Liste eingeben.\n' >&2
    done
  fi

  printf '\nAusgewähltes Ziel: %s\n' "$target"
  printf '%s\n' 'Bitte kontrolliere Größe, Modell und Seriennummer oberhalb sorgfältig.'
  read -r -p "Zur endgültigen Bestätigung exakt ${target} eingeben (leer = Abbruch): " confirmation
  [[ "$confirmation" == "$target" ]] || die 'Ziel nicht bestätigt; keine SD-Karte wurde verändert'
}

checkout_release_tools() {
  local candidate="$1"

  git -C "$candidate" fetch --quiet --depth 1 origin \
    'refs/tags/v1.0.1:refs/tags/v1.0.1' 2>/dev/null && \
    git -C "$candidate" checkout --quiet --detach v1.0.1 2>/dev/null
}

prepare_release_tools() {
  local fallback

  if [[ ! -e "$REPO" ]]; then
    git clone --branch v1.0.1 --depth 1 "$REPO_URL" "$REPO"
    return
  fi

  if [[ -d "$REPO/.git" ]] && checkout_release_tools "$REPO"; then
    return
  fi

  # Do not touch an existing checkout when it is read-only, has local changes,
  # or otherwise cannot be switched to the release tag.  A separate directory
  # keeps the first run and a later retry independent from each other.
  fallback="${REPO}-v1.0.1"
  printf '%s\n' 'Vorhandener Werkzeuge-Ordner kann nicht sicher auf v1.0.1 aktualisiert werden.' >&2
  printf 'Verwende deshalb einen getrennten Release-Werkzeuge-Ordner: %s\n' "$fallback" >&2

  if [[ ! -e "$fallback" ]]; then
    git clone --branch v1.0.1 --depth 1 "$REPO_URL" "$fallback"
  elif [[ -d "$fallback/.git" ]] && checkout_release_tools "$fallback"; then
    :
  else
    die "Release-Werkzeuge können nicht vorbereitet werden: $fallback"
  fi
  REPO="$fallback"
}

for tool in awk bash curl date git mapfile mv sha256sum tr xz lsblk; do need "$tool"; done

WORKDIR="${T95_WORKDIR:-$PWD/t95-t95-install}"
REPO="$WORKDIR/t95-tvbox-to-armbian-home-server"
PRIVATE="$WORKDIR/t95-private"
IMAGE_XZ="$WORKDIR/$IMAGE_XZ_NAME"
IMAGE="$WORKDIR/$IMAGE_NAME"
MANIFEST="$WORKDIR/SHA256SUMS"
RELEASE_MANIFEST="$WORKDIR/RELEASE-MANIFEST.txt"

mkdir -p "$WORKDIR"
cd "$WORKDIR"
prepare_release_tools

printf 'Lade Release-Metadaten und prüfe vorhandene Dateien ...\n'
curl -fL --retry 3 -o "$MANIFEST" "$RELEASE_BASE/SHA256SUMS"
curl -fL --retry 3 -o "$RELEASE_MANIFEST" "$RELEASE_BASE/RELEASE-MANIFEST.txt"
expected_sha="$(awk -v name="$IMAGE_XZ_NAME" '$2 == name { print $1; exit }' "$MANIFEST")"
expected_raw_sha="$(awk -F= '$1 == "image_uncompressed_sha256" { print $2; exit }' "$RELEASE_MANIFEST")"
[[ "$expected_sha" =~ ^[0-9a-f]{64}$ && "$expected_raw_sha" =~ ^[0-9a-f]{64}$ ]] \
  || die 'Release-Manifeste enthalten keine erwarteten Prüfsummen'

if [[ -f "$IMAGE_XZ" ]]; then
  actual_sha="$(sha256sum "$IMAGE_XZ" | awk '{ print $1 }')"
  if [[ "$actual_sha" == "$expected_sha" ]]; then
    printf 'Vorhandener Download wird weiterverwendet: %s\n' "$IMAGE_XZ_NAME"
  else
    invalid_xz="$IMAGE_XZ.invalid-$(timestamp)-$$"
    mv -- "$IMAGE_XZ" "$invalid_xz"
    printf 'Ungültigen Download nicht überschrieben, sondern verschoben nach: %s\n' "$invalid_xz" >&2
  fi
fi
if [[ ! -f "$IMAGE_XZ" ]]; then
  printf 'Lade Release-Image ...\n'
  curl -fL --retry 3 -o "$IMAGE_XZ" "$RELEASE_BASE/$IMAGE_XZ_NAME"
fi
actual_sha="$(sha256sum "$IMAGE_XZ" | awk '{ print $1 }')"
[[ "$actual_sha" == "$expected_sha" ]] || die 'SHA-256-Prüfung des Release-Images fehlgeschlagen'
printf '%s: OK\n' "$IMAGE_XZ_NAME"
xz -t "$IMAGE_XZ"

mkdir -p "$PRIVATE"
PERSONAL_IMAGE="$PRIVATE/t95-personal.img"
PERSONAL_MANIFEST="$PERSONAL_IMAGE.t95-provisioned-manifest"
create_personal=1

if [[ -f "$PERSONAL_IMAGE" && -f "$PERSONAL_MANIFEST" ]]; then
  existing_generic_sha="$(awk -F= '$1 == "generic_image_sha256" { print $2; exit }' "$PERSONAL_MANIFEST")"
  if [[ "$existing_generic_sha" == "$expected_raw_sha" ]] && ask_existing_copy; then
    create_personal=0
    printf 'Vorhandene persönliche Kopie wird verwendet: %s\n' "$PERSONAL_IMAGE"
  else
    PERSONAL_IMAGE="$PRIVATE/t95-personal-$(timestamp)-$$.img"
    PERSONAL_MANIFEST="$PERSONAL_IMAGE.t95-provisioned-manifest"
    printf 'Neue persönliche Kopie wird erzeugt: %s\n' "$PERSONAL_IMAGE"
  fi
elif [[ -e "$PERSONAL_IMAGE" || -e "$PERSONAL_MANIFEST" ]]; then
  PERSONAL_IMAGE="$PRIVATE/t95-personal-$(timestamp)-$$.img"
  PERSONAL_MANIFEST="$PERSONAL_IMAGE.t95-provisioned-manifest"
  printf 'Unvollständige alte Personalisierung bleibt erhalten; neue Kopie: %s\n' "$PERSONAL_IMAGE" >&2
fi

if (( create_personal )); then
  if [[ -f "$IMAGE" ]]; then
    actual_raw_sha="$(sha256sum "$IMAGE" | awk '{ print $1 }')"
    if [[ "$actual_raw_sha" != "$expected_raw_sha" ]]; then
      invalid_image="$IMAGE.invalid-$(timestamp)-$$"
      mv -- "$IMAGE" "$invalid_image"
      printf 'Ungültiges entpacktes Image nicht überschrieben, sondern verschoben nach: %s\n' "$invalid_image" >&2
    fi
  fi
  if [[ ! -f "$IMAGE" ]]; then
    printf 'Entpacke das geprüfte Release-Image ...\n'
    xz -dk --keep "$IMAGE_XZ"
  fi
  printf '%s\n' 'Jetzt wird ein lokales Root-Passwort abgefragt.'
  bash "$REPO/tools/provision-t95-release-image.sh" \
    "$IMAGE" "$PERSONAL_IMAGE" PROVISION-T95-ROOT-PASSWORD
fi

printf '\nLokale Image-Kopie bereit: %s\n' "$PERSONAL_IMAGE"
printf '\nDie folgende Aktion überschreibt das ausgewählte Wechselmedium vollständig.\n'
if ! ask_write_confirmation; then
  printf 'Vorbereitung beendet. Die SD-Karte wurde nicht verändert.\n'
  exit 0
fi

choose_removable_sd

bash "$REPO/tools/write-t95-provisioned-image-to-sd.sh" \
  "$target" \
  "$PERSONAL_IMAGE" \
  "$PERSONAL_MANIFEST" \
  WRITE-T95-PROVISIONED-TO-SDX

printf '\nERFOLG: SD-Karte ist vorbereitet. Erst bei ausgeschalteter T95 einsetzen.\n'
