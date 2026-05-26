Figure 文件夹 — 子图脚本索引
==============================

MainFig1A_species_space.py              — 主图 Fig. 1A，物种选择 3D scatter (k-means 聚类)
MainFig1D_mammilla_quantification.py    — 主图 Fig. 1D，乳突层微结构量化 (箱线图)
SuppFigS2_phylo_context.py              — 补充图 Fig. S2，物种选择系统发育树 + 热图
Fig1C                                  — 主图 Fig. 1C，乳突层 CT 形貌图 (非 Python 生成，来源: eggtooth/乳突层结构.jpg)

MainFig2_glycotype_network.py           — 主图 Fig. 2，同源糖型蛋白圆环网络图

MainFig3A_ortholog_circos.py            — 主图 Fig. 3A，糖蛋白 BlastP 弦图 (chord diagram)
MainFig3B_D_proteotype_coevolution.py   — 主图 Fig. 3B-D，Proteotype Coevolution 散点图
MainFig3E_G_glycan_protein_enrichment.py — 主图 Fig. 3E-G，2D Glycan-Protein Enrichment

MainFig4A_C_SuppFigS8_reglyco_apbs.py   — 主图 Fig. 4A-C + 补充图 Fig. S8，OVAL APBS/热点/逐结构电势
MainFig4D_G_glycan_geometry.py          — 主图 Fig. 4D-G，糖链集合体几何统计
MainFig4H_M_hotspot_accessibility.py    — 主图 Fig. 4H-M，Hotspot 可及性分析

MainFig6_mechanics_force_shear.py       — 主图 Fig. 6，Force/Shear 时间序列和 F_max/τ_max 统计

SuppFigS3_orthogroup_venn.py            — 补充图 Fig. S3，蛋白组 Venn 图 (三物种交集)
SuppFigS4_single_copy_phylogeny.py      — 补充图 Fig. S4，单拷贝直系同源物系统发育树
SuppFigS5_go_enrichment.py              — 补充图 Fig. S5，GO 富集图
SuppFigS6_gene_turnover_go_alluvial.py  — 补充图 Fig. S6，基因家族扩张/收缩对应 GO 富集 alluvial 图
SuppFigS7_glycosylation_profiles.py     — 补充图 Fig. S7，蛋白特异性 Glycosylation Profiling
SuppFigS9_cafe5_turnover_tree.py        — 补充图 Fig. S9，CAFE5 基因家族扩张/收缩树

注意:
- 每个多面板脚本运行一次即生成对应的所有子图
- 主图 Fig. 1B、Fig. 5A-C 还会直接使用 eggtooth/FEM 图片素材，不完全由 Figure 文件夹脚本生成
- 原始脚本路径中的数据引用可能需要调整 (部分脚本使用绝对路径读取数据)
- 运行前请确认数据文件路径正确
