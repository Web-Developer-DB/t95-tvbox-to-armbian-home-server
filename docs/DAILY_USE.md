<a id="die-t95-im-alltag-benutzen"></a>

# 🧭 Die T95 im Alltag benutzen

**Deutsch** | [English](DAILY_USE.en.md)

Deine Box ist eingerichtet und die Kernel-/DTB-Sperre gesetzt? Hier findest
du die täglichen Handgriffe. Eine neue Box zuerst nach der
[Installationsanleitung](INSTALLATION.md) einrichten.

[Startseite](../README.md) · [Hilfe nach Symptomen](TROUBLESHOOTING.md)

<a id="mit-der-box-verbinden"></a>

## 🔑 Mit der Box verbinden

1. Auf deinem PC im Anwendungsmenü **Terminal** öffnen; unter Windows **PowerShell**.
2. Im Beispiel `alex` durch deinen normalen T95-Benutzer und `192.168.178.50`
   durch die aktuelle Adresse der Box aus dem Router ersetzen.

**Auf dem PC, normaler Benutzer; Beispiel vorher anpassen:**

```bash
ssh alex@192.168.178.50
```

Gib bei der Frage das Linux-Passwort dieses T95-Benutzers ein und drücke Enter.
Es erscheinen keine Zeichen oder Sternchen. Einen neuen SSH-Schlüssel nach der
[Anmeldeanleitung](INSTALLATION.md#4-erstes-ssh-login-und-normalen-benutzer-einrichten) prüfen.

**Ergebnis:** Eine Eingabezeile wie `alex@t95:~$`. Du bedienst jetzt die T95,
obwohl das Fenster auf deinem PC steht. Die folgenden Box-Befehle gehören in
dieses Fenster. Bei Verbindungsproblemen [SSH-Hilfe öffnen](TROUBLESHOOTING.md#ssh-anmeldung-scheitert).

<a id="die-passende-aufgabe-wählen"></a>

## 🧭 Die passende Aufgabe wählen

| Du möchtest … | Hier geht es weiter |
| --- | --- |
| 📂 Dateien auf der Box öffnen oder speichern | [Dateizugriff am PC, Handy oder in VLC](../server/samba-usb/README.md#zugriff-von-clients-und-vlc) |
| ⏏️ Einen USB-Datenträger abziehen | [Genau dieses Laufwerk sicher auswerfen](../server/samba-usb/README.md#usb-sicher-auswerfen) |
| 🎧 Kopfhörer finden, verbinden oder trennen | [Bluetooth einfach bedienen](BLUETOOTH_CHEATSHEET.md) |
| 🎵 Eigene Musik übertragen und hören | [Erste Musikdatei abspielen](MUSIKPLAYER_CHEATSHEET.md#start-kopfhörer-und-musik-bereitstellen) |
| 🗂️ Den eingerichteten Zustand sichern | [Vollständiges SD-Backup](BACKUP.md) |
| 📊 Systeminformationen bei der Anmeldung sehen | [Dashboard einrichten](SSH_DASHBOARD.md) |

Die feste Freigabe `T95-DATA` liegt beim empfohlenen Erststart auf der System-SD.
USB-Laufwerke haben eigene Freigaben. Ein SD-Backup sichert keine Daten auf
separaten USB-Laufwerken oder eMMC; diese regelmäßig zusätzlich sichern.

> [!TIP]
> **Nur das Fenster schließen?** Die Box bleibt an. Wähle unten bewusst zwischen Abmelden, Neustarten und Herunterfahren.

| Deine Absicht | Wirkung |
| --- | --- |
| 🚪 [SSH abmelden](#nur-von-ssh-abmelden) | Nur deine Verbindung endet; der Server läuft weiter. |
| 🔄 [Neu starten](#die-box-neu-starten) | Die Box startet neu; danach wieder per SSH anmelden. |
| ⏻ [Herunterfahren](#die-box-sauber-herunterfahren) | Das System wird beendet; erst danach SD oder Strom trennen. |

<a id="nur-von-ssh-abmelden"></a>

## 🚪 Nur von SSH abmelden

**Auf der T95, normaler SSH-Benutzer:**

```bash
exit
```

**Ergebnis:** Du bist wieder am PC. Die Box, Dateifreigaben und eine bereits
laufende Musikwiedergabe laufen weiter. Auch das Schließen des Terminalfensters
schaltet die T95 nicht aus.

<a id="die-box-neu-starten"></a>

## 🔄 Die Box neu starten

Offene Dateien auf den Clients speichern und laufende Kopiervorgänge beenden.

**Auf der T95, normaler SSH-Benutzer mit `sudo`:**

```bash
sudo reboot
```

**Ergebnis:** SSH wird getrennt; die Box startet neu. Sobald sie im Router
wieder erreichbar ist, erneut anmelden. Bei einer anderen IP-Adresse den
SSH-Aufruf anpassen. Bei Problemen die [Start-/Netzwerkhilfe](TROUBLESHOOTING.md#keine-ip-adresse) verwenden.

<a id="die-box-sauber-herunterfahren"></a>

## ⏻ Die Box sauber herunterfahren

Offene Dateien speichern und Kopiervorgänge beenden.

**Auf der T95, normaler SSH-Benutzer mit `sudo`:**

```bash
sudo poweroff
```

**Ergebnis:** Die SSH-Verbindung endet und die Box fährt herunter. Warte auf
das vollständig beendete Herunterfahren, bevor du die SD entnimmst oder die
Stromversorgung trennst. Der Verbindungsabbruch allein beweist noch nicht,
dass alle Schreibvorgänge abgeschlossen sind.
Zum nächsten Start die Box wieder mit der passenden Stromversorgung einschalten.

<a id="vor-neuen-anwendungen"></a>

## 🔒 Vor neuen Anwendungen

[Kernel-/DTB-Sperre beibehalten](INSTALLATION.md#5-kernel-und-dtb-vor-updates-schützen).
Bei gesetzter Sperre kannst du passende optionale Module oder
[weitere Armbian-Anwendungen](../README.md#weitere-anwendungen-installieren) auswählen.
Ein [vollständiges SD-Backup](BACKUP.md) ist optional und bewahrt den aktuellen
Einrichtungsstand für eine spätere Wiederherstellung.
