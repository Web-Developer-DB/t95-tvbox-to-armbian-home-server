# Vollständiges Armbian-SD-Backup

Diese Anleitung erstellt ein sektorgetreues Backup der **gesamten** Armbian-
SD-Karte und stellt es auf derselben oder einer mindestens gleich großen
Ersatzkarte wieder her. Bootloader, Partitionstabelle, DTB, Kernel, Rootfs,
Benutzerkonten und Konfigurationen werden gemeinsam erfasst.

> [!CAUTION]
> Ein vollständiges Abbild kann persönliche Konten, SSH-Konfigurationen,
> Samba-Datenbanken, Logs und weitere Geheimnisse enthalten. Es ist ein
> privates Recovery-Backup und darf nicht in GitHub, in ein öffentliches
> Release oder in einen Cloud-Ordner ohne Verschlüsselung hochgeladen werden.

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

Auf der T95:

```bash
sudo poweroff
```

Warten, bis die Box vollständig aus ist. Erst danach die SD-Karte entnehmen
und am Linux-PC anschließen.

## 2. Quellgerät eindeutig identifizieren

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

```bash
export SD_DEVICE=/dev/sdX   # /dev/sdX durch den lsblk-Namen der eigenen SD ersetzen
```

## 3. Partitionen aushängen

Wenn der Desktop die Karte automatisch eingehängt hat, müssen alle
SD-Partitionen vor dem Rohbackup ausgehängt werden. Die Partitionsnummern
zuerst mit `lsblk` prüfen:

```bash
sudo umount "${SD_DEVICE}1"
sudo umount "${SD_DEVICE}2"
```

Eine Meldung wie „nicht eingehängt“ ist unkritisch. Weitere vorhandene
Partitionen ebenfalls aushängen; das Gerät selbst wird nicht gemountet.

## 4. Komprimiertes Vollbackup erstellen

Einmalig auf Ubuntu/Debian installieren:

```bash
sudo apt update
sudo apt install -y zstd
```

Backupziel und Dateinamen festlegen. Das Ziel muss auf einem **anderen**
Datenträger liegen:

```bash
export BACKUP_DIR=/absolute/path/to/T95-Backups
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
IMAGE="$BACKUP_DIR/t95-armbian-full-$STAMP.img.zst"
```

Danach die gesamte Karte einmal lesen und komprimieren:

```bash
set -o pipefail
sudo dd if="$SD_DEVICE" bs=16M iflag=fullblock status=progress \
  | zstd -T0 -6 --checksum -o "$IMAGE"
```

`if=` zeigt absichtlich auf das vollständige Gerät und nicht auf eine
Partition. Der Vorgang liest die SD-Karte, schreibt aber nicht auf sie oder
auf die interne eMMC. Je nach Kartenleser kann er längere Zeit dauern.

## 5. Backup prüfen und dokumentieren

Zuerst den zstd-Datenstrom testen:

```bash
zstd -t "$IMAGE"
```

Danach eine SHA-256-Prüfsumme erzeugen und direkt kontrollieren:

```bash
sha256sum "$IMAGE" | tee "$IMAGE.sha256"
sha256sum -c "$IMAGE.sha256"
```

Die Ausgabe muss mit `OK` enden. Image, Prüfsumme und die notierte
Quellkartengröße gemeinsam auf einem zweiten, geschützten Datenträger sichern.

## Wiederherstellung auf dieselbe oder eine Ersatzkarte

Die Wiederherstellung überschreibt die Zielkarte vollständig. Sie ist nur
notwendig, wenn eine Karte ersetzt oder der dokumentierte Systemstand exakt
wiederhergestellt werden soll.

### 1. Zielkarte prüfen

Ersatzkarte einstecken und den Gerätenamen neu ermitteln:

```bash
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,FSTYPE,MOUNTPOINTS
export SD_DEVICE=/dev/sdX   # /dev/sdX durch den lsblk-Namen der eigenen SD ersetzen
```

Vor dem Schreiben müssen `TYPE=disk`, `TRAN=usb`, `RM=1` und eine mindestens
so große Byte-Größe wie beim Backup bestätigt sein. Alle automatisch
eingehängten Partitionen aushängen:

```bash
sudo umount "${SD_DEVICE}1"
sudo umount "${SD_DEVICE}2"
```

### 2. Archiv prüfen

```bash
export IMAGE=/absolute/path/to/t95-armbian-full-YYYYMMDD-HHMMSS.img.zst
sha256sum -c "$IMAGE.sha256"
zstd -t "$IMAGE"
```

Nur wenn beide Prüfungen erfolgreich sind, fortfahren.

### 3. Vollständiges Image schreiben

```bash
set -o pipefail
zstd -dc "$IMAGE" \
  | sudo dd of="$SD_DEVICE" bs=16M conv=fsync status=progress
sync
sudo udevadm settle
```

Dieser Schritt schreibt die komplette Zielkarte einschließlich Bootbereich und
Partitionstabelle. Die interne eMMC wird nicht angesprochen.

### 4. Rücklesen und Einsatz

Partitionstabelle neu einlesen und die Karte prüfen:

```bash
sudo partprobe "$SD_DEVICE"
sudo udevadm settle
lsblk -b -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINTS "$SD_DEVICE"
```

Bei einem Armbian-Layout kann das Root-Dateisystem zusätzlich rein lesend
geprüft werden (Partitionsnummer mit `lsblk` bestätigen):

```bash
sudo e2fsck -fn "${SD_DEVICE}2"
```

Danach alle Partitionen aushängen, die Karte sicher entfernen und sie **nur
bei ausgeschalteter T95** einsetzen. Nach dem Start die bekannte UART-
Aufzeichnung und die DHCP-/SSH-Prüfung durchführen.

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
