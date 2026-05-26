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

OUT = str(Path(__file__).with_name("manuscript260520_cn.docx"))
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
    "蛋壳基质蛋白糖链状态连接鸟类乳突层组织与局部出壳抗性",
    bold=True, size=14, before=0, after=160,
    align=WD_ALIGN_PARAGRAPH.LEFT
)

para(
    "短标题：基质蛋白糖链与出壳抗性",
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
    "鸟类依赖功能保守的破壳齿完成出壳，因此未解的力学差异更可能来自蛋壳而非破壳工具本身。"
    "我们比较鸡、鸭和鸽，检验第一层清晰分化是否出现在乳突层，以及共享基质蛋白上的糖链状态是否与这种分化一致。"
    "显微CT形态测量、蛋壳基质蛋白组学、完整糖肽质谱、Re-Glyco结构建模、电势分析和有限元模拟表明，乳突层组织首先分化，而蛋壳基质蛋白工具箱整体仍然共享。"
    "在共享蛋白中，OVAL表现出有序的糖链状态变化：鸡以高甘露糖型为主，鸭转向中性复合/杂合型，鸽进一步转向唾液酸化复合/杂合型。"
    "这一变化对应于从鸡到鸽逐步降低的Ca²⁺相关表面可及性，以及局部出壳抗性中同样的鸡对鸭/鸽分离格局。"
    "这些结果表明，OVAL糖链状态是连接鸡式蛋壳状态、乳突层组织和局部出壳力学的最有信息量分子层。",
    bold=False, size=10, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY
)

para(
    "导语：紧凑OVAL糖链与鸡式蛋壳状态及更高模拟局部出壳抗性相对应。",
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
    ("鸟类出壳面对的是一个局部化的力学问题：胚胎必须把力准确传递到一个很小的破壳位点。在鸟类中，这个位点由暂时存在的破壳齿定义，它从壳内侧顶压蛋壳；类似的辅助出壳结构也见于其他卵生羊膜动物。", [16, 82, 83, 84, 85, 86]),
    ("正因为破壳齿的功能总体保守，真正有生物学意义的出壳差异更可能位于蛋壳，而不是破壳工具本身。鸟类蛋壳则会随巢穴环境、气体交换和微生物暴露压力以及发育方式而变化，而不是呈现一种统一方案。", [15, 26, 39, 40, 41]),
    ("在这一背景下，乳突层尤为关键，因为它是蛋壳中最先对力学产生直接影响的层级，也是蛋壳基质调控下方解石开始生长的位置。后续壳层会继承这一早期成矿背景，因此乳突层组织正是局部分子差异最可能被放大为成熟蛋壳行为差异的位置。", [1, 4, 20, 28, 30, 34, 57]),
])

p_s1b_cn = spara([
    ("因此，真正的机制问题就变成：当破壳界面被固定后，究竟是哪一类调控乳突层组织的分子因素，能够解释不同物种之间恢复出的不同蛋壳状态？", [1, 2, 4, 16, 28]),
])

# §2 — 已知工作与局限
p_intro2 = spara([
    ("蛋壳基质蛋白之所以构成最直接的候选层，是因为它们调控乳突层成矿、晶体生长以及成熟蛋壳的结构组织，而 OC17、OC116、TRFE 和 OVAL 都是其中反复被讨论的代表性蛋白。", [1, 2, 4, 10, 19, 21, 29]),
    ("近期的蛋壳基质蛋白综述与实验研究反复回到一组部分重叠的关键蛋白，尤其是 OC17、OC116、ovotransferrin 相关蛋白、OVAL、ovomucoid 以及 ovocalyxin 家族成员，因为这些分子在不同研究中被足够稳定地重复回收，能够构成讨论蛋壳结构组织的共同锚点。", [1, 2, 4, 19, 21, 29]),
    ("也正因为这些蛋白在鸟类蛋壳研究中持续出现，它们构成了检验“共享成矿工具箱如何在不同壳体背景中被重复使用”的天然比较锚点。真正仍待回答的问题，并不是这些蛋白是否存在，而是它们如何被使用。", [1, 2, 4]),
    ("已有蛋壳糖蛋白组学研究表明，同一种蛋壳基质蛋白可处于不同的 N-糖基化状态，而既往以鸡为主的生化研究也已确认 OC116 中存在糖基化 Asn，并对 OVAL 相关糖链的组成给出了基础描述；平行开展的鸟类卵研究则在蛋清、卵索、卵黄膜及孵化阶段变化中记录了糖基化状态转变。", [7, 8, 18, 21, 47, 48]),
    ("这些工作当然是基础性的，但它们大多仍停留在单一物种、单一壳层区室或单纯位点目录的范围内。因此，前人已经证明了蛋壳糖基化确实存在且具有化学多样性，却还没有进一步说明，共享基质蛋白上的匹配糖型如何与跨物种蛋壳结构一起变化。", [8, 18, 21]),
    ("换句话说，领域内已经知道哪些蛋白会反复出现，也已经知道不少可检测的糖基化位点；真正还缺少的，是这些反复出现的共享蛋白在糖链状态层面如何被重新部署，并进一步对应到跨物种乳突层组织和出壳力学差异。", [1, 2, 18, 29, 66]),
    ("但鸟类蛋壳研究很少在跨物种框架中解析共享基质蛋白具体携带哪些 N-糖链形式。真正缺失的一层因此并不是基质蛋白是否重要，而是共享基质蛋白上的糖基化能否解释为什么相似的蛋白工具箱会产生不同的蛋壳结构。", [2, 4, 18]),
])

