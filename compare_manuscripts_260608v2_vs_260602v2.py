from __future__ import annotations

import difflib
import re
from pathlib import Path

from docx import Document


BASE = Path.cwd()
WORK_DIR = next(p for p in BASE.iterdir() if p.is_dir() and p.name.startswith("03_"))
OLD_DOCX = WORK_DIR / "0_Manuscript" / "manuscript260602v2.docx"
NEW_DOCX = WORK_DIR / "0_Manuscript" / "manuscript260608v2.docx"
REPORT = WORK_DIR / "manuscript260608v2_vs_260602v2_changes.md"


SECTION_STARTS = [
    (0, "Title / Short Title"),
    (3, "Abstract"),
    (5, "Teaser"),
    (6, "Introduction"),
    (12, "Results"),
    (13, "Results: Hatching Interface and Mammillary Morphology"),
    (24, "Results: OVAL Glycosylation"),
    (33, "Results: OVAL Surface Accessibility"),
    (42, "Results: Inside-Out Loading"),
    (51, "Discussion"),
    (64, "Materials and Methods"),
    (91, "References"),
]


def paragraphs(path: Path) -> list[str]:
    return [p.text.strip() for p in Document(str(path)).paragraphs]


def section_for_index(index: int) -> str:
    current = SECTION_STARTS[0][1]
    for start, name in SECTION_STARTS:
        if index >= start:
            current = name
        else:
            break
    return current


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?|[\u4e00-\u9fff]", text))


def short(text: str, limit: int = 230) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def changed_rows(old: list[str], new: list[str]) -> list[dict]:
    rows = []
    for i in range(max(len(old), len(new))):
        old_text = old[i] if i < len(old) else ""
        new_text = new[i] if i < len(new) else ""
        if old_text == new_text:
            continue
        if not old_text and not new_text:
            continue
        ratio = difflib.SequenceMatcher(None, old_text, new_text).ratio() if old_text or new_text else 1
        rows.append(
            {
                "idx": i,
                "section": section_for_index(i),
                "ratio": ratio,
                "old_words": words(old_text),
                "new_words": words(new_text),
                "old": old_text,
                "new": new_text,
            }
        )
    return rows


def refs_with_doi(texts: list[str]) -> tuple[int, int, int]:
    in_refs = False
    total = doi = url = 0
    for text in texts:
        if text == "References":
            in_refs = True
            continue
        if not in_refs:
            continue
        if re.match(r"^\d+\.\s+", text):
            total += 1
            doi += bool(re.search(r"\bdoi:\s*10\.", text, re.I))
            url += "Available at:" in text
    return total, doi, url


