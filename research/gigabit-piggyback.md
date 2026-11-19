# Piggybacking a small device on a gigabit Ethernet link

Question: can the adapter's MCU get onto (listen to, or send on) the
passthrough gigabit link more cheaply than with the 3‑port switch from
[`ethernet-switch.md`](ethernet-switch.md) (RTL8363NB + CH32V307, about **+$4.50** per unit over
the passive variant in [`design/block-diagram-and-bom.md`](../design/block-diagram-and-bom.md))?

Researched 2026‑10‑21. Prices are LCSC, checked live where marked **[live]**;
the rest are estimates carried over from the BOM CSV.

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
  switch. Details in §4.

## 2. Options ranked

| # | Approach | Switch IC | MCU | MCU link | Mechanism | Second mechanism | MCU can send? | Works with any host? | Needs | Δ BOM low | Δ BOM high | Basis | Verdict | Remark |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | **Host relay over USB-C** | – | – | USB 2.0 to the host | Host speaks on Ethernet | – | Via the host | No | A daemon on the host | ≈ $0.00 | ≈ $0.05 | – | **Best cheap option** | – |
| B | **3-port switch, trimmed** | RTL8363NB | RP2040 | RMII | Cap-coupled device port | – | Yes | Yes | – | ≈ +$3.3 | ≈ +$3.6 | Estimate | Best standalone option | Needs bench validation |
| C | 3-port switch as designed | RTL8363NB | CH32V307 | – | – | – | Yes | Yes | – | ≈ +$4.50 | ≈ +$4.50 | – | Baseline | Lowest risk |
| D | Switch with embedded CPU | YT9215S | Its RISC-V core | – | The core does the networking | – | Yes | Yes | A Motorcomm SDK | ≈ +$3.5 | ≈ +$4 | Estimate | Only if Motorcomm gives an SDK | – |
| E | PoE-layer signalling | – | – | – | Class events | Autoclass | Not really | Yes | – | $0 | $0 | Already in design | Already used | Tells the PD its power grant only |
| F | Analog link sensing | – | – | – | Detect pair activity | 10/100/1000 by which pairs are active | No | Yes | – | ≈ $0.05 | ≈ $0.10 | – | Status only | Risks return loss |
| G | Passive and overlay schemes | – | – | – | Each one is listed in §4 | – | — | — | – | — | — | – | Dead ends (§4) | – |

The Δ BOM columns are against the passive variant @1k.

Approach G covers the passive tap, spare pairs, 10BASE-T1S, PoE-DC powerline,
autoneg next pages and PHY-PHY + FPGA ideas.

A and B and C are not exclusive: a "basic" SKU can ship A, and a "managed" SKU
can add the switch. A's firmware (USB protocol, state model) is reusable in
the managed SKU as the local config interface.

## 3. Viable options in detail

### A. Host relay over USB‑C (recommended for the cheap SKU)

The adapter is the USB‑C power source, so by Type‑C default it is also the
**DFP (USB host)** and the sink (Pi) is the **UFP (USB device)**. That
matches the Pi's default: the Pi 4 and 5 USB‑C port is a DWC2 OTG controller that
acts as a USB 2.0 *gadget* with `dtoverlay=dwc2` and `libcomposite` (Pi 5
needed a firmware and kernel update shortly after launch; now in the normal
images). **[Pi5 gadget]**

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
  PDOs. This closes the gap [`poe.md`](poe.md) §4.5 noted ("passthrough has no PHY so
  cannot speak LLDP").
* Firmware update of the adapter MCU from the host (DFU over the same link).

Cost: the USB‑C receptacle in the CSV is already a 16‑pin part with D+ and D‑;
add two traces, maybe a 2‑line ESD array (~$0.02). No extra silicon if the
CH32V203 is kept. **Δ ≈ $0.00–0.05.**

Drawbacks:

* Needs host software. Without it the adapter still works as a dumb
  PoE→USB‑C adapter with class‑event based power limits (as designed now).
* The host sees the adapter's power state only while it is running; the
  adapter cannot be managed if the host is down. For "is my Pi alive"
  monitoring this is a real limitation.
* Pi 5 note: the official PSU signals 5 A via PD; the Pi's
  `usb_max_current_enable` / `PSU_MAX_CURRENT` logic is unaffected by having
  data on the same port, but test it.
* A USB‑C *captive cable* variant must carry D+ and D‑ (most cheap power cables
  don't).

### B. Switch, trimmed

Where the current $4.50 goes (from the design doc): switch + crystal +
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
   **$0.73 @1k [live]**, plus ~$0.10 QSPI flash and a 12 MHz crystal,
   vs. ~$1.30 estimated for CH32V307. PIO RMII drivers exist at 10 Mbit/s,
   enough for LLDP and management. The RP2040 also does USB host or device for
   option A, and has the PIO to bit‑bang USB‑PD BMC. Costs: no hardware MAC
   (CPU does CRC and framing), higher idle current, which matters for the ≤ 4 mA
   PoE mark‑event budget ([`poe.md`](poe.md) §6.3), so a CH32V003 cold‑start helper is
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
  (PSE type 1 and 2 vs 3 and 4), and Autoclass on bt. Already in [`poe.md`](poe.md) §4.
* PD → PSE: the class signature only. A PD can also drop its MPS to get
  power removed and re‑detected, which is a crude one‑bit "reset me" signal.
* No standard PSE carries data over the PoE DC. Any data‑over‑DC scheme would
  need a custom injector at the other end (§4).

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

| Idea | Would work if | Why it fails here | Key figure |
|---|---|---|---|
| **Passive tap (Throwing-Star style)** | The link is 10/100 | Gigabit sends both ways on all four pairs | – |
| **Use the spare pairs** | The link drops to 100 Mbit | 1000BASE-T uses all four pairs | Needs ≥1 Gbit/s |
| **10BASE-T1S overlay** | A custom injector is at the other end | The PSE switch has no receiver for it | – |
| **Data over PoE DC (powerline-style)** | – | Nothing at the PSE end listens | – |
| **Autoneg next pages** | The adapter terminates the link (has PHYs) | Only the two link endpoints exchange them | – |
| **Two PHYs back-to-back + glue logic** | It does work | Costs more than the switch | 2 × YT8531C at **$0.79 @1k [live]** |
| **"MAC-in-PHY" SPI Ethernet parts** | – | They all terminate their *own* link | – |
| **USB-Ethernet bridge (RTL8153)** | The host has USB 3 | The Pi's USB-C port is USB 2.0 | 480 Mbit/s |

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
* **Two PHYs back-to-back + FPGA and MCU muxing frames in.** RGMII or SGMII runs
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
* Related project research: [`ethernet-switch.md`](ethernet-switch.md), [`poe.md`](poe.md), [`../design/block-diagram-and-bom.md`](../design/block-diagram-and-bom.md)
