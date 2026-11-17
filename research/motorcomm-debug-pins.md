# Motorcomm switch ICs: JTAG, SPI flash and UART pins

Researched 2026-11-16. Covers the YT9215 family (S, SC/SCH, RB). Tags: **[V]** verified in a datasheet or netlist, **[I]** inferred, **[C]** conflicting between sources.

## Headline findings

1. **The three YT9215 variants have three different pinouts.** Each one is a pin-for-pin drop-in for a different Realtek part. The Motorcomm selection guide (2023-03-08, [`attachments/裕太微电子产品选型20230308.pdf`](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/attachments/%E8%A3%95%E5%A4%AA%E5%BE%AE%E7%94%B5%E5%AD%90%E4%BA%A7%E5%93%81%E9%80%89%E5%9E%8B20230308.pdf) in the board repo) says so **[V]**:
   - YT9215S matches the RTL8367S;
   - YT9215RB matches the RTL8367RB-VB;
   - YT9215SC/SCH matches the RTL8367SC.

   So pin numbers from one variant's datasheet **cannot** be used for another. [`switch-embedded-cpu.md`](switch-embedded-cpu.md) (2026-10-22) quoted YT9215SC pin numbers and said the S has "the same LQFP-128 pinout family". That is wrong for pin numbers. The XTAL pins show it: they are 83/84 on the S, 87/88 on the SC and 89/90 on the RB.
2. **Every YT9215 variant has the RISC-V MCU** **[V]**. The selection guide marks S, RB and SC all "内置RISC-V" (built-in RISC-V). The S and RB datasheets both list "Integrated RISC-V microprocessor", the `DIS_MCU` strap, SPI flash, two UARTs and two JTAG groups. This corrects the memory note that only the SC has the CPU.
3. **The newest datasheet drops JTAG.** The 2025 YT9215SCH datasheet (V1.03, 2025-02-10) removed every JTAG pin name. The same pins are now listed as GPIO, LED and I²C only. UART and SPI-flash pins remain. Either Motorcomm stopped documenting JTAG or it is disabled in production silicon **[I]**. Treat JTAG as unconfirmed until it has been probed.
4. **The 2025 SCH datasheet is the first public MCU description** **[V]**:
   - 64 KB SRAM, 16 KB boot ROM and 2 KB I-cache.
   - SPI NOR flash up to 8 MB, single or dual I/O, 3-byte addressing.
   - Boot modes: execute in place (XIP) from flash, flash→RAM, or EEPROM→RAM.

## YT9215S (RTL8367S pinout, used on the mirrored board)

Sources: YT9215S Datasheet Draft_01 (2022-11-08, [`attachments/YT9215S_Datasheet_draft_V0.1.pdf`](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/attachments/YT9215S_Datasheet_draft_V0.1.pdf) in the repo). Also Draft_05 (2023-02-21) on [LCSC/szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20230829/432918AE041FF2F1E459558942DE4628.pdf). Both drafts give the same pin numbers **[V]**.

The board netlist (`schematic/netlist-schematic.enet`) uses an RTL8367S-CG symbol. It has XTAL on 83/84 and nRESET on 86, and the author reports it boots with a YT9215S fitted. That confirms the shipping S silicon uses this pinout **[V]**.

### SPI flash

One interface. The `SPF_MUX_SEL` strap on pin 48 picks which pins it uses. Pin 48 has an internal pull-down, and pull-down selects **SPF1**.

| Group | Signal | Pin | GPIO | Other function | Strap on pin |
|---|---|---|---|---|---|
| SPF0 | SCK | 48 | GPIO9 | RGMII TXD0 | `SPF_MUX_SEL` |
| SPF0 | SI | 49 | GPIO10 | RGMII TXCTL | – |
| SPF0 | SO | 53 | GPIO14 | RGMII RXD0 | – |
| SPF0 | CS# | 54 | GPIO15 | RGMII RXD1 | – |
| SPF1 | SCK | 77 | GPIO40 | P2LED1 | – |
| SPF1 | SI | 71 | GPIO34 | P4LED1 | – |
| SPF1 | SO | 72 | GPIO35 | P3LED1 | – |
| SPF1 | CS# | 76 | GPIO39 | – | `DISAUTOLOAD` |

