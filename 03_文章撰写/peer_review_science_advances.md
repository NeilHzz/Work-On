# Science Advances 送审前同行评审意见

评审对象：`cover_letter260608.docx`、`manuscript260608v4.docx`、`supplementary_materials260608.docx`、`Table_S1` 至 `Table_S7`。  
说明：已按要求忽略作者信息和占位符；本轮未做外部文献真实性核查。

## 编辑初筛结论

我认为该稿件具备送外审的科学基础，不建议编辑部直接拒稿；但在送审前应先完成技术性清理，尤其是表格残留信息、数据/代码可用性表述、统计独立性表述和若干正文低级错误。

## （1）直接错误和低级问题

1. `cover_letter260608.docx` 日期为 `2026/6/9`，而当前提交包日期为 2026-06-08；如今天提交，应改为 2026-06-08。

2. `manuscript260608v4.docx` 总词数约 12,413 词；如按 Science Advances Research Article 常规总词数口径检查，可能偏长，建议投稿前用期刊系统或模板复核。

3. 主文所有标题和图题均使用 `Normal` 样式，而非 Word 标题样式；这不一定导致拒收，但会降低自动目录、结构解析和生产处理稳定性。

4. 主文第 1 处结果段落有大小写错误：`pigeon was dominated by discrete triangular-conical mammillae.` 应改为 `Pigeon...` 或改写为 `In pigeon, ...`。

5. 主文机械结果段落有大小写错误：`By contrast, Chicken exhibited...` 应改为 `By contrast, chicken exhibited...`。

6. 主文中 `Ca²⁺surface`、`Ca²⁺accessible`、`Ca²⁺relevant`、`Ca²⁺hotspots` 等至少 24 处缺少空格或连字符；建议统一为 `Ca²⁺-surface`、`Ca²⁺-accessible`、`Ca²⁺-relevant`、`Ca²⁺ hotspots`。

7. 主文结果中单位写作 `per mm2`，应改为 `per mm²`。

8. 英文拼写风格不统一：主文多用 `organisation/modelling/behaviour/favourable`，封面信用 `modeling/organization`；建议全稿统一为美式或英式。Science Advances 通常更适合统一为美式。

9. 主文 Fig. 4 结果段中 `Fig. 4G to J resolved...` 以图号开头，读起来接近图例而不是结果叙述；建议改为一句普通结果句。

10. 主文 Fig. 2B 相关叙述与 `Table_S2_Glycan_MS.xlsx` 不一致：正文称 duck 有 321 个 glycoproteins 和 547 个 glycosites；表中 `Anas_Site_quant` 实际为 320 个 unique proteins、546 个 nonempty glycosites，`Anas_Summary` 也列出 320 个 identified proteins。

11. `supplementary_materials260608.docx` 写有 `This PDF file includes:`，但当前提交文件是 `.docx`；若最终作为 PDF 上传则无问题，否则应改为 `This file includes:`。

12. 补充材料 Fig. S1 图例使用 `R^2`，建议改为 `R²` 或按期刊文本规范写作。

13. 补充材料 Fig. S11 图例使用 `3 x 3`，建议改为 `3 × 3`。

14. `Table_S1_Protein_MS.xlsx` 和 `Table_S2_Glycan_MS.xlsx` 的 Summary sheets 保留了 `Unnamed: 0`、`Header line description...` 等导出残留字段；这些会让审稿人感觉表格未经整理。

15. `Table_S2_Glycan_MS.xlsx` 中存在 `Gallus_Sheet1`，但该 sheet 实际包含 Gallus、Anas、Columba 的 OVAL 相关行，命名和内容不匹配；应重命名、解释或删除。

16. `Table_S3_Ortholog_GO_CAFE5.xlsx` 和 `Table_S6_ReGlyco_Ensemble_Stats.xlsx` 含中文 sheet 名或中文列名；若面向国际审稿，建议统一为英文。

17. 多个 Excel sheet 名因 Excel 长度限制被截断，例如 `GO_Enrichment_Gallus (chicken o`、`Force_YDirection_Chicken_Summar`；建议在 `Table_Description` 中列出完整说明，或使用短而完整的英文名。

18. 数据和代码可用性声明称 “All data and code needed ... are present in the paper and/or the Supplementary Materials”，但提交包中没有脚本、raw MS 文件、micro-CT 体数据、STL/FEA keyword decks、APBS/PQR/DX 文件或 Re-Glyco 模型文件；这属于送审前必须修正的问题。

## （2）文章评价和审稿问题

### 总体评价

稿件的核心优点是把 eggshell mammillary morphology、glycoproteomics、OVAL glycan state、结构建模、电静力学和 inside-out FEA 串成一个跨尺度机制框架。题目和摘要能明确提出广义 biomineralization 问题，且不仅是描述性比较。以 Science Advances 的编辑视角看，这个方向有潜在广泛兴趣，适合送给 biomineralization、glycoproteomics/structural glycobiology 和 biomechanics 三类审稿人。

