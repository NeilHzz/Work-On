# Acta Biomaterialia 投稿前修改指南

目标：将稿件从“强机制证明”调整为“高度一致的跨尺度关联框架”，重点降低编辑初筛和审稿阶段最可能出现的三类风险：统计独立性、因果表述过强、数据开放不足。

## 总体判断

当前稿件主线适合 Acta Biomaterialia：OVAL glycan state -> Ca2+ surface accessibility -> mammillary architecture -> local structure-function response，符合该刊强调的 structure-property-function relationships。

但不建议原样投稿。送审前必须先处理统计层级、因果语气、数据可得性和 Word 字符损坏。

## 一、必须修改

### 1. 统计独立性表述降级

涉及位置：

- Fig. 1D mammillary morphometry
- Fig. 5B-C finite-element outcomes
- Statistical Analysis
- Results 中所有与上述图相关的显著性表述

核心问题：

Fig. 1D 的 9 个点来自一个 scanned fragment 内的 subfragments；Fig. 5 的 9 个点来自一个 reconstructed fragment 内的 loading positions。它们不是独立 biological replicates。

必须避免的表达：

- species means differed significantly
- chicken was significantly higher than duck and pigeon
- Tukey groupings demonstrate species-level difference
- n = 9 per species, without qualification

推荐表达：

> Within the sampled fragment, chicken showed the highest mammillary density, whereas duck and pigeon were lower and overlapping.

> These values represent regional or positional sampling within one reconstructed fragment per species and should not be interpreted as independent biological replication.

> The statistical tests describe within-fragment or within-model separation under the sampled conditions.

建议处理方式：

- 保留 p values 可以，但必须明确其层级是 regional / positional sampling。
- Results 中的显著性语言降级为 pattern / separation / grouping。
- Discussion 中避免用这些 p values 直接支撑 species-level biological conclusion。

### 2. 因果链语气削弱

核心问题：

当前稿件从 OVAL glycan state 到 mammillary architecture 再到 local response 的链条较完整，但证据性质主要是 association、structural modelling 和 finite-element readout，不是直接因果验证。

建议全局替换方向：

- links -> is associated with / aligns with
- drives -> is consistent with
- determines -> is compatible with
- upstream of -> positioned before / plausibly precedes
- providing a route from -> suggesting a plausible route from
- functional endpoint -> local functional readout
- demonstrates -> supports / indicates / is consistent with

摘要中建议改写：

> Rebuilt OVAL glycoform ensembles were consistent with a Ca2+ surface-accessibility gradient, suggesting a plausible route by which glycan state could modulate matrix-mineral presentation during mammillary-layer formation.

> This ordering aligned with mammillary density and a local inside-out loading readout after separating thickness-driven force effects.

Discussion 中建议保留的边界句：

> Although this result does not establish direct causality, it supports a model in which glycan-state variation on a shared matrix protein is associated with mineral-facing surface accessibility and mammillary-layer organization.

### 3. 糖蛋白组采样深度不平衡必须解释

涉及位置：

- Results, Fig. 2 section
- Discussion, OVAL prioritization paragraph

核心问题：

chicken glycoproteomic catalog 明显小于 duck 和 pigeon。审稿人可能质疑 OVAL 差异是否来自 MS sampling depth、database quality 或 enrichment bias。

建议加入：

> Because glycoproteomic sampling depth differed among species, species-private catalog size was not interpreted as a direct measure of biological complexity. Downstream comparisons therefore focused on shared-core similarity, ortholog-restricted candidates, and matched OVAL glycoform states.

建议进一步说明：

> This strategy reduced dependence on species-private detection depth and prioritized features that were comparable across orthologous proteins.

避免表达：

- chicken contributed little private cluster space, if interpreted biologically without qualification
- true lower chicken glycoproteome complexity
- lineage-specific absence, unless supported by detection-independent evidence

### 4. Word 字符损坏必须修复

当前稿件中存在真实问号字符和转义残留，会影响编辑初筛观感。

必须替换：

- `mean ? s.d.` -> `mean ± s.d.`
- `shaded ?1? envelopes` -> `shaded ±1 s.d. envelopes`
- `kg/m?` -> `kg/m3` 或 `kg/m³`
- `3.0 ? 10^10` -> `3.0 × 10^10`
- `1.5 ? 10^7` -> `1.5 × 10^7`
- `1.0 ? 10^-4` -> `1.0 × 10^-4`
- `1 ? 10^-8` -> `1 × 10^-8`
- `3 ? 3 grid` -> `3 × 3 grid`
- `Tukey HSD; ? = 0.05` -> `Tukey HSD; α = 0.05`
- `Writing?original draft` -> `Writing - original draft`
- `Writing?review and editing` -> `Writing - review and editing`
- `surface\.` -> `surface.`

如需保持纯 ASCII，可将乘号和上标写成：

- `kg/m3`
- `3.0 x 10^10`
- `alpha = 0.05`

但投稿稿件中推荐使用正式数学符号。

### 5. Data availability 强化

当前版本：

> All data supporting the findings of this study are included within the article and its Supplementary Materials, as well as from the corresponding authors upon reasonable request.

问题：

对含 proteomics、glycoproteomics、structural modelling、finite-element analysis 的稿件而言，这句话偏弱。

推荐改写：

