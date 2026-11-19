# Budget PoE to USB-C adapter

Notes and research for an open source, non-isolated, very cheap and
flexible PoE to USB-C adapter that passes Ethernet through at 1 Gbit/s or faster.

The design uses only the Motorcomm YT9215 switch IC and its internal RISC-V CPU. The
adapter's firmware runs on that CPU, and there is no external MCU and no other switch IC.

The project is at the research stage. It has no schematic or PCB of the adapter.

| Resource | Location |
| --- | --- |
| Rendered documentation | [budget-poe-adapter.readthedocs.io](https://budget-poe-adapter.readthedocs.io/en/latest/) |
| Source repository | [GitHub repository](https://github.com/mithro/budget-poe-adapter) |

## Documents

The documents are grouped by the question they answer. Each group is listed in reading order.
The [Archive](#archive) group comes last and holds the notes that are not part of the current design.

| Group | Question it answers |
| --- | --- |
| [YT9215 switch IC](#yt9215-switch-ic) | What is known about the YT9215 and the CPU inside it? |
| [Switch boards](#switch-boards) | How are the two YT9215 switch boards built? |
| [YT921x switch programming](#yt921x-switch-programming) | How is a YT921x switch programmed? |
| [Power](#power) | How does the adapter take PoE power and hand it on over USB-C? |
| [Datasheets](#datasheets) | Where are the vendor documents? |
| [Archive](#archive) | Which notes assume a design other than the current one? |

### YT9215 switch IC

| Document | Covers |
| --- | --- |
| [The RISC-V CPU inside the YT9215](research/yt9215-embedded-cpu.md) | What is publicly known about the CPU that runs the adapter firmware |
| [Motorcomm debug pins](research/motorcomm-debug-pins.md) | Debug pins of the YT9215 variants with their routes on the LX-IS601F board |
| [Boards and products that carry a YT9215](research/yt9215-boards.md) | Hardware on which the YT9215 can be studied |

### Switch boards

| Document | Covers |
| --- | --- |
| [Switch boards: strapping and major components](research/switch-board-strapping.md) | Strap settings with the major components of both boards |
| [LX-IS601F V2.0 switch board](research/lx-is601f-board/README.md) | Annotated photos of the debug pins and the strap resistors |
| [LX-IS601F schematic](research/lx-is601f-board/schematic/README.md) | Reverse-engineered KiCad schematic of the board |
| [LX-IS601F photo catalogue](research/lx-is601f-board/photos/README.md) | 34 photos of two LX-IS601F boards |

### YT921x switch programming

The guide and its bindings describe register access from an external host. How that carries
over to firmware on the YT9215 CPU is an open question in
[The RISC-V CPU inside the YT9215](research/yt9215-embedded-cpu.md#packet-path).

| Document | Covers |
| --- | --- |
| [YT921x switch programmer's guide](research/yt9215-registers/docs/index.rst) | Manual for writing a YT921x driver with a register reference |
| [YT921x source files and build commands](research/yt9215-registers/README.md) | The files behind the manual with the commands that check them |

### Power

| Document | Covers |
| --- | --- |
| [PoE powered device](research/poe.md) | PoE standards and negotiation for a software-driven powered device |
| [USB-C power](research/usb-c-pd.md) | USB-C power standards with PD negotiation for a source that feeds a Raspberry Pi 5 |

### Datasheets

| Document | Covers |
| --- | --- |
| [Datasheets](datasheets/README.md) | Vendor documents of the switch ICs and of the parts on the two switch boards |

### Archive

These notes assume an external MCU, a switch IC from another vendor, or no switch at all.
Each one opens with a statement of the design it assumes.

| Document | Covers |
| --- | --- |
| [Archive index](archive/README.md) | Index of the archived notes with the design each one assumes |
| [Block diagram and rough BOM](archive/design/block-diagram-and-bom.md) | Blocks of an adapter with an external MCU with their rough cost |
| [Cheap gigabit switch ICs](archive/research/ethernet-switch.md) | Survey of cheap gigabit switch ICs with about three ports |
| [Switch IC comparison table](archive/research/ethernet-switch-comparison.md) | The surveyed switch ICs side by side |
| [Switch ICs in detail](archive/research/switch-detail-comparison.md) | The RTL8363NB compared with the RTL8367S and the YT9215S |
| [Embedded CPUs in the switch ICs](archive/research/switch-embedded-cpu.md) | Whether the CPU inside a switch IC can replace an external MCU |
| [Switch IC dev boards](archive/research/switch-cpu-dev-boards.md) | Hardware to buy that carries an RTL8367S or a YT9215S |
| [MCU comparison](archive/research/risc-v-mcu-comparison.md) | Candidate external MCUs with their price and features |
| [Piggybacking on a gigabit link](archive/research/gigabit-piggyback.md) | Ways to attach a small device to a gigabit Ethernet link |
| [Bit-banged 10 Mbit/s Ethernet](archive/research/bitbang-10mbit-ethernet.md) | Whether an MCU can bit-bang 10 Mbit/s Ethernet |
| [Bit-banged USB](archive/research/bitbang-usb.md) | Whether an MCU can bit-bang a USB device |
| [USB network card](archive/research/usb-network-card.md) | The adapter presenting itself to the host as a USB network card |
| [Cost and part-count reduction](archive/research/cost-reduction.md) | Ways to cut the cost and the part count of the archived design |

## Repository layout

| Folder | Contents |
| --- | --- |
| [`research/`](https://github.com/mithro/budget-poe-adapter/tree/main/research) | Research notes of the current design |
| [`research/lx-is601f-board/`](https://github.com/mithro/budget-poe-adapter/tree/main/research/lx-is601f-board) | Photos and schematic of the LX-IS601F switch board |
| [`research/yt9215-registers/`](https://github.com/mithro/budget-poe-adapter/tree/main/research/yt9215-registers) | YT921x manual with register description and bindings |
| [`datasheets/`](https://github.com/mithro/budget-poe-adapter/tree/main/datasheets) | Vendor documents of the switch ICs and the board parts |
| [`archive/`](https://github.com/mithro/budget-poe-adapter/tree/main/archive) | Notes that are not part of the current design |

[`conf.py`](https://github.com/mithro/budget-poe-adapter/blob/main/conf.py) is the Sphinx configuration of the documentation site and
[`index.md`](https://github.com/mithro/budget-poe-adapter/blob/main/index.md) holds its navigation. The site shows this file as its
landing page, so links to folders here are full GitHub addresses.

## Related repositories

* [The wu-kou board repository](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0):
  mirror of an open-hardware 5-port gigabit switch built around the Motorcomm YT9215S
  (EasyEDA source, schematic, PCB, Gerbers, BOM). It is the reference design for the
  YT9215S notes here. [Datasheets](datasheets/README.md) lists the datasheets
  that are also attachments of that repository.

## Licence

See [`LICENSE`](https://github.com/mithro/budget-poe-adapter/blob/main/LICENSE). Vendor datasheets under [`datasheets/`](https://github.com/mithro/budget-poe-adapter/tree/main/datasheets) remain the property of
their vendors.
