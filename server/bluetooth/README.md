# Bluetooth und Musikplayer auf der T95

**Deutsch** | [English](README.en.md)

**Ort: laufende T95, normaler SSH-Benutzer mit `sudo`.** Zuerst
[Grundsystem, Kernel-Sperre und SD-Backup](../../docs/INSTALLATION.md) abschließen.

Starter-Voraussetzungen: [Bash, curl, tar, Python 3, sudo](../setup/README.md#voraussetzungen).

> [!NOTE]
> **Prüfbranch:** Audio und Kopfhörertasten sind an der manuellen
> Ausgangseinrichtung geprüft. Die neuen Installer sind mit simulierten
> Systemdiensten getestet; vollständige Installation, Rücknahme und Kaltstart
> auf einer frischen T95-SD stehen noch aus.

Diese Einrichtung nutzt das **interne BCM43342-UART-Modul** der T95 mit
AXP313A. Ein USB-Bluetooth-Dongle ist dafür nicht erforderlich. Der Player
sendet Musik an Bluetooth-Kopfhörer; deren Wiedergabetasten steuern MPD über
mpDris2 und BlueZ `mpris-proxy`.

## Schnell installieren

**Quellstand:** Die Downloadbefehle verwenden den Prüfbranch
`codex/archive-ssh-dashboard`. Nach einem geprüften Merge müssen Links und
Standardreferenz gemeinsam auf `main` umgestellt werden.

Auf der **T95**, als normaler SSH-Benutzer, ausführen:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/codex/archive-ssh-dashboard/tools/install-t95-bluetooth.sh)
```

Das Skript fragt über `sudo` nach dem Passwort. Es lädt einen zusammenhängenden
Quellstand von GitHub, installiert die Pakete und richtet die Benutzerdienste
ein. Es startet keine Musik und koppelt kein unbekanntes Gerät automatisch.
Standard-Musikordner ist `~/Music`; vorhandene Musik wird nicht verändert.

Aus einem [Checkout des Prüfbranches](../setup/README.md#lokaler-checkout)
auf der T95, im Repository-Hauptverzeichnis als normaler SSH-Benutzer mit `sudo`:

```bash
sudo python3 server/setup/t95_setup.py bluetooth install --user "$USER"
```

Für die bereits vorhandenen eigenen Testdateien kann beim **ersten** Aufruf
ein anderer Ordner angegeben werden:

```bash
sudo python3 server/setup/t95_setup.py bluetooth install --user "$USER" --music-dir "$HOME/.local/share/t95-music-test"
```

Der Installer erzeugt selbst keine Testtöne. Ein externer Musikordner muss
vorher eingehängt und für den gewählten Benutzer lesbar sein. Als Root ist
`--user NAME` erforderlich. Benutzername, UID und Geräteadressen werden nicht
aus der ursprünglichen Box übernommen.

## Kopfhörer verbinden und als Ausgang wählen

Kopfhörer in den Kopplungsmodus versetzen; die automatische Verbindung zum
Handy oder PC vorübergehend verhindern. Dann:

```bash
t95-bluetooth pair
```

Dieser Befehl öffnet `bluetoothctl` und zeigt die notwendigen Schritte an.
`AA:BB:CC:DD:EE:FF` durch die gefundene Kopfhöreradresse ersetzen:

```text
power on
agent on
default-agent
scan on
devices
pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
scan off
quit
```

Anschließend den tatsächlich vorhandenen Audio-Ausgang auswählen:

```bash
t95-bluetooth audio AA:BB:CC:DD:EE:FF
```

Das setzt den MPD-Ausgang auf genau diesen Kopfhörer und die PipeWire-Lautstärke
auf 20 %. Es stoppt die Wiedergabe. Bis zur ersten Auswahl verwendet MPD einen
Platzhalter, damit keine Musik ungewollt an einen anderen Ausgang geschickt
wird. Nach einem Profilwechsel mit geändertem Ausgangsnamen den `audio`-Befehl
erneut ausführen. Für schon gekoppelte Geräte reicht später `connect`;
`pair` kann eine vorhandene Kopplung erneuern.

## Kurzzeitig ausschalten: Kopfhörer am PC verwenden

```bash
t95-bluetooth off      # Player stoppen, Bluetooth-Funk sperren, BlueZ stoppen
t95-bluetooth on       # Funk freigeben, BlueZ starten, Controller einschalten
t95-bluetooth restart  # Bluetooth aus und wieder an; Musik bleibt gestoppt
t95-bluetooth status   # Funk-, Controller- und Playerstatus
```

`off` betrifft **alle Bluetooth-Controller** der Box, auch einen zusätzlich
eingesteckten USB-Bluetooth-Dongle. Es löscht keine Kopplungen. Damit können die
Kopfhörer ohne Ausschalten des Home-Servers mit dem PC verbunden werden. Für
den Rückwechsel zuerst am PC trennen, dann `on` und bei Bedarf
`sudo bluetoothctl connect ADRESSE` ausführen. Der genaue Funkzustand nach einem
Neustart hängt auch von `systemd-rfkill` und der Systemkonfiguration ab; bei
Bedarf erneut `on` aufrufen.

Diese kurzen Befehle funktionieren nach Installation **ohne Internet**.
Der Server und Samba werden nicht gestoppt. Für reines Trennen eines einzelnen
Geräts steht `sudo bluetoothctl disconnect ADRESSE` zur Verfügung; es kann sich
danach jedoch wieder verbinden.

## Player entfernen und Bluetooth deaktivieren

Ein Befehl für Rücknahme und Entfernung der neu hinzugefügten Zielpakete:

```bash
t95-bluetooth remove --remove-packages
```

Für die Deinstallation gibt es einen eigenen Downloadstarter, ohne Menüauswahl:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/codex/archive-ssh-dashboard/tools/uninstall-t95-bluetooth.sh)
```

