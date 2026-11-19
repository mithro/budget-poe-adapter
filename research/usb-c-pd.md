# USB-C Power: Standards, RPi 5 Requirements, and PD Negotiation at the Electrical Level

The adapter is a **USB-C power source**: it supplies a device such as a Raspberry Pi 5. This note gives the standards, the Raspberry Pi 5 requirements and the electrical and timing detail of PD negotiation that any implementation has to meet. The design has no microcontroller other than the RISC-V CPU inside the YT9215 switch IC ([`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md)); how that chip does the job, and with which external parts, is worked out in [`yt9215-usb-pd.md`](yt9215-usb-pd.md).

Numbers come from the USB Type-C spec (R2.x), USB PD spec (R3.1 and R3.2), BC1.2, and Raspberry Pi documentation. Treat values marked **(verify)** as needing a check against the spec tables before committing to a schematic. Everything else is well established.

---

## 1. Summary for this project

- **The RPi 5 only ever uses 5 V.** To get full power it needs the source to advertise a **USB PD Fixed 5 V PDO at 5 A** (27 W supply = 5.1 V at 5 A). Anything else (Type-C 3 A, or PD without a 5 A PDO) makes it boot with USB peripheral current limited to 600 mA and print a power warning. This can also be overridden on the Pi side with `usb_max_current_enable=1` in `config.txt` or `PSU_MAX_CURRENT=5000` in the bootloader EEPROM config, so **PD is a nice-to-have, not mandatory, for a Pi-only product.**
- **Power budget:** 5 V × 5 A = 25 W at the USB-C port, which is about 28 W into the converter at roughly 90% efficiency. 802.3at (PoE+, 25.5 W at the PD) is just short of that at full load. 802.3bt Type 3 (51 W) covers it comfortably. Most real Pi 5 loads (about 5 to 12 W without heavy USB devices) fit PoE+ easily.
- **The minimum viable source** is a 5 V output, load switch, CC attach detection, an Rp advertising 3 A, and a small PD stack that sends one Source_Capabilities message containing a single 5 V at 5 A PDO and handles Request → Accept → PS_RDY. No variable-voltage converter is needed.
- **The PD physical layer is the hard part for the YT9215.** Transmit needs a bit stream with edges placed to about 100 ns and a 1.1 V swing. Receive needs a **comparator**, because the 1.1 V BMC swing is below 3.3 V logic thresholds, and something that times the edges. The hard real-time constraint is replying with GoodCRC within **195 µs**. [`yt9215-usb-pd.md`](yt9215-usb-pd.md) compares the ways to meet this.
- **A catch with 5 A:** PD only allows >3 A when the source knows the cable is 5 A-rated. That means either a **captive cable** (simplest, compliant) or a receptacle plus VCONN plus SOP' Discover Identity to read the cable e-marker (more firmware, plus a 5 V, 1 W VCONN switch). Many cheap supplies just offer 5 A anyway, and the Pi will accept it.
- **Fallback:** a PD transceiver with an I²C interface, such as the FUSB302B, does the physical layer and the GoodCRC reply in hardware and leaves only the message logic to the YT9215 ([`yt9215-usb-pd.md`](yt9215-usb-pd.md#option-a)).

---

## 2. USB power standards: voltages and currents

| Mechanism | Signalling line | Signalling detail | Voltage | Voltage step | Max current | With e-marked 5 A cable | Max power | Relevance as a source | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USB 2.0 default | None | – | 5 V | – | 500 mA | – | 2.5 W | Baseline | – |
| USB 3.x default | None | – | 5 V | – | 900 mA | – | 4.5 W | Baseline | – |
| BC1.2 DCP | Data pair | D+ shorted to D- | 5 V | – | 1.5 A | – | 7.5 W | Trivial on a power-only port | – |
| BC1.2 CDP | Data pair | – | 5 V | – | 1.5 A | – | 7.5 W | Trivial on a power-only port | – |
| Apple divider, level 1 | Data pair | Fixed voltages | 5 V | – | 1 A | – | – | Resistors only | – |
| Apple divider, level 2 | Data pair | Fixed voltages | 5 V | – | 2.1 A | – | – | Resistors only | – |
| Apple divider, level 3 | Data pair | Fixed voltages | 5 V | – | 2.4 A | – | – | Resistors only | – |
| Type-C Current, default | CC | Rp value | 5 V | – | Default | – | – | Required for any USB-C source | – |
| Type-C Current, 1.5 A | CC | Rp value | 5 V | – | 1.5 A | – | – | Required for any USB-C source | – |
| Type-C Current, 3.0 A | CC | Rp value | 5 V | – | 3.0 A | – | 15 W | Required for any USB-C source | – |
| USB PD Fixed (SPR) | CC | BMC | 5 V | – | 3 A | 5 A | – | 5 V at 5 A for the Pi 5 | – |
| USB PD Fixed (SPR) | CC | BMC | 9 V | – | 3 A | 5 A | – | 5 V at 5 A for the Pi 5 | – |
| USB PD Fixed (SPR) | CC | BMC | 15 V | – | 3 A | 5 A | – | 5 V at 5 A for the Pi 5 | – |
| USB PD Fixed (SPR) | CC | BMC | 20 V | – | 3 A | 5 A | 100 W | 5 V at 5 A for the Pi 5 | – |
| USB PD PPS (PD 3.0) | CC | BMC | 3.3 to 21 V | 20 mV | – | – | ≤ 100 W | Skip | Needs a tightly controlled converter |
| USB PD EPR Fixed (PD 3.1) | CC | BMC with EPR mode entry | 28 V | – | 5 A | – | 140 W | Out of PoE budget | bt max ≈ 71 W at the PD |
| USB PD EPR Fixed (PD 3.1) | CC | BMC with EPR mode entry | 36 V | – | 5 A | – | 180 W | Out of PoE budget | bt max ≈ 71 W at the PD |
| USB PD EPR Fixed (PD 3.1) | CC | BMC with EPR mode entry | 48 V | – | 5 A | – | 240 W | Out of PoE budget | bt max ≈ 71 W at the PD |
| USB PD EPR AVS (PD 3.1) | CC | BMC | 15 to 48 V | 100 mV | – | – | – | Skip | – |
| USB PD SPR AVS (PD 3.2) | CC | BMC | 9 to 20 V (verify) | – | – | – | – | Skip | – |
| Qualcomm QC 2.0 | Data pair | Voltage levels | 5 V | – | – | – | ~18 W | Only for phones on legacy ports | – |
| Qualcomm QC 2.0 | Data pair | Voltage levels | 9 V | – | – | – | ~18 W | Only for phones on legacy ports | – |
| Qualcomm QC 2.0 | Data pair | Voltage levels | 12 V | – | – | – | ~18 W | Only for phones on legacy ports | – |
| Qualcomm QC 2.0 | Data pair | Voltage levels | 20 V (optional) | – | – | – | ~18 W | Only for phones on legacy ports | – |
| Qualcomm QC 3.0 | Data pair | Pulses | 5 to 20 V | 200 mV | – | – | ~18 W | Only for phones on legacy ports | – |
| Samsung AFC | Data pair | Proprietary single-wire | 9 V etc. | – | – | – | – | Skip | – |
| Huawei FCP | Data pair | Proprietary single-wire | 9 V etc. | – | – | – | – | Skip | – |
| Huawei SCP | Data pair | Proprietary single-wire | 9 V etc. | – | – | – | – | Skip | – |

PPS sets its current limit in 50 mA steps.

**PD power rules (SPR source profiles):** a source rated at P watts must offer every lower standard voltage. ≤15 W offers 5 V; 15 to 27 W also offers 9 V; 27 to 45 W also offers 15 V; >45 W also offers 20 V. A **5 V-only 25 W source is not a "PD Power Rule" compliant 27 W supply** (a compliant 27 W source must also offer 9 V at 3 A). The Pi official PSU offers 5.1 V at 5 A plus 9, 12 and 15 V at lower current (verify exact PDO list). This matters only for certification, not function.

**Data over USB:** if the adapter also carries data to the device over USB (for example Ethernet via a USB NIC), D+ and D- are used for data, so the DCP short is not an option. You would advertise CDP behaviour or rely on Type-C Rp and PD only. For a Pi 5, Type-C Rp + PD is all that matters.

---

## 3. Raspberry Pi 5 specifics

- Official supply: **27 W USB-C PD, 5.1 V @ 5 A**. The Pi 5 is a PD **sink** that only requests 5 V. It does not use 9 V or 15 V.
- Behaviour by supply:
  - PD source offering **5 V ≥ 5 A** → USB ports allowed **1.6 A** total, no warning.
  - 5 V 3 A (Type-C Rp 3 A, or PD without a 5 A PDO) → USB ports limited to **600 mA**, boot warning about the power supply.
  - Overrides: `usb_max_current_enable=1` (config.txt), or `PSU_MAX_CURRENT=5000` in the bootloader EEPROM (`rpi-eeprom-config`). With these, a dumb 5 V supply that can genuinely deliver 5 A works fine.
- Input tolerance: nominal 5 V, roughly ±5%. Design the converter for 5.1 V at the connector to cover cable drop at 5 A (a 0.1 Ω round trip costs 0.5 V, so keep the cable short or captive).
- Real consumption: idle about 3 W, full CPU load about 8 to 12 W, the rest is USB, NVMe and HAT budget.

**Recommended Pi-oriented design:** a fixed 5.1 V buck from the PoE rail, a single PDO `Fixed 5 V / 5 A` (optionally 3 A when the cable is not e-marked), and a captive cable or a documented "5 A cable only" receptacle.

---

## 4. Type-C CC layer (DC, no protocol)

Every USB-C power source must implement this, even without PD.

### 4.1 Resistors

| Role | Component | Type | Where | Value min | Value max |
|---|---|---|---|---|---|
| Source advertises current | **Rp** | Pull-up | Each CC pin | [Rp table](#rp-values) | [Rp table](#rp-values) |
| Sink | **Rd** | Pull-down | – | 5.1 kΩ | 5.1 kΩ |
| Active cable (VCONN powered) | **Ra** | – | The unused CC | 0.8 kΩ | 1.2 kΩ |

<a id="rp-values"></a>

| Rp advertises | Rp to 5 V | Rp to 3.3 V | Or current source |
|---|---|---|---|
| Default USB | 56 kΩ | 36 kΩ | 80 µA |
| **1.5 A** | **22 kΩ** | **12 kΩ** | **180 µA** |
| **3.0 A** | **10 kΩ** | **4.7 kΩ** | **330 µA** |

A 3.3 V pull-up suits the YT9215 because its pins are not 5 V tolerant and the CC node then stays within their limits. With 4.7 kΩ to 3.3 V and Rd 5.1 kΩ, CC sits at about 1.72 V.

### 4.2 Voltage windows

Source-side detection (what the attach detector must distinguish), in volts (verify):

| Rp advertised | Ra present, below | Rd present, min | Rd present, max | Open, above |
|---|---|---|---|---|
| Default | 0.2 | 0.25 | 1.5 | 1.6 |
| 1.5 A | 0.4 | 0.45 | 1.5 | 1.6 |
| 3.0 A | 0.8 | 0.85 | 2.45 | 2.6 |

Sink-side (vRd) windows that tell the sink what current it may draw:

| Source advertises | vRd min | vRd max |
|---|---|---|
| **Default** | **0.2 V** | **0.66 V** |
| **1.5 A** | **0.66 V** | **1.23 V** |
| **3.0 A** | **1.23 V** | **2.04 V** |

With 3 A Rp: below 0.8 V means Ra, 0.85 to 2.45 V means Rd (attached sink), above 2.6 V means open. The CC that sees Rd gives the plug orientation, and PD runs on that pin. The YT9215 has no ADC, and the Rd window lies between its logic thresholds, so a comparator with a threshold near 2.6 V detects attach and detach. A logic input reads Ra as low.

### 4.3 Source state machine and timing

1. **Unattached.Source:** Rp on both CC, **VBUS off** (vSafe0V < 0.8 V).
2. See Rd on one CC → debounce **tCCDebounce 100 to 200 ms** → **Attached.Source**.
3. Turn VBUS on within **tVBUSON ≤ 275 ms** (verify). If Ra is on the other CC and you support VCONN, apply 5 V VCONN to that pin.
4. Detach (CC goes open, debounce tPDDebounce 10 to 20 ms) → VBUS off and discharged to vSafe0V within **tVBUSOFF ≤ 650 ms** (needs a bleed resistor or discharge FET).

Hardware this implies: a high-side load switch on VBUS (P-FET or N-FET with a charge pump, about $0.05 to $0.15), a discharge path, and reverse and over-current protection. An eFuse or a load switch with a current-limit (ILIM) pin can do the over-current shutdown in place of a sense resistor. Plugging two sources together must never back-feed, because a dumb 5 V barrel-style output on a USB-C receptacle is non-compliant and dangerous.

### 4.4 Protection on CC

Pins on a USB-C receptacle can be shorted to VBUS by bad cables. Even if VBUS is only ever 5 V, anything on CC that leads to a YT9215 pin needs a series resistor (about 1 kΩ for the sense path) plus a clamp, because those pins are not 5 V tolerant. **The TX driver path cannot have 1 kΩ in series** (see [section 6.1](#61-transmit)), so it needs a 5 V-tolerant driver or a small clamp and FET. Add ESD diodes on CC.

---

## 5. USB PD physical layer (BMC on CC)

### 5.1 Signalling

- **Line coding:** Biphase Mark Code (BMC). There is a transition at the start of every bit, plus an extra mid-bit transition for a `1`. It is DC-balanced-ish and self-clocking.
- **Bit rate:** 300 kbps ±10% (**270 to 330 kbps**), so UI = 3.03 to 3.70 µs and the half-UI is about 1.67 µs.
- **Transmit swing (vSwing):** 1.05 to 1.20 V (nominal 1.125 V), referenced to ground, driven on top of the CC line (the Rp and Rd DC level is overridden while transmitting).
- **Driver output impedance (zDriver):** 33 to 75 Ω.
- **Rise and fall time:** ≥ 300 ns (10 to 90%) to limit EMI. Edges that are too sharp are non-compliant but usually still decoded.
- **Receiver:** must tolerate ground offset between partners (about ±250 mV) and noise. It must reject glitches shorter than about 100 ns. Total receiver capacitance on CC (cReceiver) is 200 to 600 pF (verify). That capacitance limits what you can hang on CC.
- **Start of drive (tStartDrive):** the transmitter starts driving the line within 1 µs before or after the start of the first preamble bit (verify).
- **Idle detection:** the line is "busy" if ≥ 3 transitions occur within tTransitionWindow (12 to 20 µs) (verify).
- **Packet end:** after EOP, the transmitter drives a final hold (tHoldLowBMC ≥ 1 µs) then releases within tEndDriveBMC ≤ 23 µs. Wait **tInterFrameGap ≥ 25 µs** before the next packet.

### 5.2 Framing

```
Preamble | SOP* (4 K-codes) | Header (16b) | 0–7 Data Objects (32b each) | CRC-32 | EOP
```

- **Preamble:** 64 bits of alternating 0 and 1 (starts with 0, ends with 1). It is not 4b5b-encoded. The receiver uses it to lock bit timing.
- **4b5b encoding** of everything after the preamble. Each nibble is sent as 5 bits, **LSB first**, low nibble first.

| Nibble | 5b | Nibble | 5b |
|---|---|---|---|
| 0 | 11110 | 8 | 10010 |
| 1 | 01001 | 9 | 10011 |
| 2 | 10100 | A | 10110 |
| 3 | 10101 | B | 10111 |
| 4 | 01010 | C | 11010 |
| 5 | 01011 | D | 11011 |
| 6 | 01110 | E | 11100 |
| 7 | 01111 | F | 11101 |

K-codes:

| K-code | 5b |
|---|---|
| **Sync-1** | **11000** |
| **Sync-2** | **10001** |
| **Sync-3** | **00110** |
| **RST-1** | **00111** |
| **RST-2** | **11001** |
| **EOP** | **01101** |

- Ordered sets: **SOP** = S1 S1 S1 S2 (port partner). **SOP'** = S1 S1 S3 S3 (cable plug near end). **SOP''** = S1 S3 S1 S3. **Hard Reset** = R1 R1 R1 R2. **Cable Reset** = R1 S1 R1 S3. A receiver should accept an ordered set when 3 of 4 K-codes match.
- **CRC-32:** same as Ethernet (poly 0x04C11DB7, init 0xFFFFFFFF, reflected, final inversion), over header + data objects, transmitted as 4b5b like data. It is the same CRC as the Ethernet frame check sequence.

Example: Source_Capabilities with one PDO = 64 + 20 + 20 + 40 + 40 + 5 = **189 bits ≈ 630 µs** on the wire.

### 5.3 Message layer essentials

**Header (16 bits):** b15 Extended, b14..12 Number of Data Objects, b11..9 MessageID (3-bit, increments per sent message, GoodCRC echoes the received ID), b8 Port Power Role (1 = Source), b7..6 Spec Revision (01 = PD2.0, 10 = PD3.x), b5 Port Data Role (1 = DFP), b4..0 Message Type.

Message types needed for a minimal source:

- Control (0 data objects): 1 GoodCRC, 3 Accept, 4 Reject, 6 PS_RDY, 7 Get_Source_Cap, 8 Get_Sink_Cap, 13 Soft_Reset, 16 Not_Supported (PD3).
- Data: 1 Source_Capabilities, 2 Request, 4 Sink_Capabilities, 15 Vendor_Defined (VDM).

**Fixed Supply PDO (32 bits):** b31..30 = 00, b29 Dual-Role Power, b28 USB Suspend Supported, b27 Unconstrained Power, b26 USB Comms Capable, b25 Dual-Role Data, b24 Unchunked Ext Msg, b23 EPR Capable, b21..20 Peak Current, **b19..10 Voltage in 50 mV units, b9..0 Max Current in 10 mA units.** For 5 V at 5 A: `(100 << 10) | 500 = 0x000191F4`, then add b27 (unconstrained, true for a PoE-powered supply) to get `0x080191F4`.

**Fixed Request Data Object (RDO):** b31..28 Object Position (1-based PDO index), b27 GiveBack, b26 Capability Mismatch, b25 USB Comms Capable, b24 No USB Suspend, b23 Unchunked Ext, b22 EPR Mode Capable, b19..10 Operating Current (10 mA), b9..0 Max Operating Current (10 mA).

**Minimal source sequence:**

1. VBUS on at vSafe5V. Start sending **Source_Capabilities** every **tTypeCSendSourceCap 100 to 200 ms** until a GoodCRC arrives (give up after nCapsCount = 50 and remain a Type-C-only source).
2. Sink responds with **GoodCRC** (within tReceive ≈ 0.9 to 1.1 ms of your EOP, otherwise retry: nRetryCount = 2 in PD3, 3 in PD2). It then sends a **Request** within tSenderResponse (about 24 to 30 ms).
3. Source → GoodCRC (**must start within tTransmit ≤ 195 µs of the Request's EOP**), then **Accept**.
4. Transition the supply (5 V to 5 V is a no-op), wait tSrcTransition 25 to 35 ms, then send **PS_RDY**. An explicit contract is now in place. At 5 V at 5 A, also switch the Rp to 3 A and use it for collision avoidance.
5. While in contract, answer Get_Source_Cap (resend caps), and answer anything unknown with **Not_Supported** (PD3) or Reject. Ignore unsupported VDMs in PD2. The Pi 5 and many sinks may send Discover Identity VDMs.
6. Errors: no GoodCRC after retries leads to **Soft_Reset**, then **Hard Reset** (VBUS goes to vSafe0V then back on, tSrcRecover 0.66 to 1 s). Implement Hard Reset receive at minimum: drop the contract and restart.

**Spec revision:** start with PD3.0 in the header. If the sink replies with PD2.0, use 2.0 for the rest of the connection.

**PD3 collision avoidance:** the source signals with its Rp: **3.0 A Rp = SinkTxOK** (sink may start an AMS), **1.5 A Rp = SinkTxNG**. The source switches Rp to 1.5 A before it initiates a message. This requires two Rp values per CC; one output and two resistors are enough ([front end](yt9215-usb-pd.md#front-end)).

**PPS and EPR (if ever needed):** a PPS sink must re-request at least every 10 s, and the source hard-resets after tPPSTimeout (about 15 s) without one. EPR requires EPR_Mode entry via an e-marked 5 A, 50 V cable check and a sink keep-alive every ≤ 500 ms (verify). Both need a programmable converter with current limiting. Not recommended within a PoE budget.

### 5.4 Cable e-marker (for advertising > 3 A)

- To offer 5 A legitimately, the source must read the cable e-marker: apply **VCONN (5 V, up to 1 W)** to the CC pin that sees Ra, then send **Discover Identity on SOP'** and parse the Cable VDO (the 3 A or 5 A maximum-current field).
- Hardware: one VCONN switch per CC (or one per plug orientation), plus the ability to transmit and receive BMC on either CC.
- Alternatives: a **captive cable** (the source knows its own cable), or offer 5 V at 3 A by default and 5 V at 5 A only after cable discovery.

---

## 6. What the PD physical layer needs from hardware

These are the requirements. [`yt9215-usb-pd.md`](yt9215-usb-pd.md) maps them to the YT9215 and to fallback chips.

### 6.1 Transmit

- A driver that swings 0 to about 1.1 V with an output impedance of 33 to 75 Ω. Two ways to get it: a 3.3 V output into a divider (for example 100 Ω in series and 51 Ω to ground gives about 1.11 V and 34 Ω, verify against drive strength and the Rp and Rd loading), or a buffer powered from a rail of about 1.1 V with a series resistor.
- Edges of ≥ 300 ns. The capacitance allowed on CC (cReceiver, at most 600 pF) with a 75 Ω driver gives only about 100 ns, so a capacitor alone cannot set the edge rate. The driver itself has to limit its slew rate.
- A driver that is high impedance when not transmitting, so the Rp and Rd DC level returns. A divider with 51 Ω to ground must be disconnected by a switch, because it would otherwise look like Ra and break attach detection.
- Timing: a half-UI of 1.67 µs means edges must be placed with roughly 100 ns accuracy. That calls for a hardware serialiser of some kind; software that counts CPU cycles is the last resort.

### 6.2 Receive

- The signal is 0 to about 1.1 V. 3.3 V CMOS thresholds (VIL ≈ 0.8 V, VIH ≈ 2.0 V) **will not decode it reliably**, so a comparator is needed.
- Threshold about 0.55 to 0.6 V with tens of mV of hysteresis. The comparator needs a clean edge within about 200 ns. Ideally the threshold is referenced to the received idle level, because the DC operating point differs with Rp (Rp 3 A plus Rd puts CC at about 1.7 V idle, while the BMC is driven from 0 to 1.1 V). In practice receivers either AC-couple with a bias network or use a threshold set relative to vSwing. **Bench measurement needed here.**
- Decoding needs the time between edges, classified as about 1.67 µs (half) or 3.33 µs (full), or samples of the line at 2.4 MHz or more. The bits are then 4b5b-decoded and the CRC is checked.
- **Latency budget:** after EOP the receiver must decode, verify the CRC, build a GoodCRC and start transmitting within **195 µs**. A GoodCRC prepared in advance for each of the 8 MessageID values removes the build step.

### 6.3 Other analog needs

| Function | Property | Value |
| --- | --- | --- |
| CC attach detect | Channels | 2 |
| CC attach detect | Threshold for Ra | 0.8 V |
| CC attach detect | Threshold for open | 2.6 V |
| CC attach detect | Speed | ms |
| CC attach detect | Implementation | Comparator |
| Rp switching (3 A vs 1.5 A) | Scope | Per CC |
| Rp switching (3 A vs 1.5 A) | Pull-up values | 2 |
| Rp switching (3 A vs 1.5 A) | Implementation | 1 output |
| Rp switching (3 A vs 1.5 A) | Pull-up for 3 A | 12 k and 7.5 k in parallel |
| Rp switching (3 A vs 1.5 A) | Pull-up for 1.5 A | 12 k to 3.3 V |
| VBUS monitor | Range | 0 to 5.5 V |
| VBUS monitor | Must detect | vSafe0V |
| VBUS monitor | Implementation | Comparator with a divider |
| VBUS current | Purpose | Over-current shutdown |
| VBUS current | Required | Optional |
| VBUS current | Implementation | Load switch with ILIM |
| VCONN | Voltage | 5 V |
| VCONN | Power | ≤ 1 W |
| VCONN | Where | The unused CC |
| VCONN | Implementation | 2 small P-FETs |
| Data-pair legacy (optional): BC1.2 | Signature | DCP short |
| Data-pair legacy (optional): BC1.2 | Implementation | Resistors |
| Data-pair legacy (optional): Apple | Divider voltage 1 | 2.7 V |
| Data-pair legacy (optional): Apple | Divider voltage 2 | 2.0 V |
| Data-pair legacy (optional): Apple | Implementation | Resistors |

A variable VBUS (9 V, 15 V or 20 V offers, or PPS with its 20 mV steps) would need a converter whose output the YT9215 can set. The design offers 5 V only, so it needs none.

---

## 7. Legacy and proprietary negotiation (source side)

For completeness, here is what a source must do to satisfy each style of sink. Only the first two matter for a Pi.

1. **Type-C current (mandatory):** a static Rp.
2. **USB PD:** [section 5](#5-usb-pd-physical-layer-bmc-on-cc).
3. **BC1.2 DCP:** short D+ to D- (< 200 Ω) on a power-only port. A BC1.2 sink drives 0.5 to 0.7 V on D+ and looks for it on D- (> 0.25 to 0.4 V). CDP (data plus charging) requires the host side to drive VDM_SRC on D- in response, which needs an analog switch or GPIO plus resistor.
4. **Apple:** D+ and D- fixed by dividers, for example D+ at 2.7 V with D- at 2.7 V means 2.4 A (and combinations of 2.0 V and 2.7 V mean 1 A or 2.1 A, verify). This conflicts with the DCP short, so pick one or use an analog switch.
5. **QC 2.0 and QC 3.0 (source):** start as DCP. When the sink holds D+ at 0.6 V for about 1.25 s, open the short between D+ and D- and pull D- low. The sink then sets levels: D+ at 0.6 V with D- at 0 V means 5 V, D+ at 3.3 V with D- at 0.6 V means 9 V, both at 0.6 V means 12 V, both at 3.3 V means 20 V, and D+ at 0.6 V with D- at 3.3 V means QC3 continuous mode (D+ pulses +200 mV, D- pulses -200 mV). The source needs two comparators and a variable converter. Not useful for a 5 V-only product.
6. **Samsung AFC, Huawei FCP, Huawei SCP and Oppo VOOC:** proprietary signalling on D- (single-wire serial). Low value here and poorly documented, so skip.

---

## 8. Open questions for bench work

1. Measure a real BMC waveform from the Pi 5 (and a few chargers) on a cheap scope and logic analyser to pick the comparator threshold and confirm the Pi's message sequence (does it send VDMs or Get_Sink_Cap?).
2. Check whether the Pi 5 accepts a 5 V at 5 A PDO from a source that has not done cable discovery (expected: yes).
3. Decide captive cable versus receptacle (drives the VCONN and e-marker work).
4. Verify the (verify)-marked values against USB PD R3.2 §5.8 (BMC tables) and Type-C R2.4 §4.11 (CC voltage tables).

The questions about the YT9215 itself are in [`yt9215-usb-pd.md`](yt9215-usb-pd.md#what-to-find-out-next).

---

## 9. Useful references

- USB Type-C Cable and Connector Specification R2.x: §4.5 (CC functional model), §4.11 (CC parameters).
- USB Power Delivery Specification R3.2: Ch. 5 (Physical Layer: BMC, 4b5b, timing), Ch. 6 (Protocol: headers, PDO and RDO, timers), Ch. 8 (Device Policy state machines).
- Battery Charging Spec BC1.2: DCP or CDP detection.
- Raspberry Pi documentation: "Power supply" section for Pi 5 (`usb_max_current_enable`, `PSU_MAX_CURRENT`).
- Open stacks to read for message-layer logic: the Google Chromium EC and Zephyr USB-C PD stack, and TCPM in Linux ([`drivers/usb/typec/tcpm`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/usb/typec/tcpm)). These are useful for the state machines even though they assume a hardware PHY and TCPC.
