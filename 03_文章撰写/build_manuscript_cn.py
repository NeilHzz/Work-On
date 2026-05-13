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

OUT = str(Path(__file__).with_name("manuscript260512_cn.docx"))
FIG_BASE = Path(__file__).resolve().parent.parent / "Figure260421"

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

# ── 行号（连续） ───────────────────────────────────────────────────────
_lnNum = OxmlElement("w:lnNumType")
_lnNum.set(qn("w:countBy"), "1")
_lnNum.set(qn("w:restart"), "continuous")
_lnNum.set(qn("w:start"), "1")
s._sectPr.append(_lnNum)

# ── 字体与段落辅助 ─────────────────────────────────────────────────────
SCI_F = "Times New Roman"
BODY = "SimSun"


def _set_font(rPr, latin_name, east_asia_name=None):
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), latin_name)
    rFonts.set(qn("w:hAnsi"), latin_name)
    rFonts.set(qn("w:cs"), latin_name)
    rFonts.set(qn("w:eastAsia"), east_asia_name or latin_name)
    rPr.insert(0, rFonts)


def fmt(run, size=11, bold=False, italic=False, heading=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    rPr = run._r.get_or_add_rPr()
    _set_font(rPr, SCI_F, BODY)


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
    return " (" + ", ".join(groups) + ")"


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
    r = p.add_run(title + " ")
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
    "基质蛋白糖链状态将鸟类蛋壳结构联系到局部出壳性能",
    bold=True, size=14, before=0, after=160,
    align=WD_ALIGN_PARAGRAPH.LEFT
)

para(
    "Short title: 糖链状态联系蛋壳结构与出壳",
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
    "鸟类的出壳起始于一个功能保守的破壳齿界面，因此物种间出壳性能的差异最终必须体现在蛋壳本身。"
    "在蛋壳内部，乳突层是整体力学性能最早建立的结构层，而乳突层又受蛋壳基质蛋白调控，这提示共享基质蛋白上的不同糖基化状态可能参与跨物种差异。"
    "这里，我们整合显微CT形态测量、蛋壳基质蛋白组学、完整糖肽质谱、结构系综建模和有限元分析，对鸡、鸭和鸽进行比较，发现乳突层组织、基质蛋白糖链状态和局部出壳抗性沿同一比较轴线变化。"
    "蛋壳基质蛋白工具箱整体上仍然共享，因此分析重点被收束到糖基化，而不是蛋白工具箱的整体替换。"
    "比较糖蛋白组学首次在这一跨物种框架下直接解析了共享蛋壳基质蛋白的具体糖型，其中以OVAL最为清晰：鸡以高甘露糖型为主，鸭转向中性复合/杂合型，鸽进一步转向更延伸的唾液酸化复合/杂合型。"
    "Re-Glyco与静电分析表明，这些糖型改变了OVAL的表面暴露和Ca²⁺相关可及性，而有限元分析进一步显示，同样的排序仍保留在乳突界面的局部出壳抗性中。"
    "综合来看，基质蛋白糖链状态构成了一个具有明确化学含义的比较层，用于连接鸟类蛋壳结构与局部出壳性能。",
    bold=False, size=10, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY
)

para(
    "Teaser: 蛋壳糖链状态把基质蛋白变化联系到局部出壳抗性。",
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
    ("鸟类出壳首先面对的是一个保守的力学问题：胚胎施加的力必须被传递到一个局部破壳位点。", [16, 17, 38, 82, 86]),
    ("在鸟类中，这个位点由短暂存在的破壳齿定义，它从壳内侧作用于蛋壳并触发出壳。", [16, 17, 38, 82, 86]),
    ("如果破壳齿的功能在不同鸟类之间总体保守，那么真正导致物种间出壳差异的生物学来源就更可能存在于蛋壳本身，而不是破壳工具本身。", [16, 17, 38, 82, 86]),
    ("在蛋壳内部，乳突层是整体力学性能最早建立的结构层，而乳突结节的位置又由蛋壳基质蛋白决定。", [1, 4, 28, 38]),
    ("因此，蛋壳为我们提供了一个可直接比较的跨尺度系统，使基质化学、微结构和与出壳相关的力学后果可以放在同一个框架里解读。", [1, 4, 16, 20, 21, 38, 42]),
])

p_s1b_cn = spara([
    ("因此，乳突层应当成为首先被检验的表型，因为它是最早能够把结构差异转译为力学差异的蛋壳层级。", [1, 4, 16, 28, 38]),
    ("而一旦比较从保守的破壳工具转移到这一与力学直接相关的蛋壳层，下一步机制解释就必须回答：究竟是哪一类分子调控了这一层，以及这些分子在不同物种中以何种状态发挥作用。", [1, 2, 4, 20, 21, 28, 38]),
])

# §2 — 已知工作与局限
p_intro2 = spara([
    ("蛋壳基质蛋白之所以是最直接的候选层，是因为它们调控乳突层成矿、晶体生长取向以及成熟蛋壳的结构组织，其中OC17、OC116、TRFE和OVAL是最具代表性的例子。", [1, 2, 4, 6, 7, 8, 9, 10, 19, 20, 21, 29]),
    ("值得注意的是，这些蛋白并不只通过“有没有”或“多少”起作用。同一种基质蛋白在不同糖基化状态下，可能具有不同生物学行为。", [18, 20, 21, 49, 50, 52]),
    ("但鸟类蛋壳共享基质蛋白到底携带哪些具体N-糖链形式，过去几乎没有在跨物种框架中被直接解析。", [18, 20, 21]),
    ("因此，当前最关键的缺口不是蛋壳是否存在物种差异，而是共享基质蛋白上的糖链状态能否帮助解释乳突层结构和出壳相关力学差异。", [2, 4, 20, 21]),
    ("换句话说，真正缺失的不是‘基质蛋白是否重要’，而是‘共享基质蛋白上的糖基化是否能够解释同一套蛋白工具箱为何会导向不同的蛋壳结构’。", [2, 4, 18, 20, 21]),
])

