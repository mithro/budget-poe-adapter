# Bit-banging 10 Mbit/s Ethernet

Question: can the adapter's MCU get onto Ethernet with no MAC/PHY silicon of
its own, either by driving 10BASE-T on the wire straight from GPIO, or by
running the MAC in software (RP2040 PIO) against an external PHY or a switch
port? Context: price cap is the RP2040 (~$0.79 @100); see
[`risc-v-mcu-comparison.md`](risc-v-mcu-comparison.md), [`gigabit-piggyback.md`](gigabit-piggyback.md) and [`ethernet-switch.md`](ethernet-switch.md).

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
  bit-banged 10BASE-T port could talk on (see [`gigabit-piggyback.md`](gigabit-piggyback.md) §1, §4).
  A bit-banged port needs something on the board to talk to, and that means
  the 3-port switch from [`ethernet-switch.md`](ethernet-switch.md).
* **Best fit: PIO MAC to the switch's extension MAC port, with no PHY at all.**
  The RTL8363NB's extension port speaks RMII/MII in PHY mode, so an RP2040
  can run the existing PIO RMII code (or a simpler MII variant at 10 Mbit/s)
  straight into it. That replaces the CH32V307 in the switch design for
  $0 of extra silicon, which is the "RP2040 on RMII" trim already costed in
  [`gigabit-piggyback.md`](gigabit-piggyback.md) §3 (≈ −$0.40). This is the recommendation.
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
  [`risc-v-mcu-comparison.md`](risc-v-mcu-comparison.md)) is simpler and frees the PIO.
* **Without PIO (CH32X035, CH32V003), MII at 10 Mbit/s is the only plausible
  bit-bang target.** MII at 10M is a 2.5 MHz nibble clock supplied by the
  PHY/switch, slow enough for timer-triggered DMA to and from a GPIO port on
  a 48 MHz part. I found no one who has done this; it is a research item, not
  a plan (§4.3).

## 2. Options ranked for this adapter

| # | MCU | Alt MCU | Method | Via | Ends at | Switch | Alt switch | Link partner on the board |
|---|---|---|---|---|---|---|---|---|
| A | **RP2040** | – | **PIO RMII/MII MAC** | – | **Switch ext port (MAC-to-MAC)** | RTL8363NB | – | Switch ext MAC port in PHY mode |
| B | RP2040 | – | PIO direct 10BASE-T | – | Spare copper port | RTL8367S | YT9215S | Copper PHY (cap-coupled) |
| C | RP2040 | – | PIO RMII | SR8201F PHY | Own magjack | – | – | Whatever the user plugs into the second port |
| D | RP2040 | – | PIO direct 10BASE-T | – | Own magjack | – | – | Same as C |
| E | CH32X035 | CH32V003 | DMA-driven MII | – | Switch ext port | – | – | Switch ext MAC port (MII PHY mode at 10M) |
| F | Any | – | Any bit-banged port | – | The PoE cable itself | – | – | None |

| # | Extra BOM | PHY | Crystal | Magjack | Passives | Replaces | Saving | Proven? | Proven against | Not yet proven |
|---|---|---|---|---|---|---|---|---|---|---|
| A | $0 | – | – | – | – | CH32V307 | ≈ $0.40 | Partly | LAN8720 | A switch port |
| B | ≈ +$0.5–2 over RTL8363NB | – | – | – | – | – | – | Yes | Real switches over a cable | – |
| C | – | ≈ $0.23 | ~$0.05 | Needed | – | – | – | Yes | LAN8720 | – |
| D | – | – | – | Needed | A few resistors | – | – | Yes | TCP at 5–7 Mbit/s | – |
| E | $0 | – | – | – | – | – | – | **No** | – | Not done by anyone I found |
| F | — | – | – | – | – | – | – | — | – | – |

| # | Verdict | Upside | Downside |
|---|---|---|---|
| A | **Recommended** for the switch SKU | – | – |
| B | Works | – | Costs more than A |
| C | Only for a product with a separate management port | – | – |
| D | Same as C | Cheaper | Flakier RX |
| E | Research item | – | – |
| F | Dead end | – | Gigabit uses all four pairs |


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

