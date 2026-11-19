# Boards and products that carry a YT9215

Hardware on which the YT9215 and its RISC-V CPU can be studied: the boards
documented in this repository, and the retail products found to use the chip. The CPU
itself is described in [`yt9215-embedded-cpu.md`](yt9215-embedded-cpu.md).

<a id="evidence-codes"></a>
Each statement carries one of these evidence marks:

| Mark | Meaning |
|---|---|
| Verified | Read in a cited source |
| Inferred | Reasoned from other evidence |

Prices are indicative, from listings and deal sites seen on 2026-10-22. They are not
quotes, and they were not read from live Amazon, eBay or AliExpress product pages, which
block automated fetches.

## Boards documented in this repository

| Board | Switch IC | Kind | CPU strap | Notes |
| --- | --- | --- | --- | --- |
| <a id="board-lx"></a>LX-IS601F V2.0 | YT9215SCH | Bought switch board | [Disabled](switch-board-strapping.md#lx-is601f-v20) | [Board notes](lx-is601f-board/README.md) |
| <a id="board-wu-kou"></a>Open-hardware 5-port switch V2.0 | YT9215S | Open-hardware design | [Enabled](switch-board-strapping.md#wu-kou-yt9215s-v20) | [Design files](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0) |

- The [LX-IS601F V2.0](#board-lx) board has five copper ports and one SFP port. Its
  strap levels are inferred from a photo ([inferred](#evidence-codes)); the strapping and
  major components of both boards are in
  [`switch-board-strapping.md`](switch-board-strapping.md). Where the
  debug pins of its switch IC come out is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#lx-is601f-v20-boards), and a
  reverse-engineered schematic is in
  [`lx-is601f-board/schematic/`](lx-is601f-board/schematic/README.md).
- The [open-hardware switch](#board-wu-kou) is "基于裕太微YT9215S的五口千兆交换机" v2.0 by
  pankanwen on [OSHWHub](https://oshwhub.com/pankanwen/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0)
  ([verified](#evidence-codes)). The linked repository mirrors its EasyEDA source, schematic,
  PCB, Gerbers and BOM, so it can be ordered or changed. How it wires the debug and boot
  pins is in
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#how-the-mirrored-board-wires-these-pins).

## Official evaluation boards

No Motorcomm evaluation board for the YT9215 was found. The
[Motorcomm product page](https://www.motor-comm.com/product/switching-chip) mentions none
for the YT9215S, the YT9215SC or the YT9215RB ([verified](#evidence-codes)). Searches of
distributors and marketplaces found none listed ([inferred](#evidence-codes)).

## What Motorcomm says about the CPU for each part

| Part | GE ports | SerDes ports | RGMII ports | CPU on the product page | CPU in the datasheet |
| --- | --- | --- | --- | --- | --- |
| YT9215S | 5 | 1 | 1 | No | Yes |
| YT9215SC | 5 | 2 | 1 | Yes | Yes |
| YT9215RB | 5 | – | 2 | No | Yes |
| YT9218N | 8 | – | – | Yes | Not checked |
| YT9218MB | 8 | 2 | 2 | Yes | Not checked |

- The [YT9215SC](../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf) datasheet lists two SerDes
  ports and one RGMII port for two extension ports: the second extension port is either
  RGMII or SerDes. The
  [selection guide](../datasheets/motorcomm/Motorcomm_Product_Selection_Guide_2023-03-08.pdf)
  says the same ([verified](#evidence-codes)).
- Of the parts in the table, the product page lists the CPU and simple network
  management for the YT9215SC, the YT9218N and the YT9218MB only. Its wording for the YT9215SC is "内置高性能RISC-V
  核心CPU" and "支持简单网管" ([verified](#evidence-codes)).
- The [YT9215S](../datasheets/motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf), [YT9215SC](../datasheets/motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf) and [YT9215RB](../datasheets/motorcomm/YT9215RB_Datasheet_Draft_05_2023-02-16.pdf) datasheets all list an integrated
  RISC-V microprocessor ([verified](#evidence-codes)).
  [`motorcomm-debug-pins.md`](motorcomm-debug-pins.md#every-variant-has-the-risc-v-mcu)
  has the detail.
- The product page and the datasheets therefore disagree for the YT9215S and the
  YT9215RB. Motorcomm may support CPU firmware only on the parts where its product page
  lists the CPU ([inferred](#evidence-codes)).

## Retail products with a YT9215

| Product | Chinese name | Host SoC | Switch | Count | Link | Alternative link | MDIO address | Linux support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="product-cr881x"></a>Xiaomi CR881x | – | IPQ5018 | YT9215S | 1 | SGMII | 2500base-X | 0x1d | OpenWrt fork |
| <a id="product-g98"></a>BDY-G98 | 彼度云 G98 | RK3588 | YT9215S | 2 | `rgmii-txid` | – | 0x1d | DSA `yt921x` |
| Unnamed industrial boards | – | RK3568 | YT9215 | – | MAC-to-MAC | – | – | – |
| Unnamed industrial boards | – | RK3588 | YT9215 | – | MAC-to-MAC | – | – | – |

In both named products a host SoC manages the switch from outside. Neither is known to
run firmware on the switch CPU.

| Product | Property | Value | Evidence |
| --- | --- | --- | --- |
| [Xiaomi CR881x](#product-cr881x) | Model 1 | CR8816 | – |
| [Xiaomi CR881x](#product-cr881x) | Model 2 | CR8818 | – |
| [Xiaomi CR881x](#product-cr881x) | Type | China carrier AX3000 mesh units | – |
| [Xiaomi CR881x](#product-cr881x) | Board | M79 | – |
| [Xiaomi CR881x](#product-cr881x) | Switch CPU port | Port 8 | [Verified](#evidence-codes) |
| [Xiaomi CR881x](#product-cr881x) | Switch reset | GPIO 35 | [Verified](#evidence-codes) |
| [Xiaomi CR881x](#product-cr881x) | Source 1 | [OpenWrt forum](https://forum.openwrt.org/t/ipq5018-yt9215s-and-1000base-x-2500base-x/241325) | – |
| [Xiaomi CR881x](#product-cr881x) | Source 2 | [hzyitc issue #150](https://github.com/hzyitc/openwrt-redmi-ax3000/issues/150) | – |
| [Xiaomi CR881x](#product-cr881x) | Host UART header | J1 | – |
| [Xiaomi CR881x](#product-cr881x) | Host UART pin 1 | VCC | – |
| [Xiaomi CR881x](#product-cr881x) | Host UART pin 2 | RX | – |
| [Xiaomi CR881x](#product-cr881x) | Host UART pin 3 | GND | – |
| [Xiaomi CR881x](#product-cr881x) | Host UART pin 4 | TX | – |
| [Xiaomi CR881x](#product-cr881x) | OpenWrt | [hzyitc/openwrt-redmi-ax3000](https://github.com/hzyitc/openwrt-redmi-ax3000) | – |
| [Xiaomi CR881x](#product-cr881x) | Known issue | Flaky switch probe | [Verified](#evidence-codes) |
| [Xiaomi CR881x](#product-cr881x) | Where sold | Second-hand in China | – |
| [Xiaomi CR881x](#product-cr881x) | Marketplace | Xianyu | – |
| [Xiaomi CR881x](#product-cr881x) | AliExpress | Occasional listings | – |
| [Xiaomi CR881x](#product-cr881x) | eBay | Occasional listings | – |
| [Xiaomi CR881x](#product-cr881x) | Typical price | US$25–50 | – |
| [Xiaomi CR881x](#product-cr881x) | Not confirmed YT9215 | CR8806 | [Inferred](#evidence-codes) |
| [Xiaomi CR881x](#product-cr881x) | Not confirmed YT9215 | CR8808 | [Inferred](#evidence-codes) |
| [Xiaomi CR881x](#product-cr881x) | Not confirmed YT9215 | CR8809 | [Inferred](#evidence-codes) |
| [Xiaomi CR881x](#product-cr881x) | Not confirmed YT9215 | Redmi AX3000 | [Inferred](#evidence-codes) |
| [BDY-G98](#product-g98) | Type 1 | NAS | – |
| [BDY-G98](#product-g98) | Type 2 | Router | – |
| [BDY-G98](#product-g98) | LAN ports | 8 | – |
| [BDY-G98](#product-g98) | Switch attach | Each YT9215S on an RK3588 GMAC | [Verified](#evidence-codes) |
| [BDY-G98](#product-g98) | Source | [GitHub issue](https://github.com/yifengyou/BDY_G98_RK3588/issues/6) | – |
| [BDY-G98](#product-g98) | Known issue | Cross-chip forwarding lock-up | [Verified](#evidence-codes) |
| [BDY-G98](#product-g98) | Where sold | China-market box | – |
| [BDY-G98](#product-g98) | Amazon AU | Not found | – |
| [BDY-G98](#product-g98) | eBay | Not found | – |
| [BDY-G98](#product-g98) | AliExpress | Not found | – |
| Unnamed industrial boards | Source | [CSDN write-up](https://blog.csdn.net/xuesong10210/article/details/135957672) | – |
| Unnamed industrial boards | Product names | Not given | – |

Before buying a Xiaomi unit, check that the model is a CR881x: the other models in the
table are not confirmed to carry a YT9215.

## Chips

Prices and stock are the LCSC figures in the archived
[switch IC comparison](../archive/research/ethernet-switch-comparison.md).

| Part | LCSC part | Price | Stock | Read on |
| --- | --- | --- | --- | --- |
| YT9215S | [C5899183](https://www.lcsc.com/product-detail/C5899183.html) | $1.92 @1k | 57 | 2026-10-22 |
| YT9215SC | [C51037433](https://www.lcsc.com/product-detail/C51037433.html) | $2.89 @1k | 115 | 2026-10-22 |

## Search links

Results change daily.

| Shop | Search |
| --- | --- |
| eBay | [Xiaomi CR8818](https://www.ebay.com/sch/i.html?_nkw=Xiaomi+CR8818) |
| AliExpress | [Xiaomi CR881x](https://www.aliexpress.com/w/wholesale-xiaomi-CR8818.html) |

## Open questions

- Does the CR881x's YT9215S have its CPU strapped off (pin
  [75](motorcomm-debug-pins.md#s-pin-75))? A photo of the board around the switch would
  answer it.
- Is the CPU of the [LX-IS601F V2.0](#board-lx) boards really disabled? The strap levels
  are inferred from a photo of the resistor array, not measured
  ([`switch-board-strapping.md`](switch-board-strapping.md#checks-that-would-confirm-the-strapping)).
  With those levels the chip loads its registers from the 24C08 EEPROM on the board and
  the CPU does not run.
- Does any other retail product run firmware on the YT9215 CPU? None was identified. Motorcomm
  describes the CPU as being for simple network management, so a web-managed switch built
  on a YT9215SC or a YT9218 would be the place to look ([inferred](#evidence-codes)).