p_intro_sig_cn = spara([
    ("把问题锚定到出壳界面之后，这条逻辑链还应继续往下推进到结构和功能层。", [16, 17, 38]),
    ("如果糖链状态是候选解释层，那么下一步就应当检验它能否被翻译成结构功能推导。", [18, 20, 21, 49, 50, 52]),
    ("更具体地说，不同糖型如果改变了同一个共享基质蛋白的表面暴露状态，那么结构建模就应当能够揭示其Ca²⁺相关可及性如何发生变化。", [11, 12, 18, 42, 43, 49, 50, 51]),
    ("而如果这种结构排序具有生物学意义，它还应当保留在出壳相关的力学终点上，也就是破壳齿样加载条件下乳突界面的局部抗性。", [16, 17, 34, 35, 37, 38]),
])

# §3 — 核心缺口
p_intro_gap_cn = spara([
    ("因此，本文真正要问的是一个逐层推进的问题：当比较被锚定到保守的破壳齿界面之后，物种差异是否首先出现在乳突层，随后能否在共享基质蛋白的糖链状态上被解析出来，并进一步通过蛋白表面可及性得到结构解释，最终在局部出壳抗性中得到功能验证。", [55, 58, 59, 60, 65]),
    ("这样一来，引言本身的逻辑顺序就可以与全文主线保持一致：破壳齿功能相同，关注蛋壳，进入乳突层，追到基质蛋白和糖基化，再进入结构功能推导和有限元验证。", [4, 11, 12, 16, 42, 57, 69]),
])

# §4 — 本研究
p_intro4 = smixed([
    ([ ("为检验这一问题，本文选择三种喙形差异明显、但仍通过同一种破壳齿介导局部接触事件完成出壳的鸟类作为比较对象：", False, False),
            ("Gallus gallus", False, True),
            ("、", False, False),
            ("Anas platyrhynchos", False, True),
            ("和", False, False),
            ("Columba livia", False, True),
            ("，分别代表陆生早成型、强水域关联早成型和陆生晚成型模型，从而在共享出壳框架内跨越发育和生态两个被刻意拉开的比较维度。", False, False)], [3, 22, 24, 25, 82, 83]),
        ([ ("以这一比较框架为基础，本文先用显微CT界定乳突层组织，再用蛋壳基质蛋白组学和完整糖肽质谱解析共享基质蛋白及其糖链状态，随后用Re-Glyco结构建模和APBS静电分析推导蛋白表面后果，最后用有限元仿真检验同样的排序是否仍保留在局部出壳抗性中。", False, False)], [3, 22, 24, 25]),
        ([ ("在当前数据中，这一链条在OVAL上表现得最为清晰，其糖链状态与乳突层组织、Ca²⁺相关可及性和局部出壳抗性沿同一比较轴线变化。", False, False)], [4, 11, 12, 16]),
        ([ ("因此，引言在这里导向结果部分时，也遵循与全文相同的因果顺序：破壳齿功能相同，关注蛋壳，进入乳突层，追到基质蛋白和糖基化，再进入结构功能推导与有限元验证。", False, False)], [4, 11, 12, 16, 42]),
])

para("结果", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT, heading=True)

head("保守的破壳齿功能将比较焦点转向蛋壳")

p_ss1_cn = smixed([
    ([('尽管三种目标鸟类的喙尖几何不同，但破壳齿本身在三物种中都保持为定位相近的背侧喙尖结构，并把胚胎施加的力导向同一种由壳内侧发起的局部破壳事件（图1B）。也就是说，真正承担出壳功能的工具在三物种中是保守的。', False, False)], [16, 17, 22, 38, 82, 86]),
    ([('既然破壳齿本身没有提供一个能够解释有序表型的物种特异性差异，我们就把比较焦点转向蛋壳，并进一步基于AVONET收录的10,993个鸟类物种生态记录，把三种模型放回比较空间中（图1A）。', False, False)], [15, 16, 22, 23, 24, 25, 41]),
    ([('在这一比较空间中，', False, False),
        ('Gallus gallus', False, True),
        ('、', False, False),
        ('Anas platyrhynchos', False, True),
        ('和', False, False),
        ('Columba livia', False, True),
        ('分别位于陆生早成型、强水域依赖早成型和陆生晚成型三个代表位置，因此被选作后续比较对象。', False, False)], [15, 22, 23, 24, 25, 41]),
    ([('在这一对比集合中，后续要回答的问题就变得非常直接：一旦出壳工具被视为保守，蛋壳究竟是从哪一层开始把三物种区分开来。', False, False)], []),
])

head("乳突层给出第一层结构差异")

mixed([
    ("当比较被放到这一出壳背景下阅读时，最先把三物种拉开的蛋壳层级就是乳突层形态（图1C）。在", False, False),
    ("G. gallus", False, True),
    ("中，乳突轮廓整体更平滑，表现为圆钝突起。在", False, False),
    ("A. platyrhynchos", False, True),
    ("中，乳突表面可见更多棱脊和转角。", False, False),
    ("C. livia", False, True),
    ("则以独立、尖锐的三角锥样乳突为主。三维表面重建与横截面观察一致，说明这三种蛋壳并非共享同一内表面模板，而是对应不同的乳突几何组织方式。", False, False),
])

p_s0b_cn = mixed([
    ("定量分析进一步显示，三物种在两个相关但并不完全相同的指标上被区分开来（图1D）。乳突 knobs 密度在", False, False),
    ("G. gallus", False, True),
    ("中最高（171.36 ± 5.63 个/mm²），显著高于", False, False),
    ("A. platyrhynchos", False, True),
    ("（155.22 ± 8.63 个/mm²）和", False, False),
    ("C. livia", False, True),
    ("（158.27 ± 11.39 个/mm²），后两者彼此接近。相比之下，晶体单元占比在", False, False),
    ("C. livia", False, True),
    ("中最高（0.5321 ± 0.0389），", False, False),
    ("A. platyrhynchos", False, True),
    ("居中（0.4413 ± 0.0249），", False, False),
    ("G. gallus", False, True),
    ("最低（0.3975 ± 0.0127）。这些结果说明，鸡形成了最致密的乳突成核场，鸽由单个乳突 knobs 启动并向外扩展的晶体单元在整个蛋壳中占比最高，而鸭在晶体单元占比上居中、在密度上则与鸽更为接近。由于乳突层是蛋壳力学最早建立的结构层，而乳突层又受蛋壳基质蛋白调控，接下来的问题自然变成：这种有序形态差异究竟对应蛋壳基质工具箱的整体更替，还是共享系统内部的差异化部署。", False, False),
])
cite(p_s0b_cn, [1, 2, 28, 30, 36, 38])
cite(p_s0b_cn, [53, 54, 57])

