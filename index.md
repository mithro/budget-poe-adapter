<!-- Root page of the documentation site: the README followed by the navigation.
     Each toctree mirrors one group of the "Documents" section of README.md, in the same
     order. Sphinx does not run the link rewriting of conf.py on the included README, so
     the README links to folders with full GitHub addresses. -->

```{include} README.md
```

```{toctree}
:hidden:
:caption: Power

research/poe
research/usb-c-pd
```

```{toctree}
:hidden:
:caption: YT9215 switch IC

research/yt9215-embedded-cpu
research/motorcomm-debug-pins
research/yt9215-boards
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
:caption: Datasheets

datasheets/README
```

```{toctree}
:hidden:
:caption: Archive

archive/README
archive/design/block-diagram-and-bom
archive/research/ethernet-switch
archive/research/ethernet-switch-comparison
archive/research/switch-detail-comparison
archive/research/switch-embedded-cpu
archive/research/switch-cpu-dev-boards
archive/research/risc-v-mcu-comparison
archive/research/gigabit-piggyback
archive/research/bitbang-10mbit-ethernet
archive/research/bitbang-usb
archive/research/usb-network-card
archive/research/cost-reduction
```

