# Dev boards and off-the-shelf hardware for the RTL8367S and YT9215S

Companion to [`switch-embedded-cpu.md`](switch-embedded-cpu.md) (what the embedded CPUs are) and [`switch-detail-comparison.md`](switch-detail-comparison.md). This note answers: what can we buy to experiment with the RTL8367S DW8051 and the YT9215 RISC-V core, and how easy is it to reach the chip's pins on each?

<a id="evidence-codes"></a>
Evidence codes:

- **V**: read in a cited source.
- **I**: inference.

Prices are indicative from listings and deal sites seen on 2026-10-22, not quotes. Retail switches change chips between hardware versions, so **always check the hardware version (Vx.y) on the label** before buying.

Spreadsheet copy: the *Dev boards* tab of the [comparison sheet](https://docs.google.com/spreadsheets/d/1nPsWa2ZrP8suhqZF9iXVH5w3_iRSPm5tRze83cas7SA/edit#gid=3), with search links per store.

## TL;DR

- **Neither vendor sells a public evaluation board.** I found no Realtek RTL8367S EVB or Motorcomm YT9215 EVB listed at any distributor, AliExpress, eBay or Amazon. Both exist only through distributors under NDA. [**V**](#evidence-codes) (absence in searches)
- **RTL8367S: the cheapest and best dev platform is a A$15–30 unmanaged 5-port TP-Link switch.**
  - TP-Link TL-SG105 **V6**, LS1005G **V1** and TL-SG1005D **rev 7** use the RTL8367S with only a 24Cxx EEPROM next to it. [**V**](#evidence-codes)
  - Pull the EEPROM and its footprint gives you the chip's SMI bus (SDA and SCK), 3.3 V and GND. McMCCRU drove a TL-SG1005D rev 7 from an Arduino Nano and an STM32 Blue Pill this way. [**V**](#evidence-codes)
  - From there an RP2040 can load 8051 code into the IROM window over SMI, exactly as the GPL `rtl8367c` driver does. UART (pins 45 and 46) and the SPI-flash pins would need fine-pitch wires to the LQFP. [**I**](#evidence-codes)
  - For a cleaner board with a real CPU link, the routers MERCUSYS MR85X (MT7981B, RTL8367S over 2500base-X) and TP-Link Archer C5 v4 (MT7620A) run OpenWrt with the switch already on DSA and swconfig. [**V**](#evidence-codes)
  - Open-hardware designs to copy or order from JLCPCB: AlbrechtL's `rpi-managed-switch-4-port` (GPL-3.0, KiCad) and the PCBWay "RTL8367S-4GE+SFP" project. [**V**](#evidence-codes)
- **YT9215: much thinner.**
  - Motorcomm's product page lists the embedded RISC-V CPU and "simple network management" **only for the YT9215SC**. The YT9215S and YT9215RB entries don't mention a CPU. [**V**](#evidence-codes)
  - The YT9215S draft datasheet on LCSC says "Integrated RISC-V microprocessor" and has a `STRAP_DIS_MCU` pin, so the core is probably on the die but not supported on the S. [**VI**](#evidence-codes) For CPU work, buy the **YT9215SC**.
  - The only retail products I could confirm are the Xiaomi CR881x routers (IPQ5018 + YT9215S over SGMII or 2500base-X) and the BDY-G98 (彼度云 G98) RK3588 box (two YT9215S over RGMII). [**V**](#evidence-codes) Both are mostly sold in China.
  - The practical dev board is to **build our own**: one LQFP-128 chip (YT9215S about US$1.92 at LCSC), plus the open-hardware 5-port YT9215S switch on OSHWHub as a reference layout. [**VI**](#evidence-codes)
- **Recommendation:** buy two or three TP-Link TL-SG105 V6 and LS1005G V1 units now for RTL8367S 8051 experiments, and treat any YT9215 work as "spin our own breakout with a YT9215SC" if it is ever needed.

## 1. Official evaluation boards

| Chip | Official EVB | Official EVB evidence | Who can get it | Evidence | Public availability | Public availability evidence |
| --- | --- | --- | --- | --- | --- | --- |
| RTL8367S-CG | Reference designs and EVBs | [**V**](#evidence-codes) | Partners only | Leaked programming guide | None found | [**V**](#evidence-codes) |
| YT9215S | None mentioned | [**V**](#evidence-codes) | – | Motorcomm product page | None found | [**V**](#evidence-codes) |
| YT9215SC | None mentioned | [**V**](#evidence-codes) | – | Motorcomm product page | None found | [**V**](#evidence-codes) |
| YT9215RB | None mentioned | [**V**](#evidence-codes) | – | Motorcomm product page | None found | [**V**](#evidence-codes) |

| Leaked Realtek document | Rev | Year | Marking | Audience |
|---|---|---|---|---|
| "Realtek Unmanaged Switch Programming Guide" | 1.3.11 | 2017 | Confidential | Development partners |

| Shop searched | RTL8367S EVB found |
|---|---|
| Mouser | No |
| Digi-Key | No |
| LCSC | No |
| AliExpress | No |
| eBay | No |
| Amazon | No |

Schematic + PCB + BOM packs for RTL8367S designs circulate on Chinese forums (e.g. [bbs.16rd.com thread 585232](https://bbs.16rd.com/thread-585232-1-1.html)). They are useful as reference layouts but are of unclear provenance and licence.

## 2. RTL8367S options

### 2a. Cheap unmanaged switches (best 8051 dev platform)

All of these are "dumb" switches where the RTL8367S boots from a small EEPROM with no host CPU. That is exactly the configuration where we could load our own 8051 code over SMI.

| Product | Case | Ports | Series | HW version with RTL8367S | Evidence | Config storage | EEPROM size |
|---|---|---|---|---|---|---|---|
| **TP-Link TL-SG105** | Metal | 5 | – | **V6.0** | [Gough Lui teardown](https://goughlui.com/2022/02/27/unbox-teardown-tp-link-tl-sg105-5-port-gigabit-desktop-ethernet-switch/) | Serial EEPROM | – |
| **TP-Link LS1005G** | Plastic | – | LiteWave | **V1** | [TechInfoDepot](https://techinfodepot.shoutwiki.com/wiki/TP-LINK_LS1005G_V1) | 24C02 EEPROM | 2 Kbit |
| **TP-Link TL-SG1005D** | Plastic | – | – | **rev 7** | [McMCCRU](https://github.com/McMCCRU/Arduino_RTL8367C) | 24Cxx EEPROM | – |

Board-level access:

| Product | Flash | Header | EEPROM location | Case room | Opening | Other chips | Step 1 | Step 2 |
|---|---|---|---|---|---|---|---|---|
| TL-SG105 V6.0 | None | None | Next to the chip | Roomy | Easy | – | – | – |
| LS1005G V1 | None | – | – | – | – | None | – | – |
| TL-SG1005D rev 7 | – | – | [EEPROM socket pins](#eeprom-socket-pins) | – | – | – | Remove the EEPROM | Drive SMI from an MCU |

<a id="eeprom-socket-pins"></a>TL-SG1005D rev 7 EEPROM socket pins:

| EEPROM pin | Signal |
|---|---|
| 1–4 | GND |
| 5 | SDA |
| 6 | SCK |
| 8 | 3.3 V |

Indicative prices and where to buy:

| Product | Shop | Kind | Low | High | Currency | Source | Note |
|---|---|---|---|---|---|---|---|
| TL-SG105 | **amazon.com.au** | New | 20 | 29 | A$ | – | Gough Lui paid about A$20 |
| TL-SG105 | AU retailers | New | 27 | 35 | A$ | [PriceMe](https://www.priceme.com.au/TP-Link-TL-SG105/p-888455411.aspx) | – |
| TL-SG105 | **eBay** | New | 20 | 30 | A$ | [ebay.com.au TL-SG105 listings](https://www.ebay.com.au/sch/i.html?_nkw=TP-Link+TL-SG105+v6) | Often |
| TL-SG105 | **eBay** | Used | – | – | A$ | Same listings | Less than new |
| TL-SG105 | **AliExpress** | Available | – | – | – | – | Versions unclear |
| LS1005G | **amazon.com.au** | RRP | 24.95 | 24.95 | A$ | – | – |
| LS1005G | **amazon.com.au** | Seen at | 16 | 16 | A$ | [OzBargain](https://ozbargain.com.au/node/738664) | – |
| LS1005G | US Amazon | New | 9 | 12 | US$ | – | Often |
| LS1005G | **eBay** | – | 12 | 20 | A$ | – | Common |
| LS1005G | **AliExpress** | – | 12 | 20 | A$ | – | Common |
| TL-SG1005D | **AliExpress** | – | 15 | 25 | A$ | – | – |
| TL-SG1005D | **eBay** | – | 15 | 25 | A$ | – | – |
| TL-SG1005D | Amazon AU | – | – | – | – | – | Less common |

On Amazon AU the TL-SG105 and the LS1005G have replaced the TL-SG1005D.

How to use one as a dev board: [**I**](#evidence-codes), building on the [**V**](#evidence-codes) items in this section.

1. Desolder the EEPROM and solder a 6-pin header to its pads (SDA, SCK, 3.3 V, GND).
2. Wire an RP2040 (Pico) to SDA and SCK. Port the GPL `rtl8367c` SMI routines, or start from McMCCRU's Arduino sketch.
3. Load test code into the 8051 IROM: assert `DW8051_RST`, enable `ACS_IROM_EN`, write bytes to 0xE000+, release reset (see [`switch-embedded-cpu.md`](switch-embedded-cpu.md) boot flow).
4. For printf debug, tack a wire to the chip's UART TX (pin 46). For flash boot experiments, add a SOIC-8 SPI flash on SPIF pins 48, 49, 53 and 54 and set the EN_SPIF strap.

Variants to avoid: newer hardware versions of these models may move to RTL8367S-VB, RTL8367RB-VB or a different vendor. Older TL-SG1005D v5 uses "RTL8367" (no S, per [shaddack's notes](https://shaddack.mauriceward.com/notes/ethernet.webt)). AliExpress "5-port gigabit switch module" PCBAs are almost all **RTL8367RB** (older RTL8367B family), not the S (e.g. [eBay 135146159571](https://www.ebay.com/itm/135146159571)). [**V**](#evidence-codes)

### 2b. Routers with RTL8367S behind a Linux SoC

Useful if we want the switch on a real CPU port with a working Linux driver to compare against, or to sniff SMI traffic while the vendor driver loads the 8051.

| Product | Class | SoC | RTL8367S link | Evidence | OpenWrt | Status | Market |
|---|---|---|---|---|---|---|---|
| **MERCUSYS MR85X** | AX3000 | MT7981B | 2500base-X fixed link | [OpenWrt commit](https://git.openwrt.org/b2648d89517c05f7b5633e1d79a989c3e5fd011e) | Supported | Current model | – |
| **TP-Link Archer C5 v4** | – | MT7620A | – | [OpenWrt forum](https://forum.openwrt.org/t/reduce-number-of-drivers-for-rtl8367s/237681) | Supported | Old | Cheap |
| **TP-Link EC220-G5 v2** | – | MT7620A-class | – | [**V**](#evidence-codes) | – | ISP-branded | Cheap second-hand |
| **TOTOLINK A8000RU** | – | MT7622 | 2500base-X | [OpenWrt PR #24861](https://github.com/openwrt/openwrt/pull/24861) | Supported | – | – |
| **Buffalo WSR-2533DHP2** | – | MT7622 | 2500base-X | [**V**](#evidence-codes) | – | – | Japan |

| Product | Board detail | Value |
|---|---|---|
| MERCUSYS MR85X | Switch reset | GPIO 39 |
| MERCUSYS MR85X | UART port | UART0 |
| MERCUSYS MR85X | UART baud rate | 115200 |
| MERCUSYS MR85X | UART format | 8N1 |
| TP-Link Archer C5 v4 | Switch driver | Old rtl8367b swconfig driver |

Indicative prices and where to buy:

| Product | Shop | Kind | Low | High | Currency | Source |
|---|---|---|---|---|---|---|
| MERCUSYS MR85X | **AU retail** | New | 123.50 | 123.50 | A$ | [icit.net.au](https://icit.net.au/product/mr85x-mercusys-mr85x-ax3000-dual-band-wi-fi-6-router/) |
| MERCUSYS MR85X | **amazon.com.au** | Listings | 100 | 130 | A$ | – |
| MERCUSYS MR85X | **eBay** | Listings | 100 | 130 | A$ | – |
| MERCUSYS MR85X | **AliExpress** | Occasional listings | – | – | – | – |
| TP-Link Archer C5 v4 | **eBay** | Used | 20 | 40 | A$ | – |
| TP-Link EC220-G5 v2 | **eBay** | Used | – | – | – | – |
| TOTOLINK A8000RU | **AliExpress** | – | 50 | 80 | US$ | – |
| TOTOLINK A8000RU | **eBay** | – | 50 | 80 | US$ | – |
| Buffalo WSR-2533DHP2 | **eBay** | Japanese sellers | – | – | – | – |

Linux support: upstream `rtl8365mb` DSA driver (RGMII; SGMII or HSGMII patches for RTL8367S posted June 2026), plus OpenWrt's `rtl8367b` and `rtk-gsw` drivers. [**V**](#evidence-codes)

### 2c. Open hardware RTL8367S boards

| Project | Switch IC | Controller | Kind |
|---|---|---|---|
| [AlbrechtL/rpi-managed-switch-4-port](https://github.com/AlbrechtL/rpi-managed-switch-4-port) | RTL8367S | Raspberry Pi Zero | Open board |
| [PCBWay: RTL8367S-4GE+SFP Gigabit Optical Switch](https://www.pcbway.com/project/sponsor/RTL8367S_4GE_SFP_Gigabit_Optical_Switch_7f271618.html) | RTL8367S | None | Shared PCBWay project |
| [BrixIT: Making a Linux-managed network switch](https://blog.brixit.nl/making-a-linux-managed-network-switch/) | RTL8367S | PINE64 A64-LTS | Blog write-up |
| [maxx-ukoo/rtl8367-controller](https://github.com/maxx-ukoo/rtl8367-controller) | 2 × RTL8367S | STM32F103 | Retail switch mod |
| [libc0607/Realtek_switch_hacking](https://github.com/libc0607/Realtek_switch_hacking) | RTL8367RB | ESP8266 | Community hub |

| Project | Property | Value | Value evidence |
| --- | --- | --- | --- |
| AlbrechtL | Switch IC | RTL8367S | [**V**](#evidence-codes) |
| AlbrechtL | Host | Raspberry Pi Zero | [**V**](#evidence-codes) |
| AlbrechtL | Host link chip | ENC28J60 | [**V**](#evidence-codes) |
| AlbrechtL | Design files | KiCad | [**V**](#evidence-codes) |
| AlbrechtL | Production | "ready for JLCPCB production" | [**V**](#evidence-codes) |
| AlbrechtL | Licence | GPL-3.0 | [**V**](#evidence-codes) |
| AlbrechtL | Software | OpenWrt fork using `rtl8365mb` DSA | [**V**](#evidence-codes) |
| AlbrechtL | Cost (author's estimate) | About US$54/unit for 2-unit PCBA | [**V**](#evidence-codes) |
| AlbrechtL | Pi link speed | Only about 5 Mbit/s over SPI |  |
| AlbrechtL | 8051 broken out | No |  |
| AlbrechtL | UART broken out | No |  |
| AlbrechtL | Flash broken out | No |  |
| AlbrechtL | Use to us | Good layout reference |  |
| PCBWay | GE ports | 4 | [**V**](#evidence-codes) |
| PCBWay | SFP ports | 1 | [**V**](#evidence-codes) |
| PCBWay | SFP link | SGMII | [**V**](#evidence-codes) |
| PCBWay | Power input | USB 5 V | [**V**](#evidence-codes) |
| PCBWay | Buck converter | MT2492 | [**V**](#evidence-codes) |
| PCBWay | Core rail | On-chip 1.1 V DC-DC | [**V**](#evidence-codes) |
| PCBWay | Licence | None stated |  |
| PCBWay | Firmware | Realtek config `.bin` |  |
| PCBWay | Firmware terms | "non-commercial use only" |  |
| PCBWay | How to get | Order through PCBWay |  |
| BrixIT | Author | Martijn Braam |  |
| BrixIT | Control link | GPIO SMI from the PINE64 A64-LTS | [**V**](#evidence-codes) |
| BrixIT | Straps | Solder jumpers | [**V**](#evidence-codes) |
| BrixIT | SPI flash | Optional footprint | [**V**](#evidence-codes) |
| BrixIT | Repo | None linked |  |
| BrixIT | Useful notes 1 | Straps |  |
| BrixIT | Useful notes 2 | The minimal config |  |
| maxx-ukoo | Target | ZX900-AFG-82N PoE switch | [**V**](#evidence-codes) |
| maxx-ukoo | Switch ICs | 2 × RTL8367S over RGMII | [**V**](#evidence-codes) |
| maxx-ukoo | PoE controller in target | TMI7608S |  |
| libc0607 | Contents 1 | Docs | [**V**](#evidence-codes) |
| libc0607 | Contents 2 | ESP8266 SMI tools | [**V**](#evidence-codes) |
| libc0607 | Contents 3 | Yakigani RTL8370 IROM programmer | [**V**](#evidence-codes) |
| libc0607 | Open board switch IC | RTL8367RB | [**V**](#evidence-codes) |
| libc0607 | Open board MCU | ESP8266 | [**V**](#evidence-codes) |

Longer entries for this table:

- **PCBWay, Use to us**: Closest to our use-case (SerDes port in use)
- **maxx-ukoo, What it does**: Replaces the MCU with an STM32F103 over SMI.
- **maxx-ukoo, Use to us**: A retail PoE switch close to our topology.
- **libc0607, Use to us**: Best community hub for Realtek 8051 work.

## 3. YT9215 options

### 3a. Which part has the CPU

| Part | GE ports | SerDes ports | SerDes SGMII | SerDes 2.5G | RGMII ports | CPU on Motorcomm product page | CPU on Motorcomm product page evidence | CPU in LCSC draft datasheet | CPU in LCSC draft datasheet evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YT9215S | 5 | 1 | Yes | – | 1 | No | [**V**](#evidence-codes) | Yes | [**V**](#evidence-codes) |
| YT9215SC | 5 | 2 | Yes | Yes | – | Yes | [**V**](#evidence-codes) | Yes | [**V**](#evidence-codes) |
| YT9215RB | 5 | – | – | – | 2 | No | [**V**](#evidence-codes) | n/a |  |
| YT9218N | 8 | – | – | – | – | Yes | [**V**](#evidence-codes) | n/a |  |
| YT9218MB | 8 | – | – | – | – | Yes | [**V**](#evidence-codes) | n/a |  |

| Part | Source | What it says |
|---|---|---|
| YT9215S | [Product page](https://www.motor-comm.com/product/switching-chip) | No CPU listed |
| YT9215S | [Draft datasheet](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308291451_Motorcomm-YT9215S_C5899183.pdf) | "Integrated RISC-V microprocessor" |
| YT9215S | Draft datasheet | 2 JTAG groups |
| YT9215S | Draft datasheet | UART0–2 |
| YT9215S | Draft datasheet | SPI flash |
| YT9215S | Draft datasheet | `STRAP_DIS_MCU` on pin [75](motorcomm-debug-pins.md#s-pin-75) |
| YT9215SC | Product page | "内置高性能RISC-V 核心CPU" |
| YT9215SC | Product page | "支持简单网管" |
| YT9215SC | Draft datasheet | Same pin functions as the YT9215S |
| YT9215RB | Product page | No CPU |
| YT9218N | Product page | RISC-V CPU |
| YT9218N | Product page | Simple management |
| YT9218MB | Product page | RISC-V CPU |
| YT9218MB | Product page | Simple management |

So on retail YT9215S boards the core is probably present but unsupported and likely strapped off. [**I**](#evidence-codes) Plan any CPU work on the **YT9215SC**.

### 3b. Retail products with YT9215

| Product | Chinese name | Host SoC | Switch | Count | Link | Alternative link | MDIO addr | Linux support |
|---|---|---|---|---|---|---|---|---|
| **Xiaomi CR881x** | – | IPQ5018 | YT9215S | 1 | SGMII | 2500base-X | 0x1d | OpenWrt fork |
| **BDY-G98** | 彼度云 G98 | RK3588 | YT9215S | 2 | `rgmii-txid` | – | 0x1d | DSA `yt921x` |
| Unnamed industrial boards | – | RK3568 | YT9215 | – | MAC-to-MAC | – | n/a | n/a |
| Unnamed industrial boards | – | RK3588 | YT9215 | – | MAC-to-MAC | – | n/a | n/a |

| Product | Property | Value | Evidence |
| --- | --- | --- | --- |
| Xiaomi CR881x | Model 1 | CR8816 |  |
| Xiaomi CR881x | Model 2 | CR8818 |  |
| Xiaomi CR881x | More models | Yes |  |
| Xiaomi CR881x | Type | China carrier AX3000 mesh units |  |
| Xiaomi CR881x | Board | M79 |  |
| Xiaomi CR881x | Switch CPU port | Port 8 | [**V**](#evidence-codes) |
| Xiaomi CR881x | Switch reset | GPIO 35 | [**V**](#evidence-codes) |
| Xiaomi CR881x | Evidence 1 | [OpenWrt forum](https://forum.openwrt.org/t/ipq5018-yt9215s-and-1000base-x-2500base-x/241325) |  |
| Xiaomi CR881x | Evidence 2 | [hzyitc issue #150](https://github.com/hzyitc/openwrt-redmi-ax3000/issues/150) |  |
| Xiaomi CR881x | UART | J1 (VCC-RX-GND-TX) |  |
| Xiaomi CR881x | OpenWrt | [hzyitc/openwrt-redmi-ax3000](https://github.com/hzyitc/openwrt-redmi-ax3000) |  |
| Xiaomi CR881x | Where sold | Mostly second-hand in China (Xianyu) |  |
| Xiaomi CR881x | **AliExpress** | Occasional listings |  |
| Xiaomi CR881x | **eBay** | Occasional listings |  |
| Xiaomi CR881x | Typical price | US$25–50 |  |
| Xiaomi CR881x | Check before buying | The model must be **CR881x** |  |
| Xiaomi CR881x | Not confirmed YT9215 | CR8806 | [**I**](#evidence-codes) |
| Xiaomi CR881x | Not confirmed YT9215 | CR8808 | [**I**](#evidence-codes) |
| Xiaomi CR881x | Not confirmed YT9215 | CR8809 | [**I**](#evidence-codes) |
| Xiaomi CR881x | Not confirmed YT9215 | Redmi AX3000 | [**I**](#evidence-codes) |
| BDY-G98 | Type 1 | NAS |  |
| BDY-G98 | Type 2 | Router |  |
| BDY-G98 | LAN ports | 8 |  |
| BDY-G98 | Switch attach | Each YT9215S on an RK3588 GMAC | [**V**](#evidence-codes) |
| BDY-G98 | Evidence | [GitHub issue](https://github.com/yifengyou/BDY_G98_RK3588/issues/6) |  |
| BDY-G98 | Known issue | Cross-chip forwarding lock-up bug reported | [**V**](#evidence-codes) |
| BDY-G98 | Where sold | China-market box |  |
| BDY-G98 | Amazon AU | Not found in this search |  |
| BDY-G98 | eBay | Not found in this search |  |
| BDY-G98 | AliExpress | Not found in this search |  |
| Unnamed boards | Evidence | Several CSDN write-ups ([CSDN](https://blog.csdn.net/xuesong10210/article/details/135957672)) |  |
| Unnamed boards | Product names | Not given |  |

Longer entries for this table:

- **Xiaomi CR881x, Known issue**: Switch probe still flaky on some boards.

I found **no cheap unmanaged retail switch** confirmed to use a YT9215. Motorcomm targets "dumb switch" use, so some Chinese-brand 5-port switches likely use it, but none were identified in teardowns. [**I**](#evidence-codes)

### 3c. Open hardware and self-build

- **OSHWHub "基于裕太微YT9215S的五口千兆交换机" v2.0** by pankanwen ([oshwhub.com](https://oshwhub.com/pankanwen/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0)) is an open 5-port gigabit switch on the YT9215S. It can be ordered through JLCPCB. I could not read the page (robots block), so I don't know whether JTAG or UART are broken out. The board's existence is [**V**](#evidence-codes); the rest is [**I**](#evidence-codes).
- **Chip cost:** YT9215S about US$1.92 at LCSC (C5899183, 57 in stock). The YT9215SC is LCSC C51037433. [**V**](#evidence-codes)
- **Our own breakout** (recommended if we ever pursue the RISC-V core): YT9215SC + SPI flash socket + both JTAG groups on a 2.54 mm header + UART0 + strap jumpers (`STRAP_DIS_MCU`, `STRAP_EN_SPIF`, `STRAP_SMI_SEL`) + one RJ45 + SGMII to an SFP cage. [**I**](#evidence-codes)

## 4. Purchase quick-links

Search links (results change daily; check hardware version in the listing photos):

- amazon.com.au: [TP-Link TL-SG105](https://www.amazon.com.au/s?k=TP-Link+TL-SG105), [TP-Link LS1005G](https://www.amazon.com.au/s?k=TP-Link+LS1005G), [Mercusys MR85X](https://www.amazon.com.au/s?k=Mercusys+MR85X)
- eBay: [TL-SG105 V6](https://www.ebay.com.au/sch/i.html?_nkw=TP-Link+TL-SG105+v6), [LS1005G](https://www.ebay.com.au/sch/i.html?_nkw=TP-Link+LS1005G), [TL-SG1005D](https://www.ebay.com.au/sch/i.html?_nkw=TL-SG1005D), [Archer C5 v4](https://www.ebay.com.au/sch/i.html?_nkw=Archer+C5+v4), [TOTOLINK A8000RU](https://www.ebay.com/sch/i.html?_nkw=TOTOLINK+A8000RU), [Xiaomi CR8818](https://www.ebay.com/sch/i.html?_nkw=Xiaomi+CR8818)
- AliExpress: [RTL8367S chips](https://www.aliexpress.com/w/wholesale-rtl8367s.html) (US$1–3 each, bare chips only, no boards), [TL-SG1005D](https://www.aliexpress.com/w/wholesale-TL-SG1005D.html), [TOTOLINK A8000RU](https://www.aliexpress.com/w/wholesale-A8000RU.html), [Xiaomi CR881x](https://www.aliexpress.com/w/wholesale-xiaomi-CR8818.html)
- LCSC: [YT9215S C5899183](https://www.lcsc.com/product-detail/Ethernet-ICs_Motorcomm-YT9215S_C5899183.html), RTL8367S-CG C2760849

Note: the prices in this file come from search snippets and deal pages, not from opening live Amazon, eBay or AliExpress product pages (those block automated fetches).

## Open questions

- Which current TL-SG105 and LS1005G hardware versions are still RTL8367S? The V6 and V1 data points are from 2022.
- Does the CR881x's YT9215S have its MCU strapped off (pin [75](motorcomm-debug-pins.md#s-pin-75))? A photo of the board around the switch would answer it.
- Contents of the OSHWHub YT9215S design (JTAG or UART breakout).
