<a id="uart-bring-up"></a>

# 🔌 UART-Bring-up

**Deutsch** | [English](UART_BRINGUP.en.md)

UART ist der erste Diagnosekanal. Verwende 3,3-V-TTL, gemeinsame Masse und
115200 Baud, 8N1 ohne Flow-Control. Ein RP2040-Zero kann mit dem
[separaten UART-Adapterprojekt](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter)
verwendet werden.

| Prüfpunkt | Vorgabe |
| --- | --- |
| 🔌 Verbindung | 3,3-V-TTL, gemeinsame Masse; zuerst nur Box TX → Adapter RX und GND |
| ⚙️ Terminal | 115200 Baud, 8N1, keine Flusssteuerung |
| 🖥️ Aufnahme | Auf dem Linux-PC im separaten UART-Adapterprojekt |
| ✅ Erfolg | Lesbare Ausgabe beim Start; bei fehlender Ausgabe zuerst Verdrahtung und Pegel prüfen |

<a id="sicher-anschließen-und-aufnehmen"></a>

## 🔌 Sicher anschließen und aufnehmen

1. Box stromlos machen und GND bestimmen.
2. Nur `Box-TX → Adapter-RX` und `GND → GND` verbinden.
3. Aufnahme starten, dann Box einschalten.
4. `Box-RX → Adapter-TX` erst bei Bedarf und eindeutigem Bootzustand ergänzen.

Der Capture-Code gehört zum UART-Adapterprojekt, nicht zu diesem Repository.
Nach dessen Clone beispielsweise:

```bash
python3 tools/capture_uart.py /dev/ttyACM0 --baud 115200 --prefix captures/stock-boot
```

Der Gerätename ist nur ein Beispiel. Logs vor Veröffentlichung von IPs, MACs,
Seriennummern, UUIDs und Zugangsdaten bereinigen.
