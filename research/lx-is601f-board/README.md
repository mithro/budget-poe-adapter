# LX-IS601F V2.0 switch board

Photos of a bought PoE switch board (silkscreen `LX-IS601F V2.0`, four PoE ports, one uplink port and one SFP port), with annotated
images showing where the UART, SPI flash and JTAG pins of its switch IC come out and
where its strap resistors sit. The photos show two boards with the same layout, called board A and board B.

The switch IC, [U4](../switch-board-strapping.md#major-components), is a **YT9215SCH**. Its pinout differs from the YT9215S used on the
open-hardware board in
[the wu-kou board repository](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0);
the pin tables of both parts, and the route of each debug pin on this board, are in
[the LX-IS601F V2.0 boards section of `../motorcomm-debug-pins.md`](../motorcomm-debug-pins.md#lx-is601f-v20-boards).

| Image | File | Kind | Board | Side | Shows |
| --- | --- | --- | --- | --- | --- |
| <a href="#photo-debug-pins">Debug pins annotated</a> | [`lx-is601f-debug-pins-annotated.png`](lx-is601f-debug-pins-annotated.png) | Annotated image | B | Top | Debug pins of [U4](../switch-board-strapping.md#major-components) with a pin table |
| <a href="#photo-strap-array">Strap array annotated</a> | [`strap-resistors-annotated.jpg`](strap-resistors-annotated.jpg) | Annotated image | Not known | Bottom | Strap resistor array with decoded levels |
| <a href="#photo-u4-close-up">U4 close-up</a> | [`photo-u4-macro.jpg`](photo-u4-macro.jpg) | Source photo | B | Top | Close-up of [U4](../switch-board-strapping.md#major-components) with the heatsink removed |
| <a href="#photo-board-a-top">Board A top</a> | [`photo-u4-wide.jpg`](photo-u4-wide.jpg) | Source photo | A | Top | Area around [U4](../switch-board-strapping.md#major-components) |
| <a href="#photo-board-b-top">Board B top</a> | [`photo-board-b-top.jpg`](photo-board-b-top.jpg) | Source photo | B | Top | Whole board |
| <a href="#photo-bottom-under-u4">Bottom under U4</a> | [`photo-bottom-under-u4.jpg`](photo-bottom-under-u4.jpg) | Source photo | Not known | Bottom | Area under [U4](../switch-board-strapping.md#major-components) with the strap resistor array |
| <a href="#photo-poe-module">PoE module wide view</a> | [`photo-poe-module.jpg`](photo-poe-module.jpg) | Source photo | B | Top | Plug-in PoE module with the parts around it |
| <a href="#photo-poe-module-crop">PoE module</a> | [`crop-poe-module.jpg`](crop-poe-module.jpg) | Area crop | B | Top | Plug-in PoE module |
| <a href="#photo-board-b-power-input">Board B power input</a> | [`crop-board-b-power-input.jpg`](crop-board-b-power-input.jpg) | Area crop | B | Top | Power input parts |
| <a href="#photo-board-b-switch-ic">Board B switch IC</a> | [`crop-board-b-switch-ic.jpg`](crop-board-b-switch-ic.jpg) | Area crop | B | Top | [U4](../switch-board-strapping.md#major-components) with the parts beside it |
| <a href="#photo-board-b-magnetics">Board B magnetics</a> | [`crop-board-b-magnetics.jpg`](crop-board-b-magnetics.jpg) | Area crop | B | Top | Port magnetics with ESD arrays |
| <a href="#photo-board-a-regulator">Board A regulator</a> | [`crop-board-a-regulator.jpg`](crop-board-a-regulator.jpg) | Area crop | A | Top | Buck regulator |
| <a href="#photo-board-a-power-input">Board A power input</a> | [`crop-board-a-power-input.jpg`](crop-board-a-power-input.jpg) | Area crop | A | Top | Power input parts |
| <a href="#photo-board-a-led-esd">Board A LED and ESD arrays</a> | [`crop-board-a-led-esd.jpg`](crop-board-a-led-esd.jpg) | Area crop | A | Top | LED array with two ESD arrays |
| <a href="#photo-bottom-eeprom-flash">Bottom EEPROM and flash</a> | [`crop-bottom-eeprom-flash.jpg`](crop-bottom-eeprom-flash.jpg) | Area crop | Not known | Bottom | EEPROM with the flash footprint |
| <a href="#photo-u4-right-edge">U4 right edge</a> | [`crop-u4-right-edge.jpg`](crop-u4-right-edge.jpg) | Area crop | B | Top | Leads 33 to 64 of [U4](../switch-board-strapping.md#major-components) with their traces |
| None | [`photos/README.md`](photos/README.md) | Photo catalogue | Both | Both | 34 photos of the two boards |
| None | [`strap-resistors-source.jpg`](strap-resistors-source.jpg) | Source photo | Not known | Bottom | Strap resistor array without labels |
| None | [`annotate.py`](annotate.py) | Script | None | None | Draws the debug pin annotations |
| None | [`annotate_straps.py`](annotate_straps.py) | Script | None | None | Draws the strap resistor annotations |
| None | [`crop_photos.py`](crop_photos.py) | Script | None | None | Cuts the area crops out of the source photos |

Run [`annotate.py`](annotate.py) with `python3 annotate.py`; it needs Pillow and draws on
[`photo-u4-macro.jpg`](photo-u4-macro.jpg). Run [`annotate_straps.py`](annotate_straps.py) with `python3 annotate_straps.py`; it needs Pillow and the DejaVu Sans fonts, and draws on
[`strap-resistors-source.jpg`](strap-resistors-source.jpg). Run [`crop_photos.py`](crop_photos.py) with `python3 crop_photos.py`; it needs Pillow. The
strap resistors are explained in [`../switch-board-strapping.md`](../switch-board-strapping.md).

## Images

<a id="photo-debug-pins"></a>

**Debug pins annotated**

![Debug pins of U4 on board B with annotations](lx-is601f-debug-pins-annotated.png)

<a id="photo-strap-array"></a>

**Strap array annotated**

![Strap resistor array on the bottom side with the decoded levels](strap-resistors-annotated.jpg)

<a id="photo-u4-close-up"></a>

**U4 close-up**

![Close-up of U4 on board B](photo-u4-macro.jpg)

<a id="photo-board-a-top"></a>

**Board A top**

![Top side of board A around U4](photo-u4-wide.jpg)

<a id="photo-board-b-top"></a>

**Board B top**

![Top side of board B](photo-board-b-top.jpg)

<a id="photo-bottom-under-u4"></a>

**Bottom under U4**

![Bottom side under U4](photo-bottom-under-u4.jpg)

<a id="photo-poe-module"></a>

**PoE module wide view**

![PoE module on board B](photo-poe-module.jpg)

<a id="photo-poe-module-crop"></a>

**PoE module**

![PoE module on board B](crop-poe-module.jpg)

<a id="photo-board-b-power-input"></a>

**Board B power input**

![Power input area of board B](crop-board-b-power-input.jpg)

<a id="photo-board-b-switch-ic"></a>

**Board B switch IC**

![Switch IC area of board B](crop-board-b-switch-ic.jpg)

<a id="photo-board-b-magnetics"></a>

**Board B magnetics**

![Port magnetics area of board B](crop-board-b-magnetics.jpg)

<a id="photo-board-a-regulator"></a>

**Board A regulator**

![Buck regulator area of board A](crop-board-a-regulator.jpg)

<a id="photo-board-a-power-input"></a>

**Board A power input**

![Power input area of board A](crop-board-a-power-input.jpg)

<a id="photo-board-a-led-esd"></a>

**Board A LED and ESD arrays**

![LED and ESD array area of board A](crop-board-a-led-esd.jpg)

<a id="photo-bottom-eeprom-flash"></a>

**Bottom EEPROM and flash**

![EEPROM and flash footprint area on the bottom side](crop-bottom-eeprom-flash.jpg)

<a id="photo-u4-right-edge"></a>

**U4 right edge**

![Right edge of U4 on board B, pins 33 to 64](crop-u4-right-edge.jpg)

## How the debug pins are identified

* Pin numbers are from the [YT9215SCH datasheet V1.03](../../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf). JTAG names are from
  the [YT9215SC Draft_07 datasheet, page 22](../../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf#page=22); the V1.03 datasheet does not list them, so
  JTAG is unconfirmed.
* Pin 1 is the lead beside the small dimple on the package. Leads are counted from
  there, 32 per side, in the <a href="#photo-u4-close-up">U4 close-up</a> and <a href="#photo-board-a-top">Board A top</a> images, and checked against features whose pins are known from
  [Table 1 of the datasheet, pages 17 to 19](../../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=17): the ground pour on pins 61 and 62, the wide power
  traces on pins 58, 59, 68 and 69, the decoupling capacitor on pin 82, and the crystal [Y6](../motorcomm-debug-pins.md#parts-beside-u4) on pins 87 and 88.
* Routing is traced from the <a href="#photo-u4-close-up">U4 close-up</a> and <a href="#photo-board-a-top">Board A top</a> images only. Where the vias go on other layers is not known. What the far pads of
  [R44](../switch-board-strapping.md#other-configuration-pins), [R89](../switch-board-strapping.md#other-configuration-pins), [R92](../switch-board-strapping.md#other-configuration-pins) and [R93](../switch-board-strapping.md#other-configuration-pins) connect to is not known either. The strap levels are worked out in
  [`../switch-board-strapping.md`](../switch-board-strapping.md).

## Schematic

A reverse-engineered KiCad schematic of the whole board is described in [`schematic/README.md`](schematic/README.md). It marks
each connection as confirmed, seen, inferred or unknown, and lists the measurements that would settle the open ones.
