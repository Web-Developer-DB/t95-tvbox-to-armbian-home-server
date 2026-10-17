<a id="everyday-use-of-your-t95"></a>

# 🧭 Everyday use of your T95

[Deutsch](DAILY_USE.md) | **English**

Box configured and kernel/DTB holds enabled? Use this page for daily tasks.
For a new box, complete [installation](INSTALLATION.en.md) first.

[Home](../README.en.md) · [Troubleshooting](TROUBLESHOOTING.en.md)

<a id="connect-to-the-box"></a>

## 🔑 Connect to the box

1. Open **Terminal** from your computer's application menu, or **PowerShell** on Windows.
2. Replace example user `alex` with your normal T95 user and `192.168.178.50`
   with the box's current router address.

**On the PC, normal user; adapt this example first:**

```bash
ssh alex@192.168.178.50
```

Enter that T95 user's Linux password when asked, then press Enter. No letters
or stars appear. Check a new SSH key using the
[login guide](INSTALLATION.en.md#4-first-ssh-login-and-normal-user).

**Success:** input such as `alex@t95:~$`. You are now controlling the T95,
even though the window is on the PC. Box commands below belong in that window.
For connection problems, use [SSH help](TROUBLESHOOTING.en.md#ssh-login-fails).

<a id="choose-your-task"></a>

## 🧭 Choose your task

| You want to … | Go here |
| --- | --- |
| 📂 Open or save files on the box | [PC, phone, and VLC access](../server/samba-usb/README.en.md#client-and-vlc-access) |
| ⏏️ Unplug a USB drive | [Safely eject that specific drive](../server/samba-usb/README.en.md#safely-eject-usb-storage) |
| 🎧 Find, connect, or disconnect headphones | [Bluetooth made simple](BLUETOOTH_CHEATSHEET.en.md) |
| 🎵 Transfer and play your music | [Play a first music file](MUSIKPLAYER_CHEATSHEET.en.md#prepare-headphones-and-music) |
| 🗂️ Save the configured system | [Complete SD backup](BACKUP.en.md) |
| 📊 See system information at login | [Set up the dashboard](SSH_DASHBOARD.en.md) |

The recommended fixed `T95-DATA` share uses the system SD. USB drives have
separate shares. An SD backup excludes separate USB/eMMC data; back up that
storage separately and regularly.

> [!TIP]
> **Just closing the window?** The box stays on. Choose deliberately between logging out, rebooting, and shutting down below.

| Your intention | Effect |
| --- | --- |
| 🚪 [Log out of SSH](#log-out-of-ssh-only) | Only your connection ends; the server keeps running. |
| 🔄 [Reboot](#reboot-the-box) | The box restarts; log in over SSH again afterward. |
| ⏻ [Shut down](#shut-down-cleanly) | The system stops; only then remove SD or power. |

<a id="log-out-of-ssh-only"></a>

## 🚪 Log out of SSH only

**On the T95, normal SSH user:**

```bash
exit
```

**Success:** you are back on the PC. The box, shares, and music already playing
keep running. Closing the terminal window also does not turn the box off.

<a id="reboot-the-box"></a>

## 🔄 Reboot the box

Save open client files and finish any transfers first.

**On the T95, normal SSH user with `sudo`:**

```bash
sudo reboot
```

**Success:** SSH disconnects and the box reboots. Reconnect when it is reachable
in the router again. Adjust the SSH address if DHCP assigned another one.
For problems, use [boot/network help](TROUBLESHOOTING.en.md#no-ip-address).

<a id="shut-down-cleanly"></a>

## ⏻ Shut down cleanly

Save open files and finish transfers.

**On the T95, normal SSH user with `sudo`:**

```bash
sudo poweroff
```

**Success:** SSH disconnects and shutdown begins. Wait for shutdown to finish
completely before removing SD or power. A disconnected SSH session alone does
not prove that disk writes have finished. To start again, power the box on
with its correct supply.

<a id="before-adding-applications"></a>

## 🔒 Before adding applications

[Keep kernel/DTB holds enabled](INSTALLATION.en.md#5-protect-the-kernel-and-dtb-before-updates).
With those holds enabled, you can select optional modules or
[other Armbian applications](../README.en.md#install-other-applications).
A [full SD backup](BACKUP.en.md) is optional and preserves the current setup
for recovery.
