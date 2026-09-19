# FEL-Bring-up ohne Flashen

FEL ist ein flüchtiger Allwinner-USB-Modus. Ausschalten entfernt den RAM-
Zustand. Diese Stufe dient der Identifikation und dem späteren eGON-Test, nicht
dem Überschreiben der eMMC.

Die Methode zum Aktivieren ist boardabhängig. Nach Anschluss am OTG-Port:

```bash
lsusb | grep -i allwinner
sunxi-fel version
```

Auf der T95 erschien `1f3a:efe8` und `soc=00001823(H616)`. Kein Gerät oder ein
Timeout ist ein Stoppkriterium: Kabel, OTG-Port, Taster, Stromversorgung und
SoC zuerst prüfen.

`bash build/build-h616-fel-egon.sh` erzeugt einen `eGON.BT0`-Kandidaten, führt
aber keinen Upload aus. Auf gesicherten H616 kann generisches `sunxi-fel uboot`
am Secure-FEL-Handoff scheitern; das beweist weder einen RAM- noch DTB-Fehler.
Erst nach einer passenden Uploader-/Boot-ROM-Prüfung fortfahren.
