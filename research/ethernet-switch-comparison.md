# Switch IC comparison table

Prices and stock were read from LCSC product pages on 2026-10-22 (JLCPCB assembly uses the same C-numbers and LCSC stock). The table holds the data of the **Switches** tab in the comparison sheet; background and design reasoning are in [`ethernet-switch.md`](ethernet-switch.md), [`gigabit-piggyback.md`](gigabit-piggyback.md) and [`bitbang-10mbit-ethernet.md`](bitbang-10mbit-ethernet.md).

The sheet is the [comparison sheet](https://docs.google.com/spreadsheets/d/1nPsWa2ZrP8suhqZF9iXVH5w3_iRSPm5tRze83cas7SA/edit#gid=1).

## TL;DR

* **RTL8363NB-VB-CG is the pick** ($1.96 @100 on the 30+ break, $1.48 @1k, 1,562 in stock): 2 GbE PHYs + 1 RGMII, MII, RMII or TMII MAC is exactly the passthrough shape, QFN-76 9×9, single 3.3 V rail, works unmanaged from straps.
* **At 100 pcs the RTL8367S is $0.30 cheaper** ($1.67, 90+ break) and the same price at 1k. It has 3 spare GbE PHYs (idle power) and an LQFP-128 about 2.5× the area, but its spare copper PHY would let a CH32V208 (built-in 10M PHY) or RP2040 PIO 10BASE-T attach cap-coupled. Worth a power check before choosing for a 100-unit run.
* **YT9215S** ($2.12 @100, $1.92 @1k) is the only Chinese gigabit switch buyable at LCSC and JLCPCB: a second source, but only 57 in stock.
* **100M (10/100) switches are cheaper** (IP175G $0.85) but fail the ≥1 Gbit/s passthrough requirement.
* **YT9213NB** (Motorcomm's exact RTL8363NB equivalent) and **JLSemi JL6107** aren't listed at LCSC and JLCPCB; they'd need distributor quotes and consigning.

## Table

| Part | Vendor | LCSC | Datasheet | Pkg | Body size | $ @100 | Price tier | $ @1k | Stock | vs RTL8363NB | Speed | PHYs | Ext MACs | RGMII | MII | RMII | TMII | SerDes lanes | SerDes rate | Spare PHY | SMI | I²C | SPI | UART | CPU | Strap boot | Linux driver | Driver type | JLC | Supply | Core rail | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IP175G | IC Plus | [C80220](https://www.lcsc.com/product-detail/C80220.html) | [PDF](https://www.lcsc.com/datasheet/C80220.pdf) | QFN-48 | 6×6 mm | $0.853 | 100+ | $0.671 | 3,241 | -$1.109 | 100M | 5 | ? | ? | ? | ? | ? | 0 | None | Yes | ? | ? | ? | ? | None | Yes | ? | ? | ? | 3.3 V | Not listed | Too slow |
| RTL8367S-CG | Realtek | [C2760849](https://www.lcsc.com/product-detail/C2760849.html) | [PDF](https://www.lcsc.com/datasheet/C2760849.pdf) | LQFP-128 | 14×14 mm | $1.665 | 90+ | $1.490 | 4,576 | -$0.297 | 1000M | 5 | 2 | Yes | Yes | No | No | 1 | 2.5 Gbit/s | Yes | SMI | Not listed | Yes | Not listed | 8051 | Yes | rtl8365mb | DSA | Extended | 3.3 V | int. 1.1 V buck | Candidate |
| RTL8305NBI-VB-CG | Realtek | [C42451794](https://www.lcsc.com/product-detail/C42451794.html) | [PDF](https://www.lcsc.com/datasheet/C42451794.pdf) | QFN-48 | 6×6 mm | $1.725 | 100+ | $1.595 | 2,552 | -$0.237 | 100M | 5 | ? | ? | ? | ? | ? | 0 | None | Yes | SMI | Not listed | Not listed | Not listed | None | Yes | ? | ? | ? | 3.3 V | Not listed | Too slow |
| RTL8363NB-VB-CG | Realtek | [C2835942](https://www.lcsc.com/product-detail/C2835942.html) | [PDF](https://www.lcsc.com/datasheet/C2835942.pdf) | QFN-76 | 9×9 mm | $1.962 | 30+ | $1.476 | 1,562 | $0.000 | 1000M | 2 | 1 | Yes | Yes | Yes | Yes | 0 | None | No | SMI | I²C-like | Not listed | Not listed | None | Yes | rtl8365mb | DSA | Extended | 3.3 V | int. 1.1 V buck | Pick |
| YT9215S | Motorcomm | [C5899183](https://www.lcsc.com/product-detail/C5899183.html) | [PDF](https://www.lcsc.com/datasheet/C5899183.pdf) | LQFP-128-EP | 14×14 mm | $2.116 | 90+ | $1.922 | 57 | +$0.154 | 1000M | 5 | 2 | Yes | Yes | Yes | No | 1 | 2.5 Gbit/s | Yes | MDIO | Yes | Not listed | Yes | RISC-V | ? | yt921x | DSA | Extended | 3.3 V | int. 1.1 V buck | Candidate |
| YT9215SC | Motorcomm | [C51037433](https://www.lcsc.com/product-detail/C51037433.html) | [PDF](https://www.lcsc.com/datasheet/C51037433.pdf) | LQFP-128-EP | 14×14 mm | $3.154 | 90+ | $2.889 | 115 | +$1.192 | 1000M | 5 | ? | Yes | Yes | Yes | No | 2 | 2.5 Gbit/s | Yes | MDIO | Yes | Not listed | Yes | RISC-V | ? | yt921x | DSA | ? | 3.3 V | int. 1.1 V buck | Too dear |
| KSZ8863RLLI | Microchip | [C631675](https://www.lcsc.com/product-detail/C631675.html) | [PDF](https://www.lcsc.com/datasheet/C631675.pdf) | LQFP-48 | 7×7 mm | $3.189 | 30+ | $2.598 | 1,334 | +$1.227 | 100M | 2 | ? | No | Yes | Yes | No | 0 | None | No | SMI | Yes | Yes | Not listed | None | Yes | ksz8 | DSA | ? | 3.3 V | Not listed | Too slow |
| RTL8364NB-VB-CG | Realtek | [C3013610](https://www.lcsc.com/product-detail/C3013610.html) | [PDF](https://www.lcsc.com/datasheet/C3013610.pdf) | QFN-88 | 10×10 mm | $4.316 | 100+ | $4.316 | 151 | +$2.354 | 1000M | ? | ? | ? | ? | ? | ? | ? | ? | ? | SMI | I²C-like | Not listed | Not listed | None | Yes | ? | ? | Extended | ? | ? | Too dear |
| YT9215RBH | Motorcomm | [C5449202](https://www.lcsc.com/product-detail/C5449202.html) | [PDF](https://www.lcsc.com/datasheet/C5449202.pdf) | LQFP-128 | 14×14 mm | $9.308 | 90+ | $9.308 | 83 | +$7.346 | 1000M | 5 | 2 | Yes | Yes | Yes | No | ? | ? | Yes | MDIO | Yes | Not listed | Yes | RISC-V | ? | yt921x | DSA | ? | 3.3 V | Not listed | Too dear |
| KSZ9893RNXI | Microchip | [C633484](https://www.lcsc.com/product-detail/C633484.html) | [PDF](https://www.lcsc.com/datasheet/C633484.pdf) | VQFN-64 | 8×8 mm | $13.067 | 100+ | $13.067 | 37 | +$11.105 | 1000M | 2 | 1 | Yes | Yes | Yes | No | 0 | None | No | MIIM | Yes | Yes | Not listed | None | Yes | ksz9477 | DSA | ? | ? | ? | Too dear |
| RTL8305NB-CG | Realtek | [C52146](https://www.lcsc.com/product-detail/C52146.html) | [PDF](https://www.lcsc.com/datasheet/C52146.pdf) | QFN-48 | 6×6 mm | ? | ? | $0.845 | 0 | ? | 100M | 5 | ? | ? | ? | ? | ? | 0 | None | Yes | SMI | Yes | Not listed | Not listed | None | Yes | ? | ? | ? | 3.3 V | Not listed | Too slow |
| YT9213NB | Motorcomm | None | None | ? | ? | ? | ? | ? | None | ? | 1000M | 2 | ? | ? | ? | ? | ? | ? | ? | No | MDIO | Not listed | Not listed | Not listed | ? | ? | yt921x | DSA | None | ? | ? | Not listed |
| JL6107-PC | JLSemi | None | None | ? | ? | ? | ? | ? | None | ? | 1000M | 5 | ? | Yes | Yes | Yes | No | ? | ? | Yes | ? | ? | ? | ? | ? | ? | ? | ? | None | ? | ? | Not listed |

## Why the Pick and Candidates

* **RTL8367S-CG (Candidate)**: Cheapest gigabit switch at 100 pcs ($1.67 vs $1.96 for the RTL8363NB). Same driver family as the RTL8363NB, so firmware carries over. Its spare copper PHYs allow a cap-coupled MCU port (e.g. CH32V208 built-in PHY or PIO 10BASE-T). Loses on size and idle power: 3 unused PHYs and LQFP-128.
* **RTL8363NB-VB-CG (Pick)**: Exact port count: 2 GbE PHYs + 1 MAC, no wasted PHYs. Smallest package (QFN-76 9×9) and a single 3.3 V rail. Cheapest gigabit option at 1k ($1.48). RMII or MII to the MCU, so a CH32V307 MAC or RP2040 PIO RMII plugs straight in. Well stocked (1,562) and in the JLCPCB library.
* **YT9215S (Candidate)**: The only Chinese gigabit switch you can buy at LCSC and JLCPCB: a second source to Realtek. Upstream Linux yt921x driver. If Motorcomm provides an SDK, its RISC-V core could do the networking and drop the separate network MCU. Loses on size (LQFP-128), price at 100 and stock (57).

## Per-part notes

* **IP175G**: 5-port 10/100 switch with integrated PHYs. Cheapest switch found, but 100 Mbit/s only, so it fails the ≥1 Gbit/s passthrough requirement. Whether a port can be used as an MII or RMII MAC for the MCU is not confirmed.
* **RTL8367S-CG**: 5 GbE PHYs plus SGMII or HSGMII and RGMII or MII extension ports. Embedded 8051, disabled by strap. Cheaper than the RTL8363NB at 100 pcs because its 90+ break applies; about the same at 1k. But 3 unused GbE PHYs cost power and the LQFP-128 is about 2.5× the board area of the QFN-76.
* **RTL8305NBI-VB-CG**: 5-port 10/100 switch with SMI management, VLAN and QoS. Industrial-temperature version of the RTL8305NB. 100 Mbit/s only, so it fails the ≥1 Gbit/s passthrough requirement.
* **RTL8363NB-VB-CG**: 2 GbE PHYs plus 1 extension MAC: exactly the passthrough shape (PoE side, device side, MCU). The MCU attaches over RMII or MII with no PHY and no magnetics on its side. Managed over slave SMI (MDC and MDIO) or a 2-wire I²C-like bus, plus an interrupt pin. Comes up as a plain learning switch from straps, so the user's link works even if the MCU firmware is dead. Full register docs are under NDA; the GPL rtl8367c API and Linux rtl8365mb driver cover the registers. Power draw not found in the public datasheet (expect a few hundred mW to ~1 W).
* **YT9215S**: 5 GbE PHYs, one RGMII, MII or RMII port and one SGMII or HSGMII SerDes. On-chip RISC-V MCU with SPI flash interface; can be disabled by strap. The public datasheet is a draft and says nothing about the RISC-V core's SDK. Only 57 in stock.
* **YT9215SC**: YT9215S variant; LCSC gives no functional difference. About 50 % dearer than the YT9215S.
* **KSZ8863RLLI**: 3-port 10/100 switch: 2 PHYs + 1 MII or RMII MAC, the same shape as the RTL8363NB. Well documented (open datasheet). 100 Mbit/s only, so it fails the ≥1 Gbit/s passthrough requirement, and dearer than the gigabit RTL8363NB anyway.
* **RTL8364NB-VB-CG**: Same family as the RTL8363NB with more ports; exact configuration not verified. More than twice the RTL8363NB's price.
* **YT9215RBH**: Industrial-temperature (−40…85 °C) YT9215 variant with two extra MAC ports. About 4–5× the YT9215S price.
* **KSZ9893RNXI**: The nicely documented 3-port GbE part: open datasheet, SPI, I²C or MDIO management. 6–9× the RTL8363NB's price. Only worth it if Realtek's NDA documentation becomes a blocker.
* **RTL8305NB-CG**: Commercial-temperature RTL8305NB. Out of stock at LCSC; $0.845 is LCSC's 'from' price, tier not shown. 100 Mbit/s only.
* **YT9213NB**: The exact Motorcomm equivalent of the RTL8363NB: 2 GbE PHYs + 1 MAC. Not found at LCSC, JLCPCB or szlcsc. Price needs a Motorcomm distributor quote; it would then be consigned to JLCPCB.
* **JL6107-PC**: 5 GbE PHYs + 2 extension ports (RGMII, MII or RMII, SGMII). Marketed as a pin-compatible drop-in for the RTL8367RB and RTL8367S; that claim is unverified. Not at LCSC and JLCPCB; sold via the distributor VOOHU with no public price.

## Caveats

* "@100" is the LCSC break that applies to an order of 100 (e.g. 90+ or 30+ where there's no 100+ break). Out-of-stock parts show LCSC's 'from' price in the @1k column.
* ? = not confirmed. Not listed = the public datasheet does not list it. RTL8364NB port configuration, several supply rails, and the JLCPCB library status of the non-Realtek parts were not checked.
* Power draw for the RTL8363NB and RTL8367S wasn't in the public datasheets; it matters for the PoE budget and is the main open item.