| Group | Pin 48 level | Default |
|---|---|---|
| SPF0 | Pulled up | No |
| SPF1 | Low | Yes |

| Signal | Driven by | Flash pin | Flash I/O name |
|---|---|---|---|
| SI | Chip | DI | IO0 |
| SO | Flash | DO | IO1 |

- `EN_SPIF` (pin 74, GPIO37/P3LED0) is the enable strap: pull up to enable **[V]**.
- SPF0 takes over the extension-port RGMII/MII pins. If the adapter's MCU link uses that port, flash has to go on SPF1 **[I]**.
- **Strap clash [I]:** on SPF1, CS# is the `DISAUTOLOAD` strap pin. The usual CS# pull-up therefore latches DISAUTOLOAD=1. In the SCH boot table that means "no action", so nothing would load. This needs a bench test, or a pull-down on CS# during reset. The S datasheet has no boot-mode table, so this conclusion borrows the SCH table.

### JTAG (two groups, both shared with LEDs and straps) [V]

| Group | Signal | Pin | GPIO | Other function | Strap on pin |
|---|---|---|---|---|---|
| JTAG0 | TCK | 73 | GPIO36 | – | `EN_PWRLIGHT` |
| JTAG0 | TMS | 79 | GPIO44 | JTAG1 TCK | `EN_PHY` |
| JTAG0 | TDI | 81 | GPIO46 | LED_CK | `SMI_SEL` |
| JTAG0 | TDO | 80 | GPIO45 | LED_DA | – |
| JTAG1 | TCK | 79 | GPIO44 | JTAG0 TMS | `EN_PHY` |
| JTAG1 | TMS | 71 | GPIO34 | P4LED1 | – |
| JTAG1 | TDI | 72 | GPIO35 | P3LED1 | – |
| JTAG1 | TDO | 77 | GPIO40 | P2LED1 | – |

- Pin 79 is listed as both JTAG1_TCK and JTAG0_TMS in both drafts. The two groups cannot be used at once **[V]**.
- JTAG1 uses the same pins as SPF1 (71/72/77), so it cannot coexist with flash on SPF1 **[I]**.
- There is no TRST and no pin that selects JTAG. Whether the pins become JTAG after reset, or only after a register write, is not documented. The same is true of whether they reach the RISC-V debug module or only boundary scan **[I]**.

### UART

| UART | Signal | Pin | GPIO | Other function | Strap on pin | Evidence |
|---|---|---|---|---|---|---|
| UART0 | RX | 45 | GPIO6 | RGMII TXD3 | SWITCH_ID_1 | – |
| UART0 | TX | 46 | GPIO7 | RGMII TXD2 | – | – |
| UART1 | RX | 19 | GPIO2 | INTERRUPT | – | – |
| UART1 | TX | 75 | GPIO38 | P2LED0 | `DIS_MCU` | – |
| UART2 | RX | 73 | GPIO36 | – | `EN_PWRLIGHT` | – |
| UART2 | TX | 75 | GPIO38 | UART1 TX (same pin) | `DIS_MCU` | **[C]** |

- UART0 appears in the pin table of both drafts and in the Draft_05 UART table. The Draft_01 UART table leaves it out.
- On the RTL8367S symbol, pins 45/46 are labelled UART_RX/UART_TX. So UART0 is the Realtek-compatible console position **[V]**.
- TX on 75 for both UART1 and UART2 is what the datasheet says. It is probably a typo for one of them **[C]**.

### Other boot-related straps (S)

- Pin 75 `DIS_MCU`: pull-up disables the MCU.
- Pin 76 `DISAUTOLOAD`.
- Pin 70 `EEPROM_MOD`: selects EEPROM size above or at most 16 Kbit.
- I²C EEPROM: SCL on 87, SDA on 88 (GPIO48/49, also the slave MDC/MDIO).

### How the mirrored board wires these pins [V, from the netlist]

