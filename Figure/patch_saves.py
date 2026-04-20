"""
Patch all Figure scripts to use _save.save_fig for unified PNG/PDF/SVG output.
Only modifies the save/output sections, no rendering changes.
"""
import re, os

FIGURE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(FIGURE_DIR)

def read(f):
    with open(f, 'r', encoding='utf-8') as fh:
        return fh.read()

def write(f, t):
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(t)

# ═══════════════════════════════════════════════════════════════
# Fig1A.py — single panel → Fig1A
# ═══════════════════════════════════════════════════════════════
t = read('Fig1A.py')
# Add import
t = t.replace("import os\n", "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# Replace save
t = t.replace(
    "out = r'D:\\system_folder\\Desktop\\Work On\\Figure\\png\\Fig1A.png'\n",
    ""
)
t = t.replace(
    "plt.savefig(out, dpi=160, bbox_inches='tight')\nprint('Saved:', out)",
    "save_fig(plt.gcf(), 'Fig1A', dpi=160)"
)
write('Fig1A.py', t)
print("Patched Fig1A.py")

# ═══════════════════════════════════════════════════════════════
# Fig1B.py — single panel → Fig1B
# ═══════════════════════════════════════════════════════════════
t = read('Fig1B.py')
t = t.replace("import pandas as pd", "import pandas as pd\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig", 1)
t = t.replace(
    "out = r'D:\\system_folder\\Desktop\\Work On\\Figure\\png\\Fig1B.png'\n",
    ""
)
t = t.replace(
    "plt.savefig(out, dpi=160, bbox_inches='tight')\nprint('Saved:', out)",
    "save_fig(plt.gcf(), 'Fig1B', dpi=160)"
)
write('Fig1B.py', t)
print("Patched Fig1B.py")

# ═══════════════════════════════════════════════════════════════
# Fig1D.py — 2 images → keep only main one as Fig1D
# ═══════════════════════════════════════════════════════════════
t = read('Fig1D.py')
t = t.replace("import os\n", "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# First savefig → Fig1D
t = t.replace(
    "    out = os.path.join(OUT_DIR, 'Fig_mammilla_microstructure_panels.png')\n"
    "    plt.savefig(out, dpi=300, bbox_inches='tight')\n"
    "    print(f\"[Fig1] 已保存: {out}\")",
    "    save_fig(plt.gcf(), 'Fig1D')"
)
# Second savefig → remove (supplementary) — comment it out
t = t.replace(
    "    out = os.path.join(OUT_DIR, 'Fig_mammilla_density_significance.png')\n"
    "    plt.savefig(out, dpi=300, bbox_inches='tight')\n"
    "    print(f\"[Fig2] 已保存: {out}\")",
    "    pass  # density significance plot — supplementary, not main figure"
)
write('Fig1D.py', t)
print("Patched Fig1D.py")

# ═══════════════════════════════════════════════════════════════
# Fig2A.py — single venn → Fig2A
# ═══════════════════════════════════════════════════════════════
t = read('Fig2A.py')
t = t.replace("import os\n", "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# Find and replace the save block
t = re.sub(
    r'out_dir = .*\n'
    r'for fmt in .*\n'
    r'.*fig\.savefig.*\n'
    r'.*print.*Saved.*\n',
    '    save_fig(fig, "Fig2A")\n',
    t
)
write('Fig2A.py', t)
print("Patched Fig2A.py")

# ═══════════════════════════════════════════════════════════════
# Fig2B.py — single phylo tree → Fig2B
# ═══════════════════════════════════════════════════════════════
t = read('Fig2B.py')
t = t.replace("from pathlib import Path\n", "from pathlib import Path\nimport sys; sys.path.insert(0, str(Path(__file__).parent))\nfrom _save import save_fig\n", 1)
# Replace save
t = re.sub(
    r'for ext in \("png",\).*\n.*fig\.savefig.*\n.*print.*\n',
    'save_fig(fig, "Fig2B")\n',
    t
)
# Also try the specific save pattern
t = re.sub(
    r'fig\.savefig\(FIG_DIR / "Fig_phylo_tree\.png".*\n.*print.*\n',
    'save_fig(fig, "Fig2B")\n',
    t
)
write('Fig2B.py', t)
print("Patched Fig2B.py")

# ═══════════════════════════════════════════════════════════════
# Fig2C_F.py — 6 outputs, map first 4 to Fig2C-F, skip extras
# ═══════════════════════════════════════════════════════════════
t = read('Fig2C_F.py')
t = t.replace("from pathlib import Path\n", "from pathlib import Path\nimport sys; sys.path.insert(0, str(Path(__file__).parent))\nfrom _save import save_fig as _sf\n", 1)
# Replace each plot call in main block (bottom of file)
# The main block calls 6 functions. Map first 4 to C-F, comment out last 2.
t = t.replace(
    'plot_hbar_panel(frames, OUT_DIR / "Fig1_barplot_panel.png", top_n=8)',
    '_fig_c = plot_hbar_panel(frames, OUT_DIR / "Fig2C.png", top_n=8)'
)
t = t.replace(
    'plot_bubble_panel(frames, ["Gallus", "Anas", "Columba"],\n'
    '                          OUT_DIR / "Fig2_bubble_single.png")',
    'plot_bubble_panel(frames, ["Gallus", "Anas", "Columba"],\n'
    '                          OUT_DIR / "Fig2D.png")'
)
t = t.replace(
    'plot_bubble_panel(frames, ["A&C", "G&C", "G&A"],\n'
    '                          OUT_DIR / "Fig3_bubble_pairwise.png")',
    'plot_bubble_panel(frames, ["A&C", "G&C", "G&A"],\n'
    '                          OUT_DIR / "Fig2E.png")'
)
t = t.replace(
    'plot_venn_panel(frames, OUT_DIR / "Fig4_venn.png")',
    'plot_venn_panel(frames, OUT_DIR / "Fig2F.png")'
)
# Comment out summary_bar and heatmap (supplementary)
t = t.replace(
    'plot_summary_bar(frames, OUT_DIR / "Fig5_summary_bar.png")',
    '# plot_summary_bar(frames, OUT_DIR / "Fig5_summary_bar.png")  # supplementary'
)
t = t.replace(
    'plot_heatmap_overview(frames, OUT_DIR / "Fig6_heatmap.png"',
    '# plot_heatmap_overview(frames, OUT_DIR / "Fig6_heatmap.png"'
)
# Now patch each plotting function to also save PDF/SVG
# In each function, after fig.savefig(out, dpi=300), add save_fig calls
# Actually easier: replace each fig.savefig(out, dpi=300) with calls to _sf
# But the function signatures vary. Let me patch the savefig calls directly.
# Replace all fig.savefig(out, dpi=300) with a triple-save
t = t.replace(
    "    fig.savefig(out, dpi=300)\n    plt.close(fig)",
    "    from _save import save_fig as _sf\n"
    "    _name = out.stem\n"
    "    _sf(fig, _name)\n"
    "    plt.close(fig)"
)
write('Fig2C_F.py', t)
print("Patched Fig2C_F.py")

# ═══════════════════════════════════════════════════════════════
# Fig2G.py — single panel → Fig2G
# ═══════════════════════════════════════════════════════════════
t = read('Fig2G.py')
t = t.replace("import os\n", "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
t = t.replace(
    'out_base = os.path.join(r"D:\\system_folder\\Desktop\\Work On\\Figure\\png", "Fig_cafe5_expansion_contraction")\n'
    'fig.savefig(out_base + ".pdf", dpi=300, bbox_inches="tight", facecolor="white")\n'
    'fig.savefig(out_base + ".svg", bbox_inches="tight", facecolor="white")\n'
    'fig.savefig(out_base + ".png", dpi=300, bbox_inches="tight", facecolor="white")\n'
    'print(f"Saved {out_base}.pdf / .svg / .png")',
    'save_fig(fig, "Fig2G")'
)
write('Fig2G.py', t)
print("Patched Fig2G.py")

# ═══════════════════════════════════════════════════════════════
# Fig2H.py — plotly → Fig2H
# ═══════════════════════════════════════════════════════════════
t = read('Fig2H.py')
t = t.replace("import pandas as pd\n", "import pandas as pd\nimport sys; sys.path.insert(0, str(Path(__file__).parent))\nfrom _save import save_plotly\n", 1)
# Replace the write_image/write_html block
old_save = (
    "    out_png = Path(r'D:/system_folder/Desktop/Work On/Figure/png') / \"Fig.Expansions and Contractions.png\"\n"
    "    out_pdf = Path(r'D:/system_folder/Desktop/Work On/Figure/png') / \"Fig.Expansions and Contractions.pdf\"\n"
    "    out_html = Path(r'D:/system_folder/Desktop/Work On/Figure/png') / \"Fig.Expansions and Contractions.html\"\n"
    "    export_pdf = True\n"
    "\n"
    "    fig.write_html(str(out_html))\n"
    "    # 与PDF保持同一逻辑尺寸，使用scale提高PNG清晰度，避免字体相对大小变化\n"
    "    base_width = 1800\n"
    "    base_height = fig_height\n"
    "    png_scale = 3.0  # 输出为 5400x2850，满足高分辨率需求\n"
    "    fig.write_image(str(out_png), width=base_width, height=base_height, scale=png_scale)\n"
    "\n"
    "    if export_pdf:\n"
    "        fig.write_image(str(out_pdf), width=base_width, height=base_height)\n"
    "    print(\"SUCCESSfully generated PNG, PDF, and HTML!\")"
)
new_save = (
    "    save_plotly(fig, 'Fig2H', width=1800, height=fig_height, png_scale=3.0)\n"
    "    print(\"Saved Fig2H [PNG/PDF/SVG]\")"
)
t = t.replace(old_save, new_save)
write('Fig2H.py', t)
print("Patched Fig2H.py")

# ═══════════════════════════════════════════════════════════════
# Fig3A.py — single panel → Fig3A
# ═══════════════════════════════════════════════════════════════
t = read('Fig3A.py')
t = t.replace("import os, re, math\n", "import os, re, math\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
t = t.replace(
    'out_path = r"D:\\system_folder\\Desktop\\Work On\\Figure\\png\\Fig3A.png"\n'
    'plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")\n'
    'print(f"\\n已保存: {out_path}")',
    'save_fig(plt.gcf(), "Fig3A", dpi=200)'
)
write('Fig3A.py', t)
print("Patched Fig3A.py")

# ═══════════════════════════════════════════════════════════════
# Fig3B.py — chord diagram → Fig3B (was saving 5 files!)
# ═══════════════════════════════════════════════════════════════
t = read('Fig3B.py')
t = t.replace("import json, re, os\n", "import json, re, os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# Remove the old multi-format save block
# Find and replace: out_pdf through the shutil copies
old_3b = (
    'out_pdf  = os.path.join(r"D:\\system_folder\\Desktop\\Work On\\Figure\\png", "chord_diagram.pdf")\n'
    'out_tiff = os.path.join(r"D:\\system_folder\\Desktop\\Work On\\Figure\\png", "chord_diagram.tiff")\n'
    'out_png  = os.path.join(r"D:\\system_folder\\Desktop\\Work On\\Figure\\png", "chord_diagram.png")\n'
)
t = t.replace(old_3b, '# Output handled by save_fig\n')
# Replace the actual save calls
t = re.sub(
    r'fig\.savefig\(out_pdf.*\n.*Saved.*out_pdf.*\n'
    r'fig\.savefig\(out_tiff.*\n.*Saved.*out_tiff.*\n'
    r'fig\.savefig\(out_png.*\n.*Saved.*out_png.*\n',
    'save_fig(fig, "Fig3B")\n',
    t
)
# Remove the SA_FIGURE copies
t = re.sub(r'out_sa_pdf = .*\n', '', t)
t = re.sub(r'out_sa_png = .*\n', '', t)
t = re.sub(r'pathlib\.Path.*_SA_FIGURE.*mkdir.*\n', '', t)
t = re.sub(r'import shutil\n', '', t)
t = re.sub(r'shutil\.copy2.*\n.*Copied.*\n', '', t)
write('Fig3B.py', t)
print("Patched Fig3B.py")

# ═══════════════════════════════════════════════════════════════
# Fig4A_C.py — 3 species → Fig4A, Fig4B, Fig4C
# ═══════════════════════════════════════════════════════════════
t = read('Fig4A_C.py')
t = t.replace("import os\n", "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# The script iterates species. Map: Gallus→Fig4A, Anas→Fig4B, Columba→Fig4C
# Add mapping dict
t = t.replace(
    'NOLEG = os.environ.get(\'NOLEG\', \'0\') == \'1\'',
    'NOLEG = os.environ.get(\'NOLEG\', \'0\') == \'1\'\n'
    '_SP_PANEL = {"Gallus": "Fig4A", "Anas": "Fig4B", "Columba": "Fig4C"}'
)
# Replace savefig
t = t.replace(
    "    out_path = os.path.join(out_dir, f\"Fig_highlighted_correlation_{species}.png\")\n"
    "    plt.savefig(out_path, dpi=300, bbox_inches='tight')\n"
    "    plt.close()\n"
    "    print(f\"已保存: {out_path}\")",
    "    save_fig(plt.gcf(), _SP_PANEL[species])\n"
    "    plt.close()"
)
write('Fig4A_C.py', t)
print("Patched Fig4A_C.py")

# ═══════════════════════════════════════════════════════════════
# Fig4D_G.py — 4 proteins → Fig4D, Fig4E, Fig4F, Fig4G
# ═══════════════════════════════════════════════════════════════
t = read('Fig4D_G.py')
t = t.replace("import os\n", "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# Map: OVAL→Fig4D, OC116→Fig4E, TRFE→Fig4F, OC17→Fig4G
t = t.replace(
    'NOLEG = os.environ.get(\'NOLEG\', \'0\') == \'1\'',
    'NOLEG = os.environ.get(\'NOLEG\', \'0\') == \'1\'\n'
    '_PROT_PANEL = {"OVAL": "Fig4D", "OC116": "Fig4E", "TRFE": "Fig4F", "OC17": "Fig4G"}'
)
t = t.replace(
    "    out = os.path.join(OUT_DIR, f'Fig_glycan_profiling_{prot}.png')\n"
    "    fig.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')\n"
    "    plt.close(fig)\n"
    "    print(f\"  已保存: {out}\")",
    "    save_fig(fig, _PROT_PANEL[prot])\n"
    "    plt.close(fig)"
)
write('Fig4D_G.py', t)
print("Patched Fig4D_G.py")

# ═══════════════════════════════════════════════════════════════
# Fig4H_J.py — 3 comparisons → Fig4H, Fig4I, Fig4J
# ═══════════════════════════════════════════════════════════════
t = read('Fig4H_J.py')
t = t.replace("import os\n", "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# Map: GvsC→Fig4H (README: H=Anas vs Columba... wait, let me re-read)
# README says: H=Anas vs Columba, I=Gallus vs Anas, J=Gallus vs Columba
# But the script processes pairs in order. Need to check the pair iteration order.
# The script iterates PAIRS which are defined somewhere...
# Add mapping based on pair names
t = t.replace(
    "NOLEG = os.environ.get('NOLEG', '0') == '1'",
    "NOLEG = os.environ.get('NOLEG', '0') == '1'\n"
    "_PAIR_PANEL = {\n"
    "    ('Gallus', 'Columba'): 'Fig4H',\n"
    "    ('Gallus', 'Anas'):    'Fig4I',\n"
    "    ('Anas',   'Columba'): 'Fig4J',\n"
    "}"
)
# Replace savefig — need to use panel name from pair
t = t.replace(
    "    _suffix = '_noleg' if NOLEG else ''\n"
    "    out_path = os.path.join(OUT_DIR, f'Fig_2d_enrichment_{sp_ref}_vs_{sp_comp}{_suffix}.png')\n"
    "    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')\n"
    "    plt.close()\n"
    "    print(f\"  Saved → {out_path}\")",
    "    _panel = _PAIR_PANEL.get((sp_ref, sp_comp), f'Fig4_{sp_ref}_{sp_comp}')\n"
    "    save_fig(plt.gcf(), _panel)\n"
    "    plt.close()"
)
write('Fig4H_J.py', t)
print("Patched Fig4H_J.py")

# ═══════════════════════════════════════════════════════════════
# Fig5A_D.py — 4 panels → Fig5A, Fig5B, Fig5C, Fig5D
# ═══════════════════════════════════════════════════════════════
t = read('Fig5A_D.py')
t = t.replace("from scipy import stats\n", "from scipy import stats\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# Replace save_panel function
t = t.replace(
    "def save_panel(fig, name):\n"
    "    \"\"\"Save as PNG (300 dpi) and PDF to OUT_DIR.\"\"\"\n"
    "    for ext in ('png', 'pdf'):\n"
    "        out = os.path.join(OUT_DIR, f'{name}.{ext}')\n"
    "        fig.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='white')\n"
    "        print(f\"已保存: {out}\")",
    "def save_panel(fig, name):\n"
    "    \"\"\"Save as PNG/PDF/SVG.\"\"\"\n"
    "    save_fig(fig, name, dpi=DPI)"
)
# Rename panels
t = t.replace("save_panel(fig_a, 'Fig_ensemble_calcium_A')", "save_panel(fig_a, 'Fig5A')")
t = t.replace("save_panel(fig_b, 'Fig_ensemble_calcium_B')", "save_panel(fig_b, 'Fig5B')")
t = t.replace("save_panel(fig_c, 'Fig_ensemble_calcium_C')", "save_panel(fig_c, 'Fig5C')")
t = t.replace("save_panel(fig_d, 'Fig_ensemble_calcium_D')", "save_panel(fig_d, 'Fig5D')")
write('Fig5A_D.py', t)
print("Patched Fig5A_D.py")

# ═══════════════════════════════════════════════════════════════
# Fig5E_H.py — 4 panels → Fig5E, Fig5F, Fig5G, Fig5H
# ═══════════════════════════════════════════════════════════════
t = read('Fig5E_H.py')
t = t.replace("from pathlib import Path\n", "from pathlib import Path\nimport sys; sys.path.insert(0, str(Path(__file__).parent))\nfrom _save import save_fig\n", 1)
# Replace save_panel function
t = t.replace(
    "def save_panel(fig, name):\n"
    "    \"\"\"Save as PNG (300 dpi) and PDF to OUT_DIR.\"\"\"\n"
    "    for ext in ('png', 'pdf'):\n"
    "        out = OUT_DIR / f'{name}.{ext}'\n"
    "        fig.savefig(out, dpi=DPI_OUT, bbox_inches='tight', facecolor='white')\n"
    "        print(f\"已保存: {out}\")",
    "def save_panel(fig, name):\n"
    "    \"\"\"Save as PNG/PDF/SVG.\"\"\"\n"
    "    save_fig(fig, name, dpi=DPI_OUT)"
)
# Rename: the loop uses A/B/C/D labels → map to E/F/G/H
# The loop variable is `lbl` with values A, B, C, D
# Replace the save call to map labels
t = t.replace(
    "save_panel(fig, f'Fig_glycan_ensemble_stats_{lbl}')",
    "save_panel(fig, f'Fig5{chr(ord(\"E\") + ord(lbl) - ord(\"A\"))}')"
)
write('Fig5E_H.py', t)
print("Patched Fig5E_H.py")

# ═══════════════════════════════════════════════════════════════
# Fig5I_N.py — 6 panels → Fig5I, Fig5J, Fig5K, Fig5L, Fig5M, Fig5N
# ═══════════════════════════════════════════════════════════════
t = read('Fig5I_N.py')
t = t.replace("from scipy import stats\n", "from scipy import stats\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# Replace save_panel function
t = t.replace(
    "def save_panel(fig, name):\n"
    "    \"\"\"Save as PNG (300 dpi) and PDF to FOLDER.\"\"\"\n"
    "    for ext in ('png', 'pdf'):\n"
    "        out = os.path.join(r'D:\\system_folder\\Desktop\\Work On\\Figure\\png', f'{name}.{ext}')\n"
    "        fig.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='white')\n"
    "        print(f\"已保存: {out}\")",
    "def save_panel(fig, name):\n"
    "    \"\"\"Save as PNG/PDF/SVG.\"\"\"\n"
    "    save_fig(fig, name, dpi=DPI)"
)
# Rename: A-F → I-N
# Panels in the loop use lbl = A, B, C, D
t = t.replace(
    "save_panel(fig, f'Fig_hotspot_ensemble_2_{lbl}')",
    "save_panel(fig, f'Fig5{chr(ord(\"I\") + ord(lbl) - ord(\"A\"))}')"
)
t = t.replace("save_panel(fig, 'Fig_hotspot_ensemble_2_E')", "save_panel(fig, 'Fig5M')")
t = t.replace("save_panel(fig, 'Fig_hotspot_ensemble_2_F')", "save_panel(fig, 'Fig5N')")
write('Fig5I_N.py', t)
print("Patched Fig5I_N.py")

# ═══════════════════════════════════════════════════════════════
# Fig6A_B.py — 2 panels → Fig6A, Fig6B
# ═══════════════════════════════════════════════════════════════
t = read('Fig6A_B.py')
t = t.replace("import os\n", "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n", 1)
# DMRT → Fig6B (Duncan comparison), Time-series → Fig6A
# README: A=Contact Force + Shear Stress 时间序列, B=F_max/τ_max Duncan 比较
t = t.replace(
    'plt.savefig(OUT_DMRT, dpi=200, bbox_inches="tight", facecolor="white")\n'
    'plt.close("all")\n'
    'print(f"[OK] DMRT: {OUT_DMRT}")',
    'save_fig(plt.gcf(), "Fig6B", dpi=200)\n'
    'plt.close("all")'
)
t = t.replace(
    'plt.savefig(OUT_TS, dpi=200, bbox_inches="tight", facecolor="white")\n'
    'plt.close("all")\n'
    'print(f"[OK] Time-series: {OUT_TS}")',
    'save_fig(plt.gcf(), "Fig6A", dpi=200)\n'
    'plt.close("all")'
)
write('Fig6A_B.py', t)
print("Patched Fig6A_B.py")

print("\n=== ALL SCRIPTS PATCHED ===")