p_intro_sig_cn = spara([
    ("糖基化会影响蛋白稳定性、分子识别、表面暴露和构象状态，而其他系统中的研究也已表明，糖链可以作为动态遮蔽层，而不是被动附着的体积负担。", [42, 43, 61, 63, 72, 78]),
    ("Zeng Lingsen 等人的蛋壳 N-糖蛋白组工作进一步表明，同一个基质蛋白在 cuticle 与 mineralized layer 中可以对应不同的糖基化状态，这意味着糖链状态不仅是化学修饰，还可能把同一蛋白的生物学功能重新分配到不同壳层区室。", [18]),
    ("既往矿化相关工作也提示，OVAL 在早期成壳阶段可能进入 Ca²⁺ 响应的构象状态。因此，我们进一步检验跨物种糖链差异是否会重塑折叠 OVAL 的表面，并改变矿化起始时呈现给 Ca²⁺ 的可接近界面。", [4, 11, 29, 42, 43, 61, 63, 81]),
    ("而如果这种结构差异具有生物学意义，那么它也应当在出壳相关的力学终点上保留下来，即表现为破壳齿样加载下乳突界面的局部抗性差异。", [16, 37, 69]),
])

# §3 — 核心缺口
p_intro_gap_cn = spara([
    ("因此，我们把比较锚定在保守的破壳齿界面上，并检验共享基质蛋白上的糖链状态差异是否能够解释，同一套成壳工具箱为何会在矿化起始时呈现不同的 Ca²⁺ 可接近状态。放在这一框架下，真正缺少的并不是另一份蛋白清单，而是一座从糖链类别通向共享基质表面呈现方式的桥梁。", []),
    ("OVAL 提供了一个便于检验的案例，因为既往矿化相关工作已经提示其 Ca²⁺ 响应表面行为具有明确生物学意义，它在三物种中又都保持较高丰度，并且其优势糖型可以被从糖蛋白组学一路推进到结构建模。", [4, 18, 29, 42]),
])

# §4 — 本研究
p_intro4 = smixed([
    ([ ("在这里，我们比较了", False, False),
            ("Gallus gallus", False, True),
            ("、", False, False),
            ("Anas platyrhynchos", False, True),
            ("和", False, False),
            ("Columba livia", False, True),
                ("，分别作为陆生早成型、强水域关联早成型和陆生晚成型模型，从而在共同的出壳框架内跨越发育与生态两个交叉对比维度。", False, False)], [3, 22, 23]),
            ([ ("这一设计避免了比较坍缩为简单的系统发育配对，或单一的“早成对晚成”对照。", False, False)], []),
            ([ ("我们整合了显微CT形态测量以界定乳突层组织，比较蛋壳基质蛋白组学与完整糖肽质谱以解析共享基质蛋白及其糖链状态，Re-Glyco结构建模与静电分析以推断蛋白表面后果，以及有限元模拟以检验同一跨物种对比是否仍能在局部出壳抗性中被检测到。", False, False)], []),
            ([ ("因此，每一层证据都用于约束下一层，使分子解释始终与壳体结构相联系，而不是脱离材料背景。", False, False)], []),
            ([ ("在当前数据中，这条顺序化比较路径在OVAL上最为清晰，其糖链状态与乳突密度、Ca²⁺相关表面可及性和局部出壳抗性一致变化。", False, False)], [18]),
])

head("破壳齿功能保守，焦点转向蛋壳")

p_ss1_cn = smixed([
    ([('我们进一步基于AVONET收录的10,993个鸟类物种生态记录，把三种模型放回比较空间中（图1A）。', False, False)], [16, 22, 41]),
    ([('这一更宽的比较定位之所以必要，是因为与蛋最直接相关的两条轴线并不是简单二值分类：一条是巢穴环境，它与陆生到强水域依赖的梯度高度相关；另一条是雏鸟状态，它从更早成到更晚成连续分布。', False, False)], [15, 22, 23]),
    ([('在这一比较空间中，', False, False),
        ('Gallus gallus', False, True),
        ('、', False, False),
        ('Anas platyrhynchos', False, True),
        ('和', False, False),
        ('Columba livia', False, True),
        ('因此被选作后续比较对象，不是因为它们构成整齐类别，而是因为它们在这些连续生态—发育梯度上被有意拉开，从而尽量减少中间组合对比较解释的干扰。', False, False)], [3, 22, 23, 41]),
    ([('因此，这个对比被设计成既保留共同祖先背景，又把清晰的生活史差异纳入同一分析框架。', False, False)], []),
    ([('尽管三种目标鸟类的喙尖几何不同，但破壳齿本身在三物种中都保持为定位相近的背侧喙尖结构，并把胚胎施加的力导向同一种由壳内侧发起的局部破壳事件（图1B）。因此，真正承担出壳功能的工具在三物种中是保守的。', False, False)], [16, 37, 82, 86]),
    ([('在这一对比集合中，后续要回答的问题就变得非常直接：一旦出壳界面被固定，蛋壳究竟是从哪一层开始把三物种区分开来。', False, False)], []),
])

