# DRAM und PMIC: Werte ermitteln, nicht raten

Die T95-Referenz nutzt DDR3, 2 GiB, 600 MHz und AXP313A-DCDC3 mit 1,36 V.
Diese Werte sind nur für die getestete Platine belegt.

| T95-Parameter | Für andere Platinen prüfen |
| --- | --- |
| DDR3 und 600 MHz | tatsächlicher Typ, Breite, Kapazität, Stock-Takt |
| ODT/DRI/TPR10–12 | Stock-Log, Original-DTB/Bootdateien, Herstellerkernel |
| AXP313A bei `0x36` | PMIC-Chip, Busadresse und Regulatoren |
| DCDC3 1360 mV | DRAM-Rail anhand belastbarer Quelle |

Wenn SPL vor einer DRAM-Meldung stoppt oder die Größe unplausibel ist, nur
DRAM-/PMIC-Parameter untersuchen. Kernel, Rootfs, Ethernet und Samba sind in
dieser Stufe nicht relevant.

> [!CAUTION]
> Spannungen nicht durch Probieren erhöhen. Ohne belastbaren Nachweis bei
> flüchtigen FEL-Tests bleiben und keine SD/eMMC beschreiben.
