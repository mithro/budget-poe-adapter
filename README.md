# Budget PoE to USB-C adapter

Notes and research for an open source, non-isolated, very cheap and
flexible PoE to USB-C adapter that passes Ethernet through at 1 Gbit/s or faster.

The design uses only the Motorcomm YT9215 switch IC and its internal RISC-V CPU. The
adapter's firmware runs on that CPU, and there is no external MCU and no other switch IC.

The project is at the research stage. It has no schematic or PCB of the adapter.

## What is here

| Folder | Contents | Index |
| --- | --- | --- |
| [`research/`](research/) | Research notes | [Research: power](#research-power) |
| [`research/`](research/) | Research notes | [Research: YT9215 switch IC](#research-yt9215-switch-ic) |
| [`datasheets/`](datasheets/) | Switch IC documentation | [`datasheets/README.md`](datasheets/README.md) |
| [`archive/`](archive/) | Archived notes that are not part of the current design | [Archive](#archive) |

The research notes cover these topics:

| Topic | Section |
| --- | --- |
| PoE | [Research: power](#research-power) |
| USB-C PD | [Research: power](#research-power) |
| YT9215 CPU | [Research: YT9215 switch IC](#research-yt9215-switch-ic) |
| YT9215 pins | [Research: YT9215 switch IC](#research-yt9215-switch-ic) |
| YT9215 registers | [Research: YT9215 switch IC](#research-yt9215-switch-ic) |
| Boards with a YT9215 | [Research: YT9215 switch IC](#research-yt9215-switch-ic) |

| Vendor | Datasheets in [`datasheets/`](datasheets/) |
| --- | --- |
| Motorcomm | Included |
| Realtek | Linked |

### Research: power

| File | Covers |
| --- | --- |
| [`poe.md`](research/poe.md) | PoE for a cheap software-driven powered device |
| [`usb-c-pd.md`](research/usb-c-pd.md) | USB-C power standards |
| [`usb-c-pd.md`](research/usb-c-pd.md) | Raspberry Pi 5 requirements |
| [`usb-c-pd.md`](research/usb-c-pd.md) | PD negotiation at the electrical level |

### Research: YT9215 switch IC

| File | Covers |
| --- | --- |
| [`yt9215-embedded-cpu.md`](research/yt9215-embedded-cpu.md) | The RISC-V CPU inside the YT9215 |
| [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) | JTAG pins of the YT9215 variants |
| [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) | SPI flash pins of the YT9215 variants |
| [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) | UART pins of the YT9215 variants |
| [`yt9215-registers/`](research/yt9215-registers/README.md) | YT921x switch programmer's guide with register reference |
| [`yt9215-registers/`](research/yt9215-registers/README.md) | YT921x register bindings for C, Rust, MicroPython and Zephyr |
| [`yt9215-boards.md`](research/yt9215-boards.md) | Boards and products that carry a YT9215 |
| [`lx-is601f-board/`](research/lx-is601f-board/README.md) | Annotated photos of a bought LX-IS601F V2.0 board |
| [`lx-is601f-board/`](research/lx-is601f-board/README.md) | Where the debug pins of its YT9215SCH come out |

The register guide and its bindings describe access from an external host. How that
carries over to firmware on the YT9215 CPU is an open question in
[`yt9215-embedded-cpu.md`](research/yt9215-embedded-cpu.md#packet-path).


### Archive

[`archive/`](archive/README.md) holds the notes that assume an external MCU, a switch IC
from another vendor, or no switch at all. They are not part of the current design. The
[archive index](archive/README.md) says what each one covers.

| Archived group | Index |
| --- | --- |
| Block diagram with a rough BOM | [Archived design](archive/README.md#archived-design) |
| Switch IC selection | [Archived research: switch ICs](archive/README.md#archived-research-switch-ics) |
| External MCU with its network link | [Archived research: external MCU](archive/README.md#archived-research-external-mcu) |
| Cost reduction | [Archived research: cost](archive/README.md#archived-research-cost) |

## Related repositories

* [mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0):
  mirror of an open-hardware 5-port gigabit switch built around the Motorcomm YT9215S
  (EasyEDA source, schematic, PCB, Gerbers, BOM). It is the reference design for the
  YT9215S notes here. The [`attachments/...`](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/tree/main/attachments) paths quoted in
  [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) refer to that repository;
  the same two files are also in [`datasheets/motorcomm/`](https://github.com/mithro/budget-poe-adapter/tree/main/datasheets/motorcomm).

## Licence

See [`LICENSE`](LICENSE). Vendor datasheets under [`datasheets/`](datasheets/) remain the property of
their vendors.
