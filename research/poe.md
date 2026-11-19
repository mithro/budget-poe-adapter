# PoE powered device

Research note for the PoE to USB-C adapter. It covers the PoE standards, how a powered
device (PD) negotiates power with the power sourcing equipment (PSE), and the electrical limits
a PD has to meet. The adapter is non-isolated, carries a 1000BASE-T link to the Raspberry Pi and
is built around the YT9215 switch IC and its internal RISC-V CPU
([The RISC-V CPU inside the YT9215](yt9215-embedded-cpu.md)). The circuit that meets these
limits is in [Discrete PoE front end](../design/poe-front-end/README.md).

<a id="evidence-codes"></a>

## Evidence marks

A mark after a number or at the head of a section says where the figures were checked. Each
mark links to this table.

| Mark | Meaning |
| --- | --- |
| Ethernet Alliance | Checked against the 802.3bt overview white paper of the Ethernet Alliance |
| TI application note | Checked against the PD application note SLVAEE5 of Texas Instruments |
| UNH-IOL test suite | Checked against the PD conformance test suite of the UNH InterOperability Laboratory |
| IEEE draft | Checked against an IEEE 802.3 task force document that quotes the text of the standard |
| Not checked | Recalled from IEEE 802.3 clauses 33 and 145 and from PD controller datasheets |

