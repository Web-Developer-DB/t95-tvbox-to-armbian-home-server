# Public sources for H616 porting

[Deutsch](PORTING_SOURCES.md) | **English**

This file separates reproducible sources from local laboratory artifacts. The
tools download only into `build/sources/` and `build/work/`; both directories
are intentionally excluded from version control.

| Component | Source | Pinned revision / checksum | Purpose |
| --- | --- | --- | --- |
| U-Boot | `https://github.com/u-boot/u-boot.git` | `25049ad560826f7dc1c4740883b0016014a59789` | H616 SPL, eGON and TOC0 test loaders |
| TF-A | `https://github.com/ARM-software/arm-trusted-firmware.git` | `b6c0948400594e3cc4dbb5a4ef04b815d2675808` | `bl31.bin` for `sun50i_h616` |
| Armbian Tanix input | download manually from the official Armbian release | File `Armbian_26.8.4_Tanix-tx6s-axp313_trixie_current_6.18.48_minimal.img.xz`; SHA-256 `f08a37afef45bca2b2a727b2d5e48d1d7521ff533f7ebc0ec03f52ada677870c` | Reference root filesystem and Tanix DTB |

The Armbian file is intentionally not downloaded automatically from an
unversioned URL. Its filename and checksum must match before it is placed in
`images/`. A new Armbian version, layout, kernel, or checksum is a new input
and must be validated separately.

The T95 TOC0 loader in release v1.0.0 is a tested binary artifact. Its
historical private signing key is not part of this repository. A custom TOC0
test loader is therefore possible only with a locally managed user key and
without any promise of Secure Boot compatibility.
