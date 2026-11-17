# Budget PoE to USB-C adapter

Notes, research and design material for an open source, non-isolated, very cheap and
flexible PoE to USB-C adapter that passes Ethernet through at 1 Gbit/s or faster.

The project is at the research stage. There is no schematic or PCB here yet.

## What is here

| Folder | Contents | Details |
| --- | --- | --- |
| [`design/`](design/) | Block diagram and rough BOM | The current concept |
| [`research/`](research/) | Research notes | PoE, USB-C PD, switch ICs, MCUs, MCU network attachment |
| [`datasheets/`](datasheets/) | Switch IC documentation | Motorcomm included, Realtek linked ([index](datasheets/README.md)) |

### Design

| File | Topic |
| --- | --- |
| [`block-diagram-and-bom.md`](design/block-diagram-and-bom.md) | Block diagram and rough BOM cost |
| [`block-diagram.svg`](design/block-diagram.svg) / [`.png`](design/block-diagram.png) | Figure |
| [`bom-rough.csv`](design/bom-rough.csv) | BOM table |

### Research: power

| File | Topic | Covers |
| --- | --- | --- |
| [`poe.md`](research/poe.md) | PoE for a cheap, software-driven powered device | – |
| [`usb-c-pd.md`](research/usb-c-pd.md) | USB-C power and PD negotiation | Power standards, Raspberry Pi 5 requirements |
| [`usb-c-pd.md`](research/usb-c-pd.md) | (same file) | PD negotiation at the electrical level |
| [`cost-reduction.md`](research/cost-reduction.md) | Cost and part-count reduction | – |

### Research: Motorcomm and Realtek switch ICs

| File | Topic | Covers |
| --- | --- | --- |
| [`ethernet-switch.md`](research/ethernet-switch.md) | Cheap ~3-port gigabit switch ICs | – |
| [`ethernet-switch-comparison.md`](research/ethernet-switch-comparison.md) | Gigabit switch IC comparison table | Price, stock, ports, management |
| [`switch-detail-comparison.md`](research/switch-detail-comparison.md) | Detail on the pick versus the candidates | RTL8363NB (pick); RTL8367S, YT9215S (candidates) |
| [`switch-embedded-cpu.md`](research/switch-embedded-cpu.md) | The CPUs inside the switch ICs | RTL8367S (DW8051), YT9215S (RISC-V), RTL8363NB (none) |
| [`switch-cpu-dev-boards.md`](research/switch-cpu-dev-boards.md) | Dev boards and off-the-shelf hardware | Carrying the RTL8367S and YT9215S |
| [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) | JTAG, SPI flash and UART pins | YT9215 S, SC/SCH and RB variants |
| [`lx-is601f-board/`](research/lx-is601f-board/) | Annotated photos of a bought board | LX-IS601F V2.0 (YT9215SCH); where the debug pins come out |
| [`gigabit-piggyback.md`](research/gigabit-piggyback.md) | Piggybacking a small device on a gigabit Ethernet link | – |

### Research: MCU and its network link

| File | Topic | Covers |
| --- | --- | --- |
| [`risc-v-mcu-comparison.md`](research/risc-v-mcu-comparison.md) | MCU comparison | – |
| [`bitbang-10mbit-ethernet.md`](research/bitbang-10mbit-ethernet.md) | Bit-banging 10 Mbit/s Ethernet | – |
| [`bitbang-usb.md`](research/bitbang-usb.md) | Bit-banged (software) USB device | – |
| [`usb-network-card.md`](research/usb-network-card.md) | The adapter as a USB network card | CDC-ECM / NCM / RNDIS |

## Related repositories

* [mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0):
  mirror of an open-hardware 5-port gigabit switch built around the Motorcomm YT9215S
  (EasyEDA source, schematic, PCB, Gerbers, BOM). It is the reference design for the
  YT9215S notes here. The `attachments/...` paths quoted in
  [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) refer to that repository;
  the same two files are also in [`datasheets/motorcomm/`](datasheets/motorcomm/).

## Licence

See [`LICENSE`](LICENSE). Vendor datasheets under `datasheets/` remain the property of
their vendors.