Dabei werden MPD, mpDris2 und `mpris-proxy` für den gewählten Benutzer gestoppt
und deaktiviert; Bluetooth-Funk und BlueZ werden abgeschaltet, BlueZ wird
deaktiviert. Vorhandene Konfigurationsdateien werden aus der Sicherung
wiederhergestellt. Ein vom Installer neu angelegter Firmware-Alias wird
entfernt, ein schon vorher vorhandener Alias bleibt bestehen.

Nur die beim Installieren **neu hinzugefügten, ausdrücklich angeforderten**
Pakete werden für APT-Entfernung vorgeschlagen. Würde APT dafür weitere Pakete
entfernen, bricht dieser Paketschritt ab. Vorher installierte Pakete, gemeinsame
Abhängigkeiten, Musikdateien, Playlists, Playerzustände, Kopplungen und die
unveränderte Originalfirmware bleiben erhalten. Es gibt kein `autoremove` und
kein APT-Purge vorhandener Konfigurationsdateien. Ohne `--remove-packages` bleibt
auch die Paketinstallation erhalten.

PipeWire/WirePlumber, die schon vor dem Setup liefen, werden bei der Rücknahme
nicht abgeschaltet. **Linger bleibt erhalten**, weil es auch die Samba-
USB-Einrichtung verwenden kann. Die Hilfsbefehle unter `/usr/local/bin`, der
Quellcache unter `/usr/local/lib/t95-setup` und die privaten Sicherungen unter
`/var/lib/t95-setup/bluetooth` bleiben für Diagnose und erneute Installation
vorhanden. Ein weiterer `remove`-Aufruf ist erlaubt.

Nachträglich geänderte verwaltete Dateien blockieren die Rücknahme. Diese
Dateien zuerst separat sichern und prüfen. Erst danach kann
`t95-bluetooth remove --force --remove-packages` bewusst den gesicherten Zustand
wiederherstellen. `--force` überschreibt diese späteren Änderungen.

## Technischer Umfang und Nachweise

