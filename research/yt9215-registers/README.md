# YT9215 switch register map

A register map for the Motorcomm YT921x gigabit switch family, built from the upstream
Linux `yt921x` DSA driver and cross-checked against the vendor switch SDK and the
datasheets in [`datasheets/motorcomm/`](../../datasheets/motorcomm/).

The Linux driver defines 101 registers with 342 bit fields. They are listed with their
addresses and bit positions in [linux-driver-registers.md](linux-driver-registers.md).
The vendor SDK lists 237 register tables with 818 fields. They are listed in
[vendor-sdk-registers.md](vendor-sdk-registers.md). The SDK list has no descriptions, so
the 169 SDK tables the Linux driver does not use are known by name, address and field
position only.

## Files

| File | Contents |
|---|---|
| [linux-driver-registers.md](linux-driver-registers.md) | Registers, fields and field values from the Linux driver, grouped by block |
| [vendor-sdk-registers.md](vendor-sdk-registers.md) | Every table and field in the vendor SDK table list |
| [registers.csv](registers.csv) | Linux driver registers as CSV |
| [fields.csv](fields.csv) | Linux driver fields as CSV |
| [values.csv](values.csv) | Linux driver field values as CSV |
| [vendor-sdk-registers.csv](vendor-sdk-registers.csv) | Vendor SDK tables as CSV |
| [vendor-sdk-fields.csv](vendor-sdk-fields.csv) | Vendor SDK fields as CSV |
| [gen_registers.py](gen_registers.py) | Script that generates every file above from the two source trees |

## Sources

