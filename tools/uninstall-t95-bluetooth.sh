#!/usr/bin/env bash
# Audio-Setup zurücknehmen: Konfiguration/Dienste wiederherstellen, neue Zielpakete entfernen.
set -Eeuo pipefail

script_dir=$(dirname -- "${BASH_SOURCE[0]}")
if [[ -f "$script_dir/t95-setup.sh" ]]; then
    exec bash "$script_dir/t95-setup.sh" bluetooth remove --remove-packages "$@"
fi

# Beim Aufruf über curl gibt es keinen lokalen Checkout.
ref=${T95_SETUP_REF:-main}
[[ $ref =~ ^[A-Za-z0-9._/-]+$ && $ref != *..* ]] || { printf '%s\n' 'Ungültige Git-Referenz.' >&2; exit 2; }
task_starter=$(mktemp -t t95-starter.XXXXXXXX)
trap 'rm -f -- "$task_starter"' EXIT
curl --proto '=https' --tlsv1.2 -fLsS --retry 2 --connect-timeout 15 --max-time 60 \
    "https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/$ref/tools/t95-setup.sh" \
    -o "$task_starter"
bash "$task_starter" bluetooth remove --remove-packages "$@"
