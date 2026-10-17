# Gemeinsamer T95-Setup-Einstieg

**Deutsch** | [English](README.en.md)

**Ort: T95, normaler SSH-Benutzer mit `sudo`.** Erst
[Grundinstallation, Kernel-Sperre und Backup](../../docs/INSTALLATION.md)
abschließen. Dieses Menü installiert Zusatzmodule auf einer laufenden Box;
es erstellt keine Armbian-SD und richtet Samba nicht ein.

> [!NOTE]
> **Geprüft und getestet:** Der Projektbetreiber hat die dokumentierten
> Dashboard- und Bluetooth-Schritte am **17.10.2026** geprüft und als
> funktionsfähig bestätigt. [Testnachweise und offene Einzelprüfungen](../../docs/VALIDATION.md#dashboard-und-bluetooth).

## Voraussetzungen

Bash, curl, tar, Python 3 und sudo müssen bereits vorhanden sein. Falls nötig,
nach der Kernel-Sperre **auf der T95 als normaler Benutzer mit `sudo`** installieren:

```bash
sudo apt update
sudo apt install -y bash curl tar python3 sudo
```

Die eigentlichen Dashboard-/Audiopakete installiert das Setup anschließend.
Eine Git-Installation ist für den Downloadstarter nicht nötig.

## Schnellstart auf der laufenden T95

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/t95-setup.sh)
```

Wähle die gewünschte Aktion im Menü; `0` installiert Dashboard und
Bluetooth/Player nacheinander. Prüfe danach `t95-dashboard status` bzw.
`t95-bluetooth status`. Musik und Kopplung benötigen zusätzliche Schritte in
der [Bluetooth-Anleitung](../bluetooth/README.md).

## Funktionsweise und einzelne Starter

`tools/t95-setup.sh` lädt einen Quellstand von GitHub und ruft
`server/setup/t95_setup.py` mit Rootrechten auf. Ohne Argumente bietet der
Starter ein kleines Terminalmenü. Die Downloadmethode benötigt bereits Bash,
curl, tar, Python 3 und sudo auf der Armbian-Box. Die Nutzpakete installiert das
Setup selbst über APT. Eine Git-Installation ist nicht nötig.


Neben dem gemeinsamen Menü gibt es vier Starter mit fester Aktion.
Die Downloadbefehle stehen in der [Dashboard-Anleitung](../../docs/SSH_DASHBOARD.md)
und der [Bluetooth-Anleitung](../bluetooth/README.md):

| Eigener Starter | Feste Aktion |
|---|---|
| `tools/install-t95-dashboard.sh` | Dashboard installieren |
| `tools/uninstall-t95-dashboard.sh` | Vorherigen Dashboard-Stand wiederherstellen |
| `tools/install-t95-bluetooth.sh` | Bluetooth und Musikplayer installieren |
| `tools/uninstall-t95-bluetooth.sh` | Player entfernen, Bluetooth deaktivieren, neu hinzugefügte Zielpakete geprüft entfernen |

Die Einzelstarter benötigen keine Aktionsargumente und öffnen kein Menü. Aus
einem lokalen Checkout verwenden sie den benachbarten gemeinsamen Starter;
beim curl-Aufruf laden sie ihn aus derselben Git-Referenz. Zusätzliche Optionen
wie `--user NAME` oder bei Deinstallation `--force` werden weitergereicht.

Das gemeinsame Menü bietet zusätzlich **0: beide Komponenten installieren**.
Der direkte Aufruf dafür lautet `bash tools/t95-setup.sh all install`.
Dashboard und Bluetooth werden nacheinander aus demselben Quellarchiv
eingerichtet; jede Komponente führt ein eigenes Journal. Bei einem Fehler bleibt
die zuvor erfolgreich installierte Komponente erhalten und kann separat
zurückgenommen werden. Ein Bluetooth-Musikpfad mit `--music-dir` wird über den
separaten Bluetooth-Starter gewählt.

| Komponente | Aktionen |
|---|---|
| `dashboard` | `install`, `remove`, `status` |
| `bluetooth` | `install`, `remove`, `status`, `pair`, `audio ADRESSE`, `off`, `on`, `restart` |

Der Standard-Quellbranch ist `main`. Optional
kann `T95_SETUP_REF` eine andere existierende Branch-/Tag-/Commitreferenz im
selben Repository auswählen. Es wird genau **ein** GitHub-Quellarchiv geladen;
Dateien verschiedener Downloads werden nicht kombiniert. HTTPS schützt den
Transport; dies ist keine unabhängige Release-Signatur.

Anleitungen:
[Dashboard](../../docs/SSH_DASHBOARD.md) ·
[Bluetooth-Installation](../bluetooth/README.md) ·
[Bluetooth-Cheat-Sheet](../../docs/BLUETOOTH_CHEATSHEET.md) ·
[Musikplayer-Cheat-Sheet](../../docs/MUSIKPLAYER_CHEATSHEET.md).

## Lokaler Checkout

**T95 · normaler SSH-Benutzer mit `sudo` für Pakete, Git als dieser Benutzer.**
Der Release-Werkzeugeordner auf dem PC enthält die aktuellen Module nicht.
Verwende auf der T95 einen separaten Checkout von `main`:

```bash
sudo apt update
sudo apt install -y git
git clone --branch main --depth 1 \
  https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git "$HOME/t95-server-tools"
