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

| Chip | Official EVB | Public availability |
|---|---|---|
| RTL8367S-CG | Realtek reference designs and EVBs exist for partners. The leaked "Realtek Unmanaged Switch Programming Guide" (Rev 1.3.11, 2017) is marked confidential for development partners **[V]** | None found on Mouser, Digi-Key, LCSC, AliExpress, eBay or Amazon **[V]** |
| YT9215S / SC / RB | Motorcomm's product page mentions no EVB or reference design **[V]** | None found **[V]** |

Schematic + PCB + BOM packs for RTL8367S designs circulate on Chinese forums (e.g. [bbs.16rd.com thread 585232](https://bbs.16rd.com/thread-585232-1-1.html)). They are useful as reference layouts but are of unclear provenance and licence.

## 2. RTL8367S options

### 2a. Cheap unmanaged switches (best 8051 dev platform)

All of these are "dumb" switches where the RTL8367S boots from a small EEPROM with no host CPU. That is exactly the configuration where we could load our own 8051 code over SMI.

| Product | HW version with RTL8367S | Board-level access | Indicative price and where to buy |
|---|---|---|---|
| **TP-Link TL-SG105** (metal, 5-port) | **V6.0** [V: Gough Lui teardown](https://goughlui.com/2022/02/27/unbox-teardown-tp-link-tl-sg105-5-port-gigabit-desktop-ethernet-switch/) | Serial EEPROM next to the chip, no flash, no header. Roomy metal case, easy to open | **amazon.com.au**: about A$20–29 (Gough Lui paid about A$20 on Amazon AU; AU retailers A$27–35 per [PriceMe](https://www.priceme.com.au/TP-Link-TL-SG105/p-888455411.aspx)). **eBay**: [ebay.com.au TL-SG105 listings](https://www.ebay.com.au/sch/i.html?_nkw=TP-Link+TL-SG105+v6), often A$20–30 new, less used. **AliExpress**: available but versions unclear |
| **TP-Link LS1005G** (LiteWave, plastic) | **V1** [V: TechInfoDepot](https://techinfodepot.shoutwiki.com/wiki/TP-LINK_LS1005G_V1) | RTL8367S + 24C02 (2 Kbit) EEPROM only | **amazon.com.au**: RRP A$24.95, seen at A$16 ([OzBargain](https://ozbargain.com.au/node/738664)). US Amazon often US$9–12. **eBay** and **AliExpress**: common, A$12–20 |
| **TP-Link TL-SG1005D** (plastic) | **rev 7** [V: McMCCRU](https://github.com/McMCCRU/Arduino_RTL8367C) | 24Cxx EEPROM socket pins: pin 5 = SDA, pin 6 = SCK, pin 8 = 3.3 V, pins 1–4 = GND. Remove the EEPROM and drive SMI from an MCU | **AliExpress** / **eBay**: about A$15–25. Less common on Amazon AU now (TL-SG105 / LS1005G have replaced it) |

How to use one as a dev board: **[I]**, building on the [V] items above.

1. Desolder the EEPROM and solder a 6-pin header to its pads (SDA, SCK, 3.3 V, GND).
2. Wire an RP2040 (Pico) to SDA/SCK. Port the GPL `rtl8367c` SMI routines, or start from McMCCRU's Arduino sketch.
3. Load test code into the 8051 IROM: assert `DW8051_RST`, enable `ACS_IROM_EN`, write bytes to 0xE000+, release reset (see `switch-embedded-cpu.md` boot flow).
4. For printf debug, tack a wire to the chip's UART TX (pin 46). For flash boot experiments, add a SOIC-8 SPI flash on SPIF pins 48/49/53/54 and set the EN_SPIF strap.

Variants to avoid: newer hardware versions of these models may move to RTL8367S-VB, RTL8367RB-VB or a different vendor. Older TL-SG1005D v5 uses "RTL8367" (no S, per [shaddack's notes](https://shaddack.mauriceward.com/notes/ethernet.webt)). AliExpress "5-port gigabit switch module" PCBAs are almost all **RTL8367RB** (older RTL8367B family), not the S (e.g. [eBay 135146159571](https://www.ebay.com/itm/135146159571)). **[V]**

### 2b. Routers with RTL8367S behind a Linux SoC

Useful if we want the switch on a real CPU port with a working Linux driver to compare against, or to sniff SMI traffic while the vendor driver loads the 8051.

| Product | SoC and link | Notes | Indicative price and where to buy |
|---|---|---|---|
| **MERCUSYS MR85X** (AX3000) | MT7981B. RTL8367S on 2500base-X fixed link, reset on GPIO 39, UART0 115200 8N1 [V: OpenWrt commit](https://git.openwrt.org/b2648d89517c05f7b5633e1d79a989c3e5fd011e) | Supported in OpenWrt. Current model | **AU retail** A$123.50 ([icit.net.au](https://icit.net.au/product/mr85x-mercusys-mr85x-ax3000-dual-band-wi-fi-6-router/)); **amazon.com.au** and **eBay** listings around A$100–130; **AliExpress**: occasional |
| **TP-Link Archer C5 v4** | MT7620A. RTL8367S (driven by the old rtl8367b swconfig driver) [V: OpenWrt forum](https://forum.openwrt.org/t/reduce-number-of-drivers-for-rtl8367s/237681) | Old and cheap; OpenWrt supported | **eBay** used: about A$20–40 |
| **TP-Link EC220-G5 v2** | MT7620A-class, RTL8367S [V] | ISP-branded, cheap second-hand | **eBay** used |
| **TOTOLINK A8000RU** | MT7622, RTL8367S on 2500base-X [V: OpenWrt PR #24861](https://github.com/openwrt/openwrt/pull/24861) | OpenWrt supported | **AliExpress** / **eBay**: about US$50–80 |
| **Buffalo WSR-2533DHP2** | MT7622, RTL8367S on 2500base-X [V] | Japan market | **eBay** (Japanese sellers) |

Linux support: upstream `rtl8365mb` DSA driver (RGMII; SGMII/HSGMII patches for RTL8367S posted June 2026), plus OpenWrt's `rtl8367b`/`rtk-gsw` drivers. **[V]**

### 2c. Open hardware RTL8367S boards

| Project | What it is | Status and access |
|---|---|---|
| [AlbrechtL/rpi-managed-switch-4-port](https://github.com/AlbrechtL/rpi-managed-switch-4-port) | RTL8367S + Raspberry Pi Zero + ENC28J60, KiCad, GPL-3.0, "ready for JLCPCB production". Software: OpenWrt fork using `rtl8365mb` DSA [V] | Author estimates about US$54/unit for 2-unit PCBA [V]. Pi link is only about 5 Mbit/s over SPI. 8051/UART/flash not broken out. Good layout reference |
| [PCBWay: RTL8367S-4GE+SFP Gigabit Optical Switch](https://www.pcbway.com/project/sponsor/RTL8367S_4GE_SFP_Gigabit_Optical_Switch_7f271618.html) | 4 × GE + SFP on SGMII, USB 5 V input, MT2492 buck, on-chip 1.1 V DC-DC [V] | No licence stated; ships a Realtek config `.bin` "non-commercial use only". Order through PCBWay. Closest to our use-case (SerDes port in use) |
| [BrixIT: Making a Linux-managed network switch](https://blog.brixit.nl/making-a-linux-managed-network-switch/) | Martijn Braam's RTL8367S board driven from a PINE64 A64-LTS over GPIO SMI, strap solder jumpers, optional SPI-flash footprint [V] | No repo linked. Useful notes on straps and the minimal config |
| [maxx-ukoo/rtl8367-controller](https://github.com/maxx-ukoo/rtl8367-controller) | Replaces the MCU in a ZX900-AFG-82N PoE switch (2 × RTL8367S over RGMII) with an STM32F103 over SMI [V] | Shows a retail PoE switch with RTL8367S plus a TMI7608S PoE controller, close to our topology |
| [libc0607/Realtek_switch_hacking](https://github.com/libc0607/Realtek_switch_hacking) | Docs, ESP8266 SMI tools, Yakigani RTL8370 IROM programmer, RTL8367RB+ESP8266 open board [V] | Best community hub for Realtek 8051 work |

## 3. YT9215 options

### 3a. Which part has the CPU

| Part | Motorcomm product page | LCSC draft datasheet | Ports |
|---|---|---|---|
| YT9215S | No CPU listed [V: [motor-comm.com](https://www.motor-comm.com/product/switching-chip)] | "Integrated RISC-V microprocessor", JTAG0/1, UART0–2, SPI flash, `STRAP_DIS_MCU` pin 75 [V: [datasheet](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308291451_Motorcomm-YT9215S_C5899183.pdf)] | 5 GE + 1 SGMII + 1 RGMII |
| YT9215SC | "内置高性能RISC-V 核心CPU", "支持简单网管" [V] | Same pin functions [V] | 5 GE + 2 SerDes (SGMII / 2.5G) |
| YT9215RB | No CPU [V] | n/a | 5 GE + 2 RGMII |
| YT9218N / YT9218MB | RISC-V CPU + simple management [V] | n/a | 8-port |

So on retail YT9215S boards the core is probably present but unsupported and likely strapped off. **[I]** Plan any CPU work on the **YT9215SC**.

### 3b. Retail products with YT9215

| Product | Chip and link | Access | Indicative price and where to buy |
|---|---|---|---|
| **Xiaomi CR881x** (CR8816 / CR8818 etc., China carrier AX3000 mesh units; M79 board) | IPQ5018 + YT9215S. CPU port 8 on SGMII / 2500base-X, MDIO addr 0x1d, reset on GPIO 35 [V: [OpenWrt forum](https://forum.openwrt.org/t/ipq5018-yt9215s-and-1000base-x-2500base-x/241325), [hzyitc issue #150](https://github.com/hzyitc/openwrt-redmi-ax3000/issues/150)] | UART on J1 (VCC-RX-GND-TX), OpenWrt via [hzyitc/openwrt-redmi-ax3000](https://github.com/hzyitc/openwrt-redmi-ax3000). Switch probe is still flaky on some boards [V] | Mostly sold second-hand in China (Xianyu). **AliExpress** and **eBay**: occasional CR880x/CR881x listings, typically US$25–50; check the model is **CR881x**, since the CR880x (CR8806/8808/8809) and Redmi AX3000 are not confirmed to use the YT9215 **[I]** |
| **BDY-G98 / 彼度云 G98** (RK3588 NAS/router, 8 LAN) | 2 × YT9215S, each on an RK3588 GMAC over `rgmii-txid`, MDIO addr 0x1d [V: [GitHub issue](https://github.com/yifengyou/BDY_G98_RK3588/issues/6)] | Linux DSA via `yt921x`. Cross-chip forwarding lock-up bug reported [V] | China-market box; not found on Amazon AU / eBay / AliExpress in this search |
| Unnamed RK3568 / RK3588 industrial boards | Several CSDN write-ups of RK3568/RK3588 + YT9215 MAC-to-MAC designs [V: [CSDN](https://blog.csdn.net/xuesong10210/article/details/135957672)] | Product names not given | n/a |

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