head("乳突层首先拉开蛋壳差异")

mixed([
    ("当比较被放到这一出壳背景下阅读时，最先把三物种拉开的蛋壳层级就是乳突层形态（图1C）。在", False, False),
    ("G. gallus", False, True),
    ("中，乳突轮廓整体更平滑，表现为钝圆形凸起。在", False, False),
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
    ("最低（0.3975 ± 0.0127）。定量上看，鸡表现出最致密的早期成矿格局，鸽把最大比例的壳体体积分配给由单个乳突knobs启动的晶体单元，而鸭在晶体单元占比上居中、在密度上则更接近鸽。这两个指标并没有收束成一条简单的单调轴线，但它们一致说明乳突层在更晚的壳体特征出现之前就已经发生了可测量的分化。由于乳突层是蛋壳力学最早建立的结构层，而乳突层又受蛋壳基质蛋白调控，接下来的问题自然变成：这种跨物种形态差异究竟对应蛋壳基质工具箱的整体更替，还是共享系统内部的不同使用方式。", False, False),
])
cite(p_s0b_cn, [1, 4, 28])

head("共享基质蛋白把解释收束到糖基化")

p_sprot_bg_cn = spara([
    ("直系同源分组分析显示，三物种蛋壳基质蛋白组由一个大的共享核心及较小的两两共享和谱系限制性补集构成（图S3）。在整体层面，蛋白组仍遵循广义亲缘框架（图S4），说明蛋壳差异并非来自基质工具箱的整体替换。", []),
])

p_sprot_go_cn = spara([
    ("GO富集和基因家族周转进一步提示了谱系特异的免疫与防御背景（图S5和S6），但这些信号更多描述的是比较背景，而不是与乳突层组织最直接对应的层级。这些带有谱系偏向的信息仍然是重要的演化背景，但它们本身并没有指出把共享基质体系与乳突层分化及后续出壳相关力学连接起来的最近端层级。", []),
])

p_sprot_focus_cn = spara([
    ("鸡特异集合同时富集于蛋白N-糖基化（BP；图S5），因此比较重点从“有哪些蛋白”转向“共享蛋白以何种化学状态被使用”。保留下来的共享核心由此成为真正的分子背景，而共享蛋白上的糖基化则成为解释乳突层分化及后续壳体行为的最近端候选层。", [18]),
    ("从当前数据看，我们检测到的大多数反复出现的蛋壳基质蛋白与前人报道总体一致，说明整体蛋壳基质背景与既有研究相吻合；同时，这套数据也扩展了进入比较背景的基质蛋白范围。", []),
])

head("OVAL糖基化标记出最清晰的跨物种差异")
p_s2a_cn = mixed([
    ("完整糖肽为鸟类蛋壳基质蛋白上的具体糖型提供了直接的跨物种视角。图2中的糖蛋白网络显示，一个三物种共享的保守核心之外，还存在两两共享与谱系限制性扇区。最内层对应三物种共享蛋白，周围扇区对应两两共享和物种限制蛋白，最外层节点概括七类糖型。灰色连线表示蛋白与相应糖型之间的对应关系，外层糖型节点颜色越深，表示连接到该糖型的蛋白数越多。高甘露糖型和复合-岩藻糖型在多个蛋白家族中构成广泛背景，而更延伸的唾液酸化类别则集中在外围差异节点上。", False, False),
    ("这一网络层面的不对称性由此突出了一组状态差异显著的共享糖蛋白，并把后续直系同源和结构分析的候选范围进一步收窄。", False, False),
])

p_s2b_cn = mixed([
    ("更严格的BlastP过滤进一步保留了一组适合结构比较的直系同源糖蛋白，并在图3A中概括了这一共享候选空间。以", False, False),
    ("G. gallus", False, True),
    ("为参考，只有当非参考候选的平均E值低于1 × 10⁻⁵且序列一致性满足最终可比性阈值时，才予以保留。这一过滤将后续比较限制在高置信度直系同源范围内。在这一更严格的映射下，OC17仅在鸡中显示糖基化，而OC116、TRFE和OVAL在三物种中都保留了糖基化信号，可作为共享锚点。其中，OVAL表现出最清晰的跨物种糖链差异，因此成为后续结构分析的优先对象。", False, False),
])
cite(p_s2b_cn, [])

p_s2c_cn = spara([
    ("整合蛋白丰度和糖链丰度后，图3B至D进一步识别出OVAL是与跨物种蛋壳差异最一致的共享蛋白。在全数据集中，鸡的蛋白-糖链耦合较弱，而鸭和鸽则持续为正，说明三条谱系不仅糖链身份不同，糖基化与蛋白输出的对应关系也不同。", []),
    ("在重点蛋壳基质蛋白中，OVAL在三物种中都保持高丰度，但其糖链负荷变化明显：鸡最低，鸭更高，鸽最高。相比之下，OC116和TRFE虽然仍然有信息量，但并不像OVAL那样稳定地区分总体蛋白丰度与糖链输出。", []),
    ("图3E至G中的两两富集图进一步说明了为什么OVAL是最清晰的候选。在 Gallus 对 Anas 和 Gallus 对 Columba 的比较平面中，OVAL都落在糖链变化相对更突出的区域，说明它的糖链偏移并不是简单跟随蛋白丰度一起移动，而是比蛋白丰度变化更快，甚至与之部分脱耦。在 Anas 对 Columba 的比较中，OVAL仍然偏离蛋白-糖链完全一致的对角关系，从而把同一排序延续到鸡之外的比较中。完整糖肽鉴定因此把 OVAL 放入一条连贯的跨物种糖型序列：鸡以紧凑高甘露糖型为主，鸭转向中性复合/杂合型，鸽则进一步转向更延伸的唾液酸化复合/杂合型。综合来看，图3B至G将OVAL界定为糖基化变化与表型联系最稳定的共享蛋白。", []),
])

