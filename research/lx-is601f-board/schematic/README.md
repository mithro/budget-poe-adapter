# LX-IS601F V2.0 board: reverse-engineered schematic

Traced 2026-11-17 from Tim's Google Photos album (34 photos, Pixel 7 Pro, two boards). Nothing here has been probed with a meter yet.

## Files

The schematic is a KiCad 7 hierarchical project. Open `lx-is601f.kicad_sch`; the root page is a block diagram and each block is its own sheet.

| File | What it is |
|---|---|
| `lx-is601f.kicad_sch` | Root sheet: block diagram, confidence legend, how-to-read notes. |
| `power.kicad_sch` | DC input, protection, PU1 SCT2622 3.3 V buck. |
| `switch.kicad_sch` | U4 YT9215SCH in four units: clock/reset/EEPROM/flash/GPIO, copper MDI, SerDes, supply pins. |
| `ethernet_poe.kicad_sch` | Ports 1-4: G2401PR magnetics, `05U` ESD, J1 (drawn J1A-J1D), PoE centre taps. |
| `uplink_sfp.kicad_sch` | Port 5 uplink (DXFRM6, J3) and the U12 SFP connector. |
| `poe_module.kicad_sch` | PIN1 header and the PoE PSE daughterboard (U1 `2184A`). |
| `leds.kicad_sch` | FX/POW LED array, LED6 header, LED7/LED8. |
| `lx-is601f-schematic.pdf` | PDF of all seven sheets. |
| `renders/` | PNG of each sheet (`after-*`) and of the pass-1 single sheet (`before-pass1.png`). |
| `lx-is601f-nets.csv` | Every pin with its net, confidence code and sheet. Sort by `net` to get a netlist. |
| `gen_schematic.py`, `kisch.py` | Generate every sheet and the CSV from one data model, then export KiCad's netlist and check it against the model. Edit these, not the `.kicad_sch` files. |

Parts on the PoE module are renumbered R1xx/D1xx/U101 so they don't clash with mainboard references; the silkscreen name is in each part's `Silk` field. PIN1 is drawn as J4 and the LED6 header as J5 for the same reason.

## What the board is

A 6-port managed-capable switch with 4-port PoE output (PSE), not a PoE-powered device:

- **U4** Motorcomm **YT9215SCH** (LQFP-128 + EPAD). Two boards seen: `VKTP18287 3200111C 3AU2612M0` and `VKJC09324 2500211C 3AW4849M0`. Heatsink on top, and a screw through the EPAD from the bottom.
- **5 copper ports**: J1 is a 1×4 RJ45 block (ports 1–4, PoE). J3 is a single RJ45 uplink (no PoE) on the opposite edge. Each port has a United-tek **G2401PR** single-port GbE transformer (DXFRM2–6; there is no DXFRM1 part, only its silkscreen).
- **1 SFP**: U12 is a 20-pin SFP host connector. One board has the cage fitted; the other has the connector only.
- **PoE module**: a daughterboard on the 8-pin **PIN1** header beside J1. It carries U1, a QFN-48 marked **`2184A 533AQ1H`** (4-port PSE controller, maker not identified; IP804AR is the closest public match in package and function). It also has 4× `R250` 0.25 Ω sense resistors (R8/R12/R13/R14), 4× `330` 33 Ω (R3/R9/R10/R11), 5× SMB TVS marked `RGS` (D1/D3/D5/D7 + one more) and 1206 caps.
- **Power**: 2-pin `POWER2` input (48–57 V assumed), L1, three `SS510` Schottkys (D1, D4, D5), three blue disc parts RV1–RV3 (varistors or Y-caps), L2 `701` inductor, C4 47 µF/63 V. **PU1 SCT2622** (marking `2622 SCT 6DC`, 4.2–60 V 2 A non-synchronous buck, ESOP-8) with PL3 10 µH, D40 catch diode and TC1 220 µF/16 V makes **3.3 V**. **1.15 V** core comes from U4's internal switching regulator (pins 63/64 LX) through **L3 4.7 µH**.
- **25 MHz crystal Y6** with C43/C44, beside U4 XTAL pins 87/88.
- **Config EEPROM U10** `HK24C08` (Hangshun 24C08, 1 KB I²C) on the bottom. It is presumably on U4 pins 91/92 (SCL/SDA). This matters for firmware work: the earlier note said "no EEPROM", which was for the other (OSHWHub) board.
- **Empty SPI-flash footprint U6** (SOP-8/WSON-8) on the bottom, with R40/R94/R96/R98/R100/R102/R109 next to it. Together with R44/R89/R92/R93 on the SPF0 pins, the board looks designed to take a flash chip.
- **ESD**: ED1–ED10, SOT-23-6 marked `05U`, two per copper port between U4 and the magnetics.
- **LEDs**: a 6×2 array of 0603 LEDs, columns `FX` and `POW`, rows 1–6, with RJ7–RJ18 resistors. LED7/LED8 sit next to an unpopulated 2×3 header `LED6` (with R68).
- **Bottom edge under the RJ45s**: twelve SMB parts marked `CP06C` (D6, D8–D18, maybe bidirectional TVS), and 1206 caps C38/C16/C98/C55/C60/C56/C65/C61/C71/C62/C75/… with 0603 resistors R72–R76/R67/R71/R15/R32/R82–R84. These are probably per-pair Bob-Smith terminations or PoE center-tap filtering (inferred).

