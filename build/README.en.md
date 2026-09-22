# Host-side build chain

[Deutsch](README.md) | **English**

These files document the laboratory process and host-side construction of the
working T95 image. No script under `build/` should open an SD card, FEL device,
or internal eMMC. SD write operations live exclusively under `tools/` and
require a confirmation token.

The current hardware-validated boot path is described in
[../docs/RELEASE.en.md](../docs/RELEASE.en.md). Older artifacts marked
`BUILT_NOT_HARDWARE_TESTED` remain unchanged as historical, hash-verifiable
evidence. That status describes the host build at that time, not the later
hardware test of the assembled image.

## Public porting start for other H616 boxes

Do not use the historical T95 assembly recipes for a different, similar H616
board. The public starting path is entirely host-side, requires no private key,
and opens no block devices:

```bash
bash build/setup-h616-porting-host.sh --check
bash build/fetch-h616-porting-sources.sh
bash build/build-h616-fel-egon.sh
```

This creates a volatile `eGON.BT0` FEL diagnostic loader. An SD TOC0 test
should be considered only after UART, PMIC, and DRAM have been confirmed on
the other board. The test is optional, requires your own local key, and may
still fail because of the Secure Boot trust chain:

```bash
bash build/build-h616-toc0-test.sh --key /absolute/path/to/your-key.pem
```

Source commits and security boundaries are documented in
[PORTING_SOURCES.en.md](PORTING_SOURCES.en.md) and
[../docs/PORTING.en.md](../docs/PORTING.en.md).

## Relevant build sequence

```bash
export REPO=/path/to/t95-h616-axp313a-project
cd "$REPO"

# 1. Prepare the verified Armbian XZ under images/ (host files only)
bash build/prepare-t95-tanix-6.18-source.sh

# 2. Derive the T95-labelled 6.18 DTB from the verified Tanix input.
#    The build keeps AXP313A DCDC3 at 1.36 V in SPL and the Linux DTB.
bash build/build-t95-tanix-6.18-dtb.sh

# 3. Assemble the raw image from loader, DTB, and root filesystem
bash build/assemble-t95-tanix-6.18-ext4-image.sh

# 4. Transform the raw image into a public image without credentials
bash build/harden-t95-release-image.sh t95-tanix-6.18-hardened-YYYYMMDD-HHMMSS

# 5. Audit the hardening result against the private source artifact
export SOURCE_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-ext4-image-20260914-101300"
export HARDENED_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-hardened-YYYYMMDD-HHMMSS"
bash build/audit-t95-generic-release-image.sh "$HARDENED_ARTIFACT" "$SOURCE_ARTIFACT"

# 6. Only then create the GitHub release assets
T95_RELEASE_ARTIFACT="$HARDENED_ARTIFACT" \
  bash build/create-t95-release-asset.sh v1.0.1
```

The hardening step locks the root account, removes all host keys and root
account backups, creates host keys before `ssh.service`, replaces Armbian's
post-SSH key regeneration, and scrubs free ext4 blocks. The audit then searches
the complete output image for payloads from the private source artifact. The
result is a **generic** download image that cannot be logged into directly. It
is personalized locally before writing to SD with
`tools/provision-t95-release-image.sh`.

Input hashes, exact artifacts, and the non-reproducible signature boundary of
the TOC0 loader are documented in `docs/RELEASE.en.md`. The loader is based on
U-Boot `v2024.04`/`25049ad560826f7dc1c4740883b0016014a59789` and TF-A
`v2.10`/`b6c0948400594e3cc4dbb5a4ef04b815d2675808`.

## Private signing key

`build/keys/` is never published. The existing TOC0 loader was signed with a
local experimental key. This key is not required to use the supplied release
image and must not become part of a GitHub repository. A bit-identical rebuild
of the signed binary is impossible without it. Do not use a replacement key
without a separate analysis of the Secure Boot trust chain.

## Historical diagnostic tools

The remaining `build/build-t95-*.sh` scripts and notes document the gradual
path through FEL, U-Boot, AC300, and older kernel experiments. They are not an
update mechanism for the current server SD card. Their results and limitations
are summarized in the public [test matrix](../docs/VALIDATION.en.md); the full
laboratory journal remains private.