p_s2d_cn = spara([
    ("由于这些OVAL糖链类别在大小和电荷分布上差异显著，更合理的比较变量是OVAL表面可及性，而不是单纯的OVAL丰度。", []),
    ("真正相关的特征，是被不同糖链装饰后其酸性界面还有多少保持化学可及。直系同源控制、丰度解耦和糖链类别推进三方面证据共同将OVAL保留为唯一同时保持可比、化学特异且可进行结构追踪的共享候选。", []),
])

head("OVAL糖链状态重塑表面可及性")

p_s3a_cn = spara([
    ("OVAL随后被作为最强共享候选，用于检验其糖链类别如何改变生物物理可及性。为此，我们重建了主导的糖基化OVAL构象，并为每个物种配对构建去糖基化参考，以检验三物种差异是否主要来自糖链依赖的表面行为，而非仅来自蛋白骨架序列本身。", [4, 11]),
    ("第一步要回答的是，这种跨物种分离究竟是不是由糖链真正引入的。在图4A中，糖基化构象相对于配对的 apo 参考已经在 Ca²⁺ 相关酸性热点数量上发生偏移；同样的偏移在图4B的羧酸基表面暴露量和图4C的整表面电势图中再次出现。", []),
    ("但一旦去除糖链，这种分离中的大部分就会明显收敛，三物种蛋白骨架彼此更接近。因此，最初被恢复出的结构差异并不是一般性的序列差异，而是糖链把矿化起始时暴露给离子环境的酸性表面重新组织了出来（图4A至C；图S7）。", []),
])

p_s3b_cn = spara([
    ("接下来的问题是，这种糖链状态推进在几何上究竟如何落实到 OVAL 表面。鸽首先通过更大的整体糖链包络与另外两种鸟分开，这一点体现在图4D更高的回转半径和图4E更长的端到端距离上。", []),
    ("但这种扩展并没有把糖链整体抬离蛋白表面。相反，在图4F中，鸽的糖链-蛋白距离并未相应增大，而在图4G中还表现出更小的最小糖链-骨架距离，说明这些更长的糖链同时也更容易回折并贴近 OVAL 表面。鸡对应的是另一端：图4D和图4E中的糖链最紧凑，图4F和图4G中的表面接触也最弱；鸭则再次位于两者之间。这样，图4D至G就把跨物种糖型差异转化为一条遮蔽几何链条：从鸡的紧凑且弱接触糖链，到鸽的延伸但贴面糖链，再到居中的鸭状态。", []),
])
p_s3c_cn = spara([
    ("一旦这种几何排序被建立，图4H至K要回答的就不再是四个彼此无关的问题，而是同一片共享酸性界面在连续过滤后还剩下多少可用于矿化。图4H先给出整体界面遮蔽程度；图4I进一步问在这种遮蔽之后还有多少热点表面积保持溶剂暴露；图4J再问候选酸性残基中还有多大比例仍能保留为热点；图4K最后只保留其中同时满足静电有利且空间可及、能够被Ca²⁺接近的净热点。", []),
    ("按这个顺序阅读，图4H至K构成的是一条单向推进的遮蔽级联。界面遮蔽从鸡到鸭到鸽逐步增强，而每一步下游筛选都保留同样的排序，说明更延伸且更贴面的糖链会把同一片共享酸性 OVAL 表面逐步从“大面积可用界面”压缩成更小、更难被矿化环境利用的化学活性区。", []),
])

p_s3d_cn = spara([
    ("图4L和图4M则把同一差异进一步压缩到整体界面层面，分别把热点数量和热点残基表面积拆分为暴露部分与被遮蔽部分。鸡在这两幅图中都保留了最大的暴露份额，鸽把最大的份额转入遮蔽区室，而鸭仍位于两者之间。", []),
    ("把这一结果压缩到整体界面层面后，鸡也就对应于最强的 Ca²⁺ 吸附潜力，并且最符合更早进入 Ca²⁺ 响应式构象打开、从而更早启动矿化的状态；鸽则对应最弱、最晚的另一端，鸭仍处于中间。这一排序与前文表型链条是对上的：鸡同时具有最高的乳突密度和最高的局部出壳抗性，而鸭和鸽则从不同结构背景收敛到较低抗性侧。因此，图4A至M构成的是一条连续的结构论证，而不是若干并列子图：它从糖链依赖的分离出发，经过糖链几何和界面遮蔽，最后收束到共享基质蛋白上的 Ca²⁺ 相关表面可及性。", []),
])

head("有限元分析把同一对比连接到局部出壳抗性")