## Port mapping (inferred from placement)

U4's MDI pins come out on two sides. With pin 1 at the bottom-left (crystal on top), P0/P1/P2 face the J1 magnetics and P3/P4 face the bottom. The mapping below is the shortest-route guess. Check it with a meter.

| U4 port | MDI pins | Magnetics | Connector | ESD |
|---|---|---|---|---|
| P0 | 95–103 | DXFRM4 | J1 port 1 (PoE) | ED1, ED10 |
| P1 | 105–113 | DXFRM3 | J1 port 2 (PoE) | ED2, ED3 |
| P2 | 119–127 | DXFRM2 | J1 port 3 (PoE) | ED4, ED5 |
| P3 | 1–9 | DXFRM5 | J1 port 4 (PoE) | ED6, ED7 |
| P4 | 19–27 | DXFRM6 | J3 uplink | ED8, ED9 |
| SerDes 0 or 1 | 31–42 | none | U12 SFP | none |

## Not yet known

- G2401PR, the `05U` arrays and the `2184A` PSE have no datasheets found. Their pinouts in the schematic are assumed: a common 24-pin 1-port GbE transformer layout, ULC0524P-style ESD, and function-only pins for the PSE.
- SCT2622 pin **numbers** are assumed. The functions (BOOT, VIN, EN, RT, FB, SW, GND/EPAD) are from its datasheet text.
- Many U4 GPIO/LED pins (44, 48, 51–53, 56, 57, 67, 70, 72–74, 76, 78, 81, 83, 84, 93) are not traced.
- Which SerDes feeds the SFP, and where the SFP's I²C, LOS and TX_DISABLE pins go.
- What the 8 PIN1 pins carry, and how the PoE module gets 48 V and ground.

## Next steps: what Tim can measure or photograph

### Photos (these would let most I and U nets become V)

1. **Flat, straight-down shots of each whole side** with the board lying flat and the phone parallel to it. Use diffuse light (no flash), at 2–3 overlapping tiles per side. Put a ruler in frame for scale.
2. **Both sides with the PoE module unplugged**, so the PIN1 header area and the traces under the module are visible.
3. **The PoE module on its own**, both sides, straight down.
4. **Close-ups of the bottom** around U6, U10 and the R49–R66 resistor arrays, and the bottom area under U4 (pins and vias).
5. **Macro of the SFP area** (U12) on the board without the cage.

### Continuity checks (power off; a meter in beep mode)

| # | From | To | Answers |
|---|---|---|---|
| 1 | U10 pin 6 / pin 5 | U4 pin 91 / 92 | Is the EEPROM on SCL/SDA? |
| 2 | U6 pads 1, 2, 5, 6 | R44, R89, R92, R93 (far end) | Is U6 a flash footprint on SPF0? |
| 3 | PIN1 pins 1–8 | J1 pins (each port's 1/2, 3/6, 4/5, 7/8) and GND / VIN | PoE pairs and module power |
| 4 | U4 pins 95, 105, 119, 1, 19 | DXFRM2–6 chip-side pins | Port mapping table above |
| 5 | DXFRM line-side pins | J1/J3 pins | G2401PR pinout |
| 6 | PL3 output, L3 output | U4 AVDDH and AVDDL pins (e.g. 10, 13) | 3.3 V / 1.15 V rails |
| 7 | POWER2 pins | D1, D4, L1, RV1–RV3 | Input protection and polarity |
| 8 | U12 pins 12/13/18/19 | U4 pins 31–42 (through any AC caps) | Which SerDes drives the SFP |
| 9 | LED array resistors RJ7–RJ18 | U4 pins 67–85 | LED pin mapping |

### Powered measurements (if safe to do)

- The voltage on TC1 (expect 3.3 V) and on L3's output side (expect about 1.15 V).
- Read U10 with a CH341A and SOIC-8 clip (power the board off, or lift VCC) to get the EEPROM contents.

## Photo index

| Photos | Content |
|---|---|
| p01, p07, p08, p10–p18, p20, p23 | Top, U4 area and crystal (board A `VKTP18287`, board B `VKJC09324`) |
| p02–p06, p09, p33, p34 | Top overviews (p02/p06 without the PoE module, p09 with SFP cage) |
| p19 | PU1 SCT2622 buck and the R44/R89/R92/R93 column |
| p21, p22 | J1 edge, PIN1 header holes, DXFRM3/4, LED array, LED6 header |
| p30–p32 | PoE module (U1 `2184A`) in place |
| p24–p29 | Bottom: CP06C diodes, Bob-Smith R/C, U10 24C08, U6 footprint, EPAD screw |
