# Cost and part-count reduction for the PoE → USB-C adapter

Researched 2026-10-21. Scope: everything except the switch-vs-passthrough
question (covered in [`gigabit-piggyback.md`](gigabit-piggyback.md) and [`ethernet-switch.md`](ethernet-switch.md)). The
baseline is the **no-switch variant in [`design/bom-rough.csv`](../design/bom-rough.csv) (≈ $4.11 @1k,
~65 placed parts)**. Prices marked **[live]** were read from LCSC product pages
today; everything else is an estimate on the same basis as the BOM CSV.

## 1. TL;DR

* **Swap the CH32V203 for a CH32X035 [live $0.27 @1k, QFN20].** It has a
  hardware USB PD PHY (BMC + CRC), built-in CC pull-up current sources at the
  three Type-C Rp levels (80, 180 and 330 µA), 3 comparators, 2 PGAs, a 12-bit ADC,
  USB full-speed and a 48 MHz RC oscillator. That removes the crystal, the BMC
  TX divider, the RX comparator setup and the four switchable Rp resistors.
  It runs at **2.2 mA at 8 MHz**, inside the 4 mA PoE mark-event limit, so the
  CH32V003 helper is not needed. Its USB port is also what the "host relay"
  option in [`gigabit-piggyback.md`](gigabit-piggyback.md) needs. **≈ −$0.19, −8 parts.**
* **Let the buck be the VBUS switch.** A synchronous buck with EN low outputs
  0 V, so the PMOS load switch, its gate zener and NPN driver can go. A bleeder
  resistor replaces the discharge FET. **≈ −$0.13, −5 parts**, medium risk
  (PD timing and back-feed need a bench check).
* **The 60 V buck controller is the biggest cost risk, not a saving.** The
  BOM assumes $0.60. The one 100 V synchronous controller I could price live,
  SCT82A30, is **$1.44 @1k**. Finding a sub-$0.60 Chinese controller, or
  driving the buck from the MCU (§4.2), matters more than every other item
  here combined.
* **Keep the discrete PoE front end** for 802.3bt. Every Chinese PD IC I
  found is af and at only. A cheap one exists (**TMI7303B [live $0.27]**, af and at,
  integrated 100 V pass switch) and is the right choice for an at-only SKU.
  In the bt design, downsize the hot-swap FET (a 100 V SOT-23 and SOT-223 part is
  enough at ≤ 1 A): **≈ −$0.10.**
* **Stay with the splitter transformer, not magjacks.** The PoE magjack
  in the BOM (HR911130C) is **$1.64 [live]**, not $1.10, so back-to-back
  magjacks would cost ~$2 more than the splitter-transformer option.
* **Through-hole joints are about half of the JLCPCB assembly cost.**
  JLCPCB charges $0.0157 per manual or THT joint vs $0.0016 per SMT joint. Two
  shielded RJ45s with LEDs plus the USB-C shell legs come to ~30 THT joints
  ≈ $0.45. Using jacks without shield tabs or LEDs, or SMD jacks
  (unshielded right-angle SMD RJ45 **$0.26 [live]**), saves **≈ $0.15–0.20**.

**Net (same pricing basis as the BOM):** $4.11 → **≈ $3.45** with the
low-risk items, and **≈ $3.00** if the MCU-driven buck works. Placed parts
go from ~65 to ~45. The caveat in bullet 3 still applies: if the buck
controller really costs ~$1.40, both numbers rise by ~$0.80.

## 2. Itemised changes (no-switch variant)

