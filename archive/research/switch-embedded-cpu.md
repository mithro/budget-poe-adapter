# Embedded CPUs in the switch ICs

> **Archived.** This note is not part of the current design. It assumes an external MCU and recommends strapping the switch CPU off. The current design uses only the YT9215 switch IC and its internal RISC-V CPU. What is known about the YT9215 CPU is in [`yt9215-embedded-cpu.md`](../../research/yt9215-embedded-cpu.md). The [archive index](../README.md) lists every archived note.

> **Which YT9215 variants have the CPU:** Motorcomm's product page lists the embedded RISC-V CPU only for the **YT9215SC**, the YT9218N and the YT9218MB, while the selection guide and the YT9215S, YT9215SC and YT9215RB datasheets all list it (see [`switch-cpu-dev-boards.md`](switch-cpu-dev-boards.md) and [`motorcomm-debug-pins.md`](../../research/motorcomm-debug-pins.md)). The core is probably on every die but supported only on the SC. Plan any CPU work on the YT9215SC.

Sources were read on 2026-10-22. This note looks at the CPU inside each candidate switch chip and asks whether it could run our own firmware and replace, or shrink, the external MCU (RP2040-class or CH32X035) in the PoE → USB-C adapter. It builds on [`switch-detail-comparison.md`](switch-detail-comparison.md) and [`ethernet-switch-comparison.md`](ethernet-switch-comparison.md) and does not repeat the datasheet basics given there.

<a id="evidence-codes"></a>
Each statement is marked with one of these evidence codes:

- **V** verified: read directly in a cited source (datasheet, GPL source, Linux source, mailing list).
- **D** derived: worked out by static disassembly of a GPL-published 8051 blob (Keil C51 output). I read the bytes but did not run them. Treat these as strong evidence, not as documentation.
- **I** inference: a judgement from family similarity or general knowledge.
- **VD**: verified in a cited source and also derived from the disassembly.
- **VI**: part verified in a cited source, part inference.

## TL;DR

