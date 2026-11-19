# The adapter as a USB network card (CDC-ECM, NCM or RNDIS)

Presenting as a USB network card is an interesting idea, and
10 Mbit/s is fully acceptable. Price cap: RP2040,
$0.786 @100. Prices are LCSC prices; unmarked ones come from
[`risc-v-mcu-comparison.md`](risc-v-mcu-comparison.md). <a id="evidence-codes"></a>Evidence code **live**: the price or stock figure was read from the LCSC product page on 2026-10-22. Related:
[`bitbang-usb.md`](bitbang-usb.md) (why it has to be hardware USB),
[`bitbang-10mbit-ethernet.md`](bitbang-10mbit-ethernet.md) and
[`ethernet-switch.md`](ethernet-switch.md).

## TL;DR

"USB network card" can mean two different things, and both are cheap.

1. **A virtual NIC whose far end is the adapter's own MCU** (no Ethernet
   hardware). The host sees an interface named `usb0` or "USB Ethernet", gets an address
   from the MCU's DHCP server, and talks to the adapter over IP: a status web
   page, a REST or MQTT endpoint, firmware upload. **$0 extra** on the current
   CH32X035 (TinyUSB supports it; NCM or ECM class drivers are in TinyUSB).
   It replaces the HID or serial host relay with something standard and
   driverless. RAM is the constraint (20 KB), so use a small IP stack.