head("共享基质蛋白工具箱把问题收束到糖基化")

p_sprot_bg_cn = spara([
    ("正交组分析显示，三物种蛋壳基质蛋白组中仍存在一个大的共享核心，同时叠加了两两共享和谱系限制性成分（图S3）。这一格局说明，有序的蛋壳表型并不是由蛋壳基质蛋白工具箱的整体替换驱动的。", [11, 20, 52, 53, 54]),
    ("从整体格局看，这一层蛋壳基质蛋白组仍较好保留了系统发育所界定的比较背景，因此真正需要解释的重点从“有哪些蛋白”转向“共享蛋白以何种状态发挥作用”。", []),
])

p_sprot_go_cn = spara([
    ("GO富集与基因家族周转进一步表明，三条谱系在免疫与防御相关背景上确有稳定分化（图S5和S6），但这些背景差异本身并不能解释乳突层的有序结构表型。", [3, 5, 14, 15, 24, 25, 26, 29, 52]),
])

p_sprot_focus_cn = spara([
    ("与此同时，鸡特有集合显著富集于蛋白N-连接糖基化（BP；图S5），提示三物种之间最值得继续追踪的差异，不只是蛋白组背景，还包括共享蛋壳基质蛋白的修饰状态。", []),
    ("既然糖基化可以改变同一种基质蛋白的功能，那么分析重点就应当从广义蛋白组背景收束到跨物种比较糖蛋白组学。", [8, 18, 19, 21]),
])

head("OVAL糖基化提供最清晰的共享分子信号")

p_s2a_cn = mixed([
    ("在确认这种有序蛋壳表型并非来自蛋壳基质工具箱的整体替换后，我们接着追问：哪些共享糖蛋白差异最紧密地追踪了这一表型。完整糖肽分析首次在这一比较框架下直接观测到鸟类蛋壳基质蛋白的具体糖型。图2显示，三物种糖蛋白组同时包含一个共享核心、两两共享区以及谱系限制性的外围节点。高甘露糖型和复合岩藻糖型构成较广泛的背景，而更延伸、尤其更唾液酸化的糖链更多出现在外围差异节点上。也就是说，这一层的比较很快把我们从广泛糖蛋白差异收束到一小组更适合继续做同源和结构分析的共享候选蛋白。", False, False),
])

p_s2b_cn = mixed([
    ("为了进一步判断这些糖链差异是否对应可比较的生物学功能，而不是宽泛的谱系替换，我们又对关键蛋白采用了更严格的BlastP同源筛选（图3A）。以", False, False),
    ("G. gallus", False, True),
    ("为参考序列，非参考物种候选同源物只有在E值 < 1 × 10⁻⁵，且满足最终序列可比性阈值时才被保留，从而把后续比较限制在高可信直系同源物范围内。在这一步筛选后，OC17只在鸡中检测到糖基化，而OC116、TRFE和OVAL则在三物种中均保留糖基化信号，因此构成了真正可比较的共享锚点。其中，OVAL呈现出最清晰的物种有序糖链重排，因此成为后续结构分析的优先目标。", False, False),
])
cite(p_s2b_cn, [6, 7, 8, 9, 10, 19, 21, 29])

p_s2c_cn = spara([
    ("将蛋白丰度和糖基化丰度放到同一坐标系中联合分析后，图3B-D进一步显示了为什么 OVAL 比 OC116 或 TRFE 更适合作为后续重点目标。在全体蛋白层面，鸡的蛋白丰度与糖链丰度相关性较弱，而鸭和鸽则更强，说明三物种不仅糖链类型不同，糖基化与蛋白输出的关系也不同。", []),
    ("更关键的是，OVAL在三物种中都保持高丰度，但它的糖链输出却明显分化，不能被蛋白总丰度简单解释。两两比较和完整糖肽鉴定进一步表明，OVAL呈现出最连贯的跨物种糖型排序：鸡以紧凑高甘露糖型为主，鸭转向中性复合/杂合型，鸽进一步转向更延伸的唾液酸化复合/杂合型。由此，图3将OVAL识别为那个最稳定地从总体丰度背景中解耦出来、并且仍沿表型排序变化的共享分子。", [1, 4, 6, 7, 8, 18, 47, 48]),
])

p_s2d_cn = spara([
    ("由于这些OVAL糖链类别在空间体积和电荷分布上差异显著，这一结果进一步提示，真正值得继续检验的分子变量更可能是OVAL表面可及性，而不是OVAL丰度本身。", [1, 4, 6, 7, 8, 18, 47, 48]),
    ("换句话说，下一步需要直接回答的，不是“哪个蛋白更多”，而是“同一个共享蛋白在不同糖链形式下，其化学表面被如何改变”。", [1, 4, 6, 7, 8, 18, 42, 47, 48]),
])

head("Re-Glyco将OVAL糖链状态连接到表面可及性")

p_s3a_cn = spara([
    ("OVAL随后被作为最强共享候选，用于检验其糖链类别如何改变生物物理可及性。既往体外研究已经表明，OVAL在矿化条件下能够结合Ca²⁺、发生部分解折叠并参与早期矿化相关组装，因此其糖链状态构成了一个具有生物学合理性的控制层。Re-Glyco与APBS分析显示，糖基化会在物种内改变OVAL的性质，而去糖基化后的蛋白骨架在物种间则更为接近。", [6, 7, 11, 12, 18, 42, 43]),
    ("一旦去除糖链，大部分跨物种分离便明显收敛，说明有序分化主要由糖基化而不是蛋白骨架本身引入。", [11, 12, 42, 43]),
    ("进一步的糖链几何分析表明，鸽的糖链占据最大的构象空间并产生最强的表面遮蔽，鸡的糖链最紧凑且遮蔽最弱，鸭居中。相应地，Ca²⁺相关可及性从鸡到鸭到鸽逐步下降。也就是说，不同糖型不仅仅是化学标签，它们确实改变了同一个共享基质蛋白所呈现给矿化环境的表面状态。", [11, 12, 42, 43, 44, 45, 46, 49, 50, 51]),
    ("这些结果并不直接证明糖链决定矿化，但它们清楚说明：同一个共享蛋白的不同糖链形式，可以通过改变表面可及性而提供一种结构上可解释的功能差异。", [11, 12, 42, 43, 49, 50, 51]),
])

