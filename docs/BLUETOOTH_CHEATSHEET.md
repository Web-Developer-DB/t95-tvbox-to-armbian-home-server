<a id="bluetooth-einfach-bedienen"></a>

# 🎧 Bluetooth einfach bedienen

**Deutsch** | [English](BLUETOOTH_CHEATSHEET.en.md)

Hier findest du die Handgriffe für Kopfhörer und Bluetooth-Lautsprecher an
deiner T95. Du musst dafür keine Linux-Befehle auswendig kennen.
Die Box muss bereits eingerichtet und der
[Bluetooth-Musikplayer installiert](../server/bluetooth/README.md) sein.

<a id="hier-anfangen-mit-der-box-verbinden"></a>

## 🔑 Hier anfangen: mit der Box verbinden

1. Suche auf deinem PC im Anwendungsmenü nach **Terminal** und öffne es.
   Unter Windows im Startmenü nach **PowerShell** suchen und öffnen.
2. Melde dich mit deinem normalen Benutzer an der T95 an. Benutzername und
   IP-Adresse kennst du aus der [Grundinstallation](INSTALLATION.md#4-erstes-ssh-login-und-normalen-benutzer-einrichten).
   **Passe das folgende Beispiel vor dem Eingeben an:** `alex` ist der
   Beispielbenutzer, `192.168.178.50` die Beispieladresse der Box.

   **Auf dem PC, normaler Benutzer; Beispiel vorher anpassen:**

   ```bash
   ssh alex@192.168.178.50
   ```

3. Gib das Linux-Passwort dieses Benutzers ein und drücke **Enter**. Während
   der Eingabe erscheinen keine Zeichen oder Sternchen; das ist normal.
   Einen angezeigten SSH-Hostschlüssel nach der Grundinstallationsanleitung prüfen.

**Du bist richtig, wenn** du eine Eingabezeile wie `alex@t95:~$` siehst.
Name und Darstellung können bei dir anders sein. **Alle weiteren Befehle
auf dieser Seite gehören in diese Verbindung zur T95**, auch wenn du das
Fenster auf deinem PC geöffnet hast.

So verwendest du die Beispiele:

- Kopiere einen Befehl, füge ihn in das Fenster ein und drücke **Enter**.
  Bei mehreren Zeilen jede Zeile einzeln ausführen.
- Mit **„Beispielantwort“** beschriftete Kästen nur lesen; sie zeigen, was die
  Box antworten könnte. Alle Namen und Geräteadressen hier sind erfunden.
- Fragt ein Befehl nach einer **Geräteadresse**, füge die Adresse deines
  Kopfhörers aus der Geräteliste ein, etwa `AA:BB:CC:DD:EE:01`, und drücke Enter.
  Die vorgegebenen Befehlszeilen musst du dafür nicht bearbeiten.
- `sudo` erlaubt einem Befehl, die Verbindung zu ändern. Wird nach einem
  Passwort gefragt, verwende dein Linux-Passwort von der T95.
- Steht vor der Eingabe `[bluetooth]#` oder beispielsweise `[MX42H]#`, bist
  du noch im Bluetooth-Programm. Mit `quit` und Enter gelangst du zurück
  zur normalen Eingabe. Nur beim [erstmaligen Koppeln](#neue-kopfhörer-zum-ersten-mal-verbinden)
  bleiben wir ausdrücklich in diesem Programm.

<a id="die-passende-aufgabe-wählen"></a>

## 🧭 Die passende Aufgabe wählen

| Das möchtest du tun | Hier geht es weiter |
| --- | --- |
| 💾 Nachsehen, welche Geräte die Box bereits kennt | [Gekoppelte Geräte anzeigen](#gekoppelte-geräte-anzeigen) |
| 🔗 Nachsehen, was gerade verbunden ist | [Verbundene Geräte anzeigen](#verbundene-geräte-anzeigen) |
| 🎧 Einen bekannten Kopfhörer wieder benutzen | [Wieder verbinden und für Musik auswählen](#wieder-verbinden-und-für-musik-auswählen) |
| ⏸️ Die Verbindung für heute beenden | [Nur die Verbindung trennen](#nur-die-verbindung-trennen) |
| 💻 Den Kopfhörer am PC oder Handy verwenden | [Bluetooth auf der Box pausieren](#kopfhörer-am-pc-oder-handy-verwenden) |
| 🔎 Einen neuen Kopfhörer suchen | [Suchen und erstmals koppeln](#neue-kopfhörer-zum-ersten-mal-verbinden) |
| 🗑️ Einen Kopfhörer aus der Box löschen | [Gerät dauerhaft vergessen](#gerät-dauerhaft-vergessen) |
| 🛟 Ein Problem lösen | [Wenn etwas nicht klappt](#wenn-etwas-nicht-klappt) |

| Begriff | Bedeutung |
| --- | --- |
| 💾 **Gekoppelt** | Die Box kennt das Gerät, auch wenn der Kopfhörer ausgeschaltet ist. |
| 🔗 **Verbunden** | Die Funkverbindung besteht gerade. Für Musik muss der Kopfhörer außerdem als Ausgang ausgewählt sein. |

Hast du Bluetooth mit `t95-bluetooth off` pausiert? Dann vor dem Anzeigen,
Suchen oder Verbinden mit `t95-bluetooth on` wieder einschalten.

<a id="3-bereits-gekoppelte-geräte-bedienen"></a>

<a id="gekoppelte-geräte-anzeigen"></a>

## 💾 Gekoppelte Geräte anzeigen

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
bluetoothctl devices Paired
```

**Beispielantwort — nur lesen:**

```text
Device AA:BB:CC:DD:EE:01 MX42H
Device AA:BB:CC:DD:EE:02 Wohnzimmer-Lautsprecher
```

Hier sind zwei Geräte gespeichert. Der **Name steht rechts**, die
**Geräteadresse in der Mitte**. Für den Kopfhörer `MX42H` wäre die Adresse
im Beispiel `AA:BB:CC:DD:EE:01`. Verwende bei dir die Adresse aus deiner
wirklichen Ausgabe. Die Geräteadresse ist nicht die IP-Adresse der T95.

**Keine Gerätezeile?** Für den gewählten Bluetooth-Adapter sind dann noch
keine gekoppelten Geräte gelistet. Einen neuen Kopfhörer findest du über
[Suchen und Koppeln](#neue-kopfhörer-zum-ersten-mal-verbinden).
Bei einer Fehlermeldung stattdessen [die Hilfe](#wenn-etwas-nicht-klappt) öffnen.

<a id="verbundene-geräte-anzeigen"></a>

## 🔗 Verbundene Geräte anzeigen

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
bluetoothctl devices Connected
```

**Beispielantwort — nur lesen:**

```text
Device AA:BB:CC:DD:EE:01 MX42H
```

Dieser Kopfhörer ist gerade mit der Box verbunden. Bei leerer Liste besteht
aktuell keine Verbindung zu einem Gerät. Eine Verbindung startet noch keine Musik.

Für Einzelheiten zu einem Gerät **zuerst diesen Befehl eingeben**:

```bash
read -r -p 'Geräteadresse aus der Liste: ' BT_GERAET
```

Wenn die Frage erscheint, die Geräteadresse eingeben und Enter drücken.
**Danach die Angaben abrufen:**

```bash
bluetoothctl info "$BT_GERAET"
```

**So liest du wichtige Angaben in der Antwort:**

| Anzeige | Bedeutung |
| --- | --- |
| `Name: MX42H` | Name des ausgewählten Geräts |
| `Paired: yes` | Gerät ist gekoppelt und gespeichert |
| `Connected: yes` | Gerät ist gerade verbunden |
| `Connected: no` | Gerät ist gerade getrennt |
| `Trusted: yes` | Die Box vertraut diesem bereits eingerichteten Gerät |

<a id="wieder-verbinden-und-für-musik-auswählen"></a>

## 🎧 Wieder verbinden und für Musik auswählen

1. Kopfhörer einschalten. Eine Verbindung zum Handy oder PC dort trennen,
   damit der Kopfhörer für die Box verfügbar ist.
2. Die Adresse unter [gekoppelten Geräten](#gekoppelte-geräte-anzeigen) suchen.
3. **Auf der T95 Bluetooth einschalten:**

   ```bash
   t95-bluetooth on
   ```

4. **Diese Zeile eingeben.** Wenn die Frage erscheint, deine
   Kopfhöreradresse eingeben und Enter drücken:

   ```bash
   read -r -p 'Adresse deines Kopfhörers: ' BT_GERAET
   ```

5. **Danach verbinden und das Ergebnis prüfen:**

   ```bash
   sudo bluetoothctl connect "$BT_GERAET"
   bluetoothctl info "$BT_GERAET"
   ```

**Erfolg:** In der Antwort steht `Connected: yes`. Falls die Verbindung
scheitert, mit der [Fehlerhilfe](#wenn-etwas-nicht-klappt) fortfahren.

Damit die Musik an diesen Kopfhörer geht, **im selben Fenster** eingeben:

```bash
t95-bluetooth audio "$BT_GERAET"
```

**Erfolg:** Der Helfer meldet `Kopfhörer als MPD-Ausgang gewählt`. Er merkt
sich diesen Kopfhörer, setzt die Ausgangslautstärke auf 20 % und hält die
Musik zunächst an. MPD ist der Musikplayer der Box.
Wenn bereits Titel in seiner Warteschlange liegen, mit `mpc play` starten.
Für die erste Musiksammlung siehe [Musik abspielen](MUSIKPLAYER_CHEATSHEET.md#musiksammlung-einlesen-und-abspielen).
Ein verbundenes Gerät ohne Audiofunktion lässt sich nicht als Kopfhörer verwenden.

Die abgefragte Adresse wird nur für die folgenden Befehle in diesem Fenster
vorgemerkt. Wenn du die Verbindung zur Box später neu öffnest, beginne diesen
Abschnitt wieder bei Schritt 1. Ein erneutes Koppeln ist für einen gespeicherten
Kopfhörer nicht erforderlich.

<a id="nur-die-verbindung-trennen"></a>

## ⏸️ Nur die Verbindung trennen

Nutze das, wenn der Kopfhörer auf der Box gespeichert bleiben soll.
Suche seine Adresse bei den [verbundenen Geräten](#verbundene-geräte-anzeigen).
**Auf der T95 zuerst diese Zeile ausführen und die Gerätefrage beantworten:**

```bash
read -r -p 'Adresse des zu trennenden Geräts: ' BT_GERAET
```

**Danach die Musik stoppen, die Verbindung trennen und prüfen:**

```bash
mpc stop
sudo bluetoothctl disconnect "$BT_GERAET"
bluetoothctl info "$BT_GERAET"
```

**Erfolg direkt danach:** `Connected: no`, aber weiterhin `Paired: yes`.
Die Musik ist gestoppt. Später kannst du den Kopfhörer
[wieder verbinden](#wieder-verbinden-und-für-musik-auswählen).
Andere Geräte und Samba bleiben verfügbar. Falls sich der Kopfhörer
selbstständig wieder verbindet, verwende die folgende Bluetooth-Pause.

<a id="4-kopfhörer-am-pc-statt-am-server-nutzen"></a>

<a id="kopfhörer-am-pc-oder-handy-verwenden"></a>

## 💻 Kopfhörer am PC oder Handy verwenden

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
t95-bluetooth off
```

Jetzt kannst du den Kopfhörer am PC oder Handy verbinden. Die Box stoppt
Musik und schaltet **ihren gesamten Bluetooth-Funk** aus. Gespeicherte
Kopplungen bleiben erhalten; Dateiserver und Samba laufen weiter.

Später zuerst die Verbindung am PC oder Handy trennen. Dann den Abschnitt
[Wieder verbinden](#wieder-verbinden-und-für-musik-auswählen) verwenden.
Dort schaltet `t95-bluetooth on` den Funk wieder ein.
Nach einem Neustart kann der Funkzustand abweichen; bei Bedarf erneut einschalten.

<a id="2-neue-kopfhörer-koppeln"></a>

<a id="neue-kopfhörer-zum-ersten-mal-verbinden"></a>

## 🔎 Neue Kopfhörer zum ersten Mal verbinden

### A. Kopfhörer vorbereiten

Schalte den **Kopplungsmodus** laut Kopfhöreranleitung ein. Nur Einschalten
reicht häufig nicht. Eine Verbindung zu einem anderen Gerät vorher trennen.
**Im normalen T95-Fenster eingeben:**

```bash
t95-bluetooth pair
```

### B. Suche starten

Jetzt ist das Bluetooth-Programm geöffnet. Du erkennst es an einer Eingabe
wie `[bluetooth]#`. **Nur die folgenden Befehle eingeben, jeden einzeln:**

```text
power on
agent on
default-agent
scan on
```

Warte etwa 15–30 Sekunden. Das Programm sucht nach sichtbaren Geräten in
Reichweite. **Erfundene Beispielantwort — nur lesen:**

```text
Discovery started
[NEW] Device AA:BB:CC:DD:EE:01 MX42H
[NEW] Device AA:BB:CC:DD:EE:02 Arbeits-PC
[NEW] Device AA:BB:CC:DD:EE:03 Wohnzimmer-Lautsprecher
```

Der Beispielkopfhörer heißt `MX42H`. Suchst du einen anderen Kopfhörer,
verwende dessen Namen und Adresse aus deiner Ausgabe. Mit `devices` kannst
du die gefundenen und bekannten Geräte noch einmal anzeigen. Ein Scan kann
auch Geräte ohne Audiofunktion finden.

### C. Den gefundenen Kopfhörer speichern und verbinden

**Du bist weiterhin im Bluetooth-Programm.** Ersetze in den folgenden Zeilen
`AA:BB:CC:DD:EE:01` durch die Adresse deines Kopfhörers. Jede Zeile einzeln
eingeben. Fragt das Programm nach einer Bestätigung mit `yes/no`, prüfe,
ob es dein Gerät ist, und bestätige mit `yes` und Enter. Wird auf beiden
Geräten eine Zahl angezeigt, müssen die Zahlen übereinstimmen.

```text
pair AA:BB:CC:DD:EE:01
trust AA:BB:CC:DD:EE:01
connect AA:BB:CC:DD:EE:01
info AA:BB:CC:DD:EE:01
```

**Erfolg:** `Paired: yes` und `Connected: yes`. Damit ist der Kopfhörer
gespeichert und verbunden; `Trusted: yes` zeigt das eingerichtete Vertrauen.
Wenn ein Befehl scheitert, zuerst die [Hilfe](#wenn-etwas-nicht-klappt) lesen.

### D. Suche beenden und zur normalen Eingabe zurückkehren

**Noch im Bluetooth-Programm, einzeln eingeben:**

```text
scan off
quit
```

Du siehst wieder die normale Eingabe der T95. **Dort** die folgende Zeile
ausführen und die gleiche Geräteadresse bei der Frage eingeben:

```bash
read -r -p 'Adresse des gerade verbundenen Kopfhörers: ' BT_GERAET
```

**Danach den Kopfhörer für Musik auswählen:**

```bash
t95-bluetooth audio "$BT_GERAET"
```

Der Helfer bestätigt die Wahl und hält die Wiedergabe zunächst an.
Musik nach der [Musikplayer-Anleitung](MUSIKPLAYER_CHEATSHEET.md) vorbereiten.
Beim nächsten Mal genügt [Wieder verbinden](#wieder-verbinden-und-für-musik-auswählen).

<a id="gerät-dauerhaft-vergessen"></a>

## 🗑️ Gerät dauerhaft vergessen

Nutze das, wenn die Box sich diesen Kopfhörer nicht mehr merken soll.
Suche seine Adresse zuerst bei den [gekoppelten Geräten](#gekoppelte-geräte-anzeigen).
**Auf der T95 zuerst diese Zeile ausführen und die Gerätefrage beantworten:**

```bash
read -r -p 'Adresse des zu vergessenden Geräts: ' BT_GERAET
```

**Danach die Musik stoppen, das Gerät vergessen und die Liste prüfen:**

```bash
mpc stop
sudo bluetoothctl remove "$BT_GERAET"
bluetoothctl devices Paired
```

**Erfolg:** Das Gerät steht nicht mehr in der Liste gekoppelter Geräte.
Andere Kopplungen und deine Musik bleiben erhalten. Ein späterer Scan kann
den Kopfhörer wieder finden; für seine Verwendung musst du ihn neu koppeln.
Gegebenenfalls auch am Kopfhörer die alte Verbindung zur Box löschen.

Der Musikplayer bleibt dabei installiert. Wenn du ihn vollständig entfernen
möchtest, findest du dafür eine eigene [Deinstallationsanleitung](../server/bluetooth/README.md#player-entfernen-und-bluetooth-deaktivieren).

<a id="5-wenn-kein-gerät-gefunden-wird"></a>

<a id="wenn-etwas-nicht-klappt"></a>

## 🛟 Wenn etwas nicht klappt

| Das siehst du | Das kannst du tun |
| --- | --- |
| Beim Passworttippen erscheint nichts | Das ist normal. Passwort fertig eingeben und Enter drücken. |
| `command not found` bei `t95-bluetooth` | Prüfen, ob du auf der T95 angemeldet bist und [Bluetooth installiert](../server/bluetooth/README.md) ist. |
| Statt der normalen Eingabe steht `[bluetooth]#` | Mit `quit` zurückkehren; Befehle mit `sudo`, `read` oder `t95-bluetooth` gehören in die normale Eingabe. |
| `Device ... not available` | Adresse aus deiner Liste vollständig kopieren; Kopfhörer einschalten. Bei einem neuen Gerät zuerst suchen und koppeln. |
| Kopfhörer fehlt beim Suchen | Kopplungsmodus, Abstand und Handy-/PC-Verbindung prüfen. Dann erneut suchen. |
| `Waiting to connect to bluetoothd...` und es geht nicht weiter | Mit **Strg+C** abbrechen. Im normalen T95-Fenster `t95-bluetooth on` ausführen und erneut versuchen. |
| `No default controller available` | Im normalen T95-Fenster `t95-bluetooth on` ausführen und erneut prüfen. Wenn der Fehler bleibt: technische Diagnose unten. |
| `Connected: no` trotz Verbindungsversuch | Kopfhörer einschalten, andere Verbindungen trennen und den Abschnitt „Wieder verbinden“ erneut ausführen. |
| Verbunden, aber kein Ton | Den Kopfhörer mit `t95-bluetooth audio` samt seiner Adresse auswählen; die Musik bleibt dabei zunächst gestoppt. Eine gefüllte Warteschlange mit `mpc play` starten. Weitere Hilfe: [Musikplayer](MUSIKPLAYER_CHEATSHEET.md#kein-ton-oder-keine-tastenreaktion). |
| Gerät verbindet sich nach dem Trennen wieder | `t95-bluetooth off` pausiert den Bluetooth-Funk der Box. |

Am Ende kannst du das Fenster mit `exit` von der T95 abmelden.
Das schaltet weder die Box noch eine laufende Musikwiedergabe aus.

<a id="1-adapter-und-usb-geräte-finden"></a>

<details>
<summary>Technische Diagnose für Fortgeschrittene</summary>

Diese Prüfungen sind für den normalen Verbindungswechsel nicht nötig.
**Ort: T95, normaler SSH-Benutzer; `sudo` nur dort verwenden, wo es steht.**

```bash
bluetoothctl list
bluetoothctl show
rfkill list bluetooth
lsusb
lsusb -t
```

`bluetoothctl list` zeigt lokale Bluetooth-Adapter. `select` in einer
interaktiven `sudo bluetoothctl`-Sitzung wählt einen solchen Adapter;
das gewünschte entfernte Gerät wird über seine Adresse bei `pair`/`connect`
gewählt. Adapter- und Kopfhöreradresse unterscheiden sich.
Das interne BCM43342 verwendet UART und erscheint nicht in `lsusb`.
`lsusb` zeigt USB-Hardware, keine drahtlosen Kopfhörer; ein USB-WLAN-Stick
enthält nicht automatisch Bluetooth.

```bash
for device in /sys/class/bluetooth/hci*; do
    [ -e "$device" ] || continue
    printf '%s: ' "${device##*/}"
    readlink -f "$device/device"
done
```

Bei weiterem Diagnosebedarf:

```bash
t95-bluetooth status
sudo journalctl -u bluetooth -b --no-pager -n 60
sudo dmesg | grep -Ei 'Bluetooth|hci0|btbcm|firmware' | tail -n 60
```

`t95-bluetooth restart` startet Bluetooth neu; die Musik bleibt gestoppt.
Eine Hardware-Funksperre lässt sich nicht per Software aufheben. Bei
`firmware Patch file not found` die [technischen Voraussetzungen](../server/bluetooth/README.md#technischer-umfang-und-nachweise)
prüfen. Keine beliebige Firmware laden und keine Treiber auf Verdacht entladen.
`untrust ADRESSE` in `bluetoothctl` hebt Vertrauen auf, behält aber die Kopplung.

[BlueZ-Befehlsreferenz für Debian Trixie](https://manpages.debian.org/trixie/bluez/bluetoothctl.1.en.html)

</details>