| # | Change | Δ $ @1k | Δ parts | Risk |
|---|---|---:|---:|---|
| 1 | MCU swap | −0.14 | −3 | Low |
| 2 | PD in hardware | −0.05 | −5 | Low |
| 3 | Buck EN as the VBUS switch | −0.10 | −5 | Medium |
| 4 | Simpler VBUS discharge and current sense | −0.03 | −2 | Low–medium |
| 5 | Smaller hot-swap FET | −0.10 | 0 | Low |
| 6 | Schottky bridges | ±0.00 | −6 | Low |
| 7 | Plainer connectors | −0.15 | −2 (LEDs) | Low |
| 8 | Leaner assembly | −0.08 | — | Low |
| | **Subtotal, up to medium risk** | **≈ −0.65** | **≈ −20** | |
| 9 | MCU-driven synchronous buck (§4.2) | −0.50 more | −1 | **High** |

| # | Removed | Replaced by | Alternative |
|---|---|---|---|
| 1 | CH32V203 | CH32X035F8U6 (QFN20) | CH32X035F7P6 (TSSOP20) |
| 1 | 8 MHz crystal | – | – |
| 2 | BMC TX divider | Hardware PD PHY | – |
| 2 | 4 Rp resistors | Internal Rp current sources | – |
| 3 | PMOS | Buck EN pin | – |
| 3 | Gate zener | – | – |
| 3 | NPN | – | – |
| 3 | 2 resistors | – | – |
| 4 | Discharge FET | Bleeder resistor | – |
| 4 | VBUS shunt | Buck's own current limit | – |
| 5 | 100 V 20 A FET (DFN5x6) | 100 V ~2–3 A FET (SOT-23) | SOT-223 |
| 6 | 8 discrete Schottkys | 2 MBS Schottky bridges (100 V 2 A) | ABS bridges |
| 7 | RJ45 shield tabs | RJ45s without them | SMD jacks |
| 7 | RJ45 LEDs | – | – |
| 7 | – | Full-SMD USB-C receptacle | – |
| 8 | Placements and joints | ~45 parts overall | – |
| 8 | – | Single-sided assembly | – |
| 8 | – | JLCPCB basic-library passives | – |
| 8 | – | Consolidated passive values | – |
| 9 | Buck controller | MCU-driven synchronous buck | – |

Not changed: polarity bridges (both pairsets needed for bt and for Mode A or B
PSEs), surge TVS, CC 12 V-short protection (CH32X035 CC pins are rated only
to VDD + 0.3 V), 3.3 V LDO, PCB.

## 3. MCU and USB PD: CH32X035

From the WCH datasheet (V1.7) and LCSC:

* **USB PD controller + PHY** on PC14 and PC15 (CC1 and CC2): PD 2.0 or 3.0, Source,
  Sink and DRP, automatic BMC encode and decode and CRC. The GoodCRC 195 µs
  deadline, the main bit-bang risk in [`usb-c-pd.md`](usb-c-pd.md) §5, becomes a hardware job.
* **CC pull-up current sources** of 80 µA, 180 µA and 330 µA, which are the Default, 1.5 A and 3 A Rp
  without resistors.
* **Analog:** 3 rail-to-rail comparators (15 ns, output straight into TIM2),
  2 OPA and PGA (×4–×32), 12-bit ADC with 14 channels. Enough for the Vport and
  class-current loop in [`poe.md`](poe.md) §6, the 12 V at 5 V VBUS check and output current
  sensing through a PGA.
* **Supply:** 2.0–5.5 V (3.0–5.3 V with PD or USB on). **Run at 8 MHz HSI:
  2.2 mA**; sleep 1.3–1.5 mA. That fits the ≤ 4 mA mark-event budget with
  room for the 25 kΩ signature current.
* **HSI** 48 MHz, ±1.6 % over 0–70 °C: fine for PD (BMC tolerates ±10 %),
  and WCH runs its USB crystal-less. No crystal.
* **Price:** CH32X035F8U6 QFN20 **$0.272 @1k [live, LCSC C42442062]**. The
  TSSOP20 (F7P6) is easier to rework; it should cost about the same.
* **Caveat:** the project brief preferred "no native PD hardware". Using the
  hardware PHY is cheaper and lower risk, and the firmware can still be
  open source (WCH publishes PD source examples on openwch/ch32x035).
