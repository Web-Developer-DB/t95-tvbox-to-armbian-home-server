# SSH-Dashboard einrichten

<a id="ssh-anmeldedashboard-archivieren-und-wiederherstellen"></a>

**Deutsch** | [English](SSH_DASHBOARD.en.md)

Das per Skript installierte, benutzerdefinierte Dashboard ergänzt die
Armbian-Anmeldeanzeige um zusätzliche Speicherinformationen. Bei jeder
SSH-Anmeldung siehst du neben Auslastung und Arbeitsspeicher:

- **`SD-Writes`:** die seit dem letzten Systemstart auf die SD-Karte geschriebene
  Datenmenge. Nach einem Neustart beginnt dieser Zähler von vorn.
- **Laufwerksübersicht:** die eingebundenen Dateisysteme, einschließlich der
  angeschlossenen und gemounteten USB-Sticks, SSDs und externen Festplatten.
  Pro Eintrag erscheinen Gerätename (etwa `sda1`), Gesamtgröße, freier Platz,
  prozentuale Belegung und Einhängepfad (Mountpfad). Ab 90 % Belegung wird der
  Prozentwert rot hervorgehoben.

Die Übersicht wird bei einer neuen SSH-Anmeldung aktualisiert. Du brauchst
keine zusätzliche Weboberfläche zu öffnen.

