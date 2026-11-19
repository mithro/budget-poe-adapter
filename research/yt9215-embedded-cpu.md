# The RISC-V CPU inside the YT9215

The adapter has no external MCU. Its firmware runs on the RISC-V CPU that Motorcomm
builds into the YT9215 switch IC. This note collects what is publicly known about that
CPU and lists what is unknown. How fast the CPU is likely to be, and whether that is
enough for the adapter firmware, is worked out in
[`yt9215-cpu-performance.md`](yt9215-cpu-performance.md).

Related notes:

| Topic | Note |
| --- | --- |
| Speed and resources of the CPU | [`yt9215-cpu-performance.md`](yt9215-cpu-performance.md) |
| Pins of the CPU's debug and boot interfaces | [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md) |
| Switch registers | [`yt9215-registers/`](yt9215-registers/README.md) |
| Boards that carry a YT9215 | [`yt9215-boards.md`](yt9215-boards.md) |

<a id="evidence-codes"></a>
## Evidence marks

Statements that rest on a source are marked with one of these words:

| Mark | Meaning |
| --- | --- |
| Verified | Read directly in a cited source |
| Inferred | A judgement from family similarity or general knowledge |
| Partly inferred | Part read in a cited source, part a judgement |
| Conflicting | The source contradicts itself |

## Summary