def write_report() -> None:
    old = paragraphs(OLD_DOCX)
    new = paragraphs(NEW_DOCX)
    rows = changed_rows(old, new)
    by_section: dict[str, list[dict]] = {}
    for row in rows:
        by_section.setdefault(row["section"], []).append(row)

    old_ref_total, old_doi, old_url = refs_with_doi(old)
    new_ref_total, new_doi, new_url = refs_with_doi(new)

    lines = [
        "# manuscript260608v2 vs manuscript260602v2 结构化修改对比",
        "",
        f"- 基准稿：`{OLD_DOCX.relative_to(WORK_DIR)}`",
        f"- 当前稿：`{NEW_DOCX.relative_to(WORK_DIR)}`",
        "- 对比范围：英文主文稿；不包含中文译稿。",
        "",
        "## 总览",
        "",
        f"- 段落总数：旧稿 {len(old)}，当前稿 {len(new)}。",
        f"- 有文本变化的段落：{len(rows)}。",
        f"- 参考文献：旧稿 {old_ref_total} 条，当前稿 {new_ref_total} 条。",
        f"- DOI/稳定链接：旧稿 DOI {old_doi}、URL {old_url}；当前稿 DOI {new_doi}、URL {new_url}。",
        "- 主要变化方向：从“描述性连接 OVAL 糖链与蛋壳状态”转为“Ca²⁺可及性 -> OVAL 解折叠 -> 成核位点暴露 -> 乳突层致密度 -> 局部破壳力学”的机制链。",
        "",
        "## 分节变化",
        "",
        "### Title / Short Title",
        "",
        "- 标题由 `Cross-species OVAL glycan states reveal a matrix mechanism for avian shell-breaking mechanics` 改为 `OVAL glycan states link eggshell matrix chemistry to avian shell-breaking mechanics`。",
        "- 短题名由 `OVAL glycans shape eggshell state` 改为 `OVAL glycans tune shell-breaking mechanics`。",
        "- 变化目的：降低过强的 `reveal` 语气，使题名更直接指向 matrix chemistry 与 shell-breaking mechanics 的连接。",
        "",
        "### Abstract",
        "",
        "- 首句重写为 Science Advances 风格的背景-缺口句：蛋壳由基质引导矿化形成，但连接成核位点与孵化力学的分子表面状态仍不清楚。",
        "- 删除原稿较泛化的 `eggshell matrix proteins are key regulators...` 开场，改为直接引出 mechanistic gap。",
        "- 加入关键机制链：鸡 OVAL 保留最高 Ca²⁺可及表面，在富 Ca²⁺子宫液环境中更早满足解折叠钙载荷，更高效暴露基质结合成核位点，形成更致密乳突层。",
        "- 摘要结论从“连接 Ca²⁺可及表面与有利孵化力学”扩展为“更致密乳突状态对应剥离壳厚效应后的最高局部破壳响应”。",
        "",
        "### Teaser",
        "",
        "- 由“OVAL glycan states reveal how eggshell matrix chemistry can shape shell regions used during hatching”改为“OVAL glycan states connect matrix-protein surface accessibility to shell regions used during hatching”。",
        "- 变化目的：把 teaser 的焦点从宽泛的 matrix chemistry 转到 surface accessibility。",
        "",
        "### Introduction",
        "",
        "- 第一段重构句间逻辑：先说明蛋壳必须外部坚固、内部可破，再说明其保护胚胎、维持生物安全隔室、供应钙、提供发育空间。",
        "- 恢复并强化“鸟类蛋壳形成是自然界最快速的生物矿化过程之一”的背景。",
        "- 明确基质蛋白在快速矿化中协调钙递送、成核、晶体生长和壳结构形成。",
        "- 加入从孵化反转力学问题到卵齿局部加载的过渡，减少原稿从矿化直接跳到卵齿的突兀感。",
        "- 末端仍落到原机制问题：在可比破壳界面下，乳突层中哪些分子调控因子解释跨物种蛋壳状态差异。",
        "- 后续引言段落主要为语气和可读性微调：`OVAL provided that bridge...` 从长句拆分为更清晰的两句；研究路线段由 `We established an integrated approach` 改为 `using an integrated workflow`。",
        "",
        "### Results: Hatching Interface and Mammillary Morphology",
        "",
        "- 图 1 相关结果保留原始数据和统计解释。",
        "- 对乳突层形态描述做局部语言修正，例如 `pigeon` 句首改为 `Pigeon`，并保持 chicken/duck/pigeon 的形态对比不变。",
        "- 该部分未改变结论：乳突层是首先出现清晰跨物种对比的层级。",
        "",
        "### Results: OVAL Glycosylation",
        "",
        "- 小标题由 `OVAL glycosylation gives...` 改为 `OVAL glycosylation provides...`，语气更正式。",
        "- 修复 Fig. 2 段落中的句号后缺空格等格式问题。",
        "- OVAL 仍作为共享蛋白中最可解释的 glycan-state discriminator；未改变 glycoprotein、glycosite、glycan composition、JS similarity 等数值。",
        "",
        "### Results: OVAL Surface Accessibility",
        "",
        "- 大幅增强 Fig. 4 结果的机制解释。",
        "- 原稿主要说鸡保留最高 Ca²⁺相关表面、鸽受糖链遮蔽更强；当前稿进一步解释这意味着鸡 OVAL 在富 Ca²⁺子宫液环境中更容易达到构象打开所需钙载荷。",
        "- 新增逻辑：更早或更高效的 OVAL 打开 -> 基质结合成核位点暴露 -> 更高成核位点密度 -> 更致密乳突层 -> 为后续局部破壳力学测试提供结构前提。",
        "- Fig. 4 图注保持面板说明和统计方法，主要做术语和格式统一，如 `Ca²⁺ hotspot`、`modeling`。",
        "",
        "### Results: Inside-Out Loading",
        "",
        "- Fig. 5 图注被修改：星形标记现在明确表示 Tukey HSD 显著差异峰值，点标记表示无显著成对差异峰值。",
        "- 保留 F_max 和 τ_max 的全部数值与显著性结果。",
        "- 删除/改写不清楚的句子 `It did not indicate superior unit-area material resistance.`。",
        "- 新表述解释为：鸭较高 F_max 主要来自更厚壳体，表示可承载更高总接触力，但在接触应力尺度上并未表现出更强局部抗力。",
        "- 继续强调 τ_max 更能分离壳厚效应与乳突界面局部响应。",
        "",
        "### Discussion",
        "",
        "- 讨论首段保留核心结论：分化首先出现在乳突层，而不是大规模 matrix-protein turnover。",
        "- 乳突层解释段被重写为完整机制模型：紧凑鸡 OVAL 糖链保留最高 Ca²⁺可及酸性表面；在富 Ca²⁺子宫液中更快达到构象打开所需钙载荷；更早暴露成核位点；形成更致密乳突层场。",
        "- Re-Glyco/APBS 讨论段从“糖链产生物理可解释表面差异”进一步推进到“糖链改变共享基质蛋白满足 Ca²⁺载荷并发生解折叠的速度”。",
        "- 力学讨论段明确鸭的厚壳提高 F_max 但不重现鸡的高 τ_max，强调厚度解释不能替代乳突界面机制。",
        "- 新增早成-晚成生态/生活史解释：早成到晚成的变化可能改变壳保护与雏鸟出壳能力之间的平衡；晚成鸟如鸽可能通过关键基质蛋白糖基化改变形成更疏松乳突层，降低弱雏局部破壳难度。",
        "- 该进化解释使用 `consistent with the possibility`、`could favor`、`may contribute` 等克制语气，避免把当前三物种比较写成已证明的宏观进化规律。",
        "- 结论段加入：鸡端点包含更高 Ca²⁺相关表面暴露、预测更低 Ca²⁺依赖 OVAL 打开阈值、更密集成核位点形成；鸽端点对应更强遮蔽和较低局部响应。",
        "",
        "### Materials and Methods",
        "",
        "- Biological materials 删除 `during the mid-laying period`。",
        "- 品种名规范为 `Chahua pink-shell laying hens`、`Shaoxing spotted green-shell ducks`、`White King pigeons`。",
        "- 删除鸽子来源中的个人姓名，改为来自中国农业大学兽医学院。",
        "- `N-glycan structural ensemble modelling` 改为美式拼写 `modeling`，与全稿 US spelling 保持一致。",
        "- 方法部分其余实验参数、样品数量、仪器、统计方法未做实质改动。",
        "",
        "### References",
        "",
        "- 参考文献从无 DOI 状态更新为 66 条 DOI + 1 条稳定来源 URL。",
        "- Ref. 7 为 1961 年 Wilson Bulletin 文献，未找到 DOI，补充稳定来源 URL。",
        "- Ref. 3 题名修正为 Crossref/ScienceDirect 记录中的正式题名。",
        "- Ref. 11 补全 gecko 物种名信息并加入 DOI。",
        "- 当前稿引用复查结果：正文引用与参考文献匹配，编号连续，首次引用顺序正确。",
        "",
        "## 段落级变更索引",
        "",
        "说明：Similarity 越低，说明该段改写幅度越大；标题、摘要、引言首段、Fig. 4 解释、Fig. 5 图注、讨论机制段、方法材料来源和参考文献 DOI 是主要变化区。",
        "",
        "| 段落 | 章节 | Similarity | 字数变化 | 旧稿摘要 | 当前稿摘要 |",
        "|---:|---|---:|---:|---|---|",
    ]

    for row in rows:
        if not row["old"] and not row["new"]:
            continue
        delta = row["new_words"] - row["old_words"]
        lines.append(
            f"| {row['idx']} | {row['section']} | {row['ratio']:.2f} | {delta:+d} | {short(row['old']).replace('|', '/')} | {short(row['new']).replace('|', '/')} |"
        )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT)


if __name__ == "__main__":
    write_report()
