# Veröffentlichung auf GitHub

Das Archiv ist so aufgebaut, dass der komplette Ordner direkt als Git-Repository verwendet oder in ein bestehendes T95-Projekt kopiert werden kann.

## Neues Repository lokal vorbereiten

```bash
cd T95-Samba-USB-Setup
git init
git add .
git commit -m "Document Samba and dynamic USB share setup"
git branch -M main
git remote add origin git@github.com:USER/REPOSITORY.git
git push -u origin main
```

## In ein bestehendes Projekt übernehmen

Empfohlener Zielordner, z. B.:

```text
docs/t95-samba-usb/
```

oder als eigener Infrastruktur-Ordner:

```text
server/samba-usb/
```

Anschließend:

```bash
git add docs/t95-samba-usb
git commit -m "Add T95 Samba USB automount documentation"
git push
```

## Vor dem Push prüfen

```bash
git status
git diff --cached
```

Keine Passwörter, `passdb.tdb`, privaten Schlüssel oder System-Images committen. Die bereitgestellte `.gitignore` deckt typische problematische Dateien ab, ersetzt aber keine manuelle Kontrolle.
