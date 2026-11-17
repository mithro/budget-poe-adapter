# Bit-banged (software) USB device for the PoE → USB-C adapter

Researched 2026-10-22. Scope: USB **device** mode only (host mode is out of
scope per Tim). Price cap is the RP2040 (~$0.79 @100); MCU prices come from
[`risc-v-mcu-comparison.md`](risc-v-mcu-comparison.md). The question: can a
cheaper MCU with no USB hardware do the adapter's USB link in software, the way
Sean "xobs" Cross did with grainuum?

## TL;DR

* **Bit-banged USB on a normal MCU means low speed (1.5 Mbit/s).** Every working
  CPU-only stack (grainuum, V-USB, rv003usb, stm32f030-vusb) is low speed. Full
  speed (12 Mbit/s) in software needs something like the RP2040's PIO
  (Pico-PIO-USB). People on EEVblog who have tried it say FS on a generic 48 MHz
  MCU "is just not going to happen" ([EEVblog]).
* **Low speed is enough for what the adapter needs.** The host relay in
  [`gigabit-piggyback.md`](gigabit-piggyback.md) §A moves a few hundred bytes:
  PoE class, PD contract, telemetry, LLDP power values, firmware update. A HID
  device does all of that with no drivers on Linux, Windows, macOS or Android.
  rv003usb's HID bootloader fits in 1,920 bytes.
* **Low speed cannot be a USB network card.** The spec forbids bulk endpoints on
  low speed. Linux rewrites them to 8-byte interrupt endpoints ([LS bulk patch]),
  and the Linux network class drivers (cdc_ether, cdc_ncm, rndis_host) reject the
  device. cnlohr's RNDIS demo on the CH32V003 "works with Windows, but not Linux"
  and is "VERY SLOW". So CDC-ECM/NCM/RNDIS is off the table. CDC-ACM serial on low
  speed is also out of spec and only half works.
* **It saves almost no money here.** Hardware USB FS device is nearly free in the
  WCH range: the CH570Q ($0.233 @50) has USB FS and costs about the same as the
  CH32V003 ($0.244 @50), which does not. The current pick, CH32X035 ($0.31 @100),
  adds a hardware USB-PD PHY. Bit-banging USB on a CH32V003 saves at most ~$0.07
  against the CH32X035, and then USB-PD BMC has to be bit-banged on the same core
  too (see risks below).
* **Recommendation: don't bit-bang USB on the main MCU.** Keep the CH32X035
  (hardware USB FS + PD). Bit-banged low-speed HID is worth keeping in mind only
  when the MCU is chosen for some other reason and has no USB, for example a
  CH32V003 cold-start helper that needs a debug/DFU port, or a Wi-Fi part such as
  the BK7238. The RP2040's PIO USB is only useful as a *second* port, since the
  RP2040 already has hardware USB.

## 1. What the adapter's USB link has to do

From [`gigabit-piggyback.md`](gigabit-piggyback.md) §A ("host relay"):

| Job | Data | Needs bulk/high throughput? |
|---|---|---|
| Status and telemetry reports | tens of bytes, ~1/s | No |
| LLDP power request/grant relay | a few bytes per change | No |
| Firmware update from the host | 8–32 KB, rare | No (slow is fine) |
| Act as a USB NIC for the host | Mbit/s | **Yes** (out of scope) |

The status reports cover PoE class, PSE type, Vin/Iin, PD contract,
temperature and faults. The LLDP exchange is relayed by a host daemon
(`lldpd`). The USB NIC job is out of scope because the host already has
gigabit through the passthrough.

So a low-speed HID device covers everything the design needs.

**Role caveat.** The adapter is the Type-C source, so by default it is the USB
host (DFP) and the Pi is the device. For the adapter to be a USB *device*, the
host side must run as host on that port (laptops, phones, most SBCs do; a Pi
needs `dtoverlay=dwc2,dr_mode=host`), or the two must do a PD `DR_Swap`. This is
the same for hardware and software USB; see `gigabit-piggyback.md` §A option 2.

## 2. Survey of software USB device stacks

| Stack | Author | MCU / core | Clock | Speed | What works | License |
|---|---|---|---|---|---|---|
| **grainuum** ("Palawan") | Sean "xobs" Cross | Cortex-M0+ (NXP Kinetis KL) | 48 MHz | LS | HID, HID bootloader | MIT |
| **V-USB** | Objective Development | 8-bit AVR | 12–20 MHz | LS | HID, vendor control | GPLv2 or commercial |
| **rv003usb** | Charles "cnlohr" Lohr | WCH CH32V003 (RV32EC) | 48 MHz | LS | HID, HID bootloader | MIT |
| **stm32f030-vusb** | ads830e | STM32F030F4P6 (Cortex-M0) | 48 MHz | LS | Mouse only | ? |
| **Pico-PIO-USB** | sekigon-gonnoc | RP2040 / RP2350 PIO | 48 MHz × N | **FS** device; FS + LS host | HID device example | MIT |
| **ValentyUSB** (Fomu) | xobs, Luke Valenty et al. | iCE40UP5K FPGA gateware | 48 MHz | FS | Full device incl. DFU | ? |

