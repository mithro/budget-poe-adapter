# USB-C PD from the YT9215 alone

Whether the Motorcomm YT9215 and its built-in RISC-V CPU can do the work of a USB-C Power Delivery (PD) controller, with no other microcontroller on the board, and what it costs to fall back on a dedicated chip.

The adapter is the power **source**: it feeds a device such as a Raspberry Pi 5 through USB-C. [`usb-c-pd.md`](usb-c-pd.md) describes the standards and every PD number used here; the values it marks "(verify)" have the same status in this note. Pin numbers are those of the YT9215SCH, the part on the LX-IS601F boards ([`motorcomm-debug-pins.md`](motorcomm-debug-pins.md)). [`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md) describes the CPU.

<a id="captive-cable"></a>

The note assumes a **captive cable**: the adapter ends in a fixed USB-C cable, so there is one CC wire, no plug orientation and no cable marker to read. A receptacle has two CC pins and needs the CC parts of [option B](#option-b) and [option C](#option-c) twice, with a switch that routes transmit and receive to the pin in use. A captive cable is also the simple way to be allowed to offer 5 A ([cable e-marker](usb-c-pd.md#54-cable-e-marker-for-advertising--3-a)).

## Summary

- The slow parts of a PD source fit the YT9215: attach detection, switching VBUS and the message logic run on millisecond time scales [**I**](#evidence-codes).
- The fast part fits no documented peripheral. PD signalling is a 300 kbit/s biphase mark code with 1.67 µs half bits and a 0 to 1.1 V swing. No public document gives the chip a comparator, an ADC, timer capture, PWM or a general SPI master [**U**](#evidence-codes). Its 3.3 V inputs need 2.0 V for a high level [**V**](#evidence-codes), so they cannot read a 1.1 V swing [**I**](#evidence-codes).
- One documented block does clock out a bit stream under crystal timing: the MAC of extension port 9. A frame sent to port 9 at 10 Mbit/s puts a BMC waveform with valid bit timing, 312.5 kbit/s, on pin TXD1 [**S**](#evidence-codes). This is [option C](#option-c).
- Option C is untested. Its transmit side depends on a frame-transmit function whose name is public and whose behaviour is not [**U**](#evidence-codes). Its receive side depends on a MAC behaviour that is not documented [**U**](#evidence-codes).
- The transmit waveform of option C can be tried without any firmware: an external host sets up port 9 over the management interface and a PC sends the frame through a copper port ([next steps](#what-to-find-out-next)).
- Every option that speaks PD waits until code runs on the CPU. Motorcomm's SDK shows that firmware for it exists (FreeRTOS, built for RV32EC) [**V**](#evidence-codes). The boot image format and the CPU's peripheral registers are unpublished [**U**](#evidence-codes).
- Rp, VBUS and all PD signalling stay off until the PoE side has secured its power ([start-up order](#start-up-order)).
- The safe design is [option A](#option-a): a PD transceiver with an I²C interface, driven by the documented I²C master of the YT9215. It takes over every microsecond-scale task.
- Options B and C are not clearly cheaper than option A once every part is counted ([cost](#cost)) [**I**](#evidence-codes).
- The CH224K, HUSB238 and IP2721 are sink chips. They ask a charger for a voltage and cannot make this adapter a source ([fixed-function chips](#fixed-function-chips)).
- A Raspberry Pi 5 needs PD for one thing only: a 5 V, 5 A offer lifts its USB current limit. A PD source limited to 3 A gives the Pi nothing that a bare resistor does not ([Raspberry Pi 5](usb-c-pd.md#3-raspberry-pi-5-specifics)).

| Option | Firmware needed | PD signalling done by | Estimated cost, low | Estimated cost, high | Details |
|---|---|---|---|---|---|
| Resistor and attach comparator | No | Nothing, no PD | $0.03 | $0.03 | [No PD](#option-0) |
| I²C PD transceiver | Yes | Transceiver chip | $0.44 | $0.51 | [Option A](#option-a) |
| GPIO bit-bang | Yes | CPU timing loops | $0.32 | $0.52 | [Option B](#option-b) |
| Port 9 MAC | Yes | Port 9 MAC | $0.32 | $0.52 | [Option C](#option-c) |

The costs are the totals of the [cost table](#cost).

## Evidence codes

| Code | Name | Evidence |
|---|---|---|
| **V** | Verified | Printed in a datasheet |
| **V** | Verified | Present in the vendor SDK source |
| **V** | Verified | Present in the Linux driver, as cited by the register guide |
| **S** | Script | Result of [`mac_bmc_frame.py`](yt9215-usb-pd/mac_bmc_frame.py) |
| **I** | Inferred | Reasoned from other evidence |
| **U** | Unknown | In no public source |

The datasheet is [YT9215SCH V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf). The vendor SDK is the public copy at [OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk), commit `d2c8d6fc721f`, the same one the [register guide](yt9215-registers/README.md) uses.

## Terms

| Term | Meaning |
|---|---|
| CC | Configuration channel, the USB-C wire that carries attach detection and PD messages |
| Rp | Pull-up on CC at the source; its value advertises the current on offer |
| Rd | 5.1 kΩ pull-down on CC at the sink |
| VCONN | 5 V supply for the marker chip inside a cable |
| E-marker | Chip in a cable plug that reports the cable's current rating |
| BMC | Biphase mark code, the line code of PD |
| UI | Unit interval, the duration of one bit |
| 4b5b | Coding that sends each 4 data bits as 5 line bits |
| SOP | Start of packet: four special 5-bit symbols that open a message |
| EOP | End of packet: one special 5-bit symbol that closes a message |
| MessageID | 3-bit counter in each message header |
| GoodCRC | Short message that acknowledges a received message |
| Hard Reset | Four special symbols that reset both ends; no payload |
| DR_Swap | Message that exchanges the USB host and device roles |
| Slicer | Comparator that turns the small BMC signal into a logic level |
| Strap pin | Pin whose level at reset selects a chip option |
| XIP | Execute in place: the CPU runs code directly from the SPI flash |
| DMA | Hardware that moves data between memory and a peripheral without the CPU |
| SMI | Serial management interface, the MDC and MDIO pair |
| FCS | Frame check sequence, the CRC-32 that ends an Ethernet frame |
| RV32EC | Smallest 32-bit RISC-V instruction set, with 16 registers and no multiply instruction |

## What a PD source has to do

The jobs fall into three speed classes. Only the last class is hard for the YT9215.

| Job | Time scale | Needs | More |
|---|---|---|---|
| Advertise current with Rp | Static | Resistor | [CC resistors](usb-c-pd.md#41-resistors) |
| Switch Rp between 3 A and 1.5 A | 1 ms | Output pin | [Messages](usb-c-pd.md#53-message-layer-essentials) |
| Detect attach | 100 ms | Voltage window | [CC windows](usb-c-pd.md#42-voltage-windows) |
| Detect detach | 10 ms | Voltage window | [CC windows](usb-c-pd.md#42-voltage-windows) |
| Switch VBUS on | 100 ms | Load switch | [Source states](usb-c-pd.md#43-source-state-machine-and-timing) |
| Discharge VBUS | 100 ms | Discharge path | [Source states](usb-c-pd.md#43-source-state-machine-and-timing) |
| Run the message sequence | 1 ms | CPU | [Messages](usb-c-pd.md#53-message-layer-essentials) |
| 4b5b and CRC-32 | Per message | CPU | [Framing](usb-c-pd.md#52-framing) |
| Send BMC | 1.67 µs half bit | Bit serialiser | [Waveform](#the-bmc-waveform) |
| Receive BMC | 1.67 µs half bit | Slicer and sampler | [Waveform](#the-bmc-waveform) |
| Reply with GoodCRC | 195 µs | Fast turnaround | [Turnaround](#goodcrc-turnaround) |
| Send and detect Hard Reset | 1.67 µs half bit | Same as BMC | [Framing](usb-c-pd.md#52-framing) |

A PD 3 source tells the sink when it may start a message sequence by switching Rp between the 3 A and the 1.5 A value, so Rp needs two values under CPU control.

A minimal source sends few message types: Source_Capabilities, GoodCRC, Accept, PS_RDY, Not_Supported or Reject, and Hard Reset. Each type has eight variants, one for each MessageID, and a second set of eight for a sink that speaks PD 2.0. Every waveform the source transmits can therefore be prepared in advance [**I**](#evidence-codes). The full set is about 80 waveforms of some 600 bytes each in the [option C](#option-c) coding, about 50 KB against 64 KB of RAM, so the set lives in flash or each waveform is built when its MessageID is known.

VCONN, e-marker reading and DR_Swap are not needed with a [captive cable](#captive-cable) and a power-only port.

### The BMC waveform

![BMC coding: an edge starts every bit and a 1 has a second edge in its middle](yt9215-usb-pd/bmc-coding.svg)

| Property | Minimum | Nominal | Maximum |
|---|---|---|---|
| Bit rate | 270 kbit/s | 300 kbit/s | 330 kbit/s |
| Half bit | 1.52 µs | 1.67 µs | 1.85 µs |
| Swing | 1.05 V | 1.125 V | 1.20 V |
| Driver impedance | 33 Ω | – | 75 Ω |
| Rise and fall time | 300 ns | – | – |

A transmitter must place edges about 100 ns accurately. A receiver must slice a signal that never rises above 1.2 V and then measure the gaps between edges well enough to tell 1.67 µs from 3.33 µs.

### GoodCRC turnaround

![GoodCRC turnaround: the reply must begin between 25 and 195 µs after the end of the received message](yt9215-usb-pd/goodcrc-turnaround.svg)

Every received message must be acknowledged with a GoodCRC that starts no later than 195 µs after the last bit of the message. Within that time the receiver has to notice the end of the message, check its CRC, read the MessageID and start transmitting. This limit, more than the bit rate, decides which options work.

The sender waits 0.9 to 1.1 ms for the complete GoodCRC, which itself lasts about 0.5 ms. A reply that starts up to about 0.4 ms after the message may therefore still be accepted by a real sink, although it breaks the 195 µs rule [**I**](#evidence-codes).

<a id="start-up-order"></a>

## Start-up order

The USB-C side stays off until the PoE side has secured its power, by classification or by LLDP ([PoE](poe.md)). The downstream switch ports stay off for the same time.

| Stage | Rp | VBUS | PD messages |
|---|---|---|---|
| PoE power not yet granted | Off | Off | None |
| Power granted with no sink attached | On | Off | None |
| Sink attached | On | On | Source_Capabilities, then the rest |

With Rp off and VBUS off, a sink sees an unpowered port and waits. This has four consequences for the hardware [**I**](#evidence-codes):

- Rp must be switchable as a whole. Every Rp resistor is fed from a GPIO output, or from a rail that comes on with the grant, and none from the fixed 3.3 V rail.
- The VBUS load switch must stay off through reset. Its enable needs a pull-down, and whatever drives it waits for the grant.
- The BMC driver must stay off through reset, which the [strap pins](#pins-used) of option C do not give for free.
- The reset state of the GPIO pins decides whether all this holds before firmware runs. The datasheet gives the strap pulls and not the reset state of every GPIO [**U**](#evidence-codes).

<a id="power-budget"></a>

### Power budget hand-off

What the port offers is derived from what the upstream PoE switch grants, so nothing is offered before the grant is known. The PoE side hands over three values:

| Value | Source |
|---|---|
| Granted power at the PoE input | Classification result or LLDP allocation |
| Efficiency of the 5 V converter | Converter design |
| Power the adapter uses itself | Measurement of the switch and its supplies |

The current available at 5 V is the granted power times the efficiency, less the adapter's own power, divided by 5 V. The [power budget per PoE class](poe.md#5-raspberry-pi-5-power-budget-against-poe-classes) gives the figures before the adapter's own use. The offer follows from that current [**I**](#evidence-codes):

| Current available at 5 V | Rp | Source_Capabilities |
|---|---|---|
| Under 1.5 A | Off | None |
| 1.5 A to under 3 A | 12 kΩ | None |
| 3 A to under 5 A | 12 kΩ and 7.5 kΩ | 5 V at the available current |
| 5 A or more | 12 kΩ and 7.5 kΩ | 5 V at 5 A |

- Below 3 A the port advertises by Rp alone. PD 3 uses the two Rp values for collision avoidance, so a PD source has to be able to show the 3 A value.
- An offer above 3 A relies on the [captive cable](#captive-cable).
- If an LLDP allocation changes while a sink is attached, the source sends a new Source_Capabilities message. If the new budget is below the running contract, the sink has to accept the lower offer before the adapter may count on it.
- The source enforces the offer with the current limit of the VBUS load switch, because a sink is not bound by Rp.

## What the YT9215 offers

### Documented resources

Every row is from the pin tables of the datasheet [**V**](#evidence-codes). The datasheet calls port 9 Extension GMAC2 and names its pins `RG2_` in RGMII mode and `M2_` in MII mode. Port 9 is the only port of the YT9215SCH with such pins; port 8 has a SerDes interface only.

| Resource | Pin | Pin also used for |
|---|---|---|
| GPIO5 | 44 | Interrupt output |
| GPIO6 to GPIO17 | 46 to 57 | Port 9 |
| GPIO31 | 67 | LEDs |
| GPIO32 to GPIO43 | 70 to 81 | LEDs |
| GPIO44 to GPIO46 | 83 to 85 | LEDs |
| GPIO47 to GPIO50 | 90 to 93 | Management interface |
| UART0 receive | 46 | Port 9 |
| UART0 transmit | 47 | Port 9 |
| UART1 receive | 70 | Port 4 LED2 |
| UART1 transmit | 76 | Port 2 LED2 |
| I²C master 1 data | 72 | Port 4 LED1 |
| I²C master 1 clock | 73 | Port 3 LED1 |
| I²C master 2 data | 81 | Port 1 LED1 |
| I²C master 2 clock | 84 | Port 0 LED1 |
| SPI flash, group SPF0 | 49 | Port 9 TXD0 |
| SPI flash, group SPF0 | 50 | Port 9 TX_CTL |
| SPI flash, group SPF0 | 54 | Port 9 RXD0 |
| SPI flash, group SPF0 | 55 | Port 9 RXD1 |
| SPI flash, group SPF1 | 78 | Port 2 LED1 |
| SPI flash, group SPF1 | 79 | Port 1 LED2 |
| SPI flash, group SPF1 | 81 | I²C master 2 data |
| SPI flash, group SPF1 | 83 | Port 0 LED2 |
| Buzzer output | 67 | GPIO31 |

- The GPIO-capable pins number 33.
- The two SMI masters use the pins of the two I²C masters.
- The I²C masters run at 100 kHz to 1 MHz (Table 34 of the datasheet).
- The SPI flash interface runs at 31.25 MHz (Table 33) and is described only as a flash controller.
- UART baud rates are not given.
- [Figure 9 of the datasheet](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) shows the I²C master driving a PoE power-sourcing controller, so managing a power chip over I²C is a use Motorcomm intends.

### The CPU

| Item | Value | Source | Evidence |
|---|---|---|---|
| Core | Nuclei N205 | [Press release](yt9215-embedded-cpu.md#identity) | [**V**](#evidence-codes) |
| Instruction set of vendor builds | RV32EC | [`make.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/make.cfg#L29) | [**V**](#evidence-codes) |
| Compiler | `riscv-nuclei-elf-gcc` | [`.config`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/config/freeRTOS/.config) | [**V**](#evidence-codes) |
| Operating system | FreeRTOS | [`freert.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/env/freert.cfg) | [**V**](#evidence-codes) |
| Switch register access | Direct memory read and write | [`mem.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/drv/sw_ctrl/mem/mem.c) | [**V**](#evidence-codes) |
| Name of the frame transmit function | `eth_tx_by_portlist()` | [`fal_tiger_nic.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_nic.c) | [**V**](#evidence-codes) |
| Name of the frame receive function | `eth_rx_register()` | [`fal_tiger_nic.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_nic.c) | [**V**](#evidence-codes) |
| Behaviour of those two functions | Unpublished | – | [**U**](#evidence-codes) |
| CPU port number | 10 | [Board profile](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/common/boardprofile/bprofile_YT9215SC_default_demo.c#L50) | [**V**](#evidence-codes) |
| SRAM | 64 KB | [Datasheet](yt9215-embedded-cpu.md#memory) | [**V**](#evidence-codes) |
| Instruction cache | 2 KB | [Datasheet](yt9215-embedded-cpu.md#memory) | [**V**](#evidence-codes) |
| Clock frequency | Unpublished | – | [**U**](#evidence-codes) |
| Timers | Unpublished | – | [**U**](#evidence-codes) |
| GPIO registers | Unpublished | – | [**U**](#evidence-codes) |
| GPIO interrupts | Unpublished | – | [**U**](#evidence-codes) |
| Boot image format | Unpublished | – | [**U**](#evidence-codes) |

The vendor builds may be conservative, so the core could have more than RV32EC, but firmware should assume RV32EC until the chip says otherwise [**I**](#evidence-codes).

The SDK calls the two frame functions and includes their header `eth_export.h`, but does not contain their code. Its build file [`freert.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/env/freert.cfg) adds include paths into a firmware tree named `switch_sw_lite_mgmt`, with folders for FreeRTOS and for `SoC/yt921x` support code [**V**](#evidence-codes). That tree is the likely home of the frame functions, the timers, the GPIO registers, the interrupt numbers and the boot format [**I**](#evidence-codes). It is not public [**U**](#evidence-codes).

### Electrical limits of the pins

The values are for a 3.3 V pin supply. The port 9 pins have their own supply, DVDDIO_1, which may be 1.8 V, 2.5 V or 3.3 V; this note assumes 3.3 V.

| Parameter | Value | Evidence |
|---|---|---|
| Input high, minimum | 2.0 V | [**V**](#evidence-codes) |
| Input low, maximum | 0.8 V | [**V**](#evidence-codes) |
| Output high, minimum | 2.4 V | [**V**](#evidence-codes) |
| Output low, maximum | 0.4 V | [**V**](#evidence-codes) |
| Input voltage, absolute maximum | Supply plus 0.3 V | [**V**](#evidence-codes) |
| Drive strength | Not given | [**U**](#evidence-codes) |
| Hysteresis | Not given | [**U**](#evidence-codes) |

Three consequences follow [**I**](#evidence-codes):

- A BMC signal peaks at 1.2 V, below the 2.0 V input-high level. No pin can receive it directly, so a comparator is required.
- An attached sink pulls CC to about 1.7 V against a 3 A Rp. That lies between the two input thresholds, so attach detection also needs a comparator. Only the weakest Rp (36 kΩ to 3.3 V) gives a level a plain input reads as low, about 0.4 V, and it advertises the default USB current instead of 3 A.
- The pins are not 5 V tolerant. CC can touch VBUS through a faulty cable, so every pin that reaches CC needs a series resistor and a clamp.

### Interfaces that do not fit BMC

These look promising and do not work [**I**](#evidence-codes):

- **UART.** Every character is framed by a start and a stop bit, so a UART cannot emit or capture an unbroken bit stream.
- **I²C and SMI masters.** Both are open-drain and send fixed frame formats.
- **SPI flash master.** It is documented only as a flash controller, and in the XIP boot mode it is busy fetching code. Whether it can send raw bytes is unknown.
- **Serial LED output.** It repeats a short register-defined pattern at an unpublished clock rate ([LED guide](yt9215-registers/docs/leds.rst)).
- **Buzzer.** The SDK table [`LOOP_DETECT_TOP_CTRL`](yt9215-registers/sdk-tables.yaml) has a 2-bit mode and an enable for it. That describes a tone, not a data output.

<a id="option-0"></a>

## No PD: resistor and attach comparator

A 4.7 kΩ resistor from CC to 3.3 V advertises 3 A and is the only signalling part. The 3.3 V comes from a GPIO or a switched rail, so that Rp is off until PoE power is granted ([start-up order](#start-up-order)). USB-C also requires the source to keep VBUS off until a sink is attached and to remove it on detach ([attach detection](usb-c-pd.md#43-source-state-machine-and-timing)). A comparator that watches CC does this by driving the enable of the VBUS load switch directly, because a plain input pin cannot read the attach level ([electrical limits](#electrical-limits-of-the-pins)). A Raspberry Pi 5 then boots and limits its USB ports to 600 mA, unless `usb_max_current_enable=1` is set on the Pi ([Raspberry Pi 5](usb-c-pd.md#3-raspberry-pi-5-specifics)). This is the baseline every other option has to beat. It needs no firmware, so it works with the YT9215 CPU switched off and no flash fitted.

<a id="option-a"></a>

## Option A: I²C PD transceiver

A PD transceiver such as the onsemi FUSB302B contains the BMC transmitter and receiver, the CC comparators for both CC pins, switchable Rp current sources, a VCONN switch, and logic that sends GoodCRC and retries by itself. The host reads and writes whole messages over I²C.

| YT9215 resource | Pin | Use |
|---|---|---|
| I²C master 1 data | 72 | Messages and control |
| I²C master 1 clock | 73 | Messages and control |
| GPIO output | Any free | VBUS load switch |
| GPIO input | Any free | Interrupt line of the transceiver |

The interrupt line is optional: the firmware can poll the status registers instead.

Everything the firmware does is then slower than a millisecond. The tightest deadline is answering a Request within 15 ms. A FreeRTOS task with polled I²C meets that without any timer or interrupt knowledge [**I**](#evidence-codes). Using I²C master 1 gives up the LED1 outputs of ports 3 and 4 [**V**](#evidence-codes).

The remaining risks [**U**](#evidence-codes):

- **Firmware on the CPU.** This is common to options A, B and C.
- **Pin function.** The datasheet says pins 72 and 73 need "to enable the I2C function by software programming" and does not name the register.
- **Master registers.** The registers of the I²C master are unpublished. The I²C code in the SDK is the host side of the management interface, not a driver for this master.
- **Transaction format.** The datasheet shows this master only driving a PSE chip. The EEPROM reader on pins 91 and 92 is a separate interface. Whether the master can run the arbitrary reads and writes a transceiver needs is not stated.

If the master does not fit, I²C at 100 kHz can be bit-banged on two GPIO pins, which then needs the GPIO registers of [option B](#option-b) and none of its timing.

<a id="option-b"></a>

## Option B: GPIO bit-bang

The firmware toggles a GPIO for transmit and times the edges of a comparator output for receive. The external parts are those of the [front end](#front-end), connected to GPIO pins.

Published designs that run PD without a PD chip lean on a hardware timing peripheral, not on counted CPU cycles:

| Design | Direction | Peripheral | Source |
|---|---|---|---|
| Chromium EC on STM32 | Transmit | SPI fed by DMA | [`usb_pd_phy.c`](https://chromium.googlesource.com/chromiumos/platform/ec/+/v2.2.0/chip/stm32/usb_pd_phy.c) |
| Chromium EC on STM32 | Receive | Comparator into timer capture | [`usb_pd_phy.c`](https://chromium.googlesource.com/chromiumos/platform/ec/+/v2.2.0/chip/stm32/usb_pd_phy.c) |
| g3gg0 on ESP32 | Transmit | RMT pulse generator | [Hackaday](https://hackaday.com/2025/01/10/bit-banging-the-usb-pd-protocol) |
| g3gg0 on ESP32 | Receive | RMT pulse timer | [Hackaday](https://hackaday.com/2025/01/10/bit-banging-the-usb-pd-protocol) |

The YT9215 has no documented equivalent [**U**](#evidence-codes). Pure software timing needs all of the following, and none is published:

- GPIO data registers that the CPU can write and read in a few cycles.
- A clock fast enough to sample at 2.4 MHz or more, with interrupts off and the loop in RAM or in the 2 KB cache.
- A free-running counter to time edges.
- A way to notice the start of a message: a GPIO edge interrupt, or a polling loop that leaves no time for other firmware.

If the CPU runs from the 125 MHz switch clock ([clock](yt9215-embedded-cpu.md#clock)), there are about 200 cycles per half bit, which is enough [**I**](#evidence-codes). This option stays open until the registers are known.

<a id="option-c"></a>

## Option C: the port 9 MAC as serialiser

The MAC of extension port 9 shifts bytes out on pins under crystal timing. Run at 10 Mbit/s, it becomes the BMC transmitter. Port 9 must be in RGMII mode, or in the mode the register guide calls REVMII (MII as the PHY side), because in those two modes the chip itself drives the transmit clock. The [register guide](yt9215-registers/docs/ports.rst) shows the bring-up on port 8 of the YT9215RB, and the same fields exist for port 9.

### Transmit

![Port 9 at 10 Mbit/s: two equal frame bytes make one BMC half bit on TXD1](yt9215-usb-pd/mac-serialiser.svg)

- At 10 Mbit/s the RGMII transmit clock is 2.5 MHz [**V**](#evidence-codes). Each cycle carries one nibble, low nibble first, as the RGMII and IEEE 802.3 standards define.
- Pin TXD1 carries bit 1 and then bit 5 of each byte. Two bytes of `0x22` hold it high for four nibbles, 1.6 µs, and two bytes of `0x00` hold it low.
- A half bit of 1.6 µs gives 312.5 kbit/s, inside the 270 to 330 kbit/s that PD allows [**S**](#evidence-codes).
- TXD1 is low during the Ethernet preamble and start-of-frame delimiter, because bit 1 of the nibbles `0x5` and `0xD` is 0. TXD0 would be high there, which is why TXD1 is the pin to use.
- TX_CTL is high for the whole frame, preamble included. It enables an external buffer, so that the driver is off the CC line between frames ([strap pins](#pins-used) complicate this at reset). The buffer then pulls CC low for 6.4 µs before the first PD bit. PD allows the driver to start at most 1 µs before the first bit, so this breaks the specification, and whether sinks tolerate it is a bench question [**I**](#evidence-codes). [Enable from TXD3](#enable-from-txd3) is a way around it.
- PD wants the last bit closed by an edge and the line then held low before release. The frame ends with the closing edge and four extra bytes.
- The MAC appends a 4-byte FCS, which would put uncontrolled levels on TXD1. The four extra bytes are chosen so that TXD1 is low in them and in the FCS that results. The line is then low for 6.4 µs and released [**S**](#evidence-codes).

[`mac_bmc_frame.py`](yt9215-usb-pd/mac_bmc_frame.py) builds the frames and checks each by replaying its nibbles through a BMC decoder [**S**](#evidence-codes):

| Message | PD bits | Frame bytes, shortest | Frame bytes, longest | Time on the wire |
|---|---|---|---|---|
| GoodCRC | 149 | 604 | 608 | 0.49 ms |
| Accept | 149 | 604 | 608 | 0.49 ms |
| PS_RDY | 149 | 604 | 608 | 0.49 ms |
| Source_Capabilities, one offer | 189 | 764 | 768 | 0.62 ms |
| Hard Reset | 84 | 348 | 348 | 0.28 ms |

The frame length depends on the MessageID, because a message that ends on a low level needs one more bit time for its closing edge.

| Step | Register or function | Guide page | Evidence |
|---|---|---|---|
| Select the port 9 mode | `XMII` mode field | [Ports](yt9215-registers/docs/ports.rst) | [**V**](#evidence-codes) |
| Force 10 Mbit/s full duplex | `PORT_CTRL` | [Ports](yt9215-registers/docs/ports.rst) | [**V**](#evidence-codes) |
| Keep other traffic off port 9 | Port isolation | [Forwarding](yt9215-registers/docs/forwarding.rst) | [**I**](#evidence-codes) |
| Send the prepared frame to port 9 | `eth_tx_by_portlist()` | [CPU tag](yt9215-registers/docs/cpu-tag.rst) | [**U**](#evidence-codes) |

What is not known about transmit [**U**](#evidence-codes):

- Whether `eth_tx_by_portlist()` sends a frame unchanged, or adds a tag or padding.
- The delay from the CPU handing over a frame to its first nibble on the pins. It must fit in the 195 µs GoodCRC limit together with the receive side.
- Whether a sink accepts the waveform. This has not been tried on hardware.

### Receive

The same MAC can sample the line.

- Tie RXD0 high, RXD1 low and RXD2 high, and feed the **inverted** slicer output to RXD3.
- An idle CC line is high: about 1.7 V with a sink attached, above the 0.55 V slicer threshold. RXD3 is then low and the MAC sees the nibble `0x5`, which is Ethernet preamble.
- A PD transmitter starts by pulling the line low. RXD3 goes high, the nibble becomes `0xD`, and the MAC takes it as the start-of-frame delimiter.
- Every later nibble is `0x5` or `0xD`, so each received byte holds two samples of the CC line taken 400 ns apart. That is 4.2 samples per half bit, enough to tell half bits from full bits [**I**](#evidence-codes).
- While a partner transmits, its driver swings CC between 0 V and 1.1 V, so the fixed 0.55 V threshold sits in the middle of the signal.
- RX_CTL tells the MAC that data is valid. A GPIO holds it high while the port waits and pulses it low when the line has been idle for some microseconds, which ends the frame.

Five things have to hold, and none is documented [**U**](#evidence-codes):

- **Frames with a bad FCS must reach the CPU.** A captured PD message is not a valid Ethernet frame. The SDK counts such frames ([`RX_FCS_ERR`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/include/yt_stat.h#L37)), and the register tables hold no field that forwards them. If the MAC always drops them, this receive path is dead.
- **The MAC must accept a preamble of any length**, because the line can idle for seconds.
- **The firmware must see the end of a message** to pulse RX_CTL, which needs a readable GPIO and a time base, as in [option B](#option-b), though with looser timing.
- **The receive clock must run.** In RGMII mode the chip expects RXC from outside, so TXC is looped back to it.
- **The switch must not act on the addresses.** With RXD0 tied high, bit 0 of every captured byte is 1, so both the destination and the source address of the captured frame have the group bit set. Port 9 has to be isolated so that the frame goes to the CPU port only, and the switch must not discard a frame whose source is a group address.

The frame reaches the CPU only after RX_CTL falls. The 195 µs budget is then spent on end-of-message detection, frame delivery, decoding about 800 bytes and queueing the reply.

A sink may send messages with several data objects. A message with six data objects, or five at the slowest bit rate, is longer than a 1518-byte frame, so port 9 must accept jumbo frames, which the chip supports up to 9216 bytes ([frame size](yt9215-registers/docs/ports.rst)) [**V**](#evidence-codes).

### Pins used

Option C uses pins 46 to 57. They are free as long as nothing else is attached to port 9, which holds for a design with no external CPU. Four of them, 49, 50, 54 and 55, are also the SPF0 flash pins, so the flash must sit on group SPF1, the default. SPF1 takes pin 81 and with it I²C master 2. Pins 46 and 47 are also UART0, so a serial console has to use UART1.

Several of these pins are strap pins, read at reset [**V**](#evidence-codes):

| Pin | Port 9 signal | Strap | Level needed at reset |
|---|---|---|---|
| 46 | TXD3 | `SWITCH_ID_1` | Either |
| 47 | TXD2 | `RESERVED_0` | High |
| 48 | TXD1 | `RESERVED_1` | High |
| 49 | TXD0 | `SPF_MUX_SEL` | Low |
| 50 | TX_CTL | `RESERVED_2` | High |
| 51 | TXC | `SWITCH_ID_0` | Either |

The datasheet asks for an external 4.7 kΩ pull-up on each of pins 47, 48 and 50. Two problems follow [**I**](#evidence-codes):

- **The buffer is enabled from power-on.** With pins 48 and 50 pulled high, the buffer drives CC to 1.15 V until firmware puts port 9 into its 10 Mbit/s mode, and Rp does not work during that time. The enable therefore has to be gated by a second signal that is low at reset, such as a GPIO with a pull-down through an AND gate. The [front end](#front-end) includes that gate.
- **The clock loop joins two pins with opposite pulls.** Pin 51 has an internal pull-down and is a strap; pin 52 has an internal pull-up. An external strap resistor on pin 51 has to set the level. The REVMII mode needs no loop.

Three more wiring rules apply [**I**](#evidence-codes):

- Pins 54 to 56 are tied to their fixed levels through resistors, because they are also GPIO and flash pins and can be driven.
- Port 9 must have flow control off, so that the MAC never sends a pause frame onto CC.
- The firmware starts a transmit only when no receive is in progress.
- The receive path also captures the adapter's own transmissions, because CC going low starts a frame. The firmware ends that frame before the partner replies, or accepts that the partner's GoodCRC arrives in the same captured frame.

<a id="enable-from-txd3"></a>

### Enable from TXD3

A variant takes the buffer enable from TXD3, pin 46, in place of TX_CTL [**I**](#evidence-codes). The script does not cover it.

- TXD3 is 0 in every preamble nibble and 1 in the last nibble of the start-of-frame delimiter, so the buffer turns on 400 ns before the first PD bit, inside the 1 µs that PD allows.
- The data bytes become `0xAA` for high and `0x88` for low, which hold TXD3 high through the message.
- The tail has to keep TXD3 high and TXD1 low through the FCS. That is 16 conditions in place of 8, so the tail is longer than four bytes.
- Pin 46 has an internal pull-down as a strap, so the buffer is off at reset and the AND gate goes away, provided the board strap for `SWITCH_ID_1` is low.
- The level of TXD3 between frames is not documented [**U**](#evidence-codes).

<a id="front-end"></a>

## Front end for options B and C

![Front end: buffer and resistor for transmit, protection, two comparators for receive and attach detection, switchable Rp and a load switch](yt9215-usb-pd/front-end.svg)

The figure shows the option C wiring with a [captive cable](#captive-cable). Option B uses the same parts on GPIO pins and has no fixed receive wiring. The last three rows of the table apply to option C only.

| Part | Example | Quantity | Job |
|---|---|---|---|
| Buffer with enable | 74AUP1G126 | 1 | BMC driver |
| AND gate | 74AUP1G08 | 1 | Keeps the buffer off at reset |
| Capacitor | 200 to 600 pF | 1 | Receiver capacitance of the port |
| Series resistor | 47 Ω | 1 | Driver impedance |
| Dual comparator | Not chosen | 1 | Slicer and attach detector |
| Divider resistors | – | 4 | Two thresholds |
| Series resistor | 1 kΩ | 1 | CC protection |
| Clamp diode | – | 1 | CC protection |
| Rp, first | 12 kΩ | 1 | Advertises 1.5 A |
| Rp, second | 7.5 kΩ | 1 | Raises it to 3 A |
| Slow comparator | LM393 class | 1 | VBUS at 0 V |
| Divider resistors | – | 2 | VBUS threshold |
| Tie resistors | – | 3 | Fixed levels on pins 54 to 56 |
| Strap resistor | – | 1 | Reset level of pin 51 |
| Pull-down resistor | – | 1 | Holds the AND gate input low at reset |

Notes on the parts [**I**](#evidence-codes):

- The buffer is powered from the 1.15 V core rail of the switch, DVDDL, so its output swings 0 to 1.15 V with no divider that would load CC.
- Pins 48 and 50 are also strap pins. The buffer inputs are high impedance, so they do not disturb the straps.
- Rp holds CC at 3.3 V with no sink attached and at about 1.7 V with one, while the buffer is off and powered from 1.15 V. The buffer must be a type whose disabled output accepts a voltage above its supply. Otherwise it clamps CC and attach detection fails.
- Each Rp resistor hangs on its own GPIO, which is either driven high or left floating. Both resistors together make about 4.6 kΩ. With both GPIOs floating, Rp is off ([start-up order](#start-up-order)).
- The slicer needs a propagation delay of about 200 ns or less and matched rising and falling delays. An LM393-class part is too slow.
- A load switch with a built-in discharge path covers VBUS discharge. Confirming that VBUS has reached 0 V needs a third comparator, because the chip has no ADC. The figure leaves it out, with the AND gate and the capacitor.

Open points of the transmit driver [**U**](#evidence-codes):

- The output resistance of a 74AUP1G126 at a 1.15 V supply may be far above 47 Ω, so the 33 to 75 Ω driver impedance is not assured.
- PD wants rise and fall times of at least 300 ns. The capacitance on CC is limited to 600 pF, which with a 75 Ω driver gives about 100 ns. A plain buffer therefore makes edges that are too fast, and meeting the limit needs a driver with a controlled slew rate ([BMC electrical](usb-c-pd.md#51-signalling)).
- The buffer output is not protected against VBUS on CC. A 1 kΩ series resistor is not possible in the transmit path, so it needs a clamp of its own or a switch ([CC protection](usb-c-pd.md#44-protection-on-cc)).
- DVDDL may be anywhere from 1.08 to 1.32 V [**V**](#evidence-codes). Above 1.20 V the swing is out of the PD range.

<a id="cost"></a>

## Cost

All figures are estimates for quantities of about 1,000 [**I**](#evidence-codes). The VBUS load switch, the CC protection against electrostatic discharge and the 5 V converter are the same in every option and are left out.

| Option | Part | Quantity | Cost, low | Cost, high |
|---|---|---|---|---|
| [No PD](#option-0) | Rp resistor | 1 | $0.001 | $0.001 |
| [No PD](#option-0) | Slow comparator | 1 | $0.03 | $0.03 |
| [No PD](#option-0) | Divider resistors | 2 | $0.002 | $0.002 |
| [No PD](#option-0) | **Total** | | **$0.03** | **$0.03** |
| [A](#option-a) | FUSB302B | 1 | $0.34 | $0.41 |
| [A](#option-a) | I²C pull-up resistors | 2 | $0.002 | $0.002 |
| [A](#option-a) | SPI flash for firmware | 1 | $0.10 | $0.10 |
| [A](#option-a) | **Total** | | **$0.44** | **$0.51** |
| [Front end](#front-end) | Buffer with enable | 1 | $0.04 | $0.04 |
| [Front end](#front-end) | AND gate | 1 | $0.03 | $0.03 |
| [Front end](#front-end) | Fast dual comparator | 1 | $0.10 | $0.30 |
| [Front end](#front-end) | Slow comparator | 1 | $0.03 | $0.03 |
| [Front end](#front-end) | Resistors | 15 | $0.01 | $0.01 |
| [Front end](#front-end) | Clamp diode | 1 | $0.01 | $0.01 |
| [Front end](#front-end) | Capacitor | 1 | $0.002 | $0.002 |
| [Front end](#front-end) | SPI flash for firmware | 1 | $0.10 | $0.10 |
| [Front end](#front-end) | **Total** | | **$0.32** | **$0.52** |

Options B and C both use the front end, so its total is the cost of either. That total and the total of option A overlap: the front end is cheaper by up to $0.19 or dearer by up to $0.08. A receptacle in place of the [captive cable](#captive-cable) adds a second set of CC parts to the front end and nothing to option A.

<a id="fixed-function-chips"></a>

## Fixed-function chips

| Chip | Role | Host interface | Offers 5 V 5 A | Price, low | Price, high | Price basis | Fit |
|---|---|---|---|---|---|---|---|
| Rp resistor | Source | None | No | $0.001 | $0.001 | Estimate | [Baseline](#option-0) |
| onsemi FUSB302B | Either | I²C | If the host says so | $0.34 | $0.41 | 1,000 pieces | [Option A](#option-a) |
| WCH CH32X035 | Either | None | If its firmware says so | $0.27 | $0.27 | Lowest tier | [Note](#chip-notes) |
| FM XPD319BP | Source | Not stated | Not listed | $0.11 | $0.11 | Lowest tier | [Note](#chip-notes) |
| WCH CH224K | Sink | None | Not applicable | $0.27 | $0.27 | 1,000 pieces | None |
| Hynetek HUSB238 | Sink | I²C | Not applicable | $0.29 | $0.29 | Lowest tier | None |
| Injoinic IP2721 | Sink | None | Not applicable | $0.38 | $0.38 | 1,000 pieces | None |

"Either" means the chip can be a source or a sink. The CH32X035 has no host interface because it runs its own firmware. Prices are unconfirmed LCSC list prices [**I**](#evidence-codes). The product pages: [FUSB302BMPX](https://www.lcsc.com/product-detail/C132291.html), [CH32X035F8U6](https://www.lcsc.com/product-detail/C42442062.html), [XPD319BP](https://www.lcsc.com/product-detail/USB-ICs_Shenzhen-Fuman-Elec-XPD319BP_C2937661.html), [CH224K](https://www.lcsc.com/product-detail/C970725.html), [HUSB238](https://www.lcsc.com/product-detail/C7471904.html), [IP2721](https://www.lcsc.com/product-detail/C603176.html).

<a id="chip-notes"></a>

- **Sink chips.** The CH224K, HUSB238 and IP2721 request a voltage from a charger. They are the right parts for a device that is powered from USB-C. This adapter is powered from PoE and supplies USB-C, so they do not apply.
- **Standalone source chips.** The XPD319BP listing describes a source with 5 V, 9 V and 12 V offers at 3 A. For a Raspberry Pi 5 a 3 A offer is no better than the [Rp resistor](#option-0), so such a chip is worth its cost only if it can offer 5 V at 5 A. No standalone source chip with a confirmed 5 A offer is known [**U**](#evidence-codes).
- **CH32X035.** It is cheaper than the FUSB302B and has a PD transceiver built in, but it is a second microcontroller with its own firmware. The design uses no microcontroller besides the YT9215 ([project overview](../README.md)), so it serves only as the price to beat.
- **FUSB302B.** It is the cheapest part listed here that keeps all firmware on the YT9215.

## What to find out next

| Question | Needs CPU firmware | Decides |
|---|---|---|
| [Does port 9 put the waveform on TXD1?](#q-waveform) | No | [Option C](#option-c) transmit |
| [Does a Pi 5 accept the 312.5 kbit/s waveform?](#q-pi) | No | [Option C](#option-c) transmit |
| [What does the MAC do with a bad FCS?](#q-fcs) | No | [Option C](#option-c) receive |
| [Which comparator is fast and cheap enough?](#q-comparator) | No | [Front end](#front-end) |
| [Can code run on the CPU?](#q-code) | – | Every option with firmware |
| [How is the I²C master enabled and driven?](#q-i2c) | Yes | [Option A](#option-a) |
| [Where are the GPIO registers and timers?](#q-gpio) | Yes | [Option B](#option-b) |
| [How long from frame hand-over to the first nibble?](#q-latency) | Yes | [Option C](#option-c) transmit |
| [Do captured frames reach the CPU?](#q-capture) | Yes | [Option C](#option-c) receive |

How to answer each:

- <a id="q-waveform"></a>**Waveform on TXD1.** On a board with the port 9 pins exposed, an external host sets port 9 to RGMII at 10 Mbit/s over the management interface, as the [register guide](yt9215-registers/README.md) describes. A PC on a copper port sends a frame from [`mac_bmc_frame.py`](yt9215-usb-pd/mac_bmc_frame.py), the switch forwards it to port 9, and an oscilloscope on pin 48 shows the result. `mac_bmc_frame.py --hex` prints such a frame. Its destination address is an unknown unicast address, so the switch floods it to port 9.
- <a id="q-pi"></a>**Pi 5.** Add the transmit half of the [front end](#front-end), send Source_Capabilities the same way, and look for the GoodCRC of the Pi on CC.
- <a id="q-fcs"></a>**Bad FCS.** Feed a frame with a wrong FCS into port 9 and see whether the switch forwards it to another port or only raises the error counter. Looping the port back needs no equipment: TX_CTL to RX_CTL, TXD3 to RXD3, TXC to RXC, and RXD0 to RXD2 tied as in the [receive scheme](#option-c). A frame sent out of the port then returns as `0x5` and `0xD` nibbles with a wrong FCS and group addresses. A rising `RX_FCS_ERR` counter shows that the MAC received it; whether it is forwarded answers the FCS and the address question together.
- <a id="q-comparator"></a>**Comparator.** Bench test candidates against a real PD sink.
- <a id="q-code"></a>**Code on the CPU.** Obtain the firmware tree, or read the flash image of a managed switch that uses a YT9215 and work out the image format from it. The [boot modes](yt9215-embedded-cpu.md#boot) say where the chip loads code from.
- <a id="q-i2c"></a>**I²C master.** The pin function register, the master's own registers and its transaction format come from the firmware tree, or from tracing a vendor image.
- <a id="q-gpio"></a>**GPIO and timers.** From the firmware tree.
- <a id="q-latency"></a>**Transmit latency.** Send a frame from the CPU to port 9 and time TX_CTL against a GPIO edge.
- <a id="q-capture"></a>**Captured frames.** Repeat the bad-FCS test with the CPU as the destination.

The first four questions can be answered on a bench now. The rest wait for code on the CPU. Until then, a board should carry the [Rp resistor](#option-0) and the footprint of an [I²C PD transceiver](#option-a), with the port 9 pins brought out to test points so that [option C](#option-c) can be tried on the same board.

## Files

| File | Contents |
|---|---|
| [`mac_bmc_frame.py`](yt9215-usb-pd/mac_bmc_frame.py) | Builds and checks the Ethernet frames that carry PD messages |
| [`bmc-coding.json`](yt9215-usb-pd/bmc-coding.json) | WaveDrom source of the BMC coding figure |
| [`goodcrc-turnaround.json`](yt9215-usb-pd/goodcrc-turnaround.json) | WaveDrom source of the turnaround figure |
| [`mac-serialiser.json`](yt9215-usb-pd/mac-serialiser.json) | WaveDrom source of the serialiser figure |
| [`render_wavedrom.py`](yt9215-usb-pd/render_wavedrom.py) | Renders the WaveDrom sources to SVG |
| [`make_front_end.py`](yt9215-usb-pd/make_front_end.py) | Draws the front-end figure |
