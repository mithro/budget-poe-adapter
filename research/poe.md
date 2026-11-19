# PoE (Power over Ethernet) for a cheap, software-driven PD

Research notes for the open source PoE → USB-C adapter. Scope: the PoE
standards, how a Powered Device (PD) negotiates power, and the electrical
requirements for doing that negotiation with a budget MCU (WCH CH32V0xx /
CH32V2xx, RP2040 and RP2350) plus a handful of discrete parts, non-isolated,
with a 1000BASE-T data path passed through to the Raspberry Pi.

Confidence: numbers in tables marked **[EA]** were checked against the
Ethernet Alliance 802.3bt overview white paper; **[TI]** against TI's PD
application note. Unmarked numbers are from memory of IEEE 802.3 clause 33 and 145
and widely published PD controller datasheets; they are believed correct but
anything a design depends on should be re-checked against IEEE 802.3-2022
(clauses 33 and 145) before layout.

---

## 1. TL;DR for this project

* PoE negotiation is **entirely DC and slow** (millisecond timings, no
  modulation, no carrier). There is nothing to "bit-bang" in the RF sense: a
  PD just has to look like a specific resistor, then a specific current sink,
  at specific voltage windows, then switch the load on gracefully. A 10–12 bit
  ADC sampling at ~1–10 kHz and a PWM-driven current sink are more than
  enough.
* The hard constraint is **power for the MCU before PoE is granted**: during
  detection (2.7–10.1 V) the PD may leak no more than ~10 µA besides the
  25 kΩ signature, so the MCU must be off. It can wake during classification
  (14.5–20.5 V) and must survive mark events (6.9–10 V) on ≤ 4 mA total.
* **Raspberry Pi 5 at full power (5 V at 5 A = 25 W out) needs ~28–29 W at the
  PD input**, which is more than 802.3at Class 4 (25.5 W). Full power needs an
  **802.3bt Class 5 (40 W) PD on a 4-pair Type 3 and 4 PSE**. On an 802.3at switch
  the adapter should fall back to ~4.5 A at 5 V (≈ 22 W).
* Physical-layer classification alone is sufficient for all classes up to 8.
  LLDP is not required, which matters because a passthrough adapter has no
  Ethernet PHY of its own.
* Non-isolated is functionally fine but **not 802.3-compliant** (the standard
  requires 1500 Vrms isolation between the MDI and any user-accessible
  conductor, which includes the USB-C shell). See §8.

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

### Per-class power **[EA]**

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

### Minimum PD-side voltage by assigned class and PSE type **[EA]**

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
the minimum PSE and a full 100 m cable at max current. Design the buck
converter for **~36–57 V input** (and 60 V absolute with a TVS).

### Non-IEEE variants worth tolerating

* **Passive PoE** (Ubiquiti, MikroTik, many cheap injectors): 24 V or 48 V,
  sometimes 12–56 V, applied permanently on pairs 4-5(+)/7-8(−), no detection.
  An MCU-based PD can recognise "voltage already present above 30 V without a
  detection and classification sequence" and simply run. Worth supporting: it is
  free in firmware.
* **Cisco UPOE and UPOE+**, **LTPoE++** (Analog Devices): proprietary pre-bt
  4-pair schemes. bt-compliant PSEs supersede them; not worth targeting.
* **802.3bu PoDL** (single-pair automotive and SPE): unrelated; ignore.

---

## 3. Wiring: Mode A, Mode B, polarity, and 1000BASE-T

