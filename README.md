# T95 H616 / AXP313A als kleiner Linux-Server

Dieses Projekt hält einen auf echter Hardware geprüften, **SD-basierten**
Linux-Start für genau diese Platine fest:

```text
H616-T95MAX-AXP313A-V3.0
Allwinner H616 · AXP313A · AC300-Ethernet-PHY · 2 GiB RAM
```

Es ist ein experimenteller Release für diese eine Board-Revision. „T95“ ist
keine eindeutige Hardwarebezeichnung: Eine optisch ähnliche Box darf dieses
Image nicht ohne eigene UART-/Platinenprüfung verwenden.

## Fotos der geprüften Hardware

Die folgenden Fotos zeigen das konkrete Gehäuse und die Platine der
untersuchten `H616-T95MAX-AXP313A-V3.0`. Sie dienen der visuellen Zuordnung und
ersetzen keine elektrische oder UART-Prüfung. Die Bilddateien liegen unter
[`docs/images/`](docs/images/); die EXIF-Metadaten wurden für die
Veröffentlichung entfernt. Auf dem Unterseitenfoto ist der individuelle
MAC-/Barcode-Aufkleber absichtlich abgedeckt.

<p>
  <img src="docs/images/t95-box-top.jpg" alt="Oberseite des T95-Gehäuses" width="260">
  <img src="docs/images/t95-case-bottom-redacted.jpg" alt="Unterseite des T95-Gehäuses, individueller Aufkleber abgedeckt" width="260">
</p>
<p>
  <img src="docs/images/t95-board-memory.jpg" alt="T95-Platine mit H616 und Speicherbausteinen" width="260">
  <img src="docs/images/t95-board-connectors.jpg" alt="T95-Platine mit Anschlüssen und AC300-Bereich" width="260">
</p>

## Nachgewiesener Stand

- eigener TOC0-/U-Boot-Start von microSD, ohne Änderung der internen eMMC;
- Armbian 26.8.4 Trixie mit Linux `6.18.48-current-sunxi64`;
- 2 GiB DRAM, AC300-Ethernet, `end0`, 100 Mbit/s Vollduplex und DHCP;
- SSH-Anmeldung und die Armbian-Ersteinrichtung auf der Ausgangskonfiguration
  erfolgreich;
- Root-Dateisystem wird beim ersten Start auf die Karte erweitert.

Der Release ist für einen kleinen, stromsparenden Dateiserver gedacht. SMB,
eine extern versorgte USB-Platte, mehrere Kaltstarts und Langzeitstabilität
sind bewusst **Folgearbeiten** und keine Zusage dieses ersten Releases.

## UART-Adapter für die Diagnose

Für die Bootaufzeichnungen wurde ein **RP2040-Zero** als externer USB-zu-
TTL-UART-Adapter eingesetzt. Er ist kein Teil des SoC-Bootpfads und verändert
weder die T95 noch deren eMMC. Das zugehörige, separate Projekt mit Firmware,
Verdrahtung und Capture-Werkzeugen ist hier dokumentiert:

[Web-Developer-DB/rp2040-zero-uart-adapter](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter)

Für diese T95-Verbindung gelten 3,3-V-TTL und 115200 Baud, 8N1. Die übliche
Kreuzverdrahtung lautet: RP2040 `GP0` (TX) an T95-RX, RP2040 `GP1` (RX) an
T95-TX und gemeinsame Masse. 5-V-TTL und echtes RS-232 dürfen nicht direkt
angeschlossen werden. Für reine Bootaufzeichnung kann die TX-Leitung des
Adapters getrennt bleiben, damit ausschließlich die T95 sendet.

## Sicherheitsgrenzen

- Das Image startet von microSD. Es liest oder beschreibt während des normalen
  Bootvorgangs nicht die Android-eMMC.
- Die alte Android-Firmware, einschließlich eines möglichen BADBOX-Befunds,
  wird weder übernommen noch als Vertrauensquelle verwendet. Die eMMC wird
  durch dieses Projekt aber auch nicht bereinigt.
- `clk_ignore_unused nohz=off` sind vorläufige Diagnoseparameter. Kernel- und
  Bootloader-Aktualisierungen nicht blind übernehmen.
- Nur bei ausgeschalteter Box Karte einsetzen oder entnehmen.

## Kernel- und DTB-Updates einfrieren

Die geprüfte Kombination aus H616-Kernel, DTB und AC300-Netzwerktreiber soll
nach der Ersteinrichtung nicht durch ein automatisches Paketupdate ersetzt
werden. Auf der laufenden T95 werden deshalb die beiden Armbian-Metapakete
gehalten:

```bash
sudo apt-mark hold linux-image-current-sunxi64 linux-dtb-current-sunxi64
apt-mark showhold
```

Die Ausgabe von `apt-mark showhold` muss beide Paketnamen enthalten. Zusätzlich
kann der installierte Stand dokumentiert werden:

```bash
uname -r
dpkg-query -W -f='${binary:Package}\t${Version}\t${Status}\n' \\
  linux-image-current-sunxi64 linux-dtb-current-sunxi64
```

Vor einer späteren bewussten Kernel-/DTB-Aktualisierung zuerst ein vollständiges
Backup erstellen, UART bereithalten und die Sperre gezielt aufheben:

