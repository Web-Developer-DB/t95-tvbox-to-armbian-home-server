<a id="publishing-on-github"></a>

# 🌐 Publishing on GitHub

[Deutsch](GITHUB-PUBLISH.md) | **English**

This module lives in the main repository under `server/samba-usb/` and can be
published with the T95 Armbian project while retaining reproducible scripts and
technical documentation.

| Decision | Matching path |
| --- | --- |
| 📁 Maintain within the T95 project | [Main repository](#publish-the-main-repository); existing module location |
| 🧩 Deliberately maintain separately | [Standalone repository](#standalone-repository-optional) |
| ✅ Before each push | [Check files and manifest](#check-before-pushing) |

**Run on:** the Linux PC, in the local repository copy, as a user with GitHub push access. Adapt sample paths first.

<a id="publish-the-main-repository"></a>

## 📁 Publish the main repository

```bash
cd /path/to/t95-tvbox-to-armbian-home-server
git add README.md server/samba-usb
git commit -m "Document Samba and dynamic USB home-server setup"
git push
```

<a id="standalone-repository-optional"></a>

## 🧩 Standalone repository (optional)

Only if the module is deliberately maintained separately:

```text
T95-Samba-USB-Setup/
```

Then run `git init`, `git add .`, and create an appropriate commit.

<a id="check-before-pushing"></a>

## ✅ Check before pushing

```bash
git status
git diff --cached
cd server/samba-usb
sha256sum -c MANIFEST.sha256
```

Never commit passwords, `passdb.tdb`, private keys, or system images.
`.gitignore` reduces common mistakes but does not replace manual review. After
module changes, update `MANIFEST.sha256` with the new hashes and verify it
again.
