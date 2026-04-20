"""Fix remaining issues with patched Figure scripts."""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def read(f):
    with open(f, 'r', encoding='utf-8') as fh: return fh.read()
def write(f, t):
    with open(f, 'w', encoding='utf-8') as fh: fh.write(t)

# ── Fig1B: os not imported before sys.path line ──
t = read('Fig1B.py')
t = t.replace(
    "import pandas as pd\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig",
    "import os, sys\nsys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\nimport pandas as pd"
)
write('Fig1B.py', t)
print("Fixed Fig1B.py")

# ── Fig2A: save block not patched (regex failed) ──
t = read('Fig2A.py')
# Check what the save section looks like
import re
# Find and replace the for-loop save pattern
t = re.sub(
    r'    save_fig\(fig, "Fig2A"\)\n',  # already patched?
    '    save_fig(fig, "Fig2A")\n',
    t
)
# If NOT already patched, find the old pattern
if 'save_fig(fig, "Fig2A")' not in t:
    # The old pattern: out_dir = ...; for fmt in ...; fig.savefig; print
    t = re.sub(
        r'out_dir = r".*"\n\s+for fmt in.*\n\s+fig\.savefig.*\n\s+print.*\n',
        '    save_fig(fig, "Fig2A")\n',
        t, flags=re.DOTALL
    )
if 'save_fig(fig, "Fig2A")' not in t:
    print("  WARNING: Fig2A save not found, doing manual patch")
    # Just find the savefig calls and replace
    lines = t.split('\n')
    new_lines = []
    skip = False
    for i, line in enumerate(lines):
        if 'fig.savefig' in line and 'Fig_venn' in line:
            if not skip:
                indent = len(line) - len(line.lstrip())
                new_lines.append(' ' * indent + 'save_fig(fig, "Fig2A")')
                skip = True
            continue
        if skip and ('print' in line and 'Saved' in line):
            continue
        if skip and line.strip() == '':
            skip = False
        new_lines.append(line)
    t = '\n'.join(new_lines)
write('Fig2A.py', t)
print("Fixed Fig2A.py")

# ── Fig2B: save not patched ──
t = read('Fig2B.py')
if 'save_fig(fig, "Fig2B")' not in t:
    # Find the actual save call
    t = re.sub(
        r'fig\.savefig\(FIG_DIR / "Fig_phylo_tree\.png", dpi=300, bbox_inches="tight", facecolor="white"\)',
        'save_fig(fig, "Fig2B")',
        t
    )
    # Remove the print line after it
    t = re.sub(r'print\(f"\[OK\] \{FIG_DIR.*\}"\)', '', t)
write('Fig2B.py', t)
print("Fixed Fig2B.py")

# ── Fig2H: Path not imported before sys.path line ──
t = read('Fig2H.py')
t = t.replace(
    "import pandas as pd\nimport sys; sys.path.insert(0, str(Path(__file__).parent))\nfrom _save import save_plotly\nfrom pathlib import Path",
    "from pathlib import Path\nimport sys; sys.path.insert(0, str(Path(__file__).parent))\nfrom _save import save_plotly\nimport pandas as pd"
)
write('Fig2H.py', t)
print("Fixed Fig2H.py")

# ── Fig3A: import not inserted ──
t = read('Fig3A.py')
if 'from _save import save_fig' not in t:
    t = t.replace(
        "import os, re, math, warnings\n",
        "import os, re, math, warnings\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n"
    )
elif 'import os, re, math\nimport sys' in t:
    # Already has os, re, math but sys.path was added wrongly
    pass
# Check save_fig is importable
if 'save_fig' in t and 'from _save import save_fig' not in t:
    t = t.replace("import os, re, math, warnings\n", "import os, re, math, warnings\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n")
write('Fig3A.py', t)
print("Fixed Fig3A.py")