[Einrichten](#einrichten) · [Prüfen](#erfolg-prüfen) · [Entfernen](#entfernen) · [Alltag](DAILY_USE.md)

## Voraussetzungen

Die T95 läuft und du bist als normaler Benutzer per SSH angemeldet.
[Grundsystem, Kernel-Sperre und SD-Backup](INSTALLATION.md) müssen abgeschlossen
sein. Die nötigen [Startwerkzeuge](../server/setup/README.md#voraussetzungen)
sind vorhanden; Anzeige-Pakete installiert der Starter.

**Geprüft:** Der Projektbetreiber hat die dokumentierten Dashboard-Schritte
am **17.10.2026** als funktionsfähig bestätigt. [Testnachweise](VALIDATION.md#dashboard-und-bluetooth).

<a id="ein-befehl-wiederherstellung"></a>
<a id="github-starter-mit-installation-und-deinstallation"></a>

## Einrichten

**Auf der T95, normaler SSH-Benutzer mit `sudo`:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/install-t95-dashboard.sh)
```

Bei einer Passwortfrage das Linux-Passwort dieses T95-Benutzers eingeben.
Es erscheinen keine Zeichen oder Sternchen. **Ergebnis:** Der Starter beendet
die Einrichtung mit `Fertig.`. Bei einem Fehler zuerst die
[Modul-Fehlerhilfe](TROUBLESHOOTING.md#dashboard-oder-bluetooth-funktioniert-nicht) öffnen.

## Erfolg prüfen

**Auf der T95, normaler SSH-Benutzer:**

```bash
t95-dashboard status
```

**Ergebnis:** `Setup: installed` und `Abweichende Dateien: 0`. Bei einem
anderen Stand die [Modul-Hilfe](TROUBLESHOOTING.md#dashboard-oder-bluetooth-funktioniert-nicht) verwenden.

Öffne danach auf deinem PC ein **zweites Terminalfenster** und melde dich neu
an. Im Beispiel `alex` und `192.168.178.50` durch deinen normalen T95-Benutzer
und die Box-Adresse aus dem Router ersetzen.

**Auf dem PC, normaler Benutzer; Beispiel vorher anpassen:**

```bash
ssh alex@192.168.178.50
```

**Ergebnis:** Bei der neuen SSH-Anmeldung erscheint die Systemübersicht.
[Eine bereinigte Beispielansicht](images/t95-ssh-status-redacted.png) zeigt den
Aufbau; Zahlen und angezeigte Laufwerke unterscheiden sich je nach Box.

## Benutzen

Das Dashboard erscheint automatisch bei späteren SSH-Anmeldungen. Ein laufendes
Fenster wird dadurch nicht ständig aktualisiert. Für normales Arbeiten kannst
du nach der Anzeige deine weiteren Befehle eingeben.

## Entfernen

Nur ausführen, wenn du die Einrichtung zurücknehmen möchtest.

**Auf der T95, normaler SSH-Benutzer:**

```bash
t95-dashboard remove
```

**Ergebnis:** Die vor der Einrichtung gesicherten Dashboard-Dateien werden
wiederhergestellt. Zusätzliche fremde Module bleiben erhalten. Waren die alten
Dateien bereits identisch, kann die Anzeige danach gleich aussehen.
Bei späteren manuellen Änderungen zuerst die betroffenen Dateien sichern und
prüfen; `--force` überschreibt diese Änderungen mit dem Backup. Pakete bleiben
standardmäßig installiert.

<details>
<summary>Alternative Entfernung über Download</summary>

Dieser Aufruf ist eine Alternative zum lokalen `remove`, kein zusätzlicher Schritt.

**Auf der T95, normaler SSH-Benutzer mit `sudo`:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/uninstall-t95-dashboard.sh)
```

</details>

<details>
<summary>Archiv, technische Details und manuelle Wiederherstellung</summary>

Der Stand vom **16.10.2026** ist unter `server/ssh-dashboard/2026-10-16/` gesichert: 14 tatsächliche Quelldateien der laufenden T95, SHA-256-Prüfsummen und Unix-Dateimodi. Ausgangsbasis: Armbian-BSP 26.8.4, Debian Trixie, Kernel 6.18.48-current-sunxi64. Die vorhandenen Lizenzhinweise der Armbian-Dateien bleiben erhalten; siehe `NOTICE.md` im Archiv.

Ein um IP-Adressen und persönliche Mountpfade bereinigter Mitschnitt steht in [reference-logs/ssh-dashboard-2026-10-16.txt](reference-logs/ssh-dashboard-2026-10-16.txt). Er zeigt das tatsächlich erfasste Dashboard. Zahlen, Temperaturen, belegter Speicher, Container, Tipps und Upgrade-Zähler sind Momentaufnahmen und werden bei späteren Anmeldungen neu ermittelt. Unbereinigte Mitschnitte, Zugangsdaten und private SSH-Schlüssel gehören nicht in dieses Archiv.

| Datei/Gruppe | Aufgabe |
|---|---|
| `/etc/update-motd.d/10-armbian-header` | Armbian-Grafik, Board-/Kernel-/Paketstatus |
| `15-ap-info`, `20-ip-info`, `25-containers-info` | AP-, IP- und Containerinformationen |
| `30-armbian-sysinfo` | Last, RAM, Temperatur, Laufzeit, Speichernutzung |
| `35-armbian-tips`, `quotes.txt`, `41-commands` | Tipps und Kommandos |
| `95-sd-card-stats` | Eigene Erweiterung: SD-Schreibmenge und Laufwerksübersicht |
| `00-clear`, `98-armbian-autoreboot-warn`, `99-blank` | Weitere vorhandene MOTD-Bausteine |
| `/etc/default/armbian-motd` | Aktuelle Darstellungseinstellungen |
| `/usr/lib/armbian/armbian-allwinner-battery` | Vom Systeminfo-Baustein gelesene Hilfsfunktionen |

`manifest.json` ist die maschinenlesbare Grundlage für eine eigene Ein-Klick-Oberfläche: relatives Ziel, Modus und SHA-256 je Datei. `SHA256SUMS` prüft dieselben Dateien mit Standardwerkzeugen. Das bereits vorhandene Wiederherstellungswerkzeug verwendet dieses Manifest.

Der Starter installiert die benötigten Anzeige-/Systemwerkzeuge über APT und
führt das erste Installationsbackup unter `/var/lib/t95-setup/dashboard`.
Wiederholtes Installieren ersetzt dieses Backup nicht. Nachträgliche manuelle
Änderungen blockieren `remove`, bis sie separat gesichert/geprüft wurden;
`remove --force` überschreibt sie bewusst mit dem Backup. Pakete bleiben
standardmäßig erhalten; optional `remove --remove-packages` für ausschließlich
neu hinzugefügte Zielpakete, mit vorgeschalteter APT-Prüfung.

Aus einem [lokalen Checkout](../server/setup/README.md#lokaler-checkout)
auf der Box, im Repository-Hauptverzeichnis als normaler SSH-Benutzer mit `sudo`:

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
sudo python3 server/setup/t95_setup.py dashboard install
```

Nur zur späteren Rücknahme, statt des lokalen Helfers:

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
sudo python3 server/setup/t95_setup.py dashboard remove
```

Weitere Details: [gemeinsamer Setup-Einstieg](../server/setup/README.md).
Die Setup-Skripte wurden automatisiert geprüft; die dokumentierten
Dashboard-Schritte wurden zusätzlich vom Projektbetreiber bestätigt.

### Bestehendes Restore-Werkzeug mit Vorschau

Diese manuelle Alternative ist nach der Starter-Installation nicht zusätzlich
nötig. Im lokalen Checkout, im Repository-Hauptverzeichnis als normaler
Benutzer, zunächst ohne Änderungen prüfen (auch auf dem Linux-PC möglich):

**Auf dem Linux-PC, normaler Benutzer:**

```bash
python3 tools/restore-ssh-dashboard.py
```

Auf der Armbian-Box mit einem Befehl installieren:

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
sudo python3 tools/restore-ssh-dashboard.py --apply
```

Das Werkzeug prüft zunächst alle Prüfsummen und Ziele. Vor Änderungen sichert es alle verwalteten vorhandenen Dateien samt Zustand unter `/var/backups/t95-dashboard/<Zeitpunkt-Zufall>/`. Danach werden nur die 14 Manifestdateien atomar installiert. Eine bereits identische Installation bleibt unverändert und erzeugt kein zusätzliches Backup. Bei einem Installationsfehler wird der vorherige Stand automatisch wiederhergestellt.

Rücknahme mit dem vom Werkzeug ausgegebenen Backup-Pfad:

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
read -r -p 'Vollständiger ausgegebener Backup-Pfad: ' T95_DASHBOARD_BACKUP
```

Den tatsächlichen Backup-Pfad eingeben und Enter drücken. Danach auf der T95:

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
sudo python3 tools/restore-ssh-dashboard.py --rollback "$T95_DASHBOARD_BACKUP"
```

Dabei werden vorher vorhandene Dateien einschließlich Modus und Eigentümer wiederhergestellt; durch die Installation neu angelegte Dateien werden entfernt. Andere Dateien bleiben erhalten. Ein SSH-Neustart ist nicht erforderlich. Die nächste SSH-Anmeldung erzeugt das Dashboard über die vorhandene PAM-MOTD-Einbindung.

## Voraussetzungen und Grenzen

Das Ziel benötigt eine bestehende Armbian-Installation mit `/etc/armbian-release`, Bash, Python 3.9 oder neuer und der üblichen SSH/PAM-MOTD-Einbindung. Im Ausgangssystem enthält `/etc/pam.d/sshd` bereits `pam_motd.so motd=/run/motd.dynamic` und `pam_motd.so noupdate`; diese Authentifizierungsdatei wird vom Werkzeug nicht verändert. Bei abweichenden Distributionen muss die Einbindung vorher separat geprüft werden.

Die Module verwenden unter anderem Coreutils, awk, sed, grep, procps, iproute2 und util-linux. `figlet` zeichnet das Logo; ohne figlet ist ein Text-Fallback vorhanden. `curl` wird für die Ermittlung öffentlicher IP-Adressen verwendet. jq ist für Tipps optional, mit sed-Fallback. Container-/WLAN-Informationen erscheinen abhängig von den auf dem Ziel vorhandenen Diensten.

Die archivierte Konfiguration deaktiviert `clear`, verbirgt typische virtuelle Netzwerkadapter, setzt `STORAGE=/dev/sda1` und lässt den CPU-Temperaturoffset bei 0. Die eigene SD-Statistik liest `/sys/block/mmcblk0/stat`. Auf anderer Hardware müssen diese beiden Gerätebezüge geprüft werden. Die Laufwerksübersicht ermittelt vorhandene Dateisysteme zur Laufzeit; es werden keine UUIDs, Mounts oder Datenträgerinhalte wiederhergestellt.

Andere, bereits zusätzlich installierte MOTD-Module werden nicht entfernt. Die nicht ausgeführte Sicherungskopie `95-sd-card-stats+`, Betriebssystem-/Boardidentitäten und Laufzeit-Caches werden nicht installiert. Der vollständige private Ausgangsmitschnitt bleibt getrennt vom GitHub-Quellsatz. Die im Mitschnitt sichtbaren Prozent-/Escape-Formatierungsauffälligkeiten sind als Ausgangsbefund erhalten. Eine zusätzliche Zeile `28GB` war nur im vollständigen Anmeldemitschnitt sichtbar; ihre Quelle ist in den gesicherten MOTD-Modulen nicht identifiziert. Sie ist kein fest hinterlegter Bestandteil des Restore-Werkzeugs.

## Durchgeführte Prüfung

Auf einem temporären Test-Dateisystem geprüft: unverändernde Vorschau, Installation aller 14 Dateien bytegleich zu den erfassten Originalen und mit korrekten Modi, erneutes Anwenden ohne Änderung, vollständige Rücknahme, Ablehnung umgeleiteter Ziele, Ablehnung veränderter Nutzdaten und automatische Rücknahme bei unterbrochener Installation. Bash-Syntax und Manifest-Prüfsummen werden zusätzlich geprüft.

Bei der ursprünglichen Archivierung wurde die laufende Box nur gelesen;
das manuelle Restore-Werkzeug wurde dabei nicht als Root auf ihr ausgeführt.
Am **17.10.2026** bestätigte der Projektbetreiber nach eigener Prüfung, dass
die dokumentierten Dashboard-Schritte funktionieren. Gesonderte
Neuinstallations-, Rücknahme- und Kaltstartprüfungen stehen in der
[Testmatrix](VALIDATION.md#dashboard-und-bluetooth).
CPU-/RAM-Spannungen, Bootparameter, Bluetooth, Samba und die
SSH-Authentifizierung werden durch die Dashboard-Wiederherstellung nicht konfiguriert.

</details>
