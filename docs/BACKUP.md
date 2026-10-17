# Vollständiges Armbian-SD-Backup

**Deutsch** | [English](BACKUP.en.md)

Diese Anleitung erstellt ein sektorgetreues Backup der **gesamten** Armbian-
SD-Karte und stellt es auf derselben oder einer mindestens gleich großen
Ersatzkarte wieder her. Bootloader, Partitionstabelle, DTB, Kernel, Rootfs,
Benutzerkonten und Konfigurationen werden gemeinsam erfasst.
Die SD-Sicherung enthält keine Daten auf separaten USB-Laufwerken oder eMMC.
Führe alle PC-Schritte im selben Terminalfenster aus; dort bleiben die
ausgewählten Pfade bis zum Ende gespeichert.

> [!CAUTION]
> Ein vollständiges Abbild kann persönliche Konten, SSH-Konfigurationen,
> Samba-Datenbanken, Logs und weitere Geheimnisse enthalten. Es ist ein
> privates Recovery-Backup und darf nicht in GitHub, in ein öffentliches
> Release oder in einen Cloud-Ordner ohne Verschlüsselung hochgeladen werden.

**Ausführungsort:** Schritt 1 auf der T95 als normaler SSH-Benutzer mit `sudo`;
alle übrigen Befehle auf dem Linux-PC als normaler Benutzer mit `sudo`.

