"""
Science Advances 格式 — 中文版补充材料
输出: supplementary_materials_cn.docx
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


FIG_BASE = Path(r"D:\system_folder\Desktop\Work On\Supplementary\Figures")
MAIN_FIG_BASE = Path(__file__).resolve().parent.parent / "Figure260421"
OUT = str(Path(__file__).with_name("supplementary_materials_cn.docx"))

doc = Document()


# 页面设置
s = doc.sections[0]
s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.54)
s.page_width = Cm(21.0)
s.page_height = Cm(29.7)

SCI_F = "Times New Roman"
BODY = "SimSun"


def _set_font(rPr, latin_name=SCI_F, east_asia_name=BODY):
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), latin_name)
    rFonts.set(qn("w:hAnsi"), latin_name)
    rFonts.set(qn("w:cs"), latin_name)
    rFonts.set(qn("w:eastAsia"), east_asia_name)
    rPr.insert(0, rFonts)


def fmt(run, size=11, bold=False, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    _set_font(run._r.get_or_add_rPr())


def spacing(p, before=0, after=120, line=24):
    pPr = p._p.get_or_add_pPr()
    e = OxmlElement("w:spacing")
    e.set(qn("w:before"), str(before))
    e.set(qn("w:after"), str(after))
    e.set(qn("w:line"), str(line * 20))
    e.set(qn("w:lineRule"), "auto")
    pPr.append(e)


def keep_with_next(p):
    pPr = p._p.get_or_add_pPr()
    e = OxmlElement("w:keepNext")
    pPr.append(e)


def para(text, bold=False, italic=False, size=11, before=0, after=120,
         align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    r = p.add_run(text)
    fmt(r, size=size, bold=bold, italic=italic)
    return p


def fig_title(label, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    spacing(p, before=200, after=120)
    keep_with_next(p)
    r_label = p.add_run(label + " ")
    fmt(r_label, bold=True)
    r_title = p.add_run(title)
    fmt(r_title, bold=True)
    return p


def fig_caption(text, before=0, after=200):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    spacing(p, before=before, after=after)
    r = p.add_run(text)
    fmt(r)
    return p


def add_image(img_path, width_cm=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    spacing(p, before=60, after=60, line=12)
    p.add_run().add_picture(str(img_path), width=Cm(width_cm))
    return p


def add_images_row(img_paths, width_cm=7.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    spacing(p, before=60, after=60, line=12)
    for i, img_path in enumerate(img_paths):
        p.add_run().add_picture(str(img_path), width=Cm(width_cm))
        if i < len(img_paths) - 1:
            p.add_run("  ")
    return p


# 封面
para("补充材料", bold=True, size=14,
     before=0, after=240, align=WD_ALIGN_PARAGRAPH.CENTER)

para(
    "基质蛋白糖链状态分化联系鸟类蛋壳结构与生物矿化",
    italic=False, size=11, before=0, after=360,
    align=WD_ALIGN_PARAGRAPH.CENTER,
)

para("目录", bold=True, size=11, before=0, after=60,
     align=WD_ALIGN_PARAGRAPH.LEFT)

for line in [
    "补充文本 1. 物种选择与敏感性分析",
    "补充文本 2. 蛋壳基质蛋白组正交组分析",
    "",
    "图S1. 验证宏观生态物种选择框架的敏感性分析",
    "图S2. 目标物种在更广鸟类比较框架中的系统位置与比较轴热图",
    "图S3. 三物种共享与谱系限制性蛋壳基质正交组的 Venn 图",
    "图S4. 基于单拷贝直系同源物重建的三个目标物种的最大似然系统发育树",
    "图S5. 物种特异与成对共享蛋壳基质蛋白集合的 GO 富集",
    "图S6. 三个物种的 CAFE5 基因家族扩张与收缩",
    "图S7. OVAL 糖链几何及 apo/糖基化对照的 Re-Glyco 系综分析",
    "图S8. 各物种九个偏移位置的有限元反力时间历程",
]:
    para(line, size=11, before=0, after=40, align=WD_ALIGN_PARAGRAPH.LEFT)

doc.add_page_break()


# 补充文本
para("补充文本", bold=True, size=12,
     before=0, after=240, align=WD_ALIGN_PARAGRAPH.LEFT)

para("补充文本 1. 物种选择与敏感性分析。",
     bold=True, size=11, before=0, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

fig_caption(
    "基于 AVONET 生态性状得分（体重、喙长、喙宽、喙深、跗跖长、翼长、Kipps 距离、手翼指数、尾长，以及经数值编码的主要生活方式、栖息地和营养生态位）的主成分分析，将 Gallus gallus、Anas platyrhynchos 和 Columba livia 分离到鸟类生态空间中三个彼此独立的区域（图S1），分别对应陆栖地面营巢的早成型、半水生早成型和高位营巢的晚成型生活史策略。物种选择的目标是同时覆盖早成–晚成和陆生–半水生两条比较轴线，而不是追求单一的系统发育位置或外部形态差异。为确认这种三簇分离并非分类变量数值编码造成的伪影，我们进行了 500 次随机扰动迭代，在每次迭代中，所有编码权重均在原始值的 ±30% 范围内独立变动。在全部 500 次迭代中，方差解释度和聚类 silhouette 分数都紧密集中在未扰动的基线值附近（图S1），说明三物种比较框架对数值编码中的主观成分具有良好稳健性。"
)

para("补充文本 2. 蛋壳基质蛋白组正交组分析。",
     bold=True, size=11, before=240, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

fig_caption(
    "基于蛋白组学鉴定到的蛋壳基质蛋白，经 OrthoFinder 正交分析流程整理后，在 G. gallus、A. platyrhynchos 和 C. livia 中分别得到 2,620、2,921 和 3,219 个正交组（图S3）。该流程基于全对全蛋白相似性关系及图聚类来划分正交组。其中，1,997 个正交组为三物种共享，构成了保守的蛋壳基质蛋白核心。两两共享但并非三物种共同共享的正交组数量分别为 180（G. gallus–A. platyrhynchos）、434（G. gallus–C. livia）和 716（A. platyrhynchos–C. livia）。谱系限制性（物种特异）集合则分别包括鸡、鸭和鸽的 9、28 和 72 个正交组。"
)

fig_caption(
    "成对共享集合的 Gene Ontology（GO）富集提示，功能分层更多沿生态轴线展开，而不是简单追随系统发育邻近性（图S5）。A. platyrhynchos–C. livia 共享集合最显著富集于钙离子结合和金属离子结合（MF；两者 p 均 < 10⁻²⁵），以及 Wnt 信号通路和信号转导（BP）。这种在鸭和鸽共享集合中出现、但在鸡中缺失的钙结合富集，提示不同谱系在环境钙获取与利用策略上存在分子层面的分化。G. gallus–A. platyrhynchos 共享集合，即鸡雁类中的两个早成型物种而不包括晚成型鸽，则富集于适应性免疫反应和精子发生（BP），与早成型繁殖程序相一致。"
)

fig_caption(
    "谱系限制性 GO 信号进一步强化了跨物种差异。G. gallus 特异集合（9 个正交组）显著富集于蛋白 N-连接糖基化（BP），说明糖链加工能力代表了鸡谱系中的功能扩展，而在另外两个物种的特异集合中并未出现。A. platyrhynchos 特异集合（n = 28）主要富集于免疫反应调控、B 细胞激活和铁反应，这与水域相关觅食环境下更高的病原暴露和矿物代谢需求一致。C. livia 特异集合（n = 72，为最大的谱系限制性集合）则富集于神经系统发育、泛素依赖性蛋白质分解代谢和蛋白水解，反映了晚成型雏鸟快速器官成熟所需的发育复杂性。"
)

fig_caption(
    "基因家族扩张与收缩分析（CAFE5）结合正交组家族大小和物种分化时间树后，进一步表明这种谱系分化具有明显不对称性：G. gallus 总体表现为净家族收缩，A. platyrhynchos 居中，而 C. livia 表现为净扩张（图S6）。鸡中收缩的家族富集于免疫相关功能；鸽中扩张的家族则富集于跨膜转运、Rho 信号和突触相关过程。总体来看，这些蛋白组层面的模式证实了三种蛋壳形成系统之间存在广泛的进化分化，同时也表明共享核心工具箱仍被保留，而鸡中的 N-连接糖基化扩展使后续比较分析自然聚焦到修饰层面的糖链状态差异，而非蛋白是否存在本身。"
)

doc.add_page_break()


# 图S1
fig_title("图S1.", "验证宏观生态物种选择框架的敏感性分析。")
add_image(FIG_BASE / "SuppFig1_Species_Selection" / "Sensitivity_Analysis_Results.png", width_cm=15.5)
fig_caption(
    "在基于 AVONET 的主成分空间中，为选择 Gallus gallus、Anas platyrhynchos 和 Columba livia 作为目标物种而进行的 500 次随机扰动迭代，其方差解释度（R²）和聚类 silhouette 系数分布如图所示。主要生活方式、栖息地和营养生态位等分类生态变量均采用数值编码；每次迭代都在原始值 ±30% 范围内对全部编码权重进行独立随机扰动。两项指标均高度集中于基线值附近，说明物种分组结果稳健，并不敏感于数值编码中带有主观性的部分。"
)


# 图S2
doc.add_page_break()
fig_title("图S2.", "目标物种在更广鸟类比较框架中的系统位置与比较轴热图。")
add_image(MAIN_FIG_BASE / "PanelB.jpg", width_cm=15.5)
fig_caption(
    "代表性鸟类类群的系统发育关系及水生关联（X）、发育方式（Z）和生态不一致性（Y）三条比较轴的热图。彩色目级标签给出了目标物种所处的更广比较框架，并说明鸡、鸭和鸽这组三物种比较覆盖的功能轴线只与系统关系部分重合。"
)


# 图S3
doc.add_page_break()
fig_title("图S3.", "三物种共享与谱系限制性蛋壳基质正交组的 Venn 图。")
add_image(FIG_BASE / "SuppFig2_Venn_Orthogroups" / "Fig_venn_orthogroups.png", width_cm=12.0)
fig_caption(
    "三种蛋壳基质蛋白组的 OrthoFinder 正交组聚类结果。基于全对全蛋白相似性比较及图聚类，该图将检测到的正交组划分为一个大的三物种共享核心、三个两两共享区域以及三个谱系限制性区域。数字表示各区域中的正交组数量。这一划分构成了正文所述比较框架的基础。"
)


# 图S4
doc.add_page_break()
fig_title("图S4.", "基于单拷贝直系同源物重建的三个目标物种的最大似然系统发育树。")
add_image(FIG_BASE / "SuppFig3_Phylo_Tree" / "Fig_phylo_tree.png", width_cm=14.0)
fig_caption(
    "该最大似然物种树基于正交分析流程返回的单拷贝直系同源集合重建。单拷贝直系同源蛋白序列经过比对后用于推断此处展示的物种关系。分支长度表示每个位点的替换数；内部节点给出了支持度数值（1000 次重复）。树拓扑与已发表的鸟类系统发育关系一致，并确认了预期的亲缘顺序，即鸡形目和雁形目在鸡雁类中互为姐妹群，而鸽形目为更远的外群；这一顺序用于构建正文中的比较分析框架。"
)


# 图S5
doc.add_page_break()
fig_title("图S5.", "物种特异与成对共享蛋壳基质蛋白集合的 GO 富集。")
add_image(FIG_BASE / "SuppFig4_GO_Enrichment" / "图2.jpg", width_cm=16.0)
fig_caption(
    "上半部分显示三个两两共享正交组区域（GnA，即 Gallus–Anas；GnC，即 Gallus–Columba；AnC，即 Anas–Columba）的 GO 富集条目；下半部分显示三个物种特异正交组集合（Gallus、Anas、Columba）的 GO 富集条目。颜色区分 GO 类别，包括生物过程（BP）、细胞组分（CC）和分子功能（MF）。这张合并图同时展示了成对共享区域中的共同生态信号与物种特异区域中的谱系限制性信号；其中，G. gallus 特异集合中保留了蛋白 N-连接糖基化这一富集生物过程，直接支持正文将比较重点收束到跨物种糖蛋白组差异。"
)


# 图S6
doc.add_page_break()
fig_title("图S6.", "三个物种的 CAFE5 基因家族扩张与收缩。")
add_image(FIG_BASE / "SuppFig5_CAFE5_Gene_Family_Turnover" / "Fig_cafe5_expansion_contraction.png", width_cm=14.0)
fig_caption(
    "系统发育树上标注了利用物种分化时间树并由 CAFE5 推断的谱系特异性基因家族扩张（红色）与收缩（蓝色）事件。节点上的数字表示估计的祖先基因家族大小，分支上的数字表示净变化。仅展示每个家族 p < 0.05（Viterbi p 值）的基因家族。该模式与 GO 富集结果一致：各谱系在免疫和防御相关基因家族的周转上存在差异，而核心蛋壳基质基因家族则在三条谱系中总体保持保守。"
)
# 图S7
doc.add_page_break()
fig_title("图S7.", "OVAL 糖链几何及 apo/糖基化对照的 Re-Glyco 系综分析。")
add_image(FIG_BASE / "SuppFig7_Glycosylation_Hotspot" / "Fig_hotspot_ensemble_1.png", width_cm=15.5)
fig_caption(
    "(A) 三种物种特异性 OVAL–糖链复合物在构象系综重复中的糖链回旋半径（Rg）分布，按物种着色（G. gallus 为橙色，A. platyrhynchos 为蓝色，C. livia 为绿色）。(B) 相同三种复合物的糖链端到端距离分布。(C) 各物种糖基化与 apo（去糖基化）OVAL 结构逐构象的 Ca²⁺ 热点计数（Nhot）比较。C. livia 具有最大的构象空间和最强的糖链遮蔽；G. gallus 具有最小的构象空间和最弱的遮蔽；A. platyrhynchos 居中。apo 对照提供了内部参照：一旦移除 N-糖链，跨物种在热点计数上的分离便大幅收敛，从而表明在糖基化状态中检测到的分化主要来自糖链层，而不是蛋白骨架本身。图中 panel C 相对 apo 参考的差异采用一样本 t 检验评估。"
)


# 图S8
doc.add_page_break()
fig_title("图S8.", "各物种九个偏移位置的有限元反力时间历程。")
add_images_row([
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "chicken_rcforc_3x3.png",
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "chicken_rcforc_yforce.png",
], width_cm=7.5)
add_images_row([
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "duck_rcforc_3x3.png",
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "duck_rcforc_yforce.png",
], width_cm=7.5)
add_images_row([
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "pigeon_rcforc_3x3.png",
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "pigeon_rcforc_yforce.png",
], width_cm=7.5)
fig_caption(
    "(A–C) G. gallus（A）、A. platyrhynchos（B）和 C. livia（C）在九个参数化冲击位置（3 × 3 横向偏移网格）上的接触力（F）时间历程曲线。每条曲线代表一次模拟，显示从接触开始到峰值接触力的全过程。内嵌图给出了各物种九个位置的峰值接触力（Fmax）分布。(D–F) 对应的 Y 方向反力（FY）时间历程。由这九次重复计算得到的物种峰值接触力（Fmax）和峰值接触剪切应力（τmax）的均值 ± s.d. 已在正文和图6中报告。模拟采用 LS-DYNA（Ansys）显式动力有限元分析完成；蛋壳厚度设置为基于 micro-CT 重建测得的物种特异性数值。"
)


doc.save(OUT)
print(f"Saved -> {OUT}")