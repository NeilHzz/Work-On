"""
Science Advances 格式 — 中文版
manuscript_results_sa_cn.docx
"""

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path
import re
from shared_references import REFS

OUT = str(Path(__file__).with_name("manuscript260602v2_cn.docx"))
FIG_BASE = Path(__file__).resolve().parent.parent / "02_可视化" / "260601" / "02_main_composed_figures"

REF_TEXTS = {}
for ref_text in REFS:
    match = re.match(r"^(\d+)\.\s+(.*)$", ref_text)
    if not match:
        raise ValueError(f"Invalid reference entry: {ref_text}")
    REF_TEXTS[int(match.group(1))] = match.group(2)

CITATION_ORDER = []
CITATION_MAP = {}

doc = Document()

# ── 页面 ─────────────────────────────────────────────────────────────────
s = doc.sections[0]
s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.54)
s.page_width = Cm(21.0)
s.page_height = Cm(29.7)

# ── 行号（连续） ──────────────────────────────────────────────────────────
_lnNum = OxmlElement("w:lnNumType")
_lnNum.set(qn("w:countBy"), "1")
_lnNum.set(qn("w:restart"), "continuous")
_lnNum.set(qn("w:start"), "1")
s._sectPr.append(_lnNum)

# ── 字体与段落辅助 ─────────────────────────────────────────────────────
SCI_F = "Times New Roman"
BODY = "SimSun"


def _set_font(rPr, latin_name, east_asia_name=None):
    if east_asia_name is None:
        east_asia_name = latin_name
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), latin_name)
    rFonts.set(qn("w:hAnsi"), latin_name)
    rFonts.set(qn("w:eastAsia"), east_asia_name)
    rFonts.set(qn("w:cs"), latin_name)
    rPr.insert(0, rFonts)


