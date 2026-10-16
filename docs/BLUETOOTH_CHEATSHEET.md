# Bluetooth-Cheat-Sheet: finden, koppeln, trennen

Für die T95 über SSH. Die kurzen `t95-bluetooth`-Befehle setzen die
[Bluetooth-Installation](../server/bluetooth/README.md) voraus.
`AA:BB:CC:DD:EE:FF` ist ein Platzhalter für die Adresse deines Geräts.

## 1. Adapter und USB-Geräte finden

```bash
lsusb                         # eingesteckte USB-Geräte, IDs Hersteller:Produkt
lsusb -t                      # USB-Baum, Treiber und ausgehandelte USB-Geschwindigkeit
bluetoothctl list             # alle von BlueZ erkannten Bluetooth-Controller
bluetoothctl show             # Zustand des gewählten Standardcontrollers
rfkill list bluetooth         # Software-/Hardware-Funksperren
```

`lsusb` findet **USB-Hardware**, keine drahtlosen Kopfhörer. Ein Bluetooth-USB-
Dongle sollte dort erscheinen. Das interne BCM43342 der T95 ist über **UART**
angebunden und erscheint daher nicht in `lsusb`; dafür `bluetoothctl list`
verwenden. Auch ein WLAN-USB-Stick hat nicht automatisch Bluetooth.

Optionaler Blick auf die vom Kernel angelegten Bluetooth-Geräte:

```bash
for device in /sys/class/bluetooth/hci*; do
    [ -e "$device" ] || continue
    printf '%s: ' "${device##*/}"
    readlink -f "$device/device"
done
```

Bei mehreren Controllern in einer interaktiven `sudo bluetoothctl`-Sitzung mit
`list` auflisten und `select CONTROLLER-ADRESSE` auswählen. Controller-Adresse
und Kopfhörer-Adresse sind zwei verschiedene Adressen.

## 2. Neue Kopfhörer koppeln

Kopfhörer in den **Kopplungsmodus** versetzen, nicht nur einschalten. Eine
Verbindung zum Handy/PC vorher trennen. Dann den Helfer öffnen:

```bash
t95-bluetooth pair
```

In der nun geöffneten `bluetoothctl`-Eingabe nacheinander eingeben. Beim Scan
etwa 15–30 Sekunden warten und Name/Adresse aus der Ausgabe übernehmen:

```text
power on
agent on
default-agent
scan on
devices
pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
info AA:BB:CC:DD:EE:FF
scan off
quit
```

Gegebenenfalls die angezeigte Kopplungsabfrage bestätigen. `info` sollte
`Paired: yes`, `Trusted: yes` und `Connected: yes` zeigen. `trust` erlaubt
spätere Verbindungen zu diesem bekannten Gerät. Die BlueZ-Sitzung bis zum
Ende offen lassen, damit Suchlauf und Kopplungsagent verfügbar bleiben.

Zurück im normalen SSH-Terminal den Audio-Ausgang festlegen:

```bash
t95-bluetooth audio AA:BB:CC:DD:EE:FF
```

Ohne Setup-Helfer kann die Sitzung auch mit `sudo bluetoothctl` geöffnet
werden. Für die Wiedergabe müssen die Audiopakete und der Player trotzdem
eingerichtet sein.

## 3. Bereits gekoppelte Geräte bedienen

| Zweck | Befehl im normalen SSH-Terminal |
|---|---|
| Bekannte Geräte anzeigen | `bluetoothctl devices` |
| Kopplungs-/Verbindungsstatus | `bluetoothctl info AA:BB:CC:DD:EE:FF` |
| Wieder verbinden | `sudo bluetoothctl connect AA:BB:CC:DD:EE:FF` |
| Nur Verbindung trennen | `sudo bluetoothctl disconnect AA:BB:CC:DD:EE:FF` |
| Vertrauen aufheben, Kopplung behalten | `sudo bluetoothctl untrust AA:BB:CC:DD:EE:FF` |
| Entkoppeln / Gerät auf der Box vergessen | `sudo bluetoothctl remove AA:BB:CC:DD:EE:FF` |

`disconnect` bewahrt die Kopplung; das Gerät kann sich wieder verbinden.
`remove` entfernt die lokale Kopplung. Bei erneuter Kopplung gegebenenfalls
auch am Kopfhörer die alte Verbindung löschen. Für ein schon gekoppeltes
Gerät `connect` verwenden; `pair` kann eine bestehende Kopplung erneuern.

## 4. Kopfhörer am PC statt am Server nutzen

```bash
t95-bluetooth off
```

Jetzt am PC verbinden. Der Home-Server und Samba laufen weiter. Zum Rückwechsel
am PC trennen, dann:

```bash
t95-bluetooth on
sudo bluetoothctl connect AA:BB:CC:DD:EE:FF
```

Weitere schnelle Befehle:

```bash
t95-bluetooth restart         # Bluetooth kurz aus/an; Wiedergabe bleibt gestoppt
t95-bluetooth status
```

`off` sperrt den Bluetooth-Funk für **alle** Controller der Box. Kopplungen
werden nicht gelöscht. Nach einem Neustart kann der Funkzustand abhängig von
der Systemkonfiguration abweichen; bei Bedarf `on` ausführen.

## 5. Wenn kein Gerät gefunden wird

1. Kopplungsmodus, Abstand und bestehende Handy-/PC-Verbindung prüfen.
2. `t95-bluetooth status` und `rfkill list bluetooth` ansehen; eine Hardware-
   Sperre lässt sich nicht durch den Softwarebefehl aufheben.
3. `t95-bluetooth restart`, dann erneut mit offenem `bluetoothctl` suchen.
4. Meldungen lesen:

```bash
sudo journalctl -u bluetooth -b --no-pager -n 60
sudo dmesg | grep -Ei 'Bluetooth|hci0|btbcm|firmware' | tail -n 60
```

Bei `firmware Patch file not found` oder `No default controller available`
die [Voraussetzungen](../server/bluetooth/README.md) prüfen. Keine beliebige
Firmware laden und keine WLAN-/Bluetooth-Treiber auf Verdacht entladen.

Befehlsreferenz:
[BlueZ bluetoothctl (Debian Trixie)](https://manpages.debian.org/trixie/bluez/bluetoothctl.1.en.html).
