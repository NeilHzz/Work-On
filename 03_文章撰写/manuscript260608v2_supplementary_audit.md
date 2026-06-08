# manuscript260608v2 附图附表复核

复核对象：

- 主文：`0_Manuscript/manuscript260608v2.docx`
- 补充材料：`0_Supplementary_materials/supplementary_materials260605.docx`
- 独立附图源文件：`Supplementary/Figures`
- 独立附表源文件：`Supplementary/Tables`

## 结论

当前补充材料 Word 内嵌图像未发现空白或导出失败，主文引用到的 `Fig. S2/S3/S4/S5/S10/S11` 在补充材料中均有对应图注；但提交前仍需修正 4 类问题。

## 已通过

- `supplementary_materials260605.docx` 标明包含 `Figs. S1 to S11`、`Tables S1 to S7`，与内嵌图像数量和附表文件数量基本一致。
- 主文当前引用的补充图号为 `Fig. S2`、`Fig. S3`、`Fig. S4`、`Fig. S5`、`Fig. S10`、`Fig. S11`，在 `supplementary_materials260605.docx` 中均存在对应图注。
- 附表文件 `SuppTable1` 到 `SuppTable7` 均可打开，工作表结构完整，未发现损坏文件。
- `supplementary_materials_en.docx` 判断为旧版，不建议作为当前提交版本使用。

## 需要修正

1. `Fig. S10` 图注与实际图像不一致。
   - 当前图注写的是 glycan radius of gyration、end-to-end distance 和 Nhot。
   - 实际内嵌图是 `Total Ca2+ Hotspots`、`Glycan-Shielded Hotspots` 和 `Hotspot Count Trajectory Across 50 Conformations`。
   - 建议按实际图像重写 `Fig. S10` 图题和图注。

2. `Fig. S11` 图注与实际图像表述不够精确。
   - 实际图像标题均为 `Contact Y-Force vs Time`，并同时显示 Y-force 与 T_normal/τ normal 曲线。
   - 当前图注称 `(A-C) Contact force (F)`、`(D-F) Y-direction reaction-force`，容易造成变量定义混淆。
   - 建议改为按物种顺序说明每组 3 x 3 offset 曲线和汇总 Y-force 曲线，并明确实线/虚线分别代表的力学变量。

3. 主文方法中的 `Supplementary Table 1` 指向不准确。
   - 主文写道：目标蛋白最终 UniProt ortholog identifiers listed in `Supplementary Table 1`。
   - 当前 `SuppTable1_Protein_MS.xlsx` 是蛋白质组 MS 数据，不是目标 ortholog identifier 清单。
   - 目标 ortholog 信息实际更接近 `SuppTable3_Ortholog_GO_CAFE5.xlsx` 的 `BlastP_目标蛋白识别结果` 工作表。
   - 建议把主文改为 `Supplementary Table 3`，或把目标 ortholog identifier 摘要表移动/复制到 `Table S1`。

4. 独立附图源文件夹与补充材料 Word 的编号不一致。
   - `Supplementary/Figures` 目前只有 `SuppFig1` 到 `SuppFig8` 文件夹。
   - `supplementary_materials260605.docx` 中是 `Fig. S1` 到 `Fig. S11`。
   - 其中源文件夹 `SuppFig6_Mammilla_Microstructure` 不对应当前 `Fig. S6` 图注；`Fig. S9-S11` 也没有按编号独立文件夹整理。
   - 建议提交前按 `FigS01` 到 `FigS11` 重新导出并整理独立图源，避免上传时错配。

## 可选微调

- `Fig. S7` 图注中的 `surface electrostatic maps` 可改为 `surface-potential distributions and residue-level APBS potential maps`，更贴合当前图像内容。
- `supplementary_materials260605.docx` 标题仍为 `Cross-species OVAL glycan states connect mammillary-layer organisation to hatching-favourable eggshell mechanics`，建议与主文题名 `OVAL glycan states link eggshell matrix chemistry to avian shell-breaking mechanics` 统一。
