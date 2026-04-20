#!/usr/bin/env python3
"""
Nature Communications style — species phylogenetic tree
Source: Species_phylogenetic_tree.nwk.gz
Output: Phylogenetic/Fig_phylo_tree.png
"""

from pathlib import Path
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── NC style ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.sans-serif":  ["Times New Roman", "DejaVu Sans"],
    "font.size":        8,
    "figure.dpi":       300,
    "savefig.dpi":      300,
    "savefig.bbox":     "tight",
    "pdf.fonttype":     42,
})

ROOT    = Path(__file__).parent
SRC     = ROOT / "Species_phylogenetic_tree.nwk.gz"
FIG_DIR = ROOT.parent / "Phylogenetic"
FIG_DIR.mkdir(exist_ok=True)

SP_COLOR = {
    "Gallus":  "#B54664",
    "Anas":    "#7895C1",
    "Columba": "#F0C284",
}
SP_COMMON = {
    "Gallus":  "Chicken",
    "Anas":    "Duck",
    "Columba": "Pigeon",
}

# ── Newick parser ─────────────────────────────────────────────────────────────
def parse_newick(nwk: str):
    nwk = nwk.strip().rstrip(";")

    def parse(s):
        s = s.strip()
        if s.startswith("("):
            depth = i = 0
            for i, c in enumerate(s):
                if c == "(":  depth += 1
                elif c == ")": depth -= 1
                if depth == 0: break
            inner = s[1:i];  rest = s[i + 1:]
            parts, buf, d = [], "", 0
            for c in inner:
                if c == "(":  d += 1
                elif c == ")": d -= 1
                if c == "," and d == 0:
                    parts.append(buf); buf = ""
                else:
                    buf += c
            parts.append(buf)
            children = [parse(p) for p in parts]
            m = re.match(r"([^:]*)?(?::(.+))?$", rest)
            name   = (m.group(1) or "").strip()
            length = float(m.group(2)) if m and m.group(2) else 0.0
            return {"name": name, "length": length, "children": children}
        else:
            m = re.match(r"([^:]+)?(?::(.+))?$", s)
            name   = (m.group(1) or "").strip()
            length = float(m.group(2)) if m and m.group(2) else 0.0
            return {"name": name, "length": length, "children": []}

    return parse(nwk)


def assign_coords(node, x=0.0, counter=None):
    if counter is None: counter = [0]
    if not node["children"]:
        node["x"] = x + node["length"]
        node["y"] = counter[0]; counter[0] += 1
        return node["y"]
    ys = [assign_coords(c, x + node["length"], counter) for c in node["children"]]
    node["x"] = x + node["length"]
    node["y"] = (min(ys) + max(ys)) / 2
    return node["y"]


def get_leaves(node):
    if not node["children"]: return [node]
    leaves = []
    for c in node["children"]: leaves.extend(get_leaves(c))
    return leaves


def max_x(node):
    if not node["children"]: return node["x"]
    return max(max_x(c) for c in node["children"])


# ── Drawing ───────────────────────────────────────────────────────────────────
def draw_clade(ax, node, lw=1.8):
    if node["children"]:
        cy = [c["y"] for c in node["children"]]
        ax.plot([node["x"]] * 2, [min(cy), max(cy)],
                color="#555555", lw=lw, solid_capstyle="round", zorder=3)
        for ch in node["children"]:
            leaf_name = ch["name"] if not ch["children"] else ""
            color = SP_COLOR.get(leaf_name, "#888888")
            ax.plot([node["x"], ch["x"]], [ch["y"]] * 2,
                    color=color, lw=lw, solid_capstyle="round", zorder=3)
            # branch-length label above mid-branch
            if ch["length"] > 1e-6:
                mx = (node["x"] + ch["x"]) / 2
                ax.text(mx, ch["y"] + 0.14, f"{ch['length']:.4f}",
                        ha="center", va="bottom", fontsize=6, color="#888888")
            draw_clade(ax, ch, lw)
    else:
        col = SP_COLOR.get(node["name"], "#333333")
        ax.scatter([node["x"]], [node["y"]], s=36, color=col,
                   zorder=5, linewidths=0)
        label = f"$\\it{{{node['name']}}}$  ({SP_COMMON[node['name']]})"
        ax.text(node["x"] + 0.002, node["y"], label,
                va="center", ha="left", fontsize=9, color=col)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    with open(SRC, "r", encoding="utf-8", errors="ignore") as f:
        nwk = f.read().strip()

    tree = parse_newick(nwk)
    tree["length"] = 0.0          # root starts at x = 0
    assign_coords(tree)

    n_tips = len(get_leaves(tree))
    xmax   = max_x(tree)

    fig, ax = plt.subplots(figsize=(100 / 25.4, 80 / 25.4))

    # root horizontal line(s) to first children
    for ch in tree["children"]:
        col = SP_COLOR.get(ch["name"], "#888888")
        ax.plot([0, ch["x"]], [ch["y"]] * 2,
                color=col, lw=1.8, solid_capstyle="round", zorder=3)
        if ch["length"] > 1e-6:
            mx = ch["x"] / 2
            ax.text(mx, ch["y"] + 0.14, f"{ch['length']:.4f}",
                    ha="center", va="bottom", fontsize=6, color="#888888")
    draw_clade(ax, tree, lw=1.8)

    # root marker
    ax.scatter([0], [tree["y"]], s=18, color="#555555", zorder=6)

    # scale bar
    bar = 0.02
    bx, by = 0.002, -0.6
    ax.annotate("", xy=(bx + bar, by), xytext=(bx, by),
                arrowprops=dict(arrowstyle="-", color="#555555", lw=1.0))
    ax.text(bx + bar / 2, by - 0.12, f"{bar} substitutions/site",
            ha="center", va="top", fontsize=6.5, color="#555555")

    # model annotation
    ax.text(0.98, 0.02,
            "Model: JTT+CAT\nMethod: Maximum Likelihood",
            transform=ax.transAxes,
            ha="right", va="bottom", fontsize=6.5, color="#777777",
            linespacing=1.6)

    ax.set_xlim(-0.005, xmax + 0.055)
    ax.set_ylim(-0.9, n_tips - 0.1)
    ax.axis("off")

    # legend
    handles = [mpatches.Patch(facecolor=SP_COLOR[s], label=s, linewidth=0)
               for s in ["Gallus", "Anas", "Columba"]]
    ax.legend(handles=handles, title="Species", frameon=False,
              fontsize=7.5, title_fontsize=8,
              loc="upper left", bbox_to_anchor=(0, 1.0))

    fig.tight_layout()
    out = FIG_DIR / "Fig_phylo_tree.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
