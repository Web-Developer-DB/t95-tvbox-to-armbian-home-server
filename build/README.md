# Hostseitige Buildkette

Diese Dateien bilden das Laborprotokoll und die hostseitige Konstruktion des
funktionierenden T95-Images ab. Keines der Skripte unter `build/` soll eine
SD-Karte, FEL-Hardware oder die interne eMMC öffnen; Schreibvorgänge auf eine
SD sind ausschließlich unter `tools/` und verlangen ein Bestätigungstoken.

Der aktuelle, auf Hardware geprüfte Startpfad ist in
[../docs/RELEASE.md](../docs/RELEASE.md) beschrieben. Ältere Buildartefakte
mit `BUILT_NOT_HARDWARE_TESTED` bleiben unverändert als historische,
hashbare Beweise erhalten: Ihr Status beschreibt den Zeitpunkt des jeweiligen
Host-Builds, nicht den späteren Hardwaretest des zusammengesetzten Images.

## Relevante Buildreihenfolge

```bash
export REPO=/pfad/zum/t95-h616-axp313a-projekt
cd "$REPO"

# 1. Geprüfte Armbian-XZ unter images/ vorbereiten (nur Host-Dateien)
bash build/prepare-t95-tanix-6.18-source.sh

# 2. T95-markierten 6.18-DTB aus der geprüften Tanix-Eingabe ableiten
bash build/build-t95-tanix-6.18-dtb.sh

# 3. Zusammengesetztes Rohimage aus Loader, DTB und Rootfs erzeugen
bash build/assemble-t95-tanix-6.18-ext4-image.sh

# 4. Das Rohimage in ein öffentliches, zugangsdatenfreies Image transformieren
bash build/harden-t95-release-image.sh t95-tanix-6.18-hardened-YYYYMMDD-HHMMSS

# 5. Den Härtungsnachweis gegen das private Quellartefakt auditieren
export SOURCE_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-ext4-image-20260914-101300"
export HARDENED_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-hardened-YYYYMMDD-HHMMSS"
bash build/audit-t95-generic-release-image.sh "$HARDENED_ARTIFACT" "$SOURCE_ARTIFACT"

# 6. Erst danach GitHub-Release-Assets erzeugen
T95_RELEASE_ARTIFACT="$HARDENED_ARTIFACT" \
  bash build/create-t95-release-asset.sh v0.1.1-hardened-experimental
```

Der Härtungsschritt sperrt den Root-Account, entfernt alle Hostschlüssel und
die Root-Account-Backups, erzeugt eine Hostkey-Initialisierung vor
`ssh.service`, ersetzt die Armbian-Nach-SSH-Neuerzeugung und bereinigt freie
Ext4-Blöcke. Der Audit sucht anschließend die Payloads des privaten
Ausgangsartefakts im kompletten Ergebnisimage. Das Resultat ist ein
**generisches**, nicht direkt loginfähiges Download-Image; eine lokale
Personalisierung vor dem SD-Schreiben erfolgt mit
`tools/provision-t95-release-image.sh`.

Die Eingabehashes, exakten Artefakte und die nichtreproduzierbare Signaturgrenze
des TOC0-Loaders sind in `docs/RELEASE.md` festgehalten. Der Loader basiert
auf U-Boot `v2024.04`/`25049ad560826f7dc1c4740883b0016014a59789` und TF-A
`v2.10`/`b6c0948400594e3cc4dbb5a4ef04b815d2675808`.

## Privater Signaturschlüssel

`build/keys/` wird niemals veröffentlicht. Der vorhandene TOC0-Loader ist
mit einem lokalen Experimentierschlüssel signiert. Dieser Schlüssel ist weder
für den praktischen Einsatz des bereitgestellten Release-Images erforderlich
noch darf er Teil eines GitHub-Repositories werden. Ohne ihn ist ein
bitidentischer Neubau des signierten Binaries nicht möglich. Einen Ersatzschlüssel
nicht ohne separate Analyse der Secure-Boot-Vertrauenskette verwenden.

## Historische Diagnosewerkzeuge

Die übrigen `build/build-t95-*.sh`-Skripte und Unterlagen dokumentieren den
schrittweisen Weg über FEL, U-Boot, AC300 und ältere Kernelversuche. Sie sind
kein Update-Mechanismus für die aktuelle Server-SD. Ihre Ergebnisse und
Grenzen sind in der öffentlichen [Testmatrix](../docs/VALIDATION.md)
zusammengefasst; das vollständige Laborjournal bleibt privat.
