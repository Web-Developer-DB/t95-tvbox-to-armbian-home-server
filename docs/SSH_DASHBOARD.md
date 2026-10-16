# SSH-Anmeldedashboard archivieren und wiederherstellen

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

## Ein-Befehl-Wiederherstellung

### GitHub-Starter mit Installation und Deinstallation

Die Downloadbefehle verwenden den Prüfbranch `codex/archive-ssh-dashboard`.
Auf der T95 direkt installieren:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/codex/archive-ssh-dashboard/tools/install-t95-dashboard.sh)
```

Eigene Schnell-Deinstallation, ohne Auswahlmenü:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/codex/archive-ssh-dashboard/tools/uninstall-t95-dashboard.sh)
```

Rücknahme und Status funktionieren danach lokal ohne erneuten Download:

```bash
t95-dashboard status
t95-dashboard remove
```

`remove` stellt die vor dieser
Installation vorhandenen Dashboard-Dateien wieder her; es löscht nicht pauschal
das Armbian-Dashboard. War vorher bereits exakt derselbe Stand vorhanden, sieht
die Rücknahme deshalb gleich aus. Fremde zusätzliche MOTD-Module bleiben erhalten.

Der Starter installiert die benötigten Anzeige-/Systemwerkzeuge über APT und
führt das erste Installationsbackup unter `/var/lib/t95-setup/dashboard`.
Wiederholtes Installieren ersetzt dieses Backup nicht. Nachträgliche manuelle
Änderungen blockieren `remove`, bis sie separat gesichert/geprüft wurden;
`remove --force` überschreibt sie bewusst mit dem Backup. Pakete bleiben
standardmäßig erhalten; optional `remove --remove-packages` für ausschließlich
neu hinzugefügte Zielpakete, mit vorgeschalteter APT-Prüfung.

Aus einem lokalen Checkout auf der Box:

```bash
sudo python3 server/setup/t95_setup.py dashboard install
sudo python3 server/setup/t95_setup.py dashboard remove
```

Weitere Details: [gemeinsamer Setup-Einstieg](../server/setup/README.md).
Die neuen Setup-Skripte wurden in Fixtures geprüft, noch nicht mit echten
APT-/systemd-Aktionen auf der Produktivbox.

### Bestehendes Restore-Werkzeug mit Vorschau

Im ausgecheckten Repository zunächst ohne Änderungen prüfen:

```bash
python3 tools/restore-ssh-dashboard.py
```

Auf der Armbian-Box mit einem Befehl installieren:

```bash
sudo python3 tools/restore-ssh-dashboard.py --apply
```

Das Werkzeug prüft zunächst alle Prüfsummen und Ziele. Vor Änderungen sichert es alle verwalteten vorhandenen Dateien samt Zustand unter `/var/backups/t95-dashboard/<Zeitpunkt-Zufall>/`. Danach werden nur die 14 Manifestdateien atomar installiert. Eine bereits identische Installation bleibt unverändert und erzeugt kein zusätzliches Backup. Bei einem Installationsfehler wird der vorherige Stand automatisch wiederhergestellt.

Rücknahme mit dem vom Werkzeug ausgegebenen Backup-Pfad:

```bash
sudo python3 tools/restore-ssh-dashboard.py --rollback /var/backups/t95-dashboard/BACKUP-NAME
```

Dabei werden vorher vorhandene Dateien einschließlich Modus und Eigentümer wiederhergestellt; durch die Installation neu angelegte Dateien werden entfernt. Andere Dateien bleiben erhalten. Ein SSH-Neustart ist nicht erforderlich. Die nächste SSH-Anmeldung erzeugt das Dashboard über die vorhandene PAM-MOTD-Einbindung.

## Voraussetzungen und Grenzen

Das Ziel benötigt eine bestehende Armbian-Installation mit `/etc/armbian-release`, Bash, Python 3.9 oder neuer und der üblichen SSH/PAM-MOTD-Einbindung. Im Ausgangssystem enthält `/etc/pam.d/sshd` bereits `pam_motd.so motd=/run/motd.dynamic` und `pam_motd.so noupdate`; diese Authentifizierungsdatei wird vom Werkzeug nicht verändert. Bei abweichenden Distributionen muss die Einbindung vorher separat geprüft werden.

Die Module verwenden unter anderem Coreutils, awk, sed, grep, procps, iproute2 und util-linux. `figlet` zeichnet das Logo; ohne figlet ist ein Text-Fallback vorhanden. `curl` wird für die Ermittlung öffentlicher IP-Adressen verwendet. jq ist für Tipps optional, mit sed-Fallback. Container-/WLAN-Informationen erscheinen abhängig von den auf dem Ziel vorhandenen Diensten.

Die archivierte Konfiguration deaktiviert `clear`, verbirgt typische virtuelle Netzwerkadapter, setzt `STORAGE=/dev/sda1` und lässt den CPU-Temperaturoffset bei 0. Die eigene SD-Statistik liest `/sys/block/mmcblk0/stat`. Auf anderer Hardware müssen diese beiden Gerätebezüge geprüft werden. Die Laufwerksübersicht ermittelt vorhandene Dateisysteme zur Laufzeit; es werden keine UUIDs, Mounts oder Datenträgerinhalte wiederhergestellt.

Andere, bereits zusätzlich installierte MOTD-Module werden nicht entfernt. Die nicht ausgeführte Sicherungskopie `95-sd-card-stats+`, Betriebssystem-/Boardidentitäten und Laufzeit-Caches werden nicht installiert. Der vollständige private Ausgangsmitschnitt bleibt getrennt vom GitHub-Quellsatz. Die im Mitschnitt sichtbaren Prozent-/Escape-Formatierungsauffälligkeiten sind als Ausgangsbefund erhalten. Eine zusätzliche Zeile `28GB` war nur im vollständigen Anmeldemitschnitt sichtbar; ihre Quelle ist in den gesicherten MOTD-Modulen nicht identifiziert. Sie ist kein fest hinterlegter Bestandteil des Restore-Werkzeugs.

## Durchgeführte Prüfung

Auf einem temporären Test-Dateisystem geprüft: unverändernde Vorschau, Installation aller 14 Dateien bytegleich zu den erfassten Originalen und mit korrekten Modi, erneutes Anwenden ohne Änderung, vollständige Rücknahme, Ablehnung umgeleiteter Ziele, Ablehnung veränderter Nutzdaten und automatische Rücknahme bei unterbrochener Installation. Bash-Syntax und Manifest-Prüfsummen werden zusätzlich geprüft.

Die laufende Box wurde zur Archivierung nur gelesen. Das Restore-Werkzeug wurde nicht als Root auf ihr ausgeführt; ihre Dashboard-Dateien wurden nicht geändert. Ein vollständiger Neuinstallations-/Kaltstarttest ist noch offen. CPU-/RAM-Spannungen, Bootparameter, Bluetooth, Samba und die SSH-Authentifizierung werden durch die Dashboard-Wiederherstellung nicht konfiguriert.
