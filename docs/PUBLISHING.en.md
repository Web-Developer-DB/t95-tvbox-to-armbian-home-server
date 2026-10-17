# GitHub publishing checklist

[Deutsch](PUBLISHING.md) | **English**

This checklist separates public tools and documentation from forensic data,
private artifacts, and personalized system states.

## Public source set

A new, clean repository should contain:

- `README.md`, `.gitignore`, approved files under `docs/`, `build/`, and
  `tools/`, including hardening and personalization scripts;
- `docs/BACKUP.en.md` without a personal backup image;
- four sanitized photos under `docs/images/`;
- a license selected by the maintainer;
- the six files in a freshly generated `release-assets/v1.0.1/` directory as
  GitHub **release assets**, not Git commits.

Before the first push, check a fresh copy:

```bash
git status --ignored
git ls-files
rg -n -i 'password|passwd|authorized_keys|private key|BEGIN.*PRIVATE' .
```

Matches may refer only to hardening descriptions, placeholders, and notes on
the excluded TOC0 signing key. Do not publish usernames, local paths,
passwords, private keys, SSH host keys, IP/MAC captures, or personalized image
files.

## Never publish

- `build/keys/`, `backups/`, `captures/`, `evidence/`, `Archiv/`, `.agents/`,
  `.codex/`, `AGENTS.md`, `T95_Armbian.txt`, or private laboratory journals;
- `build/work/`, `build/sources/`, historical `build/artifacts/`, downloaded
  or raw images, and every image personalized with an individual password,
  including its `.t95-provisioned-manifest`;
- eMMC or SD backups after first-run setup, as they may contain accounts, host
  keys, and private configuration.

`.gitignore` prevents common mistakes but does not replace checking
`git status --ignored`.

## Approve a release asset

1. Audit the hardened artifact against the private source artifact:

   ```bash
   export REPO=/path/to/t95-h616-axp313a-project
   export SOURCE_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-ext4-image-20260914-101300"
   export HARDENED_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-hardened-20260915-120000"
   bash "$REPO/build/audit-t95-generic-release-image.sh" \
     "$HARDENED_ARTIFACT" "$SOURCE_ARTIFACT"
   ```

2. Create the package and verify the six files:

   ```bash
   T95_RELEASE_ARTIFACT="$HARDENED_ARTIFACT" \
     bash "$REPO/build/create-t95-release-asset.sh" v1.0.1
   cd "$REPO/release-assets/v1.0.1"
   sha256sum -c SHA256SUMS
   xz -t *.img.xz
   ```

3. State the exact board revision, SD-only operation, stable hardware-specific
   status, untouched eMMC, required local password personalization, new SSH
   fingerprint verification, and open tests in the release description.
   [GITHUB_RELEASE_NOTES.en.md](GITHUB_RELEASE_NOTES.en.md) is the text draft.

4. Record end-user acceptance—boot, clean shutdown, SSH, and file access—with
   a locally personalized SD in a private journal. Further long-term and
   peripheral tests are optional follow-up work, not requirements for the
   stable tested baseline.

## Publish documentation and release description together

The documentation update is delivered on its existing working branch.
Merging and editing the public release description are separate publication steps.
Use this order:

1. **Before merge:** check both languages, previous section anchors, images,
   executable examples, and module manifests. Keep the mandatory personalization,
   exact PCB, kernel holds, and SD-erasure notices in
   [the release text](GITHUB_RELEASE_NOTES.en.md) and its [German counterpart](GITHUB_RELEASE_NOTES.md).
2. **Merge to `main`.** Until then, new absolute `main` links can return 404;
   checking their repository-relative source targets is the pre-merge check.
3. **After merge, open the public targets:** both installation guides, everyday
   use, troubleshooting, validation, and all five shared/module launchers.
   Confirm successful responses and a consistent `main` source ref; do not run
   installation commands on the development PC for this check.
4. **Then update the public release description** using the prepared text.
   Keep the password-personalization warning, installation link, and kernel
   protection before download assets. Include both language-guide links.
5. Open the release page as a reader and follow its installation/help links.
   Do not mark publication complete until the actual page is updated.

Image assets, release versions, and image hashes are unchanged by this
documentation update. Keep the maintainer's confirmed module results and
separately tracked hardware checks distinct in the validation matrix.

## License and upstream review

Before publishing, select a suitable license and separately review licensing
obligations for Armbian, Linux, TF-A, U-Boot, and reused patch fragments. This
document is not legal advice.