* **grainuum.** Needs a Cortex-M0+ with single-cycle IO. The HID bootloader
  is "driver-free", including on Windows. D+ and D− may sit on **different
  GPIO banks**, on non-adjacent pins. 32 CPU cycles per bit. Talk: 33C3 "No
  USB? No problem." ([33C3], [grainuum])
* **V-USB.** The original (2007-ish). Runs at 12, 12.8, 15, 16, 16.5, 18 or
  20 MHz only. The 12.8/16.5 MHz versions run from the AVR's RC oscillator,
  trimmed from USB frames. CDC-ACM forks (AVR-CDC) use out-of-spec LS bulk.
  ([V-USB])
* **rv003usb.** The CH32V003 is RISC-V RV32EC; its HSI is trimmed from the
  1 ms SOF/keep-alive. HID covers keyboard, mouse, gamepad, raw HID and
  WebUSB, and the HID bootloader fits in **1,920 bytes**. CDC and MIDI are
  partial; RNDIS is "VERY SLOW" and Windows only. The pin-change interrupt is
  in assembly. D+, D− and the pull-up must be on one port, pins 0–4 only. The
  USB IRQ must be top priority and never pre-empted; other critical sections
  ≤ ~40 cycles. Still "beta". ([rv003usb])
* **stm32f030-vusb.** 48 MHz from the internal RC. A port of the STM8
  V-USB-style code; proof of concept ([f030-vusb]). Someone tried a PY32F002
  port; no result reported ([py32 issue]).
* **Pico-PIO-USB.** PIO is clocked at 48 MHz × N from the sys clock (a
  fractional divider is allowed). There is a TinyUSB driver for both roles.
  Uses 1 PIO, 3 state machines, 32 instructions, ~15 KB. Needs an external
  1.5 kΩ D+ pull-up and 22 Ω series resistors. RX CRC is done by the CPU in
  an IRQ, so one core is busy during transfers. ([PIO-USB])
* **ValentyUSB.** DFU is foboot. "Soft" USB in logic, not CPU bit-banging.
  Shown for completeness; an FPGA is far over the price cap.

(Tomu, xobs's other USB board, uses the EFM32HG's hardware USB, so it is not a
bit-bang design.)

### How the CPU stacks work

All of them share the same structure:

1. **RX** is a pin-change (EXTI) interrupt on D+ or D−, fired by the SYNC
   pattern. The ISR samples the line in a cycle-counted assembly loop, does NRZI
   decode and bit-unstuffing on the fly, and stores bytes. At LS, 48 MHz gives
   32 cycles per bit, which is enough for two GPIO writes plus stuffing and a
   running CRC.
2. **The handshake reply** (ACK/NAK/DATA) has to start within the USB
   turnaround time (≈ 2–7.5 bit times, i.e. 1.3–5 µs at LS). That is why the
   ISR cannot be pre-empted and why descriptors and replies are prepared ahead.
3. **TX** drives both lines from precomputed, bit-stuffed NRZI data, ending in
   SE0 + J (end of packet).
4. **Clock**: no crystal. The internal RC is trimmed by timing the host's 1 ms
   keep-alive (LS) pulses. V-USB at 12.8/16.5 MHz and rv003usb both do this.
5. **Pull-up**: 1.5 kΩ on D− marks a low-speed device; a GPIO can drive it to
   force re-enumeration.

At FS (12 Mbit/s, 4 cycles per bit at 48 MHz) a CPU cannot sample, decode,
unstuff and store in time. The RP2040 gets around this because PIO does the
bit-level work in hardware state machines and the CPU only handles bytes.

## 3. Low-speed limits that matter here

| Limit | Effect on the adapter |
|---|---|
| Max packet 8 bytes | Fine |
| Only control and interrupt endpoints | Fine |
| Interrupt `bInterval` ≥ 10 ms by spec | Fine |
| No bulk → no CDC-ECM/NCM/RNDIS on Linux | Can't be a network interface |
| CDC-ACM needs bulk | Use HID instead |
| LS edge rates from plain GPIOs | Add 33–47 Ω series resistors |

* **Packet size and endpoint types** (USB 2.0 §5.7–5.8). Fine for telemetry
  and DFU. Control transfers (HID feature reports) carry larger blocks in
  8-byte pieces.
* **`bInterval`.** ~800 B/s per interrupt endpoint by the book; hosts often
  poll faster. Control-transfer DFU is quicker. Fine either way.
* **No bulk.** Linux's usbnet drivers reject LS devices
  ([rv003usb test_ethernet]) and the core converts LS bulk to interrupt
  ([LS bulk patch]).
* **CDC-ACM.** Out of spec; works by luck on some hosts. Use HID (or
  WebUSB/vendor control) instead.
