# Music player cheat sheet: MPD on the T95

[Deutsch](MUSIKPLAYER_CHEATSHEET.md) | **English**

**Run on: T95, the normal SSH user for whom the player was installed.** Run
`mpc`, `wpctl`, and `systemctl --user` **without sudo**. The
[Bluetooth player](../server/bluetooth/README.en.md) listens locally at
`127.0.0.1:6600`.

## Prepare headphones and music

```bash
t95-bluetooth on
sudo bluetoothctl connect AA:BB:CC:DD:EE:FF
```

Replace the address with your headphones. On first setup or output-name change:

```bash
t95-bluetooth audio AA:BB:CC:DD:EE:FF
```

This selects the headphones, sets PipeWire volume to 20%, and stops MPD.
Default music storage is `~/Music`, or the directory selected with
`--music-dir` during installation. Inspect it:

```bash
grep '^music_directory' "$HOME/.config/mpd/mpd.conf"
```

Copy music there as the normal user. Existing music is preserved. Earlier
personal test files may be selected with
`--music-dir "$HOME/.local/share/t95-music-test"`; MPD does not import a prior
manual installation's playlist automatically.

## Scan and play music

```bash
mpc update --wait
mpc ls
mpc clear
mpc add /
mpc volume 30
mpc play
```

`update` scans the collection, `ls` lists recognized files, `clear` empties
the queue without deleting music, and `add /` queues the configured library.
For a single album/track, use the path returned by `mpc ls`, for example
`mpc add "Album/Track.flac"`.

## Daily commands

| Action | Command |
| --- | --- |
| Status / current track | `mpc status` / `mpc current` |
| Show queue | `mpc playlist` |
| Play / resume | `mpc play` |
| Pause / toggle | `mpc pause` / `mpc toggle` |
| Stop | `mpc stop` |
| Next / previous | `mpc next` / `mpc prev` |
| Play queue item 2 | `mpc play 2` |
| Player volume | `mpc volume 30` |
| Louder / softer | `mpc volume +5` / `mpc volume -5` |
| Repeat on / off | `mpc repeat on` / `mpc repeat off` |
| Shuffle on / off | `mpc random on` / `mpc random off` |
| Save playlist | `mpc save MyList` |
| List saved playlists | `mpc lsplaylists` |
| Add saved playlist to queue | `mpc load MyList` |
| Delete saved playlist | `mpc rm MyList` |

`clear`, `del`, and `rm` affect queues/playlists, not music files. `load`
appends; use `clear` first to replace the queue. If `save` reports an existing
name, choose another or deliberately remove the old saved list.

PipeWire also has output volume:

```bash
wpctl status
wpctl get-volume @DEFAULT_AUDIO_SINK@
wpctl set-volume @DEFAULT_AUDIO_SINK@ 20%
wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
```

`@DEFAULT_AUDIO_SINK@` is the current default output. With several outputs,
inspect `wpctl status` first; MPD uses the separately stored headphone output
from `t95-bluetooth audio`.

## Headphone buttons

Play/pause/next/previous were verified with MX42H on the documented manual
setup. MPD continues after SSH closes. Button assignments vary by model;
a dedicated physical stop button was not verified, while `mpc stop` works.
The three user services must run:

```bash
systemctl --user is-active mpd mpdris2 mpris-proxy
```

If they need restarting, run `systemctl --user restart mpd mpdris2 mpris-proxy`.

## No sound or button response

```bash
t95-bluetooth status
bluetoothctl info AA:BB:CC:DD:EE:FF
wpctl status
mpc status
mpc outputs
systemctl --user status mpd mpdris2 mpris-proxy wireplumber --no-pager
journalctl --user -u mpd -u mpdris2 -u mpris-proxy -u wireplumber -b --no-pager -n 80
```

Expect connected headphones listed as an output in `wpctl status`. Rerun
`t95-bluetooth audio ADDRESS` if the output name changed. Populate an empty
queue with `update --wait`, `add /`, and `play`. If `mpc` addresses another
instance, use `mpc -h 127.0.0.1 -p 6600 status` explicitly.

To use headphones on the PC, run `t95-bluetooth off`. Later run `on`, reconnect,
then `mpc play`. For removal, use `t95-bluetooth remove --remove-packages`;
[installation/removal details](../server/bluetooth/README.en.md) describe retained data.

Official references: [MPC](https://manpages.debian.org/trixie/mpc/mpc.1.en.html),
[MPD/PipeWire](https://mpd.readthedocs.io/en/stable/plugins.html#pipewire).
