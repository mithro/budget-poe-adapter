# LX-IS601F V2.0 switch board: debug pins

Photos of a bought 5-port switch board (silkscreen `LX-IS601F V2.0`) and an annotated
image showing where the UART, SPI flash and JTAG pins of its switch IC come out.

The switch IC is a **YT9215SCH**. Its pinout differs from the YT9215S used on the
open-hardware board mirrored at
[mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0);
see [`../motorcomm-debug-pins.md`](../motorcomm-debug-pins.md).

| File | Kind | Shows | Also shows | Needs |
| --- | --- | --- | --- | --- |
| [`lx-is601f-debug-pins-annotated.png`](lx-is601f-debug-pins-annotated.png) | Annotated image | Pin table | Notes on confidence | – |
| [`photo-u4-macro.jpg`](photo-u4-macro.jpg) | Source photo | Close-up of U4 | Heatsink removed | – |
| [`photo-u4-wide.jpg`](photo-u4-wide.jpg) | Source photo | Wider view of a second board | Same layout | – |
| [`annotate.py`](annotate.py) | Script (`python3 annotate.py`) | Draws the annotations | – | Pillow |

![Annotated debug pins](lx-is601f-debug-pins-annotated.png)

## How the pins were found

* Pin numbers are from the YT9215SCH datasheet V1.03 (2025-02-10). JTAG names are from
  the YT9215SC Draft_07 datasheet (2023); the 2025 datasheet no longer lists them, so
  JTAG is unconfirmed.
* Pin 1 is the lead beside the small dimple on the package. Leads were counted from
  there, 32 per side, and checked against the ground pour (61/62), the wide power traces
  (58/59, 68/69), the decoupling capacitor on pin 82 and the crystal.
* Routing was traced from top-side photos only. Where the vias go on other layers, the
  strap levels, and what the far pads of R44/R89/R92/R93 connect to are not known.
