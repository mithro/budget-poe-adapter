# Switch IC detail: RTL8363NB (pick) vs RTL8367S and YT9215S (candidates)

Side-by-side copy of the *Switch detail* tab in the [comparison sheet](https://docs.google.com/spreadsheets/d/1nPsWa2ZrP8suhqZF9iXVH5w3_iRSPm5tRze83cas7SA/edit#gid=2). Prices are LCSC on 2026-10-22. `?` means no public source gives the value; None means the chip doesn't have it.

**Takeaways**

- RTL8363NB stays the pick: exactly two GbE PHYs, RMII to the MCU, smallest package (QFN-76 9×9 mm), no embedded CPU to manage.
- RTL8367S is $0.30 cheaper at 100 pcs (LCSC price break), but its extension port has no RMII, so the MCU must use MII, and three PHYs sit unused.
- YT9215S is the Chinese second source with RMII and a Linux driver, but only 57 in stock and a draft datasheet.
- Embedded CPUs: RTL8367S has an 8051 and YT9215S a RISC-V core. Neither has a public clock, memory size or SDK, and neither has USB, so both should be strapped off.
- Support parts are similar for all three: 25 MHz crystal, buck inductor and bulk caps for the on-chip 1.1 V regulator, a 2.49 kΩ 1% bias resistor, strap resistors and two GbE transformers. Only the RTL8367S public datasheet gives the inductor value (2.2 µH).
- SerDes: RTL8363NB has none; RTL8367S and YT9215S each have one lane at 1.25 or 3.125 GBd (up to 2.5 Gbit/s). Not needed for this adapter.
- None of the public datasheets give a power-draw figure.


## Status

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| Verdict | Pick | Candidate | Candidate |
| Vendor | Realtek | Realtek | Motorcomm |

## Price & stock (LCSC, 2026-10-22)

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| LCSC part | [C2835942](https://www.lcsc.com/product-detail/C2835942.html) | [C2760849](https://www.lcsc.com/product-detail/C2760849.html) | [C5899183](https://www.lcsc.com/product-detail/C5899183.html) |
| Datasheet | [PDF](https://www.lcsc.com/datasheet/C2835942.pdf) | [PDF](https://www.lcsc.com/datasheet/C2760849.pdf) | [PDF](https://www.lcsc.com/datasheet/C5899183.pdf) |
| @100 | $1.962 | $1.665 | $2.116 |
| Price break | 30+ | 90+ | 90+ |
| @1k | $1.476 | $1.490 | $1.922 |
| vs RTL8363NB @100 | $0.000 | -$0.297 | +$0.154 |
| Stock | 1,562 | 4,576 | 57 |
| JLCPCB library | Extended | Extended | Extended |

## Ports

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| GbE copper PHYs | 2 | 5 | 5 |
| Unused PHYs | 0 | 3 | 3 |
| Extension ports | 1 (GMAC1) | 2 (GMAC1, GMAC2) | 2 (GMAC1, GMAC2) |
| MCU port modes | RGMII, MII, RMII, TMII | RGMII, MII | RGMII, MII, RMII |
| RMII to MCU | Yes | No (MII only) | Yes |
| SerDes lanes | 0 | 1 | 1 |
| SerDes modes | None | SGMII, HSGMII | SGMII, HSGMII, 1000BASE-X, 2500BASE-X, 100BASE-FX |
| SerDes line rate | None | 1.25 or 3.125 GBd | 1.25 or 3.125 GBd |
| SerDes max data rate | None | 2.5 Gbit/s | 2.5 Gbit/s |

## Management

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| External CPU interface | SMI (MDIO), I²C-like | SMI (MDIO), SPI | MDIO, I²C |
| Interrupt output | Yes | Yes | Yes |
| EEPROM autoload | 32 KB | 32 KB | 16 KB |
| Linux driver | rtl8365mb (DSA) | rtl8365mb (DSA) | yt921x (DSA) |
| Register documentation | NDA; GPL rtl8367c API | NDA; GPL rtl8367c API | Draft datasheet; Linux yt921x |

## Embedded CPU

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| CPU core | None | 8051 | RISC-V |
| CPU clock | None | ? | ? |
| CPU memory | None | ? | ? |
| Code storage | None | EEPROM or SPI flash | SPI flash, single or dual |
| Disable strap | None | DIS_8051, pull-up | DIS_MCU, pull-up |
| Internal CPU port | None | ? | Port 10 |
| SDK | None | NDA only | None public |
| Useful here | None | No | No |

## Switching features

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| MAC address table | 2K entries | 2K entries | 4K entries |
| VLAN table | 4K entries | 4K entries | 4K entries |
| Jumbo frames | 9,216 B | 9,216 B | 9,216 B |
| Priority queues | 8 | 8 | 8 unicast, 4 multicast |
| ACL rules | 48 | 96 | 384 |
| Link aggregation | None | 2 groups | 2 groups |
| Port mirroring | Port-based | Port-based | Port- and flow-based |
| IGMP/MLD snooping | Yes | Yes | Yes |
| LLDP / OAM | ? | Yes | Yes |

## PHY & diagnostics

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| EEE (802.3az) | Yes | Yes, strap-enabled | ? |
| Cable diagnostics | RTCT | RTCT | VCT |
| LEDs | 3 per port, parallel or serial | 2 per port, parallel or serial | 2 per port, parallel or serial |
| Other PHY features | Green Ethernet power saving | Green Ethernet, loop detection | 400 m at 100 Mbit/s (LRE), WoL, loop detection |

## Power & package

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| Package | QFN-76 9×9 mm | LQFP-128 14×14 mm | LQFP-128-EP 14×14 mm |
| Body area | 81 mm² | 196 mm² | 196 mm² |
| Supply | 3.3 V, int. 1.1 V buck | 3.3 V, int. 1.1 V buck | 3.3 V, int. 1.1 V buck |
| Clock | 25 MHz crystal | 25 MHz crystal | 25 MHz crystal |
| Power draw | ? | ? | ? |
| Operating temp. | ? | ? | 0–70 °C |

## External support components

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| Crystal | 25 MHz ±50 ppm, 2 load caps | 25 MHz ±50 ppm, 2 load caps, 150 Ω | 25 MHz, 2 load caps |
| Oscillator option | 3.3 V 25 MHz OSC | 3.3 V 25 MHz OSC | 3.3 V 25 MHz OSC |
| Buck inductor | ? | 2.2 µH | ? |
| Buck capacitors | ? | 10 µF on LX output, 10 µF on HV_SWR | 10 µF on HV_SWR |
| EN_SWR resistor | 4.7 kΩ | 1 kΩ | 1 kΩ |
| Bias resistor | 2.49 kΩ 1% | 2.49 kΩ 1% | 2.49 kΩ 1% |
| Reset | Int. 75 kΩ pull-up | Int. 75 kΩ pull-up | Ext. pull-up |
| Strap resistors | 4.7 kΩ per strap | 4.7 kΩ per strap | 4.7 kΩ per strap, plus 3 reserved pull-ups |
| Unused MAC inputs | 1 kΩ pull-down | 1 kΩ pull-down | ? |
| Interrupt pin | ? | 1 kΩ or 4.7 kΩ | ? |
| EEPROM | Optional 24Cxx | Optional 24Cxx | Optional 24Cxx |
| SPI flash | None | Optional | Optional |
| MDI termination | None | None | None |
| Magnetics | 2 GbE transformers | 2 GbE transformers | 2 GbE transformers |
| LED resistors | Optional, 1 per LED | Optional, 1 per LED | Optional, 1 per LED |
| Decoupling | ? | ? | ? |

## Fit for this adapter

| Feature | RTL8363NB-VB-CG | RTL8367S-CG | YT9215S |
|---|---|---|---|
| MCU attach | RMII/MII ext. port | MII ext. port, or a spare PHY | RMII/MII ext. port, or a spare PHY |
| Main advantage | Exact port count, smallest | Cheapest at 100 pcs | Second source to Realtek |
| Main risk | NDA register docs | Idle power of 3 spare PHYs | 57 in stock, draft datasheet |

## Feature notes

**Verdict**  
Assessment from the Switches tab.  
Hover the verdict cells on the Switches tab for the reasoning.

**Vendor**  
Manufacturer

**LCSC part**  
Links to the LCSC product page.  
JLCPCB assembly uses the same C-number.

**Datasheet**  
Links to LCSC's copy of the datasheet.  
RTL8367S: the public copy is a preliminary partner datasheet (Rev. Pre-0.941, 2016).  
YT9215S: the public copy is a draft (DRAFT_05, 2023).

**@100**  
Unit price at 100 pcs (USD).  
The LCSC break that applies to an order of 100.

**Price break**  
The LCSC break used for the @100 price.  
RTL8363NB has no break between 30+ and 260+, which is why it is dearer at 100 than the RTL8367S.

**@1k**  
Unit price at 1,000 pcs (USD).

**vs RTL8363NB @100**  
Price difference to the pick at 100 pcs.

**Stock**  
Units in stock at LCSC.

**JLCPCB library**  
Extended = in the JLCPCB parts library (per-part loading fee).

**GbE copper PHYs**  
Integrated 10/100/1000BASE-T PHYs.  
The passthrough needs 2: PoE side and device side.

**Unused PHYs**  
PHYs the passthrough doesn't need.  
Each costs idle power unless powered down by register, but one can host a cap-coupled 10BASE-T MCU port.

**Extension ports**  
Extra MAC ports for a CPU or another switch.

**MCU port modes**  
Digital extension port modes for the adapter MCU.

**RMII to MCU**  
RMII is what CH32V307 and the RP2040 PIO RMII drivers use.  
On the RTL8367S the MCU would need MII instead (2.5 MHz nibble clock at 10 Mbit/s), which is also fine for PIO.

**SerDes lanes**  
High-speed serial ports for an uplink, SFP or another switch.  
Not needed for this adapter.

**SerDes modes**  
Modes listed in the public datasheets.  
YT9215S: the key features list 2500BASE-X, SGMII, 1000BASE-X and 100BASE-FX; the general description calls it SGMII/HSGMII.

**SerDes line rate**  
Baud rate on the wire (8b/10b coded).  
Both datasheets write these as 1.25 GHz and 3.125 GHz.

**SerDes max data rate**  
Payload rate after 8b/10b coding.  
HSGMII / 2500BASE-X at 3.125 GBd carries 2.5 Gbit/s; SGMII at 1.25 GBd carries 1 Gbit/s.

**External CPU interface**  
How the adapter MCU configures and reads the switch.  
Selected by strap pins.  
All are easy to bit-bang from a CH32V or RP2040.

**Interrupt output**  
Interrupt pin to the MCU for link changes.

**EEPROM autoload**  
Optional I²C EEPROM for configuration at power-up, so the switch can be set up without the MCU.

**Linux driver**  
Upstream DSA driver. A good register reference for bare-metal MCU firmware.

**Register documentation**  
Where the register-level details come from.

**CPU core**  
On-chip processor besides the switch fabric.  
RTL8363NB has none; it is configured only by an external CPU or EEPROM.  
YT9215S: the datasheet says only "RISC-V microprocessor" and doesn't name the core.

**CPU clock**  
Not given in any public datasheet.

**CPU memory**  
On-chip instruction and data RAM/ROM sizes.  
RTL8367S: code is copied into "8051 instruction memory" at reset; its size isn't given.

**Code storage**  
Where the CPU loads its code from at reset.  
RTL8367S: with DISAUTOLOAD=0 and DIS_8051=0, code comes from the EEPROM, or from SPI flash when EN_SPIF=1.  
YT9215S: two SPI flash ports, selected by SPF_MUX_SEL.

**Disable strap**  
Strap pin that turns the CPU off at power-up.  
With the CPU off, the switch runs as a plain hardware switch configured by EEPROM or SMI.

**Internal CPU port**  
Switch port the embedded CPU uses to send and receive frames.  
The Linux yt921x driver lists port 10 as the MCU port.

**SDK**  
Firmware toolkit for the embedded CPU.  
Realtek's unmanaged-switch SDK is NDA-only.  
Community firmware (RTLPlayground, SDCC) runs on the 8051 in the RTL8372/RTL8373, a different family, so the RTL8367S 8051 is probably programmable but undocumented.

**Useful here**  
Could the embedded CPU replace the adapter MCU?  
No: none has USB, and none is documented well enough to write firmware for. Leave it disabled.

**MAC address table**  
Learned MAC entries.

**VLAN table**  
802.1Q VLAN entries.

**Jumbo frames**  
Maximum frame forwarded at wire speed.  
The YT9215S datasheet says 9 KB, which is the same 9,216 B.

**Priority queues**  
Egress queues per port.

**ACL rules**  
Hardware ACL entries (L2/L3/L4 match).

**Link aggregation**  
802.3ad groups.  
Not needed for this adapter.

**Port mirroring**  
Copy traffic to a monitor port.

**IGMP/MLD snooping**  
Multicast snooping in hardware.

**LLDP / OAM**  
Hardware LLDP or OAM support listed in the datasheet.  
For this adapter LLDP is sent by the MCU anyway.

**EEE (802.3az)**  
Energy-Efficient Ethernet: saves power on idle links.

**Cable diagnostics**  
Cable fault/length test, readable by the MCU.

**LEDs**  
LED outputs.

**Other PHY features**  
Notable extras.

**Package**  
Package and body size.

**Body area**  
Package body area in mm². The LQFP leads add about 1 mm on each side.

**Supply**  
Input rails.  
All three generate the 1.1 V core from 3.3 V with an on-chip switching regulator and an external inductor.

**Clock**  
Reference clock.

**Power draw**  
Typical power with 2 GbE links up.  
None of the public datasheets give a figure; this needs measuring and counts against the PoE budget.

**Operating temp.**  
Ambient operating range.

**Crystal**  
Reference crystal and its load capacitors.  
Load-capacitor values aren't given in the public datasheets; use the crystal maker's values.  
RTL8367S: put a 150 Ω resistor in series between XTALO and the crystal.

**Oscillator option**  
Instead of a crystal, drive XTALI from a 3.3 V 25 MHz oscillator and leave XTALO floating.  
One YT9215 design note fixed SGMII errors by moving to a ±10 ppm TCXO.

**Buck inductor**  
Inductor on the LX pins of the internal 3.3 V to 1.1 V switching regulator.  
Only the RTL8367S public datasheet gives the value. RTL8363NB's is in §11.5, which is missing from the public copy.

**Buck capacitors**  
Bulk capacitors for the switching regulator.

**EN_SWR resistor**  
Pull-up that enables the internal switching regulator.

**Bias resistor**  
Precision resistor that sets the PHY bias current.

**Reset**  
nRESET circuit.  
Realtek parts have an internal 75 kΩ pull-up, so the MCU can drive nRESET directly.  
YT9215S needs an external pull-up; a design note asks for at least 10 ms low at reset.

**Strap resistors**  
Each strap pin is left floating or tied through a resistor.  
YT9215S: three reserved pins must also be pulled up to DVDDIO.

**Unused MAC inputs**  
Pull-downs on unused RGMII/MII receive inputs of the extension port.

**Interrupt pin**  
External resistor on the interrupt output.  
RTL8367S: 1 kΩ pull-down for active-high, or 4.7 kΩ pull-up for active-low.

**EEPROM**  
Optional I²C configuration EEPROM.  
A strap selects 24C02–24C16 or 24C32 and up. With an MCU on SMI it can be left off.

**SPI flash**  
Optional SPI flash for the embedded CPU's code.

**MDI termination**  
All three have 100 Ω termination on-chip, so no external termination resistors are needed.

**Magnetics**  
Gigabit transformers for the two RJ45 ports the passthrough needs.  
The PoE side needs PoE-rated magnetics with centre taps. Unused PHYs need none.

**LED resistors**  
One series resistor per LED, if LEDs are fitted. LED polarity follows the strap pull direction.

**Decoupling**  
Per-pin decoupling values.  
Not given in the public datasheets. A YT9215 design note recommends a π filter on AVDD.

**MCU attach**  
How the adapter MCU joins the network.

**Main advantage**  
Why you would choose it.

**Main risk**  
What to check before committing.

## Sources

- RTL8363NB-VB-CG datasheet Rev. 1.2 (2018), via LCSC.
- RTL8367S-CG preliminary datasheet (Rev. Pre-0.941, 2016).
- YT9215S draft datasheet via LCSC; YT9215SC DRAFT_07 (2023) for the second SerDes.
- Linux yt921x DSA driver patches (MCU port 10).
- RTLPlayground (community 8051 firmware for RTL8372/RTL8373, SDCC).
- CSDN design note on RK3568 + YT9215 (crystal, reset, AVDD filtering).
