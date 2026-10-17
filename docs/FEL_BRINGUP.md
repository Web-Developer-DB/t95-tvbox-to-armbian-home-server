<a id="fel-bring-up-ohne-flashen"></a>

# 🔌 FEL-Bring-up ohne Flashen

**Deutsch** | [English](FEL_BRINGUP.en.md)

FEL ist ein flüchtiger Allwinner-USB-Modus. Ausschalten entfernt den RAM-
Zustand. Diese Stufe dient der Identifikation und dem späteren eGON-Test, nicht
dem Überschreiben der eMMC.

Die Methode zum Aktivieren ist boardabhängig. Verbinde den passenden OTG-Port mit dem Linux-PC und prüfe unten die Erkennung.

| Beobachtung | Was jetzt? |
| --- | --- |
| 🔎 USB-Gerät erkannt | T95-Referenz: `1f3a:efe8`; SoC zusätzlich mit `sunxi-fel version` prüfen |
| ✅ H616 erkannt | Referenz: `soc=00001823(H616)`; erst danach den passenden Diagnoseweg wählen |
| 🛑 Kein Gerät oder Timeout | Stoppen; Kabel, OTG-Port, Taste, Stromversorgung und SoC prüfen |

<a id="usb-erkennung-prüfen"></a>

## 🔎 USB-Erkennung prüfen

**Auf dem Linux-PC mit angeschlossener FEL-Box; erforderliche USB-Zugriffsrechte vorausgesetzt:**

```bash
lsusb | grep -i allwinner
sunxi-fel version
```

Vergleiche beide Ausgaben mit den Merkmalen in der Tabelle. Ohne passende Erkennung hier stoppen und die Verbindung prüfen.

`bash build/build-h616-fel-egon.sh` erzeugt einen `eGON.BT0`-Kandidaten, führt
aber keinen Upload aus. Auf gesicherten H616 kann generisches `sunxi-fel uboot`
am Secure-FEL-Handoff scheitern; das beweist weder einen RAM- noch DTB-Fehler.
Erst nach einer passenden Uploader-/Boot-ROM-Prüfung fortfahren.
