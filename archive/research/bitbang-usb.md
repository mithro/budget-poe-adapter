# Bit-banged USB

> **Archived.** This note is not part of the current design. It assumes an external MCU that provides the adapter's USB link. The current design uses only the YT9215 switch IC and its internal RISC-V CPU. The [archive index](../README.md) lists every archived note.

Sources were read on 2026-10-22. Scope: USB **device** mode only (host mode is out of
scope). Price cap is the RP2040 (~$0.79 @100); MCU prices come from
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
  [`gigabit-piggyback.md` section A](gigabit-piggyback.md#a-host-relay-over-usbc-recommended-for-the-cheap-sku) moves a few hundred bytes:
  PoE class, PD contract, telemetry, LLDP power values, firmware update. A HID
  device does all of that with no drivers on Linux, Windows, macOS or Android.
  rv003usb's HID bootloader fits in 1,920 bytes.
* **Low speed cannot be a USB network card.** The spec forbids bulk endpoints on
  low speed. Linux rewrites them to 8-byte interrupt endpoints ([LS bulk patch]),
  and the Linux network class drivers (cdc_ether, cdc_ncm, rndis_host) reject the
  device. cnlohr's RNDIS demo on the CH32V003 "works with Windows, but not Linux"
  and is "VERY SLOW". So CDC-ECM, NCM or RNDIS is off the table. CDC-ACM serial on low
  speed is also out of spec and only half works.
* **It saves almost no money here.** Hardware USB FS device is nearly free in the
  WCH range: the CH570Q ($0.233 @50) has USB FS and costs about the same as the
  CH32V003 ($0.244 @50), which does not. The current pick, CH32X035 ($0.31 @100),
  adds a hardware USB-PD PHY. Bit-banging USB on a CH32V003 saves at most ~$0.07
  against the CH32X035, and then USB-PD BMC has to be bit-banged on the same core
  too (see [the risks](#risks-if-both-usb-and-pd-are-done-in-software-on-one-small-core)).
* **Recommendation: don't bit-bang USB on the main MCU.** Keep the CH32X035
  (hardware USB FS + PD). Bit-banged low-speed HID is worth keeping in mind only
  when the MCU is chosen for some other reason and has no USB, for example a
  CH32V003 cold-start helper that needs a debug or DFU port, or a Wi-Fi part such as
  the BK7238. The RP2040's PIO USB is only useful as a *second* port, since the
  RP2040 already has hardware USB.

## 1. What the adapter's USB link has to do

From [`gigabit-piggyback.md` section A](gigabit-piggyback.md#a-host-relay-over-usbc-recommended-for-the-cheap-sku) ("host relay"):

| Job | Size | Rate | Needs bulk throughput? | In scope |
| --- | --- | --- | --- | --- |
| Status reports | tens of bytes | ~1/s | No | Yes |
| LLDP power request and grant | a few bytes | per change | No | Yes |
| Firmware update from the host | 8–32 KB | rare | No (slow is fine) | Yes |
| Act as a USB NIC for the host | Mbit/s | – | **Yes** | No |

Notes on the rows of this table:

- **Status reports**, note: [Status report fields](#status-report-fields)
- **LLDP power request and grant**, note: Relayed by a host daemon (`lldpd`)
- **Act as a USB NIC for the host**, note: Host already has gigabit via the passthrough.

<a id="status-report-fields"></a>

| Status report field |
|---|
| PoE class |
| PSE type |
| Vin |
| Iin |
| PD contract |
| Temperature |
| Faults |

So a low-speed HID device covers everything the design needs.

**Role caveat.** The adapter is the Type-C source, so by default it is the USB
host (DFP) and the Pi is the device. For the adapter to be a USB *device*, the
host side must run as host on that port (laptops, phones, most SBCs do; a Pi
needs `dtoverlay=dwc2,dr_mode=host`), or the two must do a PD `DR_Swap`. This is
the same for hardware and software USB; see [`gigabit-piggyback.md` section A](gigabit-piggyback.md#a-host-relay-over-usbc-recommended-for-the-cheap-sku) option 2.

## 2. Survey of software USB device stacks

| Stack | Alias | Author | Co-author | MCU | Also runs on | Core | Clock | Device speed | USB host | HID | HID bootloader | Other | License | Alt license |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **grainuum** | "Palawan" | Sean "xobs" Cross | – | NXP Kinetis KL-series | – | Cortex-M0+ | 48 MHz | LS | – | Yes | Yes | – | MIT | – |
| **V-USB** | – | Objective Development | – | 8-bit AVR | – | AVR | 12–20 MHz | LS | – | Yes | – | Vendor control | GPLv2 | Commercial |
| **rv003usb** | – | Charles "cnlohr" Lohr | – | WCH CH32V003 | – | RISC-V RV32EC | 48 MHz | LS | – | Yes | Yes | – | MIT | – |
| **stm32f030-vusb** | – | ads830e | – | STM32F030F4P6 | – | Cortex-M0 | 48 MHz | LS | – | Mouse only | – | – | ? | – |
| **Pico-PIO-USB** | – | sekigon-gonnoc | – | RP2040 | RP2350 | PIO | 48 MHz × N | **FS** | Yes | Device example | – | – | MIT | – |
| **ValentyUSB** | Fomu | xobs | Luke Valenty et al. | iCE40UP5K FPGA | – | Gateware | 48 MHz | FS | – | – | – | Full device | ? | – |

| Stack | Property | Value |
| --- | --- | --- |
| grainuum | MCU requirement | Cortex-M0+ with single-cycle IO |
| grainuum | HID bootloader drivers | "Driver-free" |
| grainuum | Bootloader works on Windows | Yes |
| grainuum | Data-pin GPIO banks | May be **different GPIO banks** |
| grainuum | Data-pin adjacency | Not required |
| grainuum | CPU cost | 32 CPU cycles per bit |
| grainuum | Talk venue | 33C3 |
| grainuum | Talk title | "No USB? No problem." |
| grainuum | Reference 1 | [33C3] |
| grainuum | Reference 2 | [grainuum] |
| V-USB | Age | The original (2007-ish) |
| V-USB | Clock option 1 | 12 MHz |
| V-USB | Clock option 2 | 12.8 MHz |
| V-USB | Clock option 3 | 15 MHz |
| V-USB | Clock option 4 | 16 MHz |
| V-USB | Clock option 5 | 16.5 MHz |
| V-USB | Clock option 6 | 18 MHz |
| V-USB | Clock option 7 | 20 MHz |
| V-USB | Other clocks | Not supported |
| V-USB | RC oscillator version 1 | 12.8 MHz |
| V-USB | RC oscillator version 2 | 16.5 MHz |
| V-USB | RC oscillator trim | From USB frames |
| V-USB | CDC-ACM forks | AVR-CDC |
| V-USB | CDC-ACM transport | Out-of-spec LS bulk |
| V-USB | Reference | [V-USB] |
| rv003usb | Clock source | HSI |
| rv003usb | HSI trim source | 1 ms SOF keep-alive |
| rv003usb | HID type 1 | Keyboard |
| rv003usb | HID type 2 | Mouse |
| rv003usb | HID type 3 | Gamepad |
| rv003usb | HID type 4 | Raw HID |
| rv003usb | HID type 5 | WebUSB |
| rv003usb | HID bootloader size | **1,920 bytes** |
| rv003usb | CDC | Partial |
| rv003usb | MIDI | Partial |
| rv003usb | RNDIS speed | "VERY SLOW" |
| rv003usb | RNDIS hosts | Windows only |
| rv003usb | Receiver | Pin-change interrupt in assembly |
| rv003usb | USB pin placement | All on one port |
| rv003usb | Allowed pins | 0–4 only |
| rv003usb | USB IRQ priority | Must be top |
| rv003usb | USB IRQ pre-emption | Never allowed |
| rv003usb | Other critical sections | ≤ ~40 cycles |
| rv003usb | Status | Still "beta" |
| rv003usb | Reference | [rv003usb] |
| stm32f030-vusb | Clock source | Internal RC |
| stm32f030-vusb | Origin | Port of the STM8 V-USB-style code |
| stm32f030-vusb | Status | Proof of concept |
| stm32f030-vusb | Reference | [f030-vusb] |
| stm32f030-vusb | PY32F002 port | Someone tried |
| stm32f030-vusb | PY32F002 port result | None reported |
| stm32f030-vusb | PY32F002 port reference | [py32 issue] |
| Pico-PIO-USB | Fractional clock divider | Allowed |
| Pico-PIO-USB | Host speed 1 | FS |
| Pico-PIO-USB | Host speed 2 | LS |
| Pico-PIO-USB | TinyUSB driver for device role | Yes |
| Pico-PIO-USB | TinyUSB driver for host role | Yes |
| Pico-PIO-USB | PIO blocks | 1 |
| Pico-PIO-USB | State machines | 3 |
| Pico-PIO-USB | PIO instructions | 32 |
| Pico-PIO-USB | Code size | ~15 KB |
| Pico-PIO-USB | D+ pull-up | 1.5 kΩ external |
| Pico-PIO-USB | Series resistors | 22 Ω |
| Pico-PIO-USB | CPU load | One core is busy during transfers |
| Pico-PIO-USB | Reference | [PIO-USB] |
| ValentyUSB | DFU | foboot |
| ValentyUSB | Kind | "Soft" USB in logic |
| ValentyUSB | CPU bit-banging | No |
| ValentyUSB | Why listed | For completeness |

Longer entries for this table:

- **Pico-PIO-USB, PIO clock**: 48 MHz × N from sys clock.
- **Pico-PIO-USB, RX CRC**: Done by the CPU in an IRQ.
- **ValentyUSB, Fit**: An FPGA is far over the price cap.

(Tomu, xobs's other USB board, uses the EFM32HG's hardware USB, so it is not a
bit-bang design.)

### How the CPU stacks work

All of them share the same structure:

1. **RX** is a pin-change (EXTI) interrupt on D+ or D−, fired by the SYNC
   pattern. The ISR samples the line in a cycle-counted assembly loop, does NRZI
   decode and bit-unstuffing on the fly, and stores bytes. At LS, 48 MHz gives
   32 cycles per bit, which is enough for two GPIO writes plus stuffing and a
   running CRC.
2. **The handshake reply** (ACK, NAK and DATA) has to start within the USB
   turnaround time (≈ 2–7.5 bit times, i.e. 1.3–5 µs at LS). That is why the
   ISR cannot be pre-empted and why descriptors and replies are prepared ahead.
3. **TX** drives both lines from precomputed, bit-stuffed NRZI data, ending in
   SE0 + J (end of packet).
4. **Clock**: no crystal. The internal RC is trimmed by timing the host's 1 ms
   keep-alive (LS) pulses. V-USB at 12.8 MHz or 16.5 MHz and rv003usb both do this.
5. **Pull-up**: 1.5 kΩ on D− marks a low-speed device; a GPIO can drive it to
   force re-enumeration.

At FS (12 Mbit/s, 4 cycles per bit at 48 MHz) a CPU cannot sample, decode,
unstuff and store in time. The RP2040 gets around this because PIO does the
bit-level work in hardware state machines and the CPU only handles bytes.

## 3. Low-speed limits that matter here

| Limit | Value | Verdict | Reference |
| --- | --- | --- | --- |
| Max packet | 8 bytes | Fine | USB 2.0 §5.7–5.8 |
| Control endpoints | Allowed | Fine | USB 2.0 §5.7–5.8 |
| Interrupt endpoints | Allowed | Fine | USB 2.0 §5.7–5.8 |
| Interrupt `bInterval` | ≥ 10 ms by spec | Fine either way | – |
| Bulk endpoints | Not allowed | Can't be a network interface | – |
| Linux usbnet drivers | Reject LS devices | – | [rv003usb test_ethernet] |
| Linux USB core | Converts LS bulk to interrupt | – | [LS bulk patch] |
| CDC-ACM | Needs bulk | Avoid | – |
| LS edge rates from plain GPIOs | – | Needs testing | – |

Notes on the rows of this table:

- **Max packet**, effect: Larger blocks go in 8-byte pieces.
- **Max packet**, workaround: HID feature reports (control transfers)
- **Max packet**, note: Enough for telemetry.
- **Max packet**, note: Enough for DFU.
- **Interrupt `bInterval`**, effect: ~800 B/s per interrupt endpoint.
- **Interrupt `bInterval`**, workaround: Control-transfer DFU is quicker.
- **Interrupt `bInterval`**, note: Hosts often poll faster.
- **Bulk endpoints**, effect: No CDC-ECM, NCM or RNDIS on Linux.
- **CDC-ACM**, effect: Out of spec.
- **CDC-ACM**, workaround: HID.
- **CDC-ACM**, alt workaround: WebUSB or vendor control transfers.
- **CDC-ACM**, note: Works by luck on some hosts.
- **LS edge rates from plain GPIOs**, effect: Some hubs and hosts are less tolerant.
- **LS edge rates from plain GPIOs**, workaround: 33–47 Ω series resistors.
- **LS edge rates from plain GPIOs**, note: Long cables are less tolerant too.

The edge-rate tests should use the Pi 5 and a laptop.

HID is driverless everywhere and also reachable from a browser (WebHID or WebUSB),
so a config page for the adapter could be a static web page.

## 4. Fit with the rest of the design

### Cost

| MCU | USB stack | MCU $ | At qty | USB | Second USB | PD PHY | PD method | Crystal-less | 5 V supply | Comparators | ADC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CH32X035G8U6 | – | $0.312 | 100 | HW FS | – | **HW** | Hardware | Yes | Yes | Yes | – |
| CH570Q | – | $0.233 | 50 | HW FS | – | ✗ | Bit-banged | – | – | – | No |
| CH32V003F4P6 | rv003usb | $0.244 | 50 | SW **LS** | – | ✗ | Bit-banged on the same core | – | – | – | – |
| RP2040 | Pico-PIO-USB | $0.786 | 100 | HW FS | SW FS | ✗ | – | – | – | – | – |

Notes on the rows of this table:

- **CH32X035G8U6**, note: Current pick.
- **RP2040, Pico-PIO-USB**, note: Only useful as a second port.

The MCU prices are from [`risc-v-mcu-comparison.md`](risc-v-mcu-comparison.md).

The saving from bit-banging is ≤ $0.07 against the CH32X035, and it is negative
against a CH570Q, which has hardware USB for the same money.

### Risks if both USB and PD are done in software on one small core

* **Two hard real-time jobs.** rv003usb's USB ISR must never be pre-empted
  (an LS 8-byte data packet plus handshake holds it for roughly 80–100 µs), and
  a bit-banged PD receiver must answer with GoodCRC within 195 µs
  ([`usb-c-pd.md`](../../research/usb-c-pd.md)). They can collide when a PD message arrives
  during a USB transaction. Timer-capture + DMA for PD RX could make it work, but
  it needs a bench test.
* **Clock trim** from USB keep-alives only works while USB is attached. PD BMC
  timing (300 kbit/s ± 10 %) is loose enough for the untrimmed HSI, so this is
  minor.
* **Maturity.** rv003usb calls itself beta; grainuum and the STM32 port are
  unmaintained proofs of concept. A hardware USB peripheral with WCH's or
  TinyUSB's stack is lower risk.

### Where software USB still earns a place

* A **CH32V003 cold-start and PoE helper** (as considered in [`usb-c-pd.md`](../../research/usb-c-pd.md)) could
  expose a HID debug and DFU port for free if two GPIOs reach D+ and D−. Not needed
  with the CH32X035, which already meets the 4 mA PoE mark-event limit
  ([`cost-reduction.md`](cost-reduction.md)).
* An MCU picked for its **network** and lacking USB (e.g. BK7238 Wi-Fi, which
  runs at 160 MHz) could in principle bit-bang LS HID, but no port exists, and
  pairing it with a CH32X035 over UART (~$0.98 total) is the documented path.
* **RP2040 and RP2350 designs**: PIO-USB gives a second FS device or host port, for
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
* [PIO-USB] https://github.com/sekigon-gonnoc/Pico-PIO-USB (README resource use; [`src/pio_usb_device.c`](https://github.com/sekigon-gonnoc/Pico-PIO-USB/blob/main/src/pio_usb_device.c) computes the PIO divider as sys_clk / 48 MHz)
* [EEVblog] STM32G030 thread on bit-banging USB FS vs LS: https://www.eevblog.com/forum/microcontrollers/stm32g030-g031/msg4983739/
* CH32V003 USB dev board (rv003usb hardware reference): https://hackaday.io/project/192233

[33C3]: https://infocondb.org/con/ccc/33c3/no-usb-no-problem-how-to-write-an-open-source-bit-bang-low-speed-usb-stack-running-on-a-sub-1-cortex-m0
[grainuum]: https://github.com/xobs/grainuum
[V-USB]: https://github.com/obdev/v-usb
[rv003usb]: https://github.com/cnlohr/rv003usb
[rv003usb test_ethernet]: https://github.com/cnlohr/rv003usb/tree/master/testing/test_ethernet
[LS bulk patch]: https://git.linaro.org/plugins/gitiles/kernel/linux-linaro-stable.git/+/60aac1ec26b960fe77bf600457bc6c06f8aa7db4%5E%21
[f030-vusb]: https://github.com/ads830e/stm32f030-vusb
[py32 issue]: https://github.com/IOsetting/py32f0-template/issues/12
[PIO-USB]: https://github.com/sekigon-gonnoc/Pico-PIO-USB
[EEVblog]: https://www.eevblog.com/forum/microcontrollers/stm32g030-g031/msg4983739/
