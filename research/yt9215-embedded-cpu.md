# The RISC-V CPU inside the YT9215

The adapter has no external MCU. Its firmware runs on the RISC-V CPU that Motorcomm
builds into the YT9215 switch IC. This note collects what is publicly known about that
CPU and lists what is unknown.

Related notes:

| Topic | Note |
| --- | --- |
| Pins of the CPU's debug and boot interfaces | [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md) |
| Switch registers | [`yt9215-registers/`](yt9215-registers/README.md) |
| Boards that carry a YT9215 | [`yt9215-boards.md`](yt9215-boards.md) |

<a id="evidence-codes"></a>
Statements that rest on a source are marked with one of these evidence codes:

- **V** verified: read directly in a cited source (datasheet, Linux source, vendor page).
- **I** inference: a judgement from family similarity or general knowledge.
- **VI**: part verified in a cited source, part inference.
- **C** conflicting: the source contradicts itself.

## Summary

| Item | Value | Evidence | Detail |
| --- | --- | --- | --- |
| Core | Nuclei N205 | [**V**](#evidence-codes) | [Identity](#identity) |
| Instruction set | RV32IMAC-class | [**I**](#evidence-codes) | [Identity](#identity) |
| SRAM (YT9215SCH) | 64 KB | [**V**](#evidence-codes) | [Memory](#memory) |
| Boot ROM (YT9215SCH) | 16 KB | [**V**](#evidence-codes) | [Memory](#memory) |
| I-cache (YT9215SCH) | 2 KB | [**V**](#evidence-codes) | [Memory](#memory) |
| Largest SPI NOR flash (YT9215SCH) | 8 MB | [**V**](#evidence-codes) | [Memory](#memory) |
| CPU clock | Unknown | – | [Clock](#clock) |
| Switch core clock | 125 MHz | [**V**](#evidence-codes) | [Clock](#clock) |
| Boot source | SPI flash | [**V**](#evidence-codes) | [Boot](#boot) |
| Boot source | EEPROM | [**V**](#evidence-codes) | [Boot](#boot) |
| Enable strap | `DIS_MCU` low | [**V**](#evidence-codes) | [Boot](#boot) |
| Switch port of the CPU | 10 | [**V**](#evidence-codes) | [Packet path](#packet-path) |
| UART pins on the chip | Yes | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| I²C master pins on the chip | Yes | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| MDIO master pins on the chip | Yes | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| GPIO pins on the chip | Yes | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| JTAG | Unconfirmed | [**VI**](#evidence-codes) | [Debug](#debug) |
| USB | Not in the datasheets | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| Vendor SDK for CPU firmware | None found | [**I**](#evidence-codes) | [Software](#software) |

## Identity

- A Nuclei (芯来) press release says Motorcomm's YT9215 series embeds the **Nuclei RISC-V
  N205** core, used for "lightweight remote management and cloud management"
  ([riscv-mcu.com, 2022-10-18](https://www.riscv-mcu.com/article-show-id-929.html))
  [**V**](#evidence-codes). Motorcomm's own
  [launch news](https://en.motor-comm.com/news/26.html) says only "built-in RISC-V
  processor" [**V**](#evidence-codes).
- The Nuclei N200 series is 32-bit with a 2-stage variable-length pipeline. Its
  instruction set is configurable up to RV32IEMACB, its local instruction and data SRAM
  and its I-cache are configurable, and it uses the Nuclei ECLIC interrupt controller.
  These series facts are from general knowledge of the Nuclei product line, with no
  source cited [**I**](#evidence-codes). Which options Motorcomm configured is unknown, so RV32IMAC is
  an assumption [**I**](#evidence-codes).
- The same N205 ("Bumblebee") core in the GD32VF103 gives 153 DMIPS and 360 CoreMark at
  108 MHz, about 1.4 DMIPS/MHz and 3.3 CoreMark/MHz
  ([GigaDevice](https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core))
  [**V**](#evidence-codes).
- Every YT9215 variant has the CPU. The evidence is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#every-variant-has-the-risc-v-mcu).

## Memory

The "Embedded RISC-V" subsection of the
[YT9215SCH V1.03 datasheet](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf),
with its section on the SPI flash interface, is the only public
description of the CPU's memory [**V**](#evidence-codes). The [YT9215S](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf), [YT9215SC](../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf) and
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
- The [`yt921x` Linux driver](https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.c) reads a `SYS_CLK` register. Its value 0 gives an 8 ns
  (125 MHz) switch core cycle on the YT9215, and 143 MHz and other values are selectable
  [**V**](#evidence-codes).
- The CPU probably runs from this clock or from a divider of it [**I**](#evidence-codes).
- At 70 to 125 MHz the GD32VF103 figures in [Identity](#identity) scale to about 100 to
  180 DMIPS [**I**](#evidence-codes).

## Boot

- The `DIS_MCU` strap enables or disables the CPU at power-on and at reset. Pulled down,
  the CPU is enabled. Pulled up, it is disabled [**V**](#evidence-codes).
- The [YT9215SCH boot table](motorcomm-debug-pins.md#boot-table) lists what the chip
  loads for each strap combination [**V**](#evidence-codes). Every loading mode needs
  `DISAUTOLOAD` low. The rows that load CPU code are:

  | `DIS_MCU` | `EN_SPIF` | `DIS_SPIS` | `SMI_SEL` | Loads from | Loads to | Evidence |
  | --- | --- | --- | --- | --- | --- | --- |
  | 0 | 1 | Any | Any | SPI flash | XIP | [**V**](#evidence-codes) |
  | 0 | 0 | 1 | 1 | EEPROM | RAM | [**V**](#evidence-codes) |
  | 1 | 1 | Any | Any | SPI flash | RAM | [**C**](#evidence-codes) |

  XIP means the code is executed in place from the flash and nothing is copied. The
  datasheet's figure "Load From Flash To RAM" draws the same strap levels as the third
  row, so the datasheet gives that combination twice. The row is marked
  [**C**](#evidence-codes) because it has `DIS_MCU` high, and the description of the
  `DIS_MCU` pin says a pull-up disables the CPU.
- On the YT9215S, the chip-select pin of the second flash pin group is also the
  `DISAUTOLOAD` strap, so the usual pull-up on chip select would latch `DISAUTOLOAD`
  high and nothing would load. The detail is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#spi-flash-on-the-yt9215s).
- The flash interface can sit on either of two pin groups, chosen by the `SPF_MUX_SEL`
  strap [**V**](#evidence-codes). The pins of each variant are in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#headline-findings).
- The image format, the size limit of an image, and any checksum or signature are not
  published. No firmware dump of a YT9215 product was found.

## Peripherals

The YT9215 datasheets list these functions of the chip beside the switch ports
[**V**](#evidence-codes). They are pins of the chip. Which of them the CPU controls is
not documented:

| Function | Detail |
| --- | --- |
| UART | [Pins of the YT9215S](motorcomm-debug-pins.md#uart-on-the-yt9215s) |
| SPI flash | [Pins of the YT9215S](motorcomm-debug-pins.md#spi-flash-on-the-yt9215s) |
| I²C master | – |
| MDIO master | – |
| GPIO | Shared with LED and strap pins |
| LEDs | Parallel mode |
| LEDs | Serial mode |
| Interrupt output | One pin |

The word "USB" does not occur in the
[YT9215SCH V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) or
[YT9215S Draft_05](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf)
datasheets [**V**](#evidence-codes). Neither names an ADC other than the one inside
the Ethernet PHY receiver [**V**](#evidence-codes).

The [YT9215SCH V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) datasheet describes the interrupt output as a signal to an external CPU. The pins of
the YT9215SC, YT9215SCH and YT9215RB are in the
[YT9215SC and YT9215SCH](motorcomm-debug-pins.md#yt9215sc-and-yt9215sch) and
[YT9215RB](motorcomm-debug-pins.md#yt9215rb) tables. How the CPU itself reaches these
functions (register addresses, drivers) is not published.

## Debug

- The [YT9215S](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf),
  [YT9215SC](../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf) and
  [YT9215RB](../datasheets/motorcomm/YT9215RB_Datasheet_Draft_05_2023-02-16.pdf) draft
  datasheets name two JTAG pin groups [**V**](#evidence-codes).
- The [YT9215SCH V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) datasheet has no JTAG pin names
  [**V**](#evidence-codes). The detail is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#the-newest-datasheet-has-no-jtag).
- If the CPU's debug module is on one of the JTAG groups, standard RISC-V debug with
  OpenOCD would give halt, memory dump and load [**I**](#evidence-codes). That has not
  been probed.

## Packet path

The upstream `yt921x` DSA driver
([`chip.c`](https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.c)
and [`chip.h`](https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.h))
gives these facts [**V**](#evidence-codes):

- The switch has 11 ports: "8 internal + 2 external + 1 mcu". The CPU is port 10.
- The driver's author notes that "Port 10 for MCU … is untested yet".
- `YT921X_CPU_COPY` (0x180690) has `TO_INT_CPU` and `TO_EXT_CPU` bits. From the names,
  frames can be trapped or copied to the internal CPU [**I**](#evidence-codes).
- The CPU tag TPID is 0x9988. [The register guide](yt9215-registers/docs/cpu-tag.rst)
  describes the tag as an external host sees it on an external CPU port.

From outside, the register space is reached over MDIO, I²C or SPI. The
[register guide and its bindings](yt9215-registers/README.md) describe that access from
an external host. How the CPU itself reaches the registers and port 10 is not published,
so how much of the guide carries over to firmware on the CPU is unknown.

## Software

- A [vendor SDK](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e)
  for driving the switch from an external host is public, and the
  [register guide](yt9215-registers/README.md) draws on it [**V**](#evidence-codes).
  Whether it holds any code for the internal CPU has not been checked.
- No Motorcomm SDK or programming guide for firmware on the CPU was found in searches
  [**I**](#evidence-codes).
- No public firmware, OpenOCD configuration or boot-ROM dump was found. Searches covered
  English and Chinese terms.
- A FreeBSD port of the switch driver exists
  ([if_yt921x_freebsd](https://github.com/am910021/if_yt921x_freebsd))
  [**V**](#evidence-codes).
- The toolchain would be upstream `riscv*-gcc -march=rv32imac` or the Nuclei SDK, with
  OpenOCD as the debugger [**I**](#evidence-codes).

## Unknowns

- CPU clock.
- Memory map.
- Boot ROM behaviour.
- Boot image format.
- Whether JTAG reaches the CPU.
- How the CPU reaches the switch registers.
- How the CPU sends and receives frames on port 10.

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