* **GPIO budget (QFN20, ~17 I/O)** is tight but fits: CC1, CC2, D+, D−,
  Vport ADC, VBUS ADC, Iout ADC, class-sink PWM, signature disconnect,
  hot-swap gate, buck EN, 5 V or 12 V select, SWD. A "managed" SKU with the switch
  still needs a MAC-capable MCU (CH32V307 or RP2040), but the CH32X035 can
  keep PoE + PD there too.

## 4. Power stage

### 4.1 Combined PoE PD + DC-DC ICs

Chinese vendors make PD interface ICs with an integrated pass switch and
some with an integrated DC-DC (sources: chongdiantou.com and QQ News market
surveys, LCSC):

| Part | Vendor | af | at | Power | Switch rating | Switch Rds | DC-DC | Package | $ @1k | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| **TMI7303B** | – | Yes | Yes | 25 W | 100 V | 0.48 Ω | – | DFN-10 | **$0.267** | In stock |
| TMI7301 | – | Yes | – | 15 W | Yes | – | – | SOP-8 | – | JLCPCB extended part |
| SD4924S | Silan | Yes | Yes | – | 100 V | 0.6 Ω | – | – | – | – |
| SD4923E | Silan | Yes | Yes | – | 100 V | 0.6 Ω | – | – | – | – |
| AS7001EP | Ashare | – | Yes | – | 100 V | – | – | – | – | – |
| AS7060AE | Ashare | Yes | Yes | – | 100 V | – | – | – | – | – |
| **AS7829AE** | Ashare | Yes | – | 13 W | 100 V hot-swap | – | **80 V non-isolated buck** | ESOP-8 | – | 1.2 A out |
| AS7016AQ | – | Yes | Yes | – | – | – | Flyback (PSR) controller | – | – | Isolated |
| AS7064BQ | – | Yes | Yes | – | – | – | Flyback (PSR) controller | – | – | Isolated |
| JWH7232 | – | Yes | Yes | – | – | – | Flyback (PSR) controller | – | – | Isolated |
| TME7350 | – | Yes | Yes | – | – | – | Flyback (PSR) controller | – | – | Isolated |
| TMI7321 | – | Yes | Yes | – | – | – | Flyback (PSR) controller | – | – | Isolated |

All of these integrate the PD interface. The TMI7303B price is a live LCSC price.
The isolated flyback parts are not useful here.

The AS7829AE would make a one-chip "lite" SKU (Pi Zero or ESP32), but it is too
small for a Pi 5.

**None supports 802.3bt.** A PD IC also can't be combined with MCU-driven bt
classes, because it presents its own class current at every event. So:

* **bt SKU (Pi 5 at 5 A):** keep the discrete front end from [`poe.md`](poe.md) §6.4.
* **at-only SKU (≤ ~22 W):** TMI7303B replaces the signature, class sink,
  hot-swap FET and most of the UVLO and bootstrap. Roughly cost-neutral
  (~+$0.05) but ~6 fewer parts and much less compliance risk. The MCU then
  only needs to measure Vport to infer the class it got (it cannot count class
  events), so it must assume the class the PSE could have granted as at most 4.

### 4.2 Buck controller: the biggest open cost

* SCT82A30 (SCT, 100 V synchronous, voltage-mode, QFN-20): **$1.44 @1k [live]**.
  TI and ADI parts (LM5145, LTC3810) are higher still.
* Integrated 100 V bucks that are cheap are **asynchronous and ≤ 2 A**
  (SCT2A25: 2 A async; SCT2A23A: 1.2 A). ZCC1005Q claims 100 V, 5 A,
  synchronous with integrated 20 mΩ FETs, but I found no distributor or price.