* **Mode A** ("endspan", alternative A"): power on pairs 1-2 and 3-6.
* **Mode B** ("midspan", alternative B"): power on pairs 4-5 and 7-8.
* **4-pair (bt)**: both at once, each pairset from its own PSE channel.
* Polarity is not fixed in Mode A (MDI or MDI-X), so a PD **must accept either
  polarity on either pairset**. Standard solution: one full-wave bridge per
  pairset (8 diodes), outputs paralleled for a single-signature PD.
* With 1000BASE-T **all four pairs carry data**, so power is always injected
  as *phantom* power on the transformer centre taps: the + rail is the common
  mode of one pair, − is the common mode of the other. Data is differential,
  power is common-mode, so they coexist.

### Implications for a gigabit passthrough adapter

The adapter sits between the switch and the Pi's own Ethernet jack. It must
take common-mode DC off the four pairs without degrading the 125 MBd PAM-5
signal (energy up to ~100 MHz; return loss and insertion loss limits apply from
1 MHz). Options, cheapest last:

1. **Back-to-back magnetics.** Switch-side RJ45 with PoE-rated integrated
   magnetics (centre taps brought out) wired to a second set of magnetics
   driving the Pi-side jack. Easiest to get right; four transformer channels
   per side. PoE-capable magjacks are cheap in volume.
2. **Single 4-channel PoE splitter transformer**, wire side on the input jack,
   centre taps to the bridges, other side to the output jack. Half the
   magnetics of option 1. The Pi's own magnetics then see a normal
   transformer-coupled link.
3. **Inductive tap**: series DC-blocking capacitors on each of the 8 wires
   towards the Pi and a matched pair of high-current inductors (or a
   centre-tapped common-mode choke) from each pair to the bridge. Fewest
   parts, but inductor matching, saturation at 0.6–1 A and return loss
   become the design problem. Many cheap "gigabit PoE splitters" do this.

Note: the Raspberry Pi 5 brings its own magnetics' centre taps out on the
4-pin PoE header (VC1–VC4). A HAT-style design could use that and skip the
passthrough entirely, but it does not give a USB-C adapter.

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
| Accept resistance (slope ΔV/ΔI), min | 19 kΩ | **23.75 kΩ** | 24.9 kΩ 1 % |
| Accept resistance (slope ΔV/ΔI), max | 26.5 kΩ | **26.25 kΩ** | 24.9 kΩ 1 % |
| Reject resistance, below | 15 kΩ | – | – |
| Reject resistance, above | 33 kΩ | – | – |
| Capacitance, min | – | 50 nF | 100 nF (typ.) |
| Capacitance, max | 150 nF (must accept) | 120 nF | 100 nF (typ.) |
| Capacitor voltage rating | – | – | 100 V |
| Voltage offset allowed (bridge drops) | – | ≤ 1.9 V | – |
| Current offset allowed | – | ≤ 10 µA | – |

The PSE measures *incremental* resistance, so diode drops are tolerated, but
anything nonlinear or leaky in 2.7–10.1 V breaks detection. **This is why the
MCU and its regulator must be completely off below ~11–12 V.**

### 4.2 Classification (how much power do you want?)

PSE drives 15.5–20.5 V (PD sees ≥ 14.5 V) and measures current. **[EA]**

| Class signature | PD current min | PD current max | PSE threshold min (roughly) | PSE threshold max (roughly) |
|---|---|---|---|---|
| 0 | 1 mA | 4 mA | 0 mA | 5 mA |
| 1 | 9 mA | 12 mA | 8 mA | 13 mA |
| 2 | 17 mA | 20 mA | 16 mA | 21 mA |
| 3 | 26 mA | 30 mA | 25 mA | 31 mA |
| 4 | 36 mA | 44 mA | 35 mA | 45 mA |

PSE thresholds are wider than the PD currents.

Between class events the PSE drops to a **mark event**: 7–10 V (PD sees
6.9–10 V), PD must draw **0.25–4 mA** and must *not* reset. Below 2.8 V for
≥ 15 ms resets the PD's classification state. **[EA]**

Event timing **[EA]**:

| Event | PSE type | Min | Max | Note |
|---|---|---|---|---|
| First class event | Type 1 | 6 ms | 75 ms | – |
| First class event | Type 2 | 6 ms | 30 ms | – |
| First class event | Type 3 | **88 ms** | **105 ms** | "Long class event" |
| First class event | Type 4 | **88 ms** | **105 ms** | "Long class event" |
| 2nd–5th class events | Any | 6 ms | 20 ms | – |
| Mark events | Any | ~6 ms | ~12 ms | – |
| Detection → power on | Any | – | 400 ms | – |

The PD can tell a Type 3 and 4 PSE from the long first event (≤ 75 ms ⇒ Type 1 and 2,
≥ 88 ms ⇒ Type 3 and 4).

**Multi-event classification.** The PSE grants power by how many class events
it runs; the PD learns its granted power by *counting* events. Single-signature
PD signatures for bt classes **[EA]**:

| PD class | Event 1 | Event 2 | Event 3 | Event 4 | Event 5 |
|---|---|---|---|---|---|
| 0–4 | Own class | Own class | Own class | Own class | Own class |
| 5 | 4 | 4 | 0 | 0 | – |
| 6 | 4 | 4 | 1 | 1 | – |
| 7 | 4 | 4 | 2 | 2 | 2 |
| 8 | 4 | 4 | 3 | 3 | 3 |

Max events: Type 1 PSE = 1, Type 2 = 2, Type 3 = 4, Type 4 = 5.

Granted (assigned) class vs events seen, for a bt PD **[EA]**:

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
*events counted ⇒ power budget ⇒ which USB-PD PDOs the USB-C side offers.*

A Type 1 (af) PSE never shows a second event, so a PD that sees one event must
stay ≤ 13 W.

**Autoclass (bt, optional)** **[EA]**: PD presents class signature 0 starting
~81 ms into the long first class event; after power-up it draws its real
maximum between 1.35 s and 3.65 s, and the PSE measures it (1.4–3.5 s window)
to allocate just that much plus margin. Not needed for this project.

### 4.3 Power-on, inrush, UVLO

* PD must turn on by Vport ≤ 42 V and turn off below ~30–36 V (hysteresis
  prevents oscillation on a long cable). The PD's own UVLO gates the hot-swap
  switch.
* PSE limits inrush to ~400–450 mA for 50–75 ms (Type 1 and 2). The PD should
  charge its bulk capacitance under that and keep its converter off (or in
  soft-start) until ≥ 80 ms after power appears, then may draw full class
  power.
* Peak and average limits per class (table in §2) apply from then on.

### 4.4 Maintain Power Signature (MPS) **[TI]**

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

A Pi running never comes near this. It matters if the Pi is shut down: the
MCU can pulse a dummy load (or itself at full speed) to keep the port alive, or
deliberately stop to power-cycle the Pi from the switch.

### 4.5 LLDP (data-link layer classification)

Optional for every class. Used to fine-tune allocation after power-up. A
passthrough adapter has no PHY so it cannot speak LLDP; the Pi could, but the
adapter does not need it. Physical classification alone gets up to Class 8.

---

## 5. Raspberry Pi 5 power budget against PoE classes

| Granted | Standard | Events | PD input | PD peak | 5 V output | 5 V current | Pi 5 behaviour | Caveat | Comparable to |
|---|---|---|---|---|---|---|---|---|---|
| Class 3 | af | 1 | 13 W | – | ~11.5 W | ≈ 2.3 A | Boots with USB current limited to 600 mA | May brown out under load | – |
| Class 4 | at | 2 | 25.5 W | 28.3 W | ~22.5 W | ≈ 4.5 A | – | – | Official PoE+ HAT (5 V at 4 A) |
| Class 5 | bt | 4 | 40 W | – | ~35 W | – | **Full 5 V at 5 A** | Has margin | – |
| Class 6 | bt | – | 51 W | – | ~45 W | – | Full power | Headroom for other loads | – |

The 5 V output assumes ~90 % efficiency, including bridge losses.

So the adapter should request **Class 5 or 6**, count events, and tell the
USB-PD side whether it may offer 5 V at 5 A or only 5 V at 3 A (or a ~4.5 A
custom limit). The 5 V at 5 A negotiation itself is covered by the USB-PD
research thread.

---

## 6. What a software PD needs electrically

### 6.1 Measurement

| Quantity | Range min | Range max | Needed resolution | Why | Rate |
|---|---|---|---|---|---|
| Port voltage (after bridge) | 0 V | 60 V | ~0.1 V | To place the voltage windows below | ≥ 1 kHz |
| Classification current | 0 mA | 50 mA | ≤ 0.5 mA | The 36–44 mA window is ±10 % | ≥ 1 kHz |
| Load current (optional) | 0 A | 2 A | ~10 mA | – | ~1 kHz |

| Voltage window edge to resolve |
|---|
| 2.7 V |
| 10.1 V |
| 14.5 V |
| 20.5 V |
| 42 V |

A 60 V : 3.3 V divider (e.g. 330 kΩ over 18 kΩ) into a 12-bit ADC gives ~15 mV/LSB.
The CH32V003 has a 10-bit ADC (~60 mV/LSB on that divider): still fine. The
divider must be switched in only after the MCU is up, or be high enough
(> 2 MΩ total) that it disappears into the 10 µA detection offset budget.
RP2040's ADC is ~9 ENOB but adequate. No DAC is needed: a PWM + RC filter
setting a reference for a transistor current sink is sufficient.

### 6.2 Timing

Everything is millisecond-scale. Hard deadlines:

* Present the right class current within a few ms of the class event starting
  (PSE samples after the first ~6 ms; Type 2 events are as short as 6 ms).
* Distinguish class (≥ 14.5 V) vs mark (≤ 10 V) vs reset (< 2.8 V) and count
  transitions.
* Time the first class event (75 ms vs 88 ms boundary) to know Type 1 and 2 vs 3 and 4.

A 1 kHz control loop is the minimum; 10 kHz polling or a comparator interrupt
is comfortable.

### 6.3 The bootstrap problem

The MCU cannot be powered during detection and must be powered (or the class
current must be hardware-generated) by the first class event. Two workable
architectures:

**A. Hardware signature + hardware class, MCU only after power-on (simplest).**
Discrete circuit does detection and a fixed class current (e.g. Class 4 for the
first two events). The MCU boots from the 48 V rail after power-on and cannot
count events, so it does not know the granted class and must assume the lowest
it could have been given. Fine for an af- and at-only product; loses bt.

**B. MCU wakes at the first class event (recommended).**
* A small high-voltage regulator (depletion-mode MOSFET + zener, or a 60 V LDO
  with an enable comparator) powers the MCU only when Vport > ~12 V, with
  hysteresis down to ~6 V so it stays up through mark events.
* Hold-up capacitor sized to ride through a ≤ 12 ms mark event.
* **Total draw during mark must be ≤ 4 mA** (incl. the 25 kΩ, ~0.4 mA at 10 V).
  CH32V003 at low clock is a few mA; RP2040 (~20 mA running) is too heavy
  here, so it would need a separate tiny supervisor or very aggressive clock
  gating. This favours a CH32V003-class part as the PoE controller, possibly
  alongside a bigger MCU for USB-PD.
* MCU must boot and enable its class current sink well inside the first class
  event. For a Type 1 and 2 PSE that can be as short as 6 ms, so boot time must be
  ~1–2 ms; Type 3 and 4 PSEs give 88 ms. A hardware default (class 4 sink enabled
  by default, MCU only modulates it) removes the boot-time risk: classes 5–8
  present 4 in events 1–2 anyway, and the MCU switches to the 0, 1, 2 and 3 signature
  from event 3 onward.
* MCU's own supply current counts toward the class current; the sink adds the
  difference, so the MCU must measure what it draws and trim.

### 6.4 Minimal external parts (architecture B)

| Function | Property | Value |
|---|---|---|
| Input rectifier | Part | 2 bridges |
| Input rectifier | Diodes | 8 × 100 V |
| Input rectifier | Placement | One bridge per pairset |
| Input rectifier | Current | 0.6–1 A |
| Input rectifier | Diode option 1 | Schottky |
| Input rectifier | Diode option 2 | Ideal-diode MOSFET bridge (for efficiency) |
| Surge | Part | SMAJ58A TVS |
| Surge | Placement | Across bridge output |
| Signature | Resistor | 24.9 kΩ 1 % |
| Signature | Capacitor | 100 nF |
| Signature | Capacitor rating | 100 V |
| Signature | Optional disconnect | MOSFET |
| Signature | Disconnect when | After power-on |
| Signature | Disconnect saving | ~2 mW |
| Signature | Why bt wants it | The signature must look invalid in some states |
| Classification sink | Transistor option 1 | NPN |
| Classification sink | Transistor option 2 | NMOS |
| Classification sink | Sense resistor | Yes |
| Classification sink | Reference | MCU PWM-RC |
| Classification sink | Current range | 0–45 mA |
| Classification sink | Duration | ≤ 105 ms |
| Classification sink | Dissipation during class | ~1 W |
| Classification sink | Worst case | 20 V × 44 mA |
| MCU bootstrap supply | Pass element option 1 | Depletion NMOS |
| MCU bootstrap supply | Pass element option 2 | Zener |
| MCU bootstrap supply | Pass element option 3 | HV LDO |
| MCU bootstrap supply | UVLO comparator | Yes |
| MCU bootstrap supply | Turns on | > 12 V |
| MCU bootstrap supply | Turns off | < 6 V |
| Hot-swap switch | Part | 100 V NMOS |
| Hot-swap switch | Position | Low side |
| Hot-swap switch | Gate drive | MCU |
| Hot-swap switch | Slew limit | RC |
| Hot-swap switch | Inrush | < 400 mA |
| Sensing | Voltage | Divider |
| Sensing | Current | Sense resistor |
| Sensing | Op-amp | Optional |
| Sensing | Destination | MCU ADC |
| Power stage | Part | 60 V synchronous buck |
| Power stage | Output | The USB-PD rail(s) |
| Power stage | Scope | Outside PoE negotiation |

That is roughly 15–25 jellybean parts. For comparison, dedicated PD controller
ICs (TI TPS2375 and TPS2378, TPS23730 for bt; ADI and Silvertel PD modules; Silicon
Labs Si34xx) integrate the signature, class, UVLO and hot-swap FET, and cheap
Chinese PD controllers exist too. Whether discrete + MCU actually beats a
~$0.30–1 PD controller IC at volume is not established here and should be
priced out before committing.

---

## 7. Firmware state machine (sketch)

```
OFF (MCU unpowered; hardware signature present)
  → first class event: MCU boots, hardware class-4 sink already on
CLASSIFY:
  count events; time event 1 (≥88 ms ⇒ Type 3/4 PSE)
  events 1–2: present class 4
  events 3+: present 0/1/2/3 for requested class 5/6/7/8
  mark: drop sink, keep total draw 0.25–4 mA
  V < 2.8 V for ≥15 ms: reset count (MCU may brown out; that is fine)
POWER_ON (V rises past ~42 V):
  ramp hot-swap gate (inrush < 400 mA), wait ≥ 80 ms
  granted = f(events, PD class)   ← table in §4.2
  tell USB-PD side the budget; enable buck
RUN:
  monitor Vport/current, enforce budget, maintain MPS if Pi is idle
  V < UVLO-off ⇒ shut down
PASSIVE (Vport > 30 V with no class sequence seen):
  assume ≤ 13 W unless configured otherwise
```

---

## 8. Isolation and safety (non-isolated design)

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
  the 48 V rail, the Ethernet data path stays transformer-isolated (the Pi's
  magnetics remain in circuit), and documenting the limitation.
* The data path itself stays isolated in all options in §3, because the Pi's
  own magnetics are still in the link.

---

## 9. Open questions for the next step

1. Price discrete + MCU (architecture B) against the cheapest PD controller IC
   at 1k units; this decides whether "software PD" is a cost win or a hobby
   win.
2. Pick the PoE controller MCU: needs ≤ 4 mA during mark events and ~1–2 ms
   boot. CH32V003 looks like the best fit; RP2040 and RP2350 likely too power
   hungry for this role alone.
3. Choose the gigabit passthrough option (§3) and verify return loss with the
   chosen magnetics and inductors.
4. Confirm the inrush, UVLO and offset figures (unmarked numbers above)
   against IEEE 802.3-2022 clauses 33 and 145.

## Sources

* Ethernet Alliance, *Overview of 802.3bt Power over Ethernet* white paper:
  <https://ethernetalliance.org/wp-content/uploads/2019/12/WP_EA_Overview8023bt_V2p1_FINAL.pdf>
* TI SLVAEE5, TPS23754 application note, Maintain Power Signature section:
  <https://www.ti.com/document-viewer/lit/html/SLVAEE5/maintain-power-signature-mps-t5982369-2>
* IEEE 802.3bt public classification baseline:
  <https://grouper.ieee.org/groups/802/3/bt/public/jul15/dual_sig_classification_baseline_v124.pdf>
* IEEE 802.3-2022, clauses 33 (Type 1 and 2) and 145 (Type 3 and 4): the normative
  reference for everything above.