def fmt(run, size=11, bold=False, italic=False, heading=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    rPr = run._r.get_or_add_rPr()
    east_asia_name = SCI_F if italic else BODY
    if heading:
        east_asia_name = BODY
    _set_font(rPr, SCI_F, east_asia_name)


def spacing(p, before=0, after=120, line=24):
    pPr = p._p.get_or_add_pPr()
    e = OxmlElement("w:spacing")
    e.set(qn("w:before"), str(before))
    e.set(qn("w:after"), str(after))
    e.set(qn("w:line"), str(line * 20))
    e.set(qn("w:lineRule"), "auto")
    pPr.append(e)


def para(text, bold=False, italic=False, size=11,
         before=0, after=120, align=WD_ALIGN_PARAGRAPH.JUSTIFY, heading=False):
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    r = p.add_run(text)
    fmt(r, size=size, bold=bold, italic=italic, heading=heading)
    return p


def mixed(parts, before=0, after=120, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    for text, bold, italic in parts:
        r = p.add_run(text)
        fmt(r, bold=bold, italic=italic)
    return p


def head(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    spacing(p, before=240, after=60)
    r = p.add_run(text)
    fmt(r, size=11, bold=True, heading=True)
    return p


def _citation_text(numbers):
    if not numbers:
        return ""
    mapped_numbers = []
    for number in numbers:
        if number not in REF_TEXTS:
            raise KeyError(f"Reference {number} not found in REFS")
        if number not in CITATION_MAP:
            CITATION_MAP[number] = len(CITATION_ORDER) + 1
            CITATION_ORDER.append(number)
        mapped_numbers.append(CITATION_MAP[number])
    sn = sorted(set(mapped_numbers))
    groups = []
    i = 0
    while i < len(sn):
        j = i
        while j + 1 < len(sn) and sn[j + 1] == sn[j] + 1:
            j += 1
        if j - i >= 2:
            groups.append(f"{sn[i]}\u2013{sn[j]}")
        elif j - i == 1:
            groups.append(f"{sn[i]}, {sn[j]}")
        else:
            groups.append(str(sn[i]))
        i = j + 1
    return "(" + ", ".join(groups) + ")"


def _add_citation_run(p, numbers):
    citation_text = _citation_text(numbers)
    if not citation_text:
        return
    r = p.add_run(citation_text)
    r.font.size = Pt(11)
    rPr = r._r.get_or_add_rPr()
    _set_font(rPr, SCI_F, BODY)


def spara(sentences, before=0, after=120, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    for text, numbers in sentences:
        r = p.add_run(text)
        fmt(r, size=11)
        _add_citation_run(p, numbers)
    return p


def smixed(sentences, before=0, after=120, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    for parts, numbers in sentences:
        for text, bold, italic in parts:
            r = p.add_run(text)
            fmt(r, bold=bold, italic=italic)
        _add_citation_run(p, numbers)
    return p


def cite(p, numbers):
    if not numbers:
        return
    _add_citation_run(p, numbers)


def add_centered_figure(image_name, width_cm, before=120, after=60):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    spacing(p, before=before, after=after, line=12)
    r = p.add_run()
    r.add_picture(str(FIG_BASE / image_name), width=Cm(width_cm))
    return p


def add_main_figure_legend(label, title, caption_parts, before=0, after=160):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    spacing(p, before=before, after=after)
    r = p.add_run(label + " ")
    fmt(r, bold=True)
    r = p.add_run(title)
    fmt(r, bold=True)
    for text, bold, italic in caption_parts:
        r = p.add_run(text)
        fmt(r, bold=bold, italic=italic)
    return p

# ════════════════════════════════════════════════════════════════════════════
# 引言
# ════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════
# 封面信息 (Science Advances)
# ════════════════════════════════════════════════════════════════════════════
para(
    "跨物种 OVAL 糖链状态连接鸟类蛋壳乳突层组织与局部出壳抗性",
    bold=True, size=14, before=0, after=160,
    align=WD_ALIGN_PARAGRAPH.LEFT
)

para(
    "OVAL 糖链塑造蛋壳状态",
    bold=False, size=11, before=0, after=60,
    align=WD_ALIGN_PARAGRAPH.LEFT
)

para(
    "[请在投稿前补充完整作者姓名、单位、ORCID、共同第一作者说明和通讯作者信息]",
    bold=False, size=10, before=80, after=80,
    align=WD_ALIGN_PARAGRAPH.LEFT
)

para("摘要", bold=True, size=11, before=80, after=40,
     align=WD_ALIGN_PARAGRAPH.LEFT, heading=True)

para(
    "蛋壳基质蛋白是控制蛋壳结构形成的关键，但其研究一直主要停留在蛋白目录和翻译后修饰位点层面。通过匹配的多层分析，我们检验了保守基质蛋白上的糖链状态如何映射到跨物种蛋壳分化。"
    "我们在一个保守的破壳齿界面下比较鸡、鸭和鸽，整合了显微 CT 形态测量、蛋壳基质蛋白组学、完整糖肽质谱、Re-Glyco 结构建模、静电分析和有限元模拟。"
    "跨物种分离首先出现在乳突层组织，而基质蛋白工具箱整体仍然大体共享。"
    "在这一共享背景下，卵清蛋白 OVAL 从鸡中以高甘露糖型为主，转变为鸭中以中性复合/杂合型为主，以及鸽中以唾液酸化复合/杂合型为主。"
    "这些糖链状态预测了 OVAL 钙相关表面的逐步增强遮蔽，并在局部出壳抗性中对应为鸡高、鸭/鸽低的对比。"
    "综合来看，数据将 OVAL 糖链状态定位为连接鸡式蛋壳状态、乳突层组织和内向外失效行为的一个分子层。",
    bold=False, size=10, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY
)

para(
    "导语：跨物种 OVAL 糖链状态揭示了鸡式高抗性蛋壳背后的分子轴线。",
    bold=False, italic=True, size=10, before=80, after=160,
    align=WD_ALIGN_PARAGRAPH.LEFT
)

# ════════════════════════════════════════════════════════════════════════════
# 引言
# ════════════════════════════════════════════════════════════════════════════
para("引言", bold=True, size=14, before=0, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT, heading=True)

# §1 — 背景价值
p_s1a_cn = spara([
    ("鸟类出壳是一个局部失效事件：破壳齿压在蛋壳内表面，而不是把力量分散到整个壳面。", [16, 86]),
    ("类似的辅助出壳结构也见于其他卵生羊膜动物，因此真正有生物学意义的出壳性能差异更可能位于蛋壳，而不是工具本身。", [16, 82, 83, 84, 85]),
    ("然而，我们对一个核心问题仍缺少解释：在相似的出壳力学约束下，不同生态与发育类型的物种为何形成不同蛋壳状态。", [15, 26, 39, 40, 41]),
    ("乳突层是最直接的切入点，因为它既是最早具有力学后果的蛋壳层，也是基质引导方解石生长的起点。当破壳界面被固定后，真正的机制问题就变成：究竟是哪些作用于乳突层的分子调控因素，解释了不同物种恢复出的不同蛋壳状态？", [1, 2, 4, 16, 28, 57]),
])

# §2 — 已知工作与局限
p_intro2 = spara([
    ("蛋壳基质蛋白调控乳突层成矿、晶体生长和成熟壳体结构，而 OC17、OC116、TRFE 和 OVAL 等反复出现的因子共同定义了一套共享的成壳工具箱。", [1, 2, 4, 10, 19, 21, 29]),
    ("尚未解决的问题不是工具箱是否存在，而是这一工具箱如何在物种间被差异化部署。", [1, 2, 4]),
    ("这一缺口在翻译后修饰层面最为明显。磷酸化和糖基化位点都已被记录，但磷酸侧链基团相对一致，而糖链在组成、大小和电荷上变化更大，能够在同一蛋白支架上产生不同分子状态。", [17, 18, 21, 49, 50, 80]),
    ("因此，糖链类别是机制变量，而不只是位点占据的附属信息。", [49, 50]),
    ("已有糖蛋白组学研究证明蛋壳基质蛋白可携带不同 N-糖基化状态，包括 OC116 的糖基化 Asn 与 OVAL 相关糖链组成；但多数分析仍局限于单一物种、单一区室或单个位点目录。", [7, 8, 18, 21, 47, 48]),
    ("结果是，跨物种比较仍很少解析共享基质蛋白上的匹配糖链状态，也就难以回答这一糖链层是否解释了相似工具箱为何产生不同蛋壳状态。", [2, 4, 18, 29, 66]),
])

p_intro_sig_cn = spara([
    ("糖基化可改变蛋白稳定性、分子识别与表面可及性；在其他系统中，糖链被证明可作为动态遮蔽层重塑可接近界面。", [42, 43, 44, 61, 63, 72, 78, 81]),
    ("分层蛋壳研究进一步显示，同一种基质蛋白在不同壳层区室间可处于不同 N-糖基化状态，提示糖链状态可能重新分配功能，而不只是装饰固定支架。", [18]),
    ("因此，OVAL 是一个可操作的检验对象：它丰度高、与矿化相关，并且在早期成壳中已被提示具有 Ca²⁺ 响应构象行为。", [4, 11, 18, 29]),
    ("我们把比较锚定在保守的破壳齿界面上，并检验共享基质蛋白上的糖链状态差异是否会在矿化起始时产生不同的 Ca²⁺ 可接近表面。", [4, 16, 18]),
])

# §3 — 核心缺口
p_intro_gap_cn = spara([
    ("这一框架真正缺失的一步，是把糖链类别直接连接到共享基质背景上的表面呈现方式；而 OVAL 提供了这一步，因为其主导糖链类别可以从糖蛋白组学一路追踪到结构建模。", [4, 18, 29, 42]),
])

# §4 — 本研究
p_intro4 = smixed([
    ([ ("在这里，我们比较了", False, False),
            ("Gallus gallus", False, True),
            ("、", False, False),
            ("Anas platyrhynchos", False, True),
            ("和", False, False),
            ("Columba livia", False, True),
                ("。", False, False)], []),
            ([ ("我们建立了一个整合式分析框架，将显微 CT 形态测量、比较蛋白组学、完整糖肽质谱、Re-Glyco 建模、静电分析和有限元模拟结合起来，用于跨尺度解析蛋壳结构、糖链状态和出壳力学。", False, False)], []),
            ([ ("我们的分析显示，乳突层组织先于更广泛的基质蛋白工具箱把物种分开，而 OVAL 糖链状态是连接分子状态、表面可及性和局部出壳抗性的最强信号。", False, False)], []),
            ([ ("总之，这些结果建立了一个把糖链状态变化连接到鸟类蛋壳组织和内向外失效行为的分析框架。", False, False)], []),
])

para("结果", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT, heading=True)

head("当破壳器保守时，变化就落在蛋壳上")

p_ss1_cn = smixed([
    ([('我们利用 AVONET 收录的 10,993 个现生鸟类物种记录，把鸟类放入一个比较空间，并从中选取三个被有意拉开的模型物种（图1A）。', False, False)], [16, 22, 41]),
    ([('这一更宽的映射优先考虑了两个最不可能只是次级效应、同时又与蛋最相关的轴线：巢穴环境和后代发育状态。它们分别跨越陆生到强水域利用，以及更早成到更晚成幼雏的连续梯度。', False, False)], [15, 22, 23]),
    ([('在这一比较空间中，', False, False),
        ('Gallus gallus', False, True),
        ('、', False, False),
        ('Anas platyrhynchos', False, True),
        ('和', False, False),
        ('Columba livia', False, True),
        ('因此被选在这些生态和发育梯度的对立区域附近，从而尽量减少中间组合对比较的模糊。', False, False)], [3, 22, 23, 41]),
    ([('这种功能性分组只与系统发育部分重叠。鸡和鸭仍是亲缘较近的早成类群，但沿栖息环境轴分开；鸽则锚定了比较中的晚成端点（图S2）。', False, False)], [3, 22, 23]),
    ([('因此，这一比较在保留共同祖先背景的同时，把清晰的生活史差异纳入同一分析框架。', False, False)], []),
    ([('三种物种的喙尖几何虽然不同，但破壳齿在三者中都保持为位置相近的背侧破壳结构，因此都指向同一种由壳内向外发起的局部破壳事件（图1B）。', False, False)], [16, 37, 82, 86]),
    ([('在这一对比集合中，真正相关的问题就变成：一旦出壳界面被固定，最先把物种区分开的蛋壳层是哪一层。', False, False)], []),
])

head("乳突层首先拉开蛋壳差异")

mixed([
    ("当比较被放到这一出壳背景下阅读时，在当前样本中最先显示出清晰对比的蛋壳层级是乳突层形态（图1C）。在", False, False),
    ("G. gallus", False, True),
    ("中，乳突轮廓整体更平滑，表现为钝圆形凸起。在", False, False),
    ("A. platyrhynchos", False, True),
    ("中，乳突表面可见更多棱脊和转角。", False, False),
    ("C. livia", False, True),
    ("则以独立、尖锐的三角锥样乳突为主。三维表面重建与横截面观察一致，说明本次取样到的内壳区域在乳突几何上确有差异，而不是同一内表面模板的轻微变体。", False, False),
])

p_s0b_cn = mixed([
    ("定量分析进一步显示，本次取样区域在两个相关但并不完全相同的指标上呈现出可区分的模式（图1D）。乳突 knobs 密度在", False, False),
    ("G. gallus", False, True),
    ("中最高（171.36 ± 5.63 个/mm²），显著高于", False, False),
    ("A. platyrhynchos", False, True),
    ("（155.22 ± 8.63 个/mm²）和", False, False),
    ("C. livia", False, True),
    ("（158.27 ± 11.39 个/mm²），后两者彼此接近。相比之下，晶体单元占比在", False, False),
    ("C. livia", False, True),
    ("中最高（0.53 ± 0.04），", False, False),
    ("A. platyrhynchos", False, True),
    ("居中（0.44 ± 0.02），", False, False),
    ("G. gallus", False, True),
    ("最低（0.40 ± 0.01）。在这一扫描碎片比较内，鸡表现出最高的局部乳突密度，而鸽把最大比例的壳体体积分配给由单个乳突knobs生长出的晶体单元。鸭在晶体单元占比上居中、在密度上则更接近鸽。这两个指标并没有压缩成一条单调轴线，但合起来说明，在考虑更晚出现的壳体特征之前，乳突层层面的对比已经可以被检测到。由于这一层是最早与蛋壳力学和基质调控相连的结构层级，我们随后进一步提出一个更窄的问题：这种已观察到的对比究竟反映了工具箱的整体替换，还是一个大体共享系统内部的差异性使用？", False, False),
])
cite(p_s0b_cn, [1, 4, 28])

doc.add_page_break()
add_centered_figure("Fig1_composed.png", width_cm=10.1, before=0, after=20)
add_main_figure_legend(
    "图1.",
    "三种模型鸟类的比较空间、出壳界面与乳突层形态差异。",
    [
        ("(A) 基于AVONET 10,993个物种记录构建的三维比较空间；坐标轴概括水域关联、生活方式-栖息地差异和发育模式。颜色表示鸟类目级类群，灰色框标示三种目标物种的采样区域，空心圆表示 ", False, False),
        ("Gallus gallus", False, True),
        ("、", False, False),
        ("Anas platyrhynchos", False, True),
        (" 和 ", False, False),
        ("Columba livia", False, True),
        ("。(B) 三物种侧面头部视图（上）和背侧喙部视图（下），显示带破壳齿的喙尖。(C) 乳突层代表性显微CT截面和三维内表面重建。比例尺，100 μm。(D) 物种间乳突密度和晶体单元体积比例箱线图。散点表示每个物种一个扫描碎片中的9个非重叠子区域；p值采用单因素ANOVA计算，不同字母表示Tukey HSD分组。", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

p_sprot_bg_cn = spara([
    ("直系同源分组分析显示，三物种蛋壳基质蛋白组由一个大的共享核心及较小的两两共享和谱系限制性补集构成（图S3）。在整体层面，蛋白组仍遵循广义亲缘框架（图S4），说明蛋壳差异并非来自基质工具箱的整体替换。", []),
])

p_sprot_go_cn = spara([
    ("共享核心因此成为真正相关的比较框架。接下来的问题是，物种之间的分化究竟来自蛋白组的整体周转，还是来自共享基质蛋白上的不同糖链状态。", []),
])

p_sprot_focus_cn = spara([
    ("鸡特异集合同时富集于蛋白N-糖基化（BP；图S5），因此比较重点从“有哪些蛋白”转向“共享蛋白以何种化学状态被使用”。保留下来的共享核心由此成为真正的分子背景，而共享蛋白上的糖基化则成为解释乳突层分化及后续壳体行为的最近端候选层。", [18]),
    ("从当前数据看，我们检测到的大多数反复出现的蛋壳基质蛋白与前人报道总体一致，说明整体蛋壳基质背景与既有研究相吻合；同时，这套数据也扩展了进入比较背景的基质蛋白范围。", [1, 2, 4, 10, 19, 21, 29]),
])

head("OVAL糖基化提供了最易解释的跨物种对比")

p_s2a_cn = spara([
    ("完整糖肽分析首先显示，三物种在采样深度上存在差异，但仍共享一个稳定的比较核心（图2A至D）。在cluster层面，三物种共有25个共享cluster，而最大的额外两两重叠来自鸭和鸽的64个cluster；鸡几乎没有形成明显的物种私有cluster空间（图2A）。", []),
    ("同样的不对称也出现在清单数量上：鸭检测到321个糖蛋白、547个糖基化位点和197种糖链组成；鸽分别为192、257和162；鸡分别为55、88和105（图2B）。尽管覆盖深度不同，共享核心的Jensen-Shannon相似性仍集中在0.33到0.40之间，其中鸭-鸽配对最高，这说明三物种的差异发生在一个仍可比较的糖蛋白背景之内，而不是彼此割裂的三个化学空间（图2C）。", []),
    ("糖链类别组成在化学部署层面进一步强化了同样的结论。高甘露糖型和Complex-Fucosylated糖链构成了跨物种的广泛背景，而Complex-Sialylated及其他更延伸的类别则更强地参与了谱系分离（图2D）。", []),
])

add_centered_figure("Fig2_composed.png", width_cm=14.6)
add_main_figure_legend(
    "图2.",
    "跨物种共享核心糖蛋白组架构与糖链类别部署。",
    [
        ("(A) 糖蛋白组数据中的物种分区cluster数量。(B) 各物种检测到的糖蛋白、糖基化位点和糖链组成数量。(C) 物种间共享核心的Jensen-Shannon相似性。(D) 物种水平糖链类别分布（High Mannose、Pauci-mannose、Hybrid、Complex-Plain、Complex-Fucosylated、Complex-Sialylated和Other）。(E) 直系同源-糖链弦图，连接鸡、鸭和鸽蛋壳糖蛋白与优势糖链类别，并高亮后续分析保留的基质蛋白。", False, False),
    ],
)

p_s2b_cn = mixed([
    ("更严格的BlastP过滤进一步保留了一组适合结构比较的直系同源糖蛋白，并在图2E中概括了这一共享候选空间。以", False, False),
    ("G. gallus", False, True),
    ("为参考，只有当非参考候选的平均E值低于1 × 10⁻⁵且序列一致性满足最终可比性阈值时，才予以保留。这一过滤将后续比较限制在高置信度直系同源范围内。在这一更严格的映射下，OC17仅在鸡中显示糖基化，而OC116、TRFE和OVAL在三物种中都保留了糖基化信号，可作为共享锚点。其中，OVAL表现出最清晰的跨物种糖链差异，因此成为后续结构分析的优先对象。", False, False),
])
cite(p_s2b_cn, [])

p_s2c_cn = spara([
    ("整合蛋白和糖链丰度后，OVAL进一步被识别为与跨物种蛋壳差异最一致的共享蛋白（图3A至C）。在全数据集中，鸡的蛋白-糖链耦合较弱，而鸭和鸽则持续为正，说明不同谱系中糖基化随蛋白输出变化的方式并不相同。", []),
    ("在被高亮的蛋壳基质蛋白中，OVAL在三物种中都保持高丰度，但糖链负荷差异显著：鸡相对较低，鸭更强，鸽最强。OC116和TRFE仍然是有信息量的共享蛋白，但都不像OVAL那样稳定地把总体蛋白丰度与糖链输出区分开。", []),
    ("随后，两两富集图说明了为什么OVAL始终是最清晰的区分指标（图3D至F）。在Gallus对Anas和Gallus对Columba的比较平面中，OVAL都落在糖链偏移更明显的一侧，因此其糖链变化并不是简单镜像蛋白丰度变化，而是快于、甚至部分逆于相应的蛋白丰度偏移。在Anas对Columba的平面中，OVAL再次偏离简单的蛋白-糖链等价关系，并把同样的排序延续到鸡之外的比较中。完整糖肽鉴定进一步把OVAL放入一条连贯的跨物种序列：鸡携带紧凑的高甘露糖型糖链，鸭富集中性复合/杂合型糖链，鸽则携带更延伸的唾液酸化复合/杂合型糖链。综上，图3A至F将OVAL界定为糖基化变化与表型关系最强的共享蛋白。", []),
])

p_s2d_cn = spara([
    ("由于这些OVAL糖链类别在大小和电荷分布上差异显著，更合理的比较变量是OVAL表面可及性，而不是单纯的OVAL丰度。", []),
    ("真正相关的特征，是被不同糖链装饰后其酸性界面还有多少保持化学可及。直系同源控制、丰度解耦和糖链类别推进三方面证据共同将OVAL保留为唯一同时保持可比、化学特异且可进行结构追踪的共享候选。", []),
])

add_centered_figure("Fig3_composed.png", width_cm=15.5)
add_main_figure_legend(
    "图3.",
    "直系同源约束下的丰度-糖链分析确定OVAL为最清晰共享区分子。",
    [
        ("(A至C) 鸡、鸭和鸽物种内蛋白丰度与糖链丰度log2转换后的proteotype coevolution图；插图给出Spearman ρ和双侧p值，高亮标注保留的基质蛋白（OVAL、OC116、TRFE和OC17）。(D至F) Gallus对Columba、Gallus对Anas和Anas对Columba的两两二维糖链-蛋白富集图。虚线对角线表示蛋白和糖链变化幅度相等；向糖链富集侧偏移表示糖链变化超过蛋白丰度变化。", False, False),
    ],
)

head("OVAL糖链状态重塑表面可及性")

p_s3a_cn = spara([
    ("OVAL随后被作为最强共享候选，用于检验其糖链类别如何改变生物物理可及性。为此，我们重建了主导的糖基化OVAL构象，并为每个物种配对构建 apo 参考，以检验三物种差异是否主要来自糖链依赖的表面行为，而非仅来自蛋白骨架序列本身。", [4, 11]),
    ("代表性重建构象和物种特异性表面图显示，优势糖链在同一折叠蛋白骨架上占据不同空间包络（图4A和B）。在A图中，编号1和2分别标记糖链端到端向量的两端，3标记糖链质心，4标记蛋白Cα质心，半透明球体则把糖链质心周围的回转半径包络可视化出来。B图进一步把这种几何变化转成表面可及性：有颜色的区域是仍可接近Ca²⁺的相关区域，黑色区域则是这些区域被遮蔽后的状态。", []),
])

p_s3b_cn = spara([
    ("鸽首先通过占据最大的整体糖链包络与另外两种鸟分开，这一点体现在图4C更高的回转半径和图4E更长的端到端距离上。若把A图中1到2的向量看作糖链的‘展开长度’，那么鸽的这条向量更长，且以3为中心的球也更大；这就意味着它在同一蛋白骨架上覆盖了更大的空间范围，同时与4所代表的蛋白质心保持着更大的几何外扩。图4D中更近的局部骨架接近距离，以及图4F中更宽的糖链-蛋白距离分布，也都与这种更伸展但仍会回折到OVAL表面的构象一致。", []),
    ("鸡则定义了相反的端点，其糖链更紧凑，对酸性界面的几何侵入最弱；鸭在回转半径和整体糖链-蛋白间距上更接近鸡，但在端到端跨度和最小骨架接近距离上又与另外两者分开。因此，图4C至F把糖链类别推进转换成了一种遮蔽几何：A图里球越小、1-2跨度越短且更贴近4，说明糖链越紧凑；球越大、1-2跨度越长，说明糖链越延展并更容易参与表面遮蔽。", []),
])
p_s3c_cn = spara([
    ("图4G至J以越来越严格的层级解析了同一片酸性界面。结合B图来看，有颜色的部分就是仍然可接近Ca²⁺的相关区域，而黑色部分是这些区域被糖链遮蔽后的状态。图4G因此测量整体界面遮蔽，图4H考察候选酸性残基中仍保持热点的比例，图4I测量热点残基保留下来的表面积，图4J则统计同时仍具静电有利性和物理可达性的Ca²⁺热点子集。", []),
    ("界面遮蔽从鸡到鸭再到鸽逐步增强，而热点表面积、热点比例和净可及Ca²⁺热点都保留了同样的排序。综合这些面板可以看出，在早期矿化阶段，共享的酸性OVAL表面被逐步遮蔽；图中字母用于表示Tukey HSD分组，p < 0.05 的不同字母代表显著差异，而 *** 代表 p < 0.001。", []),
])

p_s3d_cn = spara([
    ("配对的糖基化与apo对照进一步显示，加上糖链后，Ca²⁺相关热点残基数量和暴露羧酸基表面的变化在鸽中最清楚；鸭沿同一方向偏移，但在结构层面并未得到稳定的显著性判定；鸡则因为仅有一个糖基化结构而只能作描述性比较（图4K和L；图S10）。把这些结果和B图对应起来看，可以理解为糖基化并不是在重新创造新的Ca²⁺位点，而是在保留或遮蔽同一组可接近位点：有颜色的区域是仍可接近的Ca²⁺相关区域，黑色区域则表示这些区域被遮蔽。由此，恢复出的结构差异并不是一般性的序列差异，而是糖链把矿化起始时暴露给离子环境的酸性表面重新组织了出来。图4K至N随后利用匹配的糖基化和apo参考，把同一对比压缩到整体界面层面。跨这些指标，鸡保留了最多的Ca²⁺相关可及表面，鸽把最大的份额转入糖链影响状态，鸭则整体向低可及性一侧偏移，但并未在所有指标上都与鸽或apo参考形成统一分离。", []),
    ("因此，鸡保留了最强的推定Ca²⁺捕获能力，也最符合既往所提到的、矿化起始时OVAL较易进入Ca²⁺响应式开放状态的情形。鸭和鸽则从不同结构背景转向较低可及性一侧。相同的排序也对应了表型顺序：鸡同时具有最致密的乳突场和最高的局部出壳抗性，而鸭和鸽则收敛到较低抗性一侧。因此，图4A至N把糖链依赖的分离、糖链几何、界面遮蔽以及共享基质蛋白上的Ca²⁺相关可及性连接在一起。", [4, 11, 29]),
])

doc.add_page_break()
add_centered_figure("Fig4_composed.png", width_cm=15.2, before=0, after=20)
add_main_figure_legend(
    "图4.",
    "OVAL糖链类别重塑表面几何与Ca²⁺相关界面可及性。",
    [
        ("(A) OVAL表面上代表性重建糖链构象。编号1和2分别表示糖链端到端向量的起点和终点，3表示糖链质心，4表示蛋白Cα质心。半透明球体表示以糖链质心为中心、半径等于糖链回转半径Rg的包络球。(B) 物种特异性表面图，其中有颜色的是Ca²⁺-relevant regions，黑色的是被遮蔽的Ca²⁺-relevant regions。(C至F) 物种间比较糖链回转半径、最小糖链-骨架距离、糖链端到端距离和糖链-蛋白距离。(G至J) 物种间比较界面遮蔽、热点比例、热点残基SASA和净可及Ca²⁺热点。(K至N) 糖基化与配对apo OVAL参考之间的Ca²⁺热点残基数量、羧酸基表面可及性、Ca²⁺热点可及性和Ca²⁺热点残基SASA比较。系综层面的物种比较采用双侧Mann-Whitney U检验；在存在结构层面变异时，糖基化与apo的结构层面对照采用一样本Wilcoxon符号秩检验；不同字母表示Tukey HSD分组（p < 0.05），***表示p < 0.001。", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

head("有限元分析把同一对比连接到局部出壳抗性")

p_s4a_cn = mixed([
    ("有限元检验把共享的破壳齿界面转化为一个明确的内向外加载设计。图5A将物种特异性的喙部俯视图与基于micro-CT重建的有限元设置以及峰值接触力和峰值剪切应力的汇总箱线图并列展示。这些设置建立在图1B概括的喙尖几何基础上。由于网格保留了物种特异性的壳体几何，这一分析始终锚定在形态学上已经识别出的同一乳突层背景之上。冲击加载在蛋壳碎片的多个偏移位置上采样，从而为每个物种获得独立的接触剪切应力时间曲线。为降低模型尺寸、整体几何以及尤其是蛋壳厚度的影响，我们同时记录原始峰值接触力F_max和峰值接触剪切应力τ_max。峰值τ_max被用作乳突接触界面局部出壳抗性的直接读数。各物种的均值 ± s.d.按各采样位置计算（图S11A至F；壳厚分别为", False, False),
    ("G. gallus", False, True),
    (" 0.29 mm、", False, False),
    ("A. platyrhynchos", False, True),
    (" 0.35 mm、", False, False),
    ("C. livia", False, True),
    (" 0.19 mm）。", False, False),
])

cite(p_s4a_cn, [16, 37, 69])

doc.add_page_break()
add_centered_figure("Fig5_composed.png", width_cm=15.5, before=0, after=20)
add_main_figure_legend(
    "图5.",
    "内向外有限元加载解析乳突界面的局部出壳抗性。",
    [
        ("(A) 物种特异性喙部俯视图（虚线框标示破壳齿位置）及其对应的micro-CT有限元模型，并展示峰值接触力（F_max）和峰值剪切应力（τ_max）的汇总箱线图，包括 ", False, False),
        ("Gallus gallus", False, True),
        ("、", False, False),
        ("Anas platyrhynchos", False, True),
        (" 和 ", False, False),
        ("Columba livia", False, True),
        ("。每个物种组中，左侧为喙部俯视图，右侧为蛋壳碎片网格、锥形压头及接触时的代表性有限元输出。(B) 9个冲击位置的平均接触力时间曲线，阴影表示±1σ。(C) 同一9个位置的平均接触剪切应力时间曲线，阴影表示±1σ。箱线图中的点表示单个冲击位置（每物种n = 9）；p值采用单因素ANOVA计算，不同字母表示Tukey HSD分组。模拟基于实测重建壳体几何而非理想化壳体。", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

mixed([
    ("F_max在物种间存在显著差异（p = 1.64 × 10⁻¹³）。", False, False),
    ("G. gallus", False, True),
    (" 为1.12 ± 0.11 N，", False, False),
    ("A. platyrhynchos", False, True),
    (" 为0.90 ± 0.09 N，", False, False),
    ("C. livia", False, True),
    (" 为0.49 ± 0.04 N，且所有两两比较均显著（图5A和B）。相比之下，τ_max收束为两级格局（p = 6.64 × 10⁻¹⁰）。", False, False),
    ("G. gallus", False, True),
    (" 为551.60 ± 108.80 MPa，显著高于", False, False),
    ("A. platyrhynchos", False, True),
    (" 的404.00 ± 39.60 MPa和", False, False),
    ("C. livia", False, True),
    (" 的393.00 ± 35.20 MPa，而后两者之间无统计学差异（图5A和C）。", False, False),
])

mixed([
    ("F_max与τ_max之间的差异澄清了鸭的结果。它更高的原始接触力主要由更大的壳厚驱动（0.35 mm，而鸽为0.19 mm），而不代表更优越的单位面积材料抗性。相反，", False, False),
    ("G. gallus", False, True),
    ("相对于另外两个物种表现出36至40%的τ_max升高，表明其局部出壳抗性更高，且独立于壳厚。由此形成的高低分组中，", False, False),
    ("G. gallus", False, True),
    ("单独位于高值组，而", False, False),
    ("A. platyrhynchos", False, True),
    ("与", False, False),
    ("C. livia", False, True),
    ("共同处于低值组。这一分组与Tukey HSD在乳突密度上恢复出的分组一致（图1D）。因此，力学结果保留了乳突层组织和OVAL可及性中已经恢复出的同一对比。",
     False, False),
])

mixed([
    ("如果只看整壳层面的破裂力，鸭可能会因为壳更厚而显得在力学上优于鸡，尽管它并不具备同样的高密度乳突状态。相反，τ_max聚焦于基于micro-CT重建的乳突界面局部出壳抗性，从而消除了这种歧义。它表明，高密度鸡状态仍然保持独立，而鸭和鸽则在较低抗性上收敛。这一功能读数保留了前文已经显现出的同一不对称性，并把与糖基化相关的差异连接到三种模型物种的局部破壳力学上。", False, False),
])

para("讨论", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT, heading=True)

p_disc_mam1_cn = smixed([
    ([('在这组数据中，跨物种分化首先在乳突层被解析出来，而不是表现为整体基质蛋白工具箱的全面更替。', False, False),
            ('在大体共享的蛋壳基质背景下，OVAL 糖链状态构成了连接结构、表面可及性与局部出壳抗性的最清晰分子轴线。', False, False)], [1, 16, 18]),
])

p_disc_regulator_cn = spara([
    ("这一三物种设计之所以关键，在于蛋壳性状是沿连续的生态与发育梯度组织的，而不是由单一二分标签决定。", [15, 39]),
    ("巢穴环境对应陆生到水域利用的连续轴线，后代状态对应更早成到更晚成的连续谱，两条维度都难以被“是/否”式划分充分表征。", [3, 23]),
    ("鸭在这一设计中尤其有信息量：它在发育上保留了广义早成状态，但 OVAL 糖链状态和可及性谱型转向中间型，且其 τ_max 结果与鸽而非鸡收敛。由此，这一比较在保持出壳界面可比的前提下，覆盖了生态—发育连续空间中被有意拉开的区域。", [3, 15, 22, 23]),
], before=0, after=120)

p_disc_axis_cn = spara([
    ("乳突层成矿模式仍是这一解释框架中的核心结构层级。", [1, 28]),
    ("一旦早期方解石晶体单元建立，后续蛋壳区域会继承首次成矿窗口设定的间距逻辑。因而，高密度乳突场可同时改变基质保留、矿物连续性、局部应力再分配与最终形态。", [1, 30, 36]),
    ("这种强调与既往研究一致：乳突层位于晶体成核与基质调控的交汇处。当前比较在此基础上进一步把该层直接连接到跨物种糖链状态读数，而不止于整壳质量描述。", [1, 28, 31, 32]),
    ("近期家禽组学研究越来越多地把年龄、壳腺转录、细胞外囊泡载荷和其他整壳质量指标与蛋壳表型关联，但这些描述通常仍宽于这里被分离出的近端材料层。", [33, 52, 57, 70]),
    ("因此，乳突层组织并非“又一个壳体性状”，而是基质化学最可能开始偏置后续力学结局的最早材料背景。", [1, 2]),
    ("正因其结构位置，乳突层组织是首个可被读作“潜在具有后果”的跨物种差异，而非仅描述性差别。", [1, 28]),
], before=0, after=120)

p_disc_mam2_cn = spara([
    ("在本研究检验的分子层中，OVAL 的 N-糖链结构与跨物种结构对比的对应最紧密。", []),
    ("直系同源组更替、基因家族变化和糖蛋白网络分化仍然重要，但它们主要定义比较背景，而非最近端解释。OVAL 糖链状态之所以信息量高，在于其跨物种共享、化学可解释，并位于已被指认为参与矿化的高丰度基质蛋白上。", [4, 18, 27]),
    ("既往研究已将 OVAL 视为高丰度蛋壳糖蛋白和潜在成矿候选，早期糖蛋白组学也已表明蛋壳基质蛋白可处于不同 N-糖基化状态。这里的推进并非仅增加糖肽检出，而是以直系同源为约束识别与表型最稳定对应的糖链状态，并把这些归属前推到结构和力学解释中。", [4, 18]),
    ("更早的鸡研究为 OVAL 建立了糖基化位点基础，并鉴定 OC116 的糖基化 Asn。当前数据进一步解析了进入结构建模的 OVAL 直系同源 sequon 上的主导糖链类别（G. gallus N293；A. platyrhynchos 与 C. livia N97）。相较既往位点检测研究，本研究的扩展在于跨物种比较广度与糖链类别解释深度，而非仅延长单物种位点清单。OVAL 的价值不在于其“独特”，而在于它在保持跨物种可比性的同时保留了糖链类别层面的可解释化学分化。", [8, 18, 21]),
])

p_disc_other_cn = spara([
    ("非OVAL信号仍然重要。OC116和TRFE仍是有信息量的共享蛋白，而OC17仅在鸡中显示糖基化，因此可能代表一种更具谱系限制性的成矿程序。", []),
    ("前人的蛋壳研究已经分别赋予OC17、OC116和ovotransferrin相关组分明确的功能意义，而本研究并不是推翻这些认识。相反，我们的数据表明，这些蛋白更稳定地构成了生物学背景，而不是跨物种最尖锐的区分层。", [10, 19, 29]),
    ("对OC116尤其如此：更早的生化工作已经确认鸡蛋壳基质OC116存在糖基化Asn，而近期的鸟类古蛋白组学工作又进一步显示，OC116是鸟类蛋壳蛋白中序列变异性最高的一类分子之一，并且在种内层面也具有显著变异，而不是一个始终稳定的物种标记。放在这一背景下，我们当前的比较结果就更容易理解：OC116保持糖基化并不等于它一定会像OVAL那样恢复出稳定的结构—表型排序。", [21, 66]),
    ("这也说明本研究与既往蛋壳糖蛋白组工作的关系更像是下一步，而不是简单重复。前人的工作首先证明了蛋壳基质蛋白确实可以被糖基化，且位点层面的检测是可行的；而我们这里增加的是共享直系同源、优势糖型类别以及这些糖型在跨物种结构表面上的后果。", [18, 21]),
    ("共享工具箱因此仍然是多组分的，只是OVAL提供了当前最易检验的切入点。", []),
], before=0, after=120)

p_disc_oval_cn = spara([
    ("Re-Glyco 与 APBS 分析为这一论证提供了结构层桥梁。", []),
    ("鸡的紧凑糖链使关键酸性 OVAL 表面保持相对暴露；鸽更长且电负性更强的糖链则在空间与静电两层面降低 Ca²⁺ 接近；鸭再次处于中间状态。", []),
    ("既往体外与结构研究已提示 OVAL 构象和静电性质在矿化过程中重要，但跨鸟类物种的匹配糖型分辨表面系综此前尚未比较。", [4, 11]),
    ("因此，本研究把糖链状态变化解析为可进行物理解释的表面差异。尽管该结果不构成直接因果证明，但它支持一个克制推论：同一基质蛋白上的不同糖链状态可改变呈现给矿化环境的化学表面，并可能参与这里观察到的结构分化。", []),
], before=0, after=120)

p_disc_mech_cn = spara([
    ("本研究的力学比较围绕出壳过程中的内向外加载事件设计，而非常规外压或整壳破裂测试。", []),
    ("这一差异至关重要：蛋壳厚度会显著抬高绝对失效载荷，而 τ_max 受厚度混杂更小，更直接反映载荷通过乳突界面的传递。", [16, 34, 69]),
    ("因此，本研究与既往有限元和蛋壳强度工作形成互补：核心问题是内侧乳突界面是否保留了先前由基质状态和形态组织推断出的同一对比。", [16, 34, 35, 69]),
    ("鸭最清楚地体现了这种分离：更厚壳体抬高了 F_max，却未重建鸡所呈现的高 τ_max 状态。", []),
])

p_disc_evo_cn = para(
    "另一个需要考虑的问题是，乳突层在孵化后期和出壳过程中可能发生部分吸收。这个问题并不削弱当前比较的意义，因为我们量化的是乳突密度和晶体单元组织，这些特征即便在最内侧部分材料被吸收后，仍然保留在蛋壳整体结构中。同样的考虑也影响了力学读数的选择。我们强调第二个特征峰而不是第一个，因为最早出现的受力峰更容易受初始形貌接触影响，而后一个特征峰更能反映载荷穿过整个壳壁的应力传递。",
    bold=False, size=11, before=0, after=120
)

p_disc_discriminate_cn = spara([
    ("这些考量有助于把壳厚缓冲与发育背景，同本文强调的材料层路径区分开来。", []),
    ("蛋壳厚度、体型和广义繁殖生态都提供背景变异，谱系历史同样重要。", [3, 14]),
    ("但基于厚度的解释不能解释 τ_max 差异，而弥散的谱系分化解释也无法解释为何同一对比会在糖链类别、静电可及性、乳突层组织和出壳相关力学中反复出现。", [16, 37]),
    ("这组数据中反复出现的是糖链状态、表面遮蔽、乳突层组织与内向外加载下 τ_max 的一致对齐。", []),
    ("生态与系统发育定义了比较设计空间；基质蛋白糖链状态则仍是其中最近端且化学可读的解释层。", [4, 18]),
], before=0, after=120)

p_disc_function_cn = para(
    "综上，在这组数据中，这一比较收束到一个鸡式蛋壳状态。鸡同时具有最致密的乳突场、受遮蔽最少的OVAL钙相关表面，以及内向外加载下最高的局部出壳抗性。这一模式支持一个更广的推论：在被重复使用的基质蛋白上，化学特异性的状态可能比单纯的蛋白组周转更清楚地组织矿化表型。",
    bold=False, size=11, before=0, after=120
)
cite(p_disc_function_cn, [67, 73, 74])

p_disc_selection_cn = para(
    "鸭和鸽仍然关键，因为它们共同定义了这一鸡式状态在壳体结构与生态—发育位置上的边界。鸭将更大壳厚、中间型 OVAL 可及性与低 τ_max 结合在一起，表明仅凭厚度不能重建鸡式状态。鸽在更薄壳体和不同乳突背景下与鸭在低 τ_max 上收敛。综合这些对照，鸡在当前采样设计空间中成为连接糖链依赖基质行为与蛋壳性能的参考状态；在这一框架下，OVAL 糖链状态是使该状态获得力学可解释性的最直接分子层。",
    bold=False, size=11, before=0, after=120
)

p_disc_biomineral_cn = para(
    "同样的分析序列可能扩展到鸟类蛋壳之外。许多生物矿化系统依赖有机基质通过化学特异性的界面状态调控离子进入、表面暴露和矿物成核，而不仅由总体成分决定。在这一更广框架中，本研究流程提供了从糖蛋白状态到表面呈现再到介观功能的可迁移路径。类似尺度桥接问题也出现在其他矿化组织与仿生材料中。该逻辑还可延伸到再生应用场景，尤其是蛋壳来源材料或膜蛋白用于组织工程和骨修复的探索。因此，本研究为检验化学特异性基质状态如何组织生物矿化行为提供了一个可迁移模板。",
    bold=False, size=11, before=0, after=120
)
cite(p_disc_biomineral_cn, [64, 67, 68, 73])

p_disc_future_cn = para(
    "本研究范围仍有边界。我们分析的是主导糖型而非体内完整糖链系综；同时在平均蛋壳尺度上把各物种视为机械均一，并在 APBS 框架下使用约束尚不充分的子宫离子条件。下一步关键检验包括：定义糖型的矿化实验、在鸡中直接操控 OVAL 糖基化，以及对同一内向外力学对比进行位点分辨验证。这些实验将澄清 OVAL 糖链状态是直接参与壳体矿化，还是以异常高保真度标记鸡式高抗性状态。",
    bold=False, size=11, before=0, after=120
)

p_disc_close_cn = para(
    "总之，本研究在三种鸟类蛋壳中把乳突层组织、糖蛋白状态、表面可及性与局部出壳力学连接在同一框架下。鸡定义了这条轴线的高抗性端点，表现为致密乳突组织、紧凑 OVAL 糖链、更高 Ca²⁺ 相关表面暴露和乳突界面最高局部抗性。随着其他高丰度蛋壳基质蛋白获得可比糖型归属，这一框架可继续扩展。跨形态测量、糖蛋白组学、结构与力学四层证据，OVAL 糖链状态始终是与鸡式蛋壳状态最一致的分子特征。",
    bold=False, size=11, before=0, after=120
)

p_disc_limits_cn = p_disc_close_cn

# ════════════════════════════════════════════════════════════════════════════
# 方法
# ════════════════════════════════════════════════════════════════════════════
para("材料与方法", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

head("生物材料")

p_m_bio = mixed([
    ("在产蛋中期采集三个禽类品系的受精蛋，包括茶花鸡粉壳蛋鸡7枚、绍兴麻鸭绿壳蛋鸭7枚和白羽王蛋鸽19枚。", False, False),
    ("Gallus gallus", False, True),
    (" 蛋来自中国农业大学家禽资源保护场（北京，中国）；", False, False),
    ("Columba livia", False, True),
    (" 蛋由中国农业大学动物医学院常于教授提供；", False, False),
    ("Anas platyrhynchos", False, True),
    (" 蛋由北京金星鸭业提供。所有种蛋在分析前均按种蛋保存条件于16°C保存7 d。", False, False),
])

head("蛋壳基质蛋白提取")

mixed([
    ("采用既有的EDTA脱矿化方案提取蛋壳乳突层（EML）基质蛋白。鸡蛋以去离子水漂洗后置入无菌密封袋。每个物种保留1枚蛋用于显微CT分析，其余蛋壳用于基质蛋白提取。剩余6枚鸡蛋和6枚鸭蛋分别合并为3个两蛋提取单元，18枚鸽蛋合并为3个六蛋提取单元；这些合并提取单元同时作为shotgun proteomics和完整糖肽分析的匹配生物学样本。对 ", False, False),
    ("G.\u00a0gallus", False, True),
    (" 和 ", False, False),
    ("A.\u00a0platyrhynchos", False, True),
    ("，先以15 mL 5% EDTA（0.13 mol/L，pH 7.6，补加10 mmol/L 2-巯基乙醇）在20°C处理30 min，并轻柔揉捏以去除蛋壳外表皮层（ECL），随后以去离子水漂洗。鸽蛋壳未识别到离散cuticle层，因此 ", False, False),
    ("C.\u00a0livia", False, True),
    (" 仅以蒸馏水漂洗后直接进入同一提取流程。随后三物种都在相同EDTA-2-巯基乙醇条件下延长提取12 h（20°C）。所得悬液以1,000 × g离心15 min，沉淀重悬后再次离心，合并上清并于−80°C保存至分析。三物种在相同提取化学条件下并行处理，以尽量降低操作漂移造成的假性差异。", False, False),
])

head("显微CT成像与乳突形态计量")

p_m_ct_cn = para(
    "每个物种从赤道区靠近钝端半部中点的位置切取1块4 mm × 4 mm蛋壳碎片，使用Phoenix V|tome|x M微焦点CT系统（GE Sensing and Inspection Technologies GmbH，Wunstorf，德国）扫描。X射线源参数固定为85 kV和160 μA，无滤光片；各样品共采集1,800张投影图像。重建体数据以16-bit unsigned各向同性格式导出，x、y、z方向采样间距约为0.003836 mm（约3.84 μm体素）。扫描后，每块碎片均等分为9个子区域用于后续区域定量。体数据在3D Slicer中重建，并在Segmentation工作流中使用Threshold模块进行蛋壳分割，自动阈值初选后由操作者校正阈值。三物种阈值由同一操作者并排复核，在保留全部真实壳体体素的同时尽量保持可见孔道开口。随后依次采用5 × 5 × 5中值滤波降噪、最大连通域保留和9 × 9 × 9填孔。对每个子区域，基于labelmap计算3项形态参数。先复制分割后的蛋壳模型并以Fill Holes构建封闭实体，再以封闭实体减去原始壳体模型得到乳突间隙层，其中该层平面内出现的封闭孔洞定义为mammillary knobs。乳突密度定义为乳突数除以分析单元面积。同一区域的总蛋壳体积直接由labelmap获得，平均柱状单元体积定义为总壳体体积除以乳突数；柱状单元体积分数则定义为平均柱状单元体积除以对应分析单元总蛋壳体积。由于正常鸟类蛋壳中由乳突启动的柱状单元在平面内通常呈重复且近似均匀排列，这些参数被视为整体壳体组织的局部平均代表值。每物种的9个观测值均来自同一块扫描碎片上的非重叠子区域，因此它们用于刻画碎片内部的空间变异和局部平均状态，而不应被理解为9个独立的生物学样本。三物种全部采用相同分割与后处理流程，以确保比较主要反映形态差异，而非重建设置差异。"
)
cite(p_m_ct_cn, [1, 30])

head("蛋壳基质蛋白质组学")

para(
    "用于shotgun proteomics的蛋壳基质提取样本与显微CT取样后的样本集对应：每个物种均为3个合并生物学重复，其中鸡和鸭每个重复由2枚蛋组成，鸽每个重复由6枚蛋组成。蛋白质以裂解液（1% SDS、1%蛋白酶抑制剂混合物）重悬，冰上超声裂解后在4°C、12,000 × g离心10 min澄清，并以BCA法定量。蛋白质经预冷丙酮沉淀（5倍体积，−20°C，2 h）、丙酮洗涤两次后重溶于200 mM TEAB。二硫键以5 mM DTT在56°C还原30 min，再以11 mM碘乙酰胺在室温避光烷基化15 min。随后按酶:底物质量比1:50加入测序级胰蛋白酶过夜消化，并以Strata X SPE柱脱盐。LC-MS/MS分析前未进行离线HPLC分级；每次proteome采集上样20 μg肽段。"
)

mixed([
    ("脱盐肽段重溶于流动相A（0.1%甲酸水溶液），上样至自制15 cm × 100 μm i.d.反相C18分析柱，并联用Vanquish Neo UPLC系统（Thermo Fisher Scientific）。流动相B为0.1%甲酸的80%乙腈，流速保持400 nl/min。梯度程序为0–0.5 min 4% B，0.5–0.6 min 4–8% B，0.6–13.6 min 8–22.5% B，13.6–20.5 min 22.5–35% B，20.5–20.9 min 35–55% B，20.9–21.4 min 55–99% B，21.4–22.6 min 99% B。液相分离后，肽段经1,900 V纳喷雾电离源进入Orbitrap Astral质谱仪（Thermo Fisher Scientific）。全扫描在Orbitrap中以240,000分辨率、380–980 m/z范围采集；MS/MS在Astral分析器中以80,000分辨率采集，采用DIA模式HCD碎裂（NCE = 25%），固定首质量150 m/z，AGC目标500%，最大注入时间3 ms。DIA数据使用DIA-NN v1.8 against species-specific reference proteomes — ", False, False),
    ("G.\u00a0gallus", False, True),
    ("（43,711条目）、", False, False),
    ("A.\u00a0platyrhynchos", False, True),
    ("（91,801条目）和 ", False, False),
    ("C.\u00a0livia", False, True),
    ("（17,309条目；均下载于2024年8月）联合反向诱饵序列进行检索。使用物种匹配的参考数据库有助于降低检索结果向注释更完善蛋白组偏置的风险。酶切特异性设为Trypsin/P，最多1个漏切；固定修饰包括N端甲硫氨酸切除和Cys carbamidomethylation。蛋白和肽段FDR均控制在1%以内。", False, False),
])

head("完整糖肽质谱")

para(
    "完整糖肽分析沿用同一批3个合并生物学重复，每个合并样本取200 μg肽段消化物作为富集输入。N-糖肽通过亲水作用色谱（HILIC）富集：肽段重溶于上样缓冲液（80% ACN、5% TFA），加载至HILIC柱，以上样缓冲液洗涤3次后，以0.1% TFA、50 mM碳酸氢铵和50% ACN洗脱两次。洗脱液经C18 Zip-Tips脱盐并真空干燥。糖肽组分在同一nano-LC平台以34 min梯度（4–99% B，400 nl/min）分离。全扫描在240,000分辨率下于700–2,000 m/z范围采集；MS/MS以80,000分辨率采集，固定首质量120 m/z，cycle time 0.6 s，AGC target 100%，intensity threshold 25,000 ions/s，maximum injection time 5 ms。原始DDA数据使用MSFragger v3.4 against the same species-specific reference proteomes进行检索，设定为严格trypsin切割（最多2个漏切）、肽长7–50个残基、固定Cys carbamidomethylation、可变N端乙酰化和Met氧化，并使用MSFragger默认糖基化质量偏移。蛋白、肽段和PSM FDR均控制在1%以内。N-糖链结构类别按Oxford nomenclature分为6类：High-Mannose、Paucimannose/Truncated、Neutral Complex/Hybrid、Fucosylated Complex/Hybrid、Sialylated Complex/Hybrid和Other。每个蛋白在每个物种中的类别丰度定义为该类别占总糖链-位点信号强度的比例。结构类别在位点层面鉴定后再汇总，以便在共享蛋白背景上比较跨物种糖链使用方式。"
)

head("比较蛋白质组分析与基因家族进化")

p_m_ortho_cn = mixed([
    ("三物种蛋白质序列采用OrthoFinder（全对全BlastP；"
     "E值阈值1\u00a0\u00d7\u00a010\u207b\u00b9\u2070；MCL膨胀系数2.0）划分至直系同源群，"
     "共得到3,250个直系同源群作为富集分析背景集。"
     "物种分歧时间参考已发表时树：", False, False),
    ("G. gallus", False, True),
    ("\u2013", False, False),
    ("A. platyrhynchos", False, True),
    (" 83.37\u00a0Mya，", False, False),
    ("G. gallus", False, True),
    ("\u2013", False, False),
    ("C. livia", False, True),
    (" 90.84\u00a0Mya。"
     "基因家族扩张与收缩动态以CAFE5结合时间校正系统发育树推断。"
     "两两共享、物种特有、扩张及收缩直系同源群集的GO富集分析"
     "通过OrthoVenn3平台（https://orthovenn3.bioinfotoolkits.net）"
     "以3,250个直系同源群为背景进行；"
     "校正后p\u202f<\u202f0.05的GO条目视为显著富集。", False, False),
])
cite(p_m_ortho_cn, [3, 5, 14])

head("跨物种糖蛋白直系同源物鉴定")

para(
    "以G.\u00a0gallus参考序列对非参考物种蛋白质组进行BlastP比对"
    "（E值阈值1\u00a0\u00d7\u00a010\u207b\u2075；最多500个目标序列；输出250个比对结果），"
    "鉴定四种靶标蛋壳糖蛋白（OVAL、OC116、TRFE、OC17）的跨物种高可信直系同源物。"
    "候选命中保留标准为平均最大序列同一性\u2265\u00a00.80；"
    "当Query与Subject非重叠HSP数量不等时，放宽至\u2265\u00a00.50。"
    "用于后续结构和定量分析的最终UniProt直系同源物编号详见补充表1。"
)

head("蛋白丰度与糖链丰度整合比较")

para(
    "图3A至C所用的蛋白质与糖基化位点定量表分别来自各物种的Protein_quant与"
    "Site_quant工作表。若存在Number Comparable字段，则蛋白条目和糖基化位点条目均仅保留\u2265\u00a02的特征，以确保下游comparable-protein分析只比较在3个合并生物学重复中至少2组被检出的项目。每个蛋白accession的蛋白丰度定义为该物种全部"
    "强度列的平均值；每个糖基化位点的糖链丰度定义为对应位点强度列的平均值；"
    "仅保留正值信号。随后按protein accession将糖基化位点表与蛋白表内连接，"
    "使每个散点代表一个具有匹配蛋白丰度信息的定量糖基化sequon。蛋白丰度与"
    "糖链丰度经log2转换后，在各物种内分别计算Spearman秩相关及双侧p值。"
    "OVAL、OC116、TRFE和OC17依据图2E概括的严格直系同源注释高亮显示，"
    "标签同时标出对应糖基化Asn位点。"
)

para(
    "图3D至F的两两糖链-蛋白二维富集图基于直系同源映射后的物种间蛋白与糖链"
    "丰度差构建。每个accession的蛋白丰度定义为非零重复强度的平均值；若存在"
    "Number Comparable字段，则先去除<\u00a02的蛋白条目。蛋白层面的糖链丰度定义为"
    "该accession下全部定量糖基化位点平均非零强度之和。Gallus对Anas和Gallus对"
    "Columba的比较空间分别由blastp outfmt 6结果建立，对每个query保留最佳命中；"
    "筛选条件为平均E值<=1 × 10⁻⁵且平均序列同一性>=0.40；若query与subject的"
    "非重叠HSP数量不同，则改用最大序列同一性>=0.40作为阈值。Anas对Columba的"
    "比较则通过同时通过上述过滤的Gallus共享直系同源进行桥接。对每一对保留的"
    "直系同源蛋白，x坐标定义为log2(I_ref) - log2(I_comp)，y坐标定义为log2(G_ref) - "
    "log2(G_comp)，其中I与G分别表示蛋白丰度和糖链丰度。因此，y = x对角线表示"
    "蛋白与糖链变化幅度相当，而向糖链富集一侧偏离则表示糖链变化超过了对应的"
    "蛋白丰度变化。"
)

head("N-糖链结构系综建模")

p_m_reglyco_cn = para(
    "OVAL直系同源蛋白的三维结构（AlphaFold2预测模型）通过UniProt登录号"
    "经GlycoShape平台（glycoshape.org）获取。"
    "IGP-MS检测到的N-糖链组成通过单同位素质量匹配（容差\u00b10.5\u00a0Da）"
    "与GlycoShape糖链库比对，"
    "所用残基质量为：HexNAc 203.0794\u00a0Da、Hex 162.0528\u00a0Da、"
    "NeuAc 291.0954\u00a0Da、dHex 146.0579\u00a0Da、Pen 132.0423\u00a0Da，"
    "并施加18.0106\u00a0Da水分子修正；"
    "匹配成功的糖链以GlyTouCan登录号标识。所有能够与GlycoShape库匹配的实验检测糖型均被保留进入后续建模，而不是预先裁剪到单一优势子集。"
    "构象系综随后通过GlycoShape Re-Glyco Ensemble工具"
    "（glycoshape.org/ensemble）生成——"
    "该工具基于Privateer晶体学标准的二面角约束和GlycoShape分子动力学构象库进行采样，"
    "精确还原缺失糖链。"
    "建模流程为：首先通过GlycoShape\u00a0API以UniProt登录号创建会话，"
    "从结构模型中识别可用N-糖基化测序子；"
    "随后将每种匹配糖链独立提交建模任务，"
    "挂载至目标测序子（G.\u00a0gallus N293；"
    "A.\u00a0platyrhynchos与C.\u00a0livia N97），"
    "参数设定：系综大小50个、随机种子42、PDB格式输出。"
    "最终生成G.\u00a0gallus 50个糖蛋白模型（1种糖型）、"
    "A.\u00a0platyrhynchos 150个（3种糖型）、"
    "C.\u00a0livia 700个（14种糖型，含从GlycoShape库解析的4种NeuAc位置异构体）。"
    "所有糖链任务均采用相同随机种子与系综大小，以尽量保持三物种之间一致的采样深度。"
    "以BioPython对各模型原子坐标计算系综几何描述符："
    "糖链全部重原子的回旋半径（Rg）、糖链端到端距离，"
    "以及糖链任意重原子与蛋白质C\u03b1原子间的最小距离（最小C\u03b1接触距离）。"
    "对各描述符进行逐结构汇总统计（均值\u00b1标准差）"
    "及物种两两比较（Mann\u2013Whitney\u00a0U检验，双侧）。"
)
cite(p_m_reglyco_cn, [11, 56, 65])

head("静电势计算")

p_m_apbs_cn = para(
    "采用APBS v3.4.1对每个Re-Glyco系综模型及去除糖链后的配对apo参考结构计算静电表面势。原子部分电荷和半径通过PDB2PQR赋值，使用CHARMM36力场和PROPKA在pH 7.4下确定质子化状态；糖链重原子部分电荷来自已发表的GLYCAM06参数。APBS输入网格根据PQR边界框自动生成，四周外扩10 Å，目标网格间距0.5 Å；聚焦网格长度设为粗网格长度的70%。非线性Poisson-Boltzmann方程采用single-ion boundary conditions求解，单价盐浓度0.15 mol/L（阳离子半径2.0 Å，阴离子半径1.8 Å），蛋白介电常数2.0，溶剂介电常数78.54，溶剂可及表面定义smol，电荷离散方式spl0，溶剂探针半径1.4 Å，spline window 0.3 Å，表面密度10.0，温度298.15 K。溶剂可及表面积采用Shrake-Rupley算法计算；相对ASA ≥ 0.25的残基定义为表面残基。Ca²⁺结合静电热点定义为APBS电势 < −5 kT/e 的表面Asp或Glu残基。报告的系综指标包括热点数（N_hot）、每热点平均SASA、热点占全部表面Asp/Glu比例以及表面静电势中位数。全部模型均采用同一静电阈值和表面定义规则，以保持跨物种可比性。"
)
cite(p_m_apbs_cn, [12, 42, 43])

head("有限元分析")

p_m_fea_cn = mixed([
    ("用于后续有限元分析的感兴趣区域在显微CT重建阶段定义为半径1 mm的圆柱体积。由显微CT获得的蛋壳表面模型先导出为STL文件，并在Geomagic Wrap中完成有限元前处理，包括顺序去噪（强度2）、三角面简化至约300,000个面片、0.01 mm网格重构、迭代缺陷修复至零残余缺陷，以及以最小公差进行有机参数曲面拟合。处理后的蛋壳表面模型随后导入Ansys Workbench 2023 R1，并使用显式LS-DYNA模块求解（单位制：mm/kg/N/s）。为隔离结构本身造成的机械差异，三物种均赋予相同的蛋壳材料参数；参数取自Biology 10, 989 (2021; DOI: 10.3390/biology10100989) 报道的鸟类蛋壳弹性研究，而不是对每个物种单独重新估算。在求解器keyword deck中，蛋壳采用 *MAT_PLASTIC_KINEMATIC 和 *SECTION_SOLID，参数为密度2770 kg/m^3、Young's modulus 3.0 × 10^10 Pa、Poisson's ratio 0.33、yield strength 1.5 × 10^7 Pa、tangent modulus 0，以及failure前最大等效塑性应变0.05。该显式冲击设置遵循碰撞-变形模拟的一般逻辑，但缩放到了本研究关注的局部蛋壳加载几何。模拟破壳齿的冲击体为圆台（底半径0.1 mm、顶半径0.5 mm、高0.5 mm），赋予库内IRON-ARMCO显式材料并独立划分实体网格。冲击体与蛋壳之间采用 *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE，摩擦系数0.2。蛋壳网格尺寸分别为0.05 mm（", False, False),
    ("G. gallus", False, True),
    ("）、0.05 mm（", False, False),
    ("A. platyrhynchos", False, True),
    ("）和0.03 mm（", False, False),
    ("C. livia", False, True),
    ("），确保蛋壳横截面至少保留6层单元；冲击体网格为0.1 mm。冲击体沿加载轴施加50,000 mm/s初速度，而碎片边缘一组边界在全部平移和转动自由度上固定。分析总时长为1.0 × 10^-4 s，时步安全系数0.7，启用erosion、最小时步1 × 10^-8 s和automatic mass scaling；GLSTAT、SPCFORC、RCFORC、NCFORC、BNDOUT、NODOUT、MATSUM、ELOUT、JNTFORC和DEFORC以1.0 × 10^-7 s间隔输出，D3PLOT和INTFOR每1.0 × 10^-6 s输出一次。位置采样分析中，冲击体在3 × 3网格的9个横向偏移位置上加载，间距0.5 mm。9个工况之间仅平移冲击体坐标，其余材料参数、接触设置、边界条件、碎片尺寸和全部求解器控制保持不变。每个位置均提取峰值接触力（F_max）和峰值接触切应力（τ_max）。9点偏移采样使我们能够在不改变碎片尺寸或加载几何的前提下测量局部位置异质性。", False, False),
])
cite(p_m_fea_cn, [16, 37, 89])

head("统计分析")

mixed([
    ("所有数值均表示为mean ± s.d.，所有统计检验均为双侧，p < 0.05视为显著。参数性物种间比较前，先用Shapiro-Wilk检验正态性，并用Levene检验方差齐性。乳突层形态参数在满足前提后，采用单因素ANOVA结合Tukey HSD检验（α = 0.05）比较；但需说明的是，每物种这9个形态观测值来自同一块扫描碎片上的非重叠子区域，因此应解释为碎片内部的区域重复，而非9个独立生物学样本。相同的前提检验同样支持对有限元结果（F_max和τ_max）采用单因素ANOVA结合Tukey HSD。相比之下，糖链系综几何描述符（Rg、端到端距离、最小糖链-蛋白接触距离）和热点衍生的系综指标在物种间不满足正态性和/或方差齐性，因此这些变量的两两物种比较采用双侧Mann-Whitney U检验。在 ", False, False),
    ("C.\u00a0livia", False, True),
    (" 中，糖基化导致的N_hot下降通过相对于apo参考值的一样本Wilcoxon符号秩检验评估；整体界面的Asp/Glu SASA因各结构值不变而仅作描述性汇总；表面静电势中位数相对于apo参考的偏移则同样采用一样本Wilcoxon符号秩检验。未进行多重比较校正，也未剔除离群值。所有统计分析均在Python中使用scipy.stats和statsmodels完成。", False, False),
], before=0, after=120)

# ════════════════════════════════════════════════════════════════════════════
# 参考文献
# ════════════════════════════════════════════════════════════════════════════
para("参考文献", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT, heading=True)

for source_number in CITATION_ORDER:
    p_ref = doc.add_paragraph(style="Normal")
    p_ref.paragraph_format.space_before = Pt(0)
    p_ref.paragraph_format.space_after = Pt(4)
    p_ref.paragraph_format.left_indent = Pt(18)
    p_ref.paragraph_format.first_line_indent = Pt(-18)
    ref_text = f"{CITATION_MAP[source_number]}. {REF_TEXTS[source_number]}"
    r_ref = p_ref.add_run(ref_text)
    r_ref.font.size = Pt(9)
    rPr = r_ref._r.get_or_add_rPr()
    _set_font(rPr, SCI_F, BODY)

doc.save(OUT)
print(f"[OK]  {OUT}")