head("有限元分析在局部出壳抗性中恢复同一排序")

p_s4a_cn = mixed([
    ("结果开头所界定的共同破壳齿界面，随后被进一步转化为有限元检验中的显式加载设计。图5A给出了与出壳相关的加载背景，而图5B-D则把三种鸟类喙部俯视图与对应的micro-CT有限元建模并列展示。这里我们关注的并不是广义整壳强度，而是乳突接触界面的局部抗性是否仍与前文恢复出的分子和结构排序保持一致。也就是说，这里的有限元分析承担的是一个跨尺度检验：前文由基质蛋白糖链状态、OVAL表面可及性和乳突组织所推得的排序，是否仍能在真实出壳力学界面上被检测出来。"
     "以模拟卵齿（角质托）的锥形几何压头，对圆形蛋壳碎片"
     "（模型直径D = 2.0 mm）施加9个参数化横向偏移位置的冲击"
     "（3×3网格；间距0.5 mm），每物种获得n = 9条独立接触剪切应力时间曲线。"
    "为了尽可能剔除采样模型尺寸、整体几何以及尤其是蛋壳厚度差异对结果的影响，我们同时记录原始峰值接触力F_max和峰值接触剪切应力τ_max。本文将τ_max视为乳突接触界面局部出壳抗性的直接指标。为此，我们从有限元单元输出中"
     "直接提取各偏移位置的峰值接触剪切应力τ_max，"
     "然后计算9个位置的物种均值 ± s.d."
    "（图S8A-F；壳厚：", False, False),
    ("G. gallus", False, True),
    (" 0.29 mm、", False, False),
    ("A. platyrhynchos", False, True),
    (" 0.35 mm、", False, False),
    ("C. livia", False, True),
    (" 0.19 mm）。", False, False),
])

cite(p_s4a_cn, [16, 17, 34, 35, 37, 38])

