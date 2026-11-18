# Switch boards: strapping and major components

How the two switch boards in this project are strapped, what the strapping selects, and which parts they carry.

## Contents

- [Boards](#boards)
- [Source tags](#source-tags)
- [Summary](#summary)
- [LX-IS601F V2.0](#lx-is601f-v20)
  - <a href="#lx-strap-resistor-array">Strap resistor array</a>
  - <a href="#lx-other-configuration-pins">Other configuration pins</a>
  - <a href="#lx-what-the-strapping-selects">What the strapping selects</a>
  - <a href="#lx-major-components">Major components</a>
  - <a href="#lx-photos">Photos</a>
  - <a href="#lx-checks">Checks that would confirm the strapping</a>
- [wu-kou YT9215S V2.0](#wu-kou-yt9215s-v20)
  - <a href="#wk-design-files">Design files</a>
  - <a href="#wk-configuration-pins">Configuration pins</a>
  - <a href="#wk-led-pins">LED pins with no strap in Table 15</a>
  - <a href="#wk-led-wiring">LED wiring per port</a>
  - <a href="#wk-what-the-strapping-selects">What the strapping selects</a>
  - <a href="#wk-other-pins">Reset and unconnected pins</a>
  - <a href="#wk-major-components">Major components</a>
  - <a href="#wk-bom">All BOM lines</a>
  - <a href="#wk-designators">Designators</a>

## Boards

| Board | Switch IC | Chip datasheet | Origin | Evidence | Section |
|---|---|---|---|---|---|
| LX-IS601F V2.0 | <a href="#lx-u4">YT9215SCH</a> | [V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) | Bought PoE switch | <a href="#lx-photos">Photos</a> | [LX-IS601F V2.0](#lx-is601f-v20) |
| wu-kou YT9215S V2.0 | <a href="#wk-u2">YT9215S</a> | [Draft_05](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf) | [OSHWHub open design](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0) | <a href="#wk-design-files">Design files</a> | [wu-kou YT9215S V2.0](#wu-kou-yt9215s-v20) |

The two chips have different pinouts, so each board is decoded with its own datasheet. Debug pins (UART, JTAG and flash) are
in [motorcomm-debug-pins.md](motorcomm-debug-pins.md). The switch IC datasheets are in
[datasheets/motorcomm/](../datasheets/README.md#motorcomm-included) and the datasheets of the other parts are in
[datasheets/components/](../datasheets/README.md#board-components-included). Both are indexed in
[datasheets/README.md](../datasheets/README.md).

A datasheet link opens the PDF at the cited page when the file is viewed on GitHub. In the built documentation the link
downloads the PDF, so the page number is also given in the link text or in the Column, Tag and Source table under each table.

On both chips the strap pins are latched at reset and most of them double as LED outputs. Neither datasheet lists a strap for
port speed, port mode or the extension-port interface type; those are register settings.

## Source tags

Each value carries one of these tags.

| Tag | Meaning |
|---|---|
| <a id="tag-r"></a>**R** | Read directly from a design file or a photo |
| <a id="tag-d"></a>**D** | Taken from the datasheet of the matching chip variant |
| <a id="tag-i"></a>**I** | Inferred, with the reasoning in the prose under the table |
| <a id="tag-u"></a>**U** | Unknown because it is not traced |

## Summary

| Setting | LX-IS601F V2.0 | Tag | wu-kou YT9215S V2.0 | Tag |
|---|---|---|---|---|
| Embedded MCU | <a href="#lx-pin-76">Disabled</a> | <a href="#tag-i">I</a> | <a href="#wk-pin-75">Enabled</a> | <a href="#tag-r">R</a> |
| Start-up load | <a href="#lx-what-the-strapping-selects">EEPROM to registers</a> | <a href="#tag-i">I</a> | <a href="#wk-what-the-strapping-selects">None</a> | <a href="#tag-i">I</a> |
| SPI flash interface | <a href="#lx-pin-75">Disabled</a> | <a href="#tag-i">I</a> | <a href="#wk-pin-74">Disabled</a> | <a href="#tag-r">R</a> |
| EEPROM autoload | <a href="#lx-pin-77">Enabled</a> | <a href="#tag-i">I</a> | <a href="#wk-pin-76">Disabled</a> | <a href="#tag-r">R</a> |
| EEPROM fitted | <a href="#lx-u10">24C08</a> | <a href="#tag-r">R</a> | <a href="#wk-bom">None</a> | <a href="#tag-r">R</a> |
| SPI flash fitted | <a href="#lx-u6">None</a> | <a href="#tag-r">R</a> | <a href="#wk-bom">None</a> | <a href="#tag-r">R</a> |
| Embedded PHYs | <a href="#lx-pin-83">Enabled</a> | <a href="#tag-i">I</a> | <a href="#wk-pin-79">Enabled</a> | <a href="#tag-r">R</a> |
| Internal core regulator | <a href="#lx-pin-60">Enabled</a> | <a href="#tag-i">I</a> | <a href="#wk-pin-60">Enabled</a> | <a href="#tag-r">R</a> |
| Slave SMI address | <a href="#lx-pin-80">0x1d</a> | <a href="#tag-i">I</a> | <a href="#wk-configuration-pins">No strap</a> | <a href="#tag-d">D</a> |
| Switch ID | <a href="#lx-pin-46">0</a> | <a href="#tag-i">I</a> | <a href="#wk-pin-45">0</a> | <a href="#tag-d">D</a> |
| LED mode | <a href="#lx-what-the-strapping-selects">Parallel</a> | <a href="#tag-i">I</a> | <a href="#wk-led-wiring">Parallel</a> | <a href="#tag-i">I</a> |
| Power-on LED blink | <a href="#lx-pin-74">Enabled</a> | <a href="#tag-i">I</a> | <a href="#wk-pin-73">Enabled</a> | <a href="#tag-r">R</a> |

The LX-IS601F is strapped as a switch that loads its register settings from the I²C EEPROM at reset, with the embedded MCU held
off. The wu-kou board is strapped as a plain unmanaged switch: nothing is loaded, and the embedded MCU is left enabled with nothing to
boot from.

## LX-IS601F V2.0

Switch IC: <a href="#lx-u4">U4</a>, a Motorcomm YT9215SCH. Pin functions are from the [YT9215SCH datasheet V1.03](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf).

<a id="lx-strap-resistor-array"></a>
### Strap resistor array

The bottom side has two rows of nine small chip-resistor footprints, <a href="#lx-r49">R49</a> to <a href="#lx-r66">R66</a>. They form nine pairs, and each pair has exactly
one resistor fitted. The source photo is [photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg). The array is taken to lie under the pin 65 to 96 side of <a href="#lx-u4">U4</a>; that
placement comes from lining the bottom photo up with the top photos and is part of the <a href="#lx-inference-pin-order">pin order inference</a>.
The designators do not run in order along the rows: <a href="#lx-r65">R65</a> and <a href="#lx-r66">R66</a> are the third pair and <a href="#lx-r59">R59</a> and <a href="#lx-r60">R60</a> are the last pair.

[![Strap resistor array on the bottom of the LX-IS601F](lx-is601f-board/strap-resistors-annotated.jpg)](lx-is601f-board/strap-resistors-annotated.jpg)

| Position | Pin | Strap | LED output | Pull-up | Pull-up fitted | Pull-down | Pull-down fitted | Internal | Level | Selects |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | <a id="lx-pin-70"></a>70 | [DIS_SPIS](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | [P4LED2](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=24) | <a id="lx-r50"></a>R50 | Yes | <a id="lx-r49"></a>R49 | No | Pull-up | 1 | Slave SPI off |
| 2 | <a id="lx-pin-71"></a>71 | [EEPROM_MOD](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | [P4LED0](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=24) | <a id="lx-r52"></a>R52 | No | <a id="lx-r51"></a>R51 | Yes | Pull-up | 0 | EEPROM of 16 Kbit or less |
| 3 | <a id="lx-pin-74"></a>74 | [EN_PWRLIGHT](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | [P3LED2](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=24) | <a id="lx-r66"></a>R66 | Yes | <a id="lx-r65"></a>R65 | No | Pull-up | 1 | Power-on LED blink on |
| 4 | <a id="lx-pin-75"></a>75 | [EN_SPIF](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | [P3LED0](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=24) | <a id="lx-r54"></a>R54 | No | <a id="lx-r53"></a>R53 | Yes | Pull-up | 0 | SPI flash interface off |
| 5 | <a id="lx-pin-76"></a>76 | [DIS_MCU](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | [P2LED2](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=24) | <a id="lx-r56"></a>R56 | Yes | <a id="lx-r55"></a>R55 | No | Pull-up | 1 | MCU disabled |
| 6 | <a id="lx-pin-77"></a>77 | [DISAUTOLOAD](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | [P2LED0](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=24) | <a id="lx-r58"></a>R58 | No | <a id="lx-r57"></a>R57 | Yes | Pull-up | 0 | EEPROM autoload on |
| 7 | <a id="lx-pin-80"></a>80 | [MID29](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | [P1LED0](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=25) | <a id="lx-r62"></a>R62 | Yes | <a id="lx-r61"></a>R61 | No | Pull-up | 1 | Slave SMI address 0x1d |
| 8 | <a id="lx-pin-83"></a>83 | [EN_PHY](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | [P0LED2](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=25) | <a id="lx-r64"></a>R64 | Yes | <a id="lx-r63"></a>R63 | No | Pull-up | 1 | Embedded PHYs on |
| 9 | <a id="lx-pin-85"></a>85 | [SMI_SEL](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | [P0LED0](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=25) | <a id="lx-r60"></a>R60 | Yes | <a id="lx-r59"></a>R59 | No | Pull-up | 1 | EEPROM SMI interface |

| Column | Tag | Source |
|---|---|---|
| Position | <a href="#tag-r">R</a> | [photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg) |
| Pull-up | <a href="#tag-r">R</a> | [photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg) |
| Pull-down | <a href="#tag-r">R</a> | [photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg) |
| Pull-up fitted | <a href="#tag-r">R</a> | [photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg) |
| Pull-down fitted | <a href="#tag-r">R</a> | [photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg) |
| Strap | <a href="#tag-d">D</a> | [Table 20 on pages 28 to 29](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) |
| LED output | <a href="#tag-d">D</a> | [Table 8 on pages 24 to 25](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=24) |
| Internal | <a href="#tag-d">D</a> | [Table 20 on pages 28 to 29](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) |
| Selects | <a href="#tag-d">D</a> | [Table 20 on pages 28 to 29](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) |
| Pin | <a href="#tag-i">I</a> | <a href="#lx-inference-pin-order">Pin order</a> |
| Level | <a href="#tag-i">I</a> | <a href="#lx-inference-row">Which row pulls up</a> |

Read from the photo: which footprints carry a resistor, and their designators. Short traces run between the two rows, which fits
each pair sharing one signal on its inner pads with the outer pads on two rails, but the photo is not sharp enough to follow
each one. The resistors are unmarked, so their value is not known. The datasheet's typical value is
[4.7 kΩ, page 40](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=40).

Inferred, with the reasons:

- <a id="lx-inference-pin-order"></a>**Pin order.** The YT9215SCH has exactly nine latched strap pins on the LED side
  (<a href="#lx-pin-70">70</a>, <a href="#lx-pin-71">71</a>, <a href="#lx-pin-74">74</a>, <a href="#lx-pin-75">75</a>, <a href="#lx-pin-76">76</a>, <a href="#lx-pin-77">77</a>, <a href="#lx-pin-80">80</a>, <a href="#lx-pin-83">83</a>, <a href="#lx-pin-85">85</a>), and the array has exactly nine pairs, so the pairs are assigned to the nine pins
  in the order they sit along the package. Two things fix which end is pin <a href="#lx-pin-70">70</a>. The EEPROM <a href="#lx-u10">U10</a> sits at the
  <a href="#lx-r59">R59</a> and <a href="#lx-r60">R60</a> end of the array, which is the end nearest the I²C pins 91 and 92. With the order reversed,
  the levels would give EN_PHY (pin <a href="#lx-pin-83">83</a>) = 0 and EEPROM_MOD (pin <a href="#lx-pin-71">71</a>) = 1, which turns the copper PHYs off and contradicts the 8 Kbit EEPROM.
- <a id="lx-inference-row"></a>**Which row pulls up.** With the odd-numbered row as pull-downs, the three low straps are
  EEPROM_MOD (pin <a href="#lx-pin-71">71</a>), EN_SPIF (pin <a href="#lx-pin-75">75</a>) and DISAUTOLOAD (pin <a href="#lx-pin-77">77</a>). All three agree with what is
  fitted: the EEPROM <a href="#lx-u10">U10</a> is a 24C08 (8 Kbit, below the 16 Kbit threshold), the flash footprint <a href="#lx-u6">U6</a> is
  empty, and there is an EEPROM to autoload from. With the rows swapped, EN_PHY (pin <a href="#lx-pin-83">83</a>) would be 0, which turns
  the PHYs off on a board whose copper ports work, and all three of the straps above would contradict the fitted parts.

Neither inference has been checked with a meter; the <a href="#lx-checks">checks</a> below would settle both. The bottom-side photo does
not show which of the two photographed boards it is, so the table is for one board; the other is assumed to match.

<a id="lx-other-configuration-pins"></a>
### Other configuration pins

| Pin | Signal | Board connection | Tag | Photo | Internal | Level | Level tag | Selects |
|---|---|---|---|---|---|---|---|---|
| <a id="lx-pin-46"></a>46 | [SWITCH_ID_1](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | No trace leaves the pin | <a href="#tag-r">R</a> | [photo-u4-macro.jpg](lx-is601f-board/photo-u4-macro.jpg) | Pull-down | 0 | <a href="#tag-i">I</a> | Switch ID bit 1 = 0 |
| <a id="lx-pin-51"></a>51 | [SWITCH_ID_0](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | Not traced | <a href="#tag-u">U</a> | – | Pull-down | 0 | <a href="#tag-i">I</a> | Switch ID bit 0 = 0 |
| <a id="lx-pin-47"></a>47 | [RESERVED_0](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | No trace leaves the pin | <a href="#tag-r">R</a> | [photo-u4-macro.jpg](lx-is601f-board/photo-u4-macro.jpg) | Pull-up | 1 | <a href="#tag-i">I</a> | – |
| <a id="lx-pin-48"></a>48 | [RESERVED_1](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | Not traced | <a href="#tag-u">U</a> | – | Pull-up | 1 | <a href="#tag-i">I</a> | – |
| <a id="lx-pin-50"></a>50 | [RESERVED_2](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | <a id="lx-r92"></a>R92 | <a href="#tag-r">R</a> | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | Pull-down | Not known | <a href="#tag-u">U</a> | – |
| <a id="lx-pin-49"></a>49 | [SPF_MUX_SEL](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | <a id="lx-r93"></a>R93 | <a href="#tag-r">R</a> | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | Pull-down | Not known | <a href="#tag-u">U</a> | Flash pin group |
| <a id="lx-pin-54"></a>54 | [SPF0_SO](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=25) | <a id="lx-r89"></a>R89 | <a href="#tag-r">R</a> | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | Pull-up | – | – | Not a strap |
| <a id="lx-pin-55"></a>55 | [SPF0_CS](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=25) | <a id="lx-r44"></a>R44 | <a href="#tag-r">R</a> | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | Pull-up | – | – | Not a strap |
| <a id="lx-pin-60"></a>60 | [EN_SWR](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | Not traced | <a href="#tag-u">U</a> | – | None | 1 | <a href="#tag-i">I</a> | Internal regulator on |
| <a id="lx-pin-89"></a>89 | [nRESET](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=30) | Not traced | <a href="#tag-u">U</a> | – | Pull-up | – | – | Not a strap |

| Column | Tag | Source |
|---|---|---|
| Board connection | In the Tag column | In the Photo column |
| Level | In the Level tag column | Prose under this table |
| Pin | <a href="#tag-d">D</a> | [Table 20 on pages 28 to 29](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) |
| Signal | <a href="#tag-d">D</a> | [Table 20 on pages 28 to 29](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) |
| Internal | <a href="#tag-d">D</a> | [Table 20 on pages 28 to 29](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) |
| Selects | <a href="#tag-d">D</a> | [Table 20 on pages 28 to 29](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) |

Three rows are not in Table 20: pins <a href="#lx-pin-54">54</a> and <a href="#lx-pin-55">55</a> are from [Table 10 on page 25](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=25) and pin
<a href="#lx-pin-89">89</a> is from [Table 23 on page 30](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=30).

- The [datasheet, page 29](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) says RESERVED_0 (pin <a href="#lx-pin-47">47</a>), RESERVED_1 (pin <a href="#lx-pin-48">48</a>) and RESERVED_2 (pin <a href="#lx-pin-50">50</a>) must each be pulled high through an external
  4.7 kΩ resistor. Pin <a href="#lx-pin-47">47</a> has no external part at all, so on this board it relies on its internal pull-up.
- <a href="#lx-r44">R44</a>, <a href="#lx-r89">R89</a>, <a href="#lx-r92">R92</a> and <a href="#lx-r93">R93</a> sit on pins <a href="#lx-pin-55">55</a>, <a href="#lx-pin-54">54</a>, <a href="#lx-pin-50">50</a> and <a href="#lx-pin-49">49</a>,
  which are the four [SPF0 flash pins, page 25](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=25). Where their far pads go is not traced, so it is not known whether
  they are pull-ups or series resistors to the empty <a href="#lx-u6">U6</a> footprint. SPF_MUX_SEL only matters when EN_SPIF
  (pin <a href="#lx-pin-75">75</a>) is high, which it is not.
- EN_SWR (pin <a href="#lx-pin-60">60</a>) is taken as high because the regulator's inductor <a href="#lx-l3">L3</a> is fitted on the LX pins 63 and 64.
- A group of option footprints (R39, R40, R45, R94 to R102, R108 and R109) sits next to <a href="#lx-u6">U6</a> and is partly populated
  ([photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg)). Its function is not traced.

<a id="lx-what-the-strapping-selects"></a>
### What the strapping selects

| Strap | Pin | Level | Tag |
|---|---|---|---|
| [DISAUTOLOAD](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | <a href="#lx-pin-77">77</a> | 0 | <a href="#tag-i">I</a> |
| [DIS_MCU](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | <a href="#lx-pin-76">76</a> | 1 | <a href="#tag-i">I</a> |
| [EN_SPIF](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | <a href="#lx-pin-75">75</a> | 0 | <a href="#tag-i">I</a> |
| [DIS_SPIS](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=28) | <a href="#lx-pin-70">70</a> | 1 | <a href="#tag-i">I</a> |
| [SMI_SEL](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=29) | <a href="#lx-pin-85">85</a> | 1 | <a href="#tag-i">I</a> |

| Result | Value | Tag |
|---|---|---|
| Loads from | EEPROM <a href="#lx-u10">U10</a> | <a href="#tag-d">D</a> |
| Loads to | Registers | <a href="#tag-d">D</a> |
| MCU | Does not run | <a href="#tag-d">D</a> |

The tag <a href="#tag-d">D</a> covers the mapping from levels to result. The levels themselves are inferred, so the [summary](#summary) tags the
outcome <a href="#tag-i">I</a>.

These levels match the third row of [Table 25, "Flexible Applications", on pages 33 to 34](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=33), which the datasheet heads
DISAUTOLOAD, DIS_MCU, EN_SPIF, DIS_SPI and SMI_SEL. That row is 0, 1, 0, X, X, so DIS_SPIS (pin <a href="#lx-pin-70">70</a>) and SMI_SEL (pin <a href="#lx-pin-85">85</a>) do not affect the
result. At reset the chip reads <a href="#lx-u10">U10</a>
and writes the contents into its registers. That is how the board can bring up its SFP port
(<a href="#lx-sfp">the SFP connector</a>), which needs the SerDes configured by register, without any firmware (inferred). Reading <a href="#lx-u10">U10</a> would
show exactly which registers the vendor sets.

The LEDs are driven in parallel mode, one pin per LED (inferred from the <a href="#lx-unlisted">row of six LEDs</a> on the board). LED polarity
follows the strap level on each pin ([datasheet, page 40](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=40)): a pin pulled up drives its LED active low, and a pin
pulled down drives it active high. Pins <a href="#lx-pin-71">71</a>, <a href="#lx-pin-75">75</a> and <a href="#lx-pin-77">77</a> are therefore active high and the other six
are active low.

<a id="lx-major-components"></a>
### Major components

| Ref | Ref tag | Function | Part | Marking | Package | Value | Rating | Board | Side | Photo | Datasheet | LCSC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <a id="lx-u4"></a>U4 | <a href="#tag-r">R</a> | Switch IC | YT9215SCH | `YT9215SCH` | LQFP-128 with exposed pad | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | [PDF](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) | – |
| <a id="lx-y6"></a>Y6 | <a href="#tag-r">R</a> | Crystal | – | `25.000 MHZ` | SMD 4-pad | 25 MHz | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-u10"></a>U10 | <a href="#tag-r">R</a> | I²C EEPROM | 24C08 | `24C08` | SOIC-8 | 8 Kbit | – | Not known | Bottom | [photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg) | [Similar part](../datasheets/components/Hangshun_HK24C08.pdf) | [C495286](https://jlcpcb.com/partdetail/C495286) |
| <a id="lx-u6"></a>U6 | <a href="#tag-r">R</a> | SPI flash footprint | Not fitted | – | 8-pin footprint | – | – | Not known | Bottom | [photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg) | – | – |
| <a id="lx-pu1"></a>PU1 | <a href="#tag-r">R</a> | Buck regulator | SCT2622 | `2622 SCT` | ESOP-8 | – | – | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | [PDF](../datasheets/components/SCT_SCT2622.pdf) | [C5361735](https://www.lcsc.com/product-detail/C5361735.html) |
| <a id="lx-pr1"></a>PR1 | <a href="#tag-r">R</a> | Resistor beside PU1 | – | `86C` | Chip resistor | 76.8 kΩ | – | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | – | – |
| <a id="lx-pr2"></a>PR2 | <a href="#tag-r">R</a> | Resistor beside PU1 | – | `30D` | Chip resistor | 200 kΩ | – | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | – | – |
| <a id="lx-pr3"></a>PR3 | <a href="#tag-r">R</a> | Resistor beside PU1 | – | `304` | Chip resistor | 300 kΩ | – | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | – | – |
| <a id="lx-r8"></a>R8 | <a href="#tag-r">R</a> | Resistor beside PU1 | – | `49C` | Chip resistor | 31.6 kΩ | – | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | – | – |
| <a id="lx-r11"></a>R11 | <a href="#tag-r">R</a> | Resistor beside PU1 | – | `51C` | Chip resistor | 33.2 kΩ | – | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | – | – |
| <a id="lx-pl3"></a>PL3 | <a href="#tag-r">R</a> | Buck inductor | – | `100` | SMD | 10 µH | – | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | – | – |
| <a id="lx-d40"></a>D40 | <a href="#tag-r">R</a> | Buck catch diode | SS310 | `LGE SS310` | SMA | 3 A | 100 V | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | [PDF](../datasheets/components/LGE_SS32-SS320_Series.pdf) | [C432297](https://www.lcsc.com/product-detail/C432297.html) |
| <a id="lx-tc1"></a>TC1 | <a href="#tag-r">R</a> | Buck output capacitor | – | `220 16V` | Aluminium can | 220 µF | 16 V | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-l3"></a>L3 | <a href="#tag-i">I</a> | Core regulator inductor | – | `4R7` | SMD | 4.7 µH | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-c4"></a>C4 | <a href="#tag-r">R</a> | Input capacitor | – | `YX 47 63V` | Aluminium can | 47 µF | 63 V | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | – | – |
| <a id="lx-c4-b"></a>C4 | <a href="#tag-r">R</a> | Input capacitor | – | `22 63V EMB` | Aluminium can | 22 µF | 63 V | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-choke"></a>Not legible | <a href="#tag-u">U</a> | Input choke | – | `701` | SMD | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-d4"></a>D4 | <a href="#tag-r">R</a> | Input diode | SS510 | `LGE SS510` | SMA | 5 A | 100 V | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | [PDF](../datasheets/components/LGE_SS52-SS520_Series.pdf) | [C432296](https://www.lcsc.com/product-detail/C432296.html) |
| <a id="lx-d5"></a>D5 | <a href="#tag-r">R</a> | Input diode | SS510 | `LGE SS510` | SMA | 5 A | 100 V | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | [PDF](../datasheets/components/LGE_SS52-SS520_Series.pdf) | [C432296](https://www.lcsc.com/product-detail/C432296.html) |
| <a id="lx-p4"></a>P4 | <a href="#tag-r">R</a> | Power input | – | – | 2-pin through-hole header | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-dxfrm1"></a>DXFRM1 | <a href="#tag-r">R</a> | Port magnetics footprint | – | – | Not visible | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-dxfrm2"></a>DXFRM2 | <a href="#tag-r">R</a> | Port magnetics | G2401PR | `United-tek G2401PR` | SMD 24-pin | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | [Similar part](../datasheets/components/Usakro_UKG2401PR.pdf) | – |
| <a id="lx-dxfrm3"></a>DXFRM3 | <a href="#tag-r">R</a> | Port magnetics | G2401PR | Partly hidden | SMD 24-pin | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | [Similar part](../datasheets/components/Usakro_UKG2401PR.pdf) | – |
| <a id="lx-dxfrm5"></a>DXFRM5 | <a href="#tag-r">R</a> | Port magnetics | G2401PR | `United-tek G2401PR` | SMD 24-pin | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | [Similar part](../datasheets/components/Usakro_UKG2401PR.pdf) | – |
| <a id="lx-dxfrm6"></a>DXFRM6 | <a href="#tag-r">R</a> | Port magnetics | G2401PR | `United-tek G2401PR` | SMD 24-pin | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | [Similar part](../datasheets/components/Usakro_UKG2401PR.pdf) | – |
| <a id="lx-ed1"></a>ED1 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | – | – |
| <a id="lx-ed2"></a>ED2 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-ed3"></a>ED3 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-ed4"></a>ED4 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-ed5"></a>ED5 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-ed6"></a>ED6 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-ed7"></a>ED7 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-ed8"></a>ED8 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-ed9"></a>ED9 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-ed10"></a>ED10 | <a href="#tag-r">R</a> | ESD array | Not identified | `05U` | SOT-23-6 | – | – | A | Top | [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | – | – |
| <a id="lx-poe-ports"></a>Not legible | <a href="#tag-u">U</a> | PoE ports 1 to 4 | – | – | Through-hole 1×4 RJ45 block | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-uplink"></a>Not legible | <a href="#tag-u">U</a> | Uplink port | – | – | Through-hole RJ45 | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-sfp"></a>Not legible | <a href="#tag-u">U</a> | SFP connector | – | – | SMD with cage | – | – | B | Top | [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | – | – |
| <a id="lx-pin1"></a>PIN1 | <a href="#tag-r">R</a> | PoE module header | – | – | 8-pin through-hole | – | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-u1"></a>Module U1 | <a href="#tag-r">R</a> | PoE PSE controller | Not identified | `2184A` | QFN | – | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-r8"></a>Module R8 | <a href="#tag-r">R</a> | Module sense resistor | – | `R250` | Chip resistor | 0.25 Ω | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-r12"></a>Module R12 | <a href="#tag-r">R</a> | Module sense resistor | – | `R250` | Chip resistor | 0.25 Ω | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-r13"></a>Module R13 | <a href="#tag-r">R</a> | Module sense resistor | – | `R250` | Chip resistor | 0.25 Ω | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-r14"></a>Module R14 | <a href="#tag-r">R</a> | Module sense resistor | – | `R250` | Chip resistor | 0.25 Ω | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-r3"></a>Module R3 | <a href="#tag-r">R</a> | Module resistor | – | `330` | Chip resistor | 33 Ω | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-r9"></a>Module R9 | <a href="#tag-r">R</a> | Module resistor | – | `330` | Chip resistor | 33 Ω | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-r10"></a>Module R10 | <a href="#tag-r">R</a> | Module resistor | – | `330` | Chip resistor | 33 Ω | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-r11"></a>Module R11 | <a href="#tag-r">R</a> | Module resistor | – | `330` | Chip resistor | 33 Ω | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-d1"></a>Module D1 | <a href="#tag-r">R</a> | Module port diode | Not identified | `2616 RGS` | SMD 2-pin | – | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-d3"></a>Module D3 | <a href="#tag-r">R</a> | Module port diode | Not identified | `2616 RGS` | SMD 2-pin | – | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-d5"></a>Module D5 | <a href="#tag-r">R</a> | Module port diode | Not identified | `2616 RGS` | SMD 2-pin | – | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-d7"></a>Module D7 | <a href="#tag-r">R</a> | Module port diode | Not identified | `2616 RGS` | SMD 2-pin | – | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |
| <a id="lx-module-d-unlabelled"></a>Not legible | <a href="#tag-u">U</a> | Module diode | Not identified | `2616 RGS` | SMD 2-pin | – | – | B | Top | [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | – | – |

| Column | Tag | Source |
|---|---|---|
| Ref | In the Ref tag column | Silkscreen in the linked photo |
| Marking | <a href="#tag-r">R</a> | Top marking in the linked photo |
| Board | <a href="#tag-r">R</a> | The linked photo |
| Side | <a href="#tag-r">R</a> | The linked photo |
| Function | <a href="#tag-i">I</a> | Position on the board |
| Part | <a href="#tag-i">I</a> | The marking |
| Package | <a href="#tag-i">I</a> | Appearance in the linked photo |
| Value | <a href="#tag-i">I</a> | The marking code |
| Rating | <a href="#tag-i">I</a> | The marking code |
| Datasheet | <a href="#tag-i">I</a> | The catalogue part that matches the marking |
| LCSC | <a href="#tag-i">I</a> | The catalogue part that matches the marking |

A Ref of "Not legible" with tag <a href="#tag-u">U</a> means no designator can be read for that part in the photos. The Datasheet and LCSC
columns point at the catalogue part that matches the marking, not at a known purchase.

- There is no separate MCU on the board. The only processor is the embedded MCU inside
  <a href="#lx-u4">U4</a>, which the <a href="#lx-pin-76">DIS_MCU strap</a> disables.
- The 1.15 V core rail comes from <a href="#lx-u4">U4</a>'s own switching regulator through <a href="#lx-l3">L3</a>, not from a second DC-DC.
- <a href="#lx-pu1">PU1</a> has a 0.8 V feedback reference ([datasheet, page 3](../datasheets/components/SCT_SCT2622.pdf#page=3)). Its output is taken to be the 3.3 V rail
  (inferred from the rail it feeds). <a href="#lx-pr1">PR1</a>, <a href="#lx-pr2">PR2</a>, <a href="#lx-pr3">PR3</a>, <a href="#lx-r8">R8</a> and <a href="#lx-r11">R11</a> sit beside it and
  their values are decoded from the marking codes, but which of them form the feedback divider is not traced.
- The board is PoE sourcing equipment (PSE): it feeds power out of the <a href="#lx-poe-ports">four-port RJ45 block</a> under control of
  <a href="#lx-module-u1">module U1</a>, taken to be a four-port controller from the four `R250` sense resistors (<a href="#lx-module-r8">R8</a>, <a href="#lx-module-r12">R12</a>, <a href="#lx-module-r13">R13</a> and <a href="#lx-module-r14">R14</a>). It has no powered-device front end.
- The `701` part has two terminals on each side and exposed windings, so it is taken to be a common-mode choke on the power input.
- <a href="#lx-u10">U10</a> is marked `24C08` with a maker logo that does not identify the maker. The linked datasheet is the Hangshun HK24C08,
  one of several pin-compatible 24C08 parts.
- The marking `United-tek G2401PR` has no datasheet under that name. The linked "similar part" is the Usakro UKG2401PR, a
  single-port 1000BASE-T transformer in the same 24-pin package; that it is the same part is not confirmed.
  Four transformer bodies are visible. <a href="#lx-dxfrm3">DXFRM3</a> is partly under the PoE module, so its marking is only partly
  legible and its part is inferred. The <a href="#lx-dxfrm1">DXFRM1</a> silkscreen has no visible body beside it, and an unreadable
  label next to it may be DXFRM4.
- The <a href="#lx-l3">L3</a> silkscreen is partly hidden by <a href="#lx-c4">C4</a> in both [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) and [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg), so that designator is inferred.
- <a href="#lx-c4">C4</a> differs between the two boards, so it has one row per board.
- No datasheet is available for the `05U` ESD arrays (<a href="#lx-ed1">ED1</a> to <a href="#lx-ed10">ED10</a>), the `2184A` PSE controller (<a href="#lx-module-u1">module U1</a>) or the `2616 RGS` diodes (<a href="#lx-module-d1">module D1</a> to <a href="#lx-module-d7">D7</a> and the <a href="#lx-module-d-unlabelled">unlabelled fifth diode</a>).
- Second marking lines are date or lot codes: `533AQ1H` on <a href="#lx-module-u1">module U1</a> and `2523A` on the G2401PR parts.
- The two photographed boards differ in fitted parts. Board A ([photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg)) has no PoE module fitted. Board B ([photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg)) has the
  PoE module and the SFP cage. [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) does not show the SFP area of board A.

<a id="lx-unlisted"></a>
#### Parts not in the table

These are visible but are not identified.

- Three blue radial disc parts stand beside <a href="#lx-p4">P4</a> ([photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg)). They are taken to be surge protection parts on the power input.
- A row of six LEDs sits along the board edge beside G1, under the edge of the PoE module ([photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) and [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg)). The
  silkscreen under them reads RJ7 to RJ18. No part is visible at those labels, so what they designate is not known; they are
  taken to be the LED series resistors.
- A group of option footprints sits next to <a href="#lx-u6">U6</a> on the bottom side and is partly populated ([photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg)).

<a id="lx-photos"></a>
### Photos

| File | Board | Side | Shows |
|---|---|---|---|
| [photo-bottom-under-u4.jpg](lx-is601f-board/photo-bottom-under-u4.jpg) | Not known | Bottom | Area under <a href="#lx-u4">U4</a> with the strap array |
| [strap-resistors-annotated.jpg](lx-is601f-board/strap-resistors-annotated.jpg) | Not known | Bottom | Strap resistor array with decoded levels |
| [lx-is601f-debug-pins-annotated.png](lx-is601f-board/lx-is601f-debug-pins-annotated.png) | B | Top | Debug pins of <a href="#lx-u4">U4</a> with a pin table |
| [photo-u4-wide.jpg](lx-is601f-board/photo-u4-wide.jpg) | A | Top | Area around <a href="#lx-u4">U4</a> |
| [photo-u4-macro.jpg](lx-is601f-board/photo-u4-macro.jpg) | B | Top | Close-up of <a href="#lx-u4">U4</a> with the heatsink removed |
| [photo-board-b-top.jpg](lx-is601f-board/photo-board-b-top.jpg) | B | Top | Whole board |
| [photo-poe-module.jpg](lx-is601f-board/photo-poe-module.jpg) | B | Top | PoE module |

The originals are in the [photo album](https://photos.app.goo.gl/f4gAaRwkkgGWYLGu9). The folder notes are in
[lx-is601f-board/README.md](lx-is601f-board/README.md).

<a id="lx-checks"></a>
### Checks that would confirm the strapping

| # | Check | From | To | Confirms |
|---|---|---|---|---|
| 1 | Continuity | Outer pad of <a href="#lx-r50">R50</a> | 3.3 V | <a href="#lx-inference-row">Which row pulls up</a> |
| 2 | Continuity | Outer pad of <a href="#lx-r49">R49</a> | Ground | <a href="#lx-inference-row">Which row pulls up</a> |
| 3 | Continuity | Inner pads of <a href="#lx-r49">R49</a> | <a href="#lx-u4">U4</a> pin <a href="#lx-pin-70">70</a> | <a href="#lx-inference-pin-order">Pin order</a> |
| 4 | Continuity | Inner pads of <a href="#lx-r59">R59</a> | <a href="#lx-u4">U4</a> pin <a href="#lx-pin-85">85</a> | <a href="#lx-inference-pin-order">Pin order</a> |
| 5 | Register read of `PON_STRAP_VAL` | Management interface | Address 0x80324 | All latched levels |
| 6 | EEPROM read with a clip | <a href="#lx-u10">U10</a> | All 8 Kbit | Registers loaded at reset |

Check 5 is not certain to work as written. The register name and address come from the Linux driver, as noted in
[motorcomm-debug-pins.md](motorcomm-debug-pins.md); neither datasheet lists it. With DIS_SPIS (pin <a href="#lx-pin-70">70</a>) = 1 and SMI_SEL (pin <a href="#lx-pin-85">85</a>) = 1 the
[datasheet, page 45](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=45) selects the slave I²C interface in one place and the slave SMI interface in
[another, page 47](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=47), and the I²C pins are shared with the EEPROM bus. If slave SMI answers, its address is 0x1d
(pin <a href="#lx-pin-80">80</a>, MID29 = 1).

## wu-kou YT9215S V2.0

Switch IC: <a href="#wk-u2">U2</a>, a Motorcomm YT9215S. Pin functions are from the [YT9215S datasheet Draft_05](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf).

<a id="wk-design-files"></a>
### Design files

Everything in this section is read from the design files in [the board repository](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0).

| File | Contents |
|---|---|
| [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) | EasyEDA netlist |
| [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) | Bill of materials |
| [1_P1.kicad_sch](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | KiCad sheet P1 with the switch IC |
| [2_P2.kicad_sch](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | KiCad sheet P2 with the RJ45 ports |
| [schematic-P1.png](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/render/schematic-P1.png) | Render of sheet P1 |
| [schematic-P2.png](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/render/schematic-P2.png) | Render of sheet P2 |
| [schematic.pdf](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/render/schematic.pdf) | Both sheets as PDF |
| [description.en.md](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/docs/description.en.md) | Author's description in English |

The schematic symbol for <a href="#wk-u2">U2</a> is an RTL8367S-CG. The [author's description](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/docs/description.en.md) says a
YT9215S is fitted on the same footprint, so the pin functions below use the YT9215S datasheet. The same description reports
that an RTL8367S did not boot in this board and that the cause is not known, so the strapping below is only shown to suit
the YT9215S.

<a id="wk-configuration-pins"></a>
### Configuration pins

| Pin | Strap | Net | Resistor | Value | Pulls to | BOM line | Test point | Sheet | Internal | Level | Level tag | Selects |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <a id="wk-pin-45"></a>45 | [SWITCH_ID_1](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=28) | Unconnected | None | – | – | – | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | Pull-down | 0 | <a href="#tag-d">D</a> | Switch ID bit 1 = 0 |
| <a id="wk-pin-50"></a>50 | [SWITCH_ID_0](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | Unconnected | None | – | – | – | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | Pull-down | 0 | <a href="#tag-d">D</a> | Switch ID bit 0 = 0 |
| <a id="wk-pin-48"></a>48 | [SPF_MUX_SEL](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | Unconnected | None | – | – | – | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | Pull-down | 0 | <a href="#tag-d">D</a> | Flash pin group SPF1 |
| <a id="wk-pin-46"></a>46 | [reserved_0](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=32) | Unconnected | None | – | – | – | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | Pull-up | 1 | <a href="#tag-d">D</a> | – |
| <a id="wk-pin-47"></a>47 | [reserved_1](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=32) | Unconnected | None | – | – | – | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | Pull-up | 1 | <a href="#tag-d">D</a> | – |
| <a id="wk-pin-49"></a>49 | [reserved_2](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=32) | Unconnected | None | – | – | – | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | Pull-down | 0 | <a href="#tag-d">D</a> | – |
| <a id="wk-pin-60"></a>60 | [EN_SWR](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | EN_SWR | <a id="wk-r14"></a>R14 | 4.7 kΩ | 3V3 | <a href="#wk-bom-28">28</a> | <a href="#wk-tp16">TP16</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | None | 1 | <a href="#tag-r">R</a> | Internal regulator on |
| <a id="wk-pin-70"></a>70 | [EEPROM_MOD](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | P4_LED0 | <a id="wk-r29"></a>R29 | 4.7 kΩ | 3V3 | <a href="#wk-bom-29">29</a> | None | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | Pull-up | 1 | <a href="#tag-r">R</a> | EEPROM above 16 Kbit |
| <a id="wk-pin-73"></a>73 | [EN_PWRLIGHT](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | EN_PWRLIGHT | <a id="wk-r12"></a>R12 | 4.7 kΩ | 3V3 | <a href="#wk-bom-28">28</a> | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | Pull-up | 1 | <a href="#tag-r">R</a> | Power-on LED blink on |
| <a id="wk-pin-74"></a>74 | [EN_SPIF](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | P3_LED0 | <a id="wk-r27"></a>R27 | 4.7 kΩ | GND | <a href="#wk-bom-29">29</a> | None | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | Pull-up | 0 | <a href="#tag-r">R</a> | SPI flash interface off |
| <a id="wk-pin-75"></a>75 | [DIS_MCU](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | P2_LED0 | <a id="wk-r19"></a>R19 | 4.7 kΩ | GND | <a href="#wk-bom-29">29</a> | None | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | Pull-up | 0 | <a href="#tag-r">R</a> | MCU enabled |
| <a id="wk-pin-76"></a>76 | [DISAUTOLOAD](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | DISAUTOLOAD | <a id="wk-r11"></a>R11 | 4.7 kΩ | 3V3 | <a href="#wk-bom-28">28</a> | <a href="#wk-tp14">TP14</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | Pull-up | 1 | <a href="#tag-r">R</a> | EEPROM autoload off |
| <a id="wk-pin-79"></a>79 | [EN_PHY](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | P1_LED0 | <a id="wk-r17"></a>R17 | 4.7 kΩ | 3V3 | <a href="#wk-bom-29">29</a> | None | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | Pull-up | 1 | <a href="#tag-r">R</a> | Embedded PHYs on |
| <a id="wk-pin-81"></a>81 | [SMI_SEL](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | P0_LED0 | <a id="wk-r15"></a>R15 | 4.7 kΩ | 3V3 | <a href="#wk-bom-29">29</a> | None | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | Pull-up | 1 | <a href="#tag-r">R</a> | EEPROM SMI interface |

| Column | Tag | Source |
|---|---|---|
| Net | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Resistor | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Value | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Pulls to | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| BOM line | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Test point | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Sheet | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Pin | <a href="#tag-d">D</a> | [Table 15 on pages 28 to 29](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=28) |
| Strap | <a href="#tag-d">D</a> | [Table 15 on pages 28 to 29](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=28) |
| Internal | <a href="#tag-d">D</a> | [Table 15 on pages 28 to 29](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=28) |
| Selects | <a href="#tag-d">D</a> | [Table 15 on pages 28 to 29](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=28) |
| Level | In the Level tag column | Prose under this table |

On a row with a resistor the level is the rail that the resistor pulls to. On a row without one the level is the internal
pull given by the datasheet. For the three reserved pins the pin numbers are from the [table on page 32](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=32)
and the internal pulls are from [Table 14 on pages 27 to 28](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=27). EN_SWR (pin <a href="#wk-pin-60">60</a>) is an analog enable input
and is not latched; the other pins in the table are latched at reset.

- The [datasheet, page 32](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=32) says reserved_0, reserved_1 and reserved_2 (pins <a href="#wk-pin-46">46</a>, <a href="#wk-pin-47">47</a> and <a href="#wk-pin-49">49</a>)
  must be pulled high through external 4.7 kΩ resistors. The board leaves all three unconnected, and pin <a href="#wk-pin-49">49</a> has an
  internal pull-down, so it latches low. The [author](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/docs/description.en.md) reports that the board works.
- The [datasheet, page 29](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) asks for 1 kΩ on EN_SWR (pin <a href="#wk-pin-60">60</a>). The board uses 4.7 kΩ (<a href="#wk-r14">R14</a>).
- EEPROM_MOD (pin <a href="#wk-pin-70">70</a>) and SMI_SEL (pin <a href="#wk-pin-81">81</a>) have no effect here, because there is no EEPROM and autoload
  is off (pin <a href="#wk-pin-76">76</a>).
- The YT9215S [configuration table, page 28](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=28) has no MID29 strap, so its slave SMI address is not set by a pin.

<a id="wk-led-pins"></a>
### LED pins with no strap in Table 15

| Pin | LED signal | Net | Resistor | Value | Pulls to | BOM line | Sheet |
|---|---|---|---|---|---|---|---|
| <a id="wk-pin-71"></a>71 | [P4LED1](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=24) | P4_LED1 | <a id="wk-r30"></a>R30 | 4.7 kΩ | 3V3 | <a href="#wk-bom-29">29</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |
| <a id="wk-pin-72"></a>72 | [P3LED1](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=24) | P3_LED1 | <a id="wk-r28"></a>R28 | 4.7 kΩ | GND | <a href="#wk-bom-29">29</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |
| <a id="wk-pin-77"></a>77 | [P2LED1](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=24) | P2_LED1 | <a id="wk-r20"></a>R20 | 4.7 kΩ | GND | <a href="#wk-bom-29">29</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |
| <a id="wk-pin-78"></a>78 | [P1LED1](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=24) | P1_LED1 | <a id="wk-r18"></a>R18 | 4.7 kΩ | 3V3 | <a href="#wk-bom-29">29</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |
| <a id="wk-pin-80"></a>80 | [P0LED1](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=25) | P0_LED1 | <a id="wk-r16"></a>R16 | 4.7 kΩ | 3V3 | <a href="#wk-bom-29">29</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |

| Column | Tag | Source |
|---|---|---|
| Net | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Resistor | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Value | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Pulls to | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| BOM line | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Sheet | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Pin | <a href="#tag-d">D</a> | [Table 7 on pages 24 to 25](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=24) |
| LED signal | <a href="#tag-d">D</a> | [Table 7 on pages 24 to 25](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=24) |

[Table 15 on pages 28 to 29](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=28) lists no strap on these five pins, so their pull direction only sets the LED polarity. The
datasheet is not consistent about them: its pin tables give a latched-input type to pin <a href="#wk-pin-71">71</a>
([page 25](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=25)), pin <a href="#wk-pin-77">77</a> ([page 28](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=28)) and pin <a href="#wk-pin-80">80</a> ([page 17](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=17)) without
naming a strap function.

<a id="wk-led-wiring"></a>
### LED wiring per port

| Port | Jack | LED0 pin | LED1 pin | Pin pull | LED0 series | LED1 series | Series value | Series BOM line | LED common | Drive | Sheet |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P0 | <a href="#wk-rj1">RJ1</a> | <a href="#wk-pin-81">81</a> | <a href="#wk-pin-80">80</a> | Up | <a id="wk-r21"></a>R21 | <a id="wk-r22"></a>R22 | 470 Ω | <a href="#wk-bom-30">30</a> | 3V3 | Active low | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |
| P1 | <a href="#wk-rj2">RJ2</a> | <a href="#wk-pin-79">79</a> | <a href="#wk-pin-78">78</a> | Up | <a id="wk-r23"></a>R23 | <a id="wk-r24"></a>R24 | 470 Ω | <a href="#wk-bom-30">30</a> | 3V3 | Active low | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |
| P2 | <a href="#wk-rj3">RJ3</a> | <a href="#wk-pin-75">75</a> | <a href="#wk-pin-77">77</a> | Down | <a id="wk-r25"></a>R25 | <a id="wk-r26"></a>R26 | 470 Ω | <a href="#wk-bom-30">30</a> | GND | Active high | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |
| P3 | <a href="#wk-rj4">RJ4</a> | <a href="#wk-pin-74">74</a> | <a href="#wk-pin-72">72</a> | Down | <a id="wk-r31"></a>R31 | <a id="wk-r32"></a>R32 | 470 Ω | <a href="#wk-bom-30">30</a> | GND | Active high | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |
| P4 | <a href="#wk-rj5">RJ5</a> | <a href="#wk-pin-70">70</a> | <a href="#wk-pin-71">71</a> | Up | <a id="wk-r33"></a>R33 | <a id="wk-r34"></a>R34 | 470 Ω | <a href="#wk-bom-30">30</a> | 3V3 | Active low | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) |

| Column | Tag | Source |
|---|---|---|
| Port | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Jack | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| LED0 pin | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| LED1 pin | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| LED0 series | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| LED1 series | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Series value | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Series BOM line | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| LED common | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Sheet | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Pin pull | <a href="#tag-r">R</a> | <a href="#wk-configuration-pins">Configuration pins</a> |
| Drive | <a href="#tag-i">I</a> | The rail the LED common is on |

The pull direction on each LED0 pin is fixed by the strap level the designer wanted, so the LEDs on ports 2 and 3 are wired
to ground and driven high, and the others are wired to 3V3 and driven low. The LED1 pin of each port is pulled the same way
as its LED0 pin. The LED mode is parallel: pins <a href="#wk-pin-80">80</a> and <a href="#wk-pin-81">81</a>, which are also the
[serial LED pins, page 25](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=25), drive jack LEDs directly.

<a id="wk-what-the-strapping-selects"></a>
### What the strapping selects

| Strap | Pin | Level | Tag |
|---|---|---|---|
| [DISAUTOLOAD](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | <a href="#wk-pin-76">76</a> | 1 | <a href="#tag-r">R</a> |
| [DIS_MCU](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | <a href="#wk-pin-75">75</a> | 0 | <a href="#tag-r">R</a> |
| [EN_SPIF](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | <a href="#wk-pin-74">74</a> | 0 | <a href="#tag-r">R</a> |
| [SMI_SEL](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=29) | <a href="#wk-pin-81">81</a> | 1 | <a href="#tag-r">R</a> |

| Result | Value | Tag |
|---|---|---|
| Loads from | Nothing | <a href="#tag-i">I</a> |
| Loads to | Nothing | <a href="#tag-i">I</a> |
| MCU | Enabled with no boot source | <a href="#tag-i">I</a> |

The YT9215S datasheet has no boot-mode table, so the result uses [Table 25 of the YT9215SCH datasheet, on pages 33 to 34](../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf#page=33),
which describes the same straps (inferred to apply). DISAUTOLOAD (pin <a href="#wk-pin-76">76</a>) = 1 falls in its "Others" row, which loads nothing. Nothing is loaded
at reset and the switch runs on its register defaults as an unmanaged five-port switch.

<a id="wk-other-pins"></a>
### Reset and unconnected pins

| Pin | Group | Net | Test point | Sheet |
|---|---|---|---|---|
| <a id="wk-pin-86"></a>86 | Reset | NRST | <a href="#wk-tp15">TP15</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-19"></a>19 | Interrupt | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-35"></a>35 | SerDes | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-36"></a>36 | SerDes | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-38"></a>38 | SerDes | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-39"></a>39 | SerDes | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a href="#wk-pin-45">45</a> | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a href="#wk-pin-46">46</a> | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a href="#wk-pin-47">47</a> | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a href="#wk-pin-48">48</a> | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a href="#wk-pin-49">49</a> | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a href="#wk-pin-50">50</a> | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-51"></a>51 | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-52"></a>52 | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-53"></a>53 | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-54"></a>54 | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-55"></a>55 | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-56"></a>56 | Extension port | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-87"></a>87 | I²C | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-88"></a>88 | I²C | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-15"></a>15 | No connect | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a id="wk-pin-16"></a>16 | No connect | Unconnected | None | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |

All columns are tagged <a href="#tag-r">R</a> from [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet). With the extension port, the SerDes, the I²C pins and the interrupt pin all
unconnected, there is no management interface on the board. Pins <a href="#wk-pin-15">15</a> and <a href="#wk-pin-16">16</a> are NC pins that the [datasheet, page 32](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf#page=32)
says must be left floating.

| Ref | Role | Value | From | To | BOM line | Sheet |
|---|---|---|---|---|---|---|
| <a href="#wk-r13">R13</a> | Reset pull-up | 4.7 kΩ | NRST | 3V3 | <a href="#wk-bom-28">28</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a href="#wk-c51">C51</a> | Reset delay capacitor | 10 µF | NRST | GND | <a href="#wk-bom-6">6</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |
| <a href="#wk-d1">D1</a> | Reset discharge diode | – | NRST | 3V3 | <a href="#wk-bom-13">13</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) |

These three parts form the reset network on pin <a href="#wk-pin-86">86</a>. All columns are tagged <a href="#tag-r">R</a> except Role, which is tagged <a href="#tag-i">I</a>.

<a id="wk-major-components"></a>
### Major components

| Ref | Function | Part | Maker | Package | Value | BOM line | Sheet | Datasheet | LCSC |
|---|---|---|---|---|---|---|---|---|---|
| <a id="wk-u2"></a>U2 | Switch IC | YT9215S | Motorcomm | LQFP-128 with exposed pad | – | <a href="#wk-bom-34">34</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf) | – |
| <a id="wk-x1"></a>X1 | Crystal | XRCGB25M000F3M00R0 | Murata | 2.0 × 1.6 mm | 25 MHz | <a href="#wk-bom-36">36</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Murata_XRCGB_Crystal.pdf) | [C127893](https://www.lcsc.com/product-detail/C127893.html) |
| <a id="wk-c49"></a>C49 | Crystal load capacitor | 0603CG4R0B500NT | FH | 0603 | 4 pF | <a href="#wk-bom-11">11</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C507053](https://www.lcsc.com/product-detail/C507053.html) |
| <a id="wk-c50"></a>C50 | Crystal load capacitor | 0603CG4R0B500NT | FH | 0603 | 4 pF | <a href="#wk-bom-11">11</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C507053](https://www.lcsc.com/product-detail/C507053.html) |
| <a id="wk-u1"></a>U1 | 3.3 V buck regulator | MT2492 | Xi'an Aerosemi | SOT-23-6 | – | <a href="#wk-bom-33">33</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Aerosemi_MT2492.pdf) | [C89358](https://www.lcsc.com/product-detail/C89358.html) |
| <a id="wk-l1"></a>L1 | Buck inductor | SWPA4030S4R7MT | Sunlord | 4 × 4 mm | 4.7 µH | <a href="#wk-bom-17">17</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Sunlord_SWPA_Series.pdf) | [C57269](https://jlcpcb.com/partdetail/C57269) |
| <a id="wk-r1"></a>R1 | Buck feedback top resistor | 0402WGF1802TCE | Uni-Royal | 0402 | 18 kΩ | <a href="#wk-bom-21">21</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C25762](https://www.lcsc.com/product-detail/C25762.html) |
| <a id="wk-r4"></a>R4 | Buck feedback bottom resistor | 0402WGF2001TCE | Uni-Royal | 0402 | 2 kΩ | <a href="#wk-bom-23">23</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C4109](https://www.lcsc.com/product-detail/C4109.html) |
| <a id="wk-r3"></a>R3 | Buck feedback bottom resistor | 0402WGF2001TCE | Uni-Royal | 0402 | 2 kΩ | <a href="#wk-bom-23">23</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C4109](https://www.lcsc.com/product-detail/C4109.html) |
| <a id="wk-l2"></a>L2 | Core regulator inductor | SWPA4018S2R2MT | Sunlord | 4 × 4 mm | 2.2 µH | <a href="#wk-bom-18">18</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Sunlord_SWPA_Series.pdf) | [C50543](https://jlcpcb.com/partdetail/C50543) |
| <a id="wk-r5"></a>R5 | Core rail link to AVDDL | RS-06000JT | FH | 1206 | 0 Ω | <a href="#wk-bom-24">24</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/FH_RS_Chip_Resistor_Series.pdf) | [C115323](https://www.lcsc.com/product-detail/C115323.html) |
| <a id="wk-r6"></a>R6 | Core rail link to DVDDL | RS-06000JT | FH | 1206 | 0 Ω | <a href="#wk-bom-24">24</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/FH_RS_Chip_Resistor_Series.pdf) | [C115323](https://www.lcsc.com/product-detail/C115323.html) |
| <a id="wk-l3"></a>L3 | Ferrite bead to AVDDH | BLM18KG221SN1D | Murata | 0603 | – | <a href="#wk-bom-19">19</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Murata_BLM18KG_Series.pdf) | [C88980](https://www.lcsc.com/product-detail/C88980.html) |
| <a id="wk-l4"></a>L4 | Ferrite bead to HV_SWR | BLM18KG221SN1D | Murata | 0603 | – | <a href="#wk-bom-19">19</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Murata_BLM18KG_Series.pdf) | [C88980](https://www.lcsc.com/product-detail/C88980.html) |
| <a id="wk-l5"></a>L5 | Ferrite bead to DVDDIO_2 | BLM18KG221SN1D | Murata | 0603 | – | <a href="#wk-bom-19">19</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Murata_BLM18KG_Series.pdf) | [C88980](https://www.lcsc.com/product-detail/C88980.html) |
| <a id="wk-l6"></a>L6 | Ferrite bead to DVDDIO | BLM18KG221SN1D | Murata | 0603 | – | <a href="#wk-bom-19">19</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Murata_BLM18KG_Series.pdf) | [C88980](https://www.lcsc.com/product-detail/C88980.html) |
| <a id="wk-l7"></a>L7 | Ferrite bead to SVDDH | BLM18KG221SN1D | Murata | 0603 | – | <a href="#wk-bom-19">19</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Murata_BLM18KG_Series.pdf) | [C88980](https://www.lcsc.com/product-detail/C88980.html) |
| <a id="wk-l8"></a>L8 | Ferrite bead to SVDDL | BLM18KG221SN1D | Murata | 0603 | – | <a href="#wk-bom-19">19</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Murata_BLM18KG_Series.pdf) | [C88980](https://www.lcsc.com/product-detail/C88980.html) |
| <a id="wk-l9"></a>L9 | Ferrite bead to PLLVDDL | BLM18KG221SN1D | Murata | 0603 | – | <a href="#wk-bom-19">19</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Murata_BLM18KG_Series.pdf) | [C88980](https://www.lcsc.com/product-detail/C88980.html) |
| <a id="wk-l10"></a>L10 | Ferrite bead to PLLGND | BLM18KG221SN1D | Murata | 0603 | – | <a href="#wk-bom-19">19</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Murata_BLM18KG_Series.pdf) | [C88980](https://www.lcsc.com/product-detail/C88980.html) |
| <a id="wk-rj1"></a>RJ1 | Port 0 RJ45 jack | HR911130A | HanRun | Through-hole | – | <a href="#wk-bom-31">31</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | [PDF](../datasheets/components/HanRun_HR911130A.pdf) | [C54408](https://www.lcsc.com/product-detail/C54408.html) |
| <a id="wk-rj2"></a>RJ2 | Port 1 RJ45 jack | HR911130A | HanRun | Through-hole | – | <a href="#wk-bom-31">31</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | [PDF](../datasheets/components/HanRun_HR911130A.pdf) | [C54408](https://www.lcsc.com/product-detail/C54408.html) |
| <a id="wk-rj3"></a>RJ3 | Port 2 RJ45 jack | HR911130A | HanRun | Through-hole | – | <a href="#wk-bom-31">31</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | [PDF](../datasheets/components/HanRun_HR911130A.pdf) | [C54408](https://www.lcsc.com/product-detail/C54408.html) |
| <a id="wk-rj4"></a>RJ4 | Port 3 RJ45 jack | HR911130A | HanRun | Through-hole | – | <a href="#wk-bom-31">31</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | [PDF](../datasheets/components/HanRun_HR911130A.pdf) | [C54408](https://www.lcsc.com/product-detail/C54408.html) |
| <a id="wk-rj5"></a>RJ5 | Port 4 RJ45 jack | HR911130A | HanRun | Through-hole | – | <a href="#wk-bom-31">31</a> | [P2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/2_P2.kicad_sch) | [PDF](../datasheets/components/HanRun_HR911130A.pdf) | [C54408](https://www.lcsc.com/product-detail/C54408.html) |
| <a id="wk-usb1"></a>USB1 | USB-C power input | TYPE-C 6P(040新) | Shou Han | SMD 6-pin | – | <a href="#wk-bom-35">35</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/ShouHan_TYPE-C-6P.pdf) | [C2887422](https://www.lcsc.com/product-detail/C2887422.html) |
| <a id="wk-r9"></a>R9 | USB-C CC1 pull-down | 0603WAF5101T5E | Uni-Royal | 0603 | 5.1 kΩ | <a href="#wk-bom-27">27</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C23186](https://www.lcsc.com/product-detail/C23186.html) |
| <a id="wk-r10"></a>R10 | USB-C CC2 pull-down | 0603WAF5101T5E | Uni-Royal | 0603 | 5.1 kΩ | <a href="#wk-bom-27">27</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C23186](https://www.lcsc.com/product-detail/C23186.html) |
| <a id="wk-dc1"></a>DC1 | Barrel jack input | DC-005-20A | Hroparts | Through-hole | – | <a href="#wk-bom-14">14</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Hroparts_DC-005-20A.pdf) | [C136744](https://www.lcsc.com/product-detail/C136744.html) |
| <a id="wk-f1"></a>F1 | Input resettable fuse | BSMD1206-075-30V | BHFuse | 1206 | – | <a href="#wk-bom-15">15</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | [C976305](https://www.lcsc.com/product-detail/C976305.html) |
| <a id="wk-h1"></a>H1 | 3V3 header | PZ254V-11-02P | XFCN | 2-pin 2.54 mm | – | <a href="#wk-bom-16">16</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/XFCN_PZ254V-11-02P.pdf) | [C492401](https://www.lcsc.com/product-detail/C492401.html) |
| <a id="wk-led1"></a>LED1 | Power LED | NCD0603W1 | Nationstar | 0603 | – | <a href="#wk-bom-20">20</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Nationstar_NCD0603W1.pdf) | [C84265](https://www.lcsc.com/product-detail/C84265.html) |
| <a id="wk-r8"></a>R8 | Power LED series resistor | 0603WAF1500T5E | Uni-Royal | 0603 | 150 Ω | <a href="#wk-bom-26">26</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C22808](https://www.lcsc.com/product-detail/C22808.html) |
| <a id="wk-r13"></a>R13 | Reset pull-up | 0603WAF4701T5E | Uni-Royal | 0603 | 4.7 kΩ | <a href="#wk-bom-28">28</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C23162](https://www.lcsc.com/product-detail/C23162.html) |
| <a id="wk-c51"></a>C51 | Reset delay capacitor | 0805X106K250NT | FH | 0805 | 10 µF | <a href="#wk-bom-6">6</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C40894](https://www.lcsc.com/product-detail/C40894.html) |
| <a id="wk-d1"></a>D1 | Reset discharge diode | 1N4148WQ | Yangjie | SOD-123 | – | <a href="#wk-bom-13">13</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | [PDF](../datasheets/components/Yangjie_1N4148WQ.pdf) | [C2942441](https://jlcpcb.com/partdetail/C2942441) |
| <a id="wk-tp1"></a>TP1 | Test point on 3V3 | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp2"></a>TP2 | Test point on VBUS | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp3"></a>TP3 | Test point on VDDL | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp4"></a>TP4 | Test point on AVDDH | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp5"></a>TP5 | Test point on AVDDL | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp6"></a>TP6 | Test point on HV_SWR | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp7"></a>TP7 | Test point on DVDDL | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp8"></a>TP8 | Test point on DVDDIO_2 | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp9"></a>TP9 | Test point on DVDDIO | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp10"></a>TP10 | Test point on SVDDH | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp11"></a>TP11 | Test point on SVDDL | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp12"></a>TP12 | Test point on PLLVDDL | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp13"></a>TP13 | Test point on PLLGND | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp14"></a>TP14 | Test point on DISAUTOLOAD | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp15"></a>TP15 | Test point on NRST | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |
| <a id="wk-tp16"></a>TP16 | Test point on EN_SWR | – | – | 0.5 mm pad | – | <a href="#wk-bom-32">32</a> | [P1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/kicad/1_P1.kicad_sch) | – | – |

| Column | Tag | Source |
|---|---|---|
| Ref | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Part | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Maker | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Package | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Value | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| BOM line | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| LCSC | <a href="#tag-r">R</a> | [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv) |
| Sheet | <a href="#tag-r">R</a> | [netlist-schematic.enet](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/schematic/netlist-schematic.enet) |
| Function | <a href="#tag-i">I</a> | The nets the part connects to |
| Datasheet | <a href="#tag-i">I</a> | The maker datasheet for the BOM part number |

Four cells do not come from the BOM. The part fitted as <a href="#wk-u2">U2</a>, its maker and its package are from the
[author's description](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/docs/description.en.md) and the [YT9215S datasheet](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf). The 25 MHz value of <a href="#wk-x1">X1</a> is
decoded from its part number.

- <a href="#wk-bom-34">BOM line 34</a> names the RTL8367S-CG of the <a href="#wk-u2">U2</a> schematic symbol, not the YT9215S that is fitted.
- There is no PoE circuitry, no flash, no EEPROM and no external MCU in the <a href="#wk-bom">BOM</a>.
- The magnetics are inside the HR911130A jacks (<a href="#wk-rj1">RJ1</a> to <a href="#wk-rj5">RJ5</a>), which also hold the two LEDs per port.
- <a href="#wk-u1">U1</a> has a 0.6 V feedback reference ([datasheet, page 1](../datasheets/components/Aerosemi_MT2492.pdf#page=1)). With <a href="#wk-r1">R1</a> (18 kΩ) over <a href="#wk-r4">R4</a> and
  <a href="#wk-r3">R3</a> in series (4 kΩ), the output is 0.6 V × (1 + 18 / 4) = 3.3 V.
- The 1.1 V core rail comes from <a href="#wk-u2">U2</a>'s internal switching regulator through <a href="#wk-l2">L2</a>. Two 0 Ω links,
  <a href="#wk-r5">R5</a> and <a href="#wk-r6">R6</a>, feed it to the AVDDL and DVDDL nets.
- Each ferrite bead feeds the net named in its Function cell. <a href="#wk-l3">L3</a> is fed from 3V3. <a href="#wk-l4">L4</a> is fed from 3V3. <a href="#wk-l5">L5</a> is fed from 3V3. <a href="#wk-l6">L6</a> is fed from 3V3. <a href="#wk-l7">L7</a> is fed from 3V3. <a href="#wk-l8">L8</a> is fed from VDDL. <a href="#wk-l9">L9</a> is fed from AVDDL. <a href="#wk-l10">L10</a> is fed from GND.
- <a href="#wk-usb1">USB1</a> is power only: 5.1 kΩ on each CC pin (<a href="#wk-r9">R9</a> and <a href="#wk-r10">R10</a>) and no data pins.

<a id="wk-bom"></a>
### All BOM lines

One row per line of [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv). The Line column links to that line of the file. The designators of every line are listed
under <a href="#wk-designators">Designators</a>.

| Line | Quantity | Part | Maker | Package | Value | Datasheet | LCSC |
|---|---|---|---|---|---|---|---|
| <a id="wk-bom-1"></a>[1](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L2) | 1 | 0402B223K500NT | FH | 0402 | 22 nF | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C1532](https://www.lcsc.com/product-detail/C1532.html) |
| <a id="wk-bom-2"></a>[2](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L3) | 2 | RVT1E221M0607 | Roqang | 6.3 mm can | 220 µF | [PDF](../datasheets/components/Roqang_RVT_Series.pdf) | [C2918361](https://www.lcsc.com/product-detail/C2918361.html) |
| <a id="wk-bom-3"></a>[3](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L4) | 2 | CL05B104KO5NNNC | Samsung | 0402 | 100 nF | [PDF](../datasheets/components/Samsung_CL_MLCC_Series.pdf) | [C1525](https://www.lcsc.com/product-detail/C1525.html) |
| <a id="wk-bom-4"></a>[4](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L5) | 1 | CL05B103KB5NNNC | Samsung | 0402 | 10 nF | [PDF](../datasheets/components/Samsung_CL_MLCC_Series.pdf) | [C15195](https://www.lcsc.com/product-detail/C15195.html) |
| <a id="wk-bom-5"></a>[5](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L6) | 1 | 0402CG220J500NT | FH | 0402 | 22 pF | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C1555](https://www.lcsc.com/product-detail/C1555.html) |
| <a id="wk-bom-6"></a>[6](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L7) | 10 | 0805X106K250NT | FH | 0805 | 10 µF | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C40894](https://www.lcsc.com/product-detail/C40894.html) |
| <a id="wk-bom-7"></a>[7](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L8) | 27 | 0603B103K500NT | FH | 0603 | 10 nF | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C57112](https://www.lcsc.com/product-detail/C57112.html) |
| <a id="wk-bom-8"></a>[8](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L9) | 2 | 0603B104K500NT | FH | 0603 | 100 nF | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C30926](https://www.lcsc.com/product-detail/C30926.html) |
| <a id="wk-bom-9"></a>[9](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L10) | 2 | 0603B105K500NT | FH | 0603 | 1 µF | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C90540](https://www.lcsc.com/product-detail/C90540.html) |
| <a id="wk-bom-10"></a>[10](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L11) | 1 | 0603B102K500NT | FH | 0603 | 1 nF | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C44369](https://www.lcsc.com/product-detail/C44369.html) |
| <a id="wk-bom-11"></a>[11](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L12) | 2 | 0603CG4R0B500NT | FH | 0603 | 4 pF | [PDF](../datasheets/components/FH_MLCC_Series.pdf) | [C507053](https://www.lcsc.com/product-detail/C507053.html) |
| <a id="wk-bom-12"></a>[12](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L13) | 5 | FN15X104K250PNG | PSA | 0402 | 100 nF | [PDF](../datasheets/components/PSA_FN_MLCC_Series.pdf) | [C525225](https://www.lcsc.com/product-detail/C525225.html) |
| <a id="wk-bom-13"></a>[13](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L14) | 1 | 1N4148WQ | Yangjie | SOD-123 | – | [PDF](../datasheets/components/Yangjie_1N4148WQ.pdf) | [C2942441](https://jlcpcb.com/partdetail/C2942441) |
| <a id="wk-bom-14"></a>[14](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L15) | 1 | DC-005-20A | Hroparts | Through-hole | – | [PDF](../datasheets/components/Hroparts_DC-005-20A.pdf) | [C136744](https://www.lcsc.com/product-detail/C136744.html) |
| <a id="wk-bom-15"></a>[15](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L16) | 1 | BSMD1206-075-30V | BHFuse | 1206 | – | – | [C976305](https://www.lcsc.com/product-detail/C976305.html) |
| <a id="wk-bom-16"></a>[16](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L17) | 1 | PZ254V-11-02P | XFCN | 2-pin 2.54 mm | – | [PDF](../datasheets/components/XFCN_PZ254V-11-02P.pdf) | [C492401](https://www.lcsc.com/product-detail/C492401.html) |
| <a id="wk-bom-17"></a>[17](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L18) | 1 | SWPA4030S4R7MT | Sunlord | 4 × 4 mm | 4.7 µH | [PDF](../datasheets/components/Sunlord_SWPA_Series.pdf) | [C57269](https://jlcpcb.com/partdetail/C57269) |
| <a id="wk-bom-18"></a>[18](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L19) | 1 | SWPA4018S2R2MT | Sunlord | 4 × 4 mm | 2.2 µH | [PDF](../datasheets/components/Sunlord_SWPA_Series.pdf) | [C50543](https://jlcpcb.com/partdetail/C50543) |
| <a id="wk-bom-19"></a>[19](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L20) | 8 | BLM18KG221SN1D | Murata | 0603 | – | [PDF](../datasheets/components/Murata_BLM18KG_Series.pdf) | [C88980](https://www.lcsc.com/product-detail/C88980.html) |
| <a id="wk-bom-20"></a>[20](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L21) | 1 | NCD0603W1 | Nationstar | 0603 | – | [PDF](../datasheets/components/Nationstar_NCD0603W1.pdf) | [C84265](https://www.lcsc.com/product-detail/C84265.html) |
| <a id="wk-bom-21"></a>[21](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L22) | 1 | 0402WGF1802TCE | Uni-Royal | 0402 | 18 kΩ | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C25762](https://www.lcsc.com/product-detail/C25762.html) |
| <a id="wk-bom-22"></a>[22](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L23) | 1 | 0402WGF1002TCE | Uni-Royal | 0402 | 10 kΩ | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C25744](https://www.lcsc.com/product-detail/C25744.html) |
| <a id="wk-bom-23"></a>[23](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L24) | 2 | 0402WGF2001TCE | Uni-Royal | 0402 | 2 kΩ | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C4109](https://www.lcsc.com/product-detail/C4109.html) |
| <a id="wk-bom-24"></a>[24](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L25) | 2 | RS-06000JT | FH | 1206 | 0 Ω | [PDF](../datasheets/components/FH_RS_Chip_Resistor_Series.pdf) | [C115323](https://www.lcsc.com/product-detail/C115323.html) |
| <a id="wk-bom-25"></a>[25](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L26) | 1 | RC0402FR-072K49L | Yageo | 0402 | 2.49 kΩ | [PDF](../datasheets/components/Yageo_RC_Chip_Resistor_Series.pdf) | [C145071](https://www.lcsc.com/product-detail/C145071.html) |
| <a id="wk-bom-26"></a>[26](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L27) | 1 | 0603WAF1500T5E | Uni-Royal | 0603 | 150 Ω | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C22808](https://www.lcsc.com/product-detail/C22808.html) |
| <a id="wk-bom-27"></a>[27](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L28) | 2 | 0603WAF5101T5E | Uni-Royal | 0603 | 5.1 kΩ | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C23186](https://www.lcsc.com/product-detail/C23186.html) |
| <a id="wk-bom-28"></a>[28](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L29) | 4 | 0603WAF4701T5E | Uni-Royal | 0603 | 4.7 kΩ | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C23162](https://www.lcsc.com/product-detail/C23162.html) |
| <a id="wk-bom-29"></a>[29](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L30) | 10 | 0402WGF4701TCE | Uni-Royal | 0402 | 4.7 kΩ | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C25900](https://www.lcsc.com/product-detail/C25900.html) |
| <a id="wk-bom-30"></a>[30](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L31) | 10 | 0402WGF4700TCE | Uni-Royal | 0402 | 470 Ω | [PDF](../datasheets/components/UniRoyal_Chip_Resistor_Series.pdf) | [C25117](https://www.lcsc.com/product-detail/C25117.html) |
| <a id="wk-bom-31"></a>[31](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L32) | 5 | HR911130A | HanRun | Through-hole | – | [PDF](../datasheets/components/HanRun_HR911130A.pdf) | [C54408](https://www.lcsc.com/product-detail/C54408.html) |
| <a id="wk-bom-32"></a>[32](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L33) | 16 | – | – | 0.5 mm pad | – | – | – |
| <a id="wk-bom-33"></a>[33](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L34) | 1 | MT2492 | Xi'an Aerosemi | SOT-23-6 | – | [PDF](../datasheets/components/Aerosemi_MT2492.pdf) | [C89358](https://www.lcsc.com/product-detail/C89358.html) |
| <a id="wk-bom-34"></a>[34](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L35) | 1 | RTL8367S-CG | Realtek | LQFP-128 | – | – | [C2760849](https://www.lcsc.com/product-detail/C2760849.html) |
| <a id="wk-bom-35"></a>[35](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L36) | 1 | TYPE-C 6P(040新) | Shou Han | SMD 6-pin | – | [PDF](../datasheets/components/ShouHan_TYPE-C-6P.pdf) | [C2887422](https://www.lcsc.com/product-detail/C2887422.html) |
| <a id="wk-bom-36"></a>[36](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv?plain=1#L37) | 1 | XRCGB25M000F3M00R0 | Murata | 2.0 × 1.6 mm | – | [PDF](../datasheets/components/Murata_XRCGB_Crystal.pdf) | [C127893](https://www.lcsc.com/product-detail/C127893.html) |

All columns are tagged <a href="#tag-r">R</a> from [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv), except Datasheet, which is tagged <a href="#tag-i">I</a>: it is the maker datasheet for the part number.

- No datasheet is available for the exact BSMD1206-075-30V fuse (<a href="#wk-f1">F1</a>, <a href="#wk-bom-15">line 15</a>).
- The RTL8367S-CG datasheet (<a href="#wk-bom-34">line 34</a>) is marked confidential by Realtek, so it is linked from
  [datasheets/README.md](../datasheets/README.md#realtek-linked-not-included) and not copied.
- Four LCSC numbers ([C57269](https://jlcpcb.com/partdetail/C57269), [C50543](https://jlcpcb.com/partdetail/C50543), [C2942441](https://jlcpcb.com/partdetail/C2942441) and [C495286](https://jlcpcb.com/partdetail/C495286)) have no page on lcsc.com. Their links go to the JLCPCB page for
  the same number.

<a id="wk-designators"></a>
### Designators

One row per designator in [bom.csv](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/bom/bom.csv). A linked designator goes to the table that describes it.

| Designator | BOM line | Part | Value |
|---|---|---|---|
| <a id="wk-c1"></a>C1 | <a href="#wk-bom-1">1</a> | 0402B223K500NT | 22 nF |
| <a id="wk-c2"></a>C2 | <a href="#wk-bom-2">2</a> | RVT1E221M0607 | 220 µF |
| <a id="wk-c6"></a>C6 | <a href="#wk-bom-2">2</a> | RVT1E221M0607 | 220 µF |
| <a id="wk-c3"></a>C3 | <a href="#wk-bom-3">3</a> | CL05B104KO5NNNC | 100 nF |
| <a id="wk-c7"></a>C7 | <a href="#wk-bom-3">3</a> | CL05B104KO5NNNC | 100 nF |
| <a id="wk-c4"></a>C4 | <a href="#wk-bom-4">4</a> | CL05B103KB5NNNC | 10 nF |
| <a id="wk-c5"></a>C5 | <a href="#wk-bom-5">5</a> | 0402CG220J500NT | 22 pF |
| <a id="wk-c8"></a>C8 | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a id="wk-c11"></a>C11 | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a id="wk-c12"></a>C12 | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a id="wk-c13"></a>C13 | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a id="wk-c28"></a>C28 | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a id="wk-c37"></a>C37 | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a id="wk-c38"></a>C38 | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a id="wk-c41"></a>C41 | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a id="wk-c43"></a>C43 | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a href="#wk-c51">C51</a> | <a href="#wk-bom-6">6</a> | 0805X106K250NT | 10 µF |
| <a id="wk-c9"></a>C9 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c14"></a>C14 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c15"></a>C15 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c16"></a>C16 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c17"></a>C17 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c18"></a>C18 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c19"></a>C19 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c20"></a>C20 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c21"></a>C21 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c22"></a>C22 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c23"></a>C23 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c24"></a>C24 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c25"></a>C25 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c26"></a>C26 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c27"></a>C27 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c30"></a>C30 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c31"></a>C31 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c32"></a>C32 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c33"></a>C33 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c34"></a>C34 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c35"></a>C35 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c36"></a>C36 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c39"></a>C39 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c40"></a>C40 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c42"></a>C42 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c44"></a>C44 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c45"></a>C45 | <a href="#wk-bom-7">7</a> | 0603B103K500NT | 10 nF |
| <a id="wk-c10"></a>C10 | <a href="#wk-bom-8">8</a> | 0603B104K500NT | 100 nF |
| <a id="wk-c46"></a>C46 | <a href="#wk-bom-8">8</a> | 0603B104K500NT | 100 nF |
| <a id="wk-c29"></a>C29 | <a href="#wk-bom-9">9</a> | 0603B105K500NT | 1 µF |
| <a id="wk-c47"></a>C47 | <a href="#wk-bom-9">9</a> | 0603B105K500NT | 1 µF |
| <a id="wk-c48"></a>C48 | <a href="#wk-bom-10">10</a> | 0603B102K500NT | 1 nF |
| <a href="#wk-c49">C49</a> | <a href="#wk-bom-11">11</a> | 0603CG4R0B500NT | 4 pF |
| <a href="#wk-c50">C50</a> | <a href="#wk-bom-11">11</a> | 0603CG4R0B500NT | 4 pF |
| <a id="wk-c52"></a>C52 | <a href="#wk-bom-12">12</a> | FN15X104K250PNG | 100 nF |
| <a id="wk-c53"></a>C53 | <a href="#wk-bom-12">12</a> | FN15X104K250PNG | 100 nF |
| <a id="wk-c54"></a>C54 | <a href="#wk-bom-12">12</a> | FN15X104K250PNG | 100 nF |
| <a id="wk-c55"></a>C55 | <a href="#wk-bom-12">12</a> | FN15X104K250PNG | 100 nF |
| <a id="wk-c56"></a>C56 | <a href="#wk-bom-12">12</a> | FN15X104K250PNG | 100 nF |
| <a href="#wk-d1">D1</a> | <a href="#wk-bom-13">13</a> | 1N4148WQ | – |
| <a href="#wk-dc1">DC1</a> | <a href="#wk-bom-14">14</a> | DC-005-20A | – |
| <a href="#wk-f1">F1</a> | <a href="#wk-bom-15">15</a> | BSMD1206-075-30V | – |
| <a href="#wk-h1">H1</a> | <a href="#wk-bom-16">16</a> | PZ254V-11-02P | – |
| <a href="#wk-l1">L1</a> | <a href="#wk-bom-17">17</a> | SWPA4030S4R7MT | 4.7 µH |
| <a href="#wk-l2">L2</a> | <a href="#wk-bom-18">18</a> | SWPA4018S2R2MT | 2.2 µH |
| <a href="#wk-l3">L3</a> | <a href="#wk-bom-19">19</a> | BLM18KG221SN1D | – |
| <a href="#wk-l4">L4</a> | <a href="#wk-bom-19">19</a> | BLM18KG221SN1D | – |
| <a href="#wk-l5">L5</a> | <a href="#wk-bom-19">19</a> | BLM18KG221SN1D | – |
| <a href="#wk-l6">L6</a> | <a href="#wk-bom-19">19</a> | BLM18KG221SN1D | – |
| <a href="#wk-l7">L7</a> | <a href="#wk-bom-19">19</a> | BLM18KG221SN1D | – |
| <a href="#wk-l8">L8</a> | <a href="#wk-bom-19">19</a> | BLM18KG221SN1D | – |
| <a href="#wk-l9">L9</a> | <a href="#wk-bom-19">19</a> | BLM18KG221SN1D | – |
| <a href="#wk-l10">L10</a> | <a href="#wk-bom-19">19</a> | BLM18KG221SN1D | – |
| <a href="#wk-led1">LED1</a> | <a href="#wk-bom-20">20</a> | NCD0603W1 | – |
| <a href="#wk-r1">R1</a> | <a href="#wk-bom-21">21</a> | 0402WGF1802TCE | 18 kΩ |
| <a id="wk-r2"></a>R2 | <a href="#wk-bom-22">22</a> | 0402WGF1002TCE | 10 kΩ |
| <a href="#wk-r3">R3</a> | <a href="#wk-bom-23">23</a> | 0402WGF2001TCE | 2 kΩ |
| <a href="#wk-r4">R4</a> | <a href="#wk-bom-23">23</a> | 0402WGF2001TCE | 2 kΩ |
| <a href="#wk-r5">R5</a> | <a href="#wk-bom-24">24</a> | RS-06000JT | 0 Ω |
| <a href="#wk-r6">R6</a> | <a href="#wk-bom-24">24</a> | RS-06000JT | 0 Ω |
| <a id="wk-r7"></a>R7 | <a href="#wk-bom-25">25</a> | RC0402FR-072K49L | 2.49 kΩ |
| <a href="#wk-r8">R8</a> | <a href="#wk-bom-26">26</a> | 0603WAF1500T5E | 150 Ω |
| <a href="#wk-r9">R9</a> | <a href="#wk-bom-27">27</a> | 0603WAF5101T5E | 5.1 kΩ |
| <a href="#wk-r10">R10</a> | <a href="#wk-bom-27">27</a> | 0603WAF5101T5E | 5.1 kΩ |
| <a href="#wk-r11">R11</a> | <a href="#wk-bom-28">28</a> | 0603WAF4701T5E | 4.7 kΩ |
| <a href="#wk-r12">R12</a> | <a href="#wk-bom-28">28</a> | 0603WAF4701T5E | 4.7 kΩ |
| <a href="#wk-r13">R13</a> | <a href="#wk-bom-28">28</a> | 0603WAF4701T5E | 4.7 kΩ |
| <a href="#wk-r14">R14</a> | <a href="#wk-bom-28">28</a> | 0603WAF4701T5E | 4.7 kΩ |
| <a href="#wk-r15">R15</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r16">R16</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r17">R17</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r18">R18</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r19">R19</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r20">R20</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r27">R27</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r28">R28</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r29">R29</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r30">R30</a> | <a href="#wk-bom-29">29</a> | 0402WGF4701TCE | 4.7 kΩ |
| <a href="#wk-r21">R21</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-r22">R22</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-r23">R23</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-r24">R24</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-r25">R25</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-r26">R26</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-r31">R31</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-r32">R32</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-r33">R33</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-r34">R34</a> | <a href="#wk-bom-30">30</a> | 0402WGF4700TCE | 470 Ω |
| <a href="#wk-rj1">RJ1</a> | <a href="#wk-bom-31">31</a> | HR911130A | – |
| <a href="#wk-rj2">RJ2</a> | <a href="#wk-bom-31">31</a> | HR911130A | – |
| <a href="#wk-rj3">RJ3</a> | <a href="#wk-bom-31">31</a> | HR911130A | – |
| <a href="#wk-rj4">RJ4</a> | <a href="#wk-bom-31">31</a> | HR911130A | – |
| <a href="#wk-rj5">RJ5</a> | <a href="#wk-bom-31">31</a> | HR911130A | – |
| <a href="#wk-tp1">TP1</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp2">TP2</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp3">TP3</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp4">TP4</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp5">TP5</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp6">TP6</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp7">TP7</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp8">TP8</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp9">TP9</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp10">TP10</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp11">TP11</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp12">TP12</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp13">TP13</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp14">TP14</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp15">TP15</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-tp16">TP16</a> | <a href="#wk-bom-32">32</a> | – | – |
| <a href="#wk-u1">U1</a> | <a href="#wk-bom-33">33</a> | MT2492 | – |
| <a href="#wk-u2">U2</a> | <a href="#wk-bom-34">34</a> | RTL8367S-CG | – |
| <a href="#wk-usb1">USB1</a> | <a href="#wk-bom-35">35</a> | TYPE-C 6P(040新) | – |
| <a href="#wk-x1">X1</a> | <a href="#wk-bom-36">36</a> | XRCGB25M000F3M00R0 | – |