| Item | Value | Evidence | Detail |
| --- | --- | --- | --- |
| Core | Nuclei N205 | [Verified](#evidence-codes) | [Identity](#identity) |
| Instruction set of vendor builds | RV32EC | [Verified](#evidence-codes) | [Instruction set](#instruction-set) |
| Hardware multiplier | Unknown | – | [Instruction set](#instruction-set) |
| Pipeline | 2 stages | [Verified](#evidence-codes) | [Identity](#identity) |
| SRAM (YT9215SCH) | 64 KB | [Verified](#evidence-codes) | [Memory](#memory) |
| Boot ROM (YT9215SCH) | 16 KB | [Verified](#evidence-codes) | [Memory](#memory) |
| I-cache (YT9215SCH) | 2 KB | [Verified](#evidence-codes) | [Memory](#memory) |
| Largest SPI NOR flash (YT9215SCH) | 8 MB | [Verified](#evidence-codes) | [Memory](#memory) |
| CPU clock | Unknown | – | [Clock](#clock) |
| Switch core clock | 125 MHz | [Partly inferred](#evidence-codes) | [Clock](#clock) |
| Boot source | SPI flash | [Verified](#evidence-codes) | [Boot](#boot) |
| Boot source | EEPROM | [Verified](#evidence-codes) | [Boot](#boot) |
| Enable strap | `DIS_MCU` low | [Verified](#evidence-codes) | [Boot](#boot) |
| Boot image format | Unknown | – | [Getting code onto the CPU](#getting-code-onto-the-cpu) |
| Switch port of the CPU | 10 | [Verified](#evidence-codes) | [Packet path](#packet-path) |
| Switch register access from the CPU | Memory mapped | [Verified](#evidence-codes) | [Register access](#register-access) |
| Frame transmit from the CPU | `eth_tx_by_portlist()` | [Verified](#evidence-codes) | [Packet path](#packet-path) |
| Interrupt controller | Nuclei ECLIC | [Partly inferred](#evidence-codes) | [Interrupts and timers](#interrupts-and-timers) |
| Timer of the core | 64-bit `mtime` | [Partly inferred](#evidence-codes) | [Interrupts and timers](#interrupts-and-timers) |
| DMA | Not in any source | [Verified](#evidence-codes) | [Peripherals](#peripherals) |
| UART pins on the chip | Yes | [Verified](#evidence-codes) | [Peripherals](#peripherals) |
| I²C master pins on the chip | Yes | [Verified](#evidence-codes) | [Peripherals](#peripherals) |
| MDIO master pins on the chip | Yes | [Verified](#evidence-codes) | [Peripherals](#peripherals) |
| GPIO pins on the chip | Yes | [Verified](#evidence-codes) | [Peripherals](#peripherals) |
| JTAG | Unconfirmed | [Partly inferred](#evidence-codes) | [Debug](#debug) |
| USB | Not in the datasheets | [Verified](#evidence-codes) | [Peripherals](#peripherals) |
| Vendor operating system | FreeRTOS | [Verified](#evidence-codes) | [Software](#software) |
| Vendor compiler | `riscv-nuclei-elf-gcc` | [Verified](#evidence-codes) | [Software](#software) |
| Vendor firmware tree | Not public | [Partly inferred](#evidence-codes) | [Software](#software) |

## Identity

- A Nuclei (芯来) press release says Motorcomm's YT9215 series embeds the **Nuclei RISC-V
  N205** core, used for "lightweight remote management and cloud management"
  ([riscv-mcu.com, 2022-10-18](https://www.riscv-mcu.com/article-show-id-929.html))
  ([verified](#evidence-codes)). Motorcomm's own
  [launch news](https://en.motor-comm.com/news/26.html) says only "built-in RISC-V
  processor" ([verified](#evidence-codes)).
- Nuclei's [N200 series page](https://www.nucleisys.com/product/200.php) describes the
  series as a 32-bit core with a 2-stage pipeline and an instruction set that is
  configurable as "RV32I/EMACB/Zc". Its table gives the N205 a configurable hardware
  multiplier, hardware divider, instruction cache, instruction local memory (ILM), data
  local memory (DLM) and private peripheral interface, and no data cache and no
  floating-point unit. It lists the ECLIC interrupt controller, a timer, and debug over
  4-wire JTAG or 2-wire cJTAG as parts of the core ([verified](#evidence-codes)). The page
  names Motorcomm among Nuclei's partners ([verified](#evidence-codes)).
- Which of those options Motorcomm chose is in no public document. The
  [instruction set](#instruction-set) section gives the evidence from the vendor's own
  build.
- The GD32VF103 microcontroller has an N205 core
  ([Nuclei SDK build system](https://doc.nucleisys.com/nuclei_sdk/develop/buildsystem.html))
  ([verified](#evidence-codes)). It gives 153 DMIPS and 360 CoreMark at 108 MHz, about
  1.4 DMIPS/MHz and 3.3 CoreMark/MHz
  ([GigaDevice](https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core))
  ([verified](#evidence-codes)). Its instruction set configuration is not in those
  two sources. What those figures mean for an RV32EC configuration is
  estimated in
  [`yt9215-cpu-performance.md`](yt9215-cpu-performance.md#instruction-throughput).
- Every YT9215 variant has the CPU. The evidence is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#every-variant-has-the-risc-v-mcu).

## Instruction set

The public [vendor SDK](#software) has a build configuration for the internal CPU. It
sets these facts ([verified](#evidence-codes)):

| Item | Value | Source |
| --- | --- | --- |
| Architecture flag | `-march=rv32ec` | [`make.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/make.cfg#L29) |
| ABI flag | `-mabi=ilp32e` | [`make.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/make.cfg#L29) |
| Code model flag | `-mcmodel=medany` | [`make.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/make.cfg#L29) |
| Condition for these flags | `Tiger` set | [`make.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/make.cfg#L28) |
| Condition for these flags | `INTER_MCU` set | [`make.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/make.cfg#L27) |

What follows from the flags ([inferred](#evidence-codes)):

- **RV32E base.** The `ilp32e` ABI uses only the 16 registers `x0` to `x15`. Code built
  for it cannot be linked with code built for the 32-register `ilp32` ABI, so the whole
  vendor firmware is RV32E code. A core with 32 registers would run it, but a vendor
  that had 32 registers would not give half of them up. The core is therefore taken to
  be an N205 configured with the RV32E base, which the N200 series offers.
- **Compressed instructions.** The `c` in the flag means the vendor build emits 16-bit
  instructions, so the core decodes them.
- **No multiplier and no atomics in vendor code.** The flag has no `m` and no `a`, so
  the SDK library never uses a multiply, divide or atomic instruction. Objects with
  and without `m` link together, so the rest of the vendor firmware could still use a
  multiplier. Whether the core has one is unknown.
- **The chip can settle it.** The `misa` register of a RISC-V core reports its
  extensions. Reading it is the first thing to do with running code or a working
  debug port.

Firmware for the adapter should be built as RV32EC until `misa` says otherwise.

## Memory

The "Embedded RISC-V" subsection of the
[YT9215SCH V1.03 datasheet](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf),
with its section on the SPI flash interface, is the only public
description of the CPU's memory ([verified](#evidence-codes)). The [YT9215S](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf), [YT9215SC](../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf) and
[YT9215RB](../datasheets/motorcomm/YT9215RB_Datasheet_Draft_05_2023-02-16.pdf) draft datasheets give no figures, so the values are confirmed for the YT9215SCH
only. The YT9215SCH datasheet says the CPU is there "to support software
management/protocol functions" and that it "can transmit to or receive frames from the
switch core". The two sections give these figures:

| Item | Value |
| --- | --- |
| SRAM | 64 KB |
| Boot ROM | 16 KB |
| I-cache | 2 KB |
| Largest SPI NOR flash | 8 MB |
| Flash I/O mode | Single |
| Flash I/O mode | Dual |
| Flash addressing | 3-byte |

The memory map is not published.

## Clock

- The CPU clock is not published.
- The chip takes a 25 MHz crystal or oscillator
  ([YT9215SCH datasheet](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf))
  ([verified](#evidence-codes)).
- The [`yt921x` Linux driver](https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.h#L177) defines a `SYS_CLK` register at `0xE0040`. It names value 0 as 125 MHz for the
  YT9215 and value 1 as 143 MHz ([verified](#evidence-codes)).
  The vendor SDK reads the same register and turns value 0 into an 8 ns cycle time and value 1 into 7 ns
  ([`fal_tiger_rate.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_rate.c#L105)) ([verified](#evidence-codes)).
- Both use the cycle time for the rate meters of the switch, so `SYS_CLK` is taken to
  be the clock of the switch core ([inferred](#evidence-codes)).
- The SPI flash clock is 31.25 MHz ([Table 33](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=53) of the
  YT9215SCH datasheet) ([verified](#evidence-codes)). That is 125 MHz divided by 4, so the
  flash controller is clocked from the 125 MHz domain ([inferred](#evidence-codes)).
- The CPU probably runs from the 125 MHz clock or from a divider of it
  ([inferred](#evidence-codes)). The candidates and what each one would mean are in
  [`yt9215-cpu-performance.md`](yt9215-cpu-performance.md#clock-scenarios).

## Boot

- The `DIS_MCU` strap enables or disables the CPU at power-on and at reset. Pulled down,
  the CPU is enabled. Pulled up, it is disabled ([verified](#evidence-codes)).
- The [YT9215SCH boot table](motorcomm-debug-pins.md#boot-table) lists what the chip
  loads for each strap combination ([verified](#evidence-codes)). Every loading mode needs
  `DISAUTOLOAD` low. The rows that load CPU code are:

  | `DIS_MCU` | `EN_SPIF` | `DIS_SPIS` | `SMI_SEL` | Loads from | Loads to | Evidence |
  | --- | --- | --- | --- | --- | --- | --- |
  | 0 | 1 | Any | Any | SPI flash | XIP | [Verified](#evidence-codes) |
  | 0 | 0 | 1 | 1 | EEPROM | RAM | [Verified](#evidence-codes) |
  | 1 | 1 | Any | Any | SPI flash | RAM | [Conflicting](#evidence-codes) |

  XIP means the code is executed in place from the flash and nothing is copied. The
  datasheet's figure "Load From Flash To RAM" draws the same strap levels as the third
  row, so the datasheet gives that combination twice. The row is marked
  [conflicting](#evidence-codes) because it has `DIS_MCU` high, and the description of the
  `DIS_MCU` pin says a pull-up disables the CPU.
- On the YT9215S, the chip-select pin of the second flash pin group is also the
  `DISAUTOLOAD` strap, so the usual pull-up on chip select would latch `DISAUTOLOAD`
  high and nothing would load. The detail is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#spi-flash-on-the-yt9215s).
- The flash interface can sit on either of two pin groups, chosen by the `SPF_MUX_SEL`
  strap ([verified](#evidence-codes)). The pins of each variant are in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#headline-findings).
- The image format, the size limit of an image, and any checksum or signature are not
  published. [Getting code onto the CPU](#getting-code-onto-the-cpu) lists ways to
  find them.

## Getting code onto the CPU

No public source says how to make an image the CPU will run. This is the question that
blocks all firmware work, so this section collects what is known and then lists
experiments that can answer it.

### What is known

- **The boot ROM does the loading.** The reset description in the
  [YT9215SCH datasheet](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) has the step "Autoload from the EEPROM, or boot from
  Flash or EEPROM by internal CPU if needed" ([verified](#evidence-codes)). The CPU
  therefore starts in its 16 KB boot ROM, and the ROM decides from the straps where
  the code comes from ([inferred](#evidence-codes)).
- **Three routes are named** in the [boot table](#boot): run in place from SPI flash,
  copy from SPI flash to RAM, and copy from an I²C EEPROM to RAM
  ([verified](#evidence-codes)).
- **The EEPROM route fits the SRAM exactly.** The datasheet supports EEPROMs of 2 Kbit
  to 512 Kbit, and 512 Kbit is 64 KB, the size of the SRAM ([verified](#evidence-codes)).
  The `EEPROM_MOD` strap selects 1-byte or 2-byte addressing.
- **The same EEPROM interface also loads registers.** With `DIS_MCU` high the chip
  copies EEPROM contents into registers without the CPU ([verified](#evidence-codes)). The
  [LX-IS601F board](switch-board-strapping.md) is strapped this way and carries a
  24C08.
- **The datasheet's flash routes match two Nuclei SDK download modes.** The Nuclei SDK builds a program in one of
  the download modes `ilm`, `flash` and `flashxip`: run from RAM, copy from flash to
  RAM, and run in place from flash
  ([Nuclei SDK build system](https://doc.nucleisys.com/nuclei_sdk/develop/buildsystem.html))
  ([verified](#evidence-codes)). The two flash routes of the YT9215 are the last two
  ([inferred](#evidence-codes)).
- **The public SDK has nothing on images.** It holds no linker script, no start-up
  code, no image tool and no firmware binary ([verified](#evidence-codes)). The words "flash",
  "boot" and "XIP" do not occur in its source files ([verified](#evidence-codes)).
- **No firmware image is public.** Searches for a download, a flash dump or a
  teardown of a YT9215 product with flash turn up none ([inferred](#evidence-codes)).
- **JTAG is named only in the draft datasheets** ([debug](#debug)).

<a id="code-loading-unknowns"></a>
Unknown, in the order they matter:

- **Header and layout of a flash image.** Without them the ROM will not start the
  code.
- **Header and layout of an EEPROM image.** The same holds for the EEPROM route.
- **Checksum or signature.** A signature would close the flash and EEPROM routes.
- **Address the code runs at.** It is needed to link the firmware.
- **Whether JTAG is alive.** It would bypass the ROM altogether.

### Experiments

Each experiment needs only an existing YT9215 board and bench tools. They are in order
of cost. The first three need no code on the CPU and no knowledge of the image format.

| Experiment | Needs | Answers |
| --- | --- | --- |
| [Read the CPU's memory from outside](#exp-read-memory) | Management interface | Boot ROM contents |
| [Read the register-load EEPROM](#exp-read-eeprom) | EEPROM clip | Register image format |
| [Watch the ROM read an empty memory](#exp-watch-rom) | Logic analyser | Header size and position |
| [Raw code in XIP mode](#exp-raw-xip) | SPI flash | Whether XIP needs a header |
| [Probe JTAG](#exp-jtag) | JTAG adapter | Whether the debug port is alive |
| [Listen on the UARTs](#exp-uart) | USB serial adapter | Whether the ROM prints or listens |
| [Get a vendor image](#exp-vendor-image) | A managed YT9215 product | The format by example |

- <a id="exp-read-memory"></a>**Read the CPU's memory from outside.** For the CPU the
  switch registers are memory at their register addresses
  ([register access](#register-access)). An external host reaches the same registers
  with a 32-bit address over SMI, I²C or SPI
  ([access guide](yt9215-registers/docs/access.rst)). If both sit on one bus, the host
  may also be able to read the addresses of the boot ROM and the SRAM
  ([inferred](#evidence-codes)). The test is to read addresses outside the known register
  blocks, starting at 0, and look for RISC-V code. A readable boot ROM would answer
  every question in the [list above](#code-loading-unknowns), because it can be disassembled. A writable SRAM
  would be a way to load code with no image at all.
- <a id="exp-read-eeprom"></a>**Read the register-load EEPROM.** The 24C08 of the
  LX-IS601F holds a register image that the chip loads at reset
  ([board checks](switch-board-strapping.md)). Its layout shows how Motorcomm frames
  EEPROM data: a marker, a length, address and value pairs, a checksum. The code image
  for the EEPROM route is read by the same ROM and is likely to be framed the same way
  ([inferred](#evidence-codes)).
- <a id="exp-watch-rom"></a>**Watch the ROM read an empty memory.** Strap the chip for
  a code-loading route, fit an erased flash or EEPROM, and record the bus with a logic
  analyser. The read command, the first address and the number of bytes the ROM reads
  before it gives up show where the header is and how long it is. Filling the memory
  with a pattern and changing one field at a time then shows which bytes the ROM
  checks. On the EEPROM route the two-wire bus is slow enough for any analyser.
- <a id="exp-raw-xip"></a>**Raw code in XIP mode.** In XIP mode nothing is copied, so
  the ROM may simply jump to the start of the flash ([inferred](#evidence-codes)). The test
  program needs no GPIO: it stores a recognisable value in a switch register whose
  value is harmless, such as the switch's MAC address register, and the host reads that register back
  over the management interface. If the value appears, code is running. The same
  program is the probe for every later attempt at a header.
- <a id="exp-jtag"></a>**Probe JTAG.** Scan the JTAG pins of the draft datasheets for
  an IDCODE, with the CPU enabled. The
  [mirrored board](motorcomm-debug-pins.md#implications-for-the-adapter) has the pins
  on resistor pads. A live debug port allows halting the CPU, dumping the boot ROM and
  loading code into SRAM with OpenOCD.
- <a id="exp-uart"></a>**Listen on the UARTs.** Record both UART transmit pins at
  reset with the CPU enabled and no memory fitted, at 115200 baud and at other common
  rates. The SDK has a host-side driver that reads and writes switch registers with
  10-byte frames over a serial port at 115200 baud
  ([`uart.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/drv/sw_ctrl/uart/uart.c)) ([verified](#evidence-codes)). Whether
  the chip's own UART answers those frames, or whether they are for a separate bridge,
  is unknown. Sending one read frame for the chip ID register is a quick test.
- <a id="exp-vendor-image"></a>**Get a vendor image.** A web-managed switch built on a
  YT9215 has an SPI flash with a working image. [`yt9215-boards.md`](yt9215-boards.md)
  lists products that carry the chip. The vendor's [firmware tree](#software), with its image tool,
  is the other source. A distributor may supply it with the chip.

The first experiment is the cheapest and could settle everything, so it comes before
any board is modified.

## Peripherals

The [YT9215SCH datasheet](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) lists these functions of the chip beside the switch ports
([verified](#evidence-codes)). They are pins of the chip. Which of them the CPU controls,
and through which registers, is not documented:

| Function | Count | Speed | Detail |
| --- | --- | --- | --- |
| GPIO pins | 33 | Not given | [Table 19](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=27) |
| UART | 2 | Not given | [Pins](motorcomm-debug-pins.md#yt9215sc-and-yt9215sch) |
| I²C master | 2 | 100 kHz to 1 MHz | [Table 34](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=53) |
| SMI (MDIO) master | 2 | Up to 4 MHz | [Table 35](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=54) |
| SPI flash master | 1 | 31.25 MHz | [Table 33](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=53) |
| Buzzer output | 1 | Not given | [Pin 67](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=18) |
| Serial LED output | 1 | Not given | [LED guide](yt9215-registers/docs/leds.rst) |
| Interrupt output | 1 | – | [Pin 44](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=17) |
| Temperature sensor | 1 | – | [`fal_tiger_sensor.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_sensor.c) |

Notes on the table:

- Every GPIO pin shares its pin with another function: port 9, an LED, a strap or the
  management interface ([verified](#evidence-codes)).
- The two SMI masters use the pins of the two I²C masters, and the flash interface can
  sit on either of two pin groups ([verified](#evidence-codes)).
- The SMI figure is the 250 ns minimum clock period with a 1 kΩ pull-up
  ([verified](#evidence-codes)).
- The datasheet's block diagram draws "GPIO", "SMI", "I2C", "SPI", "LED" and "Internal Buffer" beside
  the CPU and nothing else. No source names a DMA controller, a PWM, a timer with capture
  inputs, a comparator or a general-purpose SPI master ([verified](#evidence-codes)).
- The public SDK has no function that reads or writes a GPIO pin, a UART or an I²C
  master ([verified](#evidence-codes)). Their registers are in the
  [firmware tree that is not public](#software) ([inferred](#evidence-codes)).
- The SDK's register tables, extracted to
  [`sdk-tables.yaml`](yt9215-registers/sdk-tables.yaml), name three things that touch
  these pins ([verified](#evidence-codes)). None of them is a register that reads or
  writes a GPIO pin directly:

  | Table | Address | Field | Width in bits |
  | --- | --- | --- | --- |
  | `ACL2GPIO` | `0x80384` | None described | – |
  | `ACL_ACTION_TBL` | `0x1C0000` | `GPIO_EN` | 1 |
  | `ACL_ACTION_TBL` | `0x1C0000` | `GPIO_PIN` | 4 |
  | `LOOP_DETECT_TOP_CTRL` | `0x80230` | `BUZZER_EN` | 1 |
  | `LOOP_DETECT_TOP_CTRL` | `0x80230` | `BUZZER_MODE` | 2 |

  The ACL fields let a matching rule act on 1 of 16 GPIO pins, and the buzzer output
  belongs to loop detection ([inferred](#evidence-codes)).

The word "USB" does not occur in the
[YT9215SCH V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) or
[YT9215S Draft_05](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf)
datasheets ([verified](#evidence-codes)). Neither names an ADC other than the one inside
the Ethernet PHY receiver ([verified](#evidence-codes)).

The [YT9215SCH V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) datasheet describes the interrupt output as a signal to an external CPU. The pins of
the YT9215SC, YT9215SCH and YT9215RB are in the
[YT9215SC and YT9215SCH](motorcomm-debug-pins.md#yt9215sc-and-yt9215sch) and
[YT9215RB](motorcomm-debug-pins.md#yt9215rb) tables, and the pins of the YT9215S are in
the [UART](motorcomm-debug-pins.md#uart-on-the-yt9215s) and
[SPI flash](motorcomm-debug-pins.md#spi-flash-on-the-yt9215s) sections.

## Interrupts and timers

Nothing about the CPU's interrupts or timers is in a Motorcomm document. The N200
series core brings both with it, and the vendor build uses Nuclei's support code, so
the Nuclei documents are the best available description ([partly inferred](#evidence-codes)):

- **Interrupt controller.** The N200 series uses Nuclei's ECLIC
  ([N200 series page](https://www.nucleisys.com/product/200.php)). Each interrupt source
  has a level and a priority, and can be vectored or non-vectored
  ([Nuclei ISA specification, interrupts](https://doc.nucleisys.com/nuclei_spec/isa/interrupt.html))
  ([verified](#evidence-codes)).
- **Interrupt latency.** For a vectored interrupt the specification gives 6 cycles from
  the request to the first instruction of the handler. For a non-vectored interrupt on
  RV32E it gives about 4 cycles to enter the common handler, 3 to save three control
  registers, 8 to save eight general registers and 5 to jump to the handler, 20 in all
  ([feature and latency sections](https://doc.nucleisys.com/nuclei_spec/isa/interrupt.html#feature-and-latency-of-vectored-processing-mode))
  ([verified](#evidence-codes)). These are Nuclei's ideal figures for the core, not a
  measurement of the YT9215.
- **Timer.** The core's timer unit has a 64-bit counter `mtime`, a compare register
  `mtimecmp` that raises the timer interrupt, and a software interrupt register `msip`
  ([Nuclei ISA specification, timer](https://doc.nucleisys.com/nuclei_spec/isa/timer.html))
  ([verified](#evidence-codes)). Nuclei's FreeRTOS port takes its tick from this timer
  ([inferred](#evidence-codes)). The clock that `mtime` counts on the YT9215 is unknown.
- **Cycle counter.** The Nuclei cores have the standard `mcycle` counter register
  ([Nuclei ISA specification, registers](https://doc.nucleisys.com/nuclei_spec/isa/core_csr.html))
  ([verified](#evidence-codes)). It counts CPU clock cycles unless it is stopped through the `mcountinhibit` register, and is read with one instruction,
  which makes it the finest time base firmware can have ([inferred](#evidence-codes)).
- **Interrupt sources.** Which chip events reach the ECLIC is unknown: no source says
  whether a GPIO edge, a received frame, a UART or the switch's own
  [interrupt status register](yt9215-registers/README.md) can interrupt the CPU. The
  SDK's receive call is polled from a task ([packet path](#packet-path)), which needs
  no interrupt.

## Debug

- The [YT9215S](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf),
  [YT9215SC](../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf) and
  [YT9215RB](../datasheets/motorcomm/YT9215RB_Datasheet_Draft_05_2023-02-16.pdf) draft
  datasheets name two JTAG pin groups ([verified](#evidence-codes)).
- The [YT9215SCH V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) datasheet has no JTAG pin names
  ([verified](#evidence-codes)). The detail is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#the-newest-datasheet-has-no-jtag).
- The N200 series has a standard RISC-V debug module with a 4-wire JTAG or a 2-wire
  cJTAG port ([N200 series page](https://www.nucleisys.com/product/200.php))
  ([verified](#evidence-codes)).
- If the CPU's debug module is on one of the JTAG groups, standard RISC-V debug with
  OpenOCD would give halt, memory dump and load ([inferred](#evidence-codes)). That has not
  been probed.

## Register access

From outside, the register space is reached over MDIO, I²C or SPI, and the
[register guide and its bindings](yt9215-registers/README.md) describe that access.
From the CPU the same registers are ordinary memory:

- The SDK's internal-CPU build selects the access driver
  [`mem.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/drv/sw_ctrl/mem/mem.c), whose read and write are one 32-bit load
  or store through a pointer made from the register address ([verified](#evidence-codes)).
- [`hal_mem.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/hal/hal_mem.c#L99) passes the address to that driver unchanged.
  It is the address the external host uses, such as `0x80008` for the chip ID
  ([verified](#evidence-codes)).
- The driver takes a FreeRTOS mutex around every access ([verified](#evidence-codes)).
  Firmware that owns the registers from one task does not need it
  ([inferred](#evidence-codes)).

The register addresses, fields and table procedures of the
[register guide](yt9215-registers/docs/index.rst) therefore apply to firmware on the
CPU, with a load or a store in place of the bus transaction ([inferred](#evidence-codes)).
This has not been run on hardware.

## Packet path

The upstream `yt921x` DSA driver
([`chip.c`](https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.c)
and [`chip.h`](https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.h))
gives these facts ([verified](#evidence-codes)):

- The switch has 11 ports: "8 internal + 2 external + 1 mcu". The CPU is port 10.
- The driver's author notes that "Port 10 for MCU … is untested yet".
- `YT921X_CPU_COPY` (0x180690) has `TO_INT_CPU` and `TO_EXT_CPU` bits.
- The CPU tag TPID is 0x9988. [The register guide](yt9215-registers/docs/cpu-tag.rst)
  describes the tag as an external host sees it on an external CPU port.

The vendor SDK shows how firmware on the CPU is meant to use port 10
([verified](#evidence-codes)):

| Step | SDK function | Source |
| --- | --- | --- |
| Send trapped frames to the internal CPU | `fal_tiger_nic_cpuport_mode_set()` | [`fal_tiger_nic.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_nic.c#L32) |
| Turn off address learning on port 10 | `fal_tiger_nic_init()` | [`fal_tiger_nic.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_nic.c#L19) |
| Trap LLDP frames per port | `fal_tiger_ctrlpkt_lldp_act_set()` | [`fal_tiger_ctrlpkt.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_ctrlpkt.c#L368) |
| Set number and size of frame buffers | `yt_nic_eth_buf_cnt_len_set()` | [`yt_nic.h`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/include/yt_nic.h#L120) |
| Register a receive callback | `yt_nic_rx_register()` | [`yt_nic.h`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/include/yt_nic.h#L71) |
| Poll for received frames | `yt_nic_rx_handler()` | [`yt_nic.h`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/include/yt_nic.h#L84) |
| Send a frame to a list of ports | `yt_nic_tx()` | [`yt_nic.h`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/include/yt_nic.h#L104) |

- **Receive.** The callback gets the frame with the port it arrived on, a CPU code that
  says why it was trapped, its length and its VLAN
  ([`yt_types.h`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/common/include/yt_types.h#L220)). The header calls
  `yt_nic_rx_handler()` the "rx handler API used in user's main task", so reception is
  polled from a task.
- **Transmit.** `yt_nic_tx()` sends a frame out of a given list of ports, or looks the
  destination up in a VLAN. For the port list it calls `eth_tx_by_portlist()`
  ([`fal_tiger_nic.c`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_nic.c#L275)).
- **Buffers.** The header sets minimums of 56 buffers, 6 of them for transmit, and
  256 bytes per buffer ([`yt_nic.h`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/include/yt_nic.h#L27)). The receive structure
  holds a frame of up to 1530 bytes ([`yt_types.h`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/common/include/yt_types.h#L42)).
- **LLDP.** The per-port LLDP action can be forward, trap, drop or copy. Trap sets the
  port's bit in both the copy-to-CPU and the drop mask of `L2_LLDP_PER_PORT_CTRL`
  (`0x180290`), so the frame goes to the CPU and nowhere else.

The functions `eth_init()`, `eth_rx_register()`, `eth_rx_handler()` and
`eth_tx_by_portlist()`, with their header `eth_export.h`, are called by the SDK and
are not in it. They belong to the [firmware tree](#software) that is not public. How a frame moves between the CPU's memory and the switch core, and
whether an interrupt announces a received frame, is therefore not published.

## Software

- A [vendor SDK](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e)
  for driving the switch is public, and the
  [register guide](yt9215-registers/README.md) draws on it ([verified](#evidence-codes)).
  It builds for an external Linux host and, with its `INTER_MCU` option, as a static
  library for firmware on the internal CPU
  ([`config/freeRTOS/.config`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/config/freeRTOS/.config)) ([verified](#evidence-codes)).
- The internal-CPU configuration gives these facts ([verified](#evidence-codes)):

  | Item | Value | Source |
  | --- | --- | --- |
  | Operating system | FreeRTOS | [`.config`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/config/freeRTOS/.config) |
  | Compiler prefix | `riscv-nuclei-elf-` | [`.config`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/config/freeRTOS/.config) |
  | Architecture | [RV32EC](#instruction-set) | [`make.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/make.cfg#L29) |
  | Register access | [Memory mapped](#register-access) | [`.config`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/config/freeRTOS/.config) |
  | Name of the firmware tree | `switch_sw_lite_mgmt` | [`freert.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/env/freert.cfg) |
  | Chip support folder | `SoC/yt921x` | [`freert.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/env/freert.cfg) |
  | Core support folder | `NMSIS/Core` | [`freert.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/env/freert.cfg) |
  | Application folder | `application/freertos/demo_http` | [`freert.cfg`](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/make/env/freert.cfg) |

- [NMSIS](https://doc.nucleisys.com/nmsis/) is Nuclei's software interface standard
  for its cores, so the build confirms a Nuclei core independently of the
  [press release](#identity) ([partly inferred](#evidence-codes)).
- The application folder name says the vendor firmware includes an HTTP demonstration,
  which needs a TCP/IP stack ([inferred](#evidence-codes)).
- The firmware tree `switch_sw_lite_mgmt` is not in the public SDK
  ([verified](#evidence-codes)) and does not turn up anywhere else in searches
  ([inferred](#evidence-codes)). It is the likely home of the frame driver, the
  GPIO, UART and I²C drivers, the interrupt numbers, the linker script with the memory
  map, and the tool that makes a boot image ([inferred](#evidence-codes)).
- Searches in English and Chinese turn up no public firmware image, OpenOCD
  configuration or boot-ROM dump.
- A FreeBSD port of the switch driver exists
  ([if_yt921x_freebsd](https://github.com/am910021/if_yt921x_freebsd))
  ([verified](#evidence-codes)).
- Upstream compilers also build RV32EC code. The
  [benchmark](yt9215-cpu-performance/README.md) of the performance note is built with
  clang 18 ([verified](#evidence-codes)).

## Unknowns

- CPU clock.
- Whether the core has a hardware multiplier.
- Memory map, apart from the switch registers.
- Boot ROM behaviour.
- Boot image format.
- Whether JTAG reaches the CPU.
- Registers of the GPIO pins, the UARTs and the I²C masters.
- Interrupt sources and their numbers.
- Clock of the `mtime` timer.
- How the frame driver moves frames to and from port 10.

## Sources

- YT9215SCH datasheet V1.03: [`YT9215SCH_Datasheet_V1.03_2025-02-10.pdf`](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf)
- YT9215SC datasheet Draft_07: [`YT9215SC_Datasheet_Draft_07_2023-02-28.pdf`](../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf)
- YT9215S datasheet Draft_05: [`YT9215S_Datasheet_Draft_05_2023-02-21.pdf`](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf)
- YT9215RB datasheet Draft_05: [`YT9215RB_Datasheet_Draft_05_2023-02-16.pdf`](../datasheets/motorcomm/YT9215RB_Datasheet_Draft_05_2023-02-16.pdf)
- Vendor switch SDK: <https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e>
- Nuclei press release: <https://www.riscv-mcu.com/article-show-id-929.html>
- Motorcomm launch news: <https://en.motor-comm.com/news/26.html>
- GigaDevice GD32VF103 announcement: <https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core>
- Linux `yt921x` driver: <https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.c>
- Nuclei N200 series page: <https://www.nucleisys.com/product/200.php>
- Nuclei ISA specification: <https://doc.nucleisys.com/nuclei_spec/>
- Nuclei NMSIS: <https://doc.nucleisys.com/nmsis/>