- Zielstand: Armbian 26.8.4 / Debian Trixie, Kernel
  `6.18.48-current-sunxi64`, T95 H616 mit AXP313A und internem BCM43342.
- Die bekannte `BCM43342.hcd` muss bereits aus dem Image vorhanden sein;
  SHA-256: `09970c63b7a0fc677915195923739ddac5e9ee8d589ef9f4b0ded7370684874f`.
  Es wird keine proprietäre Firmware neu verteilt oder von fremden Seiten
  geladen. Board, Firmware und UART-Treiberpfad werden vorher geprüft.
- Boardbezogener Alias:
  `BCM.mbox,t95-axp313.hcd -> BCM43342.hcd`. Bei Neuanlage wird ausschließlich
  das geprüfte Bluetooth-UART-Gerät neu gebunden, kein WLAN-Treiber.
- Audio: PipeWire + WirePlumber 0.5, MPD mit PipeWire-Ausgabe, mpDris2,
  BlueZ `mpris-proxy`. MPD lauscht auf **127.0.0.1:6600**. Die bestehende
  MPD-Systeminstanz wird deaktiviert, damit sie den Benutzerplayer nicht stört.
- Eine auf MPD begrenzte PipeWire-Clientregel setzt `node.dont-fallback` und
  `node.dont-move`. Fehlt der gewählte Kopfhörer, soll MPD dadurch nicht an
  einen anderen Audio-Ausgang wechseln. Der vollständige Hardwaretest dieser
  neuen Regel steht zusammen mit dem Installer-Test noch aus. Die Syntax wurde
  mit `pw-config` der laufenden Box aus einer temporären Datei geprüft.
- Der SSH-Benutzer kann Audio ohne grafische Anmeldung nutzen. WirePlumber
  erhält einen eigenen beschreibbaren Zustandspfad; ein bestehendes
  `~/.local/state` wird nicht pauschal umberechtigt.
- Vor Änderungen werden Dateien und Dienstzustände protokolliert. Bei Fehlern
  werden Dateien und soweit möglich Dienstzustände zurückgenommen. Bereits
  installierte/aktualisierte APT-Pakete und Linger können dabei verbleiben;
  `remove` kann anschließend die protokollierte Einrichtung bereinigen.
- CPU-/RAM-Spannungen, Bootparameter, Netzwerk-, Samba- und SSH-Konfiguration
  werden nicht geändert. Die WLAN-Seite des BCM43342 wird nicht eingerichtet.

Die manuell eingerichtete Ausgangsbox wurde mit MX42H-Kopfhörern geprüft:
A2DP/SBC, klare Testtöne und Pause/Wiedergabe/Nächster/Vorheriger am Kopfhörer
funktionierten. Das ist der Funktionsnachweis für den Aufbau. Die **neuen
Installations-/Deinstallationsskripte** wurden mit temporären Dateisystemen und
simuliertem APT/systemd geprüft; ein vollständiger Lauf auf einer frischen SD
und ein Kaltstarttest stehen noch aus. Die funktionierende Box wurde dafür
nicht deinstalliert.

Bedienung: [Bluetooth-Cheat-Sheet](../../docs/BLUETOOTH_CHEATSHEET.md) ·
[Musikplayer-Cheat-Sheet](../../docs/MUSIKPLAYER_CHEATSHEET.md).

Offizielle Grundlagen:
[WirePlumber: Audio ohne aktive grafische Sitzung](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html),
[MPD: PipeWire-Ausgang und target](https://mpd.readthedocs.io/en/stable/plugins.html#pipewire),
[PipeWire: Clientregeln](https://docs.pipewire.org/page_man_pipewire-client_conf_5.html),
[WirePlumber: Zielbindung und Fallback](https://pipewire.pages.freedesktop.org/wireplumber/policies/linking.html),
[BlueZ: bluetoothctl](https://manpages.debian.org/trixie/bluez/bluetoothctl.1.en.html).
