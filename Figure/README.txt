Figure 文件夹 — 子图脚本索引
==============================

Fig1A.py    — 物种选择 3D scatter (k-means 聚类)
Fig1B.py    — 物种选择 系统发育树 + 热图
Fig1C       — 乳突层 CT 形貌图 (非Python生成，原图: Sci_Adv_Figure/PNG/Fig1/2-1图片1.png)
Fig1D.py    — 乳突层微结构量化 (箱线图)

Fig2A.py    — 蛋白组 Venn 图 (三种交集)
Fig2B.py    — 进化树 (Newick)
Fig2C_F.py  — GO 富集气泡图 (C=BP pairwise, D=CC pairwise, E=MF pairwise, F=单物种特异性)
Fig2G.py    — CAFE5 基因家族扩张/收缩树
Fig2H.py    — 基因家族扩张/收缩对应的 GO 富集

Fig3A.py    — 同源糖型蛋白圆环网络图
Fig3B.py    — 糖蛋白 BlastP 弦图 (chord diagram)

Fig4A_C.py  — Proteotype Coevolution 散点图 (A=Gallus, B=Anas, C=Columba)
Fig4D_G.py  — Glycosylation Profiling 堆积条形图 (D=OVAL, E=OC116, F=TRFE, G=OC17)
Fig4H_J.py  — 2D Glycan-Protein Enrichment (H=Anas vs Columba, I=Gallus vs Anas, J=Gallus vs Columba)

Fig5A_D.py  — OVAL Ca²⁺ 电势/热点分析 (A=逐AA电势, B=Ca²⁺ Hotspot, C=COO⁻ SASA, D=表面电势分布)
Fig5E_H.py  — 糖链集合体统计 (E=Glycan Rg, F=End-to-End, G=Glycan-Protein Dist, H=Min Dist to Ca)
Fig5I_N.py  — Hotspot 可及性分析 (I=Interface Shielding, J=SASA, K=Fraction, L=Net Accessible, M/N=对比图)

Fig6A_B.py  — 力学仿真 (A=Contact Force + Shear Stress 时间序列, B=F_max/τ_max Duncan 比较)

注意:
- 每个多面板脚本运行一次即生成对应的所有子图
- 原始脚本路径中的数据引用可能需要调整 (原脚本使用相对路径读取同目录下的数据)
- 运行前请确认数据文件路径正确