主要风险是因果链条目前仍偏推断：`glycan state -> Ca²⁺ surface accessibility -> mammillary organization -> hatching mechanics` 的每个环节都有数据支持，但跨环节的因果连接主要来自相关性、模型和一致性排序，而非直接扰动实验。

### 需要审稿人重点追问的问题

1. 物种设计是否足以支持跨物种机制结论？当前只有 chicken、duck、pigeon 三个家养或常见模型物种，生态、发育方式、系统发育、品系、蛋龄和母体背景高度耦合。作者需要更清楚地限定结论为 “three-species comparative framework”，避免泛化为鸟类普遍规律。

2. micro-CT 形态学的生物学重复不足。每个物种只有一个扫描 fragment，九个 subfragments 是区域重复而非独立生物重复。主文虽已说明这一点，但 ANOVA/Tukey 的显著性表达仍可能让读者误以为有 n=9 biological replicates。

3. FEA 的九个 offset positions 也不是独立生物重复。`p = 1.64 × 10⁻¹³` 和 `p = 6.64 × 10⁻¹⁰` 可能严重高估证据强度；建议审稿人要求作者将 FEA 统计改为位置敏感性分析或模型内重复，而不是物种级统计推断。

4. glycoproteomics 检测深度不平衡：Gallus 检出 55 个 glycoproteins，而 Anas/Columba 分别约 320/192 个。需要解释这是生物学差异、样品处理差异、数据库注释差异还是检测深度差异；否则 shared-core 和 “dominant glycan class” 可能受检测偏差影响。

5. OVAL site comparability 需要更强证据。鸡为 N293，鸭和鸽为 N97；作者应展示序列比对和三维结构映射，证明这些 sequons 在结构和功能解释上可比较。

6. 从 glycan composition 到 glycan structure 的不确定性需要更透明。MSFragger/Oxford class 给出的是 composition/class 层面信息，而 Re-Glyco 建模使用 mass matching 和 GlycoShape library；连接方式、isomer 选择、sialylation positional uncertainty 都可能影响结构结论。

7. APBS hotspot 阈值 `< -5 kT/e` 和 Ca²⁺-relevant surface 定义需要敏感性分析。审稿人应要求作者说明阈值改变、离子强度、pH、dielectric、glycan charge assignment 是否改变物种排序。

8. FEA 物理设定需要更强验证。所有物种使用相同材料参数、egg-tooth impactor 使用 IRON-ARMCO、初速度为 50,000 mm/s、并启用 erosion 和 mass scaling；这些设定需要与实际 hatching mechanics 或文献范围建立更清楚的联系。

9. `τ_max` 被解释为比 `F_max` 更少受厚度影响，但它仍受局部几何、接触面积、网格、材料模型和边界条件影响。需要证明该指标确实隔离了 mammillary-interface mechanics，而不是另一种模型归一化输出。

10. “hatching-favourable” 和 “shell-breaking mechanics” 的表述略强。稿件没有直接测量 hatchability、embryo force、egg-tooth force 或真实破壳过程；建议把结论限定为 “hatching-relevant local mechanics”。

11. OVAL 的核心性需要与 OC116、TRFE、OC17 更清楚地区分。当前 OVAL 是最清晰的可建模信号，但还不能证明它是唯一或主导因子；建议审稿人要求作者增加 negative/alternative protein controls 或更明确解释筛选标准。

12. 统计策略需要收紧。作者说明未做 multiple-testing correction，但全文涉及 glycan classes、ortholog comparisons、ensemble descriptors、hotspots、FEA 等多层测试；应至少区分 confirmatory tests 和 exploratory tests。

13. Re-Glyco ensemble 的 conformers 不应被当作独立生物样本。结构 ensemble 可用于不确定性和构象范围，但显著性检验的独立性假设需要重新表述。

14. 数据可用性是送审和发表的关键短板。建议审稿人要求 raw MS data、search parameters、processed tables、micro-CT volumes、segmentation masks、STL meshes、Ansys/LS-DYNA input decks、APBS input/output、Re-Glyco models 和分析脚本进入公开仓库并给出 DOI/accession。

15. 文章叙事质量总体较好，但 Discussion 多处重复强调同一链条。若进入修回，建议压缩重复段落，把空间让给统计限制、数据可用性和模型敏感性。

### 建议外审人类型

1. Avian eggshell biomineralization / mammillary layer specialist.
2. Glycoproteomics or structural glycobiology reviewer familiar with N-glycan composition-to-structure uncertainty.
3. Computational biomechanics / finite-element modeling reviewer with explicit dynamics experience.