[Zur Installation](INSTALLATION.md#6-grundsystem-sichern) · [Hilfe](TROUBLESHOOTING.md)

## Voraussetzungen

- Die T95 läuft noch stabil und kann sauber heruntergefahren werden.
- Die SD-Karte wird erst nach dem Herunterfahren aus der Box genommen.
- Der Ubuntu-/Debian-PC besitzt einen Kartenleser und einen **anderen**
  Datenträger mit ausreichend freiem Speicher.
- Die Befehle werden in einer Linux-Shell ausgeführt. Unter Windows ist WSL2
  nur geeignet, wenn SD-Blockgeräte zuverlässig als `/dev/sdX` durchgereicht
  werden; natives Linux wird empfohlen.
- Die Ersatzkarte ist mindestens so groß wie die Quellkarte. Maßgeblich ist
  die Byte-Größe aus `lsblk`, nicht die aufgedruckte Kapazität.

Das Backupziel sollte mindestens die Größe der gesamten SD-Karte als freien
Platz bereitstellen. Die Komprimierung kann bei schlecht komprimierbaren Daten
nahe an die Rohgröße herankommen.

## 1. Box sauber herunterfahren

**Auf der T95, normaler SSH-Benutzer mit `sudo`:**

```bash
sudo poweroff
```

Warten, bis die Box vollständig aus ist. Erst danach die SD-Karte entnehmen
und am Linux-PC anschließen.

## 2. Quellgerät eindeutig identifizieren

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,FSTYPE,MOUNTPOINTS
```

Das Quellgerät ist die komplette wechselbare SD-Karte, zum Beispiel
`/dev/sdX`. Vor jedem Lauf müssen mindestens diese Eigenschaften stimmen:

| Prüfung | Erwartung |
| --- | --- |
| `TYPE` | `disk` |
| `TRAN` | `usb` |
| `RM` | `1` |
| Größe | passt zur zuvor dokumentierten Karte |
| Mountpoints | für den Rohdatenlauf leer |

> [!WARNING]
> Niemals `/dev/sda` aus einem alten Beispiel übernehmen. Die Zuordnung kann
> sich nach jedem Einstecken ändern. Ein falsches `if=`- oder `of=`-Gerät kann
> eine interne SSD oder eine andere Festplatte überschreiben.

Notiere den tatsächlich angezeigten Gerätenamen als `SD_DEVICE`, zum Beispiel:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
export SD_DEVICE=/dev/sdX   # /dev/sdX durch den lsblk-Namen der eigenen SD ersetzen
```

## 3. Partitionen aushängen

Wenn der Desktop die Karte automatisch eingehängt hat, müssen alle
SD-Partitionen vor dem Rohbackup ausgehängt werden. Die Partitionsnummern
zuerst mit `lsblk` prüfen:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
sudo umount "${SD_DEVICE}1"
```

Das Release `v1.0.1` hat eine Partition. Eine Meldung wie „nicht eingehängt“
ist unkritisch. Falls deine Karte weitere Partitionen zeigt, diese ebenfalls
aushängen; das Gerät selbst wird nicht gemountet.

## 4. Komprimiertes Vollbackup erstellen

Einmalig auf Ubuntu/Debian installieren:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
sudo apt update
sudo apt install -y zstd
```

Backupziel und Dateinamen festlegen. Das Ziel muss auf einem **anderen**
Datenträger liegen. Ersetze den Beispielpfad vor dem Ausführen:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
export BACKUP_DIR=/absolute/path/to/T95-Backups
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
IMAGE="$BACKUP_DIR/t95-armbian-full-$STAMP.img.zst"
```

Danach die gesamte Karte einmal lesen und komprimieren:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
set -o pipefail
sudo dd if="$SD_DEVICE" bs=16M iflag=fullblock status=progress \
  | zstd -T0 -6 --check -o "$IMAGE"
```

`if=` zeigt absichtlich auf das vollständige Gerät und nicht auf eine
Partition. Der Vorgang liest die SD-Karte, schreibt aber nicht auf sie oder
auf die interne eMMC. Je nach Kartenleser kann er längere Zeit dauern.

## 5. Backup prüfen und dokumentieren

Zuerst den zstd-Datenstrom testen:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
zstd -t "$IMAGE"
```

Danach eine SHA-256-Prüfsumme erzeugen und direkt kontrollieren:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
(
  cd -- "$(dirname -- "$IMAGE")" || exit 1
  sha256sum -- "$(basename -- "$IMAGE")" > "$(basename -- "$IMAGE").sha256" &&
    sha256sum -c -- "$(basename -- "$IMAGE").sha256"
)
```

Beide Prüfungen müssen erfolgreich sein: `zstd` meldet keinen Fehler und
die Prüfsummenprüfung endet mit `OK`. Die `.sha256`-Datei enthält nur den
Dateinamen, keinen fest gebundenen Ordnerpfad.

**Zusammen aufbewahren:** Image, zugehörige `.sha256`-Datei und die notierte
Quellkartengröße in Byte. Kopiere diesen Sicherungssatz gemeinsam auf einen
zweiten, geschützten Datenträger.

## Wiederherstellung auf dieselbe oder eine Ersatzkarte

Die Wiederherstellung überschreibt die Zielkarte vollständig. Sie ist nur
notwendig, wenn eine Karte ersetzt oder der dokumentierte Systemstand exakt
wiederhergestellt werden soll.

### 1. Zielkarte prüfen

Ersatzkarte einstecken und den Gerätenamen neu ermitteln:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,FSTYPE,MOUNTPOINTS
export SD_DEVICE=/dev/sdX   # /dev/sdX durch den lsblk-Namen der eigenen SD ersetzen
```

Vor dem Schreiben müssen `TYPE=disk`, `TRAN=usb`, `RM=1` und eine mindestens
so große Byte-Größe wie beim Backup bestätigt sein. Alle automatisch
eingehängten Partitionen aushängen:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
sudo umount "${SD_DEVICE}1"
```

### 2. Archiv prüfen

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
export IMAGE=/absolute/path/to/t95-armbian-full-YYYYMMDD-HHMMSS.img.zst
```

Ersetze den Beispielpfad oben durch dein ausgewähltes Archiv. Die passende
Prüfsummendatei muss daneben als `DATEINAME.img.zst.sha256` liegen.
Den folgenden Prüfblock vollständig ausführen.

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
T95_BACKUP_VERIFIED=
T95_BACKUP_SHA256=
if [[ -f "$IMAGE" && -f "$IMAGE.sha256" ]] &&
   read -r T95_BACKUP_SHA256 _ < "$IMAGE.sha256" &&
   [[ "$T95_BACKUP_SHA256" =~ ^[[:xdigit:]]{64}$ ]] &&
   printf '%s  %s\n' "$T95_BACKUP_SHA256" "$IMAGE" | sha256sum -c - &&
   zstd -t -- "$IMAGE"; then
  T95_BACKUP_VERIFIED="$IMAGE"
  printf '%s\n' 'OK: Ausgewähltes Archiv geprüft. Schreiben ist freigegeben.'
else
  printf '%s\n' 'STOPP: Archiv oder Prüfsumme fehlt, ist ungültig oder stimmt nicht. Nicht schreiben.' >&2
  false
fi
```

**Ergebnis:** Nur bei `OK: Ausgewähltes Archiv geprüft. Schreiben ist freigegeben.`
mit Schritt 3 fortfahren. Bei `STOPP` hier bleiben und Archiv/Pfad/Prüfsumme prüfen.
Der Prüfblock vergleicht immer die ausgewählte Datei mit dem gespeicherten
Hash. Dadurch funktionieren auch ältere `.sha256`-Dateien mit einem absoluten
Originalpfad, selbst wenn das Archiv inzwischen verschoben wurde.

Alle weiteren Befehle im selben PC-Fenster ausführen. Nach einer Änderung von
`IMAGE` oder in einem neuen Fenster diesen Schritt erneut ausführen.

### 3. Vollständiges Image schreiben

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
if [[ -n "${T95_BACKUP_VERIFIED:-}" && "$T95_BACKUP_VERIFIED" == "$IMAGE" ]]; then
  set -o pipefail
  if zstd -dc -- "$IMAGE" \
      | sudo dd of="$SD_DEVICE" bs=16M conv=fsync status=progress; then
    sync && sudo udevadm settle
  else
    printf '%s\n' 'STOPP: Schreiben fehlgeschlagen. Karte nicht einsetzen; Fehler prüfen.' >&2
    false
  fi
else
  printf '%s\n' 'STOPP: Zuerst das ausgewählte Archiv in Schritt 2 erfolgreich prüfen.' >&2
  false
fi
```

**Ergebnis:** Der Schreibbefehl muss ohne Fehler enden. Bei einer Fehlermeldung
nicht mit dem Einsatz der Karte fortfahren; [Hilfe öffnen](TROUBLESHOOTING.md).
Dieser Schritt schreibt die komplette Zielkarte einschließlich Bootbereich und
Partitionstabelle. Die interne eMMC wird nicht angesprochen.

### 4. Rücklesen und Einsatz

Partitionstabelle neu einlesen und die Karte prüfen:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
sudo partprobe "$SD_DEVICE"
sudo udevadm settle
lsblk -b -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINTS "$SD_DEVICE"
```

Dieses Release hat genau eine ext4-Partition: `${SD_DEVICE}1`. Prüfe sie
nur im ausgehängten Zustand. Kontrolliere zuvor das tatsächliche Layout mit
`lsblk`; bei einem anderen Image kann die Partitionsnummer abweichen:

**Auf dem Linux-PC, normaler Benutzer; `sudo` nur wo angegeben:**

```bash
sudo e2fsck -fn "${SD_DEVICE}1"
```

Der Abschnitt prüft Layout und Dateisystem; er führt keinen vollständigen
byteweisen Vergleich mit dem Backup durch.

Danach alle Partitionen aushängen, die Karte sicher entfernen und sie **nur
bei ausgeschalteter T95** einsetzen. Nach dem Start DHCP und SSH nach der
[Installationsanleitung](INSTALLATION.md#3-box-starten-und-netzwerkadresse-finden)
prüfen. UART ist bei Bootproblemen eine zusätzliche Diagnosemöglichkeit.

## Recovery-Grenzen

- Das Backup stellt den Zustand zum Zeitpunkt der Sicherung wieder her; es
  ersetzt keine regelmäßigen, versionierten Datenbackups.
- Eine defekte oder kleinere Ersatzkarte kann das Image nicht aufnehmen.
- Ein SD-Backup enthält möglicherweise noch die alte Armbian-Konfiguration
  und Zugangsdaten. Vor Weitergabe ein neues, gehärtetes und
  lokal personalisiertes Release-Image verwenden.
- Die Android-eMMC der T95 wird durch diese Anleitung weder gelesen noch
  beschrieben.

Weitere Informationen zum geprüften SD-Schreibweg stehen in
[`README.md`](../README.md), zum Release in
[`RELEASE.md`](RELEASE.md) und zur öffentlichen Geheimnisprüfung in
[`PUBLISHING.md`](PUBLISHING.md).
