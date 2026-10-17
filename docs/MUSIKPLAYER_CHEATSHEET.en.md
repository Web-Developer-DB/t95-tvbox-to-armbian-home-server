# Play your own music on the T95

<a id="music-player-cheat-sheet-mpd-on-the-t95"></a>

[Deutsch](MUSIKPLAYER_CHEATSHEET.md) | **English**

Transfer a first MP3 from your PC and listen through Bluetooth headphones.
Use a file you already have. MPD is the box's player; `mpc` controls it.
The [Bluetooth player must be installed](../server/bluetooth/README.en.md).
Use the normal T95 account for which you installed the player.
Run `mpc`, `wpctl`, and `systemctl --user` as this user, without `sudo`.

[Daily commands](#daily-commands) · [Troubleshooting](#no-sound-or-button-response) · [Everyday use](DAILY_USE.en.md)

## Prepare headphones and music

### A. Connect the headphones and check the folder

Use [Bluetooth made simple](BLUETOOTH_CHEATSHEET.en.md#reconnect-and-choose-music-output)
to reconnect and select the headphones. For new headphones, complete
[first pairing](BLUETOOTH_CHEATSHEET.en.md#connect-new-headphones-for-the-first-time).
Output selection starts at 20% and stops playback initially.

Stay in that T95 SSH window. Check the configured music folder:

**On the T95, normal player user:**

```bash
grep '^music_directory' "$HOME/.config/mpd/mpd.conf"
```

**Example response — read only:**

```text
music_directory "/home/alex/Music"
```

The default is your T95 user's `Music` folder. A setup using `--music-dir`
has a different path; use the **actual displayed path**. Ask for it now:

**On the T95, normal player user:**

```bash
read -r -p 'Music folder from the output, without quotes: ' T95_MUSIC_DIR
```

Enter that full path and press Enter. Then check it:

**On the T95, normal player user:**

```bash
ls -ld -- "$T95_MUSIC_DIR"
```

**Success:** your configured directory is listed. For a missing directory,
wrong user, or permissions error, stop here and check the installation.

### B. Send your MP3 from the PC

Open a **second terminal on the Linux PC**, without entering SSH there.
Keep the first window connected to the T95. SCP copies a file over SSH;
the PC's `openssh-client` package supplies it.

Example answers are `/home/alex/Music/My song.mp3`, `192.168.178.50`, and
`alex`. Replace them with your own PC file path, box address, and T95 username.
Enter paths without surrounding quotes in the prompts below.

**On the Linux PC, normal user:**

```bash
read -r -p 'Full path of your own MP3 on this PC: ' T95_AUDIO_FILE
```

Enter the local file path and press Enter. Then check the chosen file:

**On the Linux PC, normal user:**

```bash
ls -l -- "$T95_AUDIO_FILE"
```

**Success:** your intended MP3 is listed. Next ask for the box address:

**On the Linux PC, normal user:**

```bash
read -r -p 'T95 IP address from the router: ' T95_IP
```

Enter the address and press Enter. Next ask for your normal T95 username:

**On the Linux PC, normal user:**

```bash
read -r -p 'Normal T95 username: ' T95_LOGIN
```

Enter it and press Enter. Now copy the file. A timestamp gives the test copy
a new name; the original on the PC is preserved.

**On the Linux PC, normal user:**

```bash
T95_TEST_NAME="t95-test-$(date +%Y%m%d-%H%M%S).mp3"
scp -- "$T95_AUDIO_FILE" "$T95_LOGIN@$T95_IP:$T95_TEST_NAME" &&
  printf 'Uploaded test filename: %s\n' "$T95_TEST_NAME"
```

Use that T95 user's Linux password if asked. Accept a new SSH key only after
identifying the box as in [installation](INSTALLATION.en.md#4-first-ssh-login-and-normal-user).
**Success:** SCP completes without errors and the test filename is printed.
The copy first goes to your T95 home folder, so a custom music path with spaces
can be handled in the box window in the next step.

### C. Put the copy in the player's folder

Return to the **first window connected to the T95**, using the same normal
user as the player. Ask for the filename printed on the PC:

**On the T95, normal player user:**

```bash
read -r -p 'Uploaded test filename, including .mp3: ' T95_TEST_NAME
```

Enter that filename and press Enter. Then copy it into the folder checked in A.
`--backup=numbered` preserves an existing target as a numbered backup.

**On the T95, normal player user:**

```bash
ls -l -- "$HOME/$T95_TEST_NAME" &&
  cp --backup=numbered -- "$HOME/$T95_TEST_NAME" "$T95_MUSIC_DIR/$T95_TEST_NAME" &&
  ls -l -- "$T95_MUSIC_DIR/$T95_TEST_NAME"
```

**Success:** the file is listed in your configured music directory, without
copy errors. For an error, stop here. If you closed the first window, repeat
A to set the folder again before copying.

## Scan and play music

For the test file transferred above, run the next block. Use the same T95
window so `T95_TEST_NAME` still names your uploaded file. `clear` clears the
queue only; it does not delete music.

**On the T95, normal player user:**

```bash
mpc update --wait
mpc ls
mpc clear
mpc add "$T95_TEST_NAME"
mpc volume 30
mpc play
mpc status
```

**Success:** the selected track plays through the chosen headphones; status
shows `[playing]`. Check pause and stop with the controls below. For silence,
use [sound help](#no-sound-or-button-response). For music already in the library,
use the path from `mpc ls` with `mpc add`, or `mpc add /` for the whole library.
Old playlists from a previous manual player setup are not imported automatically.

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

**On the T95, normal player user:**

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

**On the T95, normal player user:**

```bash
systemctl --user is-active mpd mpdris2 mpris-proxy
```

If they need restarting, run `systemctl --user restart mpd mpdris2 mpris-proxy`.

## No sound or button response

**On the T95, normal player user:**

```bash
t95-bluetooth status
wpctl status
mpc status
mpc outputs
systemctl --user status mpd mpdris2 mpris-proxy wireplumber --no-pager
journalctl --user -u mpd -u mpdris2 -u mpris-proxy -u wireplumber -b --no-pager -n 80
```

Expect connected headphones listed as an output in `wpctl status`. Rerun
[choose the headphone output again](BLUETOOTH_CHEATSHEET.en.md#reconnect-and-choose-music-output) if the output name changed. Populate an empty
queue with `mpc update --wait`, `mpc add /`, and `mpc play`. If `mpc` addresses another
instance, use `mpc -h 127.0.0.1 -p 6600 status` explicitly.

To use headphones on the PC, run `t95-bluetooth off`. Later run `on`, reconnect,
then `mpc play`. For removal, use `t95-bluetooth remove --remove-packages`;
[installation/removal details](../server/bluetooth/README.en.md) describe retained data.

Official references: [MPC](https://manpages.debian.org/trixie/mpc/mpc.1.en.html),
[MPD/PipeWire](https://mpd.readthedocs.io/en/stable/plugins.html#pipewire).