cd "$HOME/t95-server-tools"
git branch --show-current
```

**Ergebnis:** `main`; `server/setup/t95_setup.py` ist
vorhanden. Wenn der Zielordner bereits existiert, Branch und lokale Änderungen
prüfen, statt ihn zu überschreiben. Lokale Aufrufe in den Modulanleitungen
laufen aus diesem Repository-Hauptverzeichnis.

## Zustand und Rücknahme

Informationen zu Sicherungen und Rücknahme gelten für beide Quellzugänge.

Jede Komponente führt ein privates Journal unter
`/var/lib/t95-setup/<Komponente>/state.json`. Vor Überschreiben werden bestehende
Dateien einschließlich Inhalt, Modus und Eigentümer gesichert. Das erste
Installationsbackup bleibt bei wiederholtem `install` erhalten. Vor der
Rücknahme wird auf spätere Dateiänderungen geprüft. `remove --force` darf diese
Änderungen bewusst überschreiben; vorher separat sichern. Alte Journale werden
bei Neuinstallation archiviert.

Der gemeinsame Quellcache unter `/usr/local/lib/t95-setup` und die beiden kurzen
Befehle unter `/usr/local/bin` bleiben auch nach Rücknahme erhalten. So sind
Status und erneute Einrichtung lokal verfügbar. Die Sicherungen enthalten
möglicherweise private Benutzerpfade und bleiben auf dem Zielsystem.

Standardmäßig bleiben Pakete erhalten. `remove --remove-packages` entfernt nur
zuvor fehlende und vom Setup ausdrücklich angeforderte Pakete, nachdem eine
APT-Simulation bestätigt, dass keine weiteren Pakete entfernt würden. Neue
transitive Abhängigkeiten bleiben erhalten. APT-Upgrades bestehender Pakete
werden nicht zurückgedreht. Es gibt kein automatisches `autoremove`.

Bei Bluetooth ist `remove` absichtlich eine Stilllegung: Playerdienste und
Bluetooth werden deaktiviert, auch wenn eine vorherige manuelle Einrichtung
existierte; alte Dateien werden trotzdem gesichert/wiederhergestellt.
Gemeinsam genutztes Linger und zuvor laufende PipeWire-/WirePlumber-Dienste
bleiben erhalten. Musik und Bluetooth-Kopplungen werden nicht gelöscht.

## Prüfen vor Veröffentlichung

Auf dem Linux-PC aus dem Repository ausführen:

```bash
for script in tools/t95-setup.sh tools/{install,uninstall}-t95-{dashboard,bluetooth}.sh; do bash -n "$script"; done
python3 -m unittest discover -s server/setup/tests -v
python3 tools/restore-ssh-dashboard.py
git diff --check
```

Die Tests verwenden ausschließlich temporäre Verzeichnisse und einen simulierten
APT-/systemd-/BlueZ-Unterbau. Es werden keine Pakete oder Dienste des PCs
geändert. Eigentümerwechsel werden in den Fixtures simuliert, damit die Tests
ohne Root laufen. Der originale Firmwareblob wird nicht in die Tests kopiert.

Geprüft werden Dashboard-Installation und Idempotenz, vollständige Rücknahme,
Prüfsummenfehler, umgeleitete Ziele, spätere manuelle Änderungen, Bluetooth-
Konfiguration/Audio-Auswahl, Erhalt von Daten und schon vorhandenem Firmware-
Alias, Rücknahme bei Dienstfehlern, begrenzte Paketentfernung, falsche Hardware
sowie aus/an ohne Neustart und ohne Löschen der Kopplungen.

Die sechzehn automatisierten Tests bestehen, einschließlich lokaler und
heruntergeladener Einzelstarter, gemeinsamem Menü und Abbruch bei Fehlern.
Zusätzlich wurde die neue MPD-
Streamregel mit dem auf der Ausgangsbox installierten `pw-config` eingelesen:
Die Syntax und beide Routing-Eigenschaften wurden korrekt erkannt. Dafür
wurde nur eine temporäre Datei verwendet und anschließend gelöscht; keine
aktive Konfiguration oder kein Dienst wurde geändert. Die Routingwirkung bei
fehlendem Kopfhörer ist damit noch nicht praktisch nachgewiesen.

Die dokumentierten Dashboard- und Bluetooth-Schritte wurden am **17.10.2026**
zusätzlich vom Projektbetreiber geprüft und als funktionsfähig bestätigt.
Gesonderte Neuinstallations-, Rücknahme- und Kaltstartprüfungen sind in der
[Testmatrix](../../docs/VALIDATION.md#dashboard-und-bluetooth) aufgeführt.
