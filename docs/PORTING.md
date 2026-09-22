# H616-TV-Box portieren: sicherer Bring-up-Pfad

Diese Anleitung ist für Entwickler mit einer ähnlichen, nicht exakt getesteten
H616-TV-Box. Das v1.0.1-Image ist ausschließlich für
`H616-T95MAX-AXP313A-V3.0` freigegeben.

> [!CAUTION]
> Vor jedem Test: bekannte funktionierende SD sichern, Original-Firmware und
> Stock-Bootlog lesen, 3,3-V-TTL-UART anschließen und die eMMC unangetastet
> lassen. Eine instabile 5-V-Versorgung kann wie ein DRAM- oder Bootfehler
> aussehen.

| Stufe | Ziel | Erfolg | Bei Fehler |
| --- | --- | --- | --- |
| 0 | Originalzustand sichern | Fotos, PCB-Aufdruck, Stock-Log vorhanden | nicht flashen |
| 1 | Hardware inventarisieren | SoC, RAM, PMIC, UART, Speicher, PHY bekannt | [Inventur](HARDWARE_IDENTIFICATION.md) |
| 2 | UART prüfen | Stock-Ausgabe bei 115200/8N1 | [UART](UART_BRINGUP.md) |
| 3 | FEL erkennen | H616 per USB sichtbar | [FEL](FEL_BRINGUP.md) |
| 4 | eGON bauen | `eGON.BT0`, keine Medienoperation | [DRAM/PMIC](DRAM_PMIC.md) |
| 5 | RAM-Test auswerten | plausible DRAM-Größe | nur DRAM/PMIC ändern |
| 6 | optional TOC0-SD-Test | nur mit lokalem Schlüssel | Secure Boot dokumentieren |
| 7 | Kernel und DTB | Kernel erreicht Rootfs | [DTB](DTB_PORTING.md) |
| 8 | Netzwerk und Dienste | PHY, DHCP, SSH | erst danach Samba |

## Öffentliche Buildkette

```bash
bash build/setup-h616-porting-host.sh --check
bash build/fetch-h616-porting-sources.sh
bash build/build-h616-fel-egon.sh
```

Der Standardweg erzeugt ausschließlich Hostdateien unter `build/work/` und
`build/artifacts/`. Er öffnet keine SD, keine eMMC und führt keine FEL-USB-
Befehle aus. Das T95-Profil ist ein Referenzprofil, kein Beweis für fremde
Hardware.

Ein TOC0-SD-Kandidat ist bewusst getrennt und verlangt einen lokalen Schlüssel:

```bash
bash build/build-h616-toc0-test.sh --key /absoluter/pfad/test-root-key.pem
```

Das Ergebnis kann durch Secure Boot abgelehnt werden. Es wird kein Schlüssel
generiert, veröffentlicht oder in das Repository kopiert.

Weitere Referenzen: [UART](UART_BRINGUP.md), [FEL](FEL_BRINGUP.md),
[DRAM/PMIC](DRAM_PMIC.md), [DTB](DTB_PORTING.md),
[Troubleshooting](BOOT_TROUBLESHOOTING.md) und
[bereinigte Logs](reference-logs/README.md).
