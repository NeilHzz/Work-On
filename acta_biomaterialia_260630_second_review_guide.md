# Acta Biomaterialia manuscript260630 二次审阅修改指南

审阅对象：`03_文章撰写/0_Manuscript/manuscript260630.docx`

目标：在不大改主线的前提下，进一步降低编辑初筛和外审攻击面。

## 总体判断

`manuscript260630.docx` 已明显优于上一版，主线已经回到 Acta Biomaterialia 所重视的 structure-property-function framework。当前不需要大改，投稿前重点处理 Data availability 和 Fig. 5 显著性呈现即可。

## 已解决的问题

### 1. 标题已收紧

当前标题：

> Ovalbumin Glycan-State Variation Links Eggshell Matrix Chemistry to Biomineral Architecture and Local Response

评价：

标题比上一版更短，保留了 OVAL、matrix chemistry、biomineral architecture 和 local response 四个核心信号。

### 2. 摘要因果语气已降级

当前摘要中已经使用：

- `are associated with`
- `were consistent with`
- `suggesting a plausible route`
- `aligned with`
- `support a cross-scale association framework`

评价：

语气基本合适，不再像直接因果证明。

### 3. 统计层级风险已显著降低

Fig. 1 和 Fig. 5 已明确说明：

- `regional sampling within one scanned fragment`
- `not independent biological replication`
- `within-fragment separation`
- `within-model positional separation`

评价：

pseudoreplication 风险已明显降低。

### 4. Glycoproteomic sampling depth imbalance 已正面解释

当前 Fig. 2 段已说明：

> Because glycoproteomic sampling depth differed among species, species-private catalog size was not interpreted as a direct measure of biological complexity.

评价：

这能有效降低审稿人对 chicken 低检出量的质疑。

### 5. Fig. 4 正文已压缩

当前正文只保留 glycan envelope、acidic interface shielding、Ca2+ accessibility 的主要结论，numbered markers 已转移到 caption。

评价：

正文和图注分工更合理。

### 6. 字符损坏已修复

检查结果：

- `?` 字符数量：0
- `\.` 数量：0

评价：

上一版中影响编辑观感的 Word 字符损坏已解决。

## 投稿前仍建议修改

### 1. 强化 Data availability

当前位置：

> Processed proteomic and glycoproteomic tables, morphometric measurements, structural-model descriptors, finite-element summary outputs, and plotting/statistical scripts are provided in the Supplementary Materials or in the submission data repository. Raw mass-spectrometry files and finite-element input files will be deposited in a public repository before publication; the repository accession or DOI will be provided before publication. Materials generated in this study are available from J.Z. upon reasonable request (jxzheng@cau.edu.cn).

问题：

`will be deposited before publication` 对送审不够强。编辑或审稿人可能认为关键数据尚未可查。

推荐方案 A：已有 repository / private review link 时使用

> Processed proteomic and glycoproteomic tables, morphometric measurements, structural-model descriptors, finite-element summary outputs, and plotting/statistical scripts are provided in the Supplementary Materials and deposited in [repository] under accession [ID/private review link]. Raw mass-spectrometry files and finite-element input files have been deposited in [repository] under accession [ID/private review link]. Materials generated in this study are available from J.Z. upon reasonable request (jxzheng@cau.edu.cn).

推荐方案 B：暂时只有 Zenodo 草稿 DOI 或待开放链接时使用

> Processed proteomic and glycoproteomic tables, morphometric measurements, structural-model descriptors, finite-element summary outputs, and plotting/statistical scripts are provided in the Supplementary Materials and archived in a repository prepared for peer review. Raw mass-spectrometry files and finite-element input files will be made available through the same repository record before publication, with accession details supplied during revision.

推荐方案 C：如果确实还没有任何 repository

> Processed proteomic and glycoproteomic tables, morphometric measurements, structural-model descriptors, finite-element summary outputs, and plotting/statistical scripts are provided in the Supplementary Materials. Raw mass-spectrometry files and finite-element input files are available for peer-review inspection from the corresponding author and will be deposited in a public repository before publication.

