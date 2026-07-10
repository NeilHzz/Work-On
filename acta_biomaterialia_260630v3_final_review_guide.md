# manuscript260630v3 最终审阅修改指南

审阅对象：`03_文章撰写/0_Manuscript/manuscript260630v3.docx`

对标范文：

- Liu et al., *Mechanical design principles of avian eggshells for survivability*, Acta Biomaterialia 178, 233-243. DOI: 10.1016/j.actbio.2024.02.036
- Rodríguez-Navarro et al., *Guinea fowl eggshell structural analysis at different scales reveals how organic matrix induces microstructural shifts that enhance its mechanical properties*, Acta Biomaterialia 178, 244-256. DOI: 10.1016/j.actbio.2024.03.001

## 总体判断

`manuscript260630v3.docx` 是目前最稳的一版。它已经不再硬做 eggshell mechanics / survivability 文章，而是明确转向：

> matrix glycan chemistry -> mammillary biomineral architecture -> standardized local response

这个定位比 v2 更接近 Guinea fowl 那篇多尺度结构机制范文，也避开了 Liu et al. 那篇力学设计原则文章的强项。

## 编辑视角判断

v3 已经可以进入送审考虑。

主要原因：

- 标题方向清楚。
- 摘要语气稳健。
- Fig. 1 已从 AVONET 主导转为 local shell-opening interface / mammillary architecture 主导。
- Discussion 已明确证据边界。
- Data availability 已包含 Zenodo DOI。
- FEA 已定位为 standardized local readout，而不是 fracture proof。

当前标题：

> Ovalbumin Glycan-State Variation Links Eggshell Matrix Chemistry to Biomineral Architecture and Local Response

评价：

标题可用，核心信号明确：OVAL、glycan-state variation、matrix chemistry、biomineral architecture、local response。

## 审稿人视角的剩余风险

### 1. FEA 仍可能被力学审稿人追问

当前稿件已经强调：

- not whole-shell fracture performance
- not absolute shell-breaking force
- not species-specific fracture mechanics proof
- standardized local functional readout

这已经正确。

剩余风险：

- `50,000 mm/s` impact velocity 可能被问。
- mass scaling 可能被问。
- fully fixed perimeter 可能被问。
- 单 fragment 模型可能被问。
- mesh size / parameter sensitivity 可能被问。

建议准备 Supplement 支撑：

- mesh sensitivity test
- velocity or loading-rate rationale
- boundary condition rationale
- material parameter source
- explanation that FEA is comparative and geometry-normalized, not predictive fracture modelling

建议正文不再继续扩写 FEA，避免把它重新变成主卖点。

### 2. 统计层级仍是软肋，但已可控

当前稿件已经说明：

- Fig. 1D 是 regional sampling within one scanned fragment。
- Fig. 5 是 positional sampling within one reconstructed fragment。
- these are not independent biological replicates。

评价：

pseudoreplication 风险已从高风险降为可控风险。

剩余风险：

审稿人可能仍认为 Fig. 1/Fig. 5 的统计只支持 descriptive pattern，而不是 species-level biological inference。

建议：

- 正文不要再加强显著性语言。
- Fig. 5 caption 可保留 p values，但正文不再突出 p values。
- Discussion 继续保持 association / pattern / alignment 语言。

### 3. OVAL 因果性已降级，但链条仍长

当前稿件已加入关键边界句：

> The study does not claim a complete causal chain; it identifies a convergent cross-scale association among matrix glycan state, mammillary architecture, and standardized local response.

评价：

这句话很关键，应保留。

剩余风险：

从 glycan-state 到 mammillary architecture 再到 local response 的链条仍然较长，任何一环都可能被审稿人要求更多验证。

建议：

- 不再增强因果词。
- 避免 `drives`、`determines`、`proves`。
- 保持 `associated with`、`aligned with`、`consistent with`、`supports a model`。

## 与两篇范文的关系

### 1. 与 Liu et al. 的关系

Liu et al. 的强项是：

- fracture / crack behavior
- membrane effect
- experiments plus FEA
- survivability model
- whole-shell mechanical design principle

你的稿件不应主打这些方向。

v3 已经成功避开：

- mechanical superiority
- survivability design principle
- species-specific fracture strength
- whole-shell fracture proof

应继续保持：

> FEA is a standardized local readout, not a whole-shell mechanics claim.

### 2. 与 Rodríguez-Navarro et al. 的关系

Guinea fowl 范文的强项是：

- organic matrix
- multiscale structural analysis
- microstructural shifts
- enhanced mechanical properties

你的稿件更接近这一路线，但应突出自己的升级点：

> organic matrix is resolved to OVAL glycan-state variation.

推荐主卖点：

> OVAL glycan-state variation is a molecularly resolved matrix feature aligned with mammillary biomineral architecture and standardized local response.

## 已通过的关键检查

- `?` 字符：0
- `\.`：0
- Data availability 包含 Zenodo DOI：`10.5281/zenodo.21053253`
- Fig. 1 标题已改为材料界面和 mammillary architecture 导向。
- Fig. 5 正文已弱化 p values。
- Discussion 已加入 no complete causal chain 的边界句。
- 结论已改为 matrix feature aligned with architecture and response。

## 投稿前建议微调

### 1. 确认 Zenodo 内容与 Data availability 声明一致

当前 Data availability 声明：

> Processed proteomic and glycoproteomic tables, morphometric measurements, structural-model descriptors, finite-element summary outputs, and plotting/statistical scripts are provided in the Supplementary Materials and archived in Zenodo under DOI 10.5281/zenodo.21053253. Raw mass-spectrometry files and finite-element input files are available through the same Zenodo record.

投稿前必须确认 Zenodo 中确实包含：

- processed proteomic tables
- processed glycoproteomic tables
- morphometric measurements
- structural-model descriptors
- finite-element summary outputs
- plotting/statistical scripts
- raw mass-spectrometry files
- finite-element input files

如果 raw MS 或 FE input 尚未上传，应修改 Data availability，避免声明过强。

### 2. Supplement 中补足 FEA 合理性

建议 Supplement 至少包含：

- FEA material parameters table
- mesh size rationale
- boundary condition rationale
- loading velocity rationale
- mass scaling explanation
- local readout limitation statement

### 3. 不建议再大改正文

原因：

- 当前主线已经稳定。
- 继续削弱会损失投稿亮点。
- 继续增强会重新引入因果和力学风险。

## 最终投稿定位

推荐：

> A matrix-chemistry-to-biomineral-architecture study showing that OVAL glycan-state variation is aligned with Ca2+-relevant surface accessibility, mammillary architecture, and standardized local loading response.

避免：

> A mechanical design principle paper proving species-specific eggshell survivability.

## 最终检查清单

- [ ] Zenodo DOI 可访问。
- [ ] Zenodo 内容与 Data availability 声明一致。
- [ ] Raw MS 文件已上传或 Data availability 已降级。
- [ ] FE input files 已上传或 Data availability 已降级。
- [ ] Supplement 包含 FEA 参数和边界说明。
- [ ] Fig. 1 不再由生态背景主导。
- [ ] Fig. 5 始终是 local readout。
- [ ] 全文没有把 positional / regional sampling 写成 biological replication。
- [ ] 全文没有重新出现 `drives`、`determines`、`proves` 等强因果词。
- [ ] `?` 和 `\.` 仍为 0。

## 一句话结论

v3 已经可以作为 Acta Biomaterialia 投稿主稿基础；下一步不要再大改正文，重点检查 Supplement、Zenodo 内容、图注一致性和投稿系统材料完整性。
