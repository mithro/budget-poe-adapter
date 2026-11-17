# Bit-banging 10 Mbit/s Ethernet

Question: can the adapter's MCU get onto Ethernet with no MAC/PHY silicon of
its own, either by driving 10BASE-T on the wire straight from GPIO, or by
running the MAC in software (RP2040 PIO) against an external PHY or a switch
port? Context: price cap is the RP2040 (~$0.79 @100); see
`risc-v-mcu-comparison.md`, `gigabit-piggyback.md` and `ethernet-switch.md`.

Requirement (Tim, 2026-10-22): **10 Mbit/s is fully acceptable** for the MCU's
own network link, so the 10M-only limits below are not a problem.

Researched 2026-10-22. Prices are LCSC, read live where marked **[live]**.
Spec numbers marked **[802.3]** are from IEEE 802.3 clause 14 (10BASE-T) as I
remember them, not re-read for this note.

## 1. TL;DR

* **Bit-banged 10 Mbit/s Ethernet works today on an RP2040, both ways.**
  Direct on the wire: a PIO 10BASE-T MAC+PHY with lwIP, 2 GPIOs for TX,
  1 GPIO for RX, measured 5–7 Mbit/s TCP ([holysnippet/pico_eth_doc]).
  Via a PHY: PIO RMII to a LAN8720 at 10 Mbit/s, with lwIP
  ([sandeepmistry/pico-rmii-ethernet]) or Mongoose ([Mongoose pico-rmii]).
  Nobody has a working *receive* at 100 Mbit/s in software; Steve Markgraf's
  100BASE-TX is transmit-only ([Pico-100BASE-TX]).
* **The problem in this product is not the bit-banging, it is the link
  partner.** The adapter is a gigabit passthrough. A 1000BASE-T link uses all
  four pairs in both directions, so there is no wire on the PoE cable that a
  bit-banged 10BASE-T port could talk on (see `gigabit-piggyback.md` §1, §4).
  A bit-banged port needs something on the board to talk to, and that means
  the 3-port switch from `ethernet-switch.md`.
* **Best fit: PIO MAC to the switch's extension MAC port, with no PHY at all.**
  The RTL8363NB's extension port speaks RMII/MII in PHY mode, so an RP2040
  can run the existing PIO RMII code (or a simpler MII variant at 10 Mbit/s)
  straight into it. That replaces the CH32V307 in the switch design for
  $0 of extra silicon, which is the "RP2040 on RMII" trim already costed in
  `gigabit-piggyback.md` §3 (≈ −$0.40). This is the recommendation.
* **Direct 10BASE-T from GPIO into a switch copper port also works on paper**
  (cap-coupled, no magnetics, on-board trace), but the RTL8363NB has no spare
  copper PHY, so it needs a bigger switch (RTL8367S, YT9215S), which costs
  more than it saves. It also lands in half duplex unless the MCU sends FLP
  autonegotiation bursts (§3.3).
* **A separate, standalone 10/100 port via a cheap PHY** is possible:
  CoreChips SR8201F RMII PHY is **$0.27 @100 / $0.23 @1k [live]**, plus a
  25 MHz crystal and a magjack. It only makes sense as a second cable
  (management port), which the passthrough product doesn't have. If you did
  want that, the WCH CH390H SPI MAC+PHY at ~$0.94 (from
  `risc-v-mcu-comparison.md`) is simpler and frees the PIO.
* **Without PIO (CH32X035, CH32V003), MII at 10 Mbit/s is the only plausible
  bit-bang target.** MII at 10M is a 2.5 MHz nibble clock supplied by the
  PHY/switch, slow enough for timer-triggered DMA to and from a GPIO port on
  a 48 MHz part. I found no one who has done this; it is a research item, not
  a plan (§4.3).

## 2. Options ranked for this adapter

| # | Approach | Link partner on the board | Extra BOM | Proven? | Verdict |
|---|---|---|---|---|---|
| A | **RP2040 PIO RMII/MII → switch ext port** | Switch ext MAC port, PHY mode | $0 | Partly | **Recommended** |
| B | RP2040 PIO 10BASE-T → spare copper port | Switch copper PHY, cap-coupled | ≈ +$0.5–2 | Yes | Costs more than A |
| C | RP2040 PIO RMII → SR8201F PHY → magjack | The user's device | ≈ $0.28 + magjack | Yes | Separate mgmt port only |
| D | RP2040 PIO 10BASE-T → own magjack | Same as C | Magjack + a few resistors | Yes | As C, cheaper, flakier RX |
| E | CH32X035/CH32V003 DMA MII → switch ext port | Switch ext MAC port, MII PHY mode | $0 | **No** | Research item |
| F | Bit-banged port on the PoE cable itself | None | — | — | Dead end |