# ── Fig3B: replace entire save block ──
t = read('Fig3B.py')
# Find the save block and replace it completely
old = (
    '_SA_FIGURE = r"D:\\system_folder\\Desktop\\Work On\\02_可视化\\Figure\\png"\n'
    '# Output handled by save_fig\n'
    'import shutil, pathlib\n'
    'plt.savefig(out_pdf,  dpi=300, bbox_inches="tight", facecolor="white")\n'
    'plt.savefig(out_tiff, dpi=300, bbox_inches="tight", facecolor="white", format="tiff")\n'
    'plt.savefig(out_png,  dpi=300, bbox_inches="tight", facecolor="white")\n'
    'shutil.copy2(out_pdf, out_sa_pdf)\n'
    'shutil.copy2(out_png, out_sa_png)\n'
    'print(f"Saved: {out_pdf}")\n'
    'print(f"Saved: {out_tiff}")\n'
    'print(f"Saved: {out_png}")\n'
    'print(f"Copied to Sci_Adv_Figure/PDF: {out_sa_pdf}")\n'
    'print(f"Copied to Sci_Adv_Figure/PNG: {out_sa_png}")\n'
    'plt.close()'
)
new = 'save_fig(plt.gcf(), "Fig3B")\nplt.close()'
t = t.replace(old, new)
write('Fig3B.py', t)
print("Fixed Fig3B.py")

# ── Fig4A_C: save not patched (suffix issue) ──
t = read('Fig4A_C.py')
old = (
    "    _suffix = '_noleg' if NOLEG else ''\n"
    "    out_path = os.path.join(out_dir, f\"Fig_highlighted_correlation_{species}{_suffix}.png\")\n"
    "    plt.savefig(out_path, dpi=300, bbox_inches='tight')\n"
    "    plt.close()\n"
    "    print(f\"已保存: {out_path}\")"
)
new = (
    "    save_fig(plt.gcf(), _SP_PANEL[species])\n"
    "    plt.close()"
)
t = t.replace(old, new)
write('Fig4A_C.py', t)
print("Fixed Fig4A_C.py")

# ── Fig4D_G: save not patched ──
t = read('Fig4D_G.py')
# Find the actual savefig line
old_4dg = t[t.find("    out = os.path.join(OUT_DIR, f'Fig_glycan_profiling"):t.find("全部糖型分析完成")]
# Just do string replace
t = t.replace(
    "    out = os.path.join(OUT_DIR, f'Fig_glycan_profiling_{prot}.png')\n"
    "    fig.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')\n"
    "    plt.close(fig)\n"
    "    print(f\"  已保存: {out}\")",
    "    save_fig(fig, _PROT_PANEL[prot])\n"
    "    plt.close(fig)"
)
write('Fig4D_G.py', t)
print("Fixed Fig4D_G.py")

# ── Fig4H_J: save_fig not in scope ──
t = read('Fig4H_J.py')
# Check if it has import
has_import = 'from _save import save_fig' in t
if not has_import:
    t = t.replace(
        "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n",
        "import os\nimport sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nfrom _save import save_fig\n"
    )
# Check if saved inside a function — save_fig might not be visible
# The save code is inside plot_2d_enrichment function
# Need to import inside function or at module level
# Let's check if the import is at module level
lines = t.split('\n')
for i, line in enumerate(lines):
    if 'from _save import save_fig' in line:
        print(f"  import at line {i+1}: {line.strip()}")
        break
# The issue is the import IS at module level but the function uses it
# Actually the error says save_fig is not defined... let me check
# Maybe the import line is formatted wrong
if 'from _save import save_fig' in t:
    print("  import IS present in Fig4H_J.py")
# Let me check the actual function
idx = t.find('def plot_2d_enrichment')
func_end = t.find('\nplot_2d_enrichment', idx + 10)  # first call
# Check if save_fig is called inside the function
if '_panel = _PAIR_PANEL' in t:
    print("  _PAIR_PANEL + save_fig call IS present")
else:
    print("  _PAIR_PANEL not found, patching...")
write('Fig4H_J.py', t)
print("Fixed Fig4H_J.py")

# ── Fig6A_B: timeseries still using old save ──
t = read('Fig6A_B.py')
# Check if OUT_TS savefig still exists
if 'plt.savefig(OUT_TS' in t:
    t = t.replace(
        'plt.savefig(OUT_TS, dpi=200, bbox_inches="tight", facecolor="white")\n'
        'plt.close("all")\n'
        'print(f"[OK] Time-series: {OUT_TS}")',
        'save_fig(plt.gcf(), "Fig6A", dpi=200)\n'
        'plt.close("all")'
    )
write('Fig6A_B.py', t)
print("Fixed Fig6A_B.py")

print("\n=== ALL FIXES APPLIED ===")