| Project | Author | Year | MCU | Alt MCU | TX method | TX pins | RX method | RX pins |
|---|---|---|---|---|---|---|---|---|
| [holysnippet/pico_eth_doc] | Robin Guillaume | 2022 | RP2040 | – | PIO | 2 consecutive GPIOs | PIO | 1 GPIO |
| Pico-10BASE-T ([Tom's Hardware]) | kingyoPiyo | 2022 | RP2040 | – | PIO | 2 GPIOs | None | – |
| [Pico-100BASE-TX] | Steve Markgraf | 2025 | RP2040 | RP2350 | PIO+DMA | 2 GPIOs | None | – |
| [cnlohr/espthernet] | Charles Lohr | 2016 | ESP8266 | – | I2S at 40 MHz | – | I2S at 40 MHz | – |
| AVR projects (listed below) | – | – | ATtiny85 | AVR | Bit-banged | – | Overclocked USI | – |

| AVR project | Author |
|---|---|
| ethertiny | Charles Lohr |
| IgorPlug-UDP | – |
| [PA3FWM avreth] | – |

| Project | Property | Value |
|---|---|---|
| pico_eth_doc | Line hardware option 1 | 10/100 transformer |
| pico_eth_doc | Line hardware option 2 | Magjack |
| pico_eth_doc | Resistors | ~8 |
| pico_eth_doc | Capacitors | 4 |
| pico_eth_doc | Comparator | **None needed** |
| pico_eth_doc | RX bias | Resistor |
| pico_eth_doc | RX input | Schmitt |
| pico_eth_doc | Stack | lwIP (NO_SYS=1) |
| pico_eth_doc | PIO blocks | 1 |
| pico_eth_doc | DMA channels | 4 |
| pico_eth_doc | IRQs | 2 |
| pico_eth_doc | Sys clock option 1 | 120 MHz |
| pico_eth_doc | Sys clock option 2 | 240 MHz |
| pico_eth_doc | TCP throughput | **5–7 Mbit/s** |
| pico_eth_doc | Measured with | iperf 2 |
| pico_eth_doc | NLP detection on RX | No |
| pico_eth_doc | Status | Beta |
| pico_eth_doc | Licence | BSD-3 |
| Pico-10BASE-T | TX resistor value 1 | 2 × 47 Ω |
| Pico-10BASE-T | TX resistor value 2 | 470 Ω |
| Pico-10BASE-T | Line hardware | Pulse transformer recommended |
| Pico-10BASE-T | Scope | UDP transmit only |
| Pico-10BASE-T | Role | The ancestor of the RP2040 work |
| Pico-100BASE-TX | Line code | MLT-3 |
| Pico-100BASE-TX | Block code | 4B5B |
| Pico-100BASE-TX | Scrambler | Yes |
| Pico-100BASE-TX | Line hardware option 1 | Pulse transformer |
| Pico-100BASE-TX | Line hardware option 2 | A switch in between |
| Pico-100BASE-TX | Scope | Transmit only |
| Pico-100BASE-TX | Rate | 100 Mbit/s |
| Pico-100BASE-TX | Lesson | Shows the TX side scales |
| Pico-100BASE-TX | RX | RX at 125 Mbaud MLT-3 does not exist |
| espthernet | RX sampling | Oversampled |
| espthernet | Line driver | Recommended |
| espthernet | Magnetics | Yes |
| espthernet | Duplex | Half duplex (NLP) |
| espthernet | Author's view | "a party trick, not a legitimate engineering solution" |
| AVR projects | Alternative RX method | BPSK-in-payload trick |
| AVR projects | Line hardware 1 | Resistors |
| AVR projects | Line hardware 2 | Bias |
| AVR projects | Lesson | Shows how little hardware is needed |
| AVR projects | Fit | Not a basis for a product |

### 3.3 Fit for this adapter

* **Off-board use is unattractive.** Every project above warns against PoE
  ports and recommends real magnetics. A bit-banged port on its own RJ45
  costs a magjack and buys only a second cable. The passthrough already has
  the cable the user cares about.
* **On-board use (chip to chip) is clean electrically.** Into a switch copper
  PHY over a few cm of trace, cap-coupled with no magnetics (same idea as the
  cap-coupled device port in [`gigabit-piggyback.md`](gigabit-piggyback.md) §3), the RX eye is large
  and the passive bias receiver from pico_eth_doc should be reliable. Send
  FLPs advertising 10BASE-T full duplex so the switch doesn't fall back to
  half duplex.
* **But it needs a spare copper PHY.** RTL8363NB has exactly two (PoE side,
  device side) plus one MAC. A 5-port part (RTL8367S, YT9215S at ~$1.92
  @900 per [`ethernet-switch.md`](ethernet-switch.md)) has spares, but then option A on the
  RTL8363NB is cheaper and needs no analog front end at all.

## 4. Via a PHY or a switch port (software MAC)

### 4.1 Projects

| Project | Fork | Article | MCU | Interface | Management | PHY | Speed |
|---|---|---|---|---|---|---|---|
| [sandeepmistry/pico-rmii-ethernet] | [suryatmodulus] | – | RP2040 | PIO RMII | MDIO | LAN8720 | **10 Mbit/s only** |
| [Mongoose pico-rmii] | – | [article][embeddedrelated] | RP2040 | PIO RMII | PIO SMI | LAN8720 | 10 Mbit/s only |

| Project | Property | Value |
|---|---|---|
| pico-rmii-ethernet | 100 Mbit/s | TX at 100 had a bug |
| pico-rmii-ethernet | Clocking | RP2040 clocked **from the PHY's 50 MHz REF_CLK** |
| pico-rmii-ethernet | Sys clock | Underclocked to 50 MHz |
| pico-rmii-ethernet | Stack | lwIP NO_SYS |
| Mongoose pico-rmii | Autoneg | Restricted to 10M |
| Mongoose pico-rmii | Clocking | 50 MHz ref clock from PHY drives CPU+PIO |
| Mongoose pico-rmii | TX | DMA → PIO FIFO |
| Mongoose pico-rmii | RX | Ping-pong DMA |
| Mongoose pico-rmii | RX end of frame | PIO IRQ |
| Mongoose pico-rmii | CRC | In software |
| Mongoose pico-rmii | Duplex | Full duplex only |
| Mongoose pico-rmii | Timing limit | RX buffer swap inside the 9.6 µs inter-frame gap |

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

| Vendor | Part | LCSC | MII | RMII | Speed | Pkg | $ @100 | $ @1k | Stock | Core supply | Auto-MDIX | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CoreChips | SR8201F | [C378491] | Yes | Yes | 10/100 | QFN-32 | **$0.266** | **$0.229** | 6,895 **[live]** | Internal 1.1 V | Yes | Cheapest found |
| WCH | CH182H | [C22370607] | Yes | Yes | 10/100 | QFN-32 | $0.452 | $0.390 | **Out of stock [live]** | – | – | – |
| Microchip | LAN8710A | [C46185] | Yes | Yes | – | QFN-32 | $0.545 | $0.513 | 5,829 **[live]** | – | – | LAN8720A is the one the PIO drivers test against |

All need a 25 MHz crystal (or 50 MHz RMII clock) and magnetics. The PIO
drivers use a few LAN87xx-specific MDIO registers to force 10M; for SR8201F
that would be a small port, using the standard BMCR/ANAR registers.

## 5. Recommendation

1. **Cheap SKU:** don't bit-bang Ethernet. Use the host relay over USB
   ([`gigabit-piggyback.md`](gigabit-piggyback.md) option A).
2. **Switch SKU:** RTL8363NB + **RP2040 running a PIO RMII MAC into the
   switch's extension port** (MAC-to-MAC, no PHY, no magnetics, no analog
   front end). Start from the Mongoose pico-rmii driver; change the MDIO
   part to talk to the switch's SMI instead of a PHY; use the DMA sniffer for
   CRC-32. 10 Mbit/s is plenty for LLDP, DHCP and a small web/management page.
3. **Bench tests needed before committing:**
   * RTL8363NB ext port in RMII PHY mode at 10 Mbit/s against PIO RMII:
     who sources the 50 MHz clock (the PIO driver expects to be clocked by it).
   * RP2040 idle current with the PIO MAC running vs. the PoE MPS budget
     ([`poe.md`](poe.md) §6.3).
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
