# GitHub-Veröffentlichungscheckliste

Diese Checkliste trennt öffentliche Werkzeuge und Dokumentation von
forensischen Daten, privaten Artefakten und personalisierten Systemzuständen.

## Öffentlicher Quellsatz

In ein neues, sauberes Repository gehören:

- `README.md`, `.gitignore`, die freigegebenen Dateien unter `docs/`,
  `build/` und `tools/` einschließlich der Härtungs- und
  Personalisierungsskripte;
- die allgemeine SD-Backup-Anleitung `docs/BACKUP.md` (ohne ein persönliches
  Backup-Abbild);
- die vier bereinigten Fotos unter `docs/images/`;
- eine vom Maintainer gewählte `LICENSE`;
- die sechs Dateien eines frisch erzeugten
  `release-assets/v1.0.0/`-Ordners als GitHub-
  **Release-Assets**, nicht als Git-Commit.

Vor dem ersten Push in einer frischen Kopie prüfen:

```bash
git status --ignored
git ls-files
rg -n -i 'password|passwd|authorized_keys|private key|BEGIN.*PRIVATE' .
```

Treffer dürfen nur die Härtungsbeschreibung, Platzhalter und Hinweise auf den
ausgeschlossenen TOC0-Signaturschlüssel betreffen. Es dürfen keine persönlichen
Benutzernamen, lokalen Projektpfade, Passwörter, private Schlüssel, SSH-
Hostschlüssel, IP-/MAC-Aufzeichnungen oder personalisierte Image-Dateien
enthalten sein.

## Niemals veröffentlichen

- `build/keys/`, `backups/`, `captures/`, `evidence/`, `Archiv/`, `.agents/`,
  `.codex/`, `AGENTS.md`, `T95_Armbian.txt` und private Laborjournale;
- `build/work/`, `build/sources/`, historische `build/artifacts/`,
  Image-Downloads, Rohimages und jede mit einem individuellen Passwort
  personalisierte Image-Datei samt `.t95-provisioned-manifest`;
- eMMC- oder SD-Backups nach Ersteinrichtung: Sie können Accounts,
  Hostschlüssel und private Konfiguration enthalten.

Die `.gitignore` schützt vor üblichen Versehen, ersetzt aber nicht die
Prüfung von `git status --ignored`.

## Freigabe des Release-Assets

1. Das gehärtete Artefakt gegen das private Quellartefakt auditieren:

   ```bash
   export REPO=/pfad/zum/t95-h616-axp313a-projekt
   export SOURCE_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-ext4-image-20260914-101300"
   export HARDENED_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-hardened-20260915-120000"
   bash "$REPO/build/audit-t95-generic-release-image.sh" \
     "$HARDENED_ARTIFACT" "$SOURCE_ARTIFACT"
   ```

2. Paket erzeugen und die sechs Dateien prüfen:

   ```bash
   T95_RELEASE_ARTIFACT="$HARDENED_ARTIFACT" \
     bash "$REPO/build/create-t95-release-asset.sh" v1.0.0
   cd "$REPO/release-assets/v1.0.0"
   sha256sum -c SHA256SUMS
   xz -t *.img.xz
   ```

3. In der Releasebeschreibung deutlich nennen: exakte Boardrevision,
   SD-only, stabil getesteter hardwaregebundener Status, eMMC unverändert, lokale verpflichtende
   Passwort-Personalisierung, neue SSH-Fingerprint-Prüfung und die offenen
   Tests. [GITHUB_RELEASE_NOTES.md](GITHUB_RELEASE_NOTES.md) ist der
   Textentwurf.

4. Die Endanwender-Abnahme (Start, sauberes Herunterfahren, SSH und
   Dateizugriff) mit einer lokal personalisierten SD im privaten Journal
   festhalten. Zusätzliche Langzeit- und Peripherietests bleiben optionale
   Weiterentwicklung und sind keine Voraussetzung für den stabil getesteten
   Grundstand.

## Lizenz- und Upstream-Prüfung

Vor Veröffentlichung eine passende Lizenz auswählen und Lizenzpflichten von
Armbian, Linux, TF-A, U-Boot und übernommenen Patchanteilen separat prüfen.
Dieses Dokument ist keine Rechtsberatung.
