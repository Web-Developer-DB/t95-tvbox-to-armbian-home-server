#!/usr/bin/env bash
# HISTORISCHES LABORWERKZEUG: nicht aus einem öffentlichen Clone reproduzierbar.
# Es benötigt ignorierte Zwischenartefakte und einen privaten TOC0-Schlüssel.
# Für eine neue H616-Portierung build/build-h616-fel-egon.sh verwenden.
# Build a T95-only TOC0 loader that starts Armbian's ext4 boot script.
# It operates exclusively below build/{work,artifacts}; it never opens a block
# device and has no eMMC or SD write path.
# CHANGE-ID: BOOT TFA AXP313 AC300
# T95-CHANGE: apply the board-specific AXP313/DRAM and AC300 U-Boot patches.
# PORTING-NOTE: match U-Boot/TF-A commits and DRAM/PMIC values to the board.
set -euo pipefail
umask 022

project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$project/build/sources/u-boot"
base="$project/build/artifacts/t95-axp313-sd-linux-test-20260912-143848"
preinit="$project/build/artifacts/t95-ac300-preinit-20260912-234612"
image_dir="$project/images"
image_name='Armbian_26.8.4_Tanix-tx6s-axp313_trixie_current_6.18.48_minimal.img.xz'
image_sha='f08a37afef45bca2b2a727b2d5e48d1d7521ff533f7ebc0ec03f52ada677870c'
commit='25049ad560826f7dc1c4740883b0016014a59789'
build_id="${T95_BUILD_ID:-t95-ac300-ext4boot-$(date +%Y%m%d-%H%M%S)}"

[[ "$build_id" =~ ^t95-ac300-ext4boot-[0-9]{8}-[0-9]{6}$ ]] || exit 2
work="$project/build/work/$build_id"
artifact="$project/build/artifacts/$build_id"

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
for tool in git make aarch64-linux-gnu-gcc sha256sum openssl dtc strings; do
    command -v "$tool" >/dev/null || die "Fehlt: $tool"
done

[[ $(git -C "$source_dir" rev-parse HEAD) == "$commit" ]] || die 'Falscher U-Boot-Commit'
[[ -z $(git -C "$source_dir" status --porcelain) ]] || die 'Unsaubere U-Boot-Basisquelle'
[[ -f "$image_dir/$image_name" ]] || die 'Tanix-Image fehlt; erst den Offline-Vergleich ausführen'
[[ $(sha256sum "$image_dir/$image_name" | cut -d' ' -f1) == "$image_sha" ]] || die 'Tanix-Image-Hash falsch'
for input in "$base" "$preinit"; do
    (cd "$input" && sha256sum -c SHA256SUMS >/dev/null) || die "Manifest fehlerhaft: $input"
done
[[ $(sha256sum "$base/bl31.bin" | cut -d' ' -f1) == e0a2a15bcd198452a71587d0a20d0bc099fc00f5bd902210e778f41791a63bd0 ]] || die 'TF-A-Hash falsch'

mkdir -p "$artifact"
[[ ! -e "$artifact/SHA256SUMS" ]] || die 'Fertiges Artefakt wird nicht überschrieben'
if [[ ! -d "$work" ]]; then
    git -C "$source_dir" worktree add --detach "$work" "$commit"
fi
[[ $(git -C "$work" rev-parse HEAD) == "$commit" ]] || die 'Falscher U-Boot-Arbeitsbaum'

for patch in 0001-t95-axp313-h616-fel-bringup.patch 0002-t95-ac300-preinit-command.patch; do
    patch_file="$project/build/patches/$patch"
    if ! git -C "$work" apply --reverse --check "$patch_file" 2>/dev/null; then
        git -C "$work" apply --check "$patch_file"
        git -C "$work" apply "$patch_file"
    fi
    install -m 0644 "$patch_file" "$artifact/$patch"
done

install -m 0600 "$project/build/keys/t95-fel-dev-root_key.pem" "$work/root_key.pem"
install -m 0644 "$base/t95_axp313_sd_linux_test.config" "$work/.config"
export SOURCE_DATE_EPOCH=1712055538

# Armbian 26.8.4 has one ext4 partition.  The upstream boot script needs
# prefix=/boot/, the Tanix DTB filename and an explicit mmc 0:1 bootstrap.
# Shell variables for U-Boot stay literal until U-Boot executes the command.
bootcommand='if t95_ac300; then echo T95 AC300 preinit passed; else echo T95 AC300 preinit failed - see UART; fi; setenv devtype mmc; setenv devnum 0; setenv prefix /boot/; setenv fdtfile allwinner/sun50i-h616-t95-axp313-tanix-6.18.dtb; if ext4load mmc 0:1 ${scriptaddr} /boot/boot.scr; then source ${scriptaddr}; else echo T95 ext4 Armbian boot script not found; fi'
"$work/scripts/config" --file "$work/.config" --set-str BOOTCOMMAND "$bootcommand"
"$work/scripts/config" --file "$work/.config" --set-str IDENT_STRING ' T95-AC300-EXT4BOOT-6.18-CANDIDATE'