A number with no mark has the mark "Not checked". Such a number is believed correct, but a
design that depends on it has to check it against IEEE 802.3-2022 first. The documents are
listed under [Sources](#sources).

Abbreviations: MDI is the medium dependent interface, the cable connector. UVLO is the
undervoltage lockout. MPS is the maintain power signature of
[section 4.4](#44-maintain-power-signature-mps). LLDP is the Link Layer Discovery Protocol of
[section 4.5](#45-lldp-data-link-layer-classification).

---

## 1. TL;DR for this project

* PoE negotiation is **entirely DC and slow** (millisecond timings, no modulation, no
  carrier). A PD has to look like a specific resistor, then like a specific current sink, each
  in its own voltage window, and then switch its load on gently.
* The YT9215 is **unpowered during the whole negotiation**: during detection (2.7–10.1 V) a
  PD may draw no more than about 10 µA besides the 25 kΩ signature. The negotiation is
  therefore done by a front end that works without the switch, built from discrete parts or
  around a PD controller IC, and the firmware only learns the result
  ([section 6](#6-poe-front-end-of-the-yt9215-design)).
* **A Raspberry Pi 5 at full power (5 V at 5 A = 25 W out) needs about 31 W at the PD
  input**, which is more than 802.3at Class 4 (25.5 W). Full power needs an 802.3bt Class 5
  (40 W) PD on a 4-pair Type 3 or Type 4 PSE. An 802.3at PSE leaves about 4 A at 5 V for the
  USB-C output ([section 5](#5-raspberry-pi-5-power-budget-against-poe-classes)).
* A PSE grants more than 13 W either by the number of class events or over LLDP. A Type 2 PSE
  may use either, and a Type 2 PD is required to support both
  ([section 4.5](#45-lldp-data-link-layer-classification)).
* Non-isolated is functionally fine but **not 802.3-compliant** (the standard
  requires 1500 Vrms isolation between the MDI and any user-accessible
  conductor, which includes the USB-C shell). See [section 7](#7-isolation-and-safety-non-isolated-design).

---

## 2. The standards

| Standard | Year | Name | PSE Type | Min class | Max class | PSE out (W) | PD in (W) | PD in, rounded (W) | PSE V min | PSE V max | Pairs powered | Alt pairs powered | Max current | Current basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 802.3af | 2003 | PoE | Type 1 | 0 | 3 | 15.4 | 12.95 | 13.0 | 44 | 57 | 2 | – | 350 mA | – |
| 802.3at | 2009 | PoE+ | Type 2 | 0 | 4 | 30 | 25.5 | – | 50 | 57 | 2 | – | 600 mA | – |
| 802.3bt | 2018 | 4PPoE | Type 3 | 0 | 6 | 60 | 51 | – | 50 | 57 | 2 | 4 | 600 mA | Per pair |
| 802.3bt | 2018 | 4PPoE | Type 4 | 0 | 8 | 90 | 71.3 | – | 52 | 57 | 4 | – | ~960 mA | Per pair |

All of these were folded into IEEE 802.3-2022: Type 1 and 2 in clause 33, Type 3 and 4
in clause 145. Cable model: 20 Ω loop (Type 1), 12.5 Ω (Type 2, 3 and 4, per pairset).

### Per-class power

Evidence mark for this section: [Ethernet Alliance](#evidence-codes).

| Class | PD max (W) | PSE min out (W) | PD peak (W) | Note |
|---|---|---|---|---|
| 0 | 13.0 | 15.4 | – | Same as Class 3 |
| 1 | 3.84 | 4.0 | 5.0 | – |
| 2 | 6.49 | 6.7 | 8.36 | – |
| 3 | 13.0 | 14.0 | 14.4 | – |
| 4 | 25.5 | 30.0 | 28.3 | – |
| 5 | 40.0 | 45.0 | 42.0 | – |
| 6 | 51.0 | 60.0 | 53.5 | – |
| 7 | 62.0 | 75.0 | 65.1 | – |
| 8 | 71.3 | 90.0 | 74.9 | – |

### Minimum PD-side voltage by assigned class and PSE type

Evidence mark for this section: [Ethernet Alliance](#evidence-codes).

The PD never sees more than 57 V. The worst-case minimum depends on cable drop:

| Class | Type 1 PSE | Type 2 | Type 3 | Type 4 |
|---|---|---|---|---|
| 1 | 42.9 | 49.0 | 49.0 | 51.1 |
| 3 | 39.9 | 46.5 | 46.5 | 48.7 |
| 4 | – | 42.5 | 42.5 | 44.9 |
| 5 | – | – | 44.4 | 46.6 |
| 6 | – | – | 42.5 | 44.9 |
| 8 | – | – | – | 43.0 |

The classic "37–57 V" (af) figure is the PD's full operating window including
the minimum PSE and a full 100 m cable at max current. The 5 V converter has to run over that
window and has to survive the clamp voltage of the surge diode; its requirements are listed in
[Interfaces](../design/poe-front-end/README.md#interfaces).

### Non-IEEE variants worth tolerating

* **Passive PoE** (Ubiquiti, MikroTik, many cheap injectors): 24 V or 48 V,
  sometimes 12–56 V, applied permanently on pairs 4-5 (positive) and 7-8 (negative), no detection.
  The [discrete front end](../design/poe-front-end/README.md) starts on a passive 48 V supply,
  because nothing in it waits for a detection. It does not start on 24 V. The firmware cannot know what a passive supply can
  deliver.
* **Cisco UPOE and UPOE+**, **LTPoE++** (Analog Devices): proprietary pre-bt
  4-pair schemes. bt-compliant PSEs supersede them; not worth targeting.
* **802.3bu PoDL** (single-pair automotive and SPE): unrelated; ignore.

---

## 3. Wiring: Mode A, Mode B, polarity, and 1000BASE-T

* **Mode A** ("endspan", "alternative A"): power on pairs 1-2 and 3-6.
* **Mode B** ("midspan", "alternative B"): power on pairs 4-5 and 7-8.
* **4-pair (bt)**: both at once, each pairset from its own PSE channel.
* Polarity is not fixed in Mode A (MDI or MDI-X), so a PD **must accept either
  polarity on either pairset**. Standard solution: one full-wave bridge per
  pairset (8 diodes), outputs paralleled for a single-signature PD.
* With 1000BASE-T **all four pairs carry data**, so power is always injected
  as *phantom* power on the transformer centre taps: the + rail is the common
  mode of one pair, − is the common mode of the other. Data is differential,
  power is common-mode, so they coexist.

### Implications for an adapter with a switch IC

The adapter sits between the PoE switch and the Pi's own Ethernet jack, and its switch IC
terminates both links. The input jack connects to one PHY port of the switch IC and the
output jack to another, each through its own magnetics. No signal runs from one jack to the
other, so taking the power off has no effect on the link to the Pi.

The input port needs PoE-rated magnetics with the cable-side centre taps of all four pairs brought
out to the bridges. A PoE-capable magjack is cheap in volume. The output port takes
ordinary gigabit magnetics.

Note: the Raspberry Pi 5 brings its own magnetics' centre taps out on the
4-pin PoE header (VC1–VC4). A HAT-style design could take its power there,
but it does not give a USB-C adapter.

For bt 4-pair power both pairsets must be connected to the PD, i.e. all four
centre taps used.

---

## 4. The negotiation sequence, end to end

```
 V at PD (after bridge)
 57 ┤                                         ┌─────────── powered (MPS required)
    │                                         │
 42 ┤                                     ... ┘ ← PD UVLO on (≤ 42 V)
    │        class   class        class
20.5┤        ┌──┐    ┌─┐    ...   ┌─┐
14.5┤        │  │    │ │          │ │
10  ┤ det.   │  │mark│ │mark      │ │mark
 7  ┤ ┌┐┌┐   │  └────┘ └──  ...   │ └──┐
2.7 ┤─┘└┘└───┘                    │    │
  0 ┼─────────────────────────────────────────────▶ t
     detection   classification events (1..5)    power-on (≤ 400 ms after detection)
```

### 4.1 Detection (is there a PoE device here?)

| Parameter | PSE | PD | PD design value |
|---|---|---|---|
| Probe voltage, min | 2.8 V | 2.7 V | – |
| Probe voltage, max | 10 V | 10.1 V | – |
| Probe points | At least 2 | – | – |
| Probe point spacing | ≥ 1 V | – | – |
| Accept resistance (slope ΔV/ΔI), min | 19 kΩ | **23.75 kΩ** | 24.9 kΩ |
| Accept resistance (slope ΔV/ΔI), max | 26.5 kΩ | **26.25 kΩ** | 24.9 kΩ |
| Reject resistance, below | 15 kΩ | – | – |
| Reject resistance, above | 33 kΩ | – | – |
| Capacitance, min | – | 50 nF | 100 nF |
| Capacitance, max a PSE must accept | 150 nF | 120 nF | 100 nF |
| Capacitor voltage rating | – | – | 100 V |
| Voltage offset allowed (bridge drops) | – | ≤ 1.9 V | – |
| Current offset allowed | – | ≤ 10 µA | – |

The PD columns are from the [UNH-IOL test suite](#evidence-codes). The PSE measures
*incremental* resistance, so diode drops are tolerated, but anything nonlinear or leaky in
2.7–10.1 V breaks detection. **Nothing but the signature may draw current below about 11 V**,
which is why the class sink of the [discrete front end](../design/poe-front-end/README.md) sits
behind a 10 V zener diode.

### 4.2 Classification (how much power do you want?)

PSE drives 15.5–20.5 V (PD sees ≥ 14.5 V) and measures current. [Ethernet Alliance](#evidence-codes)

| Class signature | PD current min | PD current max | PSE threshold min (roughly) | PSE threshold max (roughly) |
|---|---|---|---|---|
| 0 | 0 mA | 4 mA | 0 mA | 5 mA |
| 1 | 9 mA | 12 mA | 8 mA | 13 mA |
| 2 | 17 mA | 20 mA | 16 mA | 21 mA |
| 3 | 26 mA | 30 mA | 25 mA | 31 mA |
| 4 | 36 mA | 44 mA | 35 mA | 45 mA |

PSE thresholds are wider than the PD currents. The PD currents are from the
[UNH-IOL test suite](#evidence-codes).

Between class events the PSE drops to a **mark event**: 7–10 V (PD sees
6.9–10 V), PD must draw **0.25–4 mA** and must *not* reset. Below 2.8 V for
≥ 15 ms resets the PD's classification state. [Ethernet Alliance](#evidence-codes)

Event timing [Ethernet Alliance](#evidence-codes):

| Event | PSE type | Min | Max | Note |
|---|---|---|---|---|
| First class event | Type 1 | 6 ms | 75 ms | – |
| First class event | Type 2 | 6 ms | 30 ms | – |
| First class event | Type 3 | **88 ms** | **105 ms** | "Long class event" |
| First class event | Type 4 | **88 ms** | **105 ms** | "Long class event" |
| Later class events | Any | 6 ms | 20 ms | – |
| Mark events | Any | ~6 ms | ~12 ms | – |
| Detection → power on | Any | – | 400 ms | – |

The PD can tell a Type 3 or 4 PSE from the long first event (≤ 75 ms ⇒ Type 1 or 2,
≥ 88 ms ⇒ Type 3 or 4).

**Multi-event classification.** The PSE grants power by how many class events
it runs; the PD learns its granted power by *counting* events. Single-signature
PD signatures for bt classes [Ethernet Alliance](#evidence-codes):

| PD class | Event 1 | Event 2 | Event 3 | Event 4 | Event 5 |
|---|---|---|---|---|---|
| Up to 4 | Own class | Own class | Own class | Own class | Own class |
| 5 | 4 | 4 | 0 | 0 | – |
| 6 | 4 | 4 | 1 | 1 | – |
| 7 | 4 | 4 | 2 | 2 | 2 |
| 8 | 4 | 4 | 3 | 3 | 3 |

Max events: Type 1 PSE = 1, Type 2 = 2, Type 3 = 4, Type 4 = 5.

Granted (assigned) class vs events seen, for a bt PD [Ethernet Alliance](#evidence-codes):

| PD class | 1 event | 2 events | 3 events | 4 events | 5 events |
|---|---|---|---|---|---|
| 5 | 3 | 4 | 4 | 5 | – |
| 6 | 3 | 4 | 4 | 6 | – |
| 7 | 3 | 4 | 4 | 6 | 7 |
| 8 | 3 | 4 | 4 | 6 | 8 |

| Assigned class | Power |
|---|---|
| 3 | 13 W |
| 4 | 25.5 W |
| 5 | 40 W |
| 6 | 51 W |
| 7 | 62 W |
| 8 | 71.3 W |

"Power demotion": a PSE short of budget deliberately gives fewer events (e.g. 3
events ⇒ Class 4) rather than refusing. **The PD must then limit itself to the
demoted power.** For this project that is the key output of the PoE side:
*events counted ⇒ power budget ⇒ what the USB-C side offers.* The front ends compared in
[section 6](#6-poe-front-end-of-the-yt9215-design) tell one event from more than one and do not
count further, which is enough up to Class 4.

A Type 1 (af) PSE never shows a second event, so a PD that sees one event must
stay ≤ 13 W.

**Autoclass (bt, optional)** [Ethernet Alliance](#evidence-codes): PD presents class signature 0 starting
~81 ms into the long first class event; after power-up it draws its real
maximum between 1.35 s and 3.65 s, and the PSE measures it (1.4–3.5 s window)
to allocate just that much plus margin. Not needed for this project.

### 4.3 Power-on, inrush, UVLO

* The PD must turn on by 42 V at its input and must turn off between 30 V and 36 V
  ([UNH-IOL test suite](#evidence-codes)). The hysteresis prevents oscillation on a long cable.
* The PSE limits the inrush current to 400–450 mA for up to 75 ms, provided the input
  capacitance of the PD is below 180 µF ([IEEE draft](#evidence-codes)). A PD with more
  capacitance has to limit the inrush current itself.
* A PD that wants more than Class 3 has to stay within 13 W for the first 80 ms after power
  appears, and after that until the PSE has granted more.
* Peak and average limits per class (the [per-class power table](#per-class-power)) apply from then on.

### 4.4 Maintain Power Signature (MPS)

Evidence mark for this section: [TI application note](#evidence-codes).

To keep power on, the PD must periodically draw enough current or the PSE
disconnects:

| | Class 1–4 | Class 5–8 |
|---|---|---|
| I_hold (min) | 10 mA | 16 mA |
| Min on-time with a Type 1 PSE | 75 ms | – |
| Min on-time with a Type 2 PSE | 75 ms | – |
| Min on-time with a Type 3 PSE (long class event seen) | 7 ms | 7 ms |
| Min on-time with a Type 4 PSE (long class event seen) | 7 ms | 7 ms |
| Max dropout with a Type 1 PSE | 250 ms | – |
| Max dropout with a Type 2 PSE | 250 ms | – |
| Max dropout with a Type 3 PSE | 310 ms | 310 ms |
| Max dropout with a Type 4 PSE | 310 ms | 310 ms |

The adapter never comes near this. The YT9215SCH alone draws 0.66 W with no link, which is
more than 11 mA at 57 V, so the port stays powered when the Pi is shut down.

### 4.5 LLDP (data-link layer classification)

A PSE and a PD can also agree on power in LLDP frames after the link is up. For a Type 2
PSE this is one of two ways to grant 25.5 W: it either runs two class events, or it runs one
event, supplies 13 W and waits for the PD to ask for more over LLDP. A Type 2 PD is required
to support both ([IEEE draft](#evidence-codes), item PD13 of the conformance statement). Type 3
and Type 4 PSEs grant by class events and use LLDP to adjust the allocation afterwards.

The adapter's switch IC terminates the link from the PSE, so LLDP has to come from the
adapter's firmware. Whether the YT9215 CPU can send a frame is an open question in
[The RISC-V CPU inside the YT9215](yt9215-embedded-cpu.md#packet-path). Without LLDP the
adapter gets 25.5 W only from a PSE that grants by class events; the options are compared in
[Getting more than 13 W](../design/poe-front-end/README.md#getting-more-than-13-w).

---

## 5. Raspberry Pi 5 power budget against PoE classes

| Granted | Standard | Events | PD input (W) | 5 V converter output (W) | Left for USB-C (W) | USB-C current at 5 V (A) | Pi 5 behaviour |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Class 3 | 802.3af | 1 | 12.95 | 11.0 | 9.0 | 1.8 | USB limited to 600 mA |
| Class 4 | 802.3at | 2 | 25.5 | 21.9 | 19.9 | 4.0 | Like the official PoE+ HAT |
| Class 5 | 802.3bt | 4 | 40 | 35 | 33 | 5.0 | Full 5 V at 5 A |
| Class 6 | 802.3bt | 4 | 51 | 45 | 43 | 5.0 | Full 5 V at 5 A |

The Class 3 and Class 4 rows are worked out in
[Power sequencing](../design/poe-front-end/README.md#power-sequencing): bridge and switch losses at
the lowest PD voltage, 90 % converter efficiency and 2.0 W for the adapter's own switch. The
Class 5 and Class 6 rows use about 88 % from PD input to the 5 V rail and the same 2.0 W. On
Class 3 a Pi 5 under load may brown out.

Both front ends of [section 6](#6-poe-front-end-of-the-yt9215-design) stop at Class 4. Class 5 and Class 6
need the changing class signature of [section 4.2](#42-classification-how-much-power-do-you-want)
and a count of four events. The firmware tells the USB-C side how much it may offer; that side is
covered in [`usb-c-pd.md`](usb-c-pd.md).

---

## 6. PoE front end of the YT9215 design

The design has no MCU that could measure the port or set a class current. The YT9215 and
its CPU are unpowered until the PSE has switched the port on, so detection, classification and
inrush limiting are done by a front end that needs no firmware. Two ways to build it are set
side by side in [Discrete PoE front end](../design/poe-front-end/README.md): from discrete parts,
or around a PD controller IC. That note gives the discrete schematic, its simulation against
the limits of [section 4](#4-the-negotiation-sequence-end-to-end), the bill of materials with
prices, and the [comparison](../design/poe-front-end/README.md#discrete-parts-or-a-pd-controller-ic)
of the two.

What either front end passes to the firmware is one logic signal, T2P, which says whether the
PSE ran one class event or more than one. The firmware turns that, or an LLDP answer
([section 4.5](#45-lldp-data-link-layer-classification)), into a power budget for the downstream
ports and the USB-C output.

A PoE powered device run by an external MCU, with its measurement needs, its bootstrap supply
and a firmware state machine, is described in the archived note
[PoE powered device run by an external MCU](../archive/research/poe-software-pd.md).

---


## 7. Isolation and safety (non-isolated design)

* 802.3 (clause 33.4.1 and 145.4.1) requires the PD to provide **1500 Vrms
  isolation** between the MDI (all PoE wiring) and all accessible external
  conductors, including frame ground. A USB-C output connector tied to the
  PoE rail violates that, so the adapter is not formally compliant.
* Practically, PSE outputs are floating, so the 48 V rail is floating relative
  to earth and a non-isolated PD works. The risk is a second earth path: a Pi
  connected through the adapter and also to an earthed monitor, USB device or
  another network port. The PoE "−" rail then gets referenced to earth through
  the Pi's GND. This is usually harmless with one floating PSE, but surge and
  ESD events on the cable now couple into the Pi. Mitigations: robust TVS on
  the 48 V rail, the Ethernet data path stays transformer-isolated (each port of the
  switch IC has its own magnetics), and documenting the limitation.
* The data path stays transformer-isolated on both links: the magnetics of the input port
  stand between the PoE cable and the switch IC, and the magnetics of the output port stand
  between the switch IC and the cable to the Pi ([section 3](#3-wiring-mode-a-mode-b-polarity-and-1000base-t)).

---

## 8. Open questions

1. Build a front end ([section 6](#6-poe-front-end-of-the-yt9215-design)) and measure it on real
   Type 1 and Type 2 PSEs. For the discrete one, the
   [open points](../design/poe-front-end/README.md#limits-and-open-points) list what to measure.
2. Find out whether custom firmware on the YT9215 CPU can send and receive LLDP frames
   ([section 4.5](#45-lldp-data-link-layer-classification)).
3. Choose the PoE-rated magnetics of the input port ([section 3](#3-wiring-mode-a-mode-b-polarity-and-1000base-t)) and verify that their
   centre taps carry the full PoE current.
4. Check the numbers with the mark [Not checked](#evidence-codes) against IEEE 802.3-2022
   clauses 33 and 145.

## Sources

* Ethernet Alliance, *Overview of 802.3bt Power over Ethernet* white paper:
  <https://ethernetalliance.org/wp-content/uploads/2019/12/WP_EA_Overview8023bt_V2p1_FINAL.pdf>
* TI SLVAEE5, TPS23754 application note, Maintain Power Signature section:
  <https://www.ti.com/document-viewer/lit/html/SLVAEE5/maintain-power-signature-mps-t5982369-2>
* UNH-IOL, *Clause 33 PD parametric test suite*, version 1.5:
  <https://www.iol.unh.edu/sites/default/files/testsuites/ethernet/CL33_PD/PD_Test_Suite_v1.5.pdf>
* IEEE 802.3at draft D3.0, conformance statement of clause 33:
  <https://www.ieee802.org/3/at/comments/D3.0/attach/nadeau/802.3at%20Draft%20PICS%20v0.3.pdf>
* Text of clause 33.3 as circulated in the 802.3bt task force:
  <https://www.ieee802.org/3/4PPOE/email/pdfrCowflqhcH.pdf>
* IEEE 802.3bt public classification baseline:
  <https://grouper.ieee.org/groups/802/3/bt/public/jul15/dual_sig_classification_baseline_v124.pdf>
* IEEE 802.3-2022, clauses 33 (Type 1 and 2) and 145 (Type 3 and 4): the normative
  reference for everything in this note.
