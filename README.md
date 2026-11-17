# Budget PoE to USB-C adapter

Notes, research and design material for an open source, non-isolated, very cheap and
flexible PoE to USB-C adapter that passes Ethernet through at 1 Gbit/s or faster.

The project is at the research stage. There is no schematic or PCB here yet.

## What is here

| Folder | Contents |
| --- | --- |
| [`design/`](design/) | Block diagram and rough BOM |
| [`research/`](research/) | Research notes |
| [`datasheets/`](datasheets/) | Switch IC documentation |

The research notes cover PoE, USB-C PD, switch ICs, MCUs and how to attach an MCU
to the network. The datasheets folder includes the Motorcomm datasheets and links
to the Realtek ones; see [`datasheets/README.md`](datasheets/README.md).

### Design

| File | Topic |
| --- | --- |
| [`block-diagram-and-bom.md`](design/block-diagram-and-bom.md) | Block diagram and rough BOM cost |
| [`block-diagram.svg`](design/block-diagram.svg) / [`.png`](design/block-diagram.png) | Block diagram figure |
| [`bom-rough.csv`](design/bom-rough.csv) | BOM table |

### Research: power

| File | Topic |
| --- | --- |
| [`poe.md`](research/poe.md) | PoE for a cheap, software-driven PD |
| [`usb-c-pd.md`](research/usb-c-pd.md) | USB-C power, Pi 5 needs, PD negotiation |
| [`cost-reduction.md`](research/cost-reduction.md) | Cost and part-count reduction |

### Research: Motorcomm and Realtek switch ICs

| File | Topic |
| --- | --- |
| [`ethernet-switch.md`](research/ethernet-switch.md) | Cheap ~3-port gigabit switch ICs |
| [`ethernet-switch-comparison.md`](research/ethernet-switch-comparison.md) | Gigabit switch IC comparison table |
| [`switch-detail-comparison.md`](research/switch-detail-comparison.md) | RTL8363NB vs RTL8367S vs YT9215S in detail |
| [`switch-embedded-cpu.md`](research/switch-embedded-cpu.md) | CPUs inside the switch ICs |
| [`switch-cpu-dev-boards.md`](research/switch-cpu-dev-boards.md) | Dev boards and retail hardware |
| [`motorcomm-debug-pins.md`](research/motorcomm-debug-pins.md) | YT9215 JTAG, SPI flash and UART pins |
| [`lx-is601f-board/`](research/lx-is601f-board/) | Annotated photos of an LX-IS601F V2.0 board |
| [`gigabit-piggyback.md`](research/gigabit-piggyback.md) | Piggybacking on a gigabit link |

Notes on the files above:

* The comparison table covers price, stock, ports and management. The detail
  comparison treats the RTL8363NB as the pick and the RTL8367S and YT9215S as
  candidates.
* The embedded CPUs are the DW8051 in the RTL8367S and the RISC-V core in the
  YT9215S; the RTL8363NB has none. The dev-board note covers off-the-shelf
  hardware carrying the RTL8367S and YT9215S.
* The debug-pin note covers the YT9215 S, SC/SCH and RB variants. The LX-IS601F
  board is a bought board carrying a YT9215SCH; the photos show where the debug
  pins come out.
* The piggyback note is about attaching a small device to a gigabit Ethernet
  link.

### Research: MCU and its network link

| File | Topic |
| --- | --- |
| [`risc-v-mcu-comparison.md`](research/risc-v-mcu-comparison.md) | MCU comparison |
| [`bitbang-10mbit-ethernet.md`](research/bitbang-10mbit-ethernet.md) | Bit-banging 10 Mbit/s Ethernet |
| [`bitbang-usb.md`](research/bitbang-usb.md) | Bit-banged (software) USB device |
| [`usb-network-card.md`](research/usb-network-card.md) | The adapter as a USB network card |

The USB network card note covers CDC-ECM, NCM and RNDIS.

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