make -s -C "$work" CROSS_COMPILE=aarch64-linux-gnu- BL31="$base/bl31.bin" olddefconfig
make -s -C "$work" CROSS_COMPILE=aarch64-linux-gnu- BL31="$base/bl31.bin" -j"${JOBS:-8}"

for required in \
    'CONFIG_DRAM_CLK=600' \
    'CONFIG_AXP313_POWER=y' \
    'CONFIG_SPL_IMAGE_TYPE_SUNXI_TOC0=y' \
    'CONFIG_ENV_IS_NOWHERE=y' \
    'CONFIG_BOOTDELAY=10' \
    'CONFIG_CMD_EXT4=y' \
    'CONFIG_FS_EXT4=y' \
    'CONFIG_CMD_SOURCE=y'; do
    grep -Fxq "$required" "$work/.config" || die "Fehlt: $required"
done
! grep -Eq '^CONFIG_(MMC_WRITE|ENV_IS_IN_FAT|ENV_IS_IN_MMC)=y' "$work/.config" || die 'Persistente Schreibfunktion aktiviert'
diff -u <(grep '^CONFIG_DRAM\|^CONFIG_AXP\|^CONFIG_SUNXI_DRAM' "$base/t95_axp313_sd_linux_test.config") \
        <(grep '^CONFIG_DRAM\|^CONFIG_AXP\|^CONFIG_SUNXI_DRAM' "$work/.config")
[[ $(head -c 8 "$work/u-boot-sunxi-with-spl.bin") == TOC0.GLH ]] || die 'Kein TOC0-Loader'
[[ $(stat -c %s "$work/u-boot-sunxi-with-spl.bin") -lt 4000000 ]] || die 'Loader zu gross'
# Do not use "grep -q" in a pipe under pipefail: the intentional early grep
# exit would otherwise turn strings' SIGPIPE into a false failed build.
grep -F 'ext4load mmc 0:1 ${scriptaddr} /boot/boot.scr' < <(strings -a "$work/u-boot-sunxi-with-spl.bin") >/dev/null || die 'Ext4-Bootkommando fehlt im Loader'
grep -F 'sun50i-h616-t95-axp313-tanix-6.18.dtb' < <(strings -a "$work/u-boot-sunxi-with-spl.bin") >/dev/null || die 'Kandidaten-DTB fehlt im Loader'

for file in u-boot-sunxi-with-spl.bin u-boot.bin u-boot.dtb u-boot.map; do
    install -m 0644 "$work/$file" "$artifact/$file"
done
install -m 0644 "$work/.config" "$artifact/u-boot.config"
install -m 0644 "$base/bl31.bin" "$artifact/bl31.bin"
install -m 0644 "$work/cmd/t95_ac300.c" "$artifact/t95_ac300.c"
install -m 0644 "$image_dir/$image_name.sha" "$artifact/tanix-image.sha"
printf '%s\n' "$image_sha  $image_name" > "$artifact/tanix-image.SHA256SUM"
cat > "$artifact/BOOT-TARGET.txt" <<'EOF'
scope=host_only_artifact; no_SD_or_eMMC_write
boot_device=mmc 0:1
boot_filesystem=ext4
boot_script=/boot/boot.scr
prefix=/boot/
fdtfile=allwinner/sun50i-h616-t95-axp313-tanix-6.18.dtb
kernel_family=Armbian 6.18.48-current-sunxi64
EOF
install -m 0644 "${BASH_SOURCE[0]}" "$artifact/build-recipe.sh"
{
    printf 'u_boot_commit=%s\nsource_date_epoch=%s\n' "$commit" "$SOURCE_DATE_EPOCH"
    printf 'tf_a_commit=b6c0948400594e3cc4dbb5a4ef04b815d2675808\n'
    printf 'board=H616-T95MAX-AXP313A-V3.0\n'
    printf 'status=BUILT_NOT_HARDWARE_TESTED\n'
    printf 'scope=T95 TOC0/AXP313/AC300 loader; ext4 boot-script bootstrap only\n'
    printf 'tanix_image_sha256=%s\n' "$image_sha"
    printf 'boot=SD mmc 0:1 ext4 /boot/boot.scr; no persistent U-Boot environment\n'
    printf 'sd_write=not_performed\nemmc_write=not_performed\n'
    printf 'compiler=%s\n' "$(aarch64-linux-gnu-gcc -dumpfullversion)"
} > "$artifact/BUILD-METADATA.txt"
(cd "$artifact" && sha256sum -- * > SHA256SUMS && sha256sum -c SHA256SUMS)
printf 'Artefakt: %s\n' "$artifact"