* **Option: let the CH32X035 run the buck.** TIM1 gives complementary PWM
  with dead time, a comparator can trip the timer break input for
  cycle-by-cycle current limit, and a 100 V half-bridge driver such as
  **EG3013 (~$0.10, LCSC listing, currently out of stock)** drives two
  external FETs. Controller cost drops from $0.60–1.44 to ~$0.12.
  Problems to solve on the bench: at 48 MHz and ~150 kHz the duty resolution
  around 10 % duty is only ~30 counts (needs dithering); a firmware hang must
  never leave the high-side FET on (watchdog plus a hardware OVP that
  disables the driver); and load-step response with a software loop.
  **High risk, high reward**: worth one prototype once the rest works.
* **Option: drop 5 A.** If the Pi 5 5 A PDO is dropped (5 V at 3 A, 12 V at 1.5 A,
  ~18 W, which matches at-class budgets), the FETs and inductor shrink and
  more integrated 100 V bucks become possible. This is a product decision.
* FETs: 100 V PDFN FETs at $0.10 each are realistic; keep.

### 4.3 Buck as VBUS switch

With a synchronous buck disabled, the output sits at 0 V and the high-side
body diode blocks (VBUS < Vin). So:

* Close "VBUS" by enabling the buck after CC attach, open it by disabling.
  tSrcTurnOn (≤ 275 ms) is easy with a soft start of a few ms.
* 12 V → 5 V transitions: run forced PWM (no DCM) so the low-side FET pulls
  VBUS down within tSrcTransition.
* Discharge to vSafe0V on detach: a ~10 kΩ bleeder (≈ 15 mW at 12 V) on
  ~10 µF reaches 0.8 V in ≈ 0.27 s, under the 650 ms limit.
* What is lost: reverse-current blocking if PoE is absent and something
  back-feeds VBUS (the high-side body diode would then feed the input caps;
  harmless at 5–12 V). Check against a DRP laptop on the bench.

## 5. Magnetics and connectors

* **HR911130C PoE magjack: $1.64 @1k [live]** (BOM assumed $1.10). Option 1
  in the design (two magjacks) would be ~$2.30–2.50 for magnetics alone.
  **Option 2 (4-channel splitter transformer + two plain jacks) remains the
  cheapest.** The transformer price ($0.50) is still unverified: Pulse H5007NL
  is ~$1+ at Western distributors, and Chinese equivalents (HanRun, Mentech,
  GRT, 24-pin SOP gigabit transformers with centre taps on both sides) need a
  real quote. This is the biggest unverified line after the buck.
* Magnetics-free DC extraction (inductor taps on each wire) needs ~350 µH,
  0.6 A-rated parts per wire; that costs more than a transformer. Dead end.
* **THT cost at JLCPCB:** $0.0157 per joint (manual or wave) vs $0.0016 per SMT
  joint [JLCPCB help pages]. Choices that cut THT joints:
  * Unshielded RJ45 with plastic pegs and no LEDs: 8 joints per jack.
  * SMD RJ45 (e.g. FG-RJ-068T, unshielded right-angle, **$0.26 [live]**) is
    about the same total as a $0.10 THT jack plus joints, but makes the board
    all-SMT (one reflow pass, no hand-solder fee).
  * USB-C: a full-SMD 16-pin receptacle (keeps D+ and D− for the host relay)
    rather than one with THT shell legs. Mechanical strength is the trade-off;
    an enclosure that captures the connector covers it.
  * SMD electrolytic for the input bulk cap, not radial THT.

## 6. PCB and assembly

* **2-layer, 1.6 mm, ~45 × 30 mm** stays right for the passive variant.
  All parts on one side keeps the JLCPCB standard setup at $25 rather than
  $50 and the stencil at $8.66 rather than $17.32 (both per order).
* Choose **JLCPCB basic-library** resistors and caps and consolidate values
  (e.g. 10 k, 100 k, 1 k, 4.7 k, 100 nF, 1 µF, 10 µF): each extended part
  costs $1.50–3 per order in feeder fees.
* Per-board fixed costs at 1k units are small (≈ $0.03–0.06). The per-joint
  cost is what scales, so fewer parts matter more than cheaper parts.
