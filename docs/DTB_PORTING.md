# DTB-Portierung: erst nach stabilem FEL-/DRAM-Test

Die Device-Tree-Datei beschreibt die konkrete Platine. Sie ist kein Ersatz
für einen passenden SPL/U-Boot-Loader: Wenn U-Boot keinen Banner ausgibt oder
DRAM nicht initialisieren kann, zuerst [FEL](FEL_BRINGUP.md) und
[DRAM/PMIC](DRAM_PMIC.md) prüfen.

## Sicherer Ablauf

1. Einen möglichst nahen Upstream- oder Armbian-DTB als Ausgangspunkt wählen.
2. Nur belegte Hardwareknoten ergänzen: UART, SD, eMMC, PMIC, RAM-Parameter,
   Ethernet-PHY und die tatsächlich vorhandenen USB-Ports.
3. DTB mit dem zur Kernelversion passenden `dtc` bauen und vor dem Einsatz
   mit `fdtdump` oder `fdtget` kontrollieren.
4. Den neuen DTB zunächst zusammen mit dem unveränderten Root-Dateisystem
   testen. Nicht gleichzeitig Kernel, Rootfs und DTB austauschen.
5. Den vollständigen UART-Log sichern und erst bei stabilem Kernelstart
   weitere Komponenten aktivieren.

## Ethernet: besonders platinenabhängig

Die getestete T95 nutzt den Allwinner-AC300-EPHY über RMII. Bei einer anderen
H616-Box können PHY-Adresse, Reset-GPIO, Clock, Versorgung und sogar der PHY
selbst abweichen. Erwartete Kernelmarker der getesteten Variante sind
`end0`, ein erkannter PHY und ein Link-Status. Diese Marker belegen **nicht**,
dass die T95-DTS für ein anderes Board korrekt ist.

| Beobachtung im UART-Log | Wahrscheinliche Schicht | Nächster sicherer Schritt |
| --- | --- | --- |
| Kernel startet, kein `end0` | DTB-/MAC-Knoten | `aliases`, MAC-Knoten und kompatiblen Ethernet-Controller vergleichen |
| `end0` vorhanden, Link bleibt down | PHY/RMII/Reset/Clock | PHY-Adresse und Reset-/Clock-Signale prüfen; nicht Samba oder DHCP ändern |
| Link up, keine Adresse | Userspace | DHCP mit `ip -br addr`, `journalctl -u NetworkManager` prüfen |
| USB, Audio oder WLAN fehlerhaft | einzelner Peripherieknoten | Knoten separat deaktivieren oder nach Boardbeleg prüfen |

## Stop-Kriterien

- Keine zufälligen GPIO-, PHY- oder Spannungswerte ausprobieren.
- Bei Kernel-Panic, Dateisystemfehlern oder wiederholten DRAM-Fehlern zum
  letzten funktionierenden DTB zurückkehren.
- Die interne eMMC bleibt während der Portierung unverändert.

Weiter: [UART-basiertes Boot-Troubleshooting](BOOT_TROUBLESHOOTING.md).