p_s4a_cn = mixed([
    ("有限元检验把共同的破壳齿界面转化为显式的内向外加载设计。图5A给出了与出壳相关的加载背景，图5B至D则把三种鸟类喙部俯视图与对应的micro-CT有限元建模并列展示。由于网格保留了来自micro-CT的物种特异性壳体几何，这一力学检验始终锚定在前文已经识别出的乳突层背景之上，而不是理想化均质壳壁模型。冲击加载在圆形蛋壳碎片（模型直径D = 2.0 mm）的9个参数化横向偏移位置上采样（3 × 3网格；间距0.5 mm），每物种获得n = 9条独立接触剪切应力时间曲线。为尽可能降低模型尺寸、整体几何以及尤其是蛋壳厚度差异对结果的影响，我们同时记录原始峰值接触力F_max和峰值接触剪切应力τ_max。本文将τ_max视为乳突接触界面局部出壳抗性的直接读数，并从有限元单元输出中"
     "直接提取各偏移位置的峰值接触剪切应力τ_max，"
     "然后计算9个位置的物种均值 ± s.d."
    "（图S8A至F；壳厚分别为", False, False),
    ("G. gallus", False, True),
    (" 0.29 mm、", False, False),
    ("A. platyrhynchos", False, True),
    (" 0.35 mm、", False, False),
    ("C. livia", False, True),
    (" 0.19 mm）。", False, False),
])

cite(p_s4a_cn, [16, 37, 69])