* Standard SMT is ~$0.0016/joint; ~45 parts at ~3 joints each plus the
  QFN and transformer ≈ $0.25 in SMT joints.

## 7. Revised estimate (no-switch variant, USD @1k)

| Block | Current BOM | Up-to-medium-risk set | + MCU-driven buck |
|---|---:|---:|---:|
| PoE front end | 0.53 | 0.43 | 0.43 |
| Output buck | 1.09 | 1.09 | 0.61 |
| 3.3 V rail | 0.04 | 0.04 | 0.04 |
| USB-C output | 0.42 | 0.24 | 0.24 |
| Ethernet magnetics + jacks | 0.70 | 0.70 | 0.70 |
| MCU + passives | 0.43 | 0.29 | 0.29 |
| PCB | 0.20 | 0.20 | 0.20 |
| Assembly | 0.70 | 0.47 | 0.45 |
| **Total** | **4.11** | **≈ 3.46** | **≈ 2.96** |
| Placed parts | ~65 | ~45 | ~44 |

Same ±30 % caveat as the BOM. The buck controller and splitter
transformer prices dominate that uncertainty.

## 8. Next steps

1. Get real prices for 3–4 Chinese 80–100 V synchronous buck controllers and
   2–3 Chinese gigabit splitter transformers. Either could move the total by
   more than all of §2.
2. Bench-test the CH32X035 PD source with a Pi 5 and a 12 V sink, including
   current draw at 8 MHz during simulated mark events.
3. Bench-test the "buck as VBUS switch" behaviour (turn-on time, 12 → 5 V
   step-down, back-feed with a DRP laptop).
4. Decide whether 5 A at 5 V (bt only) is required, or whether an at-only
   SKU (TMI7303B + smaller buck) should be the cheap default.
5. Only then prototype the MCU-driven buck.

## Sources

* CH32X035 datasheet V1.7 (WCH): https://akizukidenshi.com/goodsaffix/CH32X035.pdf
* CH32X035F8U6 at LCSC (C42442062): https://www.lcsc.com/product-detail/C42442062.html
* CH32X035 notes: https://www.mikrocontroller.net/part/CH32X035
* TMI7303B at LCSC (C29779845): https://www.lcsc.com/product-detail/C29779845.html
* TMI7301 at JLCPCB: https://jlcpcb.com/partdetail/TMI-15W_PoE_PD/C29779858
* AS7829AE datasheet: https://atta.szlcsc.com/upload/public/pdf/source/20250530/ED4208A447B91733CD03705248970FC4.pdf
* Chinese PoE chip surveys: https://news.qq.com/rain/a/20250512A03KGQ00 and https://www.chongdiantou.com/archives/307846.html
* LCSC PoE controller category: https://www.lcsc.com/category/1021.html
* SCT82A30 datasheet: https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2310200951_SCT-SCT82A30DHKR_C6041259.pdf and price: https://www.lcsc.com/product-detail/C6041259.html
* SCT2A23A datasheet: https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2110131830_SCT-SCT2A23ASTER_C2901894.pdf
* SCT2A25: https://www.we-online.com/en/components/icref/silicontent-technology/SCT2A25-SVT2A25STER-Buck
* ZCC1005Q: https://blog.csdn.net/HPT_Lt/article/details/135079837
* EG3013 at LCSC: https://www.lcsc.com/product-detail/C81710.html
* HR911130C at LCSC: https://www.lcsc.com/product-detail/C50933.html
* SMD RJ45 FG-RJ-068T-1-6: https://www.lcsc.com/product-detail/C53457406.html
* JLCPCB assembly pricing: https://api.jlcpcb.com/help/article/pcb-assembly-price and https://techoverflow.net/2024/04/09/jlcpcb-pcba-assembly-price-overview/
* Car-charger PD+buck ICs (all ≤ 32–36 V input, so not usable from 57 V): https://www.chongdiantou.com/archives/348794.html
