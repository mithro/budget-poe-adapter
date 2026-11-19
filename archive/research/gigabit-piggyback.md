# Piggybacking a small device on a gigabit Ethernet link

> **Archived.** This note is not part of the current design. It assumes an external MCU that has to reach a gigabit link passed through the adapter. The current design uses only the YT9215 switch IC and its internal RISC-V CPU. The [archive index](../README.md) lists every archived note.

Question: can the adapter's MCU get onto (listen to, or send on) the
passthrough gigabit link more cheaply than with the 3‑port switch from
[`ethernet-switch.md`](ethernet-switch.md) (RTL8363NB + CH32V307, about **+$4.50** per unit over
the passive variant in [`design/block-diagram-and-bom.md`](../design/block-diagram-and-bom.md))?

<a id="evidence-codes"></a>
Prices are LCSC prices. Evidence code **live**: the price or stock figure was read from the LCSC product page on 2026-10-21.
Unmarked prices are estimates carried over from [`bom-rough.csv`](../design/bom-rough.csv).

## 1. TL;DR

* **Gigabit physics rules out a passive tap.** 1000BASE‑T sends in both
  directions on all four pairs at once and each end separates the two
  directions with echo cancellation. A third device on the wire sees the sum
  of both transmitters and cannot decode either, and it can never inject.
  There are no spare pairs either. Any device that wants to be *on* the link
  has to terminate it and regenerate it, which means two PHYs plus a
  forwarding engine. The cheapest forwarding engine is a switch chip, and
  RTL8363NB at $1.43 is already that.
* **The cheapest real option is to let the downstream device do the talking
  ("host relay").** The Pi or SBC is already on the network over the passthrough
  and already connected to the adapter over USB‑C. Wire USB 2.0 D+ and D‑ from
  the receptacle to the MCU; the host runs a small daemon that reads the
  adapter's state over USB and speaks for it on Ethernet, including **LLDP
  PoE power negotiation** with `lldpd`. Added BOM cost is about **$0.00–0.05**
  on the passive variant. The catch: it only works with host software
  installed, so the adapter stays "dumb" for other devices.
* **If the adapter must be on the network on its own, keep the switch but trim
  it.** The switch chip is only ~$1.62 of the $4.50; the rest is the second
  magjack, the bigger MCU, the 4‑layer board and assembly. Capacitor‑coupling
  the device‑side port and using an RP2040 instead of a CH32V307 could cut
  the delta to roughly **$3.3–3.6**. Both trims need a bench test.
