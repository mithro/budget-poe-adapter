<!-- Root page of the documentation site: the README followed by the navigation.
     Each toctree mirrors one group of the "Documents" section of README.md, in the same
     order. Sphinx does not run the link rewriting of conf.py on the included README, so
     the README links to folders with full GitHub addresses. -->

```{include} README.md
```

```{toctree}
:hidden:
:caption: Design

design/block-diagram-and-bom
research/cost-reduction
```

```{toctree}
:hidden:
:caption: Power

research/poe
research/usb-c-pd
```

```{toctree}
:hidden:
:caption: Switch ICs

research/ethernet-switch
research/ethernet-switch-comparison
research/switch-detail-comparison
research/switch-embedded-cpu
research/switch-cpu-dev-boards
research/motorcomm-debug-pins
```

```{toctree}
:hidden:
:caption: Switch boards

research/switch-board-strapping
research/lx-is601f-board/README
research/lx-is601f-board/schematic/README
research/lx-is601f-board/photos/README
```

```{toctree}
:hidden:
:caption: YT921x switch programming

research/yt9215-registers/docs/index
research/yt9215-registers/README
```

```{toctree}
:hidden:
:caption: MCU and its network link

research/risc-v-mcu-comparison
research/gigabit-piggyback
research/bitbang-10mbit-ethernet
research/bitbang-usb
research/usb-network-card
```

```{toctree}
:hidden:
:caption: Datasheets

datasheets/README
```

