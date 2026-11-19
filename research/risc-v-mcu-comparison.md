# MCU comparison for the PoE → USB-C adapter

Researched 2026-10-21/22. Prices and stock were read live from LCSC product pages
(JLCPCB assembly uses the same C-numbers and LCSC stock). Baseline: RP2040
at **$0.786 @100**. Anything dearer than that is marked **Over RP2040** (ruled out).
Non-RISC-V parts are included where the price is competitive.

Google Sheet (same data, with per-column notes):
https://docs.google.com/spreadsheets/d/1nPsWa2ZrP8suhqZF9iXVH5w3_iRSPm5tRze83cas7SA/edit#gid=0

## TL;DR

* **CH32X035 is the pick for USB + PD** ($0.31 @100, QFN-28 or QFN-20, both in stock).
  It is the only cheap, in-stock part with a **hardware USB-PD PHY**, and it also has
  crystal-less USB FS, a 5 V supply, op-amps/comparators for PoE sensing, and TIM1
  complementary PWM with dead time for an MCU-driven buck. It needs no external
  support parts. Prefer the **G8U6 (QFN-28)**: same price, 27 GPIO, and it has a
  comparator (the datasheet lists none on the QFN-20 F8U6). Its network path is the
  USB host relay: the Pi speaks LLDP on Ethernet for it.
* **Network means Ethernet or Wi-Fi.** Bluetooth alone doesn't count (it's a bonus
  if it comes free), so the BLE-only WCH parts (CH572D, CH592F, CH582F) are marked
  "No network".
* **BK7238 is the only network-capable part under the RP2040.** Beken BK7238QH321:
  RISC-V, Wi-Fi 4 + BLE 5.2, 2 MB flash in package, $0.67 @100. It has no USB, so it
  pairs with a CH32X035 over UART/SPI (~$0.98 together). Caveat: only 514 in stock.
* **Every Espressif part is over the RP2040 or out of stock.** ESP32-C3 is $1.29 and
  needs external flash, a crystal and RF matching. ESP8684 (~$0.84) and ESP8266EX
  ($0.99) are out of stock at LCSC; BL602 likewise (~$1.04). Espressif USB is a
  fixed Serial/JTAG function: it enumerates as a serial port, which is enough for the
  adapter-as-device host relay, but it can't present other USB classes.
* **No Ethernet route comes in under the RP2040.** The cheapest built-in MDI PHY is
  the CH579M (Cortex-M0, 10BASE-T) at $1.21, then the CH32V208WBU6 (RISC-V, 10M) at
  $1.42. The CH390H SPI 10/100 chip is $0.94 on its own (~$1.25 with a CH32X035).
  Only the CH32V307 exposes a MAC (RGMII/RMII) for an external PHY or switch port;
  nothing here offers SGMII. An Ethernet port of the adapter's own only makes sense in
  the switch design, since the passthrough has no spare port.
* **USB high speed**: the cheapest is CH585M (~$0.91 qty-1 price), then CH32V305
  ($1.27). Not needed for this adapter; FS is plenty. USB host mode isn't needed
  either, so it isn't tracked.
* **No MCU here has PoE PD hardware.** PoE signature, classification and UVLO stay
  discrete (or a TMI7303B-class PD IC), using the MCU's ADC/comparators.
* **"In-built power supplies"**: the parts that run directly from 5 V (CH32V003,
  CH32X033/X035, CH572D) save the 3.3 V regulator. The on-chip DC-DCs (RP2350,
  CH58x/CH59x) only power the chip itself; none can run the 57 V input buck. For
  driving an external buck, look at the "Adv PWM" column (complementary outputs +
  dead time).

## Table

