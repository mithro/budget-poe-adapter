# PoE → USB-C adapter: block diagram and rough BOM cost

![Block diagram](block-diagram.svg)

Rough first pass, 2026-10-21 (updated for 5 V + 12 V output). Built
from `research/poe.md`, `research/usb-c-pd.md` and
`research/ethernet-switch.md`. Line items and per-line prices are in
[`bom-rough.csv`](bom-rough.csv). The diagram is also available as
[`block-diagram.png`](block-diagram.png).

**Pricing basis:** 1k units, LCSC parts with JLCPCB PCB + assembly. Only the
RTL8363NB price ($1.43 @1k) was checked live (in the switch research). Every
other price is an estimate from typical LCSC pricing for that part class and
is tagged high/medium/low confidence in the CSV. Treat the totals as ±30 %.

## Summary

| | With switch (RTL8363NB + CH32V307) | Without switch (passive passthrough) |
|---|---|---|
| **Rough BOM + PCB + assembly @1k** | **≈ $8.60** (likely $7.50–10.50) | **≈ $4.10** (likely $3.60–5.30) |
| USB-C output | USB-PD 5 V and 12 V | same |
| Gigabit to the Pi | yes, switched | yes, passive |
| MCU on the network (LLDP, stats, config) | yes | no |
| LLDP power negotiation | possible | no |
| Extra load on the PoE budget | ~0.5–1 W for the switch | none |
| PCB | 4-layer | 2-layer possible |

The switch costs about **$4.50 extra** per unit. Of that, $1.62 is the switch
and its crystal/passives, $0.95 is the bigger MCU, $1.05 is the second set of
magnetics, and the rest is the 4-layer board and more placements.

Adding 12 V output costs about **$0.20** per unit on either variant compared
with a 5 V-only design (see below).

## Output voltages: 5 V and 12 V

The USB-C port is a USB-PD source with two fixed PDOs, **5 V and 12 V**.
That covers the Pi 5 (5 V / 5 A) and 12 V devices such as SBCs, routers,
cameras and small displays. 9/15/20 V and PPS are out of scope.

### What changes in hardware compared with 5 V only

| Change | Why | Cost delta @1k |
|---|---|---:|
| 5 V / 12 V select: a GPIO-driven NMOS switches an extra resistor into the buck's feedback divider | Two fixed set points, no PWM "DAC". With the GPIO low or floating the buck outputs 5 V, so a firmware fault can't leave 12 V on a 5 V-only sink | +$0.02 |
| Output caps rated 16–25 V | 12 V rail | +$0.02 |
| VBUS PMOS gets a gate zener and an NPN driver | Keeps Vgs within limits when switching 12 V | +$0.02 |
| 15 V TVS on VBUS instead of 6–7 V | Clamp level for a 12 V rail | +$0.01 |
| CC1/CC2 protection against a 12 V short (series NMOS clamps or a CC OVP IC) | A bad cable or plug twist can put VBUS on CC, which would kill 3.3 V MCU pins | +$0.10 |
| 3.3 V rail fed from a 5–12 V rail (18 V-rated buck / 16 V LDO) | The rail it was fed from is no longer fixed at 5 V | +$0.01–0.05 |
| **Total** | | **≈ +$0.20** |

The buck controller, FETs and inductor do not change: 57 V → 5 V at 5 A is
still the sizing case, and 12 V is at most ~3 A. Firmware gets one extra PDO,
a GPIO toggle on Request, a VBUS-in-range check before PS_RDY, and a drop
back to 5 V on Hard Reset or detach.

### What the PoE class allows

The PDOs the adapter offers come from the PoE class it was granted (counted
class events, `poe.md` §4.2), at roughly 90 % efficiency:

| Granted PoE class | USB-C budget | PDOs offered |
|---|---|---|
| Class 3 (af, 13 W) | ~11 W | 5 V / 2.2 A, 12 V / 0.9 A |
| Class 4 (at, 25.5 W) | ~22 W (~21 W with the switch) | 5 V / 3 A (4.4 A with the Pi override), 12 V / 1.8 A |
| Class 5 (bt, 40 W) | ~35 W | 5 V / 5 A*, 12 V / 2.9 A |
| Class 6 (bt, 51 W) | ~45 W | 5 V / 5 A*, 12 V / 3 A |

\* 5 A needs a captive or e-marked cable (`usb-c-pd.md` §5.4).

