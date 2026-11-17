# The adapter as a USB network card (CDC-ECM / NCM / RNDIS)

Researched 2026-10-22 for Tim ("being able to present as a USB network card is
an interesting idea"; 10 Mbit/s is fully acceptable). Price cap: RP2040,
$0.786 @100. Prices are LCSC, read live where marked **[live]**; others come from
[`risc-v-mcu-comparison.md`](risc-v-mcu-comparison.md). Related:
[`bitbang-usb.md`](bitbang-usb.md) (why it has to be hardware USB),
[`bitbang-10mbit-ethernet.md`](bitbang-10mbit-ethernet.md) and
[`ethernet-switch.md`](ethernet-switch.md).

## TL;DR

"USB network card" can mean two different things, and both are cheap.

1. **A virtual NIC whose far end is the adapter's own MCU** (no Ethernet
   hardware). The host sees a `usb0`/"USB Ethernet" interface, gets an address
   from the MCU's DHCP server, and talks to the adapter over IP: a status web
   page, a REST/MQTT endpoint, firmware upload. **$0 extra** on the current
   CH32X035 (TinyUSB supports it; NCM/ECM class drivers are in TinyUSB).
   It replaces the HID/serial host relay with something standard and
   driverless. RAM is the constraint (20 KB), so use a small IP stack.
2. **A real USB NIC that bridges an RJ45 to USB**, so a USB-C-only device
   (phone, tablet, laptop, Pi Zero-class board) gets both power and wired
   network from one PoE cable.
   * **Best part: WCH CH397A, $0.672 @100 / $0.596 @1k [live], 10.5k in
     stock.** One chip: USB 2.0 **high speed** device + 10/100 MAC + PHY, built-in
     config flash, driverless CDC-ECM by default with NCM/RNDIS listed. Needs a
     25 MHz crystal and magnetics. Under the RP2040 cap and gives 100 Mbit/s,
     not just 10.
   * In the **switch SKU** it is firmware only: the MCU already sits on the
     switch's extension MAC port, so it can bridge that port to its USB device
     as an NCM NIC. With an RP2040 (the RMII recommendation in
     `bitbang-10mbit-ethernet.md`) that is USB FS, about 5–9 Mbit/s.
3. **The catch is USB data roles, not silicon.** The adapter is the Type-C
   power source, so by default it is the USB *host* and the powered device is
   the USB *device*. To be a NIC, the adapter must be the USB device. That needs
   a PD `DR_Swap` from the CH32X035 after the power contract (how USB-C docks
   work), or a host that is configured as host on that port (Pi:
   `dtoverlay=dwc2,dr_mode=host`). This is firmware on the PD side, but it has
   to be tested with each class of device.
4. **The passthrough SKU can't also be a bridging NIC.** Gigabit uses all
   four pairs (`gigabit-piggyback.md`), so there is no second link for a NIC
   chip. Option 1 works on it; option 2 needs either the switch or a separate
   "USB NIC" SKU where the RJ45 ends at the CH397A instead of passing through.

## 1. Two meanings of "USB network card"

| | Virtual NIC to the MCU | Bridging NIC (RJ45 ⇄ USB) |
|---|---|---|
| What the host gets | A point-to-point link to the adapter (e.g. 192.168.7.0/30) | A real LAN interface with DHCP from the network |
| Use | Status page, config, telemetry, firmware update, PoE/PD info | Network for a USB-C-only device |
| Ethernet silicon | None | NIC chip, or MCU MAC + switch port |
| Works on the passthrough SKU | Yes | No (no free pair; needs switch or a NIC-only SKU) |
| Extra cost | $0 | $0 (switch SKU, firmware) to ~$0.75 (CH397A + crystal) |

## 2. Host OS support for the USB classes