Columns: Flash/SRAM KB = on-chip memory (None for flash = needs external flash); USB = speed of the on-chip controller; Gen = general-purpose USB (any device
class; Espressif's fixed Serial/JTAG port is No); PD = hardware USB-PD PHY; MDI PHY =
built-in Ethernet PHY driving the magnetics directly; MAC if. = how an Ethernet MAC is
exposed (RGMII/RMII to an external PHY, internal PHY only, or an SPI chip driven by a
host MCU); 5 V = runs directly from 5 V; DC-DC = on-chip switching regulator for the
chip itself; Xtal = needs an external crystal; Adv PWM = complementary PWM with dead
time; Price tier = the LCSC quantity break the @100 price comes from; vs RP2040 = the @1k price minus the RP2040's;
Cores = number of CPU cores; Alt core = a second, different core on the same chip; Second MAC if. = a further
way the MAC is exposed; Ext flash = needs an external flash chip. ? = not confirmed; None = absent.

| Part | Vendor | LCSC | Datasheet | Pkg | $ @100 | Price tier | $ @1k | Stock | vs RP2040 | Core | Cores | Alt core | Flash KB | SRAM KB | USB | Gen | PD | MDI PHY | MAC if. | Second MAC if. | Wi-Fi | BLE | 5 V | DC-DC | Xtal | Ext flash | Adv PWM | ADC | CMP | OPA | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RP2040 | Raspberry Pi | [C2040](https://www.lcsc.com/product-detail/C2040.html) | [PDF](https://www.lcsc.com/datasheet/C2040.pdf) | QFN-56 | $0.786 | 100+ | $0.730 | 41,863 | $0.000 | Cortex-M0+ | 2 | – | None | 264 | FS | Yes | No | None | None | – | None | No | No | No | Yes | Yes | No | 4 | 0 | 0 | Baseline |
| RP2350A | Raspberry Pi | [C42411118](https://www.lcsc.com/product-detail/C42411118.html) | [PDF](https://www.lcsc.com/datasheet/C42411118.pdf) | QFN-60 | $1.135 | 100+ | $1.099 | 6,069 | +$0.349 | Hazard3 RV32 | 2 | Cortex-M33 | None | 520 | FS | Yes | No | None | None | – | None | No | No | Yes | Yes | Yes | No | 4 | 0 | 0 | Baseline |
| RP2354A | Raspberry Pi | [C41378174](https://www.lcsc.com/product-detail/C41378174.html) | [PDF](https://www.lcsc.com/datasheet/C41378174.pdf) | QFN-60 | $1.215 | 100+ | $1.202 | 11,029 | +$0.429 | Hazard3 RV32 | 2 | Cortex-M33 | 2048 | 520 | FS | Yes | No | None | None | – | None | No | No | Yes | Yes | No | No | 4 | 0 | 0 | Baseline |
| CH570Q | WCH | [C49260680](https://www.lcsc.com/product-detail/C49260680.html) | [PDF](https://www.lcsc.com/datasheet/C49260680.pdf) | DFN-10 | $0.233 | 50+ | $0.172 | 7,740 | -$0.553 | QingKe V3C | 1 | – | 240 | 12 | FS | Yes | No | None | None | – | None | No | No | No | Yes | No | No | 0 | 1 | 0 | Helper |
| CH32V003F4P6 | WCH | [C5187096](https://www.lcsc.com/product-detail/C5187096.html) | [PDF](https://www.lcsc.com/datasheet/C5187096.pdf) | TSSOP-20 | $0.244 | 50+ | $0.177 | 23,845 | -$0.542 | QingKe V2A | 1 | – | 16 | 2 | None | No | No | None | None | – | None | No | Yes | No | No | No | Yes | 8 | 0 | 1 | Helper |
| CH572D | WCH | [C46597863](https://www.lcsc.com/product-detail/C46597863.html) | [PDF](https://www.lcsc.com/datasheet/C46597863.pdf) | QFN-20 | $0.253 | 100+ | $0.217 | 230 | -$0.533 | QingKe V3C | 1 | – | 240 | 12 | FS | Yes | No | None | None | – | None | Yes | Yes | No | Yes | No | No | 0 | 1 | 0 | No network |
| CH32X033F8P6 | WCH | [C19268290](https://www.lcsc.com/product-detail/C19268290.html) | [PDF](https://www.lcsc.com/datasheet/C19268290.pdf) | TSSOP-20 | $0.267 | 72+ | $0.243 | 1,144 | -$0.519 | QingKe V4C | 1 | – | 62 | 20 | FS | Yes | No | None | None | – | None | No | Yes | No | No | No | Yes | 10 | 2 | 2 | Candidate |
| CH32X035G8U6 | WCH | [C7437027](https://www.lcsc.com/product-detail/C7437027.html) | [PDF](https://www.lcsc.com/datasheet/C7437027.pdf) | QFN-28 | $0.312 | 100+ | $0.268 | 9,702 | -$0.474 | QingKe V4C | 1 | – | 62 | 20 | FS | Yes | Yes | None | None | – | None | No | Yes | No | No | No | Yes | 10 | 1 | 2 | Pick |
| CH32X035F8U6 | WCH | [C42442062](https://www.lcsc.com/product-detail/C42442062.html) | [PDF](https://www.lcsc.com/datasheet/C42442062.pdf) | QFN-20 | $0.316 | 100+ | $0.272 | 2,854 | -$0.470 | QingKe V4C | 1 | – | 62 | 20 | FS | Yes | Yes | None | None | – | None | No | Yes | No | No | No | Yes | 10 | ? | 2 | Pick |
| CH32L103K8U6 | WCH | [C22472334](https://www.lcsc.com/product-detail/C22472334.html) | [PDF](https://www.lcsc.com/datasheet/C22472334.pdf) | QFN-32 | $0.383 | 100+ | ? | 0 | -$0.403 | QingKe V4C | 1 | – | 64 | 20 | FS | Yes | Yes | None | None | – | None | No | No | No | No | No | Yes | ? | ? | ? | Unavailable |
| CH32V203F6P6 | WCH | [C3040880](https://www.lcsc.com/product-detail/C3040880.html) | [PDF](https://www.lcsc.com/datasheet/C3040880.pdf) | TSSOP-20 | $0.395 | 72+ | $0.357 | 1,276 | -$0.391 | QingKe V4B | 1 | – | 32 | 10 | FS | Yes | No | None | None | – | None | No | No | No | Yes | No | Yes | ? | 0 | ? | Candidate |
| CH32V203G6U6 | WCH | [C5142280](https://www.lcsc.com/product-detail/C5142280.html) | [PDF](https://www.lcsc.com/datasheet/C5142280.pdf) | QFN-28 | $0.452 | 100+ | $0.393 | 4,736 | -$0.334 | QingKe V4B | 1 | – | 32 | 10 | FS | Yes | No | None | None | – | None | No | No | No | Yes | No | Yes | ? | 0 | ? | Candidate |
| CH592F | WCH | [C39831287](https://www.lcsc.com/product-detail/C39831287.html) | [PDF](https://www.lcsc.com/datasheet/C39831287.pdf) | QFN-28 | $0.523 | 100+ | $0.448 | 17,806 | -$0.263 | QingKe V4C | 1 | – | 448 | 26 | FS | Yes | No | None | None | – | None | Yes | No | Yes | Yes | No | No | ? | ? | ? | No network |
| CH584F | WCH | [C42381468](https://www.lcsc.com/product-detail/C42381468.html) | [PDF](https://www.lcsc.com/datasheet/C42381468.pdf) | QFN-32 | $0.651 | 100+ | $0.557 | 0 | -$0.135 | QingKe V3C | 1 | – | 448 | ? | FS | Yes | No | None | None | – | None | Yes | No | No | Yes | No | No | ? | ? | ? | Unavailable |
| BK7238QH321 | Beken | [C53282000](https://www.lcsc.com/product-detail/C53282000.html) | [PDF](https://www.lcsc.com/datasheet/C53282000.pdf) | QFN-32 | $0.670 | 100+ | $0.601 | 514 | -$0.116 | RISC-V (Beken) | 1 | – | 2048 | 288 | None | No | No | None | None | – | Wi-Fi 4 | Yes | No | No | Yes | No | No | 6 | ? | ? | Pick |
| CH582F | WCH | [C3001175](https://www.lcsc.com/product-detail/C3001175.html) | [PDF](https://www.lcsc.com/datasheet/C3001175.pdf) | QFN-28 | $0.752 | 100+ | $0.679 | 1,439 | -$0.034 | QingKe V4A | 1 | – | 448 | 32 | FS | Yes | No | None | None | – | None | Yes | No | Yes | Yes | No | No | ? | ? | ? | No network |
| CH585M | WCH | [C42381469](https://www.lcsc.com/product-detail/C42381469.html) | [PDF](https://www.lcsc.com/datasheet/C42381469.pdf) | QFN-48 | $0.905 | 1+ | ? | 162 | +$0.119 | QingKe V3C | 1 | – | 448 | 128 | HS | Yes | No | None | None | – | None | Yes | No | No | Yes | No | No | ? | ? | ? | Over RP2040 |
| CH390H | WCH | [C7498452](https://www.lcsc.com/product-detail/C7498452.html) | [PDF](https://www.lcsc.com/datasheet/C7498452.pdf) | QFN-32 | $0.943 | 100+ | $0.848 | 2,501 | +$0.157 | None (SPI Ethernet chip) | – | – | None | None | None | No | No | 100M | SPI (host) | – | None | No | No | No | No | No | No | ? | ? | ? | Over RP2040 |
| ESP8266EX | Espressif | [C77967](https://www.lcsc.com/product-detail/C77967.html) | [PDF](https://www.lcsc.com/datasheet/C77967.pdf) | QFN-32 | $0.991 | 100+ | $0.872 | 0 | +$0.205 | Xtensa L106 | 1 | – | None | 160 | None | No | No | None | None | – | Wi-Fi 4 | No | No | No | Yes | Yes | No | 1 | 0 | 0 | Unavailable |
| CH32V208GBU6 | WCH | [C7434833](https://www.lcsc.com/product-detail/C7434833.html) | [PDF](https://www.lcsc.com/datasheet/C7434833.pdf) | QFN-28 | $0.994 | 100+ | $0.892 | 1,332 | +$0.208 | QingKe V4C | 1 | – | 128 | 64 | FS | Yes | No | None | None | – | None | Yes | No | No | Yes | No | Yes | ? | ? | ? | Over RP2040 |
| CH579M | WCH | [C481976](https://www.lcsc.com/product-detail/C481976.html) | [PDF](https://www.lcsc.com/datasheet/C481976.pdf) | QFN-48 | $1.210 | 100+ | $1.087 | 155 | +$0.424 | Cortex-M0 | 1 | – | 250 | 32 | FS | Yes | No | 10M | Int. PHY only | – | None | Yes | No | No | Yes | No | No | 14 | ? | ? | Over RP2040 |
| CH32V305FBP6 | WCH | [C5123443](https://www.lcsc.com/product-detail/C5123443.html) | [PDF](https://www.lcsc.com/datasheet/C5123443.pdf) | TSSOP-20 | $1.266 | 72+ | $1.181 | 1,613 | +$0.480 | QingKe V4F | 1 | – | 128 | 32 | HS | Yes | No | None | None | – | None | No | No | No | Yes | No | Yes | ? | ? | ? | Over RP2040 |
| ESP32-C3 | Espressif | [C2838500](https://www.lcsc.com/product-detail/C2838500.html) | [PDF](https://www.lcsc.com/datasheet/C2838500.pdf) | QFN-32 | $1.285 | 100+ | $1.190 | 2,527 | +$0.499 | RV32IMC | 1 | – | None | 400 | FS | No | No | None | None | – | Wi-Fi 4 | Yes | No | No | Yes | Yes | No | 6 | 0 | 0 | Over RP2040 |
| CH32V208WBU6 | WCH | [C5187528](https://www.lcsc.com/product-detail/C5187528.html) | [PDF](https://www.lcsc.com/datasheet/C5187528.pdf) | QFN-68 | $1.416 | 30+ | $1.163 | 279 | +$0.630 | QingKe V4C | 1 | – | 128 | 64 | FS | Yes | No | 10M | Int. PHY only | – | None | Yes | No | No | Yes | No | Yes | ? | ? | ? | Over RP2040 |
| ESP32-C3FH4 | Espressif | [C2858491](https://www.lcsc.com/product-detail/C2858491.html) | [PDF](https://www.lcsc.com/datasheet/C2858491.pdf) | QFN-32 | $1.513 | 100+ | $1.396 | 4,132 | +$0.727 | RV32IMC | 1 | – | 4096 | 400 | FS | No | No | None | None | – | Wi-Fi 4 | Yes | No | No | Yes | No | No | 6 | 0 | 0 | Over RP2040 |
| ESP32-H2FH4 | Espressif | [C22470214](https://www.lcsc.com/product-detail/C22470214.html) | [PDF](https://www.lcsc.com/datasheet/C22470214.pdf) | QFN-32 | $1.821 | 100+ | $1.691 | 2,622 | +$1.035 | RV32IMAC | 1 | – | 4096 | 320 | FS | No | No | None | None | – | None | Yes | No | No | Yes | No | Yes | 5 | 0 | 0 | Over RP2040 |
| CH32V317WCU6 | WCH | [C49188393](https://www.lcsc.com/product-detail/C49188393.html) | [PDF](https://www.lcsc.com/datasheet/C49188393.pdf) | QFN-68 | $2.231 | 30+ | $1.809 | 302 | +$1.445 | QingKe V4F | 1 | – | 256 | 64 | HS | Yes | No | 100M | ? | – | None | No | No | No | Yes | No | Yes | ? | ? | ? | Over RP2040 |
| GD32VF103RBT6 | GigaDevice | [C717613](https://www.lcsc.com/product-detail/C717613.html) | [PDF](https://www.lcsc.com/datasheet/C717613.pdf) | LQFP-64 | $2.533 | 10+ | ? | 0 | +$1.747 | Bumblebee N205 | 1 | – | 128 | 32 | FS | Yes | No | None | None | – | None | No | No | No | Yes | No | Yes | 16 | 0 | 0 | Unavailable |
| ESP32-C6FH4 | Espressif | [C6908287](https://www.lcsc.com/product-detail/C6908287.html) | [PDF](https://www.lcsc.com/datasheet/C6908287.pdf) | QFN-32 | $2.600 | 200+ | $2.472 | 0 | +$1.814 | RV32IMAC | 1 | – | 4096 | 512 | FS | No | No | None | None | – | Wi-Fi 6 | Yes | No | No | Yes | No | Yes | 7 | 0 | 0 | Over RP2040 |
| CH32V307RCT6 | WCH | [C2988083](https://www.lcsc.com/product-detail/C2988083.html) | [PDF](https://www.lcsc.com/datasheet/C2988083.pdf) | LQFP-64 | $2.700 | 30+ | $2.149 | 148 | +$1.914 | QingKe V4F | 1 | – | 256 | 64 | HS | Yes | No | 10M | RGMII | RMII | None | No | No | No | Yes | No | Yes | ? | ? | ? | Over RP2040 |
| ESP32-C5-WROOM-1 | Espressif | [C42441836](https://www.lcsc.com/product-detail/C42441836.html) | [PDF](https://www.lcsc.com/datasheet/C42441836.pdf) | Module | $5.698 | 200+ | $5.415 | 0 | +$4.912 | RV32IMAC | 1 | – | ? | 384 | FS | No | No | None | None | – | Wi-Fi 6 | Yes | No | No | No | No | Yes | ? | 0 | 0 | Over RP2040 |
| ESP8684H2 | Espressif | [C2922574](https://www.lcsc.com/product-detail/C2922574.html) | [PDF](https://www.lcsc.com/datasheet/C2922574.pdf) | QFN-24 | ? | ? | $0.837 | 0 | ? | RV32IMC | 1 | – | 2048 | 272 | None | No | No | None | None | – | Wi-Fi 4 | Yes | No | No | Yes | No | No | ? | 0 | 0 | Unavailable |
| BL602C-20-Q2I | Bouffalo Lab | [C2874058](https://www.lcsc.com/product-detail/C2874058.html) | [PDF](https://www.lcsc.com/datasheet/C2874058.pdf) | QFN-32 | ? | ? | $1.041 | 0 | ? | RISC-V (SiFive E24) | 1 | – | 2048 | 276 | None | No | No | None | None | – | Wi-Fi 4 | Yes | No | No | Yes | No | No | ? | ? | ? | Unavailable |

## Why the Pick, Candidate and Helper verdicts

* **CH32X035G8U6 (Pick, USB + PD)**: the only cheap, in-stock part with hardware USB-PD. No crystal or 3.3 V regulator, built-in analog for PoE sensing, dead-time PWM for the buck. Preferred over the F8U6: same price, plus a comparator and more GPIO.
* **CH32X035F8U6 (Pick, USB + PD)**: same chip in a smaller QFN-20, with no comparator listed and fewer GPIO. Use it if board space matters more.
* **BK7238QH321 (Pick, Wi-Fi)**: the only Wi-Fi part under the RP2040 price, with flash in package. Pairs with a CH32X035 over UART/SPI for about $0.98. Risk: only 514 in stock.
* **CH32X033F8P6 (Candidate)**: cheapest part with crystal-less USB and a 5 V supply, but no PD PHY. The CH32X035 adds hardware PD for about $0.05 more.
* **CH32V203F6P6 / G6U6 (Candidate)**: the current BOM's family, so firmware carries over, but no PD PHY and a crystal is needed, so they lose to the CH32X035.
* **CH570Q (Helper)**: too few pins and no ADC or BLE to be the main MCU; could be a low-power cold-start or watchdog helper.
* **CH32V003F4P6 (Helper)**: no USB, but at $0.24 with a 5 V supply and dead-time PWM it suits a PoE cold-start helper or an MCU-run buck controller.

## Per-part notes

* **RP2040**: Arm only, not RISC-V. Internal 1.1 V core LDO. PIO can bit-bang USB-PD BMC and RMII. Ext parts: QSPI flash, 12 MHz crystal + 2 caps + 1 k, 2× 27 Ω USB.
* **RP2350A**: Two Hazard3 RISC-V cores (or two Cortex-M33). The DC-DC is an on-chip switching regulator for the 1.1 V core only (needs an external 3.3 µH inductor); it cannot run the output buck.
* **RP2354A**: RP2350A with 2 MB flash stacked in the package, so no external flash.
* **CH570Q**: Only 5 GPIO and no ADC (one comparator with a 16-step reference). 5 V input range is specified for the QFN20 'D' parts; unclear for Q. CH570 has the 2.4 GHz radio but no BLE. Needs a 32 MHz crystal.
* **CH32V003F4P6**: No USB hardware. Low-speed USB can be bit-banged (rv003usb), but USB-PD BMC would also be bit-banged. Good as a PoE cold-start helper (low current, 5 V tolerant supply, TIM1 complementary PWM with dead time).
* **CH572D**: Cheapest part here with both USB FS (host + device) and BLE 5.0. No ADC: PoE voltage/class sensing would need the comparator plus its 16-step reference. Only 230 in stock at LCSC today. Needs 32 MHz crystal and antenna matching. Bluetooth only, so no Ethernet/Wi-Fi network on its own.
* **CH32X033F8P6**: Same die family as CH32X035 but no USB-PD/Type-C block (no CC pins). Crystal-less USB.
* **CH32X035G8U6**: Hardware USB-PD PHY (BMC + CRC), Rp current sources, crystal-less USB, 5 V supply, op-amps and comparator for PoE sensing, TIM1 complementary PWM with dead time for an MCU-driven buck. 27 GPIO. Network: via the USB host relay (the Pi speaks for it on Ethernet), or pair with a BK7238 for Wi-Fi (~$0.98 together @100).
* **CH32X035F8U6**: The part [`cost-reduction.md`](cost-reduction.md) chose. 19 GPIO. The datasheet ordering table lists no comparator for this package (the QFN28 has 1, LQFP48 has 3); check before relying on comparator-based current limit. Network: as CH32X035G8U6.
* **CH32L103K8U6**: USB FS device + USB-PD PHY, low-power. Out of stock at LCSC today (reference price only). 3.3 V supply; whether USB runs crystal-less is not confirmed.
* **CH32V203F6P6**: Current BOM's MCU family. No PD PHY (PD must be bit-banged). USB normally uses an 8 MHz crystal.
* **CH32V203G6U6**: As CH32V203F6P6 in QFN-28.
* **CH592F**: BLE 5.4 + USB FS, internal DC-DC (needs an inductor), 32 MHz crystal. Good stock. Cheapest well-stocked BLE option. Bluetooth only, so no Ethernet/Wi-Fi network on its own.
* **CH584F**: BLE 5.4 + NFC. Out of stock at LCSC (reference price). The CH585 is the high-speed-USB sibling.
* **BK7238QH321**: Cheapest network-capable part found, and under the RP2040: Wi-Fi 4 + BLE 5.2, 2 MB flash in package, 160 MHz RISC-V core (per SoCXin). Needs a 26 MHz crystal, RF matching and antenna; 2.7–3.6 V. No USB, so it would talk to the CH32X035 over UART/SPI. Open firmware exists (OpenBeken supports BK7238). LCSC also shows a 5 % discounted price ($0.637 @100). Only 514 in stock.
* **CH582F**: BLE 5.3, two USB FS controllers, internal DC-DC. Bluetooth only, so no Ethernet/Wi-Fi network on its own.
* **CH585M**: Cheapest RISC-V part with USB 2.0 high speed (plus BLE 5.4 + NFC). LCSC only lists a qty-1 price; 162 in stock.
* **CH390H**: Not an MCU: SPI 10/100 Ethernet MAC + PHY to pair with an MCU. CH32X035 + CH390H is about $1.25 @100, above the RP2040. An Ethernet port of the adapter's own only makes sense in the switch design, since the passthrough has no spare port.
* **ESP8266EX**: Not RISC-V. Out of stock at LCSC (reference price). Needs external flash, crystal and RF matching.
* **CH32V208GBU6**: BLE 5.3 + USB FS. The QFN-28 package has no Ethernet PHY (use WBU6).
* **CH579M**: Not RISC-V. Cheapest MCU found with a built-in Ethernet PHY (10BASE-T), plus BLE 4.2 and USB FS, but still above the RP2040. The QFN-28 CH579F has no Ethernet.
* **CH32V305FBP6**: USB 2.0 high speed with built-in PHY plus a USB FS OTG port.
* **ESP32-C3**: USB is a fixed-function Serial/JTAG device: it shows up as a serial port (enough for the adapter-as-device host relay) but can't present other classes. Needs external flash, 40 MHz crystal, RF matching and an antenna.
* **CH32V208WBU6**: Cheapest RISC-V MCU with a built-in Ethernet PHY (10BASE-T) plus BLE 5.3 and USB FS. 10BASE-T needs its own magnetics and cannot join the gigabit passthrough without a switch.
* **ESP32-C3FH4**: ESP32-C3 with 4 MB flash in package.
* **ESP32-H2FH4**: No Wi-Fi: BLE 5 + 802.15.4 only. Marked 'not recommended for new designs' at LCSC. USB Serial/JTAG only.
* **CH32V317WCU6**: Built-in 10/100 Ethernet PHY and USB HS + FS.
* **GD32VF103RBT6**: USB FS OTG. Out of stock at LCSC (reference price).
* **ESP32-C6FH4**: Wi-Fi 6 + BLE 5 + 802.15.4. Out of stock at LCSC (reference price, lowest tier 200). USB Serial/JTAG only.
* **CH32V307RCT6**: Built-in 10M PHY plus a gigabit MAC (RGMII). The switch design in [`ethernet-switch.md`](ethernet-switch.md) uses this part.
* **ESP32-C5-WROOM-1**: Dual-band Wi-Fi 6. LCSC has the module only, no bare chip; out of stock (reference price).
* **ESP8684H2**: ESP32-C2 with 2 MB flash in package. No USB at all. Out of stock at LCSC; $0.8365 is LCSC's 'from' price, tier not shown.
* **BL602C-20-Q2I**: Out of stock at LCSC; $1.041 is LCSC's 'from' price, tier not shown. Open-source SDK and community support exist.

## Not included

* **Bouffalo BL616/BL618** (Wi-Fi 6 + BLE + USB HS OTG + Ethernet MAC): only appears
  at JLCPCB as a consigned part with no price or stock, so it can't be ordered for
  JLC assembly in the normal way.
* **ESP32-C61, ESP32-P4**: no LCSC listing found. P4 has no radio and is far above the
  RP2040 price anyway.
* **W800/W801** (Winner Micro Wi-Fi): LCSC pages wouldn't load, so no price here.
* **CH641** (RISC-V, USB-PD PHY, 5–12 V supply): looks interesting for running
  straight off the 12 V rail, but its LCSC page wouldn't load so it has no price here.
  Worth a manual check.
* **CH32V002/004/005/006, CH570D**: newer CH32V003-class or CH57x parts; no LCSC price
  could be read. They lack USB-PD hardware.

## Method and caveats

* "@100" is the LCSC price break that applies to an order of 100. Where LCSC has no
  100+ break, the break below it applies (e.g. 72+ or 50+). Out-of-stock parts show
  LCSC's reference price.
* Feature flags come from datasheets, LCSC listings and the other notes in this folder.
  Where a feature was not confirmed it's marked ?, not guessed.
* The "Ext" count in the sheet is a rough estimate of support parts beyond
  decoupling and a 3.3 V regulator.