| Source | Location | Version | Role |
|---|---|---|---|
| Linux DSA driver | [drivers/net/dsa/motorcomm/](https://github.com/torvalds/linux/tree/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm) | mainline commit `20eef29b7c84` | Primary source of names and bits |
| Linux DSA tag driver | [net/dsa/tag_yt921x.c](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c) | mainline commit `20eef29b7c84` | CPU tag format |
| Linux devicetree binding | [motorcomm,yt921x.yaml](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/Documentation/devicetree/bindings/net/dsa/motorcomm,yt921x.yaml) | mainline commit `20eef29b7c84` | MDIO address and bus layout |
| OpenWrt | [target/linux/generic/backport-6.18/](https://github.com/openwrt/openwrt/tree/5732bcbeff1826d5ec41c32161395c9d5e62b5d9/target/linux/generic/backport-6.18) | commit `5732bcbeff18` | Backport of the Linux driver |
| Vendor switch SDK | [OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/tree/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e) | commit `d2c8d6fc721f` | Cross-check of addresses and bits |
| YT9215S datasheet | [YT9215S_Datasheet_Draft_05_2023-02-21.pdf](../../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf) | Draft 05 | Cross-check of table sizes |
| YT9215SCH datasheet | [YT9215SCH_Datasheet_V1.03_2025-02-10.pdf](../../datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) | V1.03 | Cross-check of table sizes and host interfaces |

The Linux driver lives in `drivers/net/dsa/motorcomm/` and is split across `chip.c`,
`chip.h`, `smi.c`, `mdio_bus.c`, `mib.c`, `leds.c`, `tc.c` and `pcs-921x.c` with their
headers. There is no `drivers/net/dsa/yt921x.c` at this commit.

OpenWrt carries the same driver as a series of `967-*` backport patches of the upstream
commits. It has no register definitions of its own for the YT921x.

The vendor SDK is a public mirror of the Motorcomm kernel module source. Its register
list is in two machine-generated files,
[fal_tiger_index.c](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_index.c)
for addresses and sizes and
[fal_tiger_struct.c](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/switch_sdk/core/fal/tiger/fal_tiger_struct.c)
for field positions.

## Register access

Every register is 32 bits wide and sits at a 32-bit address that is a multiple of 4. The
host reaches the registers through an indirect protocol on an MDIO bus, which the
datasheets call the slave SMI interface. The Linux driver implements only this
interface. The YT9215SCH datasheet also describes a slave I2C and a slave SPI interface
to the same registers.

### SMI frame encoding

The switch answers clause 22 MDIO frames at one PHY address. The devicetree binding
allows address 0x00 or 0x1d. The 5-bit register address field of each frame is not a
register number. It carries the fields below.

| Bits | Field | Value 0 | Value 1 | Source |
|---|---|---|---|---|
| 3:2 | Switch ID | | | [chip.h:11](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L11) |
| 1 | Phase | Address | Data | [chip.h:13](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L13) |
| 0 | Direction | Write | Read | [chip.h:16](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L16) |

The switch ID is the value strapped on the `SWITCH_ID_1` and `SWITCH_ID_0` pins, which
lets four switches share one PHY address. The Linux driver always uses switch ID 0.

### SMI read sequence

| Step | MDIO operation | Phase bit | Direction bit | 16-bit data | Source |
|---|---|---|---|---|---|
| 1 | Write | Address | Read | Register address bits 31:16 | [chip.c:116](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L116) |
| 2 | Write | Address | Read | Register address bits 15:0 | [chip.c:119](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L119) |
| 3 | Read | Data | Read | Register value bits 31:16 | [chip.c:125](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L125) |
| 4 | Read | Data | Read | Register value bits 15:0 | [chip.c:129](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L129) |

### SMI write sequence

| Step | MDIO operation | Phase bit | Direction bit | 16-bit data | Source |
|---|---|---|---|---|---|
| 1 | Write | Address | Write | Register address bits 31:16 | [chip.c:155](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L155) |
| 2 | Write | Address | Write | Register address bits 15:0 | [chip.c:158](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L158) |
| 3 | Write | Data | Write | Register value bits 31:16 | [chip.c:164](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L164) |
| 4 | Write | Data | Write | Register value bits 15:0 | [chip.c:167](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L167) |

The vendor's standalone MDIO driver
[yt9215rb.c](https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e/yt9215rb_mdio_driver/yt9215rb.c#L22)
uses the same encoding and the same four-step sequences.

### Multi-word registers

Table entries wider than 32 bits, such as a VLAN table entry, occupy consecutive
addresses. The driver reads and writes all words of such an entry in ascending address
order. A write to one word does not take effect until the last word of the entry is
written
([smi.h:38](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/smi.h#L38)).

### PHY registers through the MDIO master buses

The switch has two MDIO master buses that the host drives through switch registers. The
internal bus reaches the built-in gigabit PHYs, where the PHY address equals the port
number, and the SerDes PCS of ports 8 and 9 at addresses 8 and 9. The external bus
reaches PHYs wired to the switch's master SMI pins.

| Step | Read | Write | Source |
|---|---|---|---|
| 1 | Wait until `MBUS_OP_START` reads 0 | Wait until `MBUS_OP_START` reads 0 | [mdio_bus.c:12](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/mdio_bus.c#L12) |
| 2 | Set port, register and read operation in `MBUS_CTRL` | Set port, register and write operation in `MBUS_CTRL` | [mdio_bus.c:36](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/mdio_bus.c#L36) |
| 3 | | Write the value to `MBUS_DOUT` | [mdio_bus.c:75](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/mdio_bus.c#L75) |
| 4 | Write `MBUS_OP_START` to `MBUS_OP` | Write `MBUS_OP_START` to `MBUS_OP` | [mdio_bus.c:39](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/mdio_bus.c#L39) |
| 5 | Wait until `MBUS_OP_START` reads 0 | Wait until `MBUS_OP_START` reads 0 | [mdio_bus.c:43](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/mdio_bus.c#L43) |
| 6 | Read the value from `MBUS_DIN` | | [mdio_bus.c:46](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/mdio_bus.c#L46) |

The register names take the prefix `INT_` at 0x0f0000 for the internal bus and `EXT_` at
0x06a000 for the external bus. The external bus also sets `MBUS_CTRL_TYPE` to clause 22.

### EDATA bytes

`EDATA_CTRL` and `EDATA_DATA` give byte-wide read access to a 256-byte store inside the
chip. The driver writes the byte address and the read operation to `EDATA_CTRL`, waits
for the status field of `EDATA_DATA` to read idle, and takes the byte from bits 31:24 of
`EDATA_DATA`
([chip.c:2122](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L2122)).
The only byte the driver reads is 0xfb, which it calls the extended chip mode.

## Address space

| Base address | SDK module | SDK tables | Contents |
|---|---|---|---|
| 0x06a000 | | 0 | External MDIO master bus |
| 0x080000 | `SWITCH_CORE_GLOBAL` | 24 | Global control and port control |
| 0x081000 | | 0 | Per-port MAC registers at a 0x1000 stride |
| 0x0a0000 | | 0 | Per-port EEE registers at a 0x40 stride |
| 0x0b0000 | | 0 | EEE enable |
| 0x0c0000 | | 0 | MIB counters at a 0x100 stride per port |
| 0x0d0000 | | 0 | LED control |
| 0x0e0000 | | 0 | EDATA access and system clock |
| 0x0f0000 | | 0 | Internal MDIO master bus |
| 0x100000 | `PTX` | 10 | Egress tagging |
| 0x180000 | `IPE_L2` | 87 | Layer 2 forwarding |
| 0x200000 | `IPE_ACL` | 20 | ACL keys and masks |
| 0x210000 | `IPE_IPR` | 20 | Ingress parser |
| 0x220000 | `IPE_IM` | 13 | Meters and ingress rate control |
| 0x230000 | `IPE_IV` | 8 | Ingress port VLAN control |
| 0x300000 | `QM` | 7 | Queue manager and mirroring |
| 0x340000 | `SCH` | 10 | Scheduler and egress shaping |

The `IPE_L2` count includes the 4096-entry VLAN table at 0x188000 and the 384-entry ACL
action table at 0x1c0000, which sit above the other layer 2 registers.

The SDK table list holds 38 more entries at address 0x000000. They are the ACL key and
mask layouts for each key type, not memory-mapped registers.

## Blocks in the Linux driver

| Block | Registers | Section |
|---|---|---|
| Global and chip identification | 15 | [link](linux-driver-registers.md#global-and-chip-identification) |
| CPU port and tagging | 3 | [link](linux-driver-registers.md#cpu-port-and-tagging) |
| Port, MAC and external interface control | 8 | [link](linux-driver-registers.md#port-mac-and-external-interface-control) |
| MDIO master buses (PHY access) | 8 | [link](linux-driver-registers.md#mdio-master-buses-phy-access) |
| EEE | 2 | [link](linux-driver-registers.md#eee) |
| MIB counters | 2 | [link](linux-driver-registers.md#mib-counters) |
| LEDs | 9 | [link](linux-driver-registers.md#leds) |
| VLAN | 10 | [link](linux-driver-registers.md#vlan) |
| QoS priority mapping | 4 | [link](linux-driver-registers.md#qos-priority-mapping) |
| Spanning tree, isolation and learning | 4 | [link](linux-driver-registers.md#spanning-tree-isolation-and-learning) |
| FDB (address table) | 9 | [link](linux-driver-registers.md#fdb-address-table) |
| Flooding and unknown-destination handling | 6 | [link](linux-driver-registers.md#flooding-and-unknown-destination-handling) |
| Link aggregation | 3 | [link](linux-driver-registers.md#link-aggregation) |
| ACL | 9 | [link](linux-driver-registers.md#acl) |
| Meters and ingress policing | 5 | [link](linux-driver-registers.md#meters-and-ingress-policing) |
| Egress shaping | 3 | [link](linux-driver-registers.md#egress-shaping) |
| Mirroring | 1 | [link](linux-driver-registers.md#mirroring) |

Three sets of fields are shared between registers. The `FDB_IO0`, `FDB_IO1` and
`FDB_IO2` fields are listed under `FDB_OUT0`, `FDB_OUT1` and `FDB_OUT2` and apply
equally to `FDB_IN0`, `FDB_IN1` and `FDB_IN2`. The `LEDx_PORT_ACT` fields are listed
under `LED2_PORTn` and apply to `LED0_PORTn`, `LED1_PORTn` and `LED2_PORTn`. The
`FILTER_PORTS` field is listed under `FILTER_BCAST` and applies to all four `FILTER_`
registers.

## Chip variants

The driver uses one register map for every chip in the family. It identifies the chip
from three values and uses them only to decide which ports exist.

| Value | Register | Address | Bits | Source |
|---|---|---|---|---|
| Chip family | `CHIP_ID` | 0x080008 | 31:16 | [chip.h:30](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L30) |
| Chip mode | `CHIP_MODE` | 0x080388 | 1:0 | [chip.h:129](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L129) |
| Extended mode | EDATA byte | 0xfb | 7:0 | [chip.h:408](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L408) |

| Chip | Chip family | Chip mode | Extended mode | Internal PHY port mask | Port 8 SerDes | Port 8 xMII | Port 9 SerDes | Port 9 xMII | Source |
|---|---|---|---|---|---|---|---|---|---|
| YT9215SC | 0x9002 | 1 | 0 | 0x01f | yes | no | yes | yes | [chip.c:38](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L38) |
| YT9215S | 0x9002 | 2 | 0 | 0x01f | yes | no | no | yes | [chip.c:44](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L44) |
| YT9215RB | 0x9002 | 3 | 0 | 0x01f | no | yes | no | yes | [chip.c:50](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L50) |
| YT9214NB | 0x9002 | 3 | 2 | 0x00a | yes | no | no | yes | [chip.c:56](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L56) |
| YT9213NB | 0x9002 | 3 | 3 | 0x00a | no | no | yes | yes | [chip.c:62](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L62) |
| YT9218N | 0x9001 | 0 | 0 | 0x0ff | no | no | no | no | [chip.c:68](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L68) |
| YT9218MB | 0x9001 | 1 | 0 | 0x0ff | yes | yes | yes | yes | [chip.c:74](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.c#L74) |

Ports 0 to 7 are the internal PHY ports, ports 8 and 9 are the external interface ports
and port 10 is the internal MCU port. Port bitmap fields are therefore 11 bits wide.

The driver has no entry named YT9215SCH. The board in
[`lx-is601f-board/`](../lx-is601f-board/) carries a YT9215SCH, and this document assumes
it reports the YT9215SC values. Reading `CHIP_ID`, `CHIP_MODE` and EDATA byte 0xfb from
that board would settle it.

Two registers have a different layout in the YT9215 and YT9218 families.

| Register | Field | YT9215 bits | YT9218 bits | Source |
|---|---|---|---|---|
| `IO_LEVEL` | `NORMAL` | 5:4 | 1:0 | [chip.h:48](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L48) |
| `IO_LEVEL` | `RGMII1` | 3:2 | 5:4 | [chip.h:52](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L52) |
| `IO_LEVEL` | `RGMII0` | 1:0 | 3:2 | [chip.h:57](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L57) |

| Register | Field | Value | YT9215 meaning | YT9218 meaning | Source |
|---|---|---|---|---|---|
| `SYS_CLK` | `SYS_CLK_SEL` | 0 | 125 MHz | 167 MHz | [chip.h:179](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L179) |
| `SYS_CLK` | `SYS_CLK_SEL` | 1 | 143 MHz | 143 MHz | [chip.h:181](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L181) |

## CPU tag

Frames to and from the CPU port carry an 8-byte tag after the source MAC address. The
tag is four 16-bit big-endian words. It is not a register, but `EXT_CPU_PORT` and
`CPU_TAG_TPID` configure it.

| Word | Bits | Field | Direction | Source |
|---|---|---|---|---|
| 0 | 15:0 | Tag EtherType | Both | [tag_yt921x.c:12](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L12) |
| 1 | 15:0 | VLAN tag | Receive | [tag_yt921x.c:16](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L16) |
| 2 | 15 | Source port valid | Receive | [tag_yt921x.c:37](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L37) |
| 2 | 14:11 | Source port | Receive | [tag_yt921x.c:38](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L38) |
| 2 | 10:8 | Priority | Both | [tag_yt921x.c:39](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L39) |
| 2 | 7 | Code valid | Both | [tag_yt921x.c:41](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L41) |
| 2 | 6:1 | Code | Both | [tag_yt921x.c:42](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L42) |
| 2 | 0 | Unknown | Both | [tag_yt921x.c:23](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L23) |
| 3 | 15 | Destination ports valid | Transmit | [tag_yt921x.c:37](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L37) |
| 3 | 10:0 | Destination port mask | Transmit | [tag_yt921x.c:44](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L44) |

The hardware default tag EtherType is 0x9988.

| Code | Meaning | Source |
|---|---|---|
| 0x00 | Forward | [tag_yt921x.c:51](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L51) |
| 0x17 | ACL | [tag_yt921x.c:52](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L52) |
| 0x19 | Unknown unicast | [tag_yt921x.c:53](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L53) |
| 0x1a | Unknown multicast | [tag_yt921x.c:54](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L54) |
| 0x1b | Port copy | [tag_yt921x.c:55](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L55) |
| 0x1c | FDB copy | [tag_yt921x.c:56](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L56) |

## Uncertain and inferred entries

### Marked uncertain by the driver author

| Item | Driver comment | Source |
|---|---|---|
| `SYS_CLK_SEL` | unknown: 167M | [chip.h:178](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L178) |
| Chip mode value | Unknown, seems to be plain enumeration | [chip.h:491](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/chip.h#L491) |
| `LED_CTRL_UNK` | No meaning given | [leds.h:15](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/leds.h#L15) |
| `LED_SER_CTRL_UNK` | delay? | [leds.h:68](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/leds.h#L68) |
| `MBUS_CTRL_TYPE` | wild guess | [mdio_bus.h:22](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/mdio_bus.h#L22) |
| `MBUS_CTRL_OP` | wild guess | [mdio_bus.h:25](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/drivers/net/dsa/motorcomm/mdio_bus.h#L25) |
| CPU tag word 2 bit 0 | ? (unset) | [tag_yt921x.c:23](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L23) |
| CPU tag code list | Incomplete | [tag_yt921x.c:47](https://github.com/torvalds/linux/blob/20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca/net/dsa/tag_yt921x.c#L47) |

### Inferred in this document

| Item | Basis |
|---|---|
| Grouping of registers into blocks | Register names and address ranges |
| Pairing of a driver register with an SDK table | Equal address |
| Pairing of a driver field with an SDK field | Equal address, word and bits |
| SDK module of each SDK table | Nearest SDK module base address at or below the table address |
| "Contents" column of the address space table | Names of the registers found in each range |
| YT9215SCH identifies as YT9215SC | The driver has no YT9215SCH entry |
| EDATA is a 256-byte store | The driver constant `YT921X_EDATA_LEN` and the 8-bit address field |
| Meaning of every SDK table the driver does not use | The SDK table and field names |

Everything else in [linux-driver-registers.md](linux-driver-registers.md) is a direct
transcription of a `#define` in the driver, and each row links to its line.

## Cross-check against the vendor SDK

Each of the 342 driver fields was compared with the SDK field list at the same address.

| Result | Fields |
|---|---|
| Same bits as one SDK field | 174 |
| One or two bits inside a wider SDK field | 16 |
| Different field boundaries | 1 |
| SDK has the register but no field at these bits | 1 |
| SDK has the register with an empty field list | 60 |
| Address is not in the SDK table list | 67 |
| Bit position depends on an index and was not compared | 23 |

No driver field contradicts the SDK on which register it belongs to. The two
disagreements are below.

| Register | Driver field | Driver bits | SDK field | SDK bits |
|---|---|---|---|---|
| `PORTn_LEARN` | `PORT_LEARN_LIMIT` | 15:8 | `LEARN_LIMIT_NUM` | 15:3 |
| `RST` | `RST_HW` | 31 | none | none |

The 60 fields with an empty SDK field list are the ACL key and mask words. The SDK
describes those words through separate `_RULE` and `_RULE_MASK` structures, one pair
per key type, that its table list places at address 0x000000.

Of the 101 driver registers, 68 fall inside an SDK table and 33 do not. For 32 of those
33 the SDK uses the same address as a literal in another source file, named in the
"Other SDK file" column. `PORTn_SHAPE_STAT` at 0x356000 appears only in the Linux
driver.

The driver uses 68 of the 237 SDK tables. The other 169 cover features the driver does
not program, including interrupts, storm control, DoS protection, 802.1X, reserved
multicast handling, wake-on-LAN, loop detection, VLAN translation and queue scheduling.

## Cross-check against the datasheets

The datasheets contain no register addresses or bit definitions, so they cannot confirm
the map itself. They overlap with the driver on table sizes and on the host interface.

| Item | Driver constant | Driver value | YT9215S datasheet | YT9215SCH datasheet |
|---|---|---|---|---|
| FDB entries | `YT921X_FDB_NUM` | 4096 | 4K | 4K |
| VLAN table entries | SDK `L2_VLAN_TBL` entries | 4096 | 4K | 4K |
| ACL rows | `YT921X_ACL_BLK_NUM` | 48 | 48 | 48 |
| ACL entries per row | `YT921X_ACL_ENT_PER_BLK` | 8 | 8 | 8 |
| ACL entries | `YT921X_ACL_NUM` | 384 | 384 | 384 |
| Link aggregation groups | `YT921X_LAG_NUM` | 2 | 2 | 2 |
| Largest frame in bytes | `YT921X_FRAME_SIZE_MAX` | 9216 | 9K | 9K |
| Switch ID strap bits | `YT921X_SMI_SWITCHID_M` | 2 | 2 | 2 |

The YT9215SCH datasheet describes three host interfaces to the registers.

| Host interface | `DIS_SPIS` strap | `SMI_SEL` strap | In Linux driver | Datasheet detail |
|---|---|---|---|---|
| Slave SMI | high | low or high | yes | Switch ID from the `SWITCH_ID` straps |
| Slave I2C | high | high | no | Switch ID in the frame and a parity bit over address bits 31:2 |
| Slave SPI | not stated | not stated | no | Operation code 0x02 for write and 0x03 for read |

The strap values are quoted as the datasheet words them. Its text for slave SMI and for
slave I2C overlaps when both straps are high, so the datasheet alone does not say which
of the two is selected in that case.

## Regenerating

[gen_registers.py](gen_registers.py) takes a directory holding the files of
`drivers/net/dsa/motorcomm/` and a checkout of the vendor SDK.

```sh
python3 gen_registers.py \
    --linux path/to/linux/drivers/net/dsa/motorcomm \
    --linux-sha 20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca \
    --sdk path/to/motorcomm-yt9215-switch-sdk \
    --sdk-sha d2c8d6fc721fdb7e04e815b4fe2a397a2817ee5e
```