**Caveat:** a 5 V + 12 V source does not follow the PD "power rules", which
expect 9 V on any source above 15 W. This only matters for certification.
Functionally, a sink that wants 12 V will request it. Phones and laptops that
only ask for 9/15/20 V will fall back to 5 V, which is safe but slow.

## Block diagrams

See [`block-diagram.svg`](block-diagram.svg) / [`block-diagram.png`](block-diagram.png). Each block is tagged with its cost @1k; PCB and assembly are listed under each panel title.

* **A (with switch):** RJ45 IN (PoE magjack) → RTL8363NB → RJ45 OUT. The
  CH32V307 sits on the switch's RMII port. Power path: PoE front end → 60 V
  sync buck (5 V or 12 V, selected by the MCU) → VBUS switch → USB-C.
* **B (without switch):** RJ45 IN → 4-channel PoE splitter transformer →
  RJ45 OUT (`poe.md` §3 option 2; the Pi's own magnetics stay in the link).
  Option 1, back-to-back magjacks, costs about $1 more and is lower risk on
  return loss. The power path is the same as A, with a CH32V203 as the MCU.

## Cost by block (USD @1k)

| Block | With switch | Without switch |
|---|---:|---:|
| PoE front end (bridges, TVS, signature, class sink, bootstrap, hot-swap) | 0.53 | 0.53 |
| Output buck, 5 V / 12 V (controller, 2 FETs, inductor, caps, FB select) | 1.09 | 1.09 |
| 3.3 V logic rail | 0.15 | 0.04 |
| USB-C output (receptacle, VBUS switch, CC network + 12 V protection, ESD) | 0.42 | 0.42 |
| Ethernet magnetics and jacks | 1.75 | 0.70 |
| Switch IC + crystal + passives | 1.62 | – |
| MCU + crystal + passives | 1.38 | 0.43 |
| PCB | 0.45 | 0.20 |
| JLCPCB assembly (amortised setup + extended-part fees) | 1.20 | 0.70 |
| **Total** | **8.59** | **4.11** |

Not included: enclosure (~$0.30–0.80), captive 5 A USB-C cable instead of a
receptacle (~$0.50–0.80), test/programming, shipping, duties.

## What drives the cost and where the risk is

1. **Magnetics are the biggest single uncertainty.** PoE-rated gigabit
   magjacks with centre taps vary from ~$0.70 to $2 at LCSC. Pricing these
   properly is the first thing to firm up.
2. **The 60 V buck is the second.** I assumed a cheap Chinese 60–100 V
   synchronous controller plus external FETs (~$1.09 total including the
   12 V select). An integrated 60 V 5 A converter from TI/MPS would
   be $1.50–2.50.
3. **CH32V307 is overkill as an MCU but cheap for what it brings.** It is the
   only cheap WCH part with a MAC that can talk RMII to the switch. Its price
   is an estimate ($1.10–1.60 depending on package).
4. **MCU power during PoE mark events.** `poe.md` §6.3 requires ≤ 4 mA total
   during mark events. A CH32V307 running from its internal oscillator at low
   clock may or may not fit that. If it doesn't, add a CH32V003 (~$0.12) as a
   cold-start PoE controller that wakes the CH32V307 after power-on. That adds
   about $0.15 to the switch variant.
5. **Discrete PoE front end vs a PD controller IC.** The discrete front end
   costs ~$0.53 here. Cheap PD controller ICs are roughly $0.30–1 but most only
   handle af/at, and bt-capable ones cost more. The software PD looks like a
   small cost win and the main way to get bt Class 5/6 cheaply, but this has
   not been verified with real quotes.
6. **Power budget.** The switch draws ~0.5–1 W (datasheet figure not found).
   On an at/PoE+ port this lowers the USB-C budget by about 1 W. On a bt
   Class 5/6 port it doesn't matter.
7. **Output voltage safety.** With 12 V possible, a firmware bug that leaves
   VBUS at 12 V on a 5 V-only sink is the main new failure mode. Mitigations:
   the buck defaults to 5 V in hardware when the select GPIO is low or
   floating, and VBUS is checked against the contract before the load switch
   closes.

## Suggested next steps

* Get real LCSC prices for 3–4 candidate magjacks / splitter transformers and
  2–3 60 V buck controllers, then update the CSV.
* Bench-check CH32V307 supply current at low clock against the 4 mA mark-event
  limit, to decide whether the CH32V003 helper is needed.
