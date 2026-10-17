<a id="uart-bring-up"></a>

# 🔌 UART bring-up

[Deutsch](UART_BRINGUP.md) | **English**

UART is the first diagnostic channel. Use 3.3 V TTL, a common ground, and
115200 baud, 8N1, without flow control. An RP2040-Zero can be used with the
[separate UART adapter project](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter).

| Check | Setting |
| --- | --- |
| 🔌 Connection | 3.3 V TTL, common ground; initially only box TX → adapter RX and GND |
| ⚙️ Terminal | 115200 baud, 8N1, no flow control |
| 🖥️ Capture | On the Linux PC, in the separate UART adapter project |
| ✅ Success | Readable boot output; if absent, check wiring and voltage level first |

<a id="connect-and-capture-safely"></a>

## 🔌 Connect and capture safely

1. Disconnect power from the box and identify GND.
2. Connect only `Box TX → adapter RX` and `GND → GND`.
3. Start recording, then power on the box.
4. Add `Box RX → adapter TX` only when needed and after the boot state is clear.

The capture program belongs to the UART adapter project, not this repository.
After cloning that project, for example:

```bash
python3 tools/capture_uart.py /dev/ttyACM0 --baud 115200 --prefix captures/stock-boot
```

The device name is only an example. Before publishing logs, remove IP and MAC
addresses, serial numbers, UUIDs, and credentials.