* **A.** MAC-to-MAC into the RTL8363NB ext port. It replaces the CH32V307
  (≈ −$0.40). PIO RMII is proven against a LAN8720; against a switch port,
  not yet. Recommended for the switch SKU.
* **B.** Uses a spare copper port of a bigger switch (RTL8367S / YT9215S),
  ≈ +$0.5–2 over the RTL8363NB. Direct 10BASE-T is proven against real
  switches over a cable. Works, but costs more than A.
* **C.** The link partner is whatever the user plugs into the second port.
  Extra BOM is ≈ $0.23 PHY + ~$0.05 crystal + magjack. Proven with a LAN8720.
  Only for a product with a separate management port.
* **D.** Proven (TCP 5–7 Mbit/s).
* **E.** The ext port runs at 10M. **Not done by anyone I found.**
* **F.** Gigabit uses all four pairs, so there is nothing to attach to.

## 3. Direct on the wire (10BASE-T from MCU pins)

### 3.1 What the signal needs **[802.3]**

* **Manchester at 10 Mbit/s** = 20 Mbaud, 50 ns half-bit cells. Every bit has
  a mid-bit transition, so receivers resync every bit.
* **TX level**: about 2.2–2.8 V peak differential into 100 Ω. Two GPIOs driven
  in antiphase through series resistors get there from 3.3 V.
* **Clock accuracy**: 10 MHz ±0.01 % (100 ppm). Needs a crystal; an RC
  oscillator (even USB-trimmed HSI) is out of spec. RP2040 has a crystal anyway.
* **Idle**: TP_IDL end-of-frame pulse, then **normal link pulses (NLP)**: one
  ~100 ns pulse every 16 ms ± 8 ms. Without NLPs the partner drops link.
* **RX**: the squelch threshold is a few hundred mV; after 100 m the eye is
  well under 1 V. A plain GPIO with a bias network catches it on short
  cables. A differential receiver (comparator, RS-485 transceiver) is the
  robust way.
* **Duplex**: a port that only sends NLPs is parallel-detected by an autoneg
  partner as **10BASE-T half duplex**. To get full duplex, send **FLP bursts**
  (17 clock pulses 125 µs apart with data pulses in between, carrying the
  16-bit base page) instead. That's easy to generate from a timer or PIO.

### 3.2 Projects

