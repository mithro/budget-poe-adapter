# The RISC-V CPU inside the YT9215

The adapter has no external MCU. Its firmware runs on the RISC-V CPU that Motorcomm
builds into the YT9215 switch IC. This note collects what is publicly known about that
CPU and lists what is still unknown.

Related notes:

| Topic | Note |
| --- | --- |
| Pins of the CPU's debug and boot interfaces | [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md) |
| Switch registers | [`yt9215-registers/`](yt9215-registers/README.md) |
| Boards that carry a YT9215 | [`yt9215-boards.md`](yt9215-boards.md) |

<a id="evidence-codes"></a>
Each statement is marked with one of these evidence codes:

- **V** verified: read directly in a cited source (datasheet, Linux source, vendor page).
- **I** inference: a judgement from family similarity or general knowledge.
- **VI**: part verified in a cited source, part inference.

## Summary

| Item | Value | Evidence | Detail |
| --- | --- | --- | --- |
| Core | Nuclei N205 | [**V**](#evidence-codes) | [Identity](#identity) |
| Instruction set | RV32IMAC-class | [**VI**](#evidence-codes) | [Identity](#identity) |
| SRAM | 64 KB | [**V**](#evidence-codes) | [Memory](#memory) |
| Boot ROM | 16 KB | [**V**](#evidence-codes) | [Memory](#memory) |
| I-cache | 2 KB | [**V**](#evidence-codes) | [Memory](#memory) |
| Largest SPI NOR flash | 8 MB | [**V**](#evidence-codes) | [Memory](#memory) |
| CPU clock | Unknown | – | [Clock](#clock) |
| Switch core clock | 125 MHz | [**V**](#evidence-codes) | [Clock](#clock) |
| Boot source | SPI flash | [**V**](#evidence-codes) | [Boot](#boot) |
| Boot source | EEPROM | [**V**](#evidence-codes) | [Boot](#boot) |
| Enable strap | `DIS_MCU` low | [**V**](#evidence-codes) | [Boot](#boot) |
| Switch port of the CPU | 10 | [**V**](#evidence-codes) | [Packet path](#packet-path) |
| UART | Yes | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| I²C master | Yes | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| MDIO master | Yes | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| GPIO | Yes | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| JTAG | Unconfirmed | [**VI**](#evidence-codes) | [Debug](#debug) |
| USB | Not in the datasheets | [**V**](#evidence-codes) | [Peripherals](#peripherals) |
| Vendor SDK for the CPU | None public | [**V**](#evidence-codes) | [Software](#software) |

## Identity

- A Nuclei (芯来) press release says Motorcomm's YT9215 series embeds the **Nuclei RISC-V
  N205** core, used for "lightweight remote management and cloud management"
  ([riscv-mcu.com, 2022-10-18](https://www.riscv-mcu.com/article-show-id-929.html))
  [**V**](#evidence-codes). Motorcomm's own
  [launch news](https://en.motor-comm.com/news/26.html) says only "built-in RISC-V
  processor" [**V**](#evidence-codes).
- The Nuclei N200 series is 32-bit with a 2-stage variable-length pipeline. Its
  instruction set is configurable up to RV32IEMACB, its local instruction and data SRAM
  and its I-cache are configurable, and it uses the Nuclei ECLIC interrupt controller
  [**V**](#evidence-codes). Which options Motorcomm configured is unknown, so RV32IMAC is
  an assumption [**I**](#evidence-codes).
- The same N205 ("Bumblebee") core in the GD32VF103 gives 153 DMIPS and 360 CoreMark at
  108 MHz, about 1.4 DMIPS/MHz and 3.3 CoreMark/MHz
  ([GigaDevice](https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core))
  [**V**](#evidence-codes).
- Every YT9215 variant has the CPU. The evidence is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#every-variant-has-the-risc-v-mcu).

## Memory

Section 4 of the
[YT9215SCH V1.03 datasheet](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf)
("Embedded RISC-V") is the only public description of the CPU's memory
[**V**](#evidence-codes). It says the CPU is there "to support software
management/protocol functions" and that it "can transmit to or receive frames from the
switch core". It lists these features:

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
- The `yt921x` Linux driver reads a `SYS_CLK` register. Its default gives an 8 ns
  (125 MHz) switch core cycle on the YT9215, and 143 MHz and other values are selectable
  [**V**](#evidence-codes).
- The CPU probably runs from this clock or from a divider of it [**I**](#evidence-codes).
- At 70 to 125 MHz the GD32VF103 figures in [Identity](#identity) scale to about 100 to
  180 DMIPS [**I**](#evidence-codes).

## Boot

- The `DIS_MCU` strap enables or disables the CPU at power-on and at reset. Pulled down,
  the CPU is enabled. Pulled up, it is disabled [**V**](#evidence-codes).
- The [YT9215SCH boot table](motorcomm-debug-pins.md#boot-table) lists what the chip
  loads for each strap combination [**V**](#evidence-codes). With `DISAUTOLOAD` low and
  the CPU enabled it gives two choices:

  | `EN_SPIF` | `DIS_SPIS` | `SMI_SEL` | Loads from | Loads to |
  | --- | --- | --- | --- | --- |
  | 1 | Any | Any | SPI flash | Nothing: the code is executed in place (XIP) |
  | 0 | 1 | 1 | EEPROM | CPU RAM |

- The flash interface can sit on either of two pin groups, chosen by the `SPF_MUX_SEL`
  strap [**V**](#evidence-codes). The pins of each variant are in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md).
- The image format, the size limit of an image, and any checksum or signature are not
  published. No firmware dump of a YT9215 product was found.

## Peripherals

The pin tables of the YT9215 datasheets list these functions beside the switch ports
[**V**](#evidence-codes):

| Function | Detail |
| --- | --- |
| UART | [Pins per variant](motorcomm-debug-pins.md) |
| SPI flash | [Pins per variant](motorcomm-debug-pins.md) |
| I²C master | In the feature list |
| MDIO master | In the feature list |
| GPIO | Shared with LED and strap pins |
| LEDs | Parallel mode |
| LEDs | Serial mode |
| Interrupt output | One pin, meant for an external CPU |

The word "USB" does not occur in the
[YT9215SCH V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) or
[YT9215S Draft_05](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf)
datasheets [**V**](#evidence-codes). Neither names an ADC other than the one inside
the Ethernet PHY receiver [**V**](#evidence-codes).

How the CPU itself reaches these functions (register addresses, drivers) is not
published.

## Debug

- The YT9215S, YT9215SC and YT9215RB draft datasheets name two JTAG pin groups
  [**V**](#evidence-codes).
- The YT9215SCH V1.03 datasheet has no JTAG pin names
  [**V**](#evidence-codes). The detail is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#the-newest-datasheet-has-no-jtag).
- If the CPU's debug module is on one of the JTAG groups, standard RISC-V debug with
  OpenOCD would give halt, memory dump and load [**I**](#evidence-codes). That has not
  been probed.

## Packet path

The upstream
[`yt921x` DSA driver](https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.c)
gives these facts [**V**](#evidence-codes):

- The switch has 11 ports: "8 internal + 2 external + 1 mcu". The CPU is port 10.
- The driver's author notes that "Port 10 for MCU … is untested yet".
- `YT921X_CPU_COPY` (0x180690) has `TO_INT_CPU` and `TO_EXT_CPU` bits, so frames can be
  trapped or copied to the internal CPU.
- The CPU tag TPID is 0x9988. The tag is described in
  [the register guide](yt9215-registers/docs/cpu-tag.rst).

From outside, the register space is reached over MDIO, I²C or SPI. How the CPU itself
reaches the registers and port 10 is not published.

## Software

- No public Motorcomm SDK or programming guide for the CPU was found
  [**V**](#evidence-codes). The `yt921x` author notes the "lack of document".
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
- Nuclei press release: <https://www.riscv-mcu.com/article-show-id-929.html>
- Motorcomm launch news: <https://en.motor-comm.com/news/26.html>
- GigaDevice GD32VF103 announcement: <https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core>
- Linux `yt921x` driver: <https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.c>
- `yt921x` v14 patch series: <https://ratatoskr.run/lkml/2025/10/3255221/t>
