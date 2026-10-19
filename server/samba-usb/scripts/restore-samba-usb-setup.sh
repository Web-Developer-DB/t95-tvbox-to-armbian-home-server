#!/usr/bin/env bash
# Install/update the optional Samba USB layer; backs up configuration before APT.
# CHANGE-ID: SAMBA
set -Eeuo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export DEBIAN_FRONTEND=noninteractive
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec /usr/bin/python3 "$script_dir/../lib/t95_install.py" "$@"
