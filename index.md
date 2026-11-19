% Root page of the documentation site: the README followed by the navigation.
% Each toctree mirrors one group of the "Documents" section of README.md.

```{include} README.md
```

```{toctree}
:hidden:
:caption: Design

Block diagram and rough BOM <design/block-diagram-and-bom>
Cost and part-count reduction <research/cost-reduction>
```

```{toctree}
:hidden:
:caption: Power

PoE powered device <research/poe>
USB-C power <research/usb-c-pd>
```

```{toctree}
:hidden:
:caption: Switch ICs

Cheap gigabit switch ICs <research/ethernet-switch>
Switch IC comparison table <research/ethernet-switch-comparison>
Switch ICs in detail <research/switch-detail-comparison>
Embedded CPUs in the switch ICs <research/switch-embedded-cpu>
Switch IC dev boards <research/switch-cpu-dev-boards>
Motorcomm debug pins <research/motorcomm-debug-pins>
```

```{toctree}
:hidden:
:caption: MCU and its network link

MCU comparison <research/risc-v-mcu-comparison>
Piggybacking on a gigabit link <research/gigabit-piggyback>
Bit-banged 10 Mbit/s Ethernet <research/bitbang-10mbit-ethernet>
Bit-banged USB <research/bitbang-usb>
USB network card <research/usb-network-card>
```

```{toctree}
:hidden:
:caption: LX-IS601F switch board

Debug pins on the board <research/lx-is601f-board/README>
Reverse-engineered schematic <research/lx-is601f-board/schematic/README>
Photo catalogue <research/lx-is601f-board/photos/README>
```

```{toctree}
:hidden:
:caption: YT921x switch programming

Programmer's guide <research/yt9215-registers/docs/index>
Register description and bindings <research/yt9215-registers/README>
```

```{toctree}
:hidden:
:caption: Datasheets

Switch IC documentation <datasheets/README>
```

