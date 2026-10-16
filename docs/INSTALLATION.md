# Home-Server installieren

**Deutsch** | [English](INSTALLATION.en.md)

Diese Anleitung führt von der passenden TV-Box bis zum ersten Dateizugriff.
Du brauchst grundlegende Terminal- und SSH-Kenntnisse. Verwende den empfohlenen
Skriptweg; die [manuelle Alternative](#manuelle-alternative-zur-sd-vorbereitung)
ersetzt ausschließlich die SD-Vorbereitung in Schritt 2.

**Ablauf:** Hardware → Linux-PC → SD → SSH → Kernel-Schutz → Backup → Samba.

[Startseite](../README.md) · [Hilfe nach Symptomen](TROUBLESHOOTING.md)

## 1. Hardware und PC vorbereiten

**Ort: ausgeschaltete Box und Linux-PC, noch keine Schreibbefehle.**

- Prüfe den Platinenaufdruck **`H616-T95MAX-AXP313A-V3.0`** anhand der
  [Hardware-Fotos](../README.md#hardware-fotos). Der Gehäusename „T95“ genügt
  nicht. Bei anderer oder unbekannter Platine hier stoppen und den
  [Entwicklerpfad](PORTING.md) verwenden.
- Halte eine entbehrliche microSD, einen **USB-Kartenleser**, ein Netzwerkkabel
  zum Router und die passende, zuverlässige Stromversorgung der Box bereit.
  Der Schreiber unterstützt wechselbare USB-Geräte mit `RM=1` und `/dev/sdX`.
  Interne Kartenleser mit `/dev/mmcblk*` werden nicht unterstützt.
- Die Karte muss größer als das Rohimage sein: **1.535.115.264 Byte**. Die
  Referenzbox verwendete 128 GB; das ist keine Mindestanforderung. Für Daten
  und Pakete wird zusätzlich freier Platz benötigt. Auf dem PC sollten für
  Download, Rohimage, persönliche Kopie und temporäres Dateisystem zusammen
  **mindestens 6 GB** frei sein; auch `/tmp` braucht etwa 1,6 GB freien Platz.
- Die Box wird per **Ethernet und SSH** bedient. WLAN und eine HDMI-Anzeige
  gehören nicht zu den bestätigten Voraussetzungen dieses Serverwegs.

**Linux-PC · normaler Benutzer mit `sudo` · Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install -y bash git curl xz-utils coreutils util-linux e2fsprogs openssl parted udev sudo gawk
df -h "$HOME" /tmp
```

`e2fsprogs` liefert `debugfs` und `e2fsck`, `parted` liefert `partprobe`.
Prüfe, dass die Werkzeuge vorhanden sind:

```bash
for tool in bash git curl xz sha256sum lsblk dd debugfs e2fsck openssl partprobe udevadm sudo awk; do
  command -v "$tool" || { printf "Fehlt: %s\n" "$tool"; break; }
done
```

**Ergebnis:** Alle Werkzeugnamen haben einen Pfad; Home- und Temp-Dateisystem
haben ausreichend Platz. Bei fehlenden Werkzeugen [hier weiter](TROUBLESHOOTING.md#werkzeug-fehlt).

### Windows und WSL2

Der empfohlene Weg verwendet natives Linux. Unter Windows benötigen die
PC-Schritte eine Ubuntu-/Debian-Shell in WSL2 und einen zuverlässig
durchgereichten USB-Kartenleser, der in `lsblk` als `/dev/sdX`, `TRAN=usb`,
`RM=1` und `TYPE=disk` erscheint. Ein Windows-Laufwerksbuchstabe genügt nicht.
Die Bash-Blöcke gehören nicht in PowerShell. Wenn diese Gerätezuordnung nicht
funktioniert, führe die SD-Schritte auf einem nativen Linux-System aus.
Nach dem SD-Schreiben kann der SSH-Client auch unter Windows verwendet werden.
UART/FEL benötigen jeweils gesonderten USB-/Seriellzugriff; siehe
[UART-Anleitung](UART_BRINGUP.md). macOS ist für die PC-Skripte nicht dokumentiert.

## 2. Persönliche SD-Karte erstellen

**Linux-PC · normaler Benutzer, das Werkzeug fragt bei Bedarf nach `sudo`.**

> [!CAUTION]
> Das ausgewählte USB-Medium wird vollständig überschrieben. Ziehe andere
> USB-Datenträger nach Möglichkeit ab. Prüfe Größe, Modell und Seriennummer
> des Kartenlesers, bevor du den angezeigten Gerätenamen bestätigst.

```bash
mkdir -p "$HOME/t95-install"
cd "$HOME/t95-install"
export T95_WORKDIR="$PWD"
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/install-t95-release.sh)
```

Das Startskript kommt von `main`, lädt das Basisimage **`v1.0.1`** und bezieht
seine Image-Werkzeuge ausdrücklich vom **Tag `v1.0.1`**. Zusatzmodule im
Prüfbranch sind davon getrennt; siehe [Quellstände](../README.md#quellstände).

Der Installer lädt und prüft das Image, fragt zweimal verdeckt nach deinem
eigenen **ersten Root-Passwort** und erzeugt die persönliche Kopie. Bei der
SD-Frage bestätigst du mit `J` und anschließend mit dem exakten Gerätenamen.
Ohne Zustimmung wird nur die persönliche Image-Datei vorbereitet.

**Ergebnis:** Nach dem Schreiben erscheint
`ERFOLG: SD-Karte ist vorbereitet.`. Der Schreiber hat die Daten zurückgelesen
und geprüft. Erst dann die Karte sicher entfernen. Bei Abbruch
[die passende Fehlermeldung nachschlagen](TROUBLESHOOTING.md).

Bei einem erneuten Start kannst du eine passende persönliche Kopie
wiederverwenden oder eine neue mit Zeitstempel erzeugen. Ein neuer Ordner ist
nicht erforderlich. Das Passwort der wiederverwendeten Kopie bleibt dasselbe.

> [!IMPORTANT]
> Das öffentliche Image hat **kein Standardpasswort** und ist vor der
> Personalisierung nicht per Passwort loginfähig. Schreibe die `.img.xz`
> nicht unverändert mit einem anderen Flashprogramm auf SD. Persönliche
> `.img`- und `.t95-provisioned-manifest`-Dateien bleiben privat.

## 3. Box starten und Netzwerkadresse finden

**Ort: ausgeschaltete T95 und Routeroberfläche auf dem PC.**

1. Die geprüfte SD in die vollständig ausgeschaltete T95 einsetzen.
2. Ethernet mit dem Router verbinden, dann die Box einschalten.
3. In der Geräteliste des Routers nach der neuen DHCP-Adresse suchen. DHCP
   bedeutet, dass der Router der Box automatisch eine IP-Adresse zuweist.
   PC und Box müssen sich für den folgenden Zugriff im selben erreichbaren LAN befinden.

**Ergebnis:** Der Router zeigt eine Netzwerkadresse für die Box. Eine Anzeige
am Fernseher ist kein Erfolgskriterium. Eine garantierte Erststartdauer wurde
nicht gemessen. Ohne Adresse zuerst [Kabel, Router und SD prüfen](TROUBLESHOOTING.md#keine-ip-adresse),
dann bei Bedarf die UART-Diagnose verwenden.

## 4. Erstes SSH-Login und normalen Benutzer einrichten

**Linux-PC · normaler Benutzer · Verbindung zur T95:**

```bash
read -r -p 'IP-Adresse der T95: ' T95_IP
ssh "root@$T95_IP"
```

Beim ersten Kontakt zeigt SSH einen neuen Hostschlüssel-Fingerprint. Das ist
der Schlüssel der Box, nicht dein Passwort. Prüfe die Gerätezuordnung im
Router; ein unabhängiger Fingerprint-Abgleich ist über eine vertrauenswürdige
lokale UART-Konsole mit `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`
möglich. Bestätige den Schlüssel erst nach der Zuordnung. Bei einer
Schlüsselwarnung nach einem früheren Login [hier weiter](TROUBLESHOOTING.md#ssh-anmeldung-scheitert).

Melde dich mit dem in Schritt 2 gewählten Root-Passwort an. Während einer
Passworteingabe erscheinen keine Zeichen. Schließe Armbians Erststartdialog
einschließlich Passwortänderung und Anlage eines normalen Benutzers ab.
Notiere dessen Namen für deine eigene Verwendung.

**Ergebnis:** Ein normaler Benutzer mit `sudo` existiert. Beende bei Bedarf
die Root-Sitzung mit `exit`. Falls der Dialog die Sitzung bereits beendet hat,
verbinde dich direkt erneut. Die nächsten Befehle laufen wieder auf dem PC:

```bash
read -r -p 'IP-Adresse der T95: ' T95_IP
read -r -p 'Normaler Linux-Benutzer auf der T95: ' T95_LOGIN
ssh "$T95_LOGIN@$T95_IP"
```

**T95 · normaler SSH-Benutzer:**

```bash
whoami
sudo -v
```

`whoami` muss deinen normalen Benutzer zeigen, nicht `root`. `sudo` fragt
nach dessen Linux-Passwort. Bei Problemen [Zugang prüfen](TROUBLESHOOTING.md#ssh-anmeldung-scheitert).

| Zugang | Welches Passwort? |
| --- | --- |
| Erstes `root`-Login | Passwort aus der Image-Personalisierung; danach gilt eine Änderung im Erststartdialog |
| SSH als normaler Benutzer | Linux-Passwort dieses Benutzers |
| `sudo` als normaler Benutzer | dasselbe Linux-Passwort |
| Dateifreigaben über Samba | eigenes Samba-Passwort, später im Samba-Setup gesetzt |

## 5. Kernel und DTB vor Updates schützen

**T95 · normaler SSH-Benutzer mit `sudo` · vor weiterer Paketinstallation.**

> [!CAUTION]
> Führe vor diesem Schritt kein `apt upgrade`, `apt full-upgrade` oder
> `armbian-upgrade` aus. Der Kernel und die DTB-Hardwarebeschreibung müssen
> zur geprüften Platine passen. Ein Ersatz kann Boot oder Ethernet beeinträchtigen.

```bash
sudo apt-mark hold linux-image-current-sunxi64 linux-dtb-current-sunxi64
apt-mark showhold
uname -r
```

**Ergebnis:** Die Liste enthält beide Paketnamen; die Kernelversion ist
`6.18.48-current-sunxi64`. Bei Abweichung [stoppen und prüfen](TROUBLESHOOTING.md#kernelstand-weicht-ab).
Normale Debian-/Armbian-Pakete dürfen danach aktualisiert werden.
Ein bewusstes Kernel-/DTB-Update benötigt ein Backup und erneute
Hardwareprüfung; siehe [Release-Handbuch](RELEASE.md#den-geprüften-kernel-dtb-stand-schützen).

## 6. Grundsystem sichern

**T95 · normaler SSH-Benutzer mit `sudo`:**

```bash
sudo poweroff
```

Nach vollständigem Herunterfahren die Karte entnehmen und auf dem Linux-PC
ein [vollständiges SD-Backup](BACKUP.md) erstellen und prüfen. Dieses Backup
sichert das funktionierende Grundsystem vor der Installation von Diensten.
Es enthält persönliche Zugangsdaten und bleibt privat.

**Ergebnis:** Backup und Prüfsumme liegen auf einem anderen Datenträger.
Die SD wieder in die ausgeschaltete Box einsetzen, Ethernet verbinden,
starten und wie in Schritt 4 als normaler Benutzer per SSH anmelden.

## 7. Dateiserver einrichten

**T95 · normaler SSH-Benutzer mit `sudo`:** Folge jetzt dem
[Samba-Schnellstart](../server/samba-usb/README.md#schnellstart-reproduzierbare-wiederherstellung).
Er ist die maßgebliche Anleitung für Installation und Clienttest; die Befehle
werden hier nicht erneut aufgeführt.

Der empfohlene Aufruf setzt `DATA_PATH=/srv/t95-sd-data/Share` ausdrücklich:
Die feste Freigabe **`T95-DATA` liegt auf der System-SD**. USB-Sticks und
USB-Festplatten erscheinen zusätzlich als eigene Freigaben. Das Skript
partitioniert oder formatiert die interne eMMC nicht.

**Ergebnis:** Das Skript meldet `Fertig.`. Öffne auf deinem PC
`smb://<T95-IP>/T95-DATA` im Dateimanager, melde dich mit deinem normalen
Benutzernamen und dem Samba-Passwort an und schreibe und lies eine Testdatei.
Die Adresse ist ein Dateimanagerpfad, kein Terminalbefehl.
Bei Problemen [Freigaben und Anmeldung prüfen](TROUBLESHOOTING.md#freigabe-fehlt-oder-zugriff-wird-abgelehnt).

## 8. Alltag und optionale Erweiterungen

- [USB sicher auswerfen](../server/samba-usb/README.md#usb-sicher-auswerfen),
  bevor du ein Laufwerk abziehst; danach Wiedereinstecken und Zugriff testen.
- Nach erfolgreicher Einrichtung ein weiteres [SD-Backup](BACKUP.md) anlegen.
  Es erfasst keine Daten auf USB oder eMMC: Diese separat regelmäßig sichern.
- [Dashboard](SSH_DASHBOARD.md) und [Bluetooth-Musikplayer](../server/bluetooth/README.md)
  erst nach dem Grundsystem einrichten. Ihre neuen Installer sind im Prüfbranch
  und noch nicht vollständig auf einer frischen T95-SD abgenommen.
- [eMMC als Datenlaufwerk](TECHNICAL_REFERENCE.md#emmc-als-internes-datenlaufwerk)
  ist eine spätere Erweiterung mit eigener Sicherung, Partitionierung und Einbindung.

Ein vollständiger Durchlauf genau dieser neu geordneten Anleitung auf einer
separaten SD ist noch offen. Die [Abnahme-Checkliste](VALIDATION.md#abnahme-der-installationsanleitung)
benennt die erforderlichen Nachweise.

## Manuelle Alternative zur SD-Vorbereitung

**Linux-PC · normaler Benutzer mit `sudo` für den Schreibschritt.**
Diese Alternative ersetzt **nur Schritt 2**. Verwende sie bei einer neuen
Vorbereitung; nach erfolgreichem Skriptlauf ist sie nicht zusätzlich nötig.
Voraussetzungen und Hardwareprüfung aus Schritt 1 gelten weiterhin.

### A. Release herunterladen und prüfen

```bash
mkdir -p "$HOME/t95-install"
cd "$HOME/t95-install"
git clone --branch v1.0.1 --depth 1 \
  https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git t95-release-tools
curl -fL --retry 3 -O https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/releases/download/v1.0.1/T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz
curl -fL --retry 3 -O https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/releases/download/v1.0.1/SHA256SUMS
grep -F '  T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz' SHA256SUMS | sha256sum -c -
```

**Ergebnis:** Die Image-Prüfung meldet `OK`. Die Prüfsummenliste enthält auch
Entwicklerdateien; dieser Weg prüft gezielt das heruntergeladene Image.
Wenn `t95-release-tools` bereits existiert, nicht überschreiben; verwende den
empfohlenen Installer oder einen neuen Arbeitsordner.

### B. Persönliche Kopie erzeugen

Im selben PC-Terminal:

```bash
cd "$HOME/t95-install"
xz -dk --keep T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz
mkdir -p t95-private
bash t95-release-tools/tools/provision-t95-release-image.sh \
  T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img \
  t95-private/t95-personal.img PROVISION-T95-ROOT-PASSWORD
```

**Ergebnis:** Nach zweimaliger Passwortabfrage erscheint
`ERFOLG: persönliche lokale Image-Kopie erzeugt.`. Der Bestätigungstext
`PROVISION-T95-ROOT-PASSWORD` ist ein festes Token und bleibt unverändert.
Bei bestehenden Dateien neue Namen wählen oder im empfohlenen Installer
wiederverwenden; der manuelle Weg überschreibt kein persönliches Image.

### C. Karte wählen und geprüft schreiben

```bash
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS
read -r -p 'Geprüfte SD-Karte, z. B. /dev/sdb: ' T95_SD
bash "$HOME/t95-install/t95-release-tools/tools/write-t95-provisioned-image-to-sd.sh" \
  "$T95_SD" \
  "$HOME/t95-install/t95-private/t95-personal.img" \
  "$HOME/t95-install/t95-private/t95-personal.img.t95-provisioned-manifest" \
  WRITE-T95-PROVISIONED-TO-SDX
```

**Ergebnis:** `ERFOLG: Personalisierte SD wurde vollständig zurückgelesen und geprüft.`
Der Token `WRITE-T95-PROVISIONED-TO-SDX` bleibt unverändert; nur die abgefragte
Geräteadresse bezeichnet deine Karte. Jetzt mit [Schritt 3](#3-box-starten-und-netzwerkadresse-finden)
fortfahren. Die eMMC wird von diesem PC-Schreibweg nicht angesprochen.
