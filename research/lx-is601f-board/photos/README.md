# LX-IS601F V2.0 photo catalogue

Photos of two `LX-IS601F V2.0` PoE switch boards, taken on 2026-11-17 with a
Pixel 7 Pro. The originals (3072 x 4080) are in the
[Google Photos album](https://photos.app.goo.gl/f4gAaRwkkgGWYLGu9), and photo numbers
follow the album order. This folder holds three kinds of copy:

| Folder | Copy |
| --- | --- |
| [`web/`](web/) | Resized to 1600 px |
| [`thumbs/`](thumbs/) | 240 px thumbnail |
| [`annotated/`](annotated/) | Callout image |

Every copy is rotated to one orientation and cropped to the board, and carries no EXIF
data (so no GPS position).

| Side | Photos | RJ45 block | Other landmarks |
| --- | --- | --- | --- |
| Top | 01-23 and 30-34 | On the left | `LX-IS601F V2.0` silkscreen readable at the bottom right |
| Bottom | 24-29 | On the right | Top edge of the board at the top |

On the top side J2 and the blue disc parts RV1-RV3 run along the top edge. The bottom
side is shown as if the board were flipped left-to-right; the RJ45 pin rows, the six
pins of RV1-RV3 and the J2 pads fix that orientation.

In a callout image a box outlines each part, so the marking inside it stays readable,
and a numbered badge beside the box or in the margin refers to the legend.

## The two boards

Both boards carry the same `LX-IS601F V2.0` PCB and a Motorcomm **YT9215SCH** as U4.
They differ in what is fitted:

| Feature | Board A | Board B |
| --- | --- | --- |
| U4 lot line 2 | `VKTP18287` | `VKJC09324` |
| U4 lot line 3 | `3200111C` | `2500211C` |
| U4 lot line 4 | `3AU2612M0` | `3AW4849M0` |
| Magnetics date | `2632` | `2523A` |
| PoE PSE module | Not fitted | Fitted |
| SFP cage | Not fitted | Fitted |
| U4 heatsink | Fitted | Not seen |
| C4 marking | `YX 47 63V` | `22 63V MB` |
| C4 value | 47 µF | 22 µF |
| TC1 marking | `YX 220 16V` | `220 16V MB` |

Board A is the non-PoE build: the 8-hole header for the PoE module is empty and U12
has only the SFP host connector, without its cage. Board B is the PoE build, with the
PSE daughterboard plugged into that header and the SFP cage fitted over U12.

Board A is in photos 01 to 06, 13 to 23 and 33. Board B is in photos 07 to 12, 30 to 32
and 34. The bottom-side photos (24 to 29) show nothing that ties them to one board.

### Parts on both boards

| Ref | Part | Side | Package | Marking line 1 | Marking line 2 | Value |
| --- | --- | --- | --- | --- | --- | --- |
| DXFRM2-DXFRM6 | Magnetics | Top | SMD 24-pin | `United-tek` | `G2401PR` | |
| ED1-ED10 | ESD array | Top | SOT-23-6 | `05U` | | |
| Y6 | Crystal | Top | SMD 4-pad | `25.000` | `MHz` | 25 MHz |
| PU1 | SCT2622 buck regulator | Top | ESOP-8 | `2622` | `SCT 6DC` | 3.3 V out |
| PL3 | Buck inductor | Top | SMD | `100` | | 10 µH |
| L3 | Inductor | Top | SMD | `4R7` | | 4.7 µH |
| D40 | Buck diode | Top | SMA | `LGE` | `SS510` | |
| D4 | Diode | Top | SMA | `LGE` | `SS510` | |
| D5 | Diode | Top | SMA | `LGE` | `SS510` | |
| L2 | Input inductor | Top | SMD | `701` | | |
| RV1-RV3 | Blue disc part | Top | THT radial | | | |
| C4 | Input capacitor | Top | Polymer can | | | |
| TC1 | 3.3 V output capacitor | Top | Polymer can | | | 220 µF |
| PR1 | Resistor | Top | SMD | `86C` | | |
| PR3 | Resistor | Top | SMD | `304` | | |
| J2 | Power input connector | Top | THT 2-pin | | | |
| U10 | I²C EEPROM | Bottom | SOIC-8 | `HK 24C08` | `2S3746HA` | 8 Kbit |
| U6 | Unpopulated footprint | Bottom | 8-pin | | | |
| D6 | Port diode | Bottom | SMB | `CP06C` | | |
| D8-D18 | Port diode | Bottom | SMB | `CP06C` | | |

PU1 carries a third marking line, `2U650`. J2's silkscreen name is `POWER2`. The
marking of C4 and TC1, and the value of C4, differ between the boards and are in
[the first table](#the-two-boards). RV1-RV3 are varistors or Y-capacitors; their
marking is not readable in any photo.

### Parts on the PoE PSE module

The module is fitted on board B only.

| Ref | Part | Package | Marking line 1 | Marking line 2 | Value |
| --- | --- | --- | --- | --- | --- |
| U1 | PSE controller, unidentified | QFN | `2184A` | `533AQ1H` | |
| D1 | Diode | SMB | `2616` | `RGS` | |
| D3 | Diode | SMB | `2616` | `RGS` | |
| D5 | Diode | SMB | `2616` | `RGS` | |
| D7 | Diode | SMB | `2616` | `RGS` | |
| R8 | Sense resistor | SMD | `R250` | | 0.25 Ω |
| R12 | Sense resistor | SMD | `R250` | | 0.25 Ω |
| R13 | Sense resistor | SMD | `R250` | | 0.25 Ω |
| R14 | Sense resistor | SMD | `R250` | | 0.25 Ω |
| R3 | Resistor | SMD | `330` | | 33 Ω |
| R9 | Resistor | SMD | `330` | | 33 Ω |
| R10 | Resistor | SMD | `330` | | 33 Ω |
| R11 | Resistor | SMD | `330` | | 33 Ω |
| PIN1 | Header to the mainboard | THT 8-pin | | | |

A fifth diode with the same marking sits at the top right of the module; its reference
is not visible.

## Catalogue

Each number links to that photo's notes, which show the 1600 px copy. The parts to
look for in each photo are listed under [Parts in each photo](#parts-in-each-photo).
"Callout" marks photos with a callout image in their notes. Times are the camera's
local time.

| # | Preview | Board | Side | Area | Framing | Angle | U4 marking | Callout | Time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [01](#photo-01) | <img src="thumbs/01.jpg" width="120"> | A | Top | Whole board | Wide | Straight | Heatsink |  | 09:23 |
| [02](#photo-02) | <img src="thumbs/02.jpg" width="120"> | A | Top | Whole board | Wide | Straight | Heatsink |  | 09:24 |
| [03](#photo-03) | <img src="thumbs/03.jpg" width="120"> | A | Top | Whole board | Wide | Angled | Heatsink |  | 09:24 |
| [04](#photo-04) | <img src="thumbs/04.jpg" width="120"> | A | Top | Whole board | Wide | Straight | Too small | Yes | 09:48 |
| [05](#photo-05) | <img src="thumbs/05.jpg" width="120"> | A | Top | Whole board | Wide | Angled | Readable |  | 09:48 |
| [06](#photo-06) | <img src="thumbs/06.jpg" width="120"> | A | Top | U4 | Close | Straight | Readable | Yes | 09:48 |
| [07](#photo-07) | <img src="thumbs/07.jpg" width="120"> | B | Top | U4 | Close | Straight | Readable |  | 09:48 |
| [08](#photo-08) | <img src="thumbs/08.jpg" width="120"> | B | Top | Whole board | Wide | Straight | Readable | Yes | 09:48 |
| [09](#photo-09) | <img src="thumbs/09.jpg" width="120"> | B | Top | U4 | Close | Straight | Glare |  | 09:49 |
| [10](#photo-10) | <img src="thumbs/10.jpg" width="120"> | B | Top | U4 left edge | Macro | Straight | Not in shot |  | 09:49 |
| [11](#photo-11) | <img src="thumbs/11.jpg" width="120"> | B | Top | U4 left edge | Macro | Straight | Not in shot |  | 09:49 |
| [12](#photo-12) | <img src="thumbs/12.jpg" width="120"> | B | Top | U4 | Close | Straight | Readable |  | 09:49 |
| [13](#photo-13) | <img src="thumbs/13.jpg" width="120"> | A | Top | U4 | Close | Straight | Readable |  | 09:49 |
| [14](#photo-14) | <img src="thumbs/14.jpg" width="120"> | A | Top | Power section | Close | Angled | Glare |  | 09:50 |
| [15](#photo-15) | <img src="thumbs/15.jpg" width="120"> | A | Top | Power section | Close | Angled | Glare |  | 09:50 |
| [16](#photo-16) | <img src="thumbs/16.jpg" width="120"> | A | Top | Centre | Wide | Straight | Readable |  | 09:50 |
| [17](#photo-17) | <img src="thumbs/17.jpg" width="120"> | A | Top | Centre | Wide | Angled | Readable |  | 09:50 |
| [18](#photo-18) | <img src="thumbs/18.jpg" width="120"> | A | Top | Centre | Wide | Angled | Readable |  | 09:50 |
| [19](#photo-19) | <img src="thumbs/19.jpg" width="120"> | A | Top | Power corner | Close | Straight | Not in shot |  | 13:41 |
| [20](#photo-20) | <img src="thumbs/20.jpg" width="120"> | A | Top | U4 | Close | Straight | Readable |  | 13:41 |
| [21](#photo-21) | <img src="thumbs/21.jpg" width="120"> | A | Top | Port edge | Close | Angled | Not in shot | Yes | 13:41 |
| [22](#photo-22) | <img src="thumbs/22.jpg" width="120"> | A | Top | Port edge | Close | Angled | Not in shot |  | 13:41 |
| [23](#photo-23) | <img src="thumbs/23.jpg" width="120"> | A | Top | U4 | Close | Straight | Readable |  | 13:42 |
| [24](#photo-24) | <img src="thumbs/24.jpg" width="120"> | Unknown | Bottom | RJ45 pins | Close | Angled |  |  | 13:42 |
| [25](#photo-25) | <img src="thumbs/25.jpg" width="120"> | Unknown | Bottom | RJ45 pins | Close | Angled |  |  | 13:42 |
| [26](#photo-26) | <img src="thumbs/26.jpg" width="120"> | Unknown | Bottom | Under U4 | Close | Straight |  | Yes | 13:42 |
| [27](#photo-27) | <img src="thumbs/27.jpg" width="120"> | Unknown | Bottom | Under U4 | Close | Angled |  |  | 13:42 |
| [28](#photo-28) | <img src="thumbs/28.jpg" width="120"> | Unknown | Bottom | Under U4 | Close | Angled |  |  | 13:42 |
| [29](#photo-29) | <img src="thumbs/29.jpg" width="120"> | Unknown | Bottom | U10 | Macro | Straight |  |  | 13:43 |
| [30](#photo-30) | <img src="thumbs/30.jpg" width="120"> | B | Top | PoE module | Close | Straight | Not in shot |  | 13:43 |
| [31](#photo-31) | <img src="thumbs/31.jpg" width="120"> | B | Top | PoE module | Close | Angled | Not in shot |  | 13:43 |
| [32](#photo-32) | <img src="thumbs/32.jpg" width="120"> | B | Top | PoE module | Macro | Straight | Not in shot | Yes | 13:43 |
| [33](#photo-33) | <img src="thumbs/33.jpg" width="120"> | A | Top | Uplink corner | Close | Straight | Not in shot |  | 13:43 |
| [34](#photo-34) | <img src="thumbs/34.jpg" width="120"> | B | Top | Uplink corner | Close | Straight | Not in shot |  | 13:44 |

## Parts in each photo

| Photo | Part to look for |
| --- | --- |
| [01](#photo-01) | Heatsink on U4 |
| [02](#photo-02) | Heatsink on U4 |
| [03](#photo-03) | Heatsink on U4 |
| [04](#photo-04) | U4 without heatsink |
| [04](#photo-04) | U12 SFP connector |
| [05](#photo-05) | U4 without heatsink |
| [06](#photo-06) | U4 marking |
| [06](#photo-06) | Y6 |
| [06](#photo-06) | R44 |
| [06](#photo-06) | R89 |
| [06](#photo-06) | R92 |
| [06](#photo-06) | R93 |
| [07](#photo-07) | U4 marking |
| [07](#photo-07) | PoE module U1 |
| [08](#photo-08) | PoE module |
| [08](#photo-08) | SFP cage |
| [09](#photo-09) | U4 in glare |
| [10](#photo-10) | Y6 |
| [10](#photo-10) | R250 sense resistors |
| [10](#photo-10) | ESD arrays |
| [11](#photo-11) | Y6 |
| [11](#photo-11) | R250 sense resistors |
| [11](#photo-11) | ESD arrays |
| [12](#photo-12) | U4 marking |
| [12](#photo-12) | PoE module U1 |
| [13](#photo-13) | U4 marking |
| [13](#photo-13) | ESD arrays |
| [14](#photo-14) | PU1 |
| [14](#photo-14) | PL3 |
| [14](#photo-14) | C4 |
| [15](#photo-15) | PU1 |
| [15](#photo-15) | PL3 |
| [15](#photo-15) | C4 |
| [16](#photo-16) | U4 |
| [16](#photo-16) | Magnetics |
| [16](#photo-16) | TC1 |
| [17](#photo-17) | U4 |
| [17](#photo-17) | Magnetics |
| [17](#photo-17) | TC1 |
| [18](#photo-18) | U4 |
| [18](#photo-18) | Magnetics |
| [18](#photo-18) | TC1 |
| [19](#photo-19) | PU1 |
| [19](#photo-19) | C4 |
| [19](#photo-19) | L2 |
| [20](#photo-20) | U4 marking |
| [20](#photo-20) | DXFRM6 |
| [21](#photo-21) | Empty PoE module header |
| [21](#photo-21) | LED resistor pads |
| [22](#photo-22) | LED6 footprint |
| [22](#photo-22) | LED7 |
| [22](#photo-22) | LED8 |
| [22](#photo-22) | R68 |
| [23](#photo-23) | U4 |
| [23](#photo-23) | Y6 |
| [23](#photo-23) | L2 |
| [24](#photo-24) | D19 |
| [24](#photo-24) | D21 |
| [24](#photo-24) | C69 |
| [24](#photo-24) | C73 |
| [25](#photo-25) | Port diode D8 |
| [25](#photo-25) | Port diodes D10-D14 |
| [26](#photo-26) | U6 footprint |
| [26](#photo-26) | U10 |
| [27](#photo-27) | U10 |
| [27](#photo-27) | Port diodes D6-D12 |
| [27](#photo-27) | Port diodes D16-D18 |
| [28](#photo-28) | U10 |
| [29](#photo-29) | U10 marking |
| [30](#photo-30) | PoE module U1 |
| [30](#photo-30) | R250 sense resistors |
| [30](#photo-30) | Diode D1 |
| [30](#photo-30) | Diode D3 |
| [30](#photo-30) | Diode D5 |
| [30](#photo-30) | Diode D7 |
| [31](#photo-31) | Diode marking `RGS 2616` |
| [32](#photo-32) | PoE module U1 marking |
| [33](#photo-33) | `LX-IS601F V2.0` silkscreen |
| [33](#photo-33) | DXFRM6 date `2632` |
| [34](#photo-34) | `LX-IS601F V2.0` silkscreen |
| [34](#photo-34) | DXFRM6 date `2523A` |

## Notes per photo

### Photo 01

![Photo 01](web/01.jpg)

Board A, whole top side, with the heatsink on U4. The RJ45 block is on the left edge
(a long shielded block with a shorter, unidentified one below it), and a single RJ45
sits on the right edge. The PoE
module header beside the RJ45 block is empty. U12, at the bottom centre, is the SFP
host connector with no cage.

### Photo 02

![Photo 02](web/02.jpg)

Board A, same view as 01, shot square-on. Silkscreen `LX-IS601F V2.0` is at the bottom
right.

### Photo 03

![Photo 03](web/03.jpg)

Board A, same view as 02 at a slight angle.

### Photo 04

![Photo 04](web/04.jpg)

Board A with the heatsink removed from U4.

![Photo 04 with callouts](annotated/04.jpg)

### Photo 05

![Photo 05](web/05.jpg)

Board A at an angle, U4 bare. The whole U4 marking is readable.

### Photo 06

![Photo 06](web/06.jpg)

Board A, close-up of U4 and its neighbours. This is the best shot of the board A
marking: `MOTORCOMM`, `YT9215SCH`, `VKTP18287`, `3200111C`, `3AU2612M0` on five lines. Pin 1 is next to
the small dimple at the lower left (the large circle at the upper right is a mould
mark). R44, R89, R92 and R93 sit on U4's SPF0 SPI-flash lines (CS, SO, SI and SCK
in that order); see the [schematic notes](../schematic/README.md).

![Photo 06 with callouts](annotated/06.jpg)

### Photo 07

![Photo 07](web/07.jpg)

Board B, U4 with the corner of the PoE module at the top left. U4 reads
`MOTORCOMM`, `YT9215SCH`, `VKJC09324`, `2500211C`, `3AW4849M0` on five lines. The module's U1 is
visible, marked `2184A` over `533AQ1H`.

### Photo 08

![Photo 08](web/08.jpg)

Board B, whole top side. The PoE PSE module sits beside the RJ45 block, over the
DXFRM magnetics, and an SFP cage
covers U12 at the bottom left. Magnetics on this board are date-coded `2523A`.

![Photo 08 with callouts](annotated/08.jpg)

### Photo 09

![Photo 09](web/09.jpg)

Board B, U4 close-up with heavy glare; the marking cannot be read.

### Photo 10

![Photo 10](web/10.jpg)

Board B, macro of U4's left edge and the module's lower edge: Y6, the R250 sense
resistors (R8, R12) and the ESD arrays ED3-ED5. Slightly soft.

### Photo 11

![Photo 11](web/11.jpg)

Same framing as 10, a little sharper.

### Photo 12

![Photo 12](web/12.jpg)

Board B, U4 close-up with readable marking (same as 07) and the module's U1.

### Photo 13

![Photo 13](web/13.jpg)

Board A, U4 close-up from straight above. Marking is readable. ED1-ED9 and R2-R5,
R110-R114 near the crystal are clear.

### Photo 14

![Photo 14](web/14.jpg)

Board A, U4 and the power section at an angle. PU1 (an SCT2622 buck marked `2622`, `SCT 6DC`, `2U650`), PL3 `100`, D40 `SS510` and C4 (`YX 47 63V`) are in frame.

### Photo 15

![Photo 15](web/15.jpg)

Board A, same as 14 from a slightly different angle.

### Photo 16

![Photo 16](web/16.jpg)

Board A, wider view of the centre: magnetics on the left, U4, and TC1
(`YX 220 16V`).

### Photo 17

![Photo 17](web/17.jpg)

Board A, same area as 16 (magnetics, U4 and TC1) at an angle. The U4 marking is readable.

### Photo 18

![Photo 18](web/18.jpg)

Board A, same area as 16 (magnetics, U4 and TC1) from slightly further back.

### Photo 19

![Photo 19](web/19.jpg)

Board A (C4 is marked `YX 47 63V`). Power corner: PU1, PR1 (`86C`), PR2, PR3 (`304`),
PC6, C18, C20, the `4R7` inductor L3 and C4.

### Photo 20

![Photo 20](web/20.jpg)

Board A, U4 (readable marking) and the DXFRM6 magnetics (`G2401PR`, date `2632`).

### Photo 21

![Photo 21](web/21.jpg)

Board A, the corner by the RJ45 block. The PoE module header (`PIN1`, 8 holes) is
empty. The RJ7-RJ18 resistor pads for the POW and FX LEDs sit at the board edge.
LED6 is an empty through-hole footprint.

![Photo 21 with callouts](annotated/21.jpg)

### Photo 22

![Photo 22](web/22.jpg)

Board A, the RJ45 block end: LED7, LED8, R68 and the empty LED6 footprint.

### Photo 23

![Photo 23](web/23.jpg)

Board A, U4 area: Y6, L2 `701`, D5 `SS510` and the blue disc parts RV1-RV3.

### Photo 24

![Photo 24](web/24.jpg)

Bottom side, under the RJ45 block. The jack pins are covered with white tape or
residue. D19, D21, C69 and C73 are visible.

### Photo 25

![Photo 25](web/25.jpg)

Bottom side, the other end of the RJ45 block. A row of SMB diodes (D8, D10-D14,
marked `CP06C`) sits behind the jacks, with R76, R74, R73, R72, R71, R67 and 1206
capacitors beside them.

### Photo 26

![Photo 26](web/26.jpg)

Bottom side under U4. U6 is an unpopulated 8-pin footprint (the size of an SPI flash);
U10 is an `HK24C08` (1 KB I²C EEPROM). The tinned pad with a solder blob in the middle
is probably under U4's exposed pad.

![Photo 26 with callouts](annotated/26.jpg)

### Photo 27

![Photo 27](web/27.jpg)

Bottom side, wider view of 26 including U10 and the port-diode column (D6-D12 and
D16-D18).

### Photo 28

![Photo 28](web/28.jpg)

Bottom side, near U10. Out of focus.

### Photo 29

![Photo 29](web/29.jpg)

Bottom side, U10 close-up: `HK 24C08` over `2S3746HA`, with R29, R30 and C15 next to it.

### Photo 30

![Photo 30](web/30.jpg)

Board B, the PoE PSE module from above: U1, four R250 (0.25 Ω) sense resistors
(R8, R12, R13, R14), diodes D1, D3, D5 and D7, and the 8-pin header row along the RJ45
block.

### Photo 31

![Photo 31](web/31.jpg)

Board B, PoE module at an angle. The diodes are marked `2616` over `RGS`.

### Photo 32

![Photo 32](web/32.jpg)

Board B, macro of the PoE module. U1 reads `2184A` over `533AQ1H` (QFN). The part is
unidentified; it is drawn as an unidentified 4-port PSE in the
[schematic](../schematic/README.md).

![Photo 32 with callouts](annotated/32.jpg)

### Photo 33

![Photo 33](web/33.jpg)

Board A, uplink corner: `LX-IS601F V2.0` silkscreen, DXFRM6 (`G2401PR`, date `2632`), R41
and C37.

### Photo 34

![Photo 34](web/34.jpg)

Board B, same corner as 33. DXFRM6 is `G2401PR` with date `2523A`, which tells the two boards
apart.

## Regenerating the images

[`make_photos.py`](make_photos.py) builds [`web/`](web/), [`thumbs/`](thumbs/) and
[`annotated/`](annotated/) from the album originals:

```
python3 make_photos.py /path/to/originals   # 01.jpg .. 34.jpg in album order
```

The script lists each photo's rotation (`ROTATE`), crop box (`CROP`) and callouts
(`CALLOUTS`). Callout positions are percentages of the rotated, cropped photo.
