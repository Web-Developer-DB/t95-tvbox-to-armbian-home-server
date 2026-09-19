#!/usr/bin/env bash
# Check or, with explicit --install, install host dependencies for H616 builds.
# It never opens a block device, contacts FEL hardware, or accesses a T95.
# CHANGE-ID: BASE BOOT TFA
# ARMBIAN-BASE: Debian/Ubuntu build dependencies are installed only with --install.
# PORTING-NOTE: verify equivalent package names on non-Debian Linux hosts.
set -Eeuo pipefail

mode=${1:---check}
case "$mode" in
  --check|--install) ;;
  *) printf 'Aufruf: %s [--check|--install]\n' "$0" >&2; exit 2 ;;
esac

packages=(build-essential gcc-aarch64-linux-gnu device-tree-compiler bison flex swig
  python3 python3-pyelftools libssl-dev libgnutls28-dev libncurses-dev libfdt-dev
  git curl xz-utils cpio bc)
commands=(aarch64-linux-gnu-gcc dtc bison flex swig git curl xz openssl make)

if [[ "$mode" == --install ]]; then
  command -v sudo >/dev/null || { echo 'ABBRUCH: sudo fehlt.' >&2; exit 2; }
  sudo apt-get update
  sudo apt-get install -y "${packages[@]}"
fi

missing=0
for command in "${commands[@]}"; do
  if command -v "$command" >/dev/null 2>&1; then
    printf 'OK: %s -> %s\n' "$command" "$(command -v "$command")"
  else
    printf 'FEHLT: %s\n' "$command" >&2
    missing=1
  fi
done

if (( missing )); then
  echo 'Hinweis: Mit --install werden die Debian/Ubuntu-Abhängigkeiten installiert.' >&2
  exit 1
fi
echo 'ERFOLG: H616-Porting-Buildhost ist bereit.'