优先级：

方案 A > 方案 B > 方案 C。

### 2. 弱化 Fig. 5 正文中的 p 值存在感

当前位置：

> Within the positional sampling of each reconstructed fragment, peak F_max showed clear separation among models (ANOVA p = 1.64 × 10^-13).

> By contrast, τmax resolved a two-level pattern under the same sampled conditions (ANOVA p = 6.64 × 10^-10).

问题：

虽然已经说明这些测试不是 biological replication，但正文中直接给出极小 p 值仍容易吸引审稿人质疑统计独立性。

推荐改写：

> Within the positional sampling of each reconstructed fragment, peak F_max separated among the three standardized models. Chicken reached 1.12 ± 0.11 N, duck reached 0.90 ± 0.09 N, and pigeon reached 0.49 ± 0.04 N across sampled offsets (Fig. 5B).

> By contrast, τmax showed a chicken-high and duck/pigeon-low pattern under the same sampled conditions. Chicken reached 0.613 ± 0.061 MPa, whereas duck reached 0.413 ± 0.041 MPa and pigeon reached 0.406 ± 0.033 MPa (Fig. 5C).

> The statistical tests describe within-model positional separation and are reported in Fig. 5 and Table S7; they should not be interpreted as independent biological replication.

图注可保留：

> p values above the plots are one-way ANOVA omnibus p values for positional sampling, and different letters indicate Tukey HSD groupings under the sampled conditions.

### 3. 最后总结句再降低因果感

当前位置：

> In summary, this study links mammillary organisation, glycoprotein state, Ca²⁺ surface accessibility, biomineral architecture, and local structure-function response across three avian eggshells.

建议改为：

> In summary, this study associates mammillary organisation, glycoprotein state, Ca²⁺ surface accessibility, biomineral architecture, and local structure-function response across three avian eggshells.

理由：

`associates` 比 `links` 更符合当前证据强度。

### 4. Introduction 末句可轻微降级

当前位置：

> The resulting framework links OVAL glycan state to biomineral architecture and to the local response measured under standardized inside-out loading.

建议改为：

> The resulting framework evaluates how OVAL glycan state aligns with biomineral architecture and the local response measured under standardized inside-out loading.

理由：

避免 Introduction 末段提前给出过强结论。

## 不建议继续大改的部分

### 1. 不建议再压缩摘要

当前摘要已经比较平衡，保留即可。

### 2. 不建议删除 FEA

FEA 是 Acta Biomaterialia 读者会关注的 structure-function 证据，只需保持 local readout 定位。

### 3. 不建议继续削弱 OVAL 主线

OVAL 是当前稿件最清楚、最可解释、最适合 Acta 定位的分子主线。

### 4. 不建议新增复杂实验承诺

Discussion 中已有 causal limitation 和 future tests。无需再增加过多未来实验，否则会显得当前证据不足。

## 最终投稿前检查清单

- [ ] Data availability 不再只写 `will be deposited before publication`。
- [ ] Fig. 5 正文不突出极小 p 值。
- [ ] Fig. 5 p 值仅作为 positional sampling 统计保留在图注或 Table S7。
- [ ] Summary 中 `links` 改为 `associates` 或同等弱化词。
- [ ] Introduction 末句避免提前强因果结论。
- [ ] `?` 字符仍为 0。
- [ ] `\.` 仍为 0。
- [ ] 全文没有把 subfragments / loading positions 写成 biological replicates。

## 当前推荐投稿定位

推荐定位：

> A cross-scale biomaterials study associating OVAL glycan-state variation with Ca2+-relevant surface accessibility, mammillary biomineral architecture, and standardized local loading response in avian eggshells.

避免定位：

> A definitive causal demonstration that OVAL glycosylation determines species-specific eggshell fracture mechanics.
