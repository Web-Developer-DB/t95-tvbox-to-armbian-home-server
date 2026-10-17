<a id="github-veröffentlichungscheckliste"></a>

# 🌐 GitHub-Veröffentlichungscheckliste

**Deutsch** | [English](PUBLISHING.en.md)

Diese Checkliste trennt öffentliche Werkzeuge und Dokumentation von
forensischen Daten, privaten Artefakten und personalisierten Systemzuständen.

| Phase | Was muss feststehen? |
| --- | --- |
| 🔎 [Quellsatz prüfen](#öffentlicher-quellsatz) | Nur freigegebene Dateien; private Images und Schlüssel bleiben lokal |
| 📦 [Release-Assets prüfen](#freigabe-des-release-assets) | Härtung, Prüfsummen und dokumentierte Hardwareabnahme |
| 🌐 [Veröffentlichen](#dokumentation-und-releasebeschreibung-synchron-veröffentlichen) | Merge → öffentliche Links prüfen → Release-Text übernehmen |

**Ausführungsort:** Linux-PC, lokale Repository-Kopie; für Maintainer. Pfade und private Eingaben vor dem Ausführen anpassen.

<a id="öffentlicher-quellsatz"></a>

## 📁 Öffentlicher Quellsatz

In ein neues, sauberes Repository gehören:

- `README.md`, `.gitignore`, die freigegebenen Dateien unter `docs/`,
  `build/` und `tools/` einschließlich der Härtungs- und
  Personalisierungsskripte;
- die allgemeine SD-Backup-Anleitung `docs/BACKUP.md` (ohne ein persönliches
  Backup-Abbild);
- die vier bereinigten Fotos unter `docs/images/`;
- eine vom Maintainer gewählte `LICENSE`;
- die sechs Dateien eines frisch erzeugten
  `release-assets/v1.0.1/`-Ordners als GitHub-
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

<a id="niemals-veröffentlichen"></a>

## 🔒 Niemals veröffentlichen

- `build/keys/`, `backups/`, `captures/`, `evidence/`, `Archiv/`, `.agents/`,
  `.codex/`, `AGENTS.md`, `T95_Armbian.txt` und private Laborjournale;
- `build/work/`, `build/sources/`, historische `build/artifacts/`,
  Image-Downloads, Rohimages und jede mit einem individuellen Passwort
  personalisierte Image-Datei samt `.t95-provisioned-manifest`;
- eMMC- oder SD-Backups nach Ersteinrichtung: Sie können Accounts,
  Hostschlüssel und private Konfiguration enthalten.

Die `.gitignore` schützt vor üblichen Versehen, ersetzt aber nicht die
Prüfung von `git status --ignored`.

<a id="freigabe-des-release-assets"></a>

## ✅ Freigabe des Release-Assets

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
     bash "$REPO/build/create-t95-release-asset.sh" v1.0.1
   cd "$REPO/release-assets/v1.0.1"
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

<a id="dokumentation-und-releasebeschreibung-synchron-veröffentlichen"></a>

## 🌐 Dokumentation und Releasebeschreibung synchron veröffentlichen

Die Dokumentationsüberarbeitung wird auf dem bestehenden Arbeitsbranch geliefert.
Merge und Änderung der öffentlichen Releasebeschreibung sind eigene Veröffentlichungsschritte.
Diese Reihenfolge einhalten:

1. **Vor dem Merge:** beide Sprachen, frühere Sprungmarken, Bilder, ausführbare
   Beispiele und Modul-Manifeste prüfen. Verpflichtende Personalisierung,
   exakte Platine, Kernel-Sperre und SD-Löschhinweis in
   [Release-Text](GITHUB_RELEASE_NOTES.md) und [englischer Fassung](GITHUB_RELEASE_NOTES.en.md) erhalten.
2. **Nach `main` mergen.** Neue absolute `main`-Links können vorher 404 liefern;
   vor dem Merge werden stattdessen die zugehörigen Repository-Dateien geprüft.
3. **Nach dem Merge die öffentlichen Ziele öffnen:** beide Installationsanleitungen,
   Alltag, Fehlerhilfe, Testmatrix und alle fünf gemeinsamen/Modul-Starter.
   Erreichbarkeit und einheitliche Quellreferenz `main` bestätigen. Dafür keine
   Installationsbefehle auf dem Entwicklungs-PC ausführen.
4. **Erst dann die öffentliche Releasebeschreibung aktualisieren:** den vorbereiteten
   Text übernehmen. Passwort-Personalisierung, Installationslink und Kernel-Schutz
   stehen vor den Download-Dateien. Beide Sprachfassungen der Anleitung verlinken.
5. Die Release-Seite als Leser öffnen und Installations-/Hilfelinks verfolgen.
   Veröffentlichung erst nach tatsächlicher Änderung der Seite als erledigt markieren.

Image-Assets, Release-Version und Image-Prüfsummen bleiben bei dieser
Dokumentationsänderung erhalten. Bestätigte Modul-Funktionen und gesonderte
Hardwareprüfungen in der Testmatrix getrennt dokumentieren.

<a id="lizenz--und-upstream-prüfung"></a>

## 📄 Lizenz- und Upstream-Prüfung

Vor Veröffentlichung eine passende Lizenz auswählen und Lizenzpflichten von
Armbian, Linux, TF-A, U-Boot und übernommenen Patchanteilen separat prüfen.
Dieses Dokument ist keine Rechtsberatung.
