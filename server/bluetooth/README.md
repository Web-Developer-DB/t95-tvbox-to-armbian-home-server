# Bluetooth und Musikplayer auf der T95

**Deutsch** | [English](README.en.md)

Musik von der Box an Kopfhörer oder Bluetooth-Lautsprecher senden.
**Schon installiert?** Öffne direkt [Bluetooth einfach bedienen](../../docs/BLUETOOTH_CHEATSHEET.md):
dort stehen Geräte anzeigen, verbinden, trennen und vergessen im Vordergrund.

Für die einmalige Einrichtung muss die T95 laufen und du musst mit deinem
normalen Benutzer angemeldet sein. [So öffnest du die Verbindung zur Box](../../docs/BLUETOOTH_CHEATSHEET.md#hier-anfangen-mit-der-box-verbinden).
Zuerst [Grundsystem, Kernel-Sperre und SD-Backup](../../docs/INSTALLATION.md) abschließen.

Bei fehlenden Werkzeugen hilft die [Vorbereitung](../setup/README.md#voraussetzungen).

> [!NOTE]
> **Noch in Erprobung:** Musik und Kopfhörertasten wurden an der
> Referenzbox geprüft. Die automatische Einrichtung braucht noch einen
> vollständigen Test auf einer frisch eingerichteten SD-Karte. Vorher ein
> Backup des funktionierenden Systems anlegen.

Die passende T95 verwendet ihr eingebautes Bluetooth. Ein zusätzlicher
USB-Bluetooth-Adapter ist für diesen Aufbau nicht erforderlich.

## Schnell installieren

**Quellstand:** Die Downloadbefehle verwenden den Prüfbranch
`codex/archive-ssh-dashboard`. Nach einem geprüften Merge müssen Links und
Standardreferenz gemeinsam auf `main` umgestellt werden.

**Einmalig auf der T95:** Die gesamte folgende Zeile kopieren, in das
mit der Box verbundene Terminalfenster einfügen und Enter drücken.

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/codex/archive-ssh-dashboard/tools/install-t95-bluetooth.sh)
```

Bei einer Passwortfrage dein Linux-Passwort auf der T95 eingeben und Enter
drücken. Dabei bleiben Zeichen und Sternchen unsichtbar. Das Werkzeug lädt
die benötigten Dateien und installiert den Player. Nach `Fertig.` ist die
Einrichtung beendet; dann mit der [Bedienung](../../docs/BLUETOOTH_CHEATSHEET.md)
fortfahren. Kopfhörer werden anschließend bewusst ausgewählt und gekoppelt.
Eigene Musik wird im Ordner `Music` deines Benutzers erwartet und bleibt erhalten.

<details>
<summary>Weitere Installationsmöglichkeiten für Fortgeschrittene</summary>

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

</details>

## Kopfhörer verbinden und als Ausgang wählen

<a id="1-bluetooth-umgebung-scannen"></a><a id="2-gewünschtes-audiogerät-auswählen-und-verbinden"></a><a id="3-den-verbundenen-kopfhörer-als-audio-ausgang-verwenden"></a><a id="4-einen-bereits-gekoppelten-kopfhörer-erneut-verbinden"></a><a id="5-verbindung-vorübergehend-trennen"></a><a id="6-kopplung-dauerhaft-von-der-t95-entfernen"></a>

Die [Schritt-für-Schritt-Bedienung](../../docs/BLUETOOTH_CHEATSHEET.md)
erklärt auch ohne Terminal-Vorkenntnisse, wie du dich an der Box anmeldest,
Befehle eingibst und die Antworten liest.

| Deine Aufgabe | Direkter Einstieg |
| --- | --- |
| Gekoppelte Geräte finden | [Gespeicherte Geräte anzeigen](../../docs/BLUETOOTH_CHEATSHEET.md#gekoppelte-geräte-anzeigen) |
| Aktuelle Verbindungen prüfen | [Verbundene Geräte anzeigen](../../docs/BLUETOOTH_CHEATSHEET.md#verbundene-geräte-anzeigen) |
| Bekannten Kopfhörer benutzen | [Verbinden und für Musik auswählen](../../docs/BLUETOOTH_CHEATSHEET.md#wieder-verbinden-und-für-musik-auswählen) |
| Neuen Kopfhörer suchen und koppeln | [Erstmalige Verbindung](../../docs/BLUETOOTH_CHEATSHEET.md#neue-kopfhörer-zum-ersten-mal-verbinden) |
| Nur die Verbindung beenden | [Trennen, Kopplung behalten](../../docs/BLUETOOTH_CHEATSHEET.md#nur-die-verbindung-trennen) |
| Einzelnes Gerät aus der Box entfernen | [Gerät vergessen](../../docs/BLUETOOTH_CHEATSHEET.md#gerät-dauerhaft-vergessen) |

## Kurzzeitig ausschalten: Kopfhörer am PC verwenden

Mit `t95-bluetooth off` auf der T95 pausierst du deren gesamten Bluetooth-Funk.
Die Kopplungen bleiben gespeichert; Home-Server und Samba laufen weiter.
Die [Alltagsanleitung](../../docs/BLUETOOTH_CHEATSHEET.md#kopfhörer-am-pc-oder-handy-verwenden)
zeigt den Wechsel zum PC oder Handy und zurück Schritt für Schritt.

## Player entfernen und Bluetooth deaktivieren

Dieser Abschnitt entfernt die Player-Einrichtung. Wenn du nur einen
Kopfhörer trennen oder vergessen möchtest, verwende die
[Gerätebedienung](../../docs/BLUETOOTH_CHEATSHEET.md#nur-die-verbindung-trennen).

**Im normalen T95-Terminalfenster:**

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

<details>
<summary>Technische Hintergründe und Testnachweise</summary>

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

</details>