> Processed proteomic and glycoproteomic tables, morphometric measurements, structural-model descriptors, finite-element summary outputs, and plotting/statistical scripts are provided in the Supplementary Materials or deposited in [repository].

> Raw mass-spectrometry files and finite-element input files are available at [DOI/link] or from the corresponding author pending repository release.

如果暂时没有 DOI：

> The repository accession or DOI will be provided before publication.

更稳妥的投稿前方案：

- raw MS files: ProteomeXchange / PRIDE / iProX
- processed tables: Supplementary Tables and Zenodo
- scripts: GitHub or Zenodo
- FE inputs and summary outputs: Zenodo

## 二、建议修改

### 1. 标题收紧

当前标题：

> Glycan-State Variation in Ovalbumin Links Eggshell Matrix Chemistry to Biomineral Architecture and Local Structure-Function Response

推荐标题：

> Ovalbumin Glycan-State Variation Links Eggshell Matrix Chemistry to Biomineral Architecture and Local Response

理由：

更短，保留 OVAL、matrix chemistry、biomineral architecture 和 local response 四个核心信号。

### 2. Fig. 4 正文压缩

问题：

当前正文对 numbered markers、panel meaning 和图中视觉元素解释较多，读起来接近 figure caption。

建议：

- 正文只保留结论：glycan envelope、acidic interface shielding、Ca2+ accessibility。
- numbered markers 的说明放在 caption。
- 减少 “In panel A terms” 和 “With panel B in mind” 这类引导语。

推荐正文方向：

> Glycan-class progression was reflected in the spatial envelope and surface engagement of the rebuilt OVAL glycoforms. Compact chicken glycans preserved the greatest accessible acidic surface, whereas extended pigeon glycans produced stronger steric and electrostatic shielding. Duck occupied an intermediate structural state.

### 3. FEA 边界条件再限定

涉及位置：

- Results, Fig. 5 section
- Discussion, finite-element interpretation
- Methods, Finite-element analysis

建议加入：

> These simulations were intended as matched-geometry comparisons of local response and were not used to estimate absolute shell-breaking force.

> The finite-element outputs should therefore be interpreted as geometry-dependent local readouts under standardized material assumptions.

重点避免：

- direct proof of shell-breaking mechanics
- species-specific fracture strength
- absolute mechanical superiority

### 4. AVONET 背景压缩

问题：

AVONET 10,993 species comparison 增强设计感，但 Acta 读者最关心材料机制。生态和发育背景不宜压过 biomaterials question。

建议：

- 保留 species selection 的合理性。
- 减少 macroecological 展开。
- 尽快进入 mammillary layer 和 matrix chemistry。

Introduction 末段可加入 Acta 定位句：

> This framework addresses a biomaterials question central to Acta Biomaterialia: how molecular matrix state maps onto mineral architecture and local material response.

## 三、可不大改

### 1. 不需要更换主线

OVAL glycan state 是当前最强主线，因为它满足：

- shared across species
- abundant matrix protein
- glycan-state difference clear
- structurally actionable
- connected to Ca2+ accessibility
- aligned with mammillary architecture and local response

### 2. 不需要删除 FEA

FEA 对 Acta Biomaterialia 是加分项，但必须定位为 local readout，而不是 fracture proof。

### 3. 不需要完全删除生态背景

生态和 developmental gradient 可以作为 comparative design 的理由保留，但不要成为论文主卖点。

### 4. 不需要大幅增加新实验

当前送审目标应是降低过度声称和统计风险，而不是临时增加复杂实验。新增实验只应作为 Discussion limitation 和 future causal test。

## 四、推荐执行顺序

1. 修复 Word 字符损坏。
2. 强化 Data availability。
3. 统一削弱因果语气。
4. 降级 Fig. 1 和 Fig. 5 的统计独立性表述。
5. 压缩 Fig. 4 正文解释。
6. 收紧 AVONET 和生态背景。
7. 最后检查摘要、标题、Discussion summary 是否与全文语气一致。

## 五、投稿前最终检查清单

- [ ] 所有 `?` 字符已确认不是损坏符号。
- [ ] 所有 `\.` 已删除。
- [ ] Fig. 1D 的 n = 9 已说明为 within-fragment regional replicates。
- [ ] Fig. 5 的 n = 9 已说明为 loading positions, not biological replicates。
- [ ] 摘要没有过强因果词。
- [ ] Discussion 明确说明 association/model，不声称 direct causality。
- [ ] Glycoproteomic sampling depth imbalance 已解释。
- [ ] Data availability 包含 raw MS、processed data、scripts、FE inputs 或 repository plan。
- [ ] FEA 被定位为 matched local geometry readout。
- [ ] 标题、摘要、最后总结段的主张强度一致。

## 六、编辑初筛风险排序

1. Pseudoreplication / statistical independence。
2. Causal overclaiming。
3. Data availability 不足。
4. Word 字符损坏。
5. FEA 边界条件和真实性解释不足。
6. 生态背景过长导致 Acta 材料主线被稀释。

## 七、建议最终定位

推荐将稿件定位为：

> A cross-scale biomaterials study showing that glycan-state variation on a shared eggshell matrix protein is associated with Ca2+-relevant surface accessibility, mammillary biomineral architecture, and a standardized local loading readout.

不推荐定位为：

> A definitive causal mechanism proving that OVAL glycosylation determines species-specific eggshell fracture mechanics.
