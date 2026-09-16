# Veröffentlichung auf GitHub

Das Modul liegt im Hauptrepository unter `server/samba-usb/`. Es kann dort
gemeinsam mit dem T95-Armbian-Projekt veröffentlicht werden; die technische
Dokumentation und die Skripte bleiben über diesen Pfad reproduzierbar.

## Hauptrepository veröffentlichen

```bash
cd /pfad/zum/t95-tvbox-to-armbian-home-server
git add README.md server/samba-usb
git commit -m "Document Samba and dynamic USB home-server setup"
git push
```

## Eigenständiges Repository (optional)

Nur wenn das Modul bewusst separat gepflegt werden soll:

```text
T95-Samba-USB-Setup/
```

Anschließend:

```bash
git init
git add .
git commit -m "Document Samba and dynamic USB share setup"
```

## Vor dem Push prüfen

```bash
git status
git diff --cached
```

Keine Passwörter, `passdb.tdb`, privaten Schlüssel oder System-Images committen.
Die `.gitignore` deckt typische problematische Dateien ab, ersetzt aber keine
manuelle Kontrolle. Nach Änderungen am Modul muss `MANIFEST.sha256` mit den
neuen Datei-Hashes aktualisiert und anschließend erneut geprüft werden:

```bash
cd server/samba-usb
sha256sum -c MANIFEST.sha256
```
