<a id="bluetooth-und-musikplayer-auf-der-t95"></a>

# 🎧 Bluetooth und Musikplayer auf der T95

**Deutsch** | [English](README.en.md)

Musik von der Box an Kopfhörer oder Bluetooth-Lautsprecher senden.
**Schon installiert?** Öffne direkt [Bluetooth einfach bedienen](../../docs/BLUETOOTH_CHEATSHEET.md):
dort stehen Geräte anzeigen, verbinden, trennen und vergessen im Vordergrund.

| Dein Ziel | Hier geht es weiter |
| --- | --- |
| 🚀 Player einmalig einrichten | [Voraussetzungen](#voraussetzungen) → [Installieren](#schnell-installieren) |
| 🎧 Kopfhörer im Alltag benutzen | [Geräte finden, verbinden und trennen](../../docs/BLUETOOTH_CHEATSHEET.md) |
| 🎵 Erste eigene Musik hören | [Datei übertragen und abspielen](../../docs/MUSIKPLAYER_CHEATSHEET.md) |
| ↩️ Audio-Setup zurücknehmen | [Entfernung und erhaltene Daten](#player-entfernen-und-bluetooth-deaktivieren) |

<a id="voraussetzungen"></a>

## 📋 Voraussetzungen

Für die einmalige Einrichtung muss die T95 laufen und du musst mit deinem
normalen Benutzer angemeldet sein. [So öffnest du die Verbindung zur Box](../../docs/BLUETOOTH_CHEATSHEET.md#hier-anfangen-mit-der-box-verbinden).
Zuerst [Grundsystem und Kernel-Sperre](../../docs/INSTALLATION.md) abschließen.
Ein [vollständiges SD-Backup](../../docs/BACKUP.md) ist optional.

Bei fehlenden Werkzeugen hilft die [Vorbereitung](../setup/README.md#voraussetzungen).

> [!NOTE]
> **Geprüft und getestet:** Der Projektbetreiber hat die dokumentierten
> Bluetooth-Schritte am **17.10.2026** geprüft und als funktionsfähig bestätigt.
> [Testnachweise und offene Einzelprüfungen](../../docs/VALIDATION.md#dashboard-und-bluetooth).

Die passende T95 verwendet ihr eingebautes Bluetooth. Ein zusätzlicher
USB-Bluetooth-Adapter ist für diesen Aufbau nicht erforderlich.

> [!NOTE]
> **Geänderte Rücknahme vom 19.10.2026:** Die folgende Sicherung und Wiederherstellung
> der Dienstzustände ist automatisiert geprüft. Ein eigener T95-Hardwaredurchlauf
> steht [noch aus](../../docs/VALIDATION.md#dashboard-und-bluetooth).

<a id="automatische-konfigurationssicherung"></a>

## 🗂️ Automatische Konfigurationssicherung

Noch vor APT und Änderungen an der Audio-Konfiguration erzeugt das Setup ein
privates Archiv und sichert Inhalt, Modus und Eigentümer seiner verwalteten
Dateien im Journal. Schlägt die Sicherung fehl, startet die Paketinstallation nicht.

| Sicherung | Ort oder Umfang |
| --- | --- |
| Konfigurationsarchiv | `/var/lib/t95-setup/bluetooth/audio-before-setup.tar.gz` |
| Automatische Dateirücknahme | Einzelkopien und SHA-256-Nachweise im selben privaten Verzeichnis |
| Vorhandene Audio-Einstellungen | Vorhandene MPD-, mpDris2-, PipeWire-, WirePlumber-, PulseAudio- und Bluetooth-Konfiguration sowie Audio-Benutzerdienste |
| Dienstzustände | Lauf- und Autostartzustände der System- und Audio-Benutzerdienste |

Das Archiv ist nur für root lesbar und bleibt privat. Es ist eine Referenzkopie,
kein Systemimage und keine Sicherung alter Paketversionen. Die automatische
Rücknahme stellt verwaltete Dateien aus dem Journal wieder her; das Gesamtarchiv
nicht ungeprüft über ein laufendes System entpacken. Eine vorhandene `~/.mpdconf`
wird gesichert, zur Vermeidung konkurrierender MPD-Konfiguration vorübergehend
entfernt und bei Rücknahme wiederhergestellt. Ein erneutes `install` bewahrt die
erste Sicherung; nach einer Rücknahme archiviert eine Neuinstallation das alte Journal.

<a id="schnell-installieren"></a>

## 🚀 Schnell installieren

Die Downloadbefehle und der Installer beziehen ihre Dateien von `main`.

**Einmalig auf der T95:** Die gesamte folgende Zeile kopieren, in das
mit der Box verbundene Terminalfenster einfügen und Enter drücken.

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/install-t95-bluetooth.sh)
```

Bei einer Passwortfrage dein Linux-Passwort auf der T95 eingeben und Enter
drücken. Dabei bleiben Zeichen und Sternchen unsichtbar. Das Werkzeug lädt
die benötigten Dateien und installiert den Player. Nach `Fertig.` ist die
Einrichtung beendet; dann mit der [Bedienung](../../docs/BLUETOOTH_CHEATSHEET.md)
fortfahren. Kopfhörer werden anschließend bewusst ausgewählt und gekoppelt.
Eigene Musik wird im Ordner `Music` deines Benutzers erwartet und bleibt erhalten.

<a id="erfolg-prüfen"></a>

## ✅ Erfolg prüfen

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
t95-bluetooth status
```

**Ergebnis:** `Setup: installed`, `Abweichende Dateien: 0` und aktive Bluetooth-/Player-Dienste.
Kopfhörer müssen noch nicht verbunden sein. Bei Fehlern die
[Modul-Hilfe](../../docs/TROUBLESHOOTING.md#dashboard-oder-bluetooth-funktioniert-nicht) verwenden.
Danach Kopfhörer koppeln/auswählen und [die erste Datei abspielen](../../docs/MUSIKPLAYER_CHEATSHEET.md).

<details>
<summary>Weitere Installationsmöglichkeiten für Fortgeschrittene</summary>

Aus einem [lokalen Checkout](../setup/README.md#lokaler-checkout)
auf der T95, im Repository-Hauptverzeichnis als normaler SSH-Benutzer mit `sudo`:

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
sudo python3 server/setup/t95_setup.py bluetooth install --user "$USER"
```

Für die bereits vorhandenen eigenen Testdateien kann beim **ersten** Aufruf
ein anderer Ordner angegeben werden:

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
sudo python3 server/setup/t95_setup.py bluetooth install --user "$USER" --music-dir "$HOME/.local/share/t95-music-test"
```

Der Installer erzeugt selbst keine Testtöne. Ein externer Musikordner muss
vorher eingehängt und für den gewählten Benutzer lesbar sein. Als Root ist
`--user NAME` erforderlich. Benutzername, UID und Geräteadressen werden nicht
aus der ursprünglichen Box übernommen.

</details>

<a id="kopfhörer-verbinden-und-als-ausgang-wählen"></a>

## 🎧 Kopfhörer verbinden und als Ausgang wählen

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

<a id="kurzzeitig-ausschalten-kopfhörer-am-pc-verwenden"></a>

## ⏸️ Kurzzeitig ausschalten: Kopfhörer am PC verwenden

Mit `t95-bluetooth off` auf der T95 pausierst du deren gesamten Bluetooth-Funk.
Die Kopplungen bleiben gespeichert; Home-Server und Samba laufen weiter.
Die [Alltagsanleitung](../../docs/BLUETOOTH_CHEATSHEET.md#kopfhörer-am-pc-oder-handy-verwenden)
zeigt den Wechsel zum PC oder Handy und zurück Schritt für Schritt.

<a id="player-entfernen-und-bluetooth-deaktivieren"></a>
<a id="-player-entfernen-und-bluetooth-deaktivieren"></a>
<a id="vorherige-audio-einrichtung-wiederherstellen"></a>

## ↩️ Vorherige Audio-Einrichtung wiederherstellen

Dieser Abschnitt entfernt die Player-Einrichtung. Wenn du nur einen
Kopfhörer trennen oder vergessen möchtest, verwende die
[Gerätebedienung](../../docs/BLUETOOTH_CHEATSHEET.md#nur-die-verbindung-trennen).

**Im normalen T95-Terminalfenster:**

Ein Befehl für Rücknahme und Entfernung der neu hinzugefügten Zielpakete:

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
t95-bluetooth remove --remove-packages
```

**Nach erfolgreicher Rücknahme prüfen — auf der T95, normaler SSH-Benutzer:**

```bash
t95-bluetooth status
```

Erwartet wird `Setup: removed`. Vergleiche jeden benannten Dienst mit seinem
gespeicherten Ausgangszustand: `active` allein ist kein Installationsrest, wenn
der Dienst vorher schon aktiv war. Sicherungen und Musik bleiben bewusst erhalten.
Wenn du Bluetooth nur pausieren möchtest, verwende `t95-bluetooth off`.

Als Alternative zu `remove`, wenn der lokale Helfer fehlt: eigener Downloadstarter ohne Menüauswahl.
Nur einen der beiden Wege verwenden:

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/uninstall-t95-bluetooth.sh)
```

<details>
<summary>Was bei der Entfernung erhalten bleibt und wie Konflikte behandelt werden</summary>

Die Rücknahme stellt die gesicherten Dateien sowie die protokollierten
Lauf- und Autostartzustände vor der Installation wieder her. Zuvor aktive
Dienste werden mit ihrer ursprünglichen Konfiguration neu gestartet; zuvor
inaktive Dienste werden beendet. Ein vorher bereits aktiver `mpris-proxy`
oder PipeWire-Dienst darf nach erfolgreicher Rücknahme deshalb wieder laufen.
Die systemweite Aktivierung für alle Benutzer wird nicht verändert.
Ein neu angelegter Firmware-Alias wird entfernt; ein vorher vorhandener bleibt.

Mit `--remove-packages` werden nur **neu hinzugefügte, ausdrücklich angeforderte
Zielpakete** entfernt. Eine APT-Simulation verhindert, dass dabei weitere Pakete
entfernt werden. Vorher installierte Audiopakete und gemeinsame Abhängigkeiten
bleiben erhalten. Paket-Upgrades werden nicht auf ältere Versionen zurückgesetzt;
es gibt kein `autoremove` und kein pauschales Löschen von Paketkonfigurationen.
Ohne `--remove-packages` bleiben Zielpakete installiert. Lässt sich ein geerbter
systemweiter Autostart dadurch nicht zurücknehmen, meldet das Werkzeug einen
Fehler statt einen uneingeschränkten Erfolg.

Verwendet eine vorhandene Samba-/USB-Einrichtung den Sitzungsbus, bleibt außerdem
`dbus-user-session` erhalten, auch wenn das Audio-Setup es ursprünglich installiert
hat. Diese Laufzeitabhängigkeit ist für die APT-Paketprüfung nicht erkennbar.

Musik, Playlists, Kopplungen, Originalfirmware, gemeinsames Linger, Hilfsbefehle,
Quellcache und private Sicherungen bleiben erhalten. Linger kann auch Samba/USB
benötigen. Erst nach bestandener Dienstprüfung wird `Setup: removed` eingetragen.
Bei Fehlern bleibt ein wiederaufnehmbarer Zustand wie `restoring`; die Sicherung
bleibt verfügbar.

**Ältere Installationen:** Der Downloadstarter gleicht auch bereits als `removed`
markierte Protokolle ab. Nach der damaligen Entfernung geänderte Dateien bleiben
dabei erhalten. Einen früher nicht protokollierten Funkzustand kann das alte
Journal nicht rekonstruieren; das Werkzeug weist darauf hin. Neue Installationen
sichern Bluetooth-Softblocks und, soweit abfragbar, den Einschaltzustand des Controllers.

Nachträglich geänderte verwaltete Dateien blockieren die Rücknahme. Diese
Dateien zuerst separat sichern und prüfen. Erst danach kann
`t95-bluetooth remove --force --remove-packages` bewusst den gesicherten Zustand
wiederherstellen. `--force` überschreibt diese späteren Änderungen.

</details>

<details>
<summary>Technische Hintergründe und Testnachweise</summary>

<a id="technischer-umfang-und-nachweise"></a>

## 🛠️ Technischer Umfang und Nachweise

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
  einen anderen Audio-Ausgang wechseln. Der gezielte Hardwaretest bei fehlendem
  Kopfhörer ist separat in der [Testmatrix](../../docs/VALIDATION.md#dashboard-und-bluetooth) offen. Die Syntax wurde
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
funktionierten. Die Setup-Skripte wurden zusätzlich mit temporären
Dateisystemen und simuliertem APT/systemd geprüft. Am **17.10.2026** bestätigte
der Projektbetreiber nach eigener Prüfung, dass die dokumentierten
Bluetooth-Schritte funktionieren. Gesonderte Neuinstallations-, Rücknahme-
und Kaltstartprüfungen werden in der
[Testmatrix](../../docs/VALIDATION.md#dashboard-und-bluetooth) geführt.

Bedienung: [Bluetooth-Cheat-Sheet](../../docs/BLUETOOTH_CHEATSHEET.md) ·
[Musikplayer-Cheat-Sheet](../../docs/MUSIKPLAYER_CHEATSHEET.md).

Offizielle Grundlagen:
[WirePlumber: Audio ohne aktive grafische Sitzung](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html),
[MPD: PipeWire-Ausgang und target](https://mpd.readthedocs.io/en/stable/plugins.html#pipewire),
[PipeWire: Clientregeln](https://docs.pipewire.org/page_man_pipewire-client_conf_5.html),
[WirePlumber: Zielbindung und Fallback](https://pipewire.pages.freedesktop.org/wireplumber/policies/linking.html),
[BlueZ: bluetoothctl](https://manpages.debian.org/trixie/bluez/bluetoothctl.1.en.html).

**Erweiterung vom 19.10.2026:** Konfigurationssicherung und Wiederherstellung
der vorherigen Dienstzustände sind automatisiert geprüft. Ein vollständiger
Hardwaredurchlauf dieser geänderten Rücknahme auf einer separaten T95-SD
ist noch offen.

</details>