| Pin | Signal 1 | Signal 2 | Signal 3 | Board net | Strap resistor | Value | Pulls to | LED resistor | Test point | Strap level | Effect |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 45 | UART0 RX (console) | – | – | **None** | – | – | – | – | **No pad** | — | – |
| 46 | UART0 TX (console) | – | – | **None** | – | – | – | – | **No pad** | — | – |
| 19 | UART1 RX | – | – | None | – | – | – | – | – | — | – |
| 48 | SPF_MUX_SEL | – | – | None | Internal | – | GND | – | – | 0 | SPF1 selected |
| 74 | EN_SPIF | – | – | P3_LED0 | R27 | 4.7 k | GND | R31 | – | 0 | Flash off |
| 75 | DIS_MCU | UART1 TX | UART2 TX | P2_LED0 | R19 | 4.7 k | GND | R25 | – | 0 | **MCU enabled** |
| 76 | DISAUTOLOAD | SPF1_CS | – | DISAUTOLOAD | R11 | 4.7 k | 3V3 | – | TP14 | 1 | No autoload |
| 73 | JTAG0_TCK | UART2_RX | – | EN_PWRLIGHT | R12 | 4.7 k | 3V3 | – | – | 1 | – |
| 79 | JTAG1_TCK | JTAG0_TMS | – | P1_LED0 | R17 | – | 3V3 | R23 | – | 1 | – |
| 80 | JTAG0_TDO | – | – | P0_LED1 | R16 | – | 3V3 | R22 | – | 1 | – |
| 81 | JTAG0_TDI | – | – | P0_LED0 | R15 | – | 3V3 | R21 | – | 1 | – |
| 71 | JTAG1_TMS | SPF1_SI | – | P4_LED1 | R30 | – | 3V3 | R34 | – | 1 | – |
| 72 | JTAG1_TDI | SPF1_SO | – | P3_LED1 | R28 | – | GND | R32 | – | 0 | – |
| 77 | JTAG1_TDO | SPF1_SCK | – | P2_LED1 | R20 | – | GND | R26 | – | 0 | – |
| 87 | EEPROM I²C | – | – | None | – | – | – | – | – | — | – |
| 88 | EEPROM I²C | – | – | None | – | – | – | – | – | — | – |

What the wiring means:
- The board runs with the MCU **enabled** but with no flash and no EEPROM. In the SCH table, DISAUTOLOAD=1 is "no action". So the MCU probably sits in its boot ROM doing nothing **[I]**.
- To probe JTAG0 or JTAG1, or UART2 (RX 73 / TX 75), lift the 470 Ω LED resistors and tap the 4.7 k strap pads. Leaving the LEDs on loads TCK and TDO **[I]**.
- UART0 has no pad, so it means soldering to the LQFP leads 45/46.

## YT9215SC / YT9215SCH (RTL8367SC pinout, LQFP-128 with EPAD)

