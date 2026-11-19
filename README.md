# Budget PoE to USB-C adapter

Notes, research and design material for an open source, non-isolated, very cheap and
flexible PoE to USB-C adapter that passes Ethernet through at 1 Gbit/s or faster.

The project is at the research stage. It has no schematic or PCB of the adapter.

## What is here

| Folder | Contents | Index |
| --- | --- | --- |
| [`design/`](design/) | Block diagram with a rough BOM | [Design](#design) |
| [`research/`](research/) | Research notes | [Research: power](#research-power) |
| [`research/`](research/) | Research notes | [Research: Motorcomm and Realtek switch ICs](#research-motorcomm-and-realtek-switch-ics) |
| [`research/`](research/) | Research notes | [Research: MCU and its network link](#research-mcu-and-its-network-link) |
| [`datasheets/`](datasheets/) | Switch IC documentation | [`datasheets/README.md`](datasheets/README.md) |

The research notes cover these topics:

| Topic | Section |
| --- | --- |
| PoE | [Research: power](#research-power) |
| USB-C PD | [Research: power](#research-power) |
| Switch ICs | [Research: Motorcomm and Realtek switch ICs](#research-motorcomm-and-realtek-switch-ics) |
| MCUs | [Research: MCU and its network link](#research-mcu-and-its-network-link) |
| Attaching an MCU to the network | [Research: MCU and its network link](#research-mcu-and-its-network-link) |

| Vendor | Datasheets in [`datasheets/`](datasheets/) |
| --- | --- |
| Motorcomm | Included |
| Realtek | Linked |

### Design

![Block diagram A, with a switch chip](design/block-diagram-with-switch.svg)

![Block diagram B, without a switch chip](design/block-diagram-without-switch.svg)

| File | Contents |
| --- | --- |
| [`block-diagram-and-bom.md`](design/block-diagram-and-bom.md) | Block diagram with rough BOM cost |
| [`block-diagram-with-switch.svg`](design/block-diagram-with-switch.svg) | Figure A as SVG |
| [`block-diagram-without-switch.svg`](design/block-diagram-without-switch.svg) | Figure B as SVG |
| [`block-diagram-with-switch.png`](design/block-diagram-with-switch.png) | Figure A as PNG |
| [`block-diagram-without-switch.png`](design/block-diagram-without-switch.png) | Figure B as PNG |
| [`make_block_diagram.py`](design/make_block_diagram.py) | Script that draws the SVG figures |
| [`svg_to_png.js`](design/svg_to_png.js) | Script that renders the PNG figures |
| [`bom-rough.csv`](design/bom-rough.csv) | BOM table |

### Research: power

| File | Covers |
| --- | --- |
| [`poe.md`](research/poe.md) | PoE for a cheap software-driven powered device |
| [`usb-c-pd.md`](research/usb-c-pd.md) | USB-C power standards |
| [`usb-c-pd.md`](research/usb-c-pd.md) | Raspberry Pi 5 requirements |
| [`usb-c-pd.md`](research/usb-c-pd.md) | PD negotiation at the electrical level |
| [`cost-reduction.md`](research/cost-reduction.md) | Cost reduction |
| [`cost-reduction.md`](research/cost-reduction.md) | Part-count reduction |

### Research: Motorcomm and Realtek switch ICs

| File | Covers |
| --- | --- |
| [`ethernet-switch.md`](research/ethernet-switch.md) | Cheap gigabit switch ICs with about three ports |
| [`ethernet-switch-comparison.md`](research/ethernet-switch-comparison.md) | Gigabit switch IC comparison table: price |
| [`ethernet-switch-comparison.md`](research/ethernet-switch-comparison.md) | Gigabit switch IC comparison table: stock |
| [`ethernet-switch-comparison.md`](research/ethernet-switch-comparison.md) | Gigabit switch IC comparison table: ports |
| [`ethernet-switch-comparison.md`](research/ethernet-switch-comparison.md) | Gigabit switch IC comparison table: management |
| [`switch-detail-comparison.md`](research/switch-detail-comparison.md) | Detail on the RTL8363NB (the pick) |
| [`switch-detail-comparison.md`](research/switch-detail-comparison.md) | Detail on the RTL8367S (a candidate) |
| [`switch-detail-comparison.md`](research/switch-detail-comparison.md) | Detail on the YT9215S (a candidate) |
| [`switch-embedded-cpu.md`](research/switch-embedded-cpu.md) | The DW8051 CPU inside the RTL8367S |
| [`switch-embedded-cpu.md`](research/switch-embedded-cpu.md) | The RISC-V CPU inside the YT9215S |
| [`switch-embedded-cpu.md`](research/switch-embedded-cpu.md) | The RTL8363NB, which has no CPU |
| [`switch-cpu-dev-boards.md`](research/switch-cpu-dev-boards.md) | Dev boards carrying the RTL8367S |
| [`switch-cpu-dev-boards.md`](research/switch-cpu-dev-boards.md) | Dev boards carrying the YT9215S |
| [`switch-cpu-dev-boards.md`](research/switch-cpu-dev-boards.md) | Off-the-shelf hardware carrying the RTL8367S |
| [`switch-cpu-dev-boards.md`](research/switch-cpu-dev-boards.md) | Off-the-shelf hardware carrying the YT9215S |
| [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) | JTAG pins of the YT9215 variants |
| [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) | SPI flash pins of the YT9215 variants |
| [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) | UART pins of the YT9215 variants |
| [`yt9215-registers/`](research/yt9215-registers/README.md) | YT921x switch programmer's guide with register reference |
| [`yt9215-registers/`](research/yt9215-registers/README.md) | YT921x register bindings for C, Rust, MicroPython and Zephyr |
| [`lx-is601f-board/`](research/lx-is601f-board/README.md) | Annotated photos of a bought LX-IS601F V2.0 board |
| [`lx-is601f-board/`](research/lx-is601f-board/README.md) | Where the debug pins of its YT9215SCH come out |
| [`gigabit-piggyback.md`](research/gigabit-piggyback.md) | Piggybacking a small device on a gigabit Ethernet link |

### Research: MCU and its network link

| File | Covers |
| --- | --- |
| [`risc-v-mcu-comparison.md`](research/risc-v-mcu-comparison.md) | MCU comparison |
| [`bitbang-10mbit-ethernet.md`](research/bitbang-10mbit-ethernet.md) | Bit-banging 10 Mbit/s Ethernet |
| [`bitbang-usb.md`](research/bitbang-usb.md) | Bit-banged (software) USB device |
| [`usb-network-card.md`](research/usb-network-card.md) | The adapter as a CDC-ECM USB network card |
| [`usb-network-card.md`](research/usb-network-card.md) | The adapter as an NCM USB network card |
| [`usb-network-card.md`](research/usb-network-card.md) | The adapter as an RNDIS USB network card |

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