| Project | Year | MCU | TX | RX | Scope |
|---|---|---|---|---|---|
| [holysnippet/pico_eth_doc] | 2022 | RP2040 | PIO, 2 GPIOs | PIO, 1 GPIO | Full lwIP stack |
| Pico-10BASE-T ([Tom's Hardware]) | 2022 | RP2040 | PIO, 2 GPIOs | None | UDP transmit only |
| [Pico-100BASE-TX] | 2025 | RP2040/RP2350 | PIO + DMA, 2 GPIOs | None | Transmit only |
| [cnlohr/espthernet] | 2016 | ESP8266 | I2S at 40 MHz | I2S at 40 MHz | Half duplex |
| ethertiny / IgorPlug-UDP / [PA3FWM avreth] | — | ATtiny85 / AVR | Bit-banged | Overclocked USI or BPSK trick | Demos |

* **pico_eth_doc** (Robin Guillaume). TX on 2 consecutive GPIOs; RX on 1 GPIO
  with resistor bias + Schmitt input. Hardware: 10/100 transformer or
  magjack, ~8 resistors, 4 caps; **no comparator**. lwIP (NO_SYS=1), 1 PIO
  block, 4 DMA, 2 IRQs; sys clock 120 or 240 MHz; **TCP 5–7 Mbit/s**
  (iperf 2). No NLP detection on RX. Beta. BSD-3.
* **Pico-10BASE-T** (kingyoPiyo). TX through 2 × 47 Ω + 470 Ω; pulse
  transformer recommended. The ancestor of the RP2040 work.
* **Pico-100BASE-TX** (Steve Markgraf). MLT-3 with 2 GPIOs, 4B5B +
  scrambler, at 100 Mbit/s; pulse transformer or a switch in between. Shows
  the TX side scales; RX at 125 Mbaud MLT-3 does not exist.
* **cnlohr/espthernet** (Charles Lohr). RX is oversampled. Line driver
  recommended, plus magnetics. Half duplex (NLP). Author: "a party trick, not
  a legitimate engineering solution".
* **ethertiny (Charles Lohr) / IgorPlug-UDP / avreth.** RX uses an
  overclocked USI, or a BPSK-in-payload trick. Hardware is resistors and
  bias. Shows how little hardware is needed; not a basis for a product.

### 3.3 Fit for this adapter

* **Off-board use is unattractive.** Every project above warns against PoE
  ports and recommends real magnetics. A bit-banged port on its own RJ45
  costs a magjack and buys only a second cable. The passthrough already has
  the cable the user cares about.
* **On-board use (chip to chip) is clean electrically.** Into a switch copper
  PHY over a few cm of trace, cap-coupled with no magnetics (same idea as the
  cap-coupled device port in `gigabit-piggyback.md` §3), the RX eye is large
  and the passive bias receiver from pico_eth_doc should be reliable. Send
  FLPs advertising 10BASE-T full duplex so the switch doesn't fall back to
  half duplex.
* **But it needs a spare copper PHY.** RTL8363NB has exactly two (PoE side,
  device side) plus one MAC. A 5-port part (RTL8367S, YT9215S at ~$1.92
  @900 per `ethernet-switch.md`) has spares, but then option A on the
  RTL8363NB is cheaper and needs no analog front end at all.

## 4. Via a PHY or a switch port (software MAC)

### 4.1 Projects

| Project | MCU | Interface | PHY | Speed |
|---|---|---|---|---|
| [sandeepmistry/pico-rmii-ethernet] (fork: [suryatmodulus]) | RP2040 | PIO RMII + MDIO | LAN8720 | 10 Mbit/s only |
| [Mongoose pico-rmii] ([article][embeddedrelated]) | RP2040 | PIO RMII + PIO SMI | LAN8720 | 10 Mbit/s only |

* **pico-rmii-ethernet.** TX at 100 had a bug. The RP2040 is clocked **from
  the PHY's 50 MHz REF_CLK** (underclocked to 50 MHz). lwIP NO_SYS.
* **Mongoose pico-rmii.** Autoneg is restricted to 10M. The 50 MHz ref clock
  from the PHY drives CPU + PIO. TX via DMA → PIO FIFO; RX ping-pong DMA, PIO
  IRQ at end of frame. CRC in software. Full duplex only. The RX buffer swap
  must fit inside the 9.6 µs inter-frame gap.

### 4.2 Why 10 Mbit/s RMII is easy and 100 is not

* RMII always clocks at 50 MHz with 2-bit dibits. At 10 Mbit/s each dibit is
  held for 10 clocks, so PIO samples at 5 MHz effective. At 100 Mbit/s a dibit
  changes every 20 ns and the PIO must sample every edge, with RX_DV/CRS_DV
  framing, at full speed into DMA. Nobody has published a working 100 Mbit/s
  PIO RX; the existing drivers force the PHY to 10M.
* **FCS in hardware on RP2040:** the DMA sniffer has an IEEE 802.3 CRC-32
  mode, so the CPU need not compute the FCS. Neither driver above uses it;
  worth adding.
* **MII at 10 Mbit/s** is 4-bit nibbles at 2.5 MHz, with TX_CLK and RX_CLK
  supplied by the PHY (or by the switch in MII PHY mode). Even slower than
  RMII, at the cost of ~5 more pins (TXD0-3, TX_EN, TX_CLK, RXD0-3, RX_DV,
  RX_CLK, plus MDC/MDIO).

### 4.3 Without PIO: DMA-driven MII on a WCH part (untested idea)

For the CH32X035 (the chosen USB-PD MCU) to be on the network without a host
relay, it would need a MAC. A software one is conceivable over MII at 10M:

* RX: RX_CLK (2.5 MHz) into a timer input; each edge triggers a DMA transfer
  of the GPIO input register (RXD0-3 + RX_DV on one port) into RAM. The CPU
  finds frame boundaries from RX_DV afterwards. 2.5 M transfers/s on a
  48 MHz bus is plausible but takes a real share of the bus.
* TX: TX_CLK edge triggers DMA from a prepared nibble buffer to the port's
  output (BSHR) register. MII samples TXD on TX_CLK rising; 400 ns period vs.
  a few cycles of DMA latency at 48 MHz leaves margin.
* CRC-32 in software, or the CH32 CRC unit if it uses the Ethernet
  polynomial (check).
* **Unknowns**: whether the CH32X035 timers can DMA-trigger from an external
  clock edge on the needed pins, whether TX and RX at once leave CPU for
  lwIP, and whether RTL8363NB supports 10M on its MII PHY-mode port with these
  timings. Nobody seems to have tried this. Bench-test before relying on it.

### 4.4 Cheap PHYs if a standalone port is wanted

| Part | Interface | Pkg | $ @100 | $ @1k | Stock | Notes |
|---|---|---|---|---|---|---|
| CoreChips SR8201F ([C378491]) | MII/RMII, 10/100 | QFN-32 | **$0.266** | **$0.229** | 6,895 **[live]** | Internal 1.1 V, auto-MDIX. Cheapest found |
| WCH CH182H ([C22370607]) | MII/RMII, 10/100 | QFN-32 | $0.452 | $0.390 | **Out of stock [live]** | |
| Microchip LAN8710A ([C46185]) | MII/RMII | QFN-32 | $0.545 | $0.513 | 5,829 **[live]** | LAN8720A is the one the PIO drivers test against |

All need a 25 MHz crystal (or 50 MHz RMII clock) and magnetics. The PIO
drivers use a few LAN87xx-specific MDIO registers to force 10M; for SR8201F
that would be a small port, using the standard BMCR/ANAR registers.

## 5. Recommendation

1. **Cheap SKU:** don't bit-bang Ethernet. Use the host relay over USB
   (`gigabit-piggyback.md` option A).
2. **Switch SKU:** RTL8363NB + **RP2040 running a PIO RMII MAC into the
   switch's extension port** (MAC-to-MAC, no PHY, no magnetics, no analog
   front end). Start from the Mongoose pico-rmii driver; change the MDIO
   part to talk to the switch's SMI instead of a PHY; use the DMA sniffer for
   CRC-32. 10 Mbit/s is plenty for LLDP, DHCP and a small web/management page.
3. **Bench tests needed before committing:**
   * RTL8363NB ext port in RMII PHY mode at 10 Mbit/s against PIO RMII:
     who sources the 50 MHz clock (the PIO driver expects to be clocked by it).
   * RP2040 idle current with the PIO MAC running vs. the PoE MPS budget
     (`poe.md` §6.3).
   * Optional: CH32X035 DMA-driven MII (§4.3). If it works, the switch SKU
     doesn't need a second MCU at all.

## Sources

* [holysnippet/pico_eth_doc]: RP2040 PIO 10BASE-T + lwIP
* [Tom's Hardware]: kingyoPiyo Pico-10BASE-T (TX only)
* [Pico-100BASE-TX]: Steve Markgraf, TX-only 100BASE-TX; [Elektor article](https://elektormagazine.com/news/rp2350-bit-bangs-100-mbit-ethernet)
* [cnlohr/espthernet]: ESP8266 10BASE-T via I2S; [Hackaday](https://hackaday.com/tag/espthernet/)
* [PA3FWM avreth]: AVR 10BASE-T receive; mentions ethertiny and IgorPlug-UDP
* [sandeepmistry/pico-rmii-ethernet] via fork [suryatmodulus]
* [Mongoose pico-rmii] and [embeddedrelated] article on the PIO MAC design
* LCSC: [C378491], [C22370607], [C46185]

[holysnippet/pico_eth_doc]: https://github.com/holysnippet/pico_eth_doc
[Tom's Hardware]: https://www.tomshardware.com/news/raspberry-pi-pico-ethernet-hack
[Pico-100BASE-TX]: https://github.com/steve-m/Pico-100BASE-TX
[cnlohr/espthernet]: https://github.com/cnlohr/espthernet
[PA3FWM avreth]: https://pa3fwm.nl/projects/avreth/
[sandeepmistry/pico-rmii-ethernet]: https://github.com/sandeepmistry/pico-rmii-ethernet
[suryatmodulus]: https://github.com/suryatmodulus/pico-rmii-ethernet
[Mongoose pico-rmii]: https://github.com/cesanta/mongoose/tree/7.16/examples/pico-sdk/pico-rmii
[embeddedrelated]: https://www.embeddedrelated.com/showarticle/1719.php
[C378491]: https://www.lcsc.com/product-detail/C378491.html
[C22370607]: https://www.lcsc.com/product-detail/C22370607.html
[C46185]: https://www.lcsc.com/product-detail/C46185.html