2. **A real USB NIC that bridges an RJ45 to USB**, so a USB-C-only device
   (phone, tablet, laptop, Pi Zero-class board) gets both power and wired
   network from one PoE cable.
   * **Best part: WCH CH397A, $0.672 @100 and $0.596 @1k [**live**](#evidence-codes), 10.5k in
     stock.** One chip: USB 2.0 **high speed** device + 10/100 MAC + PHY, built-in
     config flash, driverless CDC-ECM by default with NCM or RNDIS listed. Needs a
     25 MHz crystal and magnetics. Under the RP2040 cap and gives 100 Mbit/s,
     not just 10.
   * In the **switch SKU** it is firmware only: the MCU already sits on the
     switch's extension MAC port, so it can bridge that port to its USB device
     as an NCM NIC. With an RP2040 (the RMII recommendation in
     [`bitbang-10mbit-ethernet.md`](bitbang-10mbit-ethernet.md)) that is USB FS, about 5–9 Mbit/s.
3. **The catch is USB data roles, not silicon.** The adapter is the Type-C
   power source, so by default it is the USB *host* and the powered device is
   the USB *device*. To be a NIC, the adapter must be the USB device. That needs
   a PD `DR_Swap` from the CH32X035 after the power contract (how USB-C docks
   work), or a host that is configured as host on that port (Pi:
   `dtoverlay=dwc2,dr_mode=host`). This is firmware on the PD side, but it has
   to be tested with each class of device.
4. **The passthrough SKU can't also be a bridging NIC.** Gigabit uses all
   four pairs ([`gigabit-piggyback.md`](gigabit-piggyback.md)), so there is no second link for a NIC
   chip. Option 1 works on it; option 2 needs either the switch or a separate
   "USB NIC" SKU where the RJ45 ends at the CH397A instead of passing through.

## 1. Two meanings of "USB network card"

| | Virtual NIC to the MCU | Bridging NIC (RJ45 ⇄ USB) |
|---|---|---|
| What the host gets | A point-to-point link to the adapter | A real LAN interface |
| Addressing | e.g. 192.168.7.0/30 | DHCP from the network |
| Use 1 | Status page | Network for a USB-C-only device |
| Use 2 | Config | – |
| Use 3 | Telemetry | – |
| Use 4 | Firmware update | – |
| Use 5 | PoE PD info | – |
| Ethernet silicon, option 1 | None | NIC chip |
| Ethernet silicon, option 2 | – | MCU MAC with a switch port |
| Works on the passthrough SKU | Yes | No (no free pair) |
| SKU needed, option 1 | Any | Switch SKU |
| SKU needed, option 2 | – | NIC-only SKU |
| Extra cost on the switch SKU | $0 | $0 (firmware only) |
| Extra cost with a NIC chip | – | ~$0.75 |
| NIC chip parts | – | CH397A with a crystal |

## 2. Host OS support for the USB classes

| Class | Linux | Linux driver | macOS | Windows 11 | Windows 10 | Android |
|---|---|---|---|---|---|---|
| CDC-ECM | in-box | `cdc_ether` | in-box | **no in-box driver** | **no in-box driver** | usually (kernel config) |
| CDC-NCM | in-box | `cdc_ncm` | in-box in recent versions (verify) | in-box | lacks it | usually |
| RNDIS | in-box but disliked | – | needs third-party driver | in-box | in-box | usually |

| Class | Trait | Packet size | Framing | Used by | Reference |
|---|---|---|---|---|---|
| CDC-ECM | Simplest | 64-byte packets | One frame per transfer | – | – |
| CDC-NCM | Best for throughput | – | Batches frames | pico-usb-wifi | [pico-usb-wifi] |
| CDC-NCM | Missing from Windows 10 | – | – | Reported by postmarketOS | [pmOS] |
| RNDIS | Fallback for older Windows only | – | – | – | – |
| RNDIS | Linux removal proposed | – | – | – | [RNDIS removal] |

Practical choice: **NCM, with RNDIS as an optional second configuration** if
Windows 10 matters. TinyUSB's `net_lwip_webserver` example builds ECM, RNDIS or
NCM and includes a tiny DHCP server.

## 3. Throughput at USB full speed

USB FS bulk tops out at 19 × 64-byte packets per 1 ms frame ≈ 9.7 Mbit/s in
theory; real MCU stacks get less. The one recent measured number for an RP2040
NCM bridge is **4.75 Mbit/s average** (Pico W USB-to-Wi-Fi bridge, "mostly
limited by the 12 Mbps USB 1.1 interface") ([pico-usb-wifi]). So a USB FS NIC
lands at **roughly 5–9 Mbit/s**, which meets the 10 Mbit/s requirement. A
high-speed part (CH397A, CH32V307) removes USB as the bottleneck.

Low-speed (bit-banged) USB cannot do this at all: no bulk endpoints, and Linux
rejects low-speed network devices ([`bitbang-usb.md` section 3](bitbang-usb.md#3-low-speed-limits-that-matter-here)).

## 4. Parts that can do it

### 4.1 Virtual NIC (MCU only)

| Part | $ @100 | USB | Flash | SRAM | USB stack | IP stack | Status |
|---|---|---|---|---|---|---|---|
| **CH32X035G8U6** (current pick) | $0.312 | FS device | 62 KB | 20 KB | TinyUSB ([TinyUSB]) | – | – |
| RP2040 | $0.786 | FS device | ext. QSPI | 264 KB | TinyUSB | lwIP | Known to work |

| Part | Property | Value |
|---|---|---|
| CH32X035G8U6 | TinyUSB MCU option | `OPT_MCU_CH32X035` |
| CH32X035G8U6 | TinyUSB driver | USBFS |
| CH32X035G8U6 | Endpoint buffers | 64-byte (fine for FS) |
| CH32X035G8U6 | lwIP with TCP in flash | Fits |
| CH32X035G8U6 | lwIP with TCP in 20 KB RAM | Tight |
| CH32X035G8U6 | Safer choice 1 | A UDP-only stack |
| CH32X035G8U6 | Safer choice 2 | uIP-style HTTP |
| CH32X035G8U6 | Confidence | **Estimate** |
| CH32X035G8U6 | Next step | **A build to confirm** |
| RP2040 | RAM | Plenty |
| RP2040 | Price | Dearer |
| RP2040 | Extra part 1 | Flash |
| RP2040 | Extra part 2 | Crystal |

### 4.2 Bridging NIC

| Option | MCU | Ethernet chip | Package | LCSC | USB | USB rate | Ethernet | Auto-MDIX | Terminations | Firmware |
|---|---|---|---|---|---|---|---|---|---|---|
| **CH397A** | – | CH397A | QFN-24 4×4 | [C7465328] | **HS** | 480 Mbit/s | 10/100 MAC + PHY | Yes | 50 Ω built in | None (fixed-function) |
| Switch SKU with RP2040 | RP2040 | RTL8363NB ext port | – | – | FS | – | PIO RMII via the switch | – | – | TinyUSB NCM + L2 bridge |
| Switch SKU with CH32V307 | CH32V307 | Switch | – | – | **HS** | – | MAC → switch | – | – | NCM + bridge |
| CH32X035 with CH390H | CH32X035 | CH390H (SPI MAC+PHY) | – | – | FS | – | 10/100 | – | – | MCU bridges SPI ⇄ USB |
| RP2040 with PIO 10BASE-T | RP2040 | None (direct on the wire) | – | – | FS | – | Bit-banged 10M | – | – | Two experimental stacks combined |
| CH579M | CH579M | Built-in 10M PHY | – | – | FS | – | 10BASE-T | – | – | MCU bridge |
| CH32V208WBU6 | CH32V208WBU6 | Built-in 10M PHY | – | – | FS | – | 10BASE-T | – | – | MCU bridge |

| Option | Silicon $ @100 | Silicon $ @1k | Silicon $ @1k evidence | Extra part 1 | Extra part 2 | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **CH397A** | **$0.672** | **$0.596** | [**live**](#evidence-codes) | 25 MHz crystal | – | **Best standalone NIC** |
| Switch SKU with RP2040 | $0 extra | $0 extra |  | – | – | Good |
| Switch SKU with CH32V307 | $0 extra | $0 extra |  | – | – | Fastest switch-SKU option |
| CH32X035 with CH390H | $1.25 | – |  | – | – | Over cap |
| RP2040 with PIO 10BASE-T | $0.79 | – |  | Flash | Crystal | Not worth it |
| CH579M | $1.21 | – |  | – | – | Over cap |
| CH32V208WBU6 | $1.42 | – |  | – | – | Over cap |

Notes on the rows of this table:

- **CH397A**, reason: Cheapest.
- **CH397A**, second reason: Fastest.
- **CH397A**, third reason: No firmware.
- **Switch SKU with RP2040**, reason: Same board serves an Ethernet Pi.
- **Switch SKU with RP2040**, second reason: It also serves a USB-only device.
- **Switch SKU with CH32V307**, reason: Already in that BOM at $2.15 @1k.
- **Switch SKU with CH32V307**, second reason: The RP2040 swap saves ~$0.40.
- **CH32X035 with CH390H**, reason: Slower than the CH397A.
- **CH32X035 with CH390H**, second reason: More work than the CH397A.
- **RP2040 with PIO 10BASE-T**, reason: 5–7 Mbit/s TCP.
- **RP2040 with PIO 10BASE-T**, second reason: "not recommended for PoE equipment".

| Part of the CH32X035 with CH390H option | $ [**live**](#evidence-codes) |
|---|---|
| CH32X035 | $0.31 |
| CH390H | $0.94 |
| Total | $1.25 |

| CH397A built-in flash holds |
|---|
| Config |
| MAC |
| VID |
| PID |

The "not recommended" quote is pico_eth_doc's own ([pico_eth_doc]). The CH32V307 in the switch SKU is the MCU chosen in [`ethernet-switch.md`](ethernet-switch.md). Prices at 1k for the other MCUs are in [`risc-v-mcu-comparison.md`](risc-v-mcu-comparison.md).

**USB-NIC SKU sketch (no passthrough):** PoE RJ45 + magnetics → CH397A → USB-C
D+ and D−; the CH32X035 does PoE, the buck and USB-PD. Extra BOM over the
passthrough SKU: CH397A $0.60 + crystal ~$0.03 + 10/100 magnetics (the
passthrough already needs a PoE magjack; the 10/100 version is usually cheaper
than gigabit). CH397A draws 42–80 mA in 10BASE-T and ~70–75 mA at 100M
(datasheet), about 0.25–0.4 W, which fits even a Class 3 budget.

One wrinkle: with the CH397A on D+ and D−, the CH32X035 is not on USB, so
the adapter's own telemetry needs either a USB 2.0 hub chip (e.g. WCH CH334 or
CH335, not priced here) or the CH397A alone (power info then only via PD).

## 5. Data roles: the part that needs testing

| Device on the USB-C end | Default role when the adapter powers it | What makes the adapter a USB device | Alternative | Support | Tested |
|---|---|---|---|---|---|
| Raspberry Pi 4 | Pi is device (dwc2 gadget) | `dtoverlay=dwc2,dr_mode=host` on the Pi | PD `DR_Swap` | – | – |
| Raspberry Pi 5 | Pi is device (dwc2 gadget) | `dtoverlay=dwc2,dr_mode=host` on the Pi | PD `DR_Swap` | – | – |
| Laptop | Laptop is device (Type-C default when sinking) | PD `DR_Swap` | – | Most laptops accept | – |
| Android phone | Device | PD `DR_Swap` | – | Generally supported | No |
| Android tablet | Device | PD `DR_Swap` | – | Generally supported | No |
| iPad (iPadOS) | Device | PD `DR_Swap` | – | USB Ethernet as host | No |
| Pi Zero | Device (micro-USB OTG) | Needs an OTG-host adapter cable | – | Out of scope | – |
| Other micro-USB boards | Device (micro-USB OTG) | Needs an OTG-host adapter cable | – | Out of scope | – |

A `DR_Swap` towards a laptop is what docks do.

The CH32X035's hardware PD PHY handles the BMC; the `DR_Swap` message and the
Type-C state machine are firmware. Without a successful swap, both ends try to
be devices and nothing enumerates, but power is unaffected.

## 6. Recommendation

* **Passthrough SKU:** add the virtual NIC to the CH32X035 firmware as the
  standard host relay (NCM + small DHCP + HTTP and JSON). $0 BOM. Keep HID as a
  fallback if RAM proves too tight. Prototype on a CH32X035 board first to
  measure RAM.
* **Switch SKU:** expose the MCU's switch port as an NCM NIC (bridge). Same
  board then serves both Ethernet-capable and USB-only devices. $0 BOM.
* **If a "PoE → USB-C power + network" SKU for USB-only devices is wanted:**
  CH397A, ~$0.65 extra, 100 Mbit/s, no NIC firmware to write. Gigabit is not
  possible on this SKU (USB 2.0 tops out below it anyway).

## Sources

* [C7465328] CH397A at LCSC (price and stock read 2026-10-22): https://www.lcsc.com/product-detail/C7465328.html
* CH397 datasheet (USB HS or FS, 10/100 PHY, ECM default, NCM or RNDIS, 25 MHz crystal, currents): https://atta.szlcsc.com/upload/public/pdf/source/20240813/7579B736A93AD62F1FA2079FDA525BA1.pdf
* CH390H at LCSC: https://www.lcsc.com/product-detail/C7498452.html
* [pico-usb-wifi] CNX Software, 2026-07-16 (NCM, L2 bridge, 4.75 Mbit/s): https://www.cnx-software.com/2026/07/16/pico-usb-wifi-converts-the-raspberry-pi-pico-w-into-a-driverless-usb-wifi-adapter/ ; code https://gitlab.com/baiyibai/pico-usb-wifi
* [pmOS] postmarketOS switch to NCM (Windows 10 lacks NCM): https://postmarketos.org/edge/2023/10/29/rndis-ncm
* [RNDIS removal] https://forum.beagleboard.org/t/linux-dropping-support-for-rndis/35849
* ECM vs EEM vs NCM notes: https://fobnail.3mdeb.com/eth-over-usb-research/
* [TinyUSB] [`src/tusb_option.h`](https://github.com/hathach/tinyusb/blob/0.18.0/src/tusb_option.h) (OPT_MCU_CH32X035) and [`src/portable/wch/dcd_ch32_usbfs.c`](https://github.com/hathach/tinyusb/blob/0.18.0/src/portable/wch/dcd_ch32_usbfs.c): https://github.com/hathach/tinyusb
* [pico_eth_doc] RP2040 PIO 10BASE-T + lwIP: https://github.com/holysnippet/pico_eth_doc
* CH335F hub (JLCPCB C5137013): https://jlcpcb.com/partdetail/CH335F/C5137013

[C7465328]: https://www.lcsc.com/product-detail/C7465328.html
[pico-usb-wifi]: https://www.cnx-software.com/2026/07/16/pico-usb-wifi-converts-the-raspberry-pi-pico-w-into-a-driverless-usb-wifi-adapter/
[pmOS]: https://postmarketos.org/edge/2023/10/29/rndis-ncm
[RNDIS removal]: https://forum.beagleboard.org/t/linux-dropping-support-for-rndis/35849
[TinyUSB]: https://github.com/hathach/tinyusb/blob/0.18.0/src/tusb_option.h
[pico_eth_doc]: https://github.com/holysnippet/pico_eth_doc
