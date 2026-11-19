# PoE powered device run by an external MCU

> **Archived.** This note is not part of the current design. It describes a PoE powered device in which a general-purpose MCU with an ADC and a PWM output measures the port and sets the class current. The current design uses only the YT9215 switch IC and its internal RISC-V CPU, and its PoE front end needs no firmware; it is described in [Discrete PoE front end](../../design/poe-front-end/README.md). The [archive index](../README.md) lists every archived note.

The standards, limits and timings this note relies on are in
[PoE powered device](../../research/poe.md). The classification tables it refers to are in
[section 4.2 of that note](../../research/poe.md#42-classification-how-much-power-do-you-want).

## 1. What a software PD needs electrically

### 1.1 Measurement

| Quantity | Range min | Range max | Needed resolution | Rate |
| --- | --- | --- | --- | --- |
| Port voltage (after bridge) | 0 V | 60 V | ~0.1 V | ≥ 1 kHz |
| Class and mark current | 0 mA | 50 mA | ≤ 0.5 mA | ≥ 1 kHz |
| Load current (optional) | 0 A | 2 A | ~10 mA | ~1 kHz |

Notes on the rows of this table:

- **Port voltage (after bridge)**, why: To place the [voltage window edges](#voltage-window-edges).
- **Class and mark current**, why: The 36–44 mA window is ±10 %.

<a id="voltage-window-edges"></a>

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

### 1.2 Timing

Everything is millisecond-scale. Hard deadlines:

* Present the right class current within a few ms of the class event starting
  (PSE samples after the first ~6 ms; Type 2 events are as short as 6 ms).
* Distinguish class (≥ 14.5 V) vs mark (≤ 10 V) vs reset (< 2.8 V) and count
  transitions.
* Time the first class event (75 ms vs 88 ms boundary) to know Type 1 or 2 from Type 3 or 4.

A 1 kHz control loop is the minimum; 10 kHz polling or a comparator interrupt
is comfortable.

### 1.3 The bootstrap problem

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
  event. For a Type 1 or 2 PSE that can be as short as 6 ms, so boot time must be
  ~1–2 ms; Type 3 and Type 4 PSEs give 88 ms. A hardware default (class 4 sink enabled
  by default, MCU only modulates it) removes the boot-time risk: classes 5–8
  present 4 in events 1–2 anyway, and the MCU switches to the 0, 1, 2 or 3 signature
  from event 3 onward.
* MCU's own supply current counts toward the class current; the sink adds the
  difference, so the MCU must measure what it draws and trim.

### 1.4 Minimal external parts (architecture B)

| Function | Property | Value |
| --- | --- | --- |
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
| Class and mark sink | Transistor option 1 | NPN |
| Class and mark sink | Transistor option 2 | NMOS |
| Class and mark sink | Sense resistor | Yes |
| Class and mark sink | Reference | MCU PWM-RC |
| Class and mark sink | Current range | 0–45 mA |
| Class and mark sink | Duration | ≤ 105 ms |
| Class and mark sink | Dissipation during class | ~1 W |
| Class and mark sink | Worst case | 20 V × 44 mA |
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

Longer entries for this table:

- **Signature, why bt requires it**: The signature must look invalid in some states.

That is roughly 15–25 jellybean parts. For comparison, dedicated PD controller
ICs (TI TPS2375 and TPS2378, TPS23730 for bt; ADI and Silvertel PD modules; Silicon
Labs Si34xx) integrate the signature, class, UVLO and hot-swap FET, and cheap
Chinese PD controllers exist too. Whether discrete + MCU actually beats a
~$0.30–1 PD controller IC at volume is not established here and should be
priced out before committing.


## 2. Firmware state machine (sketch)

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
  granted = f(events, PD class)   ← classification tables of poe.md
  tell USB-PD side the budget; enable buck
RUN:
  monitor Vport/current, enforce budget, maintain MPS if Pi is idle
  V < UVLO-off ⇒ shut down
PASSIVE (Vport > 30 V with no class sequence seen):
  assume ≤ 13 W unless configured otherwise
```