```bash
sudo apt-mark unhold linux-image-current-sunxi64 linux-dtb-current-sunxi64
sudo apt update
sudo apt full-upgrade
```

Nach jedem solchen Update muss die T95-spezifische DTB, der Ethernet-Treiber,
ein Kaltstart und die Netzwerkverbindung erneut geprüft werden. Die Sperre ist
eine Schutzmaßnahme für den nachgewiesenen Stand, kein Ersatz für Backups oder
Sicherheitsupdates.

## Sicherer Schnellstart mit dem Release-Asset

Das öffentliche Release enthält absichtlich **kein verwendbares
Root-Passwort und keine SSH-Hostschlüssel**. Das Rootkonto ist im generischen
Download gesperrt. Vor dem Schreiben erzeugt der Anwender daher eine lokale,
nicht zu veröffentlichende Kopie mit einem eigenen Passwort. Bei ihrem ersten
SSH-Start generiert die T95 anschließend eigene Hostschlüssel, bevor `sshd`
Verbindungen annimmt.

1. Aus dem GitHub-Release alle sieben Dateien herunterladen, insbesondere das
   Image `T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v0.1.1-hardened-experimental.img.xz`,
   `RELEASE-MANIFEST.txt`, `HARDENING-METADATA.txt` und `SHA256SUMS`.
2. Die Prüfsummen im Download-Ordner prüfen:

   ```bash
   sha256sum -c SHA256SUMS
   ```

3. Das generische Image entpacken und **außerhalb** des Repositorys eine
   lokale Kopie personalisieren. Das Werkzeug fragt zweimal verdeckt nach
   einem eigenen Passwort (mindestens 12 Zeichen) und speichert den Hash nur
   in dieser lokalen Image-Kopie:

   ```bash
   export REPO=/pfad/zum/t95-h616-axp313a-projekt
   export DOWNLOAD=/pfad/zum/GitHub-Release-Download
   mkdir -p "$HOME/t95-private"
   xz -dk --keep \
     "$DOWNLOAD/T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v0.1.1-hardened-experimental.img.xz"
   bash "$REPO/tools/provision-t95-release-image.sh" \
     "$DOWNLOAD/T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v0.1.1-hardened-experimental.img" \
     "$HOME/t95-private/t95-personal.img" \
     PROVISION-T95-ROOT-PASSWORD
   ```

   `t95-personal.img` und die gleichnamige Datei mit Endung
   `.t95-provisioned-manifest` sind privat. Sie gehören weder in Git noch in
   einen GitHub-Release.

4. Das Zielgerät jedes Mal neu bestimmen. Es muss eine entbehrliche,
   wechselbare microSD-Karte sein, zum Beispiel `/dev/sdX`:

   ```bash
   lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS
   ```

5. Das geprüfte Schreibwerkzeug verwenden. Es akzeptiert nur ein wechselbares
   `/dev/sdX`, verlangt ein explizites Token, prüft die lokale Manifest- und
   Image-Hashsumme und überschreibt ausschließlich die ausgewählte Karte:

   ```bash
   bash "$REPO/tools/write-t95-provisioned-image-to-sd.sh" \
     /dev/sdX \
     "$HOME/t95-private/t95-personal.img" \
     "$HOME/t95-private/t95-personal.img.t95-provisioned-manifest" \
     WRITE-T95-PROVISIONED-TO-SDX
   ```

6. Karte in die ausgeschaltete T95 einsetzen, Ethernet mit dem Router
   verbinden und einschalten. Die DHCP-Adresse steht im Router oder lässt sich
   im lokalen Netz ermitteln. Die erste Anmeldung erfolgt über SSH; Armbian
   führt durch die Ersteinrichtung. Dabei wird das bei Schritt 3 gewählte
   Passwort verwendet – es existiert kein veröffentlichtes Standardpasswort.

Die Härtung des generischen Images wurde offline geprüft. Ein Kaltstart des
neuen Release-Assets nach dieser reinen Zugangsdaten-Härtung ist noch als
eigener, dokumentierter Abnahmetest offen.

Ausführliche Schritte, die Buildkette, Wiederherstellung und die Grenzen
stehen in [docs/RELEASE.md](docs/RELEASE.md). Hinweise für eine spätere
GitHub-Veröffentlichung stehen in [docs/PUBLISHING.md](docs/PUBLISHING.md).

## Projektstruktur

- [docs/RELEASE.md](docs/RELEASE.md) – geprüfter Releaseweg und Buildgrenzen.
- [docs/VALIDATION.md](docs/VALIDATION.md) – öffentliche Testmatrix und Hash-Nachweise.
- [build/README.md](build/README.md) – hostseitige Buildkette.
- [tools/provision-t95-release-image.sh](tools/provision-t95-release-image.sh) –
  lokale, nicht öffentliche Passwort-Initialisierung.
- [tools/write-t95-provisioned-image-to-sd.sh](tools/write-t95-provisioned-image-to-sd.sh) –
  verifizierter SD-Schreiber für die persönliche Kopie.

## Lizenz und Veröffentlichung

Für dieses Repository ist absichtlich noch keine Lizenz festgelegt. Vor einer
Veröffentlichung muss der Maintainer eine Lizenz auswählen und die Lizenzen
aller übernommenen Upstream-Bestandteile prüfen. Das große Image gehört als
Release-Asset zu GitHub, nicht in das Repository.
