#!/usr/bin/env bash
# Ein-Befehl-Einstieg; alle Aktionen sind auch aus einem lokalen Checkout möglich.
set -Eeuo pipefail

repo=Web-Developer-DB/t95-tvbox-to-armbian-home-server
# Schnellstarts und Quellarchiv verwenden dieselbe Git-Referenz.
ref=${T95_SETUP_REF:-main}

if (($# == 0)); then
    printf '%s\n' 'T95: 0 Dashboard + Bluetooth/Player gemeinsam installieren' \
        '     1 Dashboard installieren | 2 Dashboard entfernen' \
        '     3 Bluetooth + Player installieren | 4 Player entfernen / Bluetooth aus' \
        '     5 Bluetooth aus | 6 Bluetooth an | 7 Bluetooth neu starten | 8 Status'
    read -r -p 'Auswahl: ' choice
    case "$choice" in
        0) set -- all install ;;
        1) set -- dashboard install ;; 2) set -- dashboard remove ;;
        3) set -- bluetooth install ;; 4) set -- bluetooth remove --remove-packages ;;
        5) set -- bluetooth off ;; 6) set -- bluetooth on ;;
        7) set -- bluetooth restart ;; 8) set -- bluetooth status ;;
        *) printf '%s\n' 'Abbruch.'; exit 1 ;;
    esac
fi
[[ $# -ge 2 ]] || { printf '%s\n' 'Aufruf: t95-setup.sh dashboard|bluetooth AKTION [Optionen] oder all install'; exit 2; }
case "$1:$2" in
    all:install|dashboard:install|dashboard:remove|dashboard:status|bluetooth:install|bluetooth:remove|bluetooth:status|bluetooth:on|bluetooth:off|bluetooth:restart|bluetooth:pair|bluetooth:audio) ;;
    *) printf '%s\n' 'Unbekannte Komponente oder Aktion.' >&2; exit 2 ;;
esac
[[ $ref =~ ^[A-Za-z0-9._/-]+$ && $ref != *..* ]] || { printf '%s\n' 'Ungültige Git-Referenz.' >&2; exit 2; }
for program in curl tar python3; do
    command -v "$program" >/dev/null || { printf 'Fehlt: %s\n' "$program" >&2; exit 1; }
done
task_tmp=$(mktemp -d -t t95-setup.XXXXXXXX)
trap 'rm -rf -- "$task_tmp"' EXIT
curl --proto '=https' --tlsv1.2 -fLsS --retry 2 --connect-timeout 15 --max-time 180 \
    "https://codeload.github.com/$repo/tar.gz/$ref" -o "$task_tmp/source.tar.gz"
mkdir "$task_tmp/source"
tar --extract --gzip --file "$task_tmp/source.tar.gz" --directory "$task_tmp/source" \
    --strip-components=1 --no-same-owner --no-same-permissions
manager=$task_tmp/source/server/setup/t95_setup.py
[[ -f $manager ]] || { printf '%s\n' 'Setup fehlt in dieser Git-Referenz.' >&2; exit 1; }
invoke_manager() {
    if [[ $(id -u) == 0 ]]; then
        python3 "$manager" "$@"
    else
        sudo python3 "$manager" "$@" --user "$(id -un)"
    fi
}
if [[ $1 == all ]]; then
    # Beide Komponenten nutzen dasselbe Archiv und eigene Rücknahmejournale.
    shift
    invoke_manager dashboard "$@"
    invoke_manager bluetooth "$@"
else
    invoke_manager "$@"
fi
