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

| Part | GbE PHYs | Extra MAC(s) | Host mgmt | Pkg | LCSC price (1 / ~30 / volume) | Stock | JLCPCB |
|---|---|---|---|---|---|---|---|
| **Realtek RTL8363NB-VB-CG** | 2 | 1 × RGMII/MII/RMII/TMII | SMI, I²C-like slave | QFN-76 9×9 | $2.61 / $1.96 / $1.43 (1k) | 1,562 | C2835942, extended |
| Realtek RTL8367S-CG | 5 | SGMII/HSGMII + RGMII/MII | SMI, SPI slave | LQFP-128 14×14 | $2.67 / $1.98 / $1.49 (990) | 4,648 | C2760849 |
| Realtek RTL8364NB-VB-CG | ? | — | As RTL8363NB | QFN-88 10×10 | $6.69 / $4.80 / $4.32 (100) | 151 | C3013610, extended |
| **Motorcomm YT9215S** | 5 | SGMII/HSGMII + RGMII/MII/RMII | MDIO slave, I²C slave, UART | LQFP-128-EP 14×14 | $3.98 / $3.22 / $1.92 (900) | 57 | C5899183, extended |
| Motorcomm YT9215SC | 5 | As YT9215S | As YT9215S | LQFP-128 | $4.59 / $3.55 / $2.89 (900) | 115 | via LCSC C51037433 |
| Motorcomm YT9215RBH | 5 | As YT9215S | As YT9215S | LQFP-128 | $13.18 / $10.22 / $9.31 (90) | 83 | via LCSC C5449202 |
| Motorcomm YT9213NB | 2 | 1 | MDIO | ? | not found at LCSC | — | — |
| Microchip KSZ9893RNXI | 2 | 1 × RGMII/MII/RMII | SPI, I²C, MIIM | VQFN-64 | $16.10 / $14.15 / $13.07 (100) | 37 | via LCSC C633484 |

* **RTL8363NB-VB-CG.** SMI is MDC/MDIO. Also has I²C EEPROM autoload and an
  INT pin.
* **RTL8367S-CG.** Also has EEPROM autoload and an embedded 8051
  (strap-disable).
* **RTL8364NB-VB-CG.** More ports, same family as the RTL8363NB; verify the
  port configuration.
* **YT9215S / SC / RBH.** Also have an on-chip RISC-V core, SPI flash and
  EEPROM. The RBH is the −40…85 °C part.
* **YT9213NB.** Same family as the YT9215.

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

| MCU | Data path to switch | Can send frames? |
|---|---|---|
| **WCH CH32V307 / CH32V317** | Native MAC → RMII/MII ext port | Yes |
| **WCH CH32V208** | Built-in 10BASE-T PHY → copper port | Yes |
| **RP2040 / RP2350** | PIO RMII at 10 Mbit/s | Yes, low throughput |
| **CH32V003 / any MCU** | None (SMI/I²C management only) | No |

* **CH32V307 / CH32V317.** Cleanest. The native Ethernet MAC connects by
  RMII/MII to the RTL8363NB ext port and talks to the switch as if it were a
  PHY (point RMII/MII at the switch's PHY-mode). WCH ships a TCP/IP lib (and
  lwIP ports exist). It has a built-in 10BASE-T PHY too, unused here.
* **CH32V208.** Its MAC is (as far as I know; not verified here) only wired
  to the internal 10M PHY, so it needs a **copper** switch port: use the
  YT9215S / RTL8367S (spare PHYs), with capacitor coupling and no magnetics
  on a short on-board trace. Wastes a GbE PHY, but no extra parts.
* **RP2040 / RP2350.** Community PIO-RMII drivers exist. There is no MAC, so
  PIO + CPU does framing/CRC. Fine for LLDP + a little management traffic;
  not for throughput.
* **CH32V003 / any MCU.** Reads link state and counters, sets config. Cannot
  send LLDP or be reachable on the network.

A practical split, matching `poe.md` §6.3: a tiny CH32V003‑class part does the
PoE signature/classification from cold start; the switch plus a CH32V307 (or
RP2040) come up after the hot‑swap FET closes and handle networking, LLDP and
USB‑PD reporting. With an Ethernet‑capable MCU the adapter can now do **LLDP
power negotiation**, which `poe.md` §4.5 said a passive passthrough could not.

## 4a. Chinese alternatives (follow-up, 2026‑10‑21)

Short answer: **none of them is cheaper than the RTL8363NB at JLCPCB/LCSC
today.** The domestic gigabit switch vendors are Motorcomm (裕太微) and JLSemi
(景略). Only Motorcomm parts are stocked at LCSC/JLCPCB.

| Vendor / part | Config | Mgmt / CPU port | At LCSC/JLCPCB? | Verdict |
|---|---|---|---|---|
| Motorcomm **YT9215S** | 5 GbE PHY + 2 MAC | MDIO/I²C slave | Yes, C5899183 | Cheapest buyable |
| Motorcomm **YT9213NB** | 2 GbE PHY + 1 MAC | MDIO | No | RTL8363NB equivalent |
| Motorcomm YT9214NB | 2 GbE PHY + 2 MAC | MDIO | No | YT9213NB + second MAC |
| JLSemi **JL6107-PC / JL6107S-PC / JL6107SC** | 5 GbE + 2 ext | Managed | No | Pin compatibility unverified |
| JLSemi JL6105-NC | 5 GbE | **Unmanaged, no CPU port** | No | Useless here |
| JLSemi JL6110 | 8 + 2 | Managed | — | Too big |
| JLSemi JL5104 / JL5106C | 4–5 port | MII/RMII | — | 100 Mbit only |

* **YT9215S.** CPU port is RGMII/MII/RMII + SGMII, with an on-chip RISC-V.
  LCSC/JLCPCB price: $3.98 @1, $2.12 @90, $1.92 @900. The cheapest Chinese
  option that's actually buyable. Still ~35 % dearer than the RTL8363NB at
  volume and 4× the board area (LQFP-128).
* **YT9213NB.** Same family as the YT9215. Not found at LCSC/JLCPCB or
  szlcsc. The exact RTL8363NB equivalent. Has upstream Linux `yt921x`
  support. A price would need a Motorcomm distributor quote.
* **YT9214NB.** Not found. Same as the YT9213NB with a second MAC.
* **JL6107-PC / JL6107S-PC / JL6107SC.** Ext ports are RGMII/MII/RMII and
  SGMII. Not at LCSC/JLCPCB; distributor VOOHU; no public price. Marketed as
  pin-compatible drop-ins for the RTL8367RB / RTL8367S / RTL8367SC. The pin
  compatibility claims are unverified.
* **JL6105-NC.** Not at LCSC. The MCU can't attach to it or manage it.
* **JL5104 / JL5106C.** Fail the GbE requirement.

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