| Class | Linux | macOS | Windows | Android | Notes |
|---|---|---|---|---|---|
| CDC-ECM | in-box (`cdc_ether`) | in-box | **no in-box driver** | usually (kernel config) | Simplest; 64-byte packets, one frame per transfer |
| CDC-NCM | in-box (`cdc_ncm`) | in-box (recent versions; verify) | in-box on Windows 11; Windows 10 lacks it per postmarketOS ([pmOS]) | usually | Batches frames; best for throughput. pico-usb-wifi uses NCM ([pico-usb-wifi]) |
| RNDIS | in-box but disliked; removal proposed ([RNDIS removal]) | needs third-party driver | in-box | usually | Fallback for older Windows only |

Practical choice: **NCM, with RNDIS as an optional second configuration** if
Windows 10 matters. TinyUSB's `net_lwip_webserver` example builds ECM, RNDIS or
NCM and includes a tiny DHCP server.

## 3. Throughput at USB full speed

USB FS bulk tops out at 19 × 64-byte packets per 1 ms frame ≈ 9.7 Mbit/s in
theory; real MCU stacks get less. The one recent measured number for an RP2040
NCM bridge is **4.75 Mbit/s average** (Pico W USB-to-Wi-Fi bridge, "mostly
limited by the 12 Mbps USB 1.1 interface") ([pico-usb-wifi]). So a USB FS NIC
lands at **roughly 5–9 Mbit/s**, which matches Tim's "10 Mbit is fine". A
high-speed part (CH397A, CH32V307) removes USB as the bottleneck.

Low-speed (bit-banged) USB cannot do this at all: no bulk endpoints, and Linux
rejects low-speed network devices ([`bitbang-usb.md`](bitbang-usb.md) §3).

## 4. Parts that can do it

### 4.1 Virtual NIC (MCU only)

| Part | $ @100 | USB | Flash / SRAM | Stack | Notes |
|---|---|---|---|---|---|
| **CH32X035G8U6** (current pick) | $0.312 | FS device | 62 KB / 20 KB | TinyUSB has `OPT_MCU_CH32X035` and a USBFS driver ([TinyUSB]) | 64-byte endpoint buffers (fine for FS). lwIP with TCP fits flash but is tight in 20 KB RAM; a UDP-only stack or uIP-style HTTP is safer. **Estimate, needs a build to confirm** |
| RP2040 | $0.786 | FS device | ext. QSPI / 264 KB | TinyUSB + lwIP, known to work | Plenty of RAM; dearer and needs flash + crystal |

### 4.2 Bridging NIC

| Option | Silicon $ | USB | Ethernet | Firmware | Verdict |
|---|---|---|---|---|---|
| **CH397A** (QFN-24 4×4, LCSC [C7465328]) | **$0.672 @100, $0.596 @1k [live]** + 25 MHz crystal | **HS** 480 Mbit/s | 10/100 MAC + PHY, auto-MDIX, 50 Ω terminations built in | None (fixed-function; config, MAC, VID/PID in built-in flash) | **Best standalone NIC**: cheapest, fastest, no firmware |
| Switch SKU: RP2040 PIO RMII → RTL8363NB ext port, bridged to RP2040 USB | $0 extra | FS | via switch | TinyUSB NCM + L2 bridge in firmware | Good: same board serves an Ethernet Pi *and* a USB-only device |
| Switch SKU: CH32V307 (as in `ethernet-switch.md`) | $0 extra (already in that BOM, $2.15 @1k) | **HS** | RGMII/RMII MAC → switch | WCH/TinyUSB NCM + bridge | Fastest switch-SKU option, but the RP2040 swap saves ~$0.40 |
| CH32X035 + CH390H (SPI MAC+PHY) | $0.31 + $0.94 [live] = $1.25 | FS | 10/100 | MCU bridges SPI ⇄ USB | Over cap, and slower and more work than CH397A |
| RP2040 + PIO 10BASE-T direct on the wire | $0.79 + flash + crystal | FS | bit-banged 10M, 5–7 Mbit/s TCP | Two experimental stacks combined | Not worth it; pico_eth_doc itself says "not recommended for PoE equipment" ([pico_eth_doc]) |
| CH579M / CH32V208WBU6 (USB FS + 10M PHY) | $1.21 / $1.42 | FS | 10BASE-T | MCU bridge | Over cap |

**USB-NIC SKU sketch (no passthrough):** PoE RJ45 + magnetics → CH397A → USB-C
D+/D−; the CH32X035 still does PoE, the buck and USB-PD. Extra BOM over the
passthrough SKU: CH397A $0.60 + crystal ~$0.03 + 10/100 magnetics (the
passthrough already needs a PoE magjack; the 10/100 version is usually cheaper
than gigabit). CH397A draws 42–80 mA in 10BASE-T and ~70–75 mA at 100M
(datasheet), about 0.25–0.4 W, which fits even a Class 3 budget.

One wrinkle: with the CH397A on D+/D−, the CH32X035 is no longer on USB, so
the adapter's own telemetry needs either a USB 2.0 hub chip (e.g. WCH CH334/
CH335, not priced here) or the CH397A alone (power info then only via PD).

