# Boot-Troubleshooting mit UART

Diese Reihenfolge verhindert, dass ein früher Bootfehler fälschlich als
Kernel-, Netzwerk- oder Samba-Problem behandelt wird. Ein sichtbarer
HDMI-Bildschirm ersetzt das UART-Protokoll nicht.

## Fehlerkette

| Letzter sichtbarer Marker | Einordnung | Prüfen | Nicht tun |
| --- | --- | --- | --- |
| Kein Text, auch nicht in FEL | Verkabelung, Pegel oder Strom | 3,3 V TTL, GND, RX/TX gekreuzt, 115200 8N1, Stromversorgung | 5-V-TTL oder RS-232 anschließen |
| FEL wird nicht erkannt | OTG-/Boot-ROM-Pfad | ausgeschaltetes Gerät, OTG-Port, UBOOT-Taste nur nach Boardbeleg | eMMC löschen |
| `eGON.BT0` startet, kein `DRAM:` | SPL, PMIC oder DRAM | PMIC, DRAM-Typ/-Takt und Boardparameter | DTB oder Rootfs ändern |
| `DRAM:` sichtbar, kein U-Boot-Banner | SPL/U-Boot-Übergang | BL31-/U-Boot-Paar, Build-Header, UART | Linux neu installieren |
| U-Boot-Banner, kein `Starting kernel` | SD-Pfad, DTB oder Bootskript | Bootpartition, `armbianEnv.txt`, Root-UUID | eMMC als Bootziel wählen |
| Kernel startet, Rootfs fehlt | Rootgerät oder Dateisystem | `root=`, PARTUUID/UUID, ext4-Integrität | DHCP oder Samba untersuchen |
| Login sichtbar, kein Netzwerk | PHY/DTB/Userspace | `end0`, Link, DHCP-Journal | Bootloader austauschen |

## Protokoll aufnehmen

Der RP2040-Adapter und das Capture-Skript gehören zum separaten Projekt
[`rp2040-zero-uart-adapter`](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter).
Nach dessen Einrichtung:

```bash
python3 tools/capture_uart.py /dev/ttyACM0 \
  --baud 115200 --duration 180 --prefix captures/boot
```

Das Gerät erst nach dem Start der Aufzeichnung einschalten. Den Log als Text
speichern; vor einer Veröffentlichung IP-Adressen, MAC-Adressen, UUIDs,
Seriennummern, lokale Pfade und Zugangsdaten entfernen.

## Referenz

Die bereinigten Soll-Marker stehen unter
[`docs/reference-logs/`](reference-logs/README.md). Sie dienen nur der
Einordnung der Bootstufe; sie ersetzen keine Messung auf der eigenen Platine.

## Abbruch und Rückweg

Bei einem unbekannten Fehler nicht mehrere Änderungen kombinieren. Die
bekannte funktionierende SD-Karte einsetzen, Original-Firmware-Backup
aufbewahren, die eMMC unverändert lassen und mit dem letzten eindeutigen
UART-Marker zur passenden Portierungsstufe zurückkehren.