doc.add_page_break()
add_centered_figure("Fig5.jpg", width_cm=13.8, before=0, after=20)
add_main_figure_legend(
    "图5.",
    "乳突界面出壳相关加载的有限元建模框架。",
    [
        ("(A) 胚胎出壳过程中卵齿由壳内侧局部顶压蛋壳的示意图。(B至D) ", False, False),
        ("Gallus gallus", False, True),
        ("、", False, False),
        ("Anas platyrhynchos", False, True),
        (" 和 ", False, False),
        ("Columba livia", False, True),
        (" 的物种特异性喙部俯视图及其对应的micro-CT有限元模型。在每个物种面板中，左侧为喙部俯视图，虚线框标示破壳齿位置，右侧为蛋壳碎片网格、相应锥形压头以及接触时的代表性有限元模型输出。模拟直接建立在实测重建壳体几何而非理想化壳体之上。", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

mixed([
    ("F_max在物种间存在显著差异（p = 1.639 × 10⁻¹³）。", False, False),
    ("G. gallus", False, True),
    (" 为1.117 ± 0.110 N，", False, False),
    ("A. platyrhynchos", False, True),
    (" 为0.898 ± 0.090 N，", False, False),
    ("C. livia", False, True),
    (" 为0.485 ± 0.039 N，且所有两两比较均显著（图6A）。相比之下，τ_max收束为两级格局（p = 6.644 × 10⁻¹⁰）。", False, False),
    ("G. gallus", False, True),
    (" 为551.6 ± 108.8 MPa，显著高于", False, False),
    ("A. platyrhynchos", False, True),
    (" 的404.0 ± 39.6 MPa和", False, False),
    ("C. livia", False, True),
    (" 的393.0 ± 35.2 MPa，而后两者之间无统计学差异（图6B）。", False, False),
])

mixed([
    ("F_max与τ_max结果的差异表明，鸭蛋壳所需较高原始接触力"
     "主要归因于其较大壳厚（0.35 mm vs. 鸽子的0.19 mm），"
     "而非更优越的单位面积材料级抵抗力。"
     "相反，", False, False),
    ("G. gallus", False, True),
    ("相对于另外两个物种τ_max升高36–40%，表明其局部出壳抗性更高，且不依赖壳厚。"
     "由此形成的高低分组中，", False, False),
    ("G. gallus", False, True),
    ("单独位于高值组，", False, False),
    ("A. platyrhynchos", False, True),
    ("和", False, False),
    ("C. livia", False, True),
    ("共同处于低值组，这一结果与显微CT乳突密度经Duncan多重极差检验得到的分组一致（图1D）。力学结果并没有制造出一个新模式，而是保留了前文已经在乳突层和OVAL可及性上恢复出的同一跨物种对比。",
     False, False),
])

mixed([
    ("若只用整壳层面的破裂力讨论三种蛋壳，鸭可能会因壳厚较大而显得在力学上优于鸡，"
    "即便它并不具备相同的高密度乳突状态。τ_max聚焦于micro-CT保留的乳突接触界面局部出壳抗性，"
    "因此消除了这种表观歧义，并显示高密度鸡状态在功能上仍然独立，而鸭与鸽则在较低抗性上收敛。这组有限元结果不是一般性的力学补充，而是对前文结构解释的一次功能验证。", False, False),
])

para("讨论", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT, heading=True)

p_disc_mam1_cn = smixed([
    ([('三物种之间首先分化的是乳突层组织，而蛋壳基质工具箱本身仍然大体共享。', False, False),
            ('在这一共享背景下，OVAL 糖链状态为分子变化、表面可及性和局部出壳抗性之间提供了当前数据中最清晰的对应关系。', False, False)], [1, 16, 18]),
])

p_disc_regulator_cn = spara([
    ("这一三物种设计之所以重要，是因为蛋壳性状对应的是连续的生态和发育梯度，而不是单一的二分对照。", [15, 39]),
    ("巢穴环境对应陆生到强水域依赖的连续轴线，雏鸟状态则从更早成到更晚成连续分布，因此两者都不适合被压缩为简单的二分法。", [3, 23]),
    ("鸭在这一设计中尤其关键，因为它保留了广义上的早成发育条件，但OVAL糖链状态和可及性谱型转向中间状态，τ_max结果也与鸽而非鸡收敛。这组三物种的价值，正在于它们在生态—发育连续空间中被有意拉开，同时保持了可比的出壳界面。", [3, 15, 22, 23]),
], before=0, after=120)

p_disc_axis_cn = spara([
    ("乳突层成矿方式仍是解释中的核心结构层级。", [1, 28]),
    ("一旦早期方解石晶体单元建立，后续蛋壳区域就会继承第一次成矿窗口所形成的间距逻辑，因此高密度乳突场改变的不只是形态，也会改变基质保留、矿物连续性和局部应力再分配。", [1, 30, 36]),
    ("这种强调与前人把乳突层视为晶体成核与基质调控交汇处的认识是一致的，但本研究进一步把这一层直接连到一个可跨物种比较的糖链状态读数上，而不只是停留在壳体质量描述层面。", [1, 28, 31, 32]),
    ("最近的家禽组学研究越来越多地把年龄、壳腺转录、细胞外囊泡货物以及其他整壳质量指标与蛋壳表型联系起来，但这些描述层面通常仍比这里被单独识别出的近端材料层更宽泛。", [33, 52, 57, 70]),
    ("因此，乳突层组织并不只是另一个壳体性状，而是基质化学最有可能开始偏置后续力学结果的最早材料背景。", [1, 2]),
    ("也正因为如此，乳突层是第一处能够被读作“可能具有后果”的跨物种差异，而不仅仅是一组描述性的形态差别。", [1, 28]),
], before=0, after=120)

p_disc_mam2_cn = spara([
    ("在这里考察的各个分子层中，OVAL的N-糖链结构与跨物种结构差异的对应最为紧密。", []),
    ("直系同源组更替、基因家族变化和糖蛋白网络分化仍然重要，但它们主要界定的是比较背景，而不是最近端的解释层。OVAL糖链状态更有信息量，因为它跨物种共享、具有化学可解释性，并位于一个已被认为参与矿化的高丰度基质蛋白上。", [4, 18, 27]),
    ("前人的工作已经把OVAL保留为高丰度蛋壳糖蛋白和潜在成矿候选，而更早的糖蛋白组研究也提示蛋壳基质蛋白可以处于不同的N-糖基化状态。因此，这里的推进并不只是“检测到更多糖肽”，而是把这些糖基化信息组织成一个受直系同源约束的跨物种比较，并进一步识别出哪一种糖链状态与表型最清楚地对应。", [4, 18]),
    ("前人的鸡来源研究已经为OVAL建立了糖基化位点基础，也确认了OC116中存在糖基化Asn；本研究则进一步解析了被带入结构建模的对应OVAL直系同源测序子上的优势糖型（G. gallus N293；A. platyrhynchos与C. livia N97）。相较于既往以位点目录为主的工作，这里的扩展首先体现在跨物种 breadth，其次体现在把优势糖型直接推进到结构和力学解释之中。因此，OVAL的价值不在于其独特，而在于它在保持跨物种可比性的同时，仍保留了具体糖链类别层面的可解释化学分化。", [8, 18, 21]),
])

p_disc_other_cn = spara([
    ("非OVAL信号仍然重要。OC116和TRFE仍是有信息量的共享蛋白，而OC17仅在鸡中显示糖基化，因此可能代表一种更具谱系限制性的成矿程序。", []),
    ("前人的蛋壳研究已经分别赋予OC17、OC116和ovotransferrin相关组分明确的功能意义，而本研究并不是推翻这些认识。相反，我们的数据表明，这些蛋白更稳定地构成了生物学背景，而不是跨物种最尖锐的区分层。", [10, 19, 29]),
    ("对OC116尤其如此：更早的生化工作已经确认鸡蛋壳基质OC116存在糖基化Asn，而近期的鸟类古蛋白组学工作又进一步显示，OC116是鸟类蛋壳蛋白中序列变异性最高的一类分子之一，并且在种内层面也具有显著变异，而不是一个始终稳定的物种标记。放在这一背景下，我们当前的比较结果就更容易理解：OC116保持糖基化并不等于它一定会像OVAL那样恢复出稳定的结构—表型排序。", [21, 66]),
    ("这也说明本研究与既往蛋壳糖蛋白组工作的关系更像是下一步，而不是简单重复。前人的工作首先证明了蛋壳基质蛋白确实可以被糖基化，且位点层面的检测是可行的；而我们这里增加的是共享直系同源、优势糖型类别以及这些糖型在跨物种结构表面上的后果。", [18, 21]),
    ("共享工具箱因此仍然是多组分的，只是OVAL提供了当前最易检验的切入点。", []),
], before=0, after=120)

p_disc_oval_cn = spara([
    ("Re-Glyco与APBS分析为这一论证提供了结构桥梁。", []),
    ("鸡的紧凑糖链使关键酸性的OVAL表面保持相对暴露，而鸽更长且电负性更强的糖链则在空间和静电两个层面削弱了Ca²⁺的接近；鸭再次位于两者之间。", []),
    ("前人的体外和结构工作已经提示OVAL的构象与静电性质会影响矿化过程，但并没有在鸟类物种之间比较一组彼此匹配、且能分辨糖型的表面系综。", [4, 11]),
    ("这样，糖链状态差异就被落实为可作物理解释的表面差异。尽管这一结果并不建立矿化的直接因果机制，但它支持一种有边界的推论：同一基质蛋白上的不同糖链状态可能改变呈现给成矿环境的化学表面，并因此参与这里观察到的结构分化。", [42, 61]),
], before=0, after=120)

p_disc_mech_cn = spara([
    ("这里的力学比较围绕出壳时由壳内向外的加载事件展开，而不是常见的外压或整壳破裂测试。", [16, 37, 69]),
    ("这一点很重要，因为蛋壳厚度会显著抬高绝对失效载荷，而τ_max受厚度混杂的影响更小，更直接反映载荷如何穿过乳突界面传递。", [16, 34, 69]),
    ("因此，本研究与既往蛋壳强度和有限元工作形成互补关系，这里检验的是内侧乳突界面是否保留了与基质状态和形态组织一致的跨物种对比。", [16, 34, 35, 69]),
    ("鸭最能说明这种分离，因为更厚的壳体抬高了F_max，却没有重建鸡那种高τ_max状态。", [16, 37, 69]),
])

p_disc_evo_cn = para(
    "另一个需要考虑的问题是，乳突层在孵化后期和出壳过程中可能发生部分吸收。这个问题并不削弱当前比较的意义，因为我们量化的是乳突密度和晶体单元组织，这些特征即便在最内侧部分材料被吸收后，仍然保留在蛋壳整体结构中。同样的考虑也影响了力学读数的选择。我们强调第二个特征峰而不是第一个，因为最早出现的受力峰更容易受初始形貌接触影响，而后一个特征峰更能反映载荷穿过整个壳壁的应力传递。",
    bold=False, size=11, before=0, after=120
)

p_disc_discriminate_cn = spara([
    ("这些因素有助于把壳厚缓冲和发育背景，与本文强调的材料层级路径区分开来。", []),
    ("壳厚、体型和广义繁殖生态都会提供背景差异，谱系历史无疑也重要。", [3, 14]),
    ("但基于厚度的解释无法说明τ_max差异，而弥散的谱系分化解释也无法说明为什么同一对比会在糖链类别、静电可及性、乳突层组织和出壳相关力学中反复出现。", [16, 37]),
    ("在这组数据中反复出现的，是糖链状态、表面遮蔽、乳突层组织和内向外加载下τ_max之间的对齐。", []),
    ("在这组三物种数据中，生态与系统发育设定了比较背景，而基质蛋白糖链状态仍然是当前恢复出的最近端、且具有化学可解释性的层级。", [4, 18]),
], before=0, after=120)

p_disc_function_cn = para(
    "因此，这一讨论最终收束到鸡蛋壳状态。在当前比较中，鸡同时表现出最高的乳突密度、最少受遮蔽的OVAL钙相关表面，以及内向外加载条件下最高的局部出壳抗性。这种一致性说明，在这组三物种数据中，鸡式蛋壳状态是最明确的结构—功能目标，也说明复用基质蛋白上的化学特异性状态，可能比广义蛋白组周转更清楚地组织矿化表型。",
    bold=False, size=11, before=0, after=120
)
cite(p_disc_function_cn, [67, 73, 74])

p_disc_selection_cn = para(
    "鸭和鸽之所以仍然关键，在于它们从壳体结构和生态—发育位置两个层面共同界定了鸡状态的边界。鸭说明，更偏水域的生态位和广义上的早成发育条件，可以与更厚的壳体、中间型的 OVAL 可及性以及较低的 τ_max 同时出现，但仍不能重建出鸡那样的乳突界面抗性；鸽则说明，更偏陆生且更晚成的位置，也可以在更薄的壳体和另一种乳突背景下与鸭收敛到同样较低的 τ_max。正是这两个对照，让鸡成为贯穿当前生态与发育取样空间、最适合用来连接糖链依赖基质行为与蛋壳性能的参考状态。在这一框架下，OVAL 糖链状态是让鸡式高抗性状态获得机制解释的最明确分子层。",
    bold=False, size=11, before=0, after=120
)

p_disc_biomineral_cn = para(
    "同样的分析序列也应当可以超出鸟类蛋壳。许多生物矿化体系都依赖有机基质通过化学特异性的界面状态来调节离子可及性、表面暴露与矿物成核，而并不只是由总体成分决定。放在这一更广的框架下，本研究提供的是一条从糖蛋白状态到表面呈现、再到介观功能结果的分析路径，这恰好也是其他矿化组织与仿生材料共同面对的尺度桥接问题。它甚至可能延伸到再生医学场景，因为蛋壳来源材料与蛋壳膜蛋白已经被用于组织工程和骨修复，包括提升注射型骨移植物的成骨效率。因此，这项工作的价值并不只局限于一种鸟类蛋壳表型，也在于它为“化学特异性的基质状态如何组织生物矿化行为”提供了一个可迁移到生物学和医学问题中的分析模板。",
    bold=False, size=11, before=0, after=120
)
cite(p_disc_biomineral_cn, [64, 67, 68, 73])

p_disc_future_cn = para(
    "当前结论仍有明确边界。我们的结构分析采用的是优势糖型，而不是体内全部糖型的完整分布；有限元模型也把各物种蛋壳近似为平均尺度上的机械均一材料，APBS所需的子宫液离子环境同样仍未被充分约束。下一步最关键的检验应当是定义糖型的矿化实验、在鸡中直接操控OVAL糖基化，以及对同一内向外力学对比进行位点分辨验证。这些实验将决定，这里识别出的OVAL糖链状态究竟直接参与成壳矿化，还是以异常稳定的方式标记了鸡式高抗性状态。",
    bold=False, size=11, before=0, after=120
)

p_disc_close_cn = para(
    "总之，本研究建立了一条从乳突层组织到糖蛋白状态、结构特征再到局部出壳力学的连续比较链条，用于解析三种鸟类蛋壳之间的差异。鸡表现为目标状态，同时具有高密度乳突层组织、紧凑的OVAL糖链、更高的Ca²⁺相关表面暴露，以及出壳过程中乳突界面最高的局部抗性。这种比较策略也可以继续扩展到其他高丰度蛋壳基质蛋白，只要其修饰状态能够以相近置信度被解析。我们的形态、糖蛋白组、结构与力学联合分析表明，OVAL糖链状态是连接鸡式蛋壳状态、乳突层组织和局部出壳力学的最有信息量分子层。",
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
    ("三个禽类物种各采集六枚新鲜产出蛋，均于产出后24\u00a0h内收集。", False, False),
    ("Gallus gallus", False, True),
    ("（家鸡）蛋壳来自中国农业大学家禽资源保护场（北京）；", False, False),
    ("Columba livia", False, True),
    ("（鸽子）蛋由中国农业大学动物医学院常于教授提供；", False, False),
    ("Anas platyrhynchos", False, True),
    ("（绿头鸭）蛋由北京金星鸭业提供。所有蛋壳样品于处理前在4\u00b0C下保存；统一的新鲜采集与冷藏条件用于尽量减少产蛋后处理带来的额外变异。", False, False),
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
    "合并上清液于\u221280\u00b0C保存至分析。三物种在相同提取化学条件下并行处理，以尽量降低因批次操作漂移造成的假性差异。"
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
    "所有样本均采用相同的分割与后处理流程，以确保物种间差异主要反映形态本身，而非重建参数设置。"
)
cite(p_m_ct_cn, [1, 30])

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
    "每个重复以两枚蛋混样，目的是降低单枚蛋个体差异，同时保留物种层面的主导信号。"
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
    "使用物种匹配的参考蛋白质组，有助于减少检索结果向注释更完善数据库偏置的风险。"
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
    "结构类别均在位点层面完成注释后再汇总，以便在共享蛋白背景上比较不同物种的糖链使用方式。"
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
    "图3B至D所用的蛋白质与糖基化位点定量表分别来自各物种的Protein_quant与"
    "Site_quant工作表。若存在Number Comparable字段，则蛋白条目保留\u2265\u00a02，"
    "糖基化位点条目保留\u2265\u00a01。每个蛋白accession的蛋白丰度定义为该物种全部"
    "强度列的平均值；每个糖基化位点的糖链丰度定义为对应位点强度列的平均值；"
    "仅保留正值信号。随后按protein accession将糖基化位点表与蛋白表内连接，"
    "使每个散点代表一个具有匹配蛋白丰度信息的定量糖基化sequon。蛋白丰度与"
    "糖链丰度经log2转换后，在各物种内分别计算Spearman秩相关及双侧p值。"
    "OVAL、OC116、TRFE和OC17依据图3A采用的严格直系同源注释高亮显示，"
    "标签同时标出对应糖基化Asn位点。"
)

para(
    "图3E至G的两两糖链-蛋白二维富集图基于直系同源映射后的物种间蛋白与糖链"
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
    "采用APBS\u00a0v3.4.1对每个Re-Glyco系综模型及其匹配的去糖基化（apo）"
    "参考结构计算静电表面势。"
    "原子分电荷和半径通过PDB2PQR赋予（CHARMM36力场，PROPKA pH\u00a07.4质子化）；"
    "糖链重原子分电荷采用GLYCAM06参数集；"
    "J.\u00a0Comput.\u00a0Chem. 29:622）。"
    "溶剂可及表面积由Shrake\u2013Rupley算法计算；"
    "相对ASA\u00a0\u2265\u00a00.25的残基定义为表面残基。"
    "Ca\u00b2\u207a结合静电热点定义为APBS势值<\u00a0\u22125\u00a0kT/e的表面Asp/Glu残基。"
    "报告的系综水平指标包括热点数（N_hot）、每热点平均SASA、"
    "热点占全部表面Asp/Glu比例及表面静电势中位数。"
    "全部模型均采用同一热点阈值和表面定义规则，以保持跨物种结果的可比性。"
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
    "分别提取峰值接触力（F_max）和峰值接触切应力（\u03c4_max）。这种9点采样设计可以在不改变碎片尺寸与加载几何的前提下，保留局部位置异质性的影响。", False, False),
])
cite(p_m_fea_cn, [16, 37, 69])

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
