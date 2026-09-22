#!/usr/bin/env bash
# Produce a labeled T95 candidate DTB from the verified Armbian 6.18 Tanix DTB.
# This script is host-only and never opens an SD card or the T95 eMMC.
# CHANGE-ID: DTB
# T95-CHANGE: add T95 identity and retain the SPL-confirmed DCDC3 DRAM rail.
# PORTING-NOTE: re-check compatible strings, PHY address, reset, clocks and DRAM voltage.
set -euo pipefail
umask 022

project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
compare_dir="$project/build/work/tanix-26.8.4-compare"
rootfs="$compare_dir/tanix-rootfs.ext4"
rootfs_sha='b19cde604d656071b8a1084acd94fe9f9c2a14606073ce351af78a6d5ec456f2'
source_path='/boot/dtb-6.18.48-current-sunxi64/allwinner/sun50i-h616-tanix-tx6s-axp313.dtb'
source_sha='d9d9143daca18557f11b15ba028f378254015f6f34c0c3db4469825bd83ffd0b'
output_name='sun50i-h616-t95-axp313-tanix-6.18.dtb'
build_id="${T95_BUILD_ID:-t95-tanix-6.18-dtb-$(date +%Y%m%d-%H%M%S)}"

[[ "$build_id" =~ ^t95-tanix-6\.18-dtb-[0-9]{8}-[0-9]{6}$ ]] || exit 2
artifact="$project/build/artifacts/$build_id"
die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
for tool in debugfs fdtput fdtget dtc sha256sum; do
    command -v "$tool" >/dev/null || die "Fehlt: $tool"
done
[[ -f "$rootfs" ]] || die 'Extrahiertes Tanix-Rootfs fehlt; erst Offline-Vergleich ausführen'
[[ $(sha256sum "$rootfs" | cut -d' ' -f1) == "$rootfs_sha" ]] || die 'Tanix-Rootfs-Hash falsch'
mkdir -p "$artifact"
[[ ! -e "$artifact/SHA256SUMS" ]] || die 'Fertiges Artefakt wird nicht überschrieben'

debugfs -R "dump -p $source_path $artifact/source-tanix.dtb" "$rootfs" 2>/dev/null
[[ $(sha256sum "$artifact/source-tanix.dtb" | cut -d' ' -f1) == "$source_sha" ]] || die 'Extrahierter Tanix-DTB-Hash falsch'
install -m 0644 "$artifact/source-tanix.dtb" "$artifact/$output_name"

# The hardware wiring remains the verified Tanix reference.  Board identity is
# explicit so U-Boot can select an unambiguous T95 filename.  SPL trains the
# tested DDR3L at 1.36 V; Linux must not subsequently reduce DCDC3 to 1.20 V.
fdtput -ts "$artifact/$output_name" / model 'T95 H616 AXP313A (Tanix 6.18 candidate)'
fdtput -ts "$artifact/$output_name" / compatible \
    'mbox,t95-axp313' 'tanix,tx6s-axp313' 'tanix,tx6s' 'allwinner,sun50i-h616'
fdtput -t i "$artifact/$output_name" /soc/i2c@7081400/pmic@36/regulators/dcdc3 regulator-min-microvolt 1360000
fdtput -t i "$artifact/$output_name" /soc/i2c@7081400/pmic@36/regulators/dcdc3 regulator-max-microvolt 1360000

[[ $(fdtget -ts "$artifact/$output_name" / model) == 'T95 H616 AXP313A (Tanix 6.18 candidate)' ]] || die 'DTB-Modell nicht gesetzt'
fdtget -ts "$artifact/$output_name" / compatible | tr ' ' '\n' | grep -Fxq 'mbox,t95-axp313' || die 'T95-Kompatibilitaet fehlt'
fdtget -ts "$artifact/$output_name" /soc/ethernet@5030000 compatible | tr ' ' '\n' | grep -Fxq 'allwinner,sun50i-h616-internal-emac' || die 'H616-internal-EMAC fehlt'
fdtget -ts "$artifact/$output_name" /soc/ethernet@5030000/mdio-mux/mdio@1/ethernet-phy@0 compatible | tr ' ' '\n' | grep -Fxq 'allwinner,sun50i-h618-ac300-ephy' || die 'AC300-PHY fehlt'
[[ $(fdtget -ti "$artifact/$output_name" /soc/i2c@7081400/pmic@36/regulators/dcdc3 regulator-min-microvolt) == 1360000 ]] || die 'DRAM-Minimalspannung stimmt nicht'
[[ $(fdtget -ti "$artifact/$output_name" /soc/i2c@7081400/pmic@36/regulators/dcdc3 regulator-max-microvolt) == 1360000 ]] || die 'DRAM-Maximalspannung stimmt nicht'

dtc -q -I dtb -O dts -o "$artifact/$output_name.dts" "$artifact/$output_name"
cat > "$artifact/DTB-NOTES.txt" <<'EOF'
scope=host_only_candidate; no_SD_or_eMMC_write
base=Armbian 26.8.4 Tanix TX6s AXP313 DTB for kernel 6.18.48
change_1=model identifies the T95 candidate
change_2=compatible prepends mbox,t95-axp313 and retains Tanix/H616 fallback
change_3=DCDC3 regulator min/max fixed at 1360000uV to match SPL DDR3L setup
unchanged=all remaining hardware wiring, AC300 internal PHY address 0, MDIO mux, SID calibration
limit=not_hardware_tested; do not use with any 6.12 kernel
target_boot_path=/boot/dtb-6.18.48-current-sunxi64/allwinner/sun50i-h616-t95-axp313-tanix-6.18.dtb
EOF
install -m 0644 "${BASH_SOURCE[0]}" "$artifact/build-recipe.sh"
{
    printf 'board=H616-T95MAX-AXP313A-V3.0\n'
    printf 'kernel_release=6.18.48-current-sunxi64\n'
    printf 'status=BUILT_NOT_HARDWARE_TESTED\n'
    printf 'source_dtb_sha256=%s\nsource_rootfs_sha256=%s\n' "$source_sha" "$rootfs_sha"
    printf 'dram_voltage_uV=1360000\n'
    printf 'scope=Tanix 6.18 DTB with T95 identity and DCDC3 1.36V; no kernel build\n'
    printf 'sd_write=not_performed\nemmc_write=not_performed\n'
} > "$artifact/BUILD-METADATA.txt"
(cd "$artifact" && sha256sum -- * > SHA256SUMS && sha256sum -c SHA256SUMS)
printf 'Artefakt: %s\n' "$artifact"