* **Edge rates.** Some hubs/hosts and long cables are less tolerant of LS
  edge rates from plain GPIOs. Test with the Pi 5 and a laptop.

HID is driverless everywhere and also reachable from a browser (WebHID/WebUSB),
so a config page for the adapter could be a static web page.

## 4. Fit with the rest of the design

### Cost

| Option | MCU $ (from MCU comparison) | USB | PD PHY | Notes |
|---|---|---|---|---|
| CH32X035G8U6 (current pick) | $0.312 @100 | HW FS | **HW** | Crystal-less, 5 V supply, comparators |
| CH570Q | $0.233 @50 | HW FS | ✗ | No ADC; PD would be bit-banged |
| CH32V003F4P6 + rv003usb | $0.244 @50 | SW **LS** | ✗ | PD also bit-banged on the same core |
| RP2040 + Pico-PIO-USB | $0.786 @100 | HW FS + SW FS | ✗ | Only useful as a second port |

The saving from bit-banging is ≤ $0.07 against the CH32X035, and it is negative
against a CH570Q, which has hardware USB for the same money.

### Risks if both USB and PD are done in software on one small core

* **Two hard real-time jobs.** rv003usb's USB ISR must never be pre-empted
  (an LS 8-byte data packet plus handshake holds it for roughly 80–100 µs), and
  a bit-banged PD receiver must answer with GoodCRC within 195 µs
  ([`usb-c-pd.md`](usb-c-pd.md)). They can collide when a PD message arrives
  during a USB transaction. Timer-capture + DMA for PD RX could make it work, but
  it needs a bench test.
* **Clock trim** from USB keep-alives only works while USB is attached. PD BMC
  timing (300 kbit/s ± 10 %) is loose enough for the untrimmed HSI, so this is
  minor.
* **Maturity.** rv003usb calls itself beta; grainuum and the STM32 port are
  unmaintained proofs of concept. A hardware USB peripheral with WCH's or
  TinyUSB's stack is lower risk.

### Where software USB still earns a place

* A **CH32V003 cold-start/PoE helper** (as considered in `usb-c-pd.md`) could
  expose a HID debug and DFU port for free if two GPIOs reach D+/D−. Not needed
  with the CH32X035, which already meets the 4 mA PoE mark-event limit
  ([`cost-reduction.md`](cost-reduction.md)).
* An MCU picked for its **network** and lacking USB (e.g. BK7238 Wi-Fi, which
  runs at 160 MHz) could in principle bit-bang LS HID, but no port exists, and
  pairing it with a CH32X035 over UART (~$0.98 total) is the documented path.
* **RP2040 / RP2350 designs**: PIO-USB gives a second FS device or host port, for
  example to be a device to the Pi and a host to something else. Not needed for
  this adapter.

## Sources

* [33C3] "No USB? No problem." talk, xobs, 33C3 (2016): https://infocondb.org/con/ccc/33c3/no-usb-no-problem-how-to-write-an-open-source-bit-bang-low-speed-usb-stack-running-on-a-sub-1-cortex-m0 and https://fahrplan.events.ccc.de/congress/2016/Fahrplan/events/8031.html
* [grainuum] https://github.com/xobs/grainuum (README: Cortex-M0+ at 48 MHz, single-cycle IO, Kinetis). ChibiOS forum note on the talk: https://forum.chibios.org/viewtopic.php?p=28052
* [V-USB] https://github.com/obdev/v-usb and `usbdrv/Readme.txt` (supported clocks); https://www.obdev.at/vusb/
* [rv003usb] https://github.com/cnlohr/rv003usb (README: LS, 1,920-byte bootloader, pin and IRQ rules, "Linux explicitly blacklists all low-speed USB Ethernet")
* [rv003usb test_ethernet] https://github.com/cnlohr/rv003usb/tree/master/testing/test_ethernet ("This works with Windows, but not Linux"; avoids `usbnet_get_endpoints`)
* [LS bulk patch] Linux "USB: Handle bogus low-speed Bulk endpoints" (converts LS bulk to interrupt, 1 ms, 8 bytes): https://git.linaro.org/plugins/gitiles/kernel/linux-linaro-stable.git/+/60aac1ec26b960fe77bf600457bc6c06f8aa7db4%5E%21
* [f030-vusb] https://github.com/ads830e/stm32f030-vusb
* [py32 issue] https://github.com/IOsetting/py32f0-template/issues/12
* [PIO-USB] https://github.com/sekigon-gonnoc/Pico-PIO-USB (README resource use; `src/pio_usb_device.c` computes the PIO divider as sys_clk / 48 MHz)
* [EEVblog] STM32G030 thread on bit-banging USB FS vs LS: https://www.eevblog.com/forum/microcontrollers/stm32g030-g031/msg4983739/
* CH32V003 USB dev board (rv003usb hardware reference): https://hackaday.io/project/192233
