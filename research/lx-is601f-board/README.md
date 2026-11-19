# LX-IS601F V2.0 switch board: debug pins

Photos of two bought 5-port switch boards (silkscreen `LX-IS601F V2.0`) and annotated
images showing where the UART, SPI flash and JTAG pins of its switch IC come out.

The switch IC, [U4](../motorcomm-debug-pins.md#lx-u4), is a **YT9215SCH**. Its pinout differs from that of the YT9215S on the
open-hardware board mirrored at
[mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0).
The pin tables of both parts, and the route of each debug pin on this board, are in
[`../motorcomm-debug-pins.md`](../motorcomm-debug-pins.md#lx-is601f-v20-boards).

## Files

| File | Kind | Shows |
| --- | --- | --- |
| [`u4-pin-numbering-annotated.png`](u4-pin-numbering-annotated.png) | Annotated image | Pin 1 and the pin range of each side of [U4](../motorcomm-debug-pins.md#lx-u4) |
| [`u4-pins-top-edge-annotated.png`](u4-pins-top-edge-annotated.png) | Annotated image | Pins 65 to 96 of [U4](../motorcomm-debug-pins.md#lx-u4) and their vias |
| [`u4-pins-right-edge-annotated.png`](u4-pins-right-edge-annotated.png) | Annotated image | Pins 46 to 55 of [U4](../motorcomm-debug-pins.md#lx-u4) and the SPF0 resistors |
| [`photo-u4-macro.jpg`](photo-u4-macro.jpg) | Source photo | Close-up of [U4](../motorcomm-debug-pins.md#lx-u4) on board B, without a heatsink |
| [`photo-u4-wide.jpg`](photo-u4-wide.jpg) | Source photo | Wider view of [U4](../motorcomm-debug-pins.md#lx-u4) on board A |
| [`u4-surroundings.jpg`](u4-surroundings.jpg) | Cropped photo | [U4](../motorcomm-debug-pins.md#lx-u4) and the named parts beside it, from [`photo-u4-wide.jpg`](photo-u4-wide.jpg) |
| [`u4-corner-pins-65-71-photo-12.jpg`](u4-corner-pins-65-71-photo-12.jpg) | Cropped photo | Leads 65 to 71 of [U4](../motorcomm-debug-pins.md#lx-u4) on board B, at the full resolution of [photo 12](photos/README.md#photo-12) |
| [`u4-corner-pins-65-70-photo-13.jpg`](u4-corner-pins-65-70-photo-13.jpg) | Cropped photo | Leads 65 to 70 of [U4](../motorcomm-debug-pins.md#lx-u4) on board A, at the full resolution of [photo 13](photos/README.md#photo-13) |
| [`annotate.py`](annotate.py) | Script | Draws the annotations and makes the crop |
| [`photos/`](photos/README.md) | Photo catalogue | 34 photos of the two boards |

[`annotate.py`](annotate.py) needs Pillow and runs as `python3 annotate.py`. It draws on
crops of [`photo-u4-macro.jpg`](photo-u4-macro.jpg), one crop per image, so that the labels stay
readable at the width of this page.

## Annotated images

The pin table for these images, and the confidence of each pin, are in
[`../motorcomm-debug-pins.md`](../motorcomm-debug-pins.md#lx-is601f-v20-boards). The chip is a YT9215SCH, so the pin
numbers are those of the SC and SCH pinout. Names marked `*` are JTAG names from the
YT9215SC draft datasheet. Label colours: orange for UART, cyan for SPI flash, pink for
JTAG, yellow for straps, green for SCL and SDA, grey for clock and reset. The lilac rings
are the vias of pins 80 and 85, which are LED pins with no debug function.

### Pin numbering

![U4 with pin 1, the corner pin numbers and the pin range of each side marked](u4-pin-numbering-annotated.png)

### Top edge: pins 65 to 96

A ring with a number marks the via that the lead of that pin runs to.

![Top edge of U4 with the function of each debug pin and its via marked](u4-pins-top-edge-annotated.png)

### Right edge: pins 46 to 55

![Right edge of U4 with the SPF0 flash pins, their resistors and the UART0 pins marked](u4-pins-right-edge-annotated.png)

## Source photos

The three annotated images are crops of [`photo-u4-macro.jpg`](photo-u4-macro.jpg), a close-up of
[U4](../motorcomm-debug-pins.md#lx-u4) on board B, without a heatsink. Boards A and B are told apart in [`photos/README.md`](photos/README.md).

[`photo-u4-wide.jpg`](photo-u4-wide.jpg) shows board A, which has the same layout. The crop below keeps
[U4](../motorcomm-debug-pins.md#lx-u4) and the parts beside it whose silkscreen names the pin table uses:
[Y6](../motorcomm-debug-pins.md#lx-y6) and [R22](../motorcomm-debug-pins.md#lx-r22) above the chip, and
[R44](../motorcomm-debug-pins.md#lx-r44), [R89](../motorcomm-debug-pins.md#lx-r89),
[R92](../motorcomm-debug-pins.md#lx-r92) and [R93](../motorcomm-debug-pins.md#lx-r93) to its right.

![U4 on board A with Y6, R22 and R23 above it and R44, R89, R92 and R93 to its right](u4-surroundings.jpg)

All 34 photos of the two boards are catalogued in [`photos/README.md`](photos/README.md).

## How the pins were found

Pin numbers are from the [YT9215SCH datasheet V1.03](../../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf).
JTAG names are from the [YT9215SC Draft_07 datasheet](../../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf);
V1.03 does not list them, so JTAG is unconfirmed.

Pin 1 is the lead beside the small dimple on the package. Leads were counted from
there anticlockwise as seen from the top, 32 to a side, and checked against these landmarks:

| Landmark | Pin |
| --- | --- |
| Ground pour | 61 |
| Ground pour | 62 |
| Wide power trace | 58 |
| Wide power trace | 59 |
| Wide power trace | 68 |
| Wide power trace | 69 |
| Decoupling capacitor C25 | 82 |
| Crystal [Y6](../motorcomm-debug-pins.md#lx-y6) | [87](../motorcomm-debug-pins.md#sch-pin-87) |
| Crystal [Y6](../motorcomm-debug-pins.md#lx-y6) | [88](../motorcomm-debug-pins.md#sch-pin-88) |

### Pins with no trace

Pins [46](../motorcomm-debug-pins.md#sch-pin-46), [47](../motorcomm-debug-pins.md#sch-pin-47), [67](../motorcomm-debug-pins.md#sch-pin-67), [79](../motorcomm-debug-pins.md#sch-pin-79) and [90](../motorcomm-debug-pins.md#sch-pin-90) have no trace leaving the pad outward. The two crops below show this for pin 67 at the full resolution of the album photos: leads 65 and 66 sit on a copper pour, leads 68 to 71 each have a trace, and the pad of lead 67 between them has none.

![Leads 65 to 71 of U4 on board B, with no trace above lead 67](u4-corner-pins-65-71-photo-12.jpg)

![Leads 65 to 70 of U4 on board A, with no trace above lead 67](u4-corner-pins-65-70-photo-13.jpg)

A top-side photo shows only the copper outside the package. A trace that runs inward from a pad to a via under the package body is hidden, so these pins are not proven unconnected. A continuity check from each lead settles it.

Routing was traced from top-side photos only. Where the vias go on other layers, the
strap levels, and what the far pads of [R44](../motorcomm-debug-pins.md#lx-r44), [R89](../motorcomm-debug-pins.md#lx-r89), [R92](../motorcomm-debug-pins.md#lx-r92) and [R93](../motorcomm-debug-pins.md#lx-r93) connect to are unknown.

## Schematic

A reverse-engineered KiCad schematic of the whole board, with each connection marked confirmed, seen, inferred or unknown, is in [`schematic/`](schematic/). Its [README](schematic/README.md) lists what is known about the board and the measurements that would settle the rest.
