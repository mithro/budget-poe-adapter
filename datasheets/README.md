# Datasheets

Vendor documents for the switch ICs studied in the research notes (indexed in [`../README.md`](../README.md)) and for
the parts found on the two switch boards described in
[`../research/switch-board-strapping.md`](../research/switch-board-strapping.md).
Copyright stays with the vendors; the files are kept here unmodified apart from their names so
the notes can cite a fixed copy.

| Section | Contents |
| --- | --- |
| [Motorcomm (included)](#motorcomm-included) | Switch IC datasheets. |
| [Board components (included)](#board-components-included) | Datasheets of the other board parts. |
| [Board components (not found)](#board-components-not-found) | Parts with no datasheet in this folder. |
| [Realtek (linked, not included)](#realtek-linked-not-included) | Links to confidential datasheets. |
| [Other references](#other-references) | Related links. |

## Motorcomm (included)

| File | Part | Version | Date | Language | Source | MD5 |
| --- | --- | --- | --- | --- | --- | --- |
| [`YT9215S_Datasheet_Draft_01_2022-11-08.pdf`](motorcomm/YT9215S_Datasheet_Draft_01_2022-11-08.pdf) | YT9215S | Draft_01 | 2022-11-08 | English | [Attachment in the wu-kou board repository](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/attachments/YT9215S_Datasheet_draft_V0.1.pdf) | `b3e4347a85bf0c4a828ef7f092006c6f` |
| [`YT9215S_Datasheet_Draft_05_2023-02-21.pdf`](motorcomm/YT9215S_Datasheet_Draft_05_2023-02-21.pdf) | YT9215S | Draft_05 | 2023-02-21 | English | [szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20230829/432918AE041FF2F1E459558942DE4628.pdf) | `28ca822ad9a5fbdbcebd1037d3b18076` |
| [`YT9215SC_Datasheet_Draft_07_2023-02-28.pdf`](motorcomm/YT9215SC_Datasheet_Draft_07_2023-02-28.pdf) | YT9215SC | Draft_07 | 2023-02-28 | English | [szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20251231/E8DA45036F659501F9799590211A88C7.pdf) | `159f2e734e7c6c036ae3e3df6edd92ad` |
| [`YT9215SCH_Datasheet_V1.03_2025-02-10.pdf`](motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf) | YT9215SCH | V1.03 | 2025-02-10 | English | [szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20251231/76B4B53D0DFB99DA2607FBF198C74D22.pdf) | `0f751119c66ffdac0fd8198d6e603314` |
| [`YT9215RB_Datasheet_Draft_05_2023-02-16.pdf`](motorcomm/YT9215RB_Datasheet_Draft_05_2023-02-16.pdf) | YT9215RB | Draft_05 | 2023-02-16 | English | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/762da1ba434211a9b4be1fec673c7fcf.pdf?productCode=C5449202) | `19bb5f993a24c597d663caebb21810ae` |
| [`Motorcomm_Product_Selection_Guide_2023-03-08.pdf`](motorcomm/Motorcomm_Product_Selection_Guide_2023-03-08.pdf) | All Motorcomm parts | None | 2023-03-08 | Chinese | [Attachment in the wu-kou board repository](https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0/blob/main/attachments/%E8%A3%95%E5%A4%AA%E5%BE%AE%E7%94%B5%E5%AD%90%E4%BA%A7%E5%93%81%E9%80%89%E5%9E%8B20230308.pdf) | `5025e54d6e6ca72b76c5ba4b840ccbba` |

The YT9215 variants have three different pinouts, so pin numbers must come from the exact variant's datasheet. The
pinouts are compared in [`../research/motorcomm-debug-pins.md`](../research/motorcomm-debug-pins.md).

| Variant | Pinout compatible with |
| --- | --- |
| YT9215S | RTL8367S |
| YT9215SC | RTL8367SC |
| YT9215SCH | RTL8367SC |
| YT9215RB | RTL8367RB-VB |

## Board components (included)

One row per part. The Board column names the board that carries the part; its designators are in
[`../research/switch-board-strapping.md`](../research/switch-board-strapping.md). Parts from the same series share one series datasheet, so a file can
appear in more than one row. The LCSC column links to the part's product page on
[lcsc.com](https://www.lcsc.com/), or on [jlcpcb.com](https://jlcpcb.com/parts) for the
four parts that lcsc.com does not list ([C57269](https://jlcpcb.com/partdetail/C57269), [C50543](https://jlcpcb.com/partdetail/C50543), [C2942441](https://jlcpcb.com/partdetail/C2942441) and [C495286](https://jlcpcb.com/partdetail/C495286)). The Source
column links to the origin of the PDF.

| File | Part | Maker | Board | LCSC | Pages | Source | MD5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [`Murata_XRCGB_Crystal.pdf`](components/Murata_XRCGB_Crystal.pdf) | XRCGB25M000F3M00R0 | Murata | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C127893](https://www.lcsc.com/product-detail/C127893.html) | 3 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/21fde927ecc243a88213e4f624c2409b.pdf?productCode=C127893) | `b3694e975cec45b5bcf5b9cc167f974d` |
| [`Aerosemi_MT2492.pdf`](components/Aerosemi_MT2492.pdf) | MT2492 | Xi'an Aerosemi | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C89358](https://www.lcsc.com/product-detail/C89358.html) | 9 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/9fd100435d2385fd4d717149b36f71d5.pdf?productCode=C89358) | `016ed66f2631bbe0500102ecf8aaaa66` |
| [`Sunlord_SWPA_Series.pdf`](components/Sunlord_SWPA_Series.pdf) | SWPA4030S4R7MT | Sunlord | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C57269](https://jlcpcb.com/partdetail/C57269) | 20 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/dc27f0913034a1bfb18554ababd47a88.pdf?productCode=C57269) | `921b65a3b52194014e000d292677b29a` |
| [`Sunlord_SWPA_Series.pdf`](components/Sunlord_SWPA_Series.pdf) | SWPA4018S2R2MT | Sunlord | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C50543](https://jlcpcb.com/partdetail/C50543) | 20 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/dc27f0913034a1bfb18554ababd47a88.pdf?productCode=C57269) | `921b65a3b52194014e000d292677b29a` |
| [`Murata_BLM18KG_Series.pdf`](components/Murata_BLM18KG_Series.pdf) | BLM18KG221SN1D | Murata | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C88980](https://www.lcsc.com/product-detail/C88980.html) | 12 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/2d503a4b167da9bb5d0eb4a3fa711314.pdf?productCode=C88980) | `db7f1aefdecea42bfdcf1846baa8a24f` |
| [`HanRun_HR911130A.pdf`](components/HanRun_HR911130A.pdf) | HR911130A | HanRun | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C54408](https://www.lcsc.com/product-detail/C54408.html) | 2 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/d9b1e130e54a44fe9872ced55aa393e4.pdf?productCode=C54408) | `016cfcb3555bfa1da52ad523c3d828a4` |
| [`ShouHan_TYPE-C-6P.pdf`](components/ShouHan_TYPE-C-6P.pdf) | TYPE-C 6P(040新) | Shou Han | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C2887422](https://www.lcsc.com/product-detail/C2887422.html) | 6 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/21e9ea2f6088bcb89b8d161e55340285.pdf?productCode=C2887422) | `705c9518ce773443b7750342ad6db054` |
| [`Hroparts_DC-005-20A.pdf`](components/Hroparts_DC-005-20A.pdf) | DC-005-20A | Hroparts | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C136744](https://www.lcsc.com/product-detail/C136744.html) | 1 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/3fb28c31ab2bd394ffd80a5135c8ebd4.pdf?productCode=C136744) | `e82b5a22a2c34e02fd5ad9f5d709667c` |
| [`XFCN_PZ254V-11-02P.pdf`](components/XFCN_PZ254V-11-02P.pdf) | PZ254V-11-02P | XFCN | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C492401](https://www.lcsc.com/product-detail/C492401.html) | 1 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/3b85a1cdf6ed945f2e278f00c1e42442.pdf?productCode=C492401) | `7c34680ef9d17aeb1fb5beff8b7b998a` |
| [`Nationstar_NCD0603W1.pdf`](components/Nationstar_NCD0603W1.pdf) | NCD0603W1 | Nationstar | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C84265](https://www.lcsc.com/product-detail/C84265.html) | 2 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/c1604f506f40a56cfb4563eed227c948.pdf?productCode=C84265) | `bfa3e72144e5050dba3b357a3b2924a1` |
| [`Yangjie_1N4148WQ.pdf`](components/Yangjie_1N4148WQ.pdf) | 1N4148WQ | Yangjie | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C2942441](https://jlcpcb.com/partdetail/C2942441) | 5 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/c1e4abb31576787dd38fb72c7a9f2a10.pdf?productCode=C2942441) | `c281feaef5d6b6de88cf407ba1c2ea2b` |
| [`Roqang_RVT_Series.pdf`](components/Roqang_RVT_Series.pdf) | RVT1E221M0607 | Roqang | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C2918361](https://www.lcsc.com/product-detail/C2918361.html) | 6 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/28b7f65130241c48e650f325ce318c84.pdf?productCode=C2918361) | `440aa5c2ab0b232c665356d4ec988bef` |
| [`Samsung_CL_MLCC_Series.pdf`](components/Samsung_CL_MLCC_Series.pdf) | CL05B104KO5NNNC | Samsung | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C1525](https://www.lcsc.com/product-detail/C1525.html) | 84 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/02336ea48ea44ca18c72517dd3cb7b47.pdf?productCode=C1525) | `e2bdfdc06e3fdaa469ba6094d07dbe10` |
| [`Samsung_CL_MLCC_Series.pdf`](components/Samsung_CL_MLCC_Series.pdf) | CL05B103KB5NNNC | Samsung | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C15195](https://www.lcsc.com/product-detail/C15195.html) | 84 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/02336ea48ea44ca18c72517dd3cb7b47.pdf?productCode=C1525) | `e2bdfdc06e3fdaa469ba6094d07dbe10` |
| [`FH_MLCC_Series.pdf`](components/FH_MLCC_Series.pdf) | 0402B223K500NT | FH | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C1532](https://www.lcsc.com/product-detail/C1532.html) | 30 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/09fe2daf22580a99fa7fea93ccb20fb7.pdf?productCode=C1532) | `7fba32e11a9eff7548e7ac0f1cc32d58` |
| [`FH_MLCC_Series.pdf`](components/FH_MLCC_Series.pdf) | 0402CG220J500NT | FH | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C1555](https://www.lcsc.com/product-detail/C1555.html) | 30 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/09fe2daf22580a99fa7fea93ccb20fb7.pdf?productCode=C1532) | `7fba32e11a9eff7548e7ac0f1cc32d58` |
| [`FH_MLCC_Series.pdf`](components/FH_MLCC_Series.pdf) | 0805X106K250NT | FH | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C40894](https://www.lcsc.com/product-detail/C40894.html) | 30 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/09fe2daf22580a99fa7fea93ccb20fb7.pdf?productCode=C1532) | `7fba32e11a9eff7548e7ac0f1cc32d58` |
| [`FH_MLCC_Series.pdf`](components/FH_MLCC_Series.pdf) | 0603B103K500NT | FH | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C57112](https://www.lcsc.com/product-detail/C57112.html) | 30 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/09fe2daf22580a99fa7fea93ccb20fb7.pdf?productCode=C1532) | `7fba32e11a9eff7548e7ac0f1cc32d58` |
| [`FH_MLCC_Series.pdf`](components/FH_MLCC_Series.pdf) | 0603B104K500NT | FH | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C30926](https://www.lcsc.com/product-detail/C30926.html) | 30 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/09fe2daf22580a99fa7fea93ccb20fb7.pdf?productCode=C1532) | `7fba32e11a9eff7548e7ac0f1cc32d58` |
| [`FH_MLCC_Series.pdf`](components/FH_MLCC_Series.pdf) | 0603B105K500NT | FH | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C90540](https://www.lcsc.com/product-detail/C90540.html) | 30 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/09fe2daf22580a99fa7fea93ccb20fb7.pdf?productCode=C1532) | `7fba32e11a9eff7548e7ac0f1cc32d58` |
| [`FH_MLCC_Series.pdf`](components/FH_MLCC_Series.pdf) | 0603B102K500NT | FH | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C44369](https://www.lcsc.com/product-detail/C44369.html) | 30 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/09fe2daf22580a99fa7fea93ccb20fb7.pdf?productCode=C1532) | `7fba32e11a9eff7548e7ac0f1cc32d58` |
| [`FH_MLCC_Series.pdf`](components/FH_MLCC_Series.pdf) | 0603CG4R0B500NT | FH | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C507053](https://www.lcsc.com/product-detail/C507053.html) | 30 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/09fe2daf22580a99fa7fea93ccb20fb7.pdf?productCode=C1532) | `7fba32e11a9eff7548e7ac0f1cc32d58` |
| [`PSA_FN_MLCC_Series.pdf`](components/PSA_FN_MLCC_Series.pdf) | FN15X104K250PNG | PSA | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C525225](https://www.lcsc.com/product-detail/C525225.html) | 55 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/3d771c0c586676719f80e96a0f8d9dcd.pdf?productCode=C525225) | `8342ee8e65ac4074174d969c93d5f0cb` |
| [`UniRoyal_Chip_Resistor_Series.pdf`](components/UniRoyal_Chip_Resistor_Series.pdf) | 0402WGF1802TCE | Uni-Royal | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C25762](https://www.lcsc.com/product-detail/C25762.html) | 9 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25762) | `009dc6cbe05a919dafd0f2794851bdb1` |
| [`UniRoyal_Chip_Resistor_Series.pdf`](components/UniRoyal_Chip_Resistor_Series.pdf) | 0402WGF1002TCE | Uni-Royal | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C25744](https://www.lcsc.com/product-detail/C25744.html) | 9 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25762) | `009dc6cbe05a919dafd0f2794851bdb1` |
| [`UniRoyal_Chip_Resistor_Series.pdf`](components/UniRoyal_Chip_Resistor_Series.pdf) | 0402WGF2001TCE | Uni-Royal | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C4109](https://www.lcsc.com/product-detail/C4109.html) | 9 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25762) | `009dc6cbe05a919dafd0f2794851bdb1` |
| [`UniRoyal_Chip_Resistor_Series.pdf`](components/UniRoyal_Chip_Resistor_Series.pdf) | 0603WAF1500T5E | Uni-Royal | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C22808](https://www.lcsc.com/product-detail/C22808.html) | 9 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25762) | `009dc6cbe05a919dafd0f2794851bdb1` |
| [`UniRoyal_Chip_Resistor_Series.pdf`](components/UniRoyal_Chip_Resistor_Series.pdf) | 0603WAF5101T5E | Uni-Royal | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C23186](https://www.lcsc.com/product-detail/C23186.html) | 9 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25762) | `009dc6cbe05a919dafd0f2794851bdb1` |
| [`UniRoyal_Chip_Resistor_Series.pdf`](components/UniRoyal_Chip_Resistor_Series.pdf) | 0603WAF4701T5E | Uni-Royal | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C23162](https://www.lcsc.com/product-detail/C23162.html) | 9 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25762) | `009dc6cbe05a919dafd0f2794851bdb1` |
| [`UniRoyal_Chip_Resistor_Series.pdf`](components/UniRoyal_Chip_Resistor_Series.pdf) | 0402WGF4701TCE | Uni-Royal | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C25900](https://www.lcsc.com/product-detail/C25900.html) | 9 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25762) | `009dc6cbe05a919dafd0f2794851bdb1` |
| [`UniRoyal_Chip_Resistor_Series.pdf`](components/UniRoyal_Chip_Resistor_Series.pdf) | 0402WGF4700TCE | Uni-Royal | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C25117](https://www.lcsc.com/product-detail/C25117.html) | 9 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25762) | `009dc6cbe05a919dafd0f2794851bdb1` |
| [`FH_RS_Chip_Resistor_Series.pdf`](components/FH_RS_Chip_Resistor_Series.pdf) | RS-06000JT | FH | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C115323](https://www.lcsc.com/product-detail/C115323.html) | 22 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/8d58778925076bf80f4c3e6ed51a56f5.pdf?productCode=C115323) | `448794996c052b7ab77b559064faf5eb` |
| [`Yageo_RC_Chip_Resistor_Series.pdf`](components/Yageo_RC_Chip_Resistor_Series.pdf) | RC0402FR-072K49L | Yageo | [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [C145071](https://www.lcsc.com/product-detail/C145071.html) | 11 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/b426be3ce22c6de3e0c3a2248e49159e.pdf?productCode=C145071) | `5fde60816c1635e407015bb17d2aca5b` |
| [`SCT_SCT2622.pdf`](components/SCT_SCT2622.pdf) | SCT2622 | SCT | [LX-IS601F V2.0](../research/switch-board-strapping.md#lx-is601f-v20) | [C5361735](https://www.lcsc.com/product-detail/C5361735.html) | 20 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/3e2302a88c5d5931afc99053bc7d0f60.pdf?productCode=C5361735) | `c0dba9386da14ecb9b75052283f4d8d7` |
| [`Hangshun_HK24C08.pdf`](components/Hangshun_HK24C08.pdf) | HK24C08 | Hangshun | [LX-IS601F V2.0](../research/switch-board-strapping.md#lx-is601f-v20) | [C495286](https://jlcpcb.com/partdetail/C495286) | 18 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/d48086d7ea0be283ec149c0a454b0107.pdf?productCode=C495286) | `87c4ae4b7c342ffeb5f5e15c40333df9` |
| [`LGE_SS52-SS520_Series.pdf`](components/LGE_SS52-SS520_Series.pdf) | SS510 | LGE | [LX-IS601F V2.0](../research/switch-board-strapping.md#lx-is601f-v20) | [C432296](https://www.lcsc.com/product-detail/C432296.html) | 2 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/8c76779574fa824d162bd3d5d1ab8dfa.pdf?productCode=C432296) | `e7a7dfa42d117ae5476c1ffc29a00c8e` |
| [`LGE_SS32-SS320_Series.pdf`](components/LGE_SS32-SS320_Series.pdf) | SS310 | LGE | [LX-IS601F V2.0](../research/switch-board-strapping.md#lx-is601f-v20) | [C432297](https://www.lcsc.com/product-detail/C432297.html) | 2 | [LCSC](https://datasheet.lcsc.com/datasheet/pdf/76ffbae64c4211150af031a34f309e4b.pdf?productCode=C432297) | `06459a91a345615c2e9523b889e8853b` |
| [`Usakro_UKG2401PR.pdf`](components/Usakro_UKG2401PR.pdf) | UKG2401PR | Usakro | [LX-IS601F V2.0](../research/switch-board-strapping.md#lx-is601f-v20) | None | 5 | [szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20251231/8F77EB1084DA065C91E50931DB5ED80E.pdf) | `bf1f01eb85364bd628da2017db71eeea` |

[`Usakro_UKG2401PR.pdf`](components/Usakro_UKG2401PR.pdf) is the closest published match to the `United-tek G2401PR` port
magnetics ([DXFRM2](../research/switch-board-strapping.md#major-components)) on the LX-IS601F V2.0 board. It is a 24-pin gigabit LAN transformer of the
same kind but is not confirmed to be the same part.

The LX-IS601F V2.0 rows are catalogue parts matched from the markings on the board, not known purchases.
[`Hangshun_HK24C08.pdf`](components/Hangshun_HK24C08.pdf) is one of several pin-compatible 24C08 parts; the maker of the
`24C08` fitted as [U10](../research/switch-board-strapping.md#major-components) is not identified.

## Board components (not found)

No datasheet is available for these parts. The Designator column gives the first designator that carries the part; the
full lists are in [`../research/switch-board-strapping.md`](../research/switch-board-strapping.md).

| Board | Designator | Part | Maker | LCSC | Status |
| --- | --- | --- | --- | --- | --- |
| [wu-kou YT9215S V2.0](../research/switch-board-strapping.md#wu-kou-yt9215s-v20) | [F1](../research/switch-board-strapping.md#major-components-1) | BSMD1206-075-30V | BHFuse | [C976305](https://www.lcsc.com/product-detail/C976305.html) | No PDF at LCSC |
| [LX-IS601F V2.0](../research/switch-board-strapping.md#lx-is601f-v20) | [DXFRM2](../research/switch-board-strapping.md#major-components) | G2401PR | United-tek | None | No datasheet under this name |
| [LX-IS601F V2.0](../research/switch-board-strapping.md#lx-is601f-v20) | [ED1](../research/switch-board-strapping.md#major-components) | Marking `05U` | Not identified | None | Marking not identified |
| [LX-IS601F V2.0](../research/switch-board-strapping.md#lx-is601f-v20) | [Module U1](../research/switch-board-strapping.md#major-components) | Marking `2184A` | Not identified | None | Marking not identified |
| [LX-IS601F V2.0](../research/switch-board-strapping.md#lx-is601f-v20) | [Module D1](../research/switch-board-strapping.md#major-components) | Marking `2616 RGS` | Not identified | None | Marking not identified |

For the G2401PR, the nearest match is the [Usakro UKG2401PR](components/Usakro_UKG2401PR.pdf) in [Board components (included)](#board-components-included).

## Realtek (linked, not included)

The Realtek datasheets are marked "CONFIDENTIAL: Development
Partners Only" and say they may not be reproduced without Realtek's written permission.
They are therefore linked, not copied into this repository.

| Part | Document | Revision | Pages | Where |
| --- | --- | --- | --- | --- |
| RTL8363NB-VB-CG | Datasheet | Rev. 1.2 | 68 | [szlcsc](https://atta.szlcsc.com/upload/public/pdf/source/20240423/989DCAA6328F19215A910B22766A32D7.pdf) |
| RTL8363NB-VB-CG | Datasheet | Rev. 1.2 | 68 | [LCSC C2835942](https://www.lcsc.com/datasheet/C2835942.pdf) |
| RTL8367S-CG | Datasheet | Rev. Pre-0.941 | 82 | [framboise314.fr mirror](https://www.framboise314.fr/wp-content/uploads/2021/06/RTL8367S-CG_Datasheet.pdf) |
| RTL8367S-CG | Datasheet | Rev. Pre-0.941 | 82 | [LCSC C2760849](https://www.lcsc.com/datasheet/C2760849.pdf) |
| RTL8364NB-VB-CG | Datasheet | Not recorded | Not recorded | [LCSC C3013610](https://www.lcsc.com/datasheet/C3013610.pdf) |
| RTL8305NB-CG | Datasheet | Not recorded | Not recorded | [LCSC C52146](https://www.lcsc.com/datasheet/C52146.pdf) |
| RTL8305NBI-VB-CG | Datasheet | Not recorded | Not recorded | [LCSC C42451794](https://www.lcsc.com/datasheet/C42451794.pdf) |
| RTL8367RB | Register Table | V1.0.0 | Not recorded | [GitHub attachment](https://github.com/user-attachments/files/18147305/RTL8367RB_RTL8367MB_Register_Table_V1.0.0.pdf) |
| RTL8367MB | Register Table | V1.0.0 | Not recorded | [GitHub attachment](https://github.com/user-attachments/files/18147305/RTL8367RB_RTL8367MB_Register_Table_V1.0.0.pdf) |

The RTL8305NB-CG and RTL8305NBI-VB-CG are 10 Mbit/s and 100 Mbit/s parts, listed for comparison. The
register table is a leaked document that covers both the RTL8367RB and the RTL8367MB.

## Other references

| What | Where |
| --- | --- |
| Motorcomm switch product page | <https://www.motor-comm.com/product/switching-chip> |
| Linux DSA driver for YT921x | [`drivers/net/dsa/motorcomm/`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/net/dsa/motorcomm) |
| Device-tree binding for YT921x | [`motorcomm,yt921x.yaml`](https://www.kernel.org/doc/Documentation/devicetree/bindings/net/dsa/motorcomm%2Cyt921x.yaml) |
| OpenWrt thread on IPQ5018 + YT9215S | <https://forum.openwrt.org/t/ipq5018-and-motorcomm-yt9215s/239942> |
| Synopsys DW8051 core inside the RTL8367S | [Datasheet hosted by Keil](https://www.keil.com/dd/docs/datashts/synopsys/dw8051_ds.pdf) |
| Open-hardware YT9215S 5-port switch board | <https://github.com/mithro/wu-kou-qian-zhao-jiao-huan-ji-_yt9215s_v2_0> |