doc.add_page_break()
add_centered_figure("Fig5.jpg", width_cm=13.8, before=0, after=20)
add_main_figure_legend(
    "图5.",
    "由破壳齿几何约束的出壳相关加载设计与物种特异性有限元建模框架。",
    [
        ("(A) 胚胎出壳过程中卵齿由壳内侧局部顶压蛋壳的示意图。(B至D) ", False, False),
        ("Gallus gallus", False, True),
        ("、", False, False),
        ("Anas platyrhynchos", False, True),
        (" 和 ", False, False),
        ("Columba livia", False, True),
        (" 的物种特异性喙部俯视图及其对应的micro-CT有限元模型。在每个物种面板中，左侧为喙部俯视图，虚线框标示破壳齿位置，右侧为蛋壳碎片网格、相应锥形压头以及接触时的代表性有限元模型输出。这些面板共同定义了与出壳相关的加载背景，并说明模拟直接建立在实测重建壳体几何而非理想化壳体之上。", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

mixed([
    ("在加载框架明确之后，对9个偏移位置的F_max进行单因素方差分析（ANOVA），支持一个显著的三级层次关系（p = 1.639 × 10⁻¹³）：", False, False),
    ("G. gallus", False, True),
    (" 1.117 ± 0.110 N > ", False, False),
    ("A. platyrhynchos", False, True),
    (" 0.898 ± 0.090 N > ", False, False),
    ("C. livia", False, True),
    (" 0.485 ± 0.039 N，且所有两两差异均显著（图6A）。值得注意的是，τ_max则收束为两级格局（p = 6.644 × 10⁻¹⁰）：", False, False),
    ("G. gallus", False, True),
    (" τ_max = 551.6 ± 108.8 MPa显著高于", False, False),
    ("A. platyrhynchos", False, True),
    (" 404.0 ± 39.6 MPa和", False, False),
    ("C. livia", False, True),
    (" 393.0 ± 35.2 MPa，而后两者之间无统计学差异（图6B）。", False, False),
])

mixed([
    ("F_max与τ_max排序的差异表明：鸭蛋壳所需较高原始接触力"
     "主要归因于其较大壳厚（0.35 mm vs. 鸽子的0.19 mm），"
     "而非更优越的单位面积材料级抵抗力。"
     "相反，", False, False),
    ("G. gallus", False, True),
    ("相对于另外两个物种τ_max升高36–40%，表明其局部出壳抗性更高，且不依赖壳厚。"
     "τ_max的分组格局——", False, False),
    ("G. gallus", False, True),
    ("单独位于高值组，", False, False),
    ("A. platyrhynchos", False, True),
    ("和", False, False),
    ("C. livia", False, True),
    ("共同处于低值组——与显微CT乳突密度的DMRT分组完全对应（图1D）。",
     False, False),
])

mixed([
    ("若只用整壳层面的破裂力讨论三种蛋壳，鸭可能会因壳厚较大而显得在力学上优于鸡，"
    "即便它并不具备相同的高密度乳突状态。τ_max聚焦于micro-CT保留的乳突接触界面局部出壳抗性，"
     "因此消除了这种表观歧义，并显示高密度鸡状态在功能上仍然独立，而鸭与鸽则在较低抗性上收敛。换句话说，这组有限元结果不是一般性的力学补充，而是对前文结构解释的一次功能验证。", False, False),
])

para("讨论", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT, heading=True)

p_disc_mam1_cn = smixed([
    ([('这篇文章的主线其实非常直接。破壳齿在三种鸟之间保持了相同的出壳功能，因此真正需要解释的差异必须转移到蛋壳本身。蛋壳内部最先出现并且与力学最相关的差异发生在乳突层，而乳突层又受蛋壳基质蛋白调控；在这个前提下，共享基质蛋白上的糖基化状态就自然成为最值得继续追踪的分子层。', False, False),
            ('在这条逻辑链中，OVAL糖链状态最终成为最清楚的共享分子信号，并且可以一路被追踪到表面可及性和局部出壳抗性。', False, False)], [1, 2, 4, 15, 16, 17, 20, 21, 22, 23, 38, 39, 41, 42, 82, 86]),
        ([(' 乳突层之所以仍居于核心，是因为这是基质化学、早期晶体单元建立与后续力学表现首次在同一个结构层级中汇合的地方。', False, False)], [1, 2, 20, 28, 30, 36, 38, 53, 54]),
])

p_disc_mam2_cn = spara([
    ("蛋白组结果进一步收紧了这一主线。蛋壳基质蛋白工具箱整体上仍然共享，因此最需要解释的不是蛋白替换，而是共享蛋白以何种修饰状态发挥作用。", [11, 20, 21, 52, 53, 54]),
    ("在本文比较的各个分子层中，OVAL 的糖链状态最具有解释力，因为它既跨物种共享、又具有明确化学含义，并且落在一个高丰度、已被证明参与矿化的关键基质蛋白上。", [4, 6, 7, 18, 21, 42, 44, 45, 46]),
    ("也就是说，OVAL糖链状态并不是取代整个基质故事，而是给这个故事提供了一个最容易被化学和结构方式读出来的中心。", [20, 21, 42, 61, 63, 66, 74, 78, 80]),
])

p_disc_other_cn = para(
    "与此同时，非OVAL信号也并不是可以忽略的背景。OC116和TRFE仍然是有信息量的共享蛋白，而OC17则更像是鸡的谱系限制性程序。但在当前数据中，没有其他蛋白像OVAL一样，同时满足跨物种共享、糖链状态有序以及结构上可直接解释这三个条件。换句话说，我们并不是在说一个蛋白解释了整个蛋壳，而是在说OVAL提供了从基质修饰走向结构和功能的最清晰路径。",
    bold=False, size=11, before=0, after=120
)

cite(p_disc_other_cn, [10, 19, 21, 29, 42, 44, 45, 46, 66, 81])

p_disc_oval_cn = para(
    "Re-Glyco与APBS分析给出了这条链条中的结构桥梁。鸡的紧凑糖链使OVAL关键酸性表面保持相对暴露，而鸽更长、带更强负电性的糖链则同时从空间和静电两个层面削弱Ca²⁺接近；鸭再次位于两者之间。这个结果本身并不直接证明糖链决定矿化，但它清楚说明：同一个共享基质蛋白在不同糖型下，能够呈现出不同的化学表面状态。",
    bold=False, size=11, before=0, after=120
)

cite(p_disc_oval_cn, [4, 11, 12, 42, 44, 45, 46, 49, 50, 51, 52, 55, 65])

p_disc_axis_cn = spara([
    ("乳突层成矿方式因此仍是解释中最核心的结构层级。", [1, 2, 20, 28, 38]),
    ("一旦早期方解石晶体单元建立完成，后续壳层就会继承这一最初成矿窗口所确定的空间逻辑。", [1, 2, 28, 30]),
    ("高密度乳突场改变的不只是显微形态本身，它还会重排基质保留、矿物连续性以及局部应力再分配。", [1, 2, 30, 36, 38]),
], before=0, after=120)

p_disc_regulator_cn = spara([
    ("鸭保留了一个三状态比较，而不是简单的“早成对晚成”二分法。", [4, 15, 23, 27, 39, 41]),
    ("如果发育方式本身就足以决定蛋壳化学，鸭理应在分子和力学层面始终与鸡聚类。", [15, 23, 27]),
    ("事实并非如此：鸭在分子层面处于中间位置，在τ_max上则与鸽收敛。", [4, 12, 16, 17, 39, 41]),
    ("这说明发育程序定义了问题背景，但共享基质蛋白上的糖链状态差异帮助规定了最终的生化解决方案。", [4, 12, 15, 23, 27, 39, 41]),
], before=0, after=120)

p_disc_discriminate_cn = spara([
    ("若干可能的背景变量，可以与那些能够反复恢复有序表型的特征区分开来。", []),
    ("壳厚、体型以及广义繁殖生态都可能提供背景差异，谱系历史也无疑重要。", [2, 14, 16, 17, 24, 25]),
    ("但仅靠厚度无法恢复τ_max的排序，而把所有分子结果都归结为弥散谱系分化，也解释不了为什么同样的有序变化会在糖链类别、表面可及性、乳突组织和局部力学中反复出现。", [4, 16, 17, 20, 21, 38, 42]),
    ("在这组三物种数据里，生态和系统发育给出了比较框架，而基质蛋白糖链状态则提供了最稳定、也最容易被化学方式读出的近端分子层。", [1, 2, 4, 20, 21, 38, 42, 57, 70]),
], before=0, after=120)

p_disc_mech_cn = spara([
    ("力学分析则把同一排序推进到个体层面的功能背景中。", [16, 17, 38]),
    ("最关键的是，真正追踪乳突层级差异的是τ_max，而不是原始破裂力。", [16, 17, 34, 35, 37, 38]),
    ("这一区别很重要，因为绝对破裂载荷仍会受到壳厚和整体几何形态影响，而τ_max更直接地给出乳突界面上的局部出壳抗性读数。", [16, 17, 34, 35, 37, 38]),
    ("鸭和鸽虽然乳突总体几何形态不同，τ_max却收敛于相近水平，这说明一旦不再处于鸡那种高密度成矿状态，仅靠更下游的形态差异并不能恢复同等级别的乳突界面抗性。换言之，前文恢复出的排序并不只停留在分子和结构描述层面，而是在功能读数中仍然可见。", [1, 2, 16, 17, 38]),
])

p_disc_evo_cn = para(
    "力学结果也与一种可能的进化补偿逻辑相一致。鸭并不具备鸡那种高可及性的糖链状态，但它仍通过更大的壳厚保留了较高的整体受力阈值；当糖基化相关的成矿状态偏离鸡所代表的极端时，壳厚可能在一定程度上缓冲局部材料抗性的下降。放到更广义的鸟类演化背景中，这一模式提出了一个值得后续系统取样去检验的问题：糖基化策略的变化，是否曾伴随鸟类从早成向晚成谱系转变，而壳厚则在某些支系中成为限制壳体强度骤降的一条替代路径。当前三物种数据并不能直接检验这一宏观演化设想，但已经界定出一条可进一步检验的轴线：表型—蛋白—修饰—力学。",
    bold=False, size=11, before=0, after=120
)

cite(p_disc_evo_cn, [3, 15, 16, 17, 37, 38, 39, 41, 57])

p_disc_function_cn = para(
    "如果从进化角度回看，这些结果提示糖链类别可能是连接宏观选择背景与具体成矿策略的一个中介层。蛋壳分化并不能被收缩为单一变量，而是更广泛的生态和发育差异在一个化学上可界定的层级开始变得结构上可读。一个可调的翻译后状态，附着在高丰度基质蛋白之上，为蛋壳系统在保留保守蛋白工具箱的同时发生分化提供了一种可能路径。由此，糖蛋白状态可以把基质化学、微结构组织和生物力学后果放到同一比较框架中。类似原则也可能适用于鸟类蛋壳之外的矿化体系，因为许多矿化系统同样依赖高丰度基质蛋白，而其翻译后状态可以在不整体替换蛋白库的情况下发生改变。通过澄清化学特异性表面状态可能如何偏置矿物生长，这一视角也可能帮助理解人类骨骼发育、再生以及相关生物矿化模型的解释方式。当前数据支持一种跨尺度联系：生态差异、分子表面状态、结构组织和局部力学读数彼此相连。",
    bold=False, size=11, before=0, after=120
)

cite(p_disc_function_cn, [4, 6, 7, 18, 20, 21, 42, 49, 50, 52, 62, 67, 68, 69, 71, 72, 73, 75, 77, 79])

p_disc_selection_cn = para(
    "OVAL糖链状态界定出一个具有明确化学含义的比较层级，这一层级既可以被映射到结构，也可以被放到功能背景下检验。在富组学的生物矿化研究中，谱系差异往往比真正最稳定组织表型的分子特征更容易被识别；在这里，承担这一比较作用的是糖链状态，而不是广义蛋白组周转。在其他矿化体系中，类似角色也可能由硫酸化、磷酸化、蛋白水解加工或丰富基质蛋白上的辅因子结合状态承担，尤其是在同一组高丰度基质成分被重复用于不同结构背景时。",
    bold=False, size=11, before=0, after=120
)

cite(p_disc_selection_cn, [20, 21, 42, 49, 50, 52, 58, 59, 60, 65, 66, 74])

p_disc_future_cn = para(
    "当然，当前数据仍有若干必须明确保留的边界。我们的结构分析采用的是各位点优势糖型，而非完整体内糖型分布，这并不只是取舍问题，也与当前糖型结构库本身仍不完整有关：有些实验上真实存在、但结构信息不足的糖型，尚无法被稳定纳入可比较的再糖基化系综中。基于这一限制，我们只能优先保留当前三物种比较中最稳定、最可支持的优势糖型；此外，有限元模型把不同物种蛋壳近似为平均尺度上的机械均一材料，APBS所需的子宫液离子环境也仍未被充分约束。这些限制也界定了下一步最关键的检验：定义糖型的矿化实验、结合子宫液化学测量的OVAL糖基化定向操控、位点分辨的力学验证，以及更广泛谱系中的扩展采样，以判断这里识别出的三物种轴线究竟是可重复模式，还是更大设计空间中的一个分支。这些工作将进一步明确OVAL糖链状态究竟直接参与矿化，还是主要作为比较中的分子指示层，并检验同一轴线是否延伸到当前生态和发育对比之外。",
    bold=False, size=11, before=0, after=120
)

cite(p_disc_future_cn, [4, 11, 12, 20, 21, 42, 49, 50, 51, 52, 57, 70, 76])

p_disc_close_cn = para(
    "综合这些结果可以看到，一旦比较被锚定到共享的破壳齿出壳界面上，基质蛋白糖链状态就会显现为连接比较分子分化、蛋壳微结构与局部力学结局的一个化学特异性层级。在鸡、鸭和鸽之间，乳突层组织、OVAL糖链类别、计算得到的Ca²⁺可及性以及模拟得到的局部出壳抗性共同构成了一个连贯但不对称的格局，而不是四个指标上完全一致的整齐排序：鸡位于高可及、高抗性端，鸭保留分子层面的中间状态，鸽则代表更强遮蔽的端点，而力学读数又把鸭与鸽归入较低抗性一侧。其他基质特征很可能也参与其中，但高丰度基质蛋白的表面状态仍是当前最容易被进一步实验检验的解释层之一。这一框架把基质蛋白糖基化放入鸟类蛋壳形成、局部功能和谱系分化的同一比较视角中，也为更广义的生物矿化问题提供了一个新的理解视角：化学特异性的界面状态本身，可能塑造离子可及性、微结构组织及力学结局。",
    bold=False, size=11, before=0, after=120
)

cite(p_disc_close_cn, [6, 7, 18, 20, 21, 42, 44, 45, 46, 49, 50, 72, 78, 80])

p_disc_limits_cn = p_disc_close_cn

# ════════════════════════════════════════════════════════════════════════════
# 方法
# ════════════════════════════════════════════════════════════════════════════
para("材料与方法", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

head("生物材料")

p_m_bio = mixed([
    ("三个禽类物种各采集六枚新鲜产出蛋，均于产出后24\u00a0h内收集。", False, False),
    ("Gallus gallus", False, True),
    ("（家鸡）蛋壳来自中国农业大学家禽资源保护场（北京）；", False, False),
    ("Columba livia", False, True),
    ("（鸽子）蛋由中国农业大学动物医学院常于教授提供；", False, False),
    ("Anas platyrhynchos", False, True),
    ("（绿头鸭）蛋由北京金星鸭业提供。所有蛋壳样品于处理前在4\u00b0C下保存。", False, False),
])

head("蛋壳基质蛋白提取")

para(
    "采用EDTA脱矿化方案提取蛋壳乳突层（EML）基质蛋白。"
    "鸡蛋用去离子水漂洗后置入无菌密封袋。"
    "对G.\u00a0gallus和A.\u00a0platyrhynchos，首先通过15\u00a0mL 5% EDTA"
    "（0.13\u00a0mol/L，pH\u00a07.6，含10\u00a0mmol/L 2-巯基乙醇）在20\u00b0C处理30\u00a0min，"
    "并轻柔揉捏蛋壳以去除蛋壳外表皮层（ECL），之后用去离子水漂洗蛋壳。"
    "三个物种的EML蛋白均在相同的EDTA\u20132-巯基乙醇条件下提取，"
    "但处理时间延长至12\u00a0h（20\u00b0C）。"
    "所得悬液以1,000\u00a0\u00d7\u00a0g离心15\u00a0min，沉淀重悬后再次离心，"
    "合并上清液于\u221280\u00b0C保存至分析。"
)

head("显微CT成像与乳突形态计量")

p_m_ct_cn = para(
    "每物种取两块赤道区蛋壳碎片（各约4\u20135\u00a0mm\u00b2），"
    "以Phoenix V|tome|x\u00a0M微焦点CT系统（GE Sensing and Inspection "
    "Technologies GmbH，Wunstorf，德国）进行扫描，"
    "扫描参数固定为85\u00a0kV、160\u00a0\u03bcA，无滤光片。"
    "三维重建在3D\u00a0Slicer中以阈值分割法完成，"
    "采用5\u00a0\u00d7\u00a05\u00a0\u00d7\u00a05中值滤波降噪，"
    "随后进行最大島保留和9\u00a0\u00d7\u00a09\u00a0\u00d7\u00a09填孔处理。"
    "在同一感兴趣区域内，我们进一步基于labelmap计算三项形态参数。"
    "首先，对分割后的蛋壳模型进行单拷贝复制，并以Fill holes生成封闭实体；"
    "再将该实体与原始蛋壳模型做差，获得乳突间隙层，其中该层平面内出现的封闭孔洞定义为mammillary knobs。"
    "对应区域的乳突密度按乳突数除以区域面积计算。"
    "随后，以labelmap统计同一区域的蛋壳总体积，并以总蛋壳体积除以乳突数定义平均柱状单元体积；"
    "单元体积比则按平均柱状单元体积除以该区域蛋壳总体积计算。"
    "鉴于正常鸟类蛋壳中由乳突启动的柱状晶体单元在平面内通常呈重复、近似均一的分布，"
    "上述指标可作为各物种整体蛋壳组织的局部平均代表值（每物种n\u202f=\u202f2块碎片）。"
)
cite(p_m_ct_cn, [1, 38])

head("蛋壳基质蛋白质组学")

para(
    "每物种每批次以两枚蛋混样，每物种共制备三个独立重复（n\u202f=\u202f3）。"
    "蛋白质提取采用裂解缓冲液（1% SDS、1%蛋白酶抑制剂混合物）重悬，"
    "冰上超声裂解后以12,000\u00a0\u00d7\u00a0g、4\u00b0C离心10\u00a0min澄清；"
    "蛋白浓度用BCA试剂盒检测。"
    "蛋白质经预冷丙酮沉淀（5倍体积，\u221220\u00b0C，2\u00a0h）、"
    "丙酮漂洗两次后重溶于200\u00a0mmol/L TEAB。"
    "二硫键还原以5\u00a0mmol/L DTT（56\u00b0C，30\u00a0min），"
    "烷基化以11\u00a0mmol/L碘乙酰胺（室温，15\u00a0min，避光）完成。"
    "蛋白质以测序级胰蛋白酶（酶:底物质量比1:50）过夜消化，"
    "肽段经Strata\u00a0X SPE柱脱盐。"
)

para(
    "脱盐肽段溶于0.1%甲酸，上样至自制15\u00a0cm\u00a0\u00d7\u00a0100\u00a0\u03bcm i.d.反相C18色谱柱，"
    "与Vanquish\u00a0Neo UPLC系统（赛默飞）联用，"
    "流速400\u00a0nl/min、22.6\u00a0min梯度（4\u201399% B；"
    "B相：80%乙腈/0.1%甲酸）分离。"
    "洗脱肽段经Orbitrap\u00a0Astral质谱仪（赛默飞）纳喷离子源（1,900\u00a0V）分析。"
    "全扫描分辨率240,000，扫描范围380\u2013980\u00a0m/z；"
    "碎片扫描分辨率80,000，HCD碎裂（NCE\u202f=\u202f25%），"
    "固定首质量150\u00a0m/z，AGC目标500%，最大注入时间3\u00a0ms。"
    "DIA数据以DIA-NN v1.8检索，比对物种特异性参考蛋白质组"
    "（G.\u00a0gallus：43,711条目；A.\u00a0platyrhynchos：91,801条目；"
    "C.\u00a0livia：17,309条目；均下载于2024年8月）与反向诱饵数据库。"
    "酶切特异性设为Trypsin/P，最多1个漏切；"
    "N端Met去除和Cys脲甲基化为固定修饰。"
    "蛋白和肽段FDR均控制在1%以内。"
)

head("完整糖肽质谱")

para(
    "胰酶消化物经亲水作用色谱（HILIC）富集N-糖肽。"
    "肽段重溶于上样缓冲液（80% ACN、5% TFA），上样至HILIC柱，"
    "以上样缓冲液洗涤三次后，"
    "以0.1% TFA/50\u00a0mmol/L碳酸氢铵/50% ACN洗脱两次；"
    "洗脱液经C18\u00a0Zip-Tips脱盐并真空干燥。"
    "糖肽组分在同一纳升液相平台以34\u00a0min梯度（4\u201399% B，400\u00a0nl/min）分离。"
    "全扫描分辨率240,000，范围700\u20132,000\u00a0m/z；"
    "碎片扫描分辨率80,000，固定首质量120\u00a0m/z，"
    "循环时间0.6\u00a0s，AGC目标100%，强度阈值25,000 ions/s，"
    "最大注入时间5\u00a0ms。"
    "DDA原始数据以MSFragger\u00a0v3.4检索，"
    "酶切设为严格胰蛋白酶（最多2个漏切），"
    "肽段长度7\u201350个残基，固定Cys脲甲基化，"
    "可变N端乙酰化和Met氧化，糖基化质量偏移采用默认列表。"
    "蛋白、肽段和PSM的FDR均控制在1%以内。"
    "N-糖链结构类别按牛津命名法分为六类："
    "高甘露糖型、少甘露糖/截短型、中性复合/杂合型、"
    "岩藻糖化复合/杂合型、唾液酸化复合/杂合型和其他。"
    "每蛋白每物种的结构类别相对丰度以糖基化位点信号强度之比计算。"
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
cite(p_m_ortho_cn, [3, 5, 14, 24, 25])

head("跨物种糖蛋白直系同源物鉴定")

para(
    "以G.\u00a0gallus参考序列对非参考物种蛋白质组进行BlastP比对"
    "（E值阈值1\u00a0\u00d7\u00a010\u207b\u2075；最多500个目标序列；输出250个比对结果），"
    "鉴定四种靶标蛋壳糖蛋白（OVAL、OC116、TRFE、OC17）的跨物种高可信直系同源物。"
    "候选命中保留标准为平均最大序列同一性\u2265\u00a00.80；"
    "当Query与Subject非重叠HSP数量不等时，放宽至\u2265\u00a00.50。"
    "用于后续结构和定量分析的最终UniProt直系同源物编号详见补充表1。"
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
    "匹配成功的糖链以GlyTouCan登录号标识。"
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
    "以BioPython对各模型原子坐标计算系综几何描述符："
    "糖链全部重原子的回旋半径（Rg）、糖链端到端距离，"
    "以及糖链任意重原子与蛋白质C\u03b1原子间的最小距离（最小C\u03b1接触距离）。"
    "对各描述符进行逐结构汇总统计（均值\u00b1标准差）"
    "及物种两两比较（Mann\u2013Whitney\u00a0U检验，双侧）。"
)
cite(p_m_reglyco_cn, [11, 49, 50, 51])
cite(p_m_reglyco_cn, [56, 58, 59, 60, 65])

head("静电势计算")

p_m_apbs_cn = para(
    "采用APBS\u00a0v3.4.1对每个Re-Glyco系综模型及其匹配的去糖基化（apo）"
    "参考结构计算静电表面势。"
    "原子分电荷和半径通过PDB2PQR赋予（CHARMM36力场，PROPKA pH\u00a07.4质子化）；"
    "糖链重原子分电荷采用GLYCAM06参数集（Kirschner等，2008，"
    "J.\u00a0Comput.\u00a0Chem. 29:622）。"
    "溶剂可及表面积由Shrake\u2013Rupley算法计算；"
    "相对ASA\u00a0\u2265\u00a00.25的残基定义为表面残基。"
    "Ca\u00b2\u207a结合静电热点定义为APBS势值<\u00a0\u22125\u00a0kT/e的表面Asp/Glu残基。"
    "报告的系综水平指标包括热点数（N_hot）、每热点平均SASA、"
    "热点占全部表面Asp/Glu比例及表面静电势中位数。"
)
cite(p_m_apbs_cn, [12, 42, 43])

head("有限元分析")

p_m_fea_cn = mixed([
    ("用于后续有限元分析的感兴趣区域限定为半径1\u00a0mm的圆柱区域。"
     "显微CT获得的蛋壳曲面模型先导出为STL文件，并在Geomagic\u00a0Wrap中完成有限元前处理："
     "依次进行去噪（强度2）、三角形简化（约30万面片）、"
     "网格重建（0.01\u00a0mm分辨率）、缺陷迭代修复至零缺陷，以及有机参数曲面拟合（最小公差）。"
     "随后将所得蛋壳表面模型导入LS-DYNA（Ansys）进行显式动力学有限元分析"
     "（单位制：mm/kg/N/s）。"
     "蛋壳赋予弹塑性材料属性"
     "（弹性模量E\u202f=\u202f3.0\u00a0\u00d7\u00a010\u00b9\u2070\u00a0Pa；"
     "屈服强度\u03c3y\u202f=\u202f1.5\u00a0\u00d7\u00a010\u2077\u00a0Pa；切线模量0；"
     "最大等效塑性应变失效值0.05）。"
    "模拟破壳齿的冲击体为圆台"
     "（底面半径0.1\u00a0mm，顶面半径0.5\u00a0mm，高0.5\u00a0mm），"
     "赋予IRON-ARMCO显式材料属性。"
     "冲击体与蛋壳间采用摩擦接触（\u03bc\u202f=\u202f0.2）。"
     "蛋壳网格单元尺寸分别为0.05\u00a0mm（", False, False),
    ("G. gallus", False, True),
    ("）、0.05\u00a0mm（", False, False),
    ("A. platyrhynchos", False, True),
    ("）和0.03\u00a0mm（", False, False),
    ("C. livia", False, True),
    ("），确保蛋壳截面网格层数≥6；冲击体网格为0.1\u00a0mm。"
     "冲击体初始速度设为50,000\u00a0mm/s，"
     "蛋壳圆盘碎片（直径2.0\u00a0mm）四侧面施加对称固定支撑。"
     "仿真时长1.0\u00a0\u00d7\u00a010\u207b\u2074\u00a0s（时步安全系数0.7；"
     "自动质量缩放；最小时步1\u00a0\u00d7\u00a010\u207b\u2078\u00a0s；双精度；100个等间距输出点）。"
     "合接触力（RCFORC）以1.0\u00a0\u00d7\u00a010\u207b\u2076\u00a0s间隔记录。"
     "冲击体在每物种蛋壳上的3\u00a0\u00d7\u00a03网格偏移位置（间距0.5\u00a0mm）共9个接触点"
     "分别提取峰值接触力（F_max）和峰值接触切应力（\u03c4_max）。", False, False),
])
cite(p_m_fea_cn, [16, 17, 38])

head("统计分析")

para(
    "所有数值以均值\u00b1标准差（mean\u00b1s.d.）表示，所有统计检验均为双侧，"
    "p\u00a0<\u00a00.05视为显著。"
    "乳突形态参数的物种间比较采用单因素方差分析（ANOVA）"
    "结合Duncan多重范围检验（DMRT；\u03b1\u202f=\u202f0.05）（每物种n\u202f=\u202f2块碎片）。"
    "糖链系综几何描述符（Rg、端到端距离、最小接触距离）"
    "及各系综热点SASA的物种间比较采用单因素ANOVA结合"
    "Duncan多重范围检验（DMRT；\u03b1\u202f=\u202f0.05）。"
    "C.\u00a0livia糖基化引起的N_hot减少以单样本t检验（t\u2081\u2083）"
    "与apo参考值比较；"
    "糖基化与apo结构间总Asp/Glu SASA差异及"
    "表面静电势中位数的偏移均以单样本t检验（对照apo参考值）评估。"
    "蛋白\u2013糖基化位点丰度耦合以log\u2082转换强度的Spearman秩相关定量。"
    "有限元仿真结果（F_max、\u03c4_max）以单因素ANOVA结合"
    "Duncan多重范围检验（DMRT；\u03b1\u202f=\u202f0.05）进行物种比较。"
    "所有统计分析在Python中以scipy.stats和statsmodels完成。"
)

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
