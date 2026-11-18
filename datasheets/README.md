# Switch IC documentation

Vendor documents for the switch ICs studied in [`../research/`](https://github.com/mithro/budget-poe-adapter/tree/main/research).
Downloaded 2026-11-17 unless noted. Copyright stays with the vendors; the files are
kept here unmodified (only renamed) so the notes can cite a fixed copy.

## Motorcomm (included)

| File | Part | Version | Source | MD5 |
| --- | --- | --- | --- | --- |
| [`YT9215S_Datasheet_Draft_01_2022-11-08.pdf`](motorcomm/YT9215S_Datasheet_Draft_01_2022-11-08.pdf) | YT9215S | Draft_01, 2022-11-08 | Attachment on the OSHWHub project page, as mirrored in the switch board repo (`attachments/YT9215S_Datasheet_draft_V0.1.pdf`) | `b3e4347a85bf0c4a828ef7f092006c6f` |
| [`YT9215S_Datasheet_Draft_05_2023-02-21.pdf`](motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf) | YT9215S | Draft_05, 2023-02-21 | [LCSC / szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20230829/432918AE041FF2F1E459558942DE4628.pdf) | `28ca822ad9a5fbdbcebd1037d3b18076` |
| [`YT9215SC_Datasheet_Draft_07_2023-02-28.pdf`](motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf) | YT9215SC | Draft_07, 2023-02-28 | [LCSC / szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20251231/E8DA45036F659501F9799590211A88C7.pdf) | `159f2e734e7c6c036ae3e3df6edd92ad` |
| [`YT9215SCH_Datasheet_V1.03_2025-02-10.pdf`](motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) | YT9215SCH | V1.03, 2025-02-10 | [LCSC / szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20251231/76B4B53D0DFB99DA2607FBF198C74D22.pdf) | `0f751119c66ffdac0fd8198d6e603314` |
| [`YT9215RB_Datasheet_Draft_05_2023-02-16.pdf`](motorcomm/YT9215RB_Datasheet_Draft_05_2023-02-16.pdf) | YT9215RB | Draft_05, 2023-02-16 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/762da1ba434211a9b4be1fec673c7fcf.pdf?productCode=C5449202) | `19bb5f993a24c597d663caebb21810ae` |
| [`Motorcomm_Product_Selection_Guide_2023-03-08.pdf`](motorcomm/Motorcomm_Product_Selection_Guide_2023-03-08.pdf) | All Motorcomm parts | 2023-03-08 (Chinese) | Attachment on the OSHWHub project page, as mirrored in the switch board repo (`attachments/裕太微电子产品选型20230308.pdf`) | `5025e54d6e6ca72b76c5ba4b840ccbba` |

The three YT9215 variants have three different pinouts (S = RTL8367S-compatible,
SC/SCH = RTL8367SC-compatible, RB = RTL8367RB-VB-compatible). Always take pin numbers
from the exact variant's datasheet. See
[`../research/motorcomm-debug-pins.md`](../research/motorcomm-debug-pins.md).

## Realtek (linked, not included)

The Realtek datasheets found during the research are marked "CONFIDENTIAL: Development
Partners Only" and say they may not be reproduced without Realtek's written permission.
They are therefore linked, not copied into this repository.

| Part | Document | Where |
| --- | --- | --- |
| RTL8363NB-VB-CG | Datasheet Rev. 1.2 (68 pages) | [LCSC / szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20240423/989DCAA6328F19215A910B22766A32D7.pdf), [LCSC C2835942](https://www.lcsc.com/datasheet/C2835942.pdf) |
| RTL8367S-CG | Datasheet Rev. Pre-0.941 (82 pages) | [framboise314.fr mirror](https://www.framboise314.fr/wp-content/uploads/2021/06/RTL8367S-CG_Datasheet.pdf), [LCSC C2760849](https://www.lcsc.com/datasheet/C2760849.pdf) |
| RTL8364NB-VB-CG | Datasheet | [LCSC C3013610](https://www.lcsc.com/datasheet/C3013610.pdf) |
| RTL8305NB-CG / RTL8305NBI-VB-CG | Datasheets (10/100 parts, for comparison) | [LCSC C52146](https://www.lcsc.com/datasheet/C52146.pdf), [LCSC C42451794](https://www.lcsc.com/datasheet/C42451794.pdf) |
| RTL8367RB / RTL8367MB | Register Table V1.0.0 (leaked) | [GitHub attachment](https://github.com/user-attachments/files/18147305/RTL8367RB_RTL8367MB_Register_Table_V1.0.0.pdf) |

## Other references

| What | Where |
| --- | --- |
| Motorcomm switch product page | <https://www.motor-comm.com/product/switching-chip> |
| Linux DSA driver for YT921x | `drivers/net/dsa/motorcomm/` in the kernel tree; [device-tree binding](https://www.kernel.org/doc/Documentation/devicetree/bindings/net/dsa/motorcomm%2Cyt921x.yaml) |
| OpenWrt thread on IPQ5018 + YT9215S | <https://forum.openwrt.org/t/ipq5018-and-motorcomm-yt9215s/239942> |
| Synopsys DW8051 core (the CPU inside the RTL8367S) | [Datasheet hosted by Keil](https://www.keil.com/dd/docs/datashts/synopsys/dw8051_ds.pdf) |
| Open-hardware YT9215S 5-port switch board (full design files) | <https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0> |