* Everything else surveyed (spare pairs, 10BASE‑T1S overlays, PoE‑DC
  powerline, autoneg next pages, PHY‑to‑PHY bridges, "MAC‑in‑PHY" parts)
  is either impossible on a standard gigabit port or costs more than the
  switch. Details in [section 4](#4-dead-ends-and-why).

## 2. Options ranked

| # | Approach | Switch IC | MCU | MCU link | MCU can send? | Works with any host? | Δ BOM low | Δ BOM high | Basis | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | **Host relay over USB-C** | – | – | USB 2.0 to the host | Via the host | No | ≈ $0.00 | ≈ $0.05 | – | **Best cheap option** |
| B | **3-port switch, trimmed** | RTL8363NB | RP2040 | RMII | Yes | Yes | ≈ +$3.3 | ≈ +$3.6 | Estimate | Best standalone option |
| C | 3-port switch as designed | RTL8363NB | CH32V307 | RMII | Yes | Yes | ≈ +$4.50 | ≈ +$4.50 | – | Baseline |
| D | Switch with embedded CPU | YT9215S | Its RISC-V core | – | Yes | Yes | ≈ +$3.5 | ≈ +$4 | Estimate | Only if Motorcomm gives an SDK |
| E | PoE-layer signalling | – | – | – | Not really | Yes | $0 | $0 | Already in design | Already used |
| F | Analog link sensing | – | – | – | No | Yes | ≈ $0.05 | ≈ $0.10 | – | Status only |
| G | Passive and overlay schemes | – | – | – | — | — | — | — | – | Dead ends ([section 4](#4-dead-ends-and-why)) |

Notes on the rows of this table:

- **A, Host relay over USB-C**, mechanism: Host speaks on Ethernet.
- **A, Host relay over USB-C**, needs: A daemon on the host.
- **B, 3-port switch, trimmed**, mechanism: Cap-coupled device port.
- **B, 3-port switch, trimmed**, remark: Needs bench validation.
- **C, 3-port switch as designed**, remark: Lowest risk.
- **D, Switch with embedded CPU**, mechanism: The core does the networking.
- **D, Switch with embedded CPU**, needs: A Motorcomm SDK.
- **E, PoE-layer signalling**, mechanism: Class events.
- **E, PoE-layer signalling**, second mechanism: Autoclass.
- **E, PoE-layer signalling**, remark: Tells the PD its power grant only.
- **F, Analog link sensing**, mechanism: Detect pair activity.
- **F, Analog link sensing**, second mechanism: 10/100/1000 by which pairs are active.
- **F, Analog link sensing**, remark: Risks return loss.
- **G, Passive and overlay schemes**, mechanism: Each one is listed in [section 4](#4-dead-ends-and-why)

The Δ BOM columns are against the passive variant @1k.

Approach G covers the passive tap, spare pairs, 10BASE-T1S, PoE-DC powerline,
autoneg next pages and PHY-PHY + FPGA ideas.

A can be combined with B or C: a "basic" SKU can ship A, and a "managed" SKU
can add the switch. A's firmware (USB protocol, state model) is reusable in
the managed SKU as the local config interface.

## 3. Viable options in detail

### A. Host relay over USB‑C (recommended for the cheap SKU)

The adapter is the USB‑C power source, so by Type‑C default it is also the
**DFP (USB host)** and the sink (Pi) is the **UFP (USB device)**. That
matches the Pi's default: the Pi 4 and 5 USB‑C port is a DWC2 OTG controller that
acts as a USB 2.0 *gadget* with `dtoverlay=dwc2` and `libcomposite` (Pi 5
needs a firmware and kernel update that the normal Raspberry Pi OS images
include). **[Pi5 gadget]**

Two ways to wire it:

1. **Adapter as USB host, Pi as gadget (default roles).** The Pi exposes a
   CDC‑ACM (serial) or vendor gadget; the adapter MCU is a USB FS host that
   talks to it. CH32V203 has a full‑speed OTG or host controller (USBFS) as well
   as a device controller (verify on the exact package); RP2040 has host mode
   via TinyUSB.
2. **Adapter as USB device.** The MCU enumerates as CDC‑ACM or HID on hosts
   that are USB hosts on their charging port (laptops, phones, most SBCs whose
   USB‑C port is host or OTG). On a Pi this needs `dtoverlay=dwc2,dr_mode=host`,
   or a PD `DR_Swap`. Simpler firmware, but on a Pi it needs config.

Supporting both (MCU starts as host, falls back to device or accepts DR_Swap)
covers Pi and laptop or phone cases. Speed is irrelevant; the traffic is a few
hundred bytes.

What the host daemon does:

* Publishes adapter state: PoE class granted, PSE type, input voltage and current,
  USB‑PD contract, temperature, fault log. Exposed as sysfs‑like files, a
  Prometheus endpoint, MQTT, whatever.
* **LLDP power negotiation on the adapter's behalf.** The PSE switch only
  cares that LLDP‑MED and 802.3at‑bt power TLVs arrive on the port; it does not
  care which MAC sends them. The host already sits on that port through the
  passthrough, so `lldpd` on the host can advertise the adapter's request
  (`configure dot3 power pd supported enabled ... requested <mW>`) and pass
  the PSE's "allocated" answer back to the MCU, which then updates the PD
  PDOs. This closes the gap [`poe.md` section 4.5](../../research/poe.md#45-lldp-data-link-layer-classification) noted ("passthrough has no PHY so
  cannot speak LLDP").
* Firmware update of the adapter MCU from the host (DFU over the same link).

Cost: the USB‑C receptacle in [`bom-rough.csv`](../design/bom-rough.csv) is already a 16‑pin part with D+ and D‑;
add two traces, maybe a 2‑line ESD array (~$0.02). No extra silicon if the
CH32V203 is kept. **Δ ≈ $0.00–0.05.**

Drawbacks:

* Needs host software. Without it the adapter still works as a dumb
  PoE→USB‑C adapter with class‑event based power limits.
* The host sees the adapter's power state only while it is running; the
  adapter cannot be managed if the host is down. For "is my Pi alive"
  monitoring this is a real limitation.
* Pi 5 note: the official PSU signals 5 A via PD; the Pi's
  `usb_max_current_enable` and `PSU_MAX_CURRENT` logic is unaffected by having
  data on the same port, but test it.
* A USB‑C *captive cable* variant must carry D+ and D‑ (most cheap power cables
  don't).

### B. Switch, trimmed

Where the current $4.50 goes (from [`block-diagram-and-bom.md`](../design/block-diagram-and-bom.md)): switch + crystal +
passives $1.62, bigger MCU +$0.95, second magjack +$1.05, 4‑layer board
+$0.25, more assembly +$0.50, 3.3 V buck instead of LDO +$0.11.

Trims worth bench‑testing:

1. **Capacitor‑coupled device‑side port (≈ −$0.55).** Replace the
   output magjack ($0.65) with a plain RJ45 ($0.10) plus 8 × 33 nF NP0 caps
   and a TVS array. The design is non‑isolated by intent and the adapter's
   ground is already tied to the host's through USB‑C, so the isolation the
   magnetics would provide buys nothing here; the Pi's own magnetics stay in
   the link. ADI documents cap‑coupled 1000BASE‑T for the ADIN1300 (33 nF NP0,
   no MDI bias resistors, ≤1 m is easy, longer needs a common‑mode choke and
   shielded cable). **[ADI]** TI and Micrel have similar app notes for older
   PHYs. **Open:** whether the RTL8363NB's line driver (voltage‑mode vs
   current‑mode with centre‑tap bias) allows this. Realtek doesn't say
   publicly. Also check EMC: a short shielded patch cable is likely needed.
2. **RP2040 instead of CH32V307 on the RMII port (≈ −$0.40).** RP2040 is
   **$0.73 @1k** [**live**](#evidence-codes), plus ~$0.10 QSPI flash and a 12 MHz crystal,
   vs. ~$1.30 estimated for CH32V307. PIO RMII drivers exist at 10 Mbit/s,
   enough for LLDP and management. The RP2040 also does USB host or device for
   option A, and has the PIO to bit‑bang USB‑PD BMC. Costs: no hardware MAC
   (CPU does CRC and framing), higher idle current, which matters for the ≤ 4 mA
   PoE mark‑event budget ([`poe.md` section 6.3](../../research/poe.md#63-the-bootstrap-problem)), so a CH32V003 cold‑start helper is
   likely needed (+$0.15). Net ≈ −$0.30 to −$0.45.
3. **Stay on 4 layers.** Two GbE ports plus a QFN‑76 switch really wants
   controlled impedance; I wouldn't try to save the $0.25 here.

Rough result: $4.50 − 0.55 − 0.40 ≈ **$3.5** (call it $3.3–3.6, ±30 % like
the rest of the BOM).

### D. Switch with an embedded CPU

Motorcomm's **YT9215S** (LCSC and JLC C5899183, $1.92 @900) has an integrated
RISC‑V MCU, SPI flash interface, UART, I²C, SPI or GPIO, and a strap to disable
the MCU. **[YT9215S]** If that core can send and receive frames through the
switch's internal CPU port (which is what such cores exist for in
web‑managed switches), the adapter could drop the networking MCU and keep only
a cheap PoE PD MCU. Net vs. option C: switch +$0.49, MCU −$0.95, but
LQFP‑128 adds board area. The public datasheet is a draft and says nothing
about the MCU's programming model, SDK or power, so this is **only worth
pursuing if Motorcomm (or a distributor) provides an SDK**. Realtek's
RTL8367S has an embedded 8051 in the same role, also undocumented.

### E. PoE‑layer signalling (what we already get for free)

* PSE → PD: number of class events (power grant), first‑class‑event length
  (PSE Type 1 or 2 versus Type 3 or 4), and Autoclass on bt. Already in [`poe.md` section 4](../../research/poe.md#4-the-negotiation-sequence-end-to-end).
* PD → PSE: the class signature only. A PD can also drop its MPS to get
  power removed and re‑detected, which is a crude one‑bit "reset me" signal.
* No standard PSE carries data over the PoE DC. Any data‑over‑DC scheme would
  need a custom injector at the other end ([section 4](#4-dead-ends-and-why)).

So this layer tells the adapter how much power it may offer, and nothing
reaches the network.

### F. Analog link sensing (status only)

Light, high‑impedance coupling (small caps into a comparator or the MCU's
ADC) on the pairs can show "link has energy" and roughly which pairs are
active: 10/100 uses pairs 1‑2 and 3‑6, 1000BASE‑T uses all four. That lets the
adapter report "link up at gigabit" over USB‑PD or an LED without any PHY.
Cost ≈ $0.05–0.10. Risks: any added capacitance unbalances the pairs and
hurts return loss and common‑mode rejection, and 1000BASE‑T idle still has
energy, so "traffic" can't be distinguished from "link". Optional nicety,
not a network presence.

## 4. Dead ends and why

| Idea | Key figure | Key figure evidence |
| --- | --- | --- |
| **Passive tap (Throwing-Star style)** | – |  |
| **Use the spare pairs** | Needs ≥1 Gbit/s |  |
| **10BASE-T1S overlay** | – |  |
| **Data over PoE DC (powerline-style)** | – |  |
| **Autoneg next pages** | – |  |
| **Two PHYs back-to-back + glue logic** | 2 × YT8531C at **$0.79 @1k** | [**live**](#evidence-codes) |
| **"MAC-in-PHY" SPI Ethernet parts** | – |  |
| **USB-Ethernet bridge (RTL8153)** | 480 Mbit/s |  |

Notes on the rows of this table:

- **Passive tap (Throwing-Star style)**, would work if: The link is 10/100.
- **Passive tap (Throwing-Star style)**, why it fails here: Gigabit sends both ways on all four pairs.
- **Use the spare pairs**, would work if: The link drops to 100 Mbit.
- **Use the spare pairs**, why it fails here: 1000BASE-T uses all four pairs.
- **10BASE-T1S overlay**, would work if: A custom injector is at the other end.
- **10BASE-T1S overlay**, why it fails here: The PSE switch has no receiver for it.
- **Data over PoE DC (powerline-style)**, why it fails here: Nothing at the PSE end listens.
- **Autoneg next pages**, would work if: The adapter terminates the link (has PHYs)
- **Autoneg next pages**, why it fails here: Only the two link endpoints exchange them.
- **Two PHYs back-to-back + glue logic**, why it fails here: It works, but costs more than the switch.
- **"MAC-in-PHY" SPI Ethernet parts**, why it fails here: They all terminate their *own* link.
- **USB-Ethernet bridge (RTL8153)**, would work if: The host has USB 3.
- **USB-Ethernet bridge (RTL8153)**, why it fails here: The Pi's USB-C port is USB 2.0.

The reasoning behind each row:

* **Passive tap.** On 10/100 each pair carries one direction. On 1000BASE-T
  both ends transmit on all four pairs at once and rely on knowing their
  *own* transmit signal to cancel it; a third party sees the sum and can't
  decode it. Commercial gigabit taps are active (they terminate and
  regenerate). Injection is impossible even at 10/100. **[LAN Tap]**
* **Spare pairs.** A 100 Mbit link fails the ≥1 Gbit/s requirement.
* **10BASE-T1S and SPE overlay.** It needs its own pair. Superimposing it in
  common mode (phantom) between pair centre taps would ride on the PoE
  power. A custom injector defeats "plug into any PoE switch".
* **Data over PoE DC.** Same problem as the overlay. It also fights the
  PSE's MPS and current monitoring.
* **Autoneg next pages.** 802.3 autoneg can carry arbitrary next-page
  messages. The adapter is not an endpoint unless it terminates the link.
* **Two PHYs back-to-back + FPGA or MCU muxing frames in.** RGMII or SGMII runs
  between the two PHYs, with everything clocked from the upstream link. On
  top of the PHYs it needs an FPGA or fast MCU that can handle 125 MHz DDR
  RGMII and buffer a frame. No MCU in this price range can do that. A
  media-converter PHY pair (UTP↔SGMII) can repeat the link but can't inject.
* **"MAC-in-PHY" and SPI Ethernet parts.** Examples are the W5500, ENC28J60
  and LAN865x 10BASE-T1S. None can sit inside someone else's gigabit link.
* **USB-Ethernet bridge instead of passthrough.** It turns the adapter into
  a USB NIC. It gives gigabit only to USB 3 hosts, so it fails the
  requirement for the main target. Different product.

## 5. Suggested next steps

1. Decide whether a "needs host software" adapter is acceptable for the base
   SKU. If yes, add D+ and D‑ routing to the passive design and prototype the
   host relay (`lldpd` + small daemon, CH32V203 USB host + Pi gadget).
2. If a standalone managed SKU is wanted, bench‑test the two trims on an
   RTL8363NB evaluation board: cap‑coupled device port at 1 Gbit/s over 0.3–2 m,
   and PIO‑RMII on RP2040 at 10 Mbit/s against the switch's ext port.
3. Ask a Motorcomm distributor whether the YT9215S (and YT9213NB) embedded
   RISC‑V core has a customer SDK; that decides option D.

## 6. Sources

* **[Pi5 gadget]** Pi 5 USB‑C gadget mode (dwc2, USB 2.0): https://blog.hardill.me.uk/2023/12/23/pi5-usb-c-gadget/
* **[ADI]** ADIN1300 and ADIN1200 capacitive coupling guide: https://wiki.analog.com/resources/eval/user-guides/adin1300-and-adin1200/cap-coupling
* TI magnetics‑less and cap‑coupled Ethernet app note SNLA088A: https://ti.com/lit/SNLA088A
* Micrel AN‑120 capacitive coupling: https://web.pa.msu.edu/hep/atlas/l1calo/hub/hardware/components/micrel/micrel_capacitive_coupling_ethernet_an_120.pdf
* **[YT9215S]** YT9215S datasheet (LCSC copy): https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308291451_Motorcomm-YT9215S_C5899183.pdf
* **[LAN Tap]** Throwing Star LAN Tap Pro (passive tap, 10/100 only): https://www.elektor.com/products/great-scott-gadgets-throwing-star-lan-tap-pro
* RP2040 at LCSC (C2040), $0.73 @1k, 41,863 in stock: https://lcsc.com/product-detail/C2040.html
* YT8531C‑CA at LCSC (C22472312), $0.79 @1k, 7,563 in stock: https://www.lcsc.com/product-detail/C22472312.html
* Related project research: [`ethernet-switch.md`](ethernet-switch.md), [`poe.md`](../../research/poe.md), [`../design/block-diagram-and-bom.md`](../design/block-diagram-and-bom.md)

[Pi5 gadget]: https://blog.hardill.me.uk/2023/12/23/pi5-usb-c-gadget/
[ADI]: https://wiki.analog.com/resources/eval/user-guides/adin1300-and-adin1200/cap-coupling
[YT9215S]: https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308291451_Motorcomm-YT9215S_C5899183.pdf
[LAN Tap]: https://www.elektor.com/products/great-scott-gadgets-throwing-star-lan-tap-pro