## 5. Data roles: the part that needs testing

| Device on the USB-C end | Default role when the adapter powers it | What makes the adapter a USB device |
|---|---|---|
| Raspberry Pi 4/5 | Pi is device (dwc2 gadget) | `dtoverlay=dwc2,dr_mode=host` on the Pi, or PD `DR_Swap` |
| Laptop | Laptop is device by Type-C default when sinking | PD `DR_Swap` (what docks do); most laptops accept |
| Phone / tablet | Device | PD `DR_Swap`; Android generally supports it, iPadOS supports USB Ethernet as host; test |
| Pi Zero / micro-USB boards | Device (micro-USB OTG) | Needs an OTG-host adapter cable; out of scope |

The CH32X035's hardware PD PHY handles the BMC; the `DR_Swap` message and the
Type-C state machine are firmware. Without a successful swap, both ends try to
be devices and nothing enumerates, but power is unaffected.

## 6. Recommendation

* **Passthrough SKU:** add the virtual NIC to the CH32X035 firmware as the
  standard host relay (NCM + small DHCP + HTTP/JSON). $0 BOM. Keep HID as a
  fallback if RAM proves too tight. Prototype on a CH32X035 board first to
  measure RAM.
* **Switch SKU:** expose the MCU's switch port as an NCM NIC (bridge). Same
  board then serves both Ethernet-capable and USB-only devices. $0 BOM.
* **If a "PoE → USB-C power + network" SKU for USB-only devices is wanted:**
  CH397A, ~$0.65 extra, 100 Mbit/s, no NIC firmware to write. Gigabit is not
  possible on this SKU (USB 2.0 tops out below it anyway).

## Sources

* [C7465328] CH397A at LCSC (price/stock read 2026-10-22): https://www.lcsc.com/product-detail/C7465328.html
* CH397 datasheet (USB HS/FS, 10/100 PHY, ECM default, NCM/RNDIS, 25 MHz crystal, currents): https://atta.szlcsc.com/upload/public/pdf/source/20240813/7579B736A93AD62F1FA2079FDA525BA1.pdf
* CH390H at LCSC: https://www.lcsc.com/product-detail/C7498452.html
* [pico-usb-wifi] CNX Software, 2026-07-16 (NCM, L2 bridge, 4.75 Mbit/s): https://www.cnx-software.com/2026/07/16/pico-usb-wifi-converts-the-raspberry-pi-pico-w-into-a-driverless-usb-wifi-adapter/ ; code https://gitlab.com/baiyibai/pico-usb-wifi
* [pmOS] postmarketOS switch to NCM (Windows 10 lacks NCM): https://postmarketos.org/edge/2023/10/29/rndis-ncm
* [RNDIS removal] https://forum.beagleboard.org/t/linux-dropping-support-for-rndis/35849
* ECM vs EEM vs NCM notes: https://fobnail.3mdeb.com/eth-over-usb-research/
* [TinyUSB] `src/tusb_option.h` (OPT_MCU_CH32X035) and `src/portable/wch/dcd_ch32_usbfs.c`: https://github.com/hathach/tinyusb
* [pico_eth_doc] RP2040 PIO 10BASE-T + lwIP: https://github.com/holysnippet/pico_eth_doc
* CH335F hub (JLCPCB C5137013): https://jlcpcb.com/partdetail/CH335F/C5137013
