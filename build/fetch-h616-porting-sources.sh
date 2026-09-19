#!/usr/bin/env bash
# Fetch only pinned U-Boot and TF-A source trees into ignored build/sources.
# No build, block-device access, FEL command, or target-hardware access occurs.
# CHANGE-ID: BOOT TFA
# ARMBIAN-BASE: fetch exact upstream source revisions, without modifying them.
# PORTING-NOTE: change a commit only together with the documented compatibility review.
set -Eeuo pipefail

project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
sources="$project/build/sources"
readonly uboot_url=https://github.com/u-boot/u-boot.git
readonly uboot_commit=25049ad560826f7dc1c4740883b0016014a59789
readonly tfa_url=https://github.com/ARM-software/arm-trusted-firmware.git
readonly tfa_commit=b6c0948400594e3cc4dbb5a4ef04b815d2675808

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
for tool in git mkdir; do command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"; done

checkout_exact() {
  local directory=$1 url=$2 commit=$3
  if [[ ! -d "$directory/.git" ]]; then
    git clone --filter=blob:none --no-checkout "$url" "$directory"
  fi
  git -C "$directory" fetch --depth 1 origin "$commit"
  git -C "$directory" checkout --detach "$commit"
  [[ $(git -C "$directory" rev-parse HEAD) == "$commit" ]] || die "Revision fehlt: $directory"
  [[ -z $(git -C "$directory" status --porcelain) ]] || die "Quellbaum nicht sauber: $directory"
}

mkdir -p "$sources"
checkout_exact "$sources/u-boot" "$uboot_url" "$uboot_commit"
checkout_exact "$sources/trusted-firmware-a" "$tfa_url" "$tfa_commit"
printf 'ERFOLG: Quellen vorbereitet. Details: build/PORTING_SOURCES.md\n'