Sources: [YT9215SC Draft_07, 2023-02-28](https://atta.szlcsc.com/upload/public/pdf/source/20251231/E8DA45036F659501F9799590211A88C7.pdf) and [YT9215SCH V1.03, 2025-02-10](https://atta.szlcsc.com/upload/public/pdf/source/20251231/76B4B53D0DFB99DA2607FBF198C74D22.pdf).

| Function | Signal | Pin | Strap on pin | Evidence | Documents | Note |
|---|---|---|---|---|---|---|
| SPF0 | SCK | 49 | `SPF_MUX_SEL` | **[V]** | – | Pull-up selects SPF0 |
| SPF0 | SI | 50 | – | **[V]** | – | – |
| SPF0 | SO | 54 | – | **[V]** | – | – |
| SPF0 | CS | 55 | – | **[V]** | – | – |
| SPF1 (default) | SO | 78 | – | **[V]** | Both | – |
| SPF1 (default) | SI | 79 | – | **[V]** | Both | – |
| SPF1 (default) | CS | 81 | – | **[V]** | Both | – |
| SPF1 (default) | SCK | 83 | – | **[V]** | Both | – |
| Strap | EN_SPIF | 75 | EN_SPIF | **[V]** | – | – |
| Strap | DIS_MCU | 76 | DIS_MCU | **[V]** | – | – |
| Strap | DISAUTOLOAD | 77 | DISAUTOLOAD | **[V]** | – | – |
| UART0 | RX | 46 | – | **[V]** | Both | – |
| UART0 | TX | 47 | – | **[V]** | Both | – |
| UART1 | RX | 70 | DIS_SPIS | **[V]** | Both | – |
| UART1 | TX | 76 | DIS_MCU | **[V]** | Both | – |
| JTAG0 | TCK | 73 | – | – | Draft_07 only | **Removed in V1.03** |
| JTAG0 | TMS | 72 | – | – | Draft_07 only | **Removed in V1.03** |
| JTAG0 | TDI | 74 | – | – | Draft_07 only | **Removed in V1.03** |
| JTAG0 | TDO | 90 | – | – | Draft_07 only | **Removed in V1.03** |
| JTAG1 | TCK | 83 | – | – | Draft_07 only | **Removed in V1.03** |
| JTAG1 | TMS | 81 | – | – | Draft_07 only | **Removed in V1.03** |
| JTAG1 | TDI | 84 | – | – | Draft_07 only | **Removed in V1.03** |
| JTAG1 | TDO | 67 | – | – | Draft_07 only | **Removed in V1.03** |
| EEPROM and slave I²C | SCL | 91 | – | – | – | – |
| EEPROM and slave I²C | SDA | 92 | – | – | – | – |
| Slave SPI | – | 90–93 | – | – | – | – |

SCH V1.03 boot table (Table 25) **[V]**:

| DISAUTOLOAD | DIS_MCU | EN_SPIF | DIS_SPIS | SMI_SEL | Loads from | Loads to | Note |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 1 | 1 | EEPROM | MCU RAM | – |
| 0 | 0 | 1 | X | X | **SPI flash** | **XIP** | – |
| 0 | 1 | 0 | X | X | EEPROM | Registers | – |
| 0 | 1 | 1 | X | X | Flash | RAM | As printed **[C]** |
| others | | | | | no action | – | – |

The last flash row is odd, because it loads RAM with the MCU disabled.

## YT9215RB (RTL8367RB-VB pinout)

Source: [YT9215RB Draft_05, 2023-02-16 (LCSC)](https://datasheet.lcsc.com/datasheet/pdf/762da1ba434211a9b4be1fec673c7fcf.pdf?productCode=C5449202) **[V]**.

| Function | Signal | Pin | Strap on pin |
|---|---|---|---|
| SPF0 | SCK | 44 | `SPF_MUX_SEL` |
| SPF0 | SI | 45 | – |
| SPF0 | SO | 49 | – |
| SPF0 | CS | 50 | – |
| SPF1 | SO | 80 | – |
| SPF1 | SI | 81 | – |
| SPF1 | CS | 83 | – |
| SPF1 | SCK | 84 | – |
| JTAG0 | TCK | 75 | – |
| JTAG0 | TMS | 74 | – |
| JTAG0 | TDI | 76 | – |
| JTAG0 | TDO | 92 | – |
| JTAG1 | TCK | 84 | – |
| JTAG1 | TMS | 83 | – |
| JTAG1 | TDI | 85 | – |
| JTAG1 | TDO | 20 | – |
| UART0 | RX | 41 | – |
| UART0 | TX | 42 | – |
| UART1 | RX | 72 | – |
| UART1 | TX | 78 | `DIS_MCU` |
| Strap | EN_SPIF | 77 | EN_SPIF |
| Strap | DIS_MCU | 78 | DIS_MCU |
| Strap | DISAUTOLOAD | 79 | DISAUTOLOAD |

## Other Motorcomm parts

- YT8512, YT8521, YT8531 and YT8821 are plain PHYs. The selection guide lists no CPU for any of them. They have MDIO, LEDs and straps, with no JTAG, UART or flash interface. These pin lists were not checked in detail, because nothing debug-related is there to find.
- YT8614 (a QSGMII PHY) is the same.
- YT9218N/MB, an 8-port relative, is in the Linux driver's chip table. No datasheet was checked for it.
- The Linux driver (`drivers/net/dsa/motorcomm/chip.c`) identifies variants by `CHIP_ID` 0x80008 (major 0x9002 = YT9215) plus `CHIP_MODE`: 1 = SC, 2 = S, 3 = RB.
- The latched strap values can be read back over MDIO from `PON_STRAP_VAL` (0x80324). This gives a way to check DIS_MCU/EN_SPIF levels on real hardware **[V]**.

## Community and SDK status

- No public firmware, SDK, OpenOCD config, boot-ROM dump or forum write-up was found for the YT9215 MCU. Searches covered English and Chinese terms.
- The image format and signing for flash or EEPROM boot are still unknown.

## Implications for the adapter

- If we use the YT9215S, strap `DIS_MCU` (pin 75) high as planned and leave `EN_SPIF` low. That is the opposite of the mirrored board, which leaves the MCU enabled.
- To keep a debug option open cheaply, put 0402 pads on:
  - pins 45/46 (UART0);
  - pins 73/75 (UART2);
  - the JTAG0 set 73/79/80/81.

  Most of these already carry strap resistors, so a test pad per net costs almost nothing.
- A first bench experiment on the mirrored board needs no new PCB:
  1. Tie DIS_MCU low, as the board already does.
  2. Scan JTAG0 at R12/R17/R16/R15 after lifting R21/R22/R23 for an IDCODE.
  3. Listen on UART0 (pins 45/46) and UART2 for boot-ROM output.

## Photographed LX-IS601F V2.0 boards (added 2026-11-16)

Tim's photographed boards (silkscreen LX-IS601F V2.0) carry a **YT9215SCH**, not a YT9215S, so the SC/SCH pin numbers above apply, not the S numbers **[V, chip marking on two boards]**. Annotated photo: [`lx-is601f-board/lx-is601f-debug-pins-annotated.png`](lx-is601f-board/lx-is601f-debug-pins-annotated.png).

Pin 1 is the lead beside the small dimple; pins 65–96 face the crystal Y6, pins 33–64 face R44/R89/R92/R93. Traced from top-side photos only **[I]**:

| Function | Signal | Pin | Where it lands | Part | Note |
|---|---|---|---|---|---|
| UART0 | RX | 46 | No trace (chip lead only) | – | – |
| UART0 | TX | 47 | No trace (chip lead only) | – | – |
| UART1 | RX | 70 | Via just above the chip | – | – |
| UART1 | TX | 76 | Via just above the chip | – | Also DIS_MCU |
| SPF1 | SCK | 83 | Via | – | – |
| SPF1 | SI | 79 | No trace | – | – |
| SPF1 | SO | 78 | Via | – | – |
| SPF1 | CS | 81 | Via | – | – |
| SPF0 | SCK | 49 | Chip-side resistor pad | R93 | – |
| SPF0 | SI | 50 | Chip-side resistor pad | R92 | – |
| SPF0 | SO | 54 | Chip-side resistor pad | R89 | – |
| SPF0 | CS | 55 | Chip-side resistor pad | R44 | – |
| JTAG0 | TCK | 73 | LED trace | – | 2023 draft name |
| JTAG0 | TMS | 72 | LED trace | – | 2023 draft name |
| JTAG0 | TDI | 74 | Via | – | 2023 draft name |
| JTAG0 | TDO | 90 | No trace | – | 2023 draft name |
| JTAG1 | TCK | 83 | Via | – | 2023 draft name |
| JTAG1 | TMS | 81 | Via | – | 2023 draft name |
| JTAG1 | TDI | 84 | Via | – | 2023 draft name |
| JTAG1 | TDO | 67 | No trace | – | 2023 draft name |
| Strap | EN_SPIF | 75 | Via | – | – |
| Strap | DIS_MCU | 76 | Via | – | – |
| Strap | DISAUTOLOAD | 77 | Via | – | – |

Not known: where the vias go on other layers, strap levels, and what the far pads of R44/R89/R92/R93 connect to. A bottom-side photo and a continuity check would settle these. One oddity: pin 86 (AVDDH in the datasheet) appears to run to R22 beside the crystal, which was not resolved.