- **RTL8367S: the CPU is a Synopsys DesignWare DW8051, and it is far more reachable than the datasheet suggests.**
  - The GPL `rtl8367c` vendor driver documents how to load it: hold it in reset, open an 8 KB instruction-RAM window at switch registers 0xE000–0xFFFF, write the bytes, release reset. The same driver ships three ready-made 8051 programs. [**V**](#evidence-codes)
  - Disassembling one of those programs shows:
    - the 8051 reads and writes every switch register through SFRs 0xA0–0xA7, the same mechanism the RTL8372 and RTL8373 8051 uses, which the RTLPlayground project already drives from SDCC;
    - the core clock is selectable between 20.8, 62.5, 100, 125 and 200 MHz. [**D**](#evidence-codes)
  - There is no signing, encryption or header: the code is raw 8051 machine code. [**VD**](#evidence-codes)
  - It is technically capable of running management firmware with a small TCP/IP stack and LLDP, but there is no public memory map, NIC description or boot-image format. It has no USB.
- **YT9215S: the CPU is a Nuclei N205** (RV32IMAC-class, 2-stage pipeline) according to a Nuclei and Motorcomm press piece. [**V**](#evidence-codes)
  - The YT9215SC datasheet shows two JTAG pin groups, two UARTs, I²C and MDIO masters and an SPI flash port. [**V**](#evidence-codes)
  - Clock, memory sizes, boot format and SDK are all unpublished. No firmware dumps or community work exist. Linux only knows it as "MCU port 10". [**V**](#evidence-codes)
  - Using it would mean bring-up from scratch through JTAG.
- **RTL8363NB: no usable CPU. Confirmed.** [**V**](#evidence-codes)
  - Its datasheet never mentions an 8051 and has no DIS_8051, SPI-flash or UART pins. Its only CPU references are to an *external* CPU.
  - It does belong to the same RTL8367C register family, so a dormant DW8051 on the die can't be ruled out. [**I**](#evidence-codes) Even then it could only be loaded by an external host over SMI, so it is useless here.
- **Recommendation: keep the external MCU.**
  - None of these CPUs has USB or a USB-PD PHY.
  - Only the RTL8367S's 8051 is realistically programmable, and getting there means reverse-engineering effort measured in weeks.
  - Strap the embedded CPUs off, as the design plans.
  - The RTL8367S 8051 is worth a later side project only if the MCU's job ever shrinks to LLDP and switch configuration, with USB-PD handled by a fixed-function controller.

## Summary table

|  | RTL8367S-CG | RTL8367S-CG evidence | YT9215S | YT9215S evidence | RTL8363NB-VB-CG | RTL8363NB-VB-CG evidence |
| --- | --- | --- | --- | --- | --- | --- |
| CPU core | Synopsys DesignWare DW8051 | [**V**](#evidence-codes) | Nuclei N205 ("RISC-V 205") | [**V**](#evidence-codes) | None in datasheet | [**V**](#evidence-codes) |
| CPU core source | – |  | Press article (not the datasheet) |  | – |  |
| ISA | MCS-51 (8051) | [**V**](#evidence-codes) | RV32IMAC-class | [**VI**](#evidence-codes) | None |  |
| ISA options | – |  | N200 series is RV32IEMACB-configurable |  | – |  |
| Clocks per machine cycle | 4 | [**V**](#evidence-codes) | – |  | – |  |
| Speed per clock vs classic 8051 | About 2.4× | [**V**](#evidence-codes) | – |  | – |  |
| CPU clock | Selectable | [**D**](#evidence-codes) | Unknown |  | None |  |
| CPU clock estimate | – |  | ≤125 MHz | [**I**](#evidence-codes) | – |  |
| CPU clock option 1 | 200 MHz | [**D**](#evidence-codes) | – |  | – |  |
| CPU clock option 2 | 125 MHz | [**D**](#evidence-codes) | – |  | – |  |
| CPU clock option 3 | 100 MHz | [**D**](#evidence-codes) | – |  | – |  |
| CPU clock option 4 | 62.5 MHz | [**D**](#evidence-codes) | – |  | – |  |
| CPU clock option 5 | 20.8 MHz | [**D**](#evidence-codes) | – |  | – |  |
| CPU clock select field | DW8051_RATE | [**D**](#evidence-codes) | – |  | – |  |
| CPU clock select register | 0x1336 | [**D**](#evidence-codes) | – |  | – |  |
| CPU clock select bits | 6:4 | [**D**](#evidence-codes) | – |  | – |  |
| CPU clock reset default | Unknown |  | – |  | – |  |
| Switch core clock | – |  | 125 MHz | [**V**](#evidence-codes) | – |  |
| Switch core clock source | – |  | 8 ns cycle in yt921x driver |  | – |  |
| Code memory | Instruction RAM loaded at boot |  | Unknown |  | None |  |
| Code memory size | 16–32 KB | [**VI**](#evidence-codes) | Unknown |  | None |  |
| Code memory window | 8 KB |  | – |  | – |  |
| Code memory page field | IROM_MSB (2 bits) |  | – |  | – |  |
| Code memory options | – |  | N200: configurable local SRAM | [**VI**](#evidence-codes) | – |  |
| Instruction cache | – |  | N200: optional | [**VI**](#evidence-codes) | – |  |
| EEPROM autoload size | 32 KB (matches the code size) |  | – |  | – |  |
| Internal RAM | 256 B (DW8051 standard) | [**I**](#evidence-codes) | Unknown |  | None |  |
| XDATA size | Unknown |  | – |  | – |  |
| XDATA used by vendor blob | Up to ≥0x0630 | [**D**](#evidence-codes) | – |  | – |  |
| Boot from EEPROM | Yes | [**V**](#evidence-codes) | – |  | None |  |
| Boot EEPROM type | 24Cxx |  | – |  | – |  |
| Boot from SPI flash | Yes | [**V**](#evidence-codes) | Yes | [**V**](#evidence-codes) | None |  |
| Boot from host over SMI | Yes | [**V**](#evidence-codes) | – |  | None |  |
| Boot source select | Strap |  | – |  | – |  |
| Boot target | "Embedded 8051 Instruction Memory" |  | – |  | – |  |
| SPI flash interfaces | – |  | 1 | [**V**](#evidence-codes) | – |  |
| SPI flash pin positions | – |  | 2 | [**V**](#evidence-codes) | – |  |
| SPI flash pin select | – |  | SPF_MUX_SEL |  | – |  |
| SPI flash single I/O | – |  | Yes |  | – |  |
| SPI flash dual I/O | – |  | Yes |  | – |  |
| SPI flash image format | – |  | Unknown |  | – |  |
| Image format | Raw 8051 code at address 0 | [**VD**](#evidence-codes) | Unknown |  | None |  |
| Header (SMI loading) | None | [**VD**](#evidence-codes) | Unknown |  | None |  |
| Checksum (SMI loading) | None | [**VD**](#evidence-codes) | Unknown |  | None |  |
| Signature (SMI loading) | None | [**VD**](#evidence-codes) | Unknown |  | None |  |
| Boot image framing | Unknown |  | Unknown |  | None |  |
| Switch register access | Whole space via SFR bus | [**D**](#evidence-codes) | – |  | None |  |
| Packet path to CPU | Internal NIC | [**V**](#evidence-codes) | "MCU port 10" | [**V**](#evidence-codes) | None |  |
| Internal NIC registers | 0x1A00–0x1A5C | [**V**](#evidence-codes) | – |  | – |  |
| Trap to CPU | – |  | Trap-to-internal-CPU bit | [**V**](#evidence-codes) | None |  |
| Interrupt: link change | Yes | [**V**](#evidence-codes) | – |  | None |  |
| Interrupt: EEE-LLDP | Yes | [**V**](#evidence-codes) | – |  | None |  |
| Interrupt: loop detect | Yes | [**V**](#evidence-codes) | – |  | None |  |
| Interrupt: cable diag | Yes | [**V**](#evidence-codes) | – |  | None |  |
| Interrupt: ACL | Yes | [**V**](#evidence-codes) | – |  | None |  |
| Interrupt: others | Yes (list continues) | [**V**](#evidence-codes) | – |  | None |  |
| UART | Yes | [**VD**](#evidence-codes) | 2× | [**V**](#evidence-codes) | None |  |
| I²C master | Yes | [**VD**](#evidence-codes) | Yes | [**V**](#evidence-codes) | None |  |
| I²C master type | Register-level |  | – |  | – |  |
| I²C master pins | GPIOs |  | – |  | – |  |
| MDIO master | – |  | Yes | [**V**](#evidence-codes) | None |  |
| GPIO | Yes | [**VD**](#evidence-codes) | Yes | [**V**](#evidence-codes) | None |  |
| LEDs | – |  | Yes | [**V**](#evidence-codes) | None |  |
| Timers | 3 | [**VD**](#evidence-codes) | – |  | None |  |
| JTAG | – |  | ×2 | [**V**](#evidence-codes) | None |  |
| Host mailbox registers | 0x13A0–0x13A7 | [**V**](#evidence-codes) | – |  | None |  |
| Datasheet | Section exists |  | Draft only |  | Rev 1.2 |  |
| Datasheet CPU section | §9.17 "Embedded 8051" |  | – |  | – |  |
| CPU section body public? | No |  | – |  | – |  |
| Open API | GPL rtl8367c |  | – |  | GPL rtl8367c |  |
| Register header in the API | Full |  | – |  | – |  |
| Linux driver as a reference | – |  | yt921x |  | – |  |
| Leaked docs | Register table for RTL8367RB and RTL8367MB |  | – |  | – |  |
| Toolchain 1 | SDCC |  | GCC rv32imac | [**I**](#evidence-codes) | None |  |
| Toolchain 1 source | As used by RTLPlayground |  | Upstream |  | – |  |
| Toolchain 2 | Keil C51 |  | GCC rv32imac (Nuclei SDK) | [**I**](#evidence-codes) | None |  |
| Toolchain 2 source | Realtek's own |  | Nuclei SDK |  | – |  |
| Debugger | – |  | OpenOCD + JTAG | [**I**](#evidence-codes) | – |  |
| Community projects | 3 |  | None found |  | None |  |
| Community: RTLPlayground target 1 | RTL8372 |  | – |  | – |  |
| Community: RTLPlayground target 2 | RTL8373 |  | – |  | – |  |
| Community: RTLPlayground relevance | Same SFR scheme |  | – |  | – |  |
| Community: Yakigani | RTL8370 IROM loader |  | – |  | – |  |
| Community: Netgear "Plus" model 1 | GS105E |  | – |  | – |  |
| Community: Netgear "Plus" model 2 | GS308E |  | – |  | – |  |
| Community: Netgear "Plus" relevance | Firmware runs on this family's 8051 |  | – |  | – |  |
| User firmware feasible? | **Yes in principle** |  | **Unknown** |  | **No** |  |
| User firmware documented? | **No** |  | No |  | – |  |
| Effort | Medium-high |  | Very high |  | – |  |
| Replaces our MCU? | No |  | No |  | No |  |
| Has USB | No |  | No |  | – |  |
| Has a PD PHY | No |  | No |  | – |  |

A dash means not applicable or not stated.

## RTL8367S: DW8051

### Identity and memory

- **Core.** [**V**](#evidence-codes)
  - The datasheet feature list says "Integrated 8051 microprocessor", and the block diagram shows a "GNIC 8051" block ([RTL8367S-CG datasheet mirror](https://www.framboise314.fr/wp-content/uploads/2021/06/RTL8367S-CG_Datasheet.pdf)).
  - The Linux SGMII patch series and Realtek's own register names call it a **DW8051**:
    - `RTL8367C_REG_DW8051_RDY` 0x1336;
    - `DW8051_EN` in 0x130C;
    - `DW8051_RST` in 0x1322;
    - `DW8051_PRO_REG0..7` 0x13A0–0x13A7;
    - `DW8051_INT_CPU` 0x111A.
- **DW8051 core, from the Synopsys datasheet hosted by Keil** [**V**](#evidence-codes) ([dw8051_ds.pdf](https://www.keil.com/dd/docs/datashts/synopsys/dw8051_ds.pdf)):
  - 4 clocks per instruction cycle against 12 on a classic 8051, about 2.4× faster on average at the same clock;
  - 0–64 KB program ROM outside the core;
  - 128 or 256 B internal RAM;
  - 2–3 timers and 0–2 UARTs;
  - 6 or 13 interrupt sources;
  - dual DPTR and MOVX stretch;
  - an external SFR bus for custom peripherals.
- **Instruction memory.** [**V**](#evidence-codes)
  - The vendor driver maps the "lower bank of the instruction ROM" into switch-register space at 0xE000–0xFFFF, which is an 8 KB window (`RTL8365MB_IROM_SIZE 0x2000` in the Linux v2 patch).
  - `IROM_MSB` (0x1336 bits 3:2, a 2-bit field) selects the page.
  - The RTL8370 IROM loader Yakigani switches page when the address reaches 0x2000.
  - So the IROM holds at least 16 KB, and probably 32 KB with four pages. [**I**](#evidence-codes) That would match the "32K-byte EEPROM" autoload and the EEPROM → "8051 Instruction Memory" boot path.
  - It is RAM, written at every boot. [**V**](#evidence-codes)
- **Clock.** [**D**](#evidence-codes)
  - The vendor `Sgmii_Init` program reads register 0x1336, extracts bits 6:4 (`DW8051_RATE`) and picks a CPU frequency for its timer maths:
    - 0 → 200 MHz;
    - 1 → 125 MHz;
    - 2 → 100 MHz;
    - 4 → 62.5 MHz;
    - anything else → 20.8 MHz.
  - These are 32-bit constants 0x0BEBC200, 0x07735940, 0x05F5E100, 0x03B9ACA0 and 0x013D6200, divided by 12 × 200 to get a 5 ms Timer 0 tick.
  - The reset default of DW8051_RATE is unknown.
  - For comparison, RTLPlayground runs the RTL837x 8051 at 125 MHz ([rtlplayground.c](https://github.com/logicog/RTLPlayground)).
- **XDATA.** [**D**](#evidence-codes) The blob keeps counters in XDATA at 0x0624–0x0630, so there is at least about 1.6 KB of XDATA RAM. The real size is unknown. The RTL837x has 64 KB [**V**](#evidence-codes), but that is a newer chip.

### Boot flow

Evidence code for this section: [**V**](#evidence-codes).

The boot path is set by three straps, per datasheet §7.5 and Table 8:

| DISAUTOLOAD | DIS_8051 | EN_SPIF | Loads from | Loads to | Source part | Max size |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | EEPROM | 8051 instruction memory | 24Cxx | 32 KB |
| 0 | 0 | 1 | SPI flash | 8051 instruction memory | – | – |
| 1 | 0 (must be) | – | EEPROM | Registers | – | – |
| 1 | – | – | Nothing | – | – | – |

- SPI flash pins: SPIF_CLK, SPIF_D0, SPIF_D1 and SPIF_CS on pins 48, 49, 53 and 54. UART_RX and UART_TX are on pins 45 and 46.
- **Host-loaded path, as the vendor API and the Linux v2 patch do it:**
  1. Set CHIP_RESET.DW8051_RST.
  2. Set MISC_CFG0.DW8051_EN.
  3. Set DW8051_RDY.ACS_IROM_EN and clear IROM_MSB.
  4. Write one byte per register to 0xE000+i.
  5. Clear ACS_IROM_EN.
  6. Release reset.
- **Image format.**
  - The SMI-loaded image is a flat 8051 binary with the reset vector at 0x0000. `Sgmii_Init` starts `02 03 81`, which is `LJMP 0x0381`, the Keil startup. No header, no checksum, no signature. [**VD**](#evidence-codes)
  - What framing the EEPROM or SPI autoload expects (length prefix, checksum, banking) is **not documented anywhere public**.
  - RTL837x images start with a 2-byte prefetch length. [**V**](#evidence-codes) The older RTL8367N and GS105E v2 flash holds a bootloader at 0x0 and firmware at 0x1D000 in a 1 MB 25Q80 ([libc0607 GS105Ev2 notes](https://github.com/libc0607/RTL8370N_switch_hacking/blob/master/RTL8367N-GS105Ev2.md)). So this family can run code larger than the IROM from flash, probably through a loader. [**I**](#evidence-codes)
  - Expect to work out the RTL8367S format by dumping a retail "easy smart" switch built on the RTL8367S, or by trial.

### What the 8051 can reach

- **Switch registers via the SFR bus.** [**D**](#evidence-codes) The blob's register-access routines are:
  - read: `CLR EA; MOV 0xA2,addrH; MOV 0xA3,addrL; MOV 0xA0,#1; NOP×11; wait until SFR 0xA1 == 0; data = 0xA6:0xA7; SETB EA`;
  - write: address to 0xA2 and 0xA3, data to 0xA4 and 0xA5, `MOV 0xA0,#3`, poll 0xA1.

  This is the same scheme RTLPlayground uses on the RTL837x (`SFR_EXEC_GO` 0xA0 with 1 = read and 3 = write, `SFR_EXEC_STATUS` 0xA1, address 0xA2 and 0xA3, data 0xA4–0xA7; see [rtl837x_sfr.h](https://github.com/logicog/RTLPlayground)). RTLPlayground's register-access layer should therefore port almost directly. [**I**](#evidence-codes)

  The blob also touches CKCON (0x8E), which is DW8051-specific, plus Timer 0 and the interrupt registers.
- **Internal NIC.** [**V**](#evidence-codes) Registers 0x1A04–0x1A5C (`nic_reg`, in the GPL [rtl8367c_reg.h](https://github.com/hanwckf/immortalwrt-mt798x/tree/openwrt-21.02/target/linux/mediatek/files-5.4/drivers/net/phy/rtk/rtl8367c)) cover:
  - RX and TX ring and buffer pointers;
  - RX and TX command;
  - interrupt mask and status;
  - RX filters (unicast, multicast and broadcast, ARP, CRC, L3 and L4 checksum error);
  - TX loopback;
  - multicast hash.

  MISC_CFG0 has `NIC_ENABLE` and CHIP_RESET has `NIC_RST`. How packets reach 8051 memory (DMA into XDATA, or register windows) is **not documented**. [**I**](#evidence-codes) By analogy with the RTL837x, it is probably a ring buffer copied with an SFR-triggered DMA.
- **Interrupts to the 8051.** [**V**](#evidence-codes) `INTR_IMR_8051` (0x1118) covers:
  - link change;
  - meter exceeded;
  - learn-over;
  - speed change;
  - congestion;
  - green timer;
  - loop detection;
  - EEE-LLDP;
  - cable-diag finished;
  - SA moving;
  - ACL action.

  There are also per-port link-up and link-down indicators for the 8051 and a thermal interrupt. RLDP (Realtek loop detection) can be handed to the 8051 (`rtl8367c_setAsicRldpEnable8051`).
- **GPIO, I²C, UART, LEDs.** [**V**](#evidence-codes)
  - GPIO: `EN_GPIO`, `CTRL_GPIO`, `SEL_GPIO` and `STATUS_GPIO` at 0x1350 and 0x13C7–0x13C9.
  - I²C master: register-level, on GPIO pin groups, about 252 kHz by default (`rtk_i2c_init`, `I2C_CTRL` 0x1374, `I2C_CLOCK_DIV` 0x130A).
  - UART: enable bits in the register map.
  - LEDs: CPU-forced LED registers at 0x1B07+.
  - So the 8051 could drive an I²C USB-PD controller or a PoE PD chip's status pins. [**I**](#evidence-codes)
- **Host mailbox.** [**V**](#evidence-codes) `DW8051_PRO_REG0..7` (0x13A0–0x13A7) are scratch registers both sides can reach. Yakigani uses 0x13A4–0x13A7 to pass TFTP IP addresses to the RTL8370 boot loader.

### Performance

Evidence code for this section: [**I**](#evidence-codes).

- At 125 MHz the DW8051 runs about 31 M machine cycles per second, roughly 15–25 M 8-bit instructions per second.
- For 16- and 32-bit work that is somewhere between a 16 MHz AVR and a slow Cortex-M0. Each switch-register access costs about 20+ cycles.
- That is plenty for:
  - LLDP and LLDP-MED power negotiation;
  - a uIP-class IPv4 stack with ping, DHCP, a tiny HTTP page or a UDP config protocol;
  - link and LED supervision;
  - polling an I²C PD controller.

  RTLPlayground shows this on the same core design: uIP, DHCP, LLDP, LACP, STP, a web UI and a serial CLI, with ping under 10 ms.
- It cannot touch data-plane traffic. It only sees frames trapped to the CPU or NIC.
- It has no USB, so it cannot be the USB device.

### Software and docs

- **Vendor API (GPL).**
  - Realtek "rtl8367c" API, in OpenWrt and ImmortalWrt trees, for example [hanwckf/immortalwrt-mt798x …/rtk/rtl8367c](https://github.com/hanwckf/immortalwrt-mt798x/tree/openwrt-21.02/target/linux/mediatek/files-5.4/drivers/net/phy/rtk/rtl8367c).
  - The full register header has about 22,800 lines.
  - [`rtl8367c_asicdrv_port.c`](https://github.com/hanwckf/immortalwrt-mt798x/blob/openwrt-21.02/target/linux/mediatek/files-5.4/drivers/net/phy/rtk/rtl8367c/rtl8367c_asicdrv_port.c) and [`port.c`](https://github.com/hanwckf/immortalwrt-mt798x/blob/openwrt-21.02/target/linux/mediatek/files-5.4/drivers/net/phy/rtk/rtl8367c/port.c) contain the 8051 programs `Sgmii_Init` (1,183 B), `Fiber2_Auto`, `Fiber2_1G` and `Fiber2_100M` (about 2 KB each) and `Fiber` (1,507 B), with their loader.
  - The [Mercusys MR80X v2 GPL drop](https://ratatoskr.run/linux-firmware/2026/06/17116216/t) is cited as the source of the 1,233-byte variant.
- **Linux.**
  - Upstream `rtl8365mb` gained RTL8367S SGMII or HSGMII support in commit fcaf2221b970 (2026-07-22) ([cover letter thread](https://ratatoskr.run/lkml/2026/07/17247411/t)).
  - v2 of the series loaded the DW8051 firmware ([v2 patch](https://lkml.rescloud.iu.edu/hypermail/linux/kernel/2606.1/05986.html)). v3 and later keep the DW8051 **in reset**, because the firmware "only duplicates the link management phylink already performs".
  - The [linux-firmware MR 1092](https://ratatoskr.run/linux-firmware/2026/06/17116216/t) for `realtek/rtl8367s-sgmii.bin` is blocked on licensing: Realtek never published the 8051 source.
  - Practical lesson: Realtek's own 8051 code for this chip is tiny Keil-compiled polling loops.
- **Register docs.** There is a leaked [RTL8367RB and RTL8367MB Register Table V1.0.0](https://github.com/user-attachments/files/18147305/RTL8367RB_RTL8367MB_Register_Table_V1.0.0.pdf), linked from [libc0607/Realtek_switch_hacking](https://github.com/libc0607/Realtek_switch_hacking). That repo also holds `Realtek_Unmanaged_Switch_API_V1.3.12_20171124`.
  - A "Realtek Unmanaged Switch Programming Guide" exists on [Scribd](https://www.scribd.com/document/866635652/Realtek-Unmanaged-Switch-ProgrammingGuide-2). I couldn't read it, so its 8051 coverage is unknown.
  - No public document describes the 8051 memory map, SFRs, NIC data path or flash image format. The RTL8367S datasheet lists §9.17 "Embedded 8051", but the public copy has no body for it.
- **Community.**
  - [RTLPlayground](https://github.com/logicog/RTLPlayground) is GPL firmware for the RTL8372 and RTL8373 DW8051, built with SDCC 4.5. Its docs cover clock dividers, timers, UART and flash via SFRs, bank switching, the NIC data path and the RTL tag format ([doc/hardware.md, doc/CpuPort.md](https://github.com/logicog/RTLPlayground/tree/main/doc)).
  - [Yakigani](https://github.com/libc0607/Yakigani) is an RTL8370 IROM loader over bit-banged SMI using the same 0x1322, 0x130C, 0x1336, 0xE000 sequence.
  - The RTL8367N and RTL8370N GS105E and GS308E conversions prove that the family's 8051 runs vendor web-managed firmware from SPI flash ([OpenWrt forum](https://forum.openwrt.org/t/netgear-gs308e-v4-adding-support-for-rtl8370n-based-switches/221816)).
  - Nobody has published custom firmware for the RTL8367S and RTL8367C 8051 specifically.
- **Toolchain.** SDCC (`-mmcs51`) works. Keil C51 is what Realtek uses. Debugging is by UART printf or the SMI-loaded RAM image; no JTAG pins are known.

### Feasibility

Evidence code for this section: [**I**](#evidence-codes).

- **Fastest path to running code:**
  1. The external MCU or a USB-SMI dongle loads a ≤8–16 KB SDCC image into IROM over MDIO and releases reset, exactly as the vendor driver does.
  2. A UART "hello" plus register read and write through SFRs 0xA0–0xA7 should work in days.
- **The NIC data path, autoloading from EEPROM or SPI flash, and the real XDATA size all need reverse engineering**, by dumping a commercial RTL8367S smart switch's flash, or by porting RTLPlayground's NIC code and probing. Estimate weeks, with no guarantee.
- **No secure boot.** None was seen for SMI-loaded code.

## YT9215S: Nuclei N205 RISC-V

### Identity

Evidence code for this section: [**VI**](#evidence-codes).

- **Core.** A Nuclei (芯来) press release says Motorcomm's YT9215 series embeds the **Nuclei RISC-V N205** core, used for "lightweight remote management and cloud management" ([riscv-mcu.com, 2022-10-18](https://www.riscv-mcu.com/article-show-id-929.html); Motorcomm's own [launch news](https://en.motor-comm.com/news/26.html) just says "built-in RISC-V processor").
  - N200 series: 32-bit, 2-stage variable-length pipeline, RV32IEMACB-configurable, configurable ILM and DLM SRAM and I-cache, Nuclei ECLIC interrupt controller.
  - The same N205 ("Bumblebee") core in the GD32VF103 gives 153 DMIPS and 360 CoreMark at 108 MHz, about 1.4 DMIPS/MHz and 3.3 CoreMark/MHz ([GigaDevice](https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core)).
  - Which extensions Motorcomm configured is unknown.
- **Clock, memory, boot ROM: unknown.**
  - The yt921x driver reads a `SYS_CLK` register: the default gives an 8 ns (125 MHz) switch cycle on YT9215, with 143 MHz and others selectable. [**V**](#evidence-codes)
  - The MCU probably runs from this clock or a divider of it. [**I**](#evidence-codes)

### Boot and pins

Evidence code for this section: [**V**](#evidence-codes).

> The pin numbers in this section are for the **YT9215SC** only. The YT9215S (RTL8367S pinout), the YT9215SC (RTL8367SC pinout) and the YT9215RB (RTL8367RB-VB pinout) are pinned differently, and all three have the RISC-V MCU. [`motorcomm-debug-pins.md`](../../research/motorcomm-debug-pins.md) gives the JTAG, flash and UART pins of each variant.

From the [YT9215SC datasheet Draft_07](../../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf); the YT9215S comes in the same LQFP-128 package with a different pinout ([YT9215S Draft_05](../../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf)).

- **SPI flash.**
  - One flash interface placed on either of two pin sets by `SPF_MUX_SEL`: SPF0 on pins [49](../../research/motorcomm-debug-pins.md#sch-pin-49), [50](../../research/motorcomm-debug-pins.md#sch-pin-50), [54](../../research/motorcomm-debug-pins.md#sch-pin-54) and [55](../../research/motorcomm-debug-pins.md#sch-pin-55), SPF1 on pins [78](../../research/motorcomm-debug-pins.md#sch-pin-78), [79](../../research/motorcomm-debug-pins.md#sch-pin-79), [81](../../research/motorcomm-debug-pins.md#sch-pin-81) and [83](../../research/motorcomm-debug-pins.md#sch-pin-83).
  - Enabled by `EN_SPIF` (pin [75](../../research/motorcomm-debug-pins.md#sch-pin-75)).
  - "Dual mode" and "Single mode" mean SPI I/O width, not two flash chips. [`switch-detail-comparison.md`](switch-detail-comparison.md) lists the two I/O modes in separate rows.
- **MCU disable.** `DIS_MCU` on pin [76](../../research/motorcomm-debug-pins.md#sch-pin-76), shared with GPIO38, UART1_TX and P2LED2. Pull-up disables the MCU.
- **Peripherals.**
  - UART0 on pins [46](../../research/motorcomm-debug-pins.md#sch-pin-46) and [47](../../research/motorcomm-debug-pins.md#sch-pin-47), UART1 on pins [70](../../research/motorcomm-debug-pins.md#sch-pin-70) and [76](../../research/motorcomm-debug-pins.md#sch-pin-76).
  - I²C master and MDIO master ("Group1").
  - GPIO5–GPIO50.
  - Parallel or serial LEDs.
  - One interrupt output.
  - 16 KB EEPROM autoload, which is for configuration, not code.
- **JTAG.** Two JTAG pin groups:
  - JTAG0: TCK on GPIO35 (pin [73](../../research/motorcomm-debug-pins.md#sch-pin-73)), TMS on GPIO34 (pin [72](../../research/motorcomm-debug-pins.md#sch-pin-72)), TDI on GPIO36 (pin [74](../../research/motorcomm-debug-pins.md#sch-pin-74)), TDO on GPIO47 (pin [90](../../research/motorcomm-debug-pins.md#sch-pin-90));
  - JTAG1: TCK on GPIO44 (pin [83](../../research/motorcomm-debug-pins.md#sch-pin-83)), TMS on GPIO43 (pin [81](../../research/motorcomm-debug-pins.md#sch-pin-81)), TDI on GPIO45 (pin [84](../../research/motorcomm-debug-pins.md#sch-pin-84)), TDO on GPIO31 (pin [67](../../research/motorcomm-debug-pins.md#sch-pin-67)).

  If the MCU's debug module sits on one of them, standard RISC-V debug with OpenOCD would give halt, memory dump and load. That would be the only realistic way in. [**I**](#evidence-codes)
- **Image format, size limit, checksum or signing: not published.** No firmware dump of a YT9215-based web-smart switch was found.

### Packet path

Evidence code for this section: [**V**](#evidence-codes).

The upstream [yt921x DSA driver](https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.c) gives the packet-path facts:

- 11 ports: "8 internal + 2 external + 1 mcu". The MCU is port 10.
- "Port 10 for MCU … is untested yet".
- `YT921X_CPU_COPY` (0x180690) has `TO_INT_CPU` and `TO_EXT_CPU` bits, so frames can be trapped or copied to the internal CPU.
- The CPU tag TPID is 0x9988.
- The register space is 0x80000+ and reached over MDIO (also I²C or SPI slave). How the MCU itself reaches registers and port 10 is unknown.

### Software

- No public Motorcomm SDK or programming guide for the switch or its MCU was found. The yt921x author notes the "lack of document".
- There is a FreeBSD port ([if_yt921x_freebsd](https://github.com/am910021/if_yt921x_freebsd)).
- yt922x DSA patches posted in August and September 2026 cover a newer family.
- Toolchain would be upstream `riscv*-gcc -march=rv32imac` or the Nuclei SDK, plus OpenOCD. Getting the memory map and boot format would need JTAG exploration.

### Feasibility

Evidence code for this section: [**I**](#evidence-codes).

- On paper this is the stronger CPU: 32-bit, an estimated 100–180 DMIPS at 70–125 MHz, enough for lwIP, LLDP and PD control over I²C.
- In practice nothing is documented: no memory map, no boot format, no samples, no community work.
- Add the poor LCSC stock (57 units) and it is not a viable base for this project.

## RTL8363NB-VB: no CPU (confirmed)

- **Datasheet.** [**V**](#evidence-codes) [RTL8363NB-VB datasheet Rev 1.2, 2018, szlcsc copy](https://atta.szlcsc.com/upload/public/pdf/source/20240423/989DCAA6328F19215A910B22766A32D7.pdf):
  - no mention of 8051, an embedded CPU, SPI flash, instruction memory or DIS_8051;
  - straps are only DISAUTOLOAD, SMI_SEL_1, SMI_SEL_0, MID29, EN_PHY and EN_SWR;
  - the only CPU text is "Slave I²C-like Interface … for external CPU";
  - the I²C *master* is described as "for EEPROM auto-download".
- **Family.** [**V**](#evidence-codes) Linux `rtl8365mb` lists RTL8363NB and RTL8363NB-VB in the same vendor family as RTL8367S ([rtl8365mb_main.c](https://github.com/torvalds/linux/blob/master/drivers/net/dsa/realtek/rtl8365mb_main.c)), so the register map includes the DW8051 control bits.
- **Inference.** [**I**](#evidence-codes) A fused-off or unbonded DW8051 may exist on the die. Without flash, UART or DIS_8051 pins, though, it could only be loaded by our own MCU over SMI. That gains nothing and is untested.

## Recommendation for the adapter

1. **Keep the external MCU.**
   - USB device and USB-PD need peripherals none of these switch CPUs have. The CH32X035 has USB FS and a PD PHY; the RP2040 has USB.
   - The external MCU is also the only option with documentation, a debugger and a community.
2. **Strap the embedded CPUs off.**
   - RTL8367S: DIS_8051 pulled up.
   - YT9215S: DIS_MCU pulled up.

   Configure the switch from the MCU over SMI or MDIO, as the design plans. The RTL8363NB pick is unaffected because it has no CPU.
3. **Optional later experiment, RTL8367S only.**
   - If a cost-down ever lets USB-PD be handled by a fixed-function controller, the MCU's remaining jobs would be LLDP-MED power requests, switch configuration, LEDs, and I²C to the PD controller. The RTL8367S 8051 could take those over, saving the MCU and its MII or RMII link.
   - Cost: a 24C256 EEPROM (≤32 KB code) or a small SPI flash, plus significant reverse engineering of the NIC path and boot format.
   - Start by SMI-loading SDCC code from a dev board and reusing RTLPlayground's SFR, timer, UART and uIP layers.
   - It would tie the design to the larger LQFP-128 part with three idle PHYs. Not recommended for v1.
4. **Do not plan around the YT9215S RISC-V core** unless Motorcomm provides an SDK under NDA.

## What could not be found

- RTL8367S:
  - DW8051_RATE reset default;
  - XDATA size;
  - exact IROM size (16 vs 32 KB);
  - NIC-to-8051 data path;
  - EEPROM and SPI-flash image framing and size limits;
  - SFR map beyond 0xA0–0xA7;
  - body of datasheet §9.17.
- YT9215S:
  - MCU clock;
  - memories;
  - boot ROM behaviour and image format;
  - whether JTAG reaches the MCU;
  - any SDK.
- A readable copy of Realtek's "Unmanaged Switch Programming Guide" (Scribd needs JavaScript).
- LCSC datasheet PDFs couldn't be fetched directly (the proxy blocked them), so mirrors were used.

## Sources

- RTL8367S-CG datasheet (mirror): https://www.framboise314.fr/wp-content/uploads/2021/06/RTL8367S-CG_Datasheet.pdf
- RTL8363NB-VB datasheet Rev 1.2 (szlcsc): https://atta.szlcsc.com/upload/public/pdf/source/20240423/989DCAA6328F19215A910B22766A32D7.pdf
- YT9215SC datasheet Draft 0.7: https://cdn.promelec.ru/upload/grab/datasheet.lcsc.com/lcsc/2512311716_Motorcomm-YT9215SC_C51037433.pdf
- YT9215S datasheet (LCSC): https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308291451_Motorcomm-YT9215S_C5899183.pdf
- GPL Realtek rtl8367c API (register header, 8051 loader, 8051 blobs): https://github.com/hanwckf/immortalwrt-mt798x/tree/openwrt-21.02/target/linux/mediatek/files-5.4/drivers/net/phy/rtk/rtl8367c
- Linux rtl8365mb SGMII series v2 (DW8051 loader, IROM 0xE000, size 0x2000): https://lkml.rescloud.iu.edu/hypermail/linux/kernel/2606.1/05986.html
- Linux rtl8365mb SGMII series v3 (DW8051 kept in reset): https://lkml.rescloud.iu.edu/hypermail/linux/kernel/2606.1/12978.html
- Linux rtl8365mb SGMII series, final thread (merged as fcaf2221b970): https://ratatoskr.run/lkml/2026/07/17247411/t
- linux-firmware rtl8367s-sgmii.bin licensing thread: https://ratatoskr.run/linux-firmware/2026/06/17116216/t
- Linux rtl8365mb driver (family list): https://github.com/torvalds/linux/blob/master/drivers/net/dsa/realtek/rtl8365mb_main.c
- Linux yt921x driver: https://github.com/torvalds/linux/blob/20eef29b7c84/drivers/net/dsa/motorcomm/chip.c
- yt921x v14 series: https://ratatoskr.run/lkml/2025/10/3255221/t
- Synopsys DW8051 datasheet (Keil): https://www.keil.com/dd/docs/datashts/synopsys/dw8051_ds.pdf
- RTLPlayground: https://github.com/logicog/RTLPlayground
- libc0607 Realtek_switch_hacking: https://github.com/libc0607/Realtek_switch_hacking
- Yakigani RTL8370 IROM loader: https://github.com/libc0607/Yakigani
- RTL8367N GS105E v2 conversion: https://github.com/libc0607/RTL8370N_switch_hacking/blob/master/RTL8367N-GS105Ev2.md
- RTL8367RB and RTL8367MB register table (leaked): https://github.com/user-attachments/files/18147305/RTL8367RB_RTL8367MB_Register_Table_V1.0.0.pdf
- Realtek Unmanaged Switch Programming Guide (Scribd, not read): https://www.scribd.com/document/866635652/Realtek-Unmanaged-Switch-ProgrammingGuide-2
- OpenWrt forum, GS308E v4 and RTL8370N: https://forum.openwrt.org/t/netgear-gs308e-v4-adding-support-for-rtl8370n-based-switches/221816
- OpenWrt forum, IPQ5018 + YT9215S: https://forum.openwrt.org/t/ipq5018-and-motorcomm-yt9215s/239942
- Nuclei and Motorcomm N205 article: https://www.riscv-mcu.com/article-show-id-929.html
- Motorcomm YT9215 launch news: https://en.motor-comm.com/news/26.html
- GigaDevice GD32VF103 (N205 (Bumblebee) performance): https://www.gigadevice.com/about/news-and-event/news/gigadevice-unveils-the-gd32v-series-with-risc-v-core
- FreeBSD yt921x port: https://github.com/am910021/if_yt921x_freebsd
