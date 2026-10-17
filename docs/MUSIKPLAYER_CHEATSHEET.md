# Eigene Musik auf der T95 abspielen

<a id="musikplayer-cheat-sheet-mpd-auf-der-t95"></a>

**Deutsch** | [English](MUSIKPLAYER_CHEATSHEET.en.md)

Übertrage eine erste eigene MP3 vom PC und höre sie über Bluetooth-Kopfhörer.
Verwende eine bereits vorhandene Datei. MPD ist der Player auf der Box;
mit `mpc` bedienst du ihn. Der [Bluetooth-Musikplayer muss installiert sein](../server/bluetooth/README.md).
Verwende das normale T95-Konto, für das du den Player eingerichtet hast.
`mpc`, `wpctl` und `systemctl --user` als dieser Benutzer ohne `sudo` ausführen.

[Bedienung](#tägliche-bedienung) · [Fehlerhilfe](#kein-ton-oder-keine-tastenreaktion) · [Alltag](DAILY_USE.md)

## Start: Kopfhörer und Musik bereitstellen

### A. Kopfhörer verbinden und Ordner prüfen

Mit [Bluetooth einfach bedienen](BLUETOOTH_CHEATSHEET.md#wieder-verbinden-und-für-musik-auswählen)
den Kopfhörer verbinden und als Musikausgang auswählen. Neue Kopfhörer zuerst
[koppeln](BLUETOOTH_CHEATSHEET.md#neue-kopfhörer-zum-ersten-mal-verbinden).
Die Ausgangswahl beginnt bei 20 % und hält die Wiedergabe zunächst an.

Bleibe in diesem SSH-Fenster der T95. Den eingerichteten Musikordner anzeigen:

**Auf der T95, normaler Player-Benutzer:**

```bash
grep '^music_directory' "$HOME/.config/mpd/mpd.conf"
```

**Beispielantwort — nur lesen:**

```text
music_directory "/home/alex/Music"
```

Standard ist der Ordner `Music` deines T95-Benutzers. Bei einer Einrichtung
mit `--music-dir` gilt ein anderer Pfad. Verwende den **tatsächlich angezeigten
Pfad**. Danach diese Abfrage starten:

**Auf der T95, normaler Player-Benutzer:**

```bash
read -r -p 'Musikordner aus der Ausgabe, ohne Anführungszeichen: ' T95_MUSIC_DIR
```

Den vollständigen Pfad eingeben und Enter drücken. Dann prüfen:

**Auf der T95, normaler Player-Benutzer:**

```bash
ls -ld -- "$T95_MUSIC_DIR"
```

**Ergebnis:** Der eingerichtete Ordner wird angezeigt. Bei fehlendem Ordner,
falschem Benutzer oder Berechtigungsfehler hier stoppen und die Einrichtung prüfen.

### B. Eigene MP3 vom PC übertragen

Öffne ein **zweites Terminalfenster auf dem Linux-PC**, dort ohne SSH-Anmeldung.
Das erste Fenster bleibt mit der T95 verbunden. SCP kopiert eine Datei über SSH;
auf dem PC liefert das Paket `openssh-client` den Befehl.

Beispielantworten sind `/home/alex/Musik/Mein Lied.mp3`, `192.168.178.50` und
`alex`. Ersetze sie durch deinen eigenen PC-Dateipfad, die Box-Adresse und
deinen T95-Benutzernamen. Pfade bei den folgenden Abfragen ohne Anführungszeichen eingeben.

**Auf dem Linux-PC, normaler Benutzer:**

```bash
read -r -p 'Vollständiger Pfad deiner eigenen MP3 auf diesem PC: ' T95_AUDIO_FILE
```

Den lokalen Dateipfad eingeben und Enter drücken. Dann die Datei prüfen:

**Auf dem Linux-PC, normaler Benutzer:**

```bash
ls -l -- "$T95_AUDIO_FILE"
```

**Ergebnis:** Die gewünschte MP3 wird angezeigt. Jetzt die Box-Adresse abfragen:

**Auf dem Linux-PC, normaler Benutzer:**

```bash
read -r -p 'IP-Adresse der T95 aus dem Router: ' T95_IP
```

Die Adresse eingeben und Enter drücken. Danach den normalen T95-Benutzer abfragen:

**Auf dem Linux-PC, normaler Benutzer:**

```bash
read -r -p 'Normaler Benutzername auf der T95: ' T95_LOGIN
```

Den Namen eingeben und Enter drücken. Anschließend kopieren. Ein Zeitstempel
gibt der Testkopie einen neuen Namen; das Original auf dem PC bleibt erhalten.

**Auf dem Linux-PC, normaler Benutzer:**

```bash
T95_TEST_NAME="t95-test-$(date +%Y%m%d-%H%M%S).mp3"
scp -- "$T95_AUDIO_FILE" "$T95_LOGIN@$T95_IP:$T95_TEST_NAME" &&
  printf 'Übertragener Testdateiname: %s\n' "$T95_TEST_NAME"
```

Bei einer Passwortfrage das Linux-Passwort dieses T95-Benutzers eingeben.
Einen neuen SSH-Schlüssel erst nach der Gerätezuordnung gemäß
[Installation](INSTALLATION.md#4-erstes-ssh-login-und-normalen-benutzer-einrichten) bestätigen.
**Ergebnis:** SCP endet ohne Fehler und der Testdateiname wird ausgegeben.
Die Kopie liegt zunächst im T95-Benutzerordner. So kann der nächste Schritt
auch einen abweichenden Musikpfad mit Leerzeichen direkt auf der Box verwenden.

### C. Testkopie in den Player-Ordner legen

Wechsle zurück in das **erste, mit der T95 verbundene Fenster**, als derselbe
normale Benutzer wie beim Player. Den am PC ausgegebenen Dateinamen abfragen:

**Auf der T95, normaler Player-Benutzer:**

```bash
read -r -p 'Übertragener Testdateiname einschließlich .mp3: ' T95_TEST_NAME
```

Den Dateinamen eingeben und Enter drücken. Danach in den in A geprüften Ordner
kopieren. `--backup=numbered` erhält eine vorhandene Zieldatei als nummerierte Sicherung.

**Auf der T95, normaler Player-Benutzer:**

```bash
ls -l -- "$HOME/$T95_TEST_NAME" &&
  cp --backup=numbered -- "$HOME/$T95_TEST_NAME" "$T95_MUSIC_DIR/$T95_TEST_NAME" &&
  ls -l -- "$T95_MUSIC_DIR/$T95_TEST_NAME"
```

**Ergebnis:** Die Datei steht ohne Kopierfehler im eingerichteten Musikordner.
Bei einem Fehler hier stoppen. Falls das erste Fenster geschlossen wurde,
zuerst A wiederholen, um den Musikordner erneut festzulegen.

## Musiksammlung einlesen und abspielen

Für die oben übertragene Testdatei den folgenden Block ausführen. Im selben
T95-Fenster bleiben, damit `T95_TEST_NAME` noch den übertragenen Namen enthält.
`clear` leert nur die Warteschlange und löscht keine Musikdatei.

**Auf der T95, normaler Player-Benutzer:**

```bash
mpc update --wait
mpc ls
mpc clear
mpc add "$T95_TEST_NAME"
mpc volume 30
mpc play
mpc status
```

**Ergebnis:** Der gewählte Titel spielt auf dem ausgewählten Kopfhörer;
der Status zeigt `[playing]`. Pause und Stoppen mit den Befehlen unten prüfen.
Bei Stille die [Ton-Fehlerhilfe](#kein-ton-oder-keine-tastenreaktion) verwenden.
Für bereits vorhandene Musik den Pfad aus `mpc ls` bei `mpc add` verwenden,
oder `mpc add /` für die ganze Sammlung. Alte Playlists einer vorherigen
manuellen Player-Einrichtung werden nicht automatisch übernommen.

## Tägliche Bedienung

| Aktion | Befehl |
|---|---|
| Status | `mpc status` |
| Aktueller Titel | `mpc current` |
| Warteschlange anzeigen | `mpc playlist` |
| Wiedergabe / fortsetzen | `mpc play` |
| Pause | `mpc pause` |
| Pause/Wiedergabe umschalten | `mpc toggle` |
| Stoppen | `mpc stop` |
| Nächster Titel | `mpc next` |
| Vorheriger Titel | `mpc prev` |
| Titel Nr. 2 aus der Warteschlange | `mpc play 2` |
| Playerlautstärke 30 % | `mpc volume 30` |
| Etwas lauter / leiser | `mpc volume +5` / `mpc volume -5` |
| Wiederholen an / aus | `mpc repeat on` / `mpc repeat off` |
| Zufall an / aus | `mpc random on` / `mpc random off` |
| Warteschlange als Playlist speichern | `mpc save MeineListe` |
| Gespeicherte Playlists anzeigen | `mpc lsplaylists` |
| Playlist zur Warteschlange hinzufügen | `mpc load MeineListe` |
| Gespeicherte Playlist löschen | `mpc rm MeineListe` |

`clear`, `del` und `rm` bearbeiten Warteschlangen/Playlists, keine Musikdateien.
`load` fügt Titel hinzu; vorher `clear`, wenn die bisherige Warteschlange ersetzt
werden soll. Ein bereits vergebener Name kann bei `save` einen Fehler ergeben;
anderen Namen wählen oder die alte gespeicherte Liste bewusst mit `rm` löschen.

PipeWire hat zusätzlich eine Ausgangslautstärke. Nach Auswahl des Kopfhörers:

**Auf der T95, normaler Player-Benutzer:**

```bash
wpctl status
wpctl get-volume @DEFAULT_AUDIO_SINK@
wpctl set-volume @DEFAULT_AUDIO_SINK@ 20%
wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
```

`@DEFAULT_AUDIO_SINK@` ist der aktuelle Standardausgang. Bei mehreren Ausgängen
zuerst `wpctl status` prüfen; MPD verwendet den separat gespeicherten
Kopfhörerausgang aus `t95-bluetooth audio`.

## Tasten am Kopfhörer

Pause/Wiedergabe und Nächster/Vorheriger wurden mit den MX42H am beschriebenen
Softwareaufbau praktisch geprüft. MPD läuft weiter, wenn SSH geschlossen wird.
Die konkrete Tastenbelegung richtet sich nach dem Kopfhörermodell. Ein separater
physischer Stoppknopf wurde nicht nachgewiesen; `mpc stop` funktioniert.

Für die Tasten müssen `mpd`, `mpdris2` und `mpris-proxy` laufen:

**Auf der T95, normaler Player-Benutzer:**

```bash
systemctl --user is-active mpd mpdris2 mpris-proxy
systemctl --user restart mpd mpdris2 mpris-proxy
```

## Kein Ton oder keine Tastenreaktion?

**Auf der T95, normaler Player-Benutzer:**

```bash
t95-bluetooth status
wpctl status
mpc status
mpc outputs
systemctl --user status mpd mpdris2 mpris-proxy wireplumber --no-pager
journalctl --user -u mpd -u mpdris2 -u mpris-proxy -u wireplumber -b --no-pager -n 80
```

Kopfhörer müssen verbunden sein und in `wpctl status` als Audio-Ausgang
erscheinen. Bei einem geänderten Ausgangsnamen erneut
[den Kopfhörer erneut auswählen](BLUETOOTH_CHEATSHEET.md#wieder-verbinden-und-für-musik-auswählen) ausführen. Eine leere Warteschlange mit
`mpc update --wait`, `mpc add /` und `mpc play` füllen. Falls `mpc` eine andere Instanz
anspricht, gezielt `mpc -h 127.0.0.1 -p 6600 status` verwenden.

Für den Wechsel zum PC: `t95-bluetooth off`. Später `on`, Kopfhörer verbinden
und `mpc play`. Für vollständige Rücknahme:
`t95-bluetooth remove --remove-packages`; Details und Datenerhalt stehen in der
[Installationsanleitung](../server/bluetooth/README.md).

Offizielle Befehlsreferenzen:
[MPC (Debian Trixie)](https://manpages.debian.org/trixie/mpc/mpc.1.en.html) ·
[MPD/PipeWire](https://mpd.readthedocs.io/en/stable/plugins.html#pipewire).
