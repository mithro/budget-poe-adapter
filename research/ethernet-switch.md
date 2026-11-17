# Cheap ~3-port gigabit switch ICs for the PoE → USB-C adapter

Goal: replace the passive PoE passthrough (see `poe.md` §3) with a tiny
managed switch so the adapter's MCU can sit on the network: report what was
negotiated (PoE class, link speed, USB-PD contract), talk LLDP, expose
counters and settings. Topology:

```
 PoE switch ──RJ45/magnetics── [PHY A] ┐
                                       ├─ switch IC ── [PHY B] ──magnetics/RJ45── Pi / device
                 adapter MCU ── RMII/MII (or a 3rd copper port) ┘
```

Two gigabit copper ports carry the user's traffic; the MCU port only needs
≤10 Mbit/s. Prices are LCSC (the part source JLCPCB assembly draws from),
checked 2026‑10‑21. **[LCSC]**/**[JLC]** links are in §6.

## 1. TL;DR

* **Pick: Realtek RTL8363NB‑VB‑CG.** Exactly the right shape: 2 × 10/100/1000
  PHYs + 1 extension MAC that does **RGMII / MII / RMII / TMII**, QFN‑76
  9 × 9 mm, single 3.3 V input (built‑in 1.1 V switching regulator), 25 MHz
  crystal. **$2.61 @1, $1.96 @30, $1.43 @1k**, 1,562 in stock at LCSC; listed
  in the JLCPCB assembly library as C2835942 (extended part).
* The MCU plugs into the extension port over **RMII/MII with no PHY and no
  magnetics on the MCU side**. Management is over slave **SMI (MDC/MDIO)** or
  a Realtek I²C‑like 2‑wire bus (strap‑selected), both trivial to bit‑bang
  from a CH32V/RP2040, plus an interrupt pin for link changes.
* Runner‑up / second source: **Motorcomm YT9215S** (5 GbE PHY + 2 MAC,
  LQFP‑128, $3.98 @1, $1.92 @900, in the JLCPCB library as C5899183). Bigger
  and more pins, but cheap at volume, has an on‑chip RISC‑V MCU, and has an
  upstream Linux DSA driver (`yt921x`). Motorcomm's exact‑fit **YT9213NB**
  (2 PHY + 1 MAC) exists but I found no LCSC/JLCPCB listing.
* The Microchip **KSZ9893** is the "nicely documented" 3‑port GbE part
  (SPI/I²C/MDIO management, open datasheet) but costs **$13–16** at LCSC: 6–10×
  the Realtek part. Only worth it if Realtek's NDA‑ish documentation becomes
  a blocker.
* NextPCB: their parts arm (HQ Online) blocks automated lookup, so I could not
  confirm stock. They source from the Shenzhen market where RTL8363NB/RTL8367S
  are common; check by hand before committing (see §5).

## 2. Candidates

| Part | GbE PHYs | Ext MACs | SGMII | HSGMII | RGMII | MII | RMII | TMII |
|---|---|---|---|---|---|---|---|---|
| **Realtek RTL8363NB-VB-CG** | 2 | 1 | – | – | Yes | Yes | Yes | Yes |
| Realtek RTL8367S-CG | 5 | 2 | Yes | Yes | Yes | Yes | – | – |
| Realtek RTL8364NB-VB-CG | More (verify) | — | — | — | — | — | — | — |
| **Motorcomm YT9215S** | 5 | 2 | Yes | Yes | Yes | Yes | Yes | – |
| Motorcomm YT9215SC | 5 | As YT9215S | As YT9215S | As YT9215S | As YT9215S | As YT9215S | As YT9215S | – |
| Motorcomm YT9215RBH | 5 | As YT9215S | As YT9215S | As YT9215S | As YT9215S | As YT9215S | As YT9215S | – |
| Motorcomm YT9213NB | 2 | 1 | – | – | – | – | – | – |
| Microchip KSZ9893RNXI | 2 | 1 | – | – | Yes | Yes | Yes | – |

Management from an external MCU, and what else is on the chip:

| Part | MDIO | I²C | SPI | UART | EEPROM | INT pin | On-chip CPU | SPI flash | Temp. range |
|---|---|---|---|---|---|---|---|---|---|
| **Realtek RTL8363NB-VB-CG** | SMI (MDC/MDIO) | I²C-like slave | – | – | I²C autoload | Yes | – | – | – |
| Realtek RTL8367S-CG | SMI (MDC/MDIO) | – | Slave | – | Yes | – | 8051 (strap-disable) | – | – |
| Realtek RTL8364NB-VB-CG | As RTL8363NB | As RTL8363NB | – | – | – | – | – | – | – |
| **Motorcomm YT9215S** | Slave | Slave | – | Yes | Yes | – | RISC-V | Yes | – |
| Motorcomm YT9215SC | As YT9215S | As YT9215S | – | As YT9215S | Yes | – | RISC-V | Yes | – |
| Motorcomm YT9215RBH | As YT9215S | As YT9215S | – | As YT9215S | Yes | – | RISC-V | Yes | −40…85 °C |
| Motorcomm YT9213NB | Yes (same family) | – | – | – | – | – | – | – | – |
| Microchip KSZ9893RNXI | MIIM | Yes | Yes | – | – | – | – | – | – |

| Part | Pkg | Body (mm) | $ @1 | $ @~30 | $ @volume | Volume qty | Stock | LCSC part | JLCPCB |
|---|---|---|---|---|---|---|---|---|---|
| **Realtek RTL8363NB-VB-CG** | QFN-76 | 9×9 | $2.61 | $1.96 | $1.43 | 1k | 1,562 | C2835942 | Extended |
| Realtek RTL8367S-CG | LQFP-128 | 14×14 | $2.67 | $1.98 | $1.49 | 990 | 4,648 | C2760849 | Listed |
| Realtek RTL8364NB-VB-CG | QFN-88 | 10×10 | $6.69 | $4.80 | $4.32 | 100 | 151 | C3013610 | Extended |
| **Motorcomm YT9215S** | LQFP-128-EP | 14×14 | $3.98 | $3.22 | $1.92 | 900 | 57 | C5899183 | Extended |
| Motorcomm YT9215SC | LQFP-128 | – | $4.59 | $3.55 | $2.89 | 900 | 115 | C51037433 | Via LCSC |
| Motorcomm YT9215RBH | LQFP-128 | – | $13.18 | $10.22 | $9.31 | 90 | 83 | C5449202 | Via LCSC |
| Motorcomm YT9213NB | ? | – | – | – | – | – | — | Not found | — |
| Microchip KSZ9893RNXI | VQFN-64 | – | $16.10 | $14.15 | $13.07 | 100 | 37 | C633484 | Via LCSC |

Prices are at the qty‑1 / ~30 / largest LCSC break shown. JLCPCB charges a
small loading fee per unique "extended" part per order (no basic switch ICs
exist).

Ruled out: 10/100‑only switches (RTL8305NB, RTL8306E, KSZ8863, IP175) are
cheaper but fail the ≥1 Gbit/s requirement; Marvell 88E6xxx and similar are
far too expensive.

## 3. Why RTL8363NB fits

* **Port count is exact.** 2 copper GbE ports (PoE side, device side) + 1 MAC
  for the MCU. No unused PHYs, so no wasted analog power or pins.
* **Low‑speed MCU port without a PHY.** RMII (50 MHz ref clock, clock‑in or
  clock‑out mode) or MII (MAC or PHY mode) at 10/100. The MCU side needs no
  transformer, no second PHY, and no third RJ45.
* **Small and single‑rail.** QFN‑76 9×9 with on‑chip 3.3→1.1 V buck: one 3.3 V
  rail, an inductor, a 25 MHz crystal.
* **Works unmanaged.** Realtek switches come up as a plain learning switch
  from straps (optionally from an I²C EEPROM). If the MCU firmware is dead the
  user's link still works. This matters because the MCU is also doing PoE
  classification during bring‑up.
* **Software exists.** Realtek's GPL "rtl8367c" switch API (used in OpenWrt
  and many vendor SDKs) covers this chip family. Linux has an upstream DSA
  driver, `drivers/net/dsa/realtek/rtl8365mb.c`, that drives the RTL8363NB /
  RTL8365MB / RTL8367S family. Both are good references for register
  sequences even on a bare‑metal MCU.
* **Caveat:** full Realtek register docs are under NDA. The public datasheet
  covers pins, straps and features; register details come from the GPL code
  above.

What the MCU can do through SMI/I²C: read per‑port link/speed/duplex/autoneg
results, force speeds, read RFC‑style MIB counters, set VLANs/QoS,
mirror ports, disable ports (e.g. hold the device‑side port down until PoE
power is good), use the cable diagnostics, and drive LEDs.

## 4. MCU attachment options

| MCU | MAC | RMII | MII | 10BASE-T PHY | Switch port used | Coupling | Can send frames |
|---|---|---|---|---|---|---|---|
| **WCH CH32V307** | Native | Yes | Yes | Built in (unused here) | RTL8363NB ext port (PHY mode) | Direct | Yes |
| **WCH CH32V317** | Native | Yes | Yes | Built in (unused here) | RTL8363NB ext port (PHY mode) | Direct | Yes |
| **WCH CH32V208** | Wired to its PHY only | – | – | Built in | A spare **copper** port | Capacitors | Yes |
| **RP2040** | None (PIO) | 10 Mbit/s | – | – | RMII ext port | Direct | Yes |
| **RP2350** | None (PIO) | 10 Mbit/s | – | – | RMII ext port | Direct | Yes |
| **CH32V003** | None | – | – | – | None | – | No |
| **Any other MCU** | None | – | – | – | None | – | No |

| MCU | Property | Value |
|---|---|---|
| CH32V307 / CH32V317 | Rating | Cleanest |
| CH32V307 / CH32V317 | How the MAC sees the switch | As a PHY |
| CH32V307 / CH32V317 | Software 1 | WCH TCP/IP lib |
| CH32V307 / CH32V317 | Software 2 | lwIP ports |
| CH32V208 | MAC wiring | Not verified here |
| CH32V208 | Switch with spare PHYs, option 1 | YT9215S |
| CH32V208 | Switch with spare PHYs, option 2 | RTL8367S |
| CH32V208 | Magnetics | None |
| CH32V208 | Trace | Short (on-board) |
| CH32V208 | Cost | Wastes a GbE PHY |
| CH32V208 | Extra parts | None |
| RP2040 / RP2350 | Software | Community PIO-RMII drivers |
| RP2040 / RP2350 | Framing and CRC | Done by PIO + CPU |
| RP2040 / RP2350 | Good for 1 | LLDP |
| RP2040 / RP2350 | Good for 2 | A little management traffic |
| RP2040 / RP2350 | Not for | Throughput |
| CH32V003 / any MCU | Management bus 1 | SMI |
| CH32V003 / any MCU | Management bus 2 | I²C |
| CH32V003 / any MCU | Can read 1 | Link state |
| CH32V003 / any MCU | Can read 2 | Counters |
| CH32V003 / any MCU | Can set | Config |
| CH32V003 / any MCU | Can send LLDP | No |
| CH32V003 / any MCU | Reachable on the network | No |

The CH32V307's MAC talks to the switch as if the switch were a PHY. The
CH32V208's MAC is, as far as I know (not verified here), only wired to its
internal 10M PHY, which is why it needs a copper port. The RP2040 option is
not for throughput.

A practical split, matching `poe.md` §6.3: a tiny CH32V003‑class part does the
PoE signature/classification from cold start; the switch plus a CH32V307 (or
RP2040) come up after the hot‑swap FET closes and handle networking, LLDP and
USB‑PD reporting. With an Ethernet‑capable MCU the adapter can now do **LLDP
power negotiation**, which `poe.md` §4.5 said a passive passthrough could not.

## 4a. Chinese alternatives (follow-up, 2026‑10‑21)

Short answer: **none of them is cheaper than the RTL8363NB at JLCPCB/LCSC
today.** The domestic gigabit switch vendors are Motorcomm (裕太微) and JLSemi
(景略). Only Motorcomm parts are stocked at LCSC/JLCPCB.

| Vendor | Part | GbE PHYs | Ext ports | Managed | MDIO | I²C | RGMII | MII | RMII | SGMII | On-chip CPU | Sold as drop-in for |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Motorcomm | **YT9215S** | 5 | 2 | Yes | Slave | Slave | Yes | Yes | Yes | Yes | RISC-V | – |
| Motorcomm | **YT9213NB** | 2 | 1 | Yes | Yes | – | – | – | – | – | – | – |
| Motorcomm | YT9214NB | 2 | 2 | Yes | Yes | – | – | – | – | – | – | – |
| JLSemi | **JL6107-PC** | 5 | 2 | Yes | – | – | Yes | Yes | Yes | Yes | – | RTL8367RB |
| JLSemi | **JL6107S-PC** | 5 | 2 | Yes | – | – | Yes | Yes | Yes | Yes | – | RTL8367S |
| JLSemi | **JL6107SC** | 5 | 2 | Yes | – | – | Yes | Yes | Yes | Yes | – | RTL8367SC |
| JLSemi | JL6105-NC | 5 | **None** | **No** | – | – | – | – | – | – | – | – |
| JLSemi | JL6110 | 8 | 2 | Yes | – | – | – | – | – | – | – | – |
| JLSemi | JL5104 / JL5106C | 4–5 | – | – | – | – | – | Yes | Yes | – | – | – |

The YT9213NB is in the same family as the YT9215.

| Vendor | Part | At LCSC/JLCPCB | LCSC part | $ @1 | $ @90 | $ @900 | Other source | Verdict | Note |
|---|---|---|---|---|---|---|---|---|---|
| Motorcomm | YT9215S | Yes | C5899183 | $3.98 | $2.12 | $1.92 | – | Cheapest buyable Chinese option | ~35 % dearer than RTL8363NB at volume |
| Motorcomm | YT9213NB | No (nor at szlcsc) | – | – | – | – | Motorcomm distributor quote | The exact RTL8363NB equivalent | Upstream Linux `yt921x` support |
| Motorcomm | YT9214NB | No | – | – | – | – | – | YT9213NB with a second MAC | – |
| JLSemi | JL6107 family | No | – | – | – | – | Distributor VOOHU (no public price) | Pin compatibility claims unverified | – |
| JLSemi | JL6105-NC | No | – | – | – | – | – | Useless here | The MCU has no port to attach to |
| JLSemi | JL6110 | — | – | – | – | – | – | Too big | – |
| JLSemi | JL5104 / JL5106C | — | – | – | – | – | – | Fails the GbE requirement | 100 Mbit only |

The YT9215S also takes 4× the board area of the RTL8363NB (LQFP-128).

JLSemi's selection guide mentions a "3+1" port gigabit part, but I couldn't
find a part number for it. If it exists, it would be the other Chinese
RTL8363NB equivalent.

Takeaways:
* **For JLCPCB assembly, RTL8363NB stays the cheapest and smallest choice.**
  YT9215S is the only Chinese part you can buy there today. It's a reasonable
  second source if a single‑vendor Realtek BOM is a concern.
* Unit price for YT9213NB or a JLSemi 3+1 part could come in below
  $1.4. That would need direct quotes (Motorcomm / VOOHU for JLSemi), and they
  would have to be consigned to JLCPCB/NextPCB as customer‑supplied parts.
* Keep the RMII/MDIO design vendor‑neutral (strap‑free management, RMII to
  the MCU). Then a YT9213NB swap later only changes the footprint and driver.

Sources for this section:
* JLSemi switch selection guide (BigGo): https://finance.biggo.com.tw/news/irXqrp0Bh5an-7Gh2XnU
* JL6107/JL6110 pin‑compatibility article: https://damodev.csdn.net/6a4332fb10ee7a33f2844cb5.html
* VOOHU JL6105 page: https://www.voohuele.com/jl6105-series/
* JL6107‑PC as RTL8367RB replacement (CSDN): https://blog.csdn.net/Maryfang/article/details/154916461
* Motorcomm YT921x variants (Linux binding): https://www.kernel.org/doc/Documentation/devicetree/bindings/net/dsa/motorcomm%2Cyt921x.yaml

## 5. Open items

* **Power draw.** I did not find a datasheet power figure for RTL8363NB in the
  pages reached. Expect a few hundred mW to ~1 W with two GbE links up; this
  comes out of the PoE budget and must be counted before MPS/inrush design.
* **NextPCB / HQ Online availability** could not be checked automatically
  (site blocks robots). Search RTL8363NB‑VB‑CG, RTL8367S‑CG, YT9215S there by
  hand. HQ Online does list other Realtek Ethernet parts (RTL8201F, RTL8309M).
* **RTL8363NB vs RTL8363SB/SC**: the SB/SC variants add SGMII/HSGMII on the
  extension port; not needed here, and they were not found at LCSC.
* **YT9213NB**: worth asking Motorcomm distributors; same family as the
  YT9215 with upstream Linux support, and the right port count.
* Layout: two sets of GbE magnetics are still needed (one per jack), plus the
  PoE centre‑tap extraction on the input side as in `poe.md` §3 option 1.

## 6. Sources

* [LCSC] RTL8363NB‑VB‑CG, C2835942: https://www.lcsc.com/product-detail/C2835942.html
* [JLC] RTL8363NB‑VB‑CG: https://jlcpcb.com/partdetail/RealtekSemicon-RTL8363NB_VBCG/C2835942
* RTL8363NB‑VB‑CG datasheet (rev 1.2): https://atta.szlcsc.com/upload/public/pdf/source/20240423/989DCAA6328F19215A910B22766A32D7.pdf
* [LCSC] RTL8367S‑CG, C2760849: https://lcsc.com/product-detail/image/RTL8367S-CG_C2760849.html
* RTL8367S datasheet: https://www.framboise314.fr/wp-content/uploads/2021/06/RTL8367S-CG_Datasheet.pdf
* [LCSC] RTL8364NB‑VB‑CG, C3013610: https://www.lcsc.com/product-detail/C3013610.html
* [JLC] RTL8364NB‑VB‑CG: https://jlcpcb.com/partdetail/RealtekSemicon-RTL8364NB_VBCG/C3013610
* [LCSC] YT9215S, C5899183: https://www.lcsc.com/product-detail/C5899183.html
* [JLC] YT9215S: https://jlcpcb.com/partdetail/YT9215S/C5899183
* YT9215S datasheet: https://atta.szlcsc.com/upload/public/pdf/source/20230829/432918AE041FF2F1E459558942DE4628.pdf
* [LCSC] YT9215SC, C51037433: https://www.lcsc.com/product-image/C51037433.html
* [LCSC] YT9215RBH, C5449202: https://www.lcsc.com/product-detail/C5449202.html
* Linux YT921x DSA binding (variant list incl. YT9213NB): https://www.kernel.org/doc/Documentation/devicetree/bindings/net/dsa/motorcomm%2Cyt921x.yaml
* Linux RTL8365MB DSA driver: https://codebrowser.dev/linux/linux/drivers/net/dsa/realtek/rtl8365mb.c.html
* [LCSC] KSZ9893RNXI, C633484: https://www.lcsc.com/product-image/C633484.html
* HQ Online (NextPCB) Realtek listing example: https://www.hqonline.com/product-detail/ethernet-transceiver--phy--realtek-rtl8201f-vb-cg-2500277426
