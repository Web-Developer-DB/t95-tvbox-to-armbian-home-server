# Musikplayer-Cheat-Sheet: MPD auf der T95

Als derselbe normale SSH-Benutzer arbeiten, für den der
[Bluetooth-Musikplayer](../server/bluetooth/README.md) installiert wurde.
`mpc`, `wpctl` und `systemctl --user` hier **ohne sudo** ausführen.
MPD hört lokal auf `127.0.0.1:6600`.

## Start: Kopfhörer und Musik bereitstellen

```bash
t95-bluetooth on
sudo bluetoothctl connect AA:BB:CC:DD:EE:FF
```

Bei erster Einrichtung oder geändertem Audio-Ausgang zusätzlich:

```bash
t95-bluetooth audio AA:BB:CC:DD:EE:FF
```

Dieser Befehl wählt den Kopfhörer, setzt PipeWire auf 20 % und stoppt MPD.
Der Standard-Musikordner ist `~/Music`. Wurde beim Installieren
`--music-dir` verwendet, gilt dieser andere Ordner. Anzeigen:

```bash
grep '^music_directory' "$HOME/.config/mpd/mpd.conf"
```

Dateien als normaler Benutzer in diesen Ordner kopieren. Vorhandene persönliche
Musik wird vom Installer nicht angefasst. Auch die früher angelegten eigenen
Testdateien können über `--music-dir "$HOME/.local/share/t95-music-test"`
verwendet werden. MPD importiert nicht automatisch die alte Playlist einer
vorherigen manuellen Einrichtung.

## Musiksammlung einlesen und abspielen

```bash
mpc update --wait          # Musiksammlung neu einlesen
mpc ls                    # erkannte Ordner/Dateien anzeigen
mpc clear                 # nur die aktuelle Warteschlange leeren, keine Musik löschen
mpc add /                 # gesamte konfigurierte Musiksammlung in die Warteschlange
mpc volume 30             # Playerlautstärke zunächst niedrig halten
mpc play
```

Für einzelne Titel oder Unterordner statt `/` den von `mpc ls` angezeigten
Pfad verwenden, z. B. `mpc add "Album/Titel.flac"`.

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

```bash
systemctl --user is-active mpd mpdris2 mpris-proxy
systemctl --user restart mpd mpdris2 mpris-proxy
```

## Kein Ton oder keine Tastenreaktion?

```bash
t95-bluetooth status
bluetoothctl info AA:BB:CC:DD:EE:FF
wpctl status
mpc status
mpc outputs
systemctl --user status mpd mpdris2 mpris-proxy wireplumber --no-pager
journalctl --user -u mpd -u mpdris2 -u mpris-proxy -u wireplumber -b --no-pager -n 80
```

Kopfhörer müssen verbunden sein und in `wpctl status` als Audio-Ausgang
erscheinen. Bei einem geänderten Ausgangsnamen erneut
`t95-bluetooth audio ADRESSE` ausführen. Eine leere Warteschlange mit
`update --wait`, `add /` und `play` füllen. Falls `mpc` eine andere Instanz
anspricht, gezielt `mpc -h 127.0.0.1 -p 6600 status` verwenden.

Für den Wechsel zum PC: `t95-bluetooth off`. Später `on`, Kopfhörer verbinden
und `mpc play`. Für vollständige Rücknahme:
`t95-bluetooth remove --remove-packages`; Details und Datenerhalt stehen in der
[Installationsanleitung](../server/bluetooth/README.md).

Offizielle Befehlsreferenzen:
[MPC (Debian Trixie)](https://manpages.debian.org/trixie/mpc/mpc.1.en.html) ·
[MPD/PipeWire](https://mpd.readthedocs.io/en/stable/plugins.html#pipewire).
