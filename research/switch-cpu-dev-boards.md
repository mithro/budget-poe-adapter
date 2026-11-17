# Dev boards and off-the-shelf hardware for the RTL8367S and YT9215S

Researched 2026-10-22. Companion to `switch-embedded-cpu.md` (what the embedded CPUs are) and `switch-detail-comparison.md`. This note answers: what can we buy today to experiment with the RTL8367S DW8051 and the YT9215 RISC-V core, and how easy is it to reach the chip's pins on each?

Tags: **[V]** read in a cited source, **[I]** my inference. Prices are indicative from listings and deal sites seen on 2026-10-22, not quotes. Retail switches change chips between hardware versions, so **always check the hardware version (Vx.y) on the label** before buying.

Spreadsheet copy: the *Dev boards* tab of the [comparison sheet](https://docs.google.com/spreadsheets/d/1nPsWa2ZrP8suhqZF9iXVH5w3_iRSPm5tRze83cas7SA/edit#gid=3), with search links per store.

## TL;DR

- **Neither vendor sells a public evaluation board.** I found no Realtek RTL8367S EVB or Motorcomm YT9215 EVB listed at any distributor, AliExpress, eBay or Amazon. Both exist only through distributors under NDA. **[V: absence in searches]**
- **RTL8367S: the cheapest and best dev platform is a A$15–30 unmanaged 5-port TP-Link switch.**
  - TP-Link TL-SG105 **V6**, LS1005G **V1** and TL-SG1005D **rev 7** use the RTL8367S with only a 24Cxx EEPROM next to it. **[V]**
  - Pull the EEPROM and its footprint gives you the chip's SMI bus (SDA/SCK), 3.3 V and GND. McMCCRU drove a TL-SG1005D rev 7 from an Arduino Nano and an STM32 Blue Pill this way. **[V]**
  - From there an RP2040 can load 8051 code into the IROM window over SMI, exactly as the GPL `rtl8367c` driver does. UART (pins 45/46) and the SPI-flash pins would need fine-pitch wires to the LQFP. **[I]**
  - For a cleaner board with a real CPU link, the routers MERCUSYS MR85X (MT7981B, RTL8367S over 2500base-X) and TP-Link Archer C5 v4 (MT7620A) run OpenWrt with the switch already on DSA/swconfig. **[V]**
  - Open-hardware designs to copy or order from JLCPCB: AlbrechtL's `rpi-managed-switch-4-port` (GPL-3.0, KiCad) and the PCBWay "RTL8367S-4GE+SFP" project. **[V]**
- **YT9215: much thinner.**
  - **Correction to `switch-embedded-cpu.md`:** Motorcomm's product page lists the embedded RISC-V CPU and "simple network management" **only for the YT9215SC**. The YT9215S and YT9215RB entries don't mention a CPU. **[V]**
  - The YT9215S draft datasheet on LCSC still says "Integrated RISC-V microprocessor" and has a `STRAP_DIS_MCU` pin, so the core is probably on the die but not supported on the S. **[V]/[I]** For CPU work, buy the **YT9215SC**.
  - The only retail products I could confirm are the Xiaomi CR881x routers (IPQ5018 + YT9215S over SGMII/2500base-X) and the BDY-G98 / 彼度云 G98 RK3588 box (two YT9215S over RGMII). **[V]** Both are mostly sold in China.
  - The practical dev board is to **build our own**: one LQFP-128 chip (YT9215S about US$1.92 at LCSC), plus the open-hardware 5-port YT9215S switch on OSHWHub as a reference layout. **[V]/[I]**
- **Recommendation:** buy two or three TP-Link TL-SG105 V6 / LS1005G V1 units now for RTL8367S 8051 experiments, and treat any YT9215 work as "spin our own breakout with a YT9215SC" if it is ever needed.

## 1. Official evaluation boards

| Chip | Official EVB | Evidence | Public availability |
|---|---|---|---|
| RTL8367S-CG | Reference designs and EVBs, partners only **[V]** | Leaked programming guide | None found **[V]** |
| YT9215S / SC / RB | None mentioned **[V]** | Motorcomm product page | None found **[V]** |

| Leaked Realtek document | Rev | Year | Marking |
|---|---|---|---|
| "Realtek Unmanaged Switch Programming Guide" | 1.3.11 | 2017 | Confidential, development partners |

Shops searched for an RTL8367S EVB: Mouser, Digi-Key, LCSC, AliExpress, eBay
and Amazon.

Schematic + PCB + BOM packs for RTL8367S designs circulate on Chinese forums (e.g. [bbs.16rd.com thread 585232](https://bbs.16rd.com/thread-585232-1-1.html)). They are useful as reference layouts but are of unclear provenance and licence.

## 2. RTL8367S options

### 2a. Cheap unmanaged switches (best 8051 dev platform)

All of these are "dumb" switches where the RTL8367S boots from a small EEPROM with no host CPU. That is exactly the configuration where we could load our own 8051 code over SMI.

| Product | Case | HW version with RTL8367S | Evidence | Config storage |
|---|---|---|---|---|
| **TP-Link TL-SG105** | Metal, 5-port | **V6.0** | [V: Gough Lui teardown](https://goughlui.com/2022/02/27/unbox-teardown-tp-link-tl-sg105-5-port-gigabit-desktop-ethernet-switch/) | Serial EEPROM |
| **TP-Link LS1005G** | Plastic (LiteWave) | **V1** | [V: TechInfoDepot](https://techinfodepot.shoutwiki.com/wiki/TP-LINK_LS1005G_V1) | 24C02 EEPROM (2 Kbit) |
| **TP-Link TL-SG1005D** | Plastic | **rev 7** | [V: McMCCRU](https://github.com/McMCCRU/Arduino_RTL8367C) | 24Cxx EEPROM |

Board-level access:

| Product | Flash | Header | Access |
|---|---|---|---|
| TL-SG105 V6.0 | None | None | EEPROM next to the chip; roomy case, easy to open |
| LS1005G V1 | None | – | RTL8367S + EEPROM only |
| TL-SG1005D rev 7 | – | – | Remove the EEPROM, drive SMI from an MCU |

TL-SG1005D rev 7 EEPROM socket pins:

| EEPROM pin | Signal |
|---|---|
| 1–4 | GND |
| 5 | SDA |
| 6 | SCK |
| 8 | 3.3 V |

Indicative prices and where to buy:

| Product | Shop | Price | Notes |
|---|---|---|---|
| TL-SG105 | **amazon.com.au** | About A$20–29 | Gough Lui paid about A$20 |
| TL-SG105 | AU retailers | A$27–35 | Per [PriceMe](https://www.priceme.com.au/TP-Link-TL-SG105/p-888455411.aspx) |
| TL-SG105 | **eBay** | Often A$20–30 new, less used | [ebay.com.au TL-SG105 listings](https://www.ebay.com.au/sch/i.html?_nkw=TP-Link+TL-SG105+v6) |
| TL-SG105 | **AliExpress** | Available | Versions unclear |
| LS1005G | **amazon.com.au** | RRP A$24.95, seen at A$16 | [OzBargain](https://ozbargain.com.au/node/738664) |
| LS1005G | US Amazon | Often US$9–12 | – |
| LS1005G | **eBay**, **AliExpress** | A$12–20 | Common |
| TL-SG1005D | **AliExpress**, **eBay** | About A$15–25 | – |
| TL-SG1005D | Amazon AU | – | Less common now; TL-SG105 / LS1005G replaced it |

How to use one as a dev board: **[I]**, building on the [V] items above.

1. Desolder the EEPROM and solder a 6-pin header to its pads (SDA, SCK, 3.3 V, GND).
2. Wire an RP2040 (Pico) to SDA/SCK. Port the GPL `rtl8367c` SMI routines, or start from McMCCRU's Arduino sketch.
3. Load test code into the 8051 IROM: assert `DW8051_RST`, enable `ACS_IROM_EN`, write bytes to 0xE000+, release reset (see `switch-embedded-cpu.md` boot flow).
4. For printf debug, tack a wire to the chip's UART TX (pin 46). For flash boot experiments, add a SOIC-8 SPI flash on SPIF pins 48/49/53/54 and set the EN_SPIF strap.

Variants to avoid: newer hardware versions of these models may move to RTL8367S-VB, RTL8367RB-VB or a different vendor. Older TL-SG1005D v5 uses "RTL8367" (no S, per [shaddack's notes](https://shaddack.mauriceward.com/notes/ethernet.webt)). AliExpress "5-port gigabit switch module" PCBAs are almost all **RTL8367RB** (older RTL8367B family), not the S (e.g. [eBay 135146159571](https://www.ebay.com/itm/135146159571)). **[V]**

### 2b. Routers with RTL8367S behind a Linux SoC

Useful if we want the switch on a real CPU port with a working Linux driver to compare against, or to sniff SMI traffic while the vendor driver loads the 8051.

| Product | SoC | RTL8367S link | Evidence | Notes |
|---|---|---|---|---|
| **MERCUSYS MR85X** (AX3000) | MT7981B | 2500base-X fixed link | [V: OpenWrt commit](https://git.openwrt.org/b2648d89517c05f7b5633e1d79a989c3e5fd011e) | Supported in OpenWrt. Current model |
| **TP-Link Archer C5 v4** | MT7620A | – | [V: OpenWrt forum](https://forum.openwrt.org/t/reduce-number-of-drivers-for-rtl8367s/237681) | Old and cheap; OpenWrt supported |
| **TP-Link EC220-G5 v2** | MT7620A-class | – | [V] | ISP-branded, cheap second-hand |
| **TOTOLINK A8000RU** | MT7622 | 2500base-X | [V: OpenWrt PR #24861](https://github.com/openwrt/openwrt/pull/24861) | OpenWrt supported |
| **Buffalo WSR-2533DHP2** | MT7622 | 2500base-X | [V] | Japan market |

| Product | Board detail | Value |
|---|---|---|
| MERCUSYS MR85X | Switch reset | GPIO 39 |
| MERCUSYS MR85X | UART | UART0, 115200 8N1 |
| TP-Link Archer C5 v4 | Switch driver | Old rtl8367b swconfig driver |

Indicative prices and where to buy:

| Product | Shop | Price |
|---|---|---|
| MERCUSYS MR85X | **AU retail** ([icit.net.au](https://icit.net.au/product/mr85x-mercusys-mr85x-ax3000-dual-band-wi-fi-6-router/)) | A$123.50 |
| MERCUSYS MR85X | **amazon.com.au**, **eBay** | Around A$100–130 |
| MERCUSYS MR85X | **AliExpress** | Occasional listings |
| TP-Link Archer C5 v4 | **eBay**, used | About A$20–40 |
| TP-Link EC220-G5 v2 | **eBay**, used | – |
| TOTOLINK A8000RU | **AliExpress**, **eBay** | About US$50–80 |
| Buffalo WSR-2533DHP2 | **eBay** (Japanese sellers) | – |

Linux support: upstream `rtl8365mb` DSA driver (RGMII; SGMII/HSGMII patches for RTL8367S posted June 2026), plus OpenWrt's `rtl8367b`/`rtk-gsw` drivers. **[V]**

### 2c. Open hardware RTL8367S boards

| Project | Switch IC | Controller | Kind |
|---|---|---|---|
| [AlbrechtL/rpi-managed-switch-4-port](https://github.com/AlbrechtL/rpi-managed-switch-4-port) | RTL8367S | Raspberry Pi Zero | Open board |
| [PCBWay: RTL8367S-4GE+SFP Gigabit Optical Switch](https://www.pcbway.com/project/sponsor/RTL8367S_4GE_SFP_Gigabit_Optical_Switch_7f271618.html) | RTL8367S | None | Shared PCBWay project |
| [BrixIT: Making a Linux-managed network switch](https://blog.brixit.nl/making-a-linux-managed-network-switch/) | RTL8367S | PINE64 A64-LTS | Blog write-up |
| [maxx-ukoo/rtl8367-controller](https://github.com/maxx-ukoo/rtl8367-controller) | 2 × RTL8367S | STM32F103 | Retail switch mod |
| [libc0607/Realtek_switch_hacking](https://github.com/libc0607/Realtek_switch_hacking) | RTL8367RB | ESP8266 | Docs, tools, open board |

| Project | Property | Value |
|---|---|---|
| AlbrechtL | Hardware | RTL8367S + Raspberry Pi Zero + ENC28J60 [V] |
| AlbrechtL | Design files | KiCad, "ready for JLCPCB production" [V] |
| AlbrechtL | Licence | GPL-3.0 [V] |
| AlbrechtL | Software | OpenWrt fork using `rtl8365mb` DSA [V] |
| AlbrechtL | Cost (author's estimate) | About US$54/unit for 2-unit PCBA [V] |
| AlbrechtL | Pi link speed | Only about 5 Mbit/s over SPI |
| AlbrechtL | Not broken out | 8051, UART, flash |
| AlbrechtL | Use to us | Good layout reference |
| PCBWay | Ports | 4 × GE + SFP on SGMII [V] |
| PCBWay | Power | USB 5 V input, MT2492 buck, on-chip 1.1 V DC-DC [V] |
| PCBWay | Licence | None stated |
| PCBWay | Firmware | Realtek config `.bin`, "non-commercial use only" |
| PCBWay | How to get | Order through PCBWay |
| PCBWay | Use to us | Closest to our use-case (SerDes port in use) |
| BrixIT | Author | Martijn Braam |
| BrixIT | Control link | GPIO SMI from the PINE64 A64-LTS [V] |
| BrixIT | Board features | Strap solder jumpers, optional SPI-flash footprint [V] |
| BrixIT | Repo | None linked |
| BrixIT | Use to us | Notes on straps and the minimal config |
| maxx-ukoo | Target | ZX900-AFG-82N PoE switch [V] |
| maxx-ukoo | Switch ICs | 2 × RTL8367S over RGMII [V] |
| maxx-ukoo | What it does | Replaces the MCU with an STM32F103 over SMI [V] |
| maxx-ukoo | PoE controller in target | TMI7608S |
| maxx-ukoo | Use to us | A retail PoE switch close to our topology |
| libc0607 | Contents | Docs, ESP8266 SMI tools [V] |
| libc0607 | Also holds | Yakigani RTL8370 IROM programmer [V] |
| libc0607 | Open board | RTL8367RB + ESP8266 [V] |
| libc0607 | Use to us | Best community hub for Realtek 8051 work |

## 3. YT9215 options

### 3a. Which part has the CPU

| Part | Ports | CPU on Motorcomm product page | CPU in LCSC draft datasheet |
|---|---|---|---|
| YT9215S | 5 GE + 1 SGMII + 1 RGMII | No **[V]** | Yes **[V]** |
| YT9215SC | 5 GE + 2 SerDes (SGMII / 2.5G) | Yes **[V]** | Yes **[V]** |
| YT9215RB | 5 GE + 2 RGMII | No **[V]** | n/a |
| YT9218N / YT9218MB | 8-port | Yes **[V]** | n/a |

| Part | Source | What it says |
|---|---|---|
| YT9215S | [Product page](https://www.motor-comm.com/product/switching-chip) | No CPU listed |
| YT9215S | [Draft datasheet](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308291451_Motorcomm-YT9215S_C5899183.pdf) | "Integrated RISC-V microprocessor" |
| YT9215S | Draft datasheet | JTAG0/1, UART0–2, SPI flash |
| YT9215S | Draft datasheet | `STRAP_DIS_MCU` on pin 75 |
| YT9215SC | Product page | "内置高性能RISC-V 核心CPU" |
| YT9215SC | Product page | "支持简单网管" |
| YT9215SC | Draft datasheet | Same pin functions as the YT9215S |
| YT9215RB | Product page | No CPU |
| YT9218N / YT9218MB | Product page | RISC-V CPU + simple management |

So on retail YT9215S boards the core is probably present but unsupported and likely strapped off. **[I]** Plan any CPU work on the **YT9215SC**.

### 3b. Retail products with YT9215

| Product | Host SoC | Switch | Switch link | MDIO addr | Linux support |
|---|---|---|---|---|---|
| **Xiaomi CR881x** | IPQ5018 | YT9215S | SGMII / 2500base-X | 0x1d | OpenWrt fork |
| **BDY-G98 / 彼度云 G98** | RK3588 | 2 × YT9215S | `rgmii-txid` | 0x1d | DSA `yt921x` |
| Unnamed industrial boards | RK3568 / RK3588 | YT9215 | MAC-to-MAC | n/a | n/a |

| Product | Property | Value |
|---|---|---|
| Xiaomi CR881x | Models | CR8816 / CR8818 etc. |
| Xiaomi CR881x | Type | China carrier AX3000 mesh units |
| Xiaomi CR881x | Board | M79 |
| Xiaomi CR881x | Switch CPU port | Port 8 [V] |
| Xiaomi CR881x | Switch reset | GPIO 35 [V] |
| Xiaomi CR881x | Evidence | [OpenWrt forum](https://forum.openwrt.org/t/ipq5018-yt9215s-and-1000base-x-2500base-x/241325), [hzyitc issue #150](https://github.com/hzyitc/openwrt-redmi-ax3000/issues/150) |
| Xiaomi CR881x | UART | J1 (VCC-RX-GND-TX) |
| Xiaomi CR881x | OpenWrt | [hzyitc/openwrt-redmi-ax3000](https://github.com/hzyitc/openwrt-redmi-ax3000) |
| Xiaomi CR881x | Known issue | Switch probe still flaky on some boards [V] |
| Xiaomi CR881x | Where sold | Mostly second-hand in China (Xianyu) |
| Xiaomi CR881x | **AliExpress**, **eBay** | Occasional CR880x/CR881x listings |
| Xiaomi CR881x | Typical price | US$25–50 |
| Xiaomi CR881x | Check before buying | The model must be **CR881x** |
| Xiaomi CR881x | Not confirmed YT9215 **[I]** | CR880x (CR8806/8808/8809), Redmi AX3000 |
| BDY-G98 | Type | RK3588 NAS/router, 8 LAN |
| BDY-G98 | Switch attach | Each YT9215S on an RK3588 GMAC [V] |
| BDY-G98 | Evidence | [GitHub issue](https://github.com/yifengyou/BDY_G98_RK3588/issues/6) |
| BDY-G98 | Known issue | Cross-chip forwarding lock-up bug reported [V] |
| BDY-G98 | Where sold | China-market box |
| BDY-G98 | Amazon AU / eBay / AliExpress | Not found in this search |
| Unnamed boards | Evidence | Several CSDN write-ups [V: [CSDN](https://blog.csdn.net/xuesong10210/article/details/135957672)] |
| Unnamed boards | Product names | Not given |

I found **no cheap unmanaged retail switch** confirmed to use a YT9215. Motorcomm targets "dumb switch" use, so some Chinese-brand 5-port switches likely use it, but none were identified in teardowns. **[I]**

### 3c. Open hardware and self-build

- **OSHWHub "基于裕太微YT9215S的五口千兆交换机" v2.0** by pankanwen ([oshwhub.com](https://oshwhub.com/pankanwen/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0)) is an open 5-port gigabit switch on the YT9215S. It can be ordered through JLCPCB. I could not read the page (robots block), so I don't know whether JTAG/UART are broken out. **[V: exists] / [I]**
- **Chip cost:** YT9215S about US$1.92 at LCSC (C5899183, 57 in stock). The YT9215SC is LCSC C51037433. **[V]**
- **Our own breakout** (recommended if we ever pursue the RISC-V core): YT9215SC + SPI flash socket + both JTAG groups on a 2.54 mm header + UART0 + strap jumpers (`STRAP_DIS_MCU`, `STRAP_EN_SPIF`, `STRAP_SMI_SEL`) + one RJ45 + SGMII to an SFP cage. **[I]**

## 4. Purchase quick-links

Search links (results change daily; check hardware version in the listing photos):

- amazon.com.au: [TP-Link TL-SG105](https://www.amazon.com.au/s?k=TP-Link+TL-SG105), [TP-Link LS1005G](https://www.amazon.com.au/s?k=TP-Link+LS1005G), [Mercusys MR85X](https://www.amazon.com.au/s?k=Mercusys+MR85X)
- eBay: [TL-SG105 V6](https://www.ebay.com.au/sch/i.html?_nkw=TP-Link+TL-SG105+v6), [LS1005G](https://www.ebay.com.au/sch/i.html?_nkw=TP-Link+LS1005G), [TL-SG1005D](https://www.ebay.com.au/sch/i.html?_nkw=TL-SG1005D), [Archer C5 v4](https://www.ebay.com.au/sch/i.html?_nkw=Archer+C5+v4), [TOTOLINK A8000RU](https://www.ebay.com/sch/i.html?_nkw=TOTOLINK+A8000RU), [Xiaomi CR8818](https://www.ebay.com/sch/i.html?_nkw=Xiaomi+CR8818)
- AliExpress: [RTL8367S chips](https://www.aliexpress.com/w/wholesale-rtl8367s.html) (US$1–3 each, bare chips only, no boards), [TL-SG1005D](https://www.aliexpress.com/w/wholesale-TL-SG1005D.html), [TOTOLINK A8000RU](https://www.aliexpress.com/w/wholesale-A8000RU.html), [Xiaomi CR881x](https://www.aliexpress.com/w/wholesale-xiaomi-CR8818.html)
- LCSC: [YT9215S C5899183](https://www.lcsc.com/product-detail/Ethernet-ICs_Motorcomm-YT9215S_C5899183.html), RTL8367S-CG C2760849

Note: the prices in this file come from search snippets and deal pages, not from opening live Amazon/eBay/AliExpress product pages (those block automated fetches).

## Open questions

- Which current TL-SG105 / LS1005G hardware versions are still RTL8367S? The V6 and V1 data points are from 2022.
- Does the CR881x's YT9215S have its MCU strapped off (pin 75)? A photo of the board around the switch would answer it.
- Contents of the OSHWHub YT9215S design (JTAG/UART breakout).
