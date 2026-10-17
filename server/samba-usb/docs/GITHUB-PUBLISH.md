<a id="veröffentlichung-auf-github"></a>

# 🌐 Veröffentlichung auf GitHub

**Deutsch** | [English](GITHUB-PUBLISH.en.md)

Das Modul liegt im Hauptrepository unter `server/samba-usb/`. Es kann dort
gemeinsam mit dem T95-Armbian-Projekt veröffentlicht werden; die technische
Dokumentation und die Skripte bleiben über diesen Pfad reproduzierbar.

| Entscheidung | Passender Weg |
| --- | --- |
| 📁 Modul im T95-Projekt pflegen | [Hauptrepository](#hauptrepository-veröffentlichen); empfohlener bestehender Ablageort |
| 🧩 Modul bewusst separat pflegen | [Eigenständiges Repository](#eigenständiges-repository-optional) |
| ✅ Vor jedem Push | [Dateien und Manifest prüfen](#vor-dem-push-prüfen) |

**Ausführungsort:** Linux-PC, lokale Repository-Kopie; als Benutzer mit GitHub-Push-Recht. Beispielpfade vorher anpassen.

<a id="hauptrepository-veröffentlichen"></a>

## 📁 Hauptrepository veröffentlichen

```bash
cd /pfad/zum/t95-tvbox-to-armbian-home-server
git add README.md server/samba-usb
git commit -m "Document Samba and dynamic USB home-server setup"
git push
```

<a id="eigenständiges-repository-optional"></a>

## 🧩 Eigenständiges Repository (optional)

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

<a id="vor-dem-push-prüfen"></a>

## ✅ Vor dem Push prüfen

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
