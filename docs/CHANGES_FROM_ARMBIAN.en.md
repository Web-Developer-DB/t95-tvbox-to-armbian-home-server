# Change inventory: Armbian base → T95

[Deutsch](CHANGES_FROM_ARMBIAN.md) | **English**

This is the technical, public, reproducible change reference for the compact
overview in [README.en.md](../README.en.md).

## Pinned baseline

| Property | Baseline |
| --- | --- |
| Distribution | Armbian 26.8.4, Debian 13 (Trixie) |
| Reference board | Tanix TX6s / AXP313 |
| Input image | `Armbian_26.8.4_Tanix-tx6s-axp313_trixie_current_6.18.48_minimal.img.xz` |
| Input SHA-256 | `f08a37afef45bca2b2a727b2d5e48d1d7521ff533f7ebc0ec03f52ada677870c` |
| Kernel | `6.18.48-current-sunxi64` |
| U-Boot | v2024.04, `25049ad560826f7dc1c4740883b0016014a59789` |
| TF-A | v2.10, `b6c0948400594e3cc4dbb5a4ef04b815d2675808` |
| Target board | `H616-T95MAX-AXP313A-V3.0` |
| Supported boot medium | microSD; eMMC boot is not supported |

`build/prepare-t95-tanix-6.18-source.sh` verifies this input by fixed SHA-256.
Images and build artifacts remain local or are supplied only as GitHub release
assets.

## Change matrix

| ID | Armbian baseline | Project file/patch | Change and purpose | Verify when porting | Evidence |
| --- | --- | --- | --- | --- | --- |
| `BASE` | verified Tanix image | `build/prepare-t95-tanix-6.18-source.sh` | offline extraction/hash check for reproducible input | image version, layout, rootfs hash | `sha256sum`, `e2fsck -fn` |
| `BOOT` | generic Allwinner path | `0001-t95-axp313-h616-fel-bringup.patch`, `build-h616-fel-egon.sh`; historical `build-t95-ac300-ext4boot.sh` | RAM-only eGON/FEL reference; optional T95 TOC0/U-Boot loader | SoC, Boot ROM contract, SD offset, DRAM | eGON/TOC0 header, UART banner |
| `TFA` | matching TF-A | fetch/build scripts | BL31 paired with T95 U-Boot | SoC platform, BL31 compatibility | pinned commit, artifact hash |
| `DTB` | Tanix TX6s/AXP313 DTB | `build-t95-tanix-6.18-dtb.sh` | T95 identity with H616/AC300 compatibility | board, PHY address, MDIO, clocks, reset | DTS/DTB inspection, hash |
| `ENV` | generic boot selection | assembly script, `armbianEnv.txt` | T95 DTB, serial console, ext4 root, diagnostics | kernel path, root UUID, console | environment hash, UART log |
| `AXP313` | board-specific SPL/DRAM | patch `0001` | AXP313A and tested 2 GiB DDR3 timing at 600 MHz | RAM, PMIC, voltage, frequency | `DRAM: 2048 MiB`, cold boot |
| `AC300` | Ethernet not guaranteed | patch `0002`, T95 DTB | AC300/RMII pre-initialization | PHY, reset, clock, MAC, MDIO, link | kernel log, DHCP, `iperf3` |
| `KMOD` | standard userspace | historical patch `0003` | no final kernel rebuild; diagnostics only | ABI, modules, initramfs order | `modinfo`, UART log |
| `HARDEN` | raw image not public entry point | harden/audit scripts | lock root, remove host keys, create keys before ssh, scrub image | rerun for every image update | manifest, audit, secret scan |
| `RELEASE` | no image in Git | create/write scripts | versioned, checked release asset | target card via `lsblk`, removable SD only | SHA-256, size/TOC0/ext4 checks |
| `SAMBA` | not minimal image | `server/samba-usb/` | optional Samba/USB automount layer | package, mounts, user, filesystem | installation/restore checks |
| `PORTING` | no Armbian image change | public porting docs and host build scripts | safe host-side bring-up with optional user key | UART, FEL, Secure Boot, real board data | host check, commits, eGON manifest, UART log |

## Unchanged components

- Debian/Armbian userspace and verified 6.18 kernel are the base; final 6.18
  does not need a kernel rebuild.
- Public release generation does not read or overwrite eMMC; after boot it may
  be used as a separate ext4 data drive.
- USB, rootfs structure, and standard packages are not replaced for Samba or
  Ethernet. Samba is an optional post-installation.
- No captures, backups, raw images, individual hardware IDs, or private keys
  belong in the public repository.

## Port another H616 board

1. Record version, kernel, partition layout, and rootfs hash (`BASE`).
2. Isolate TOC0, SD offset, DRAM, and PMIC first (`BOOT`, `TFA`, `AXP313`).
3. Adapt only confirmed DTB data; compare PHY/reset/clocks/UART/root path with
   UART logs and board evidence (`DTB`, `ENV`).
4. Test AC300/RMII and link before changing initramfs or Samba (`AC300`,
   `KMOD`).
5. Audit every release offline; add local passwords only after downloading and
   before writing your own SD card (`HARDEN`, `RELEASE`).

Change only the failed layer. A new kernel or eMMC write is never a substitute
for missing hardware evidence.

## Script markers and maintenance

`ARMBIAN-BASE` marks an unchanged Armbian step, `T95-CHANGE` a project-specific
change, and `PORTING-NOTE` a value to re-check on other hardware. For every new
Armbian release, update the relevant baseline, IDs, evidence, build/audit/
secret/link checks, then commit manifest, README, and this inventory together.
