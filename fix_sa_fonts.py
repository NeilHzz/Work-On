"""
Fix all visualization scripts to use Times New Roman (SA requirement).
Modifies files in-place.
"""
import re, os

SCRIPTS = [
    r"e:\Data\Desktop\Work On\Ortho\Fig_venn_orthogroups_visualization.py",
    r"e:\Data\Desktop\Work On\Ortho\Expansions Contractions Results\Fig_cafe5_tree_visualization.py",
    r"e:\Data\Desktop\Work On\Ortho\Phylogenetic\Fig_phylo_tree_visualization.py",
    r"e:\Data\Desktop\Work On\Ortho\Venn GO\常规气泡图\Fig_venn_go_visualization.py",
    r"e:\Data\Desktop\Work On\乳突层形态结构\Fig_mammilla_structure_visualization.py",
    r"e:\Data\Desktop\Work On\同源糖型蛋白圆环大图\Fig_glycan_network_visualization.py",
    r"e:\Data\Desktop\Work On\糖蛋白和蛋白联合分析\Fig_2d_enrichment_all_pairs_visualization.py",
    r"e:\Data\Desktop\Work On\糖蛋白和蛋白联合分析\Fig_glycan_profiling_visualization.py",
    r"e:\Data\Desktop\Work On\糖蛋白和蛋白联合分析\Fig_highlighted_proteins_visualization.py",
    r"e:\Data\Desktop\Work On\糖蛋白和蛋白联合分析\Fig_single_species_correlation_visualization.py",
    r"e:\Data\Desktop\Work On\ReGlyco_Ensemble\Fig_ensemble_visualization.py",
    r"e:\Data\Desktop\Work On\ReGlyco_Ensemble\Fig_glycan_ensemble_stats_visualization.py",
    r"e:\Data\Desktop\Work On\ReGlyco_Ensemble\Fig_hotspot_ensemble_1_visualization.py",
    r"e:\Data\Desktop\Work On\ReGlyco_Ensemble\Fig_hotspot_ensemble_2_visualization.py",
]

# Regex patterns to replace font settings
FONT_PATTERNS = [
    # "font.family": "Arial"  (with any amount of whitespace around colon/value)
    (r'"font\.family"\s*:\s*"Arial"',          '"font.family": "Times New Roman"'),
    (r'"font\.family"\s*:\s*"[^"]*serif[^"]*"', '"font.family": "Times New Roman"'),
    # rcParams dict-style: 'font.family'] = 'sans-serif' or 'Arial'
    (r"rcParams\[.font\.family.\]\s*=\s*['\"](?:sans-serif|Arial|Helvetica)['\"]",
     "rcParams['font.family'] = 'Times New Roman'"),
    # mpl.rcParams['font.family'] = '...'
    (r"(mpl\.rcParams\[.font\.family.\])\s*=\s*['\"](?:sans-serif|Arial|Helvetica)['\"]",
     r"\1 = 'Times New Roman'"),
    # matplotlib.rcParams["font.family"] = "Arial"
    (r'(matplotlib\.rcParams\["font\.family"\])\s*=\s*"(?:Arial|sans-serif|Helvetica)"',
     r'\1 = "Times New Roman"'),
    # plt.rcParams["font.family"] = "..."
    (r'(plt\.rcParams\["font\.family"\])\s*=\s*"(?:Arial|sans-serif|Helvetica)"',
     r'\1 = "Times New Roman"'),
    # DejaVu Sans in rcParams.update dict
    (r'"font\.family"\s*:\s*"DejaVu Sans"', '"font.family": "Times New Roman"'),
    # "font.family":    "DejaVu Sans"
    (r'"font\.family"\s*:\s*"(?:DejaVu Sans|Helvetica Neue)"',
     '"font.family": "Times New Roman"'),
]

# For scripts that need font.family added (no existing setting)
NEEDS_INSERT = [
    r"e:\Data\Desktop\Work On\ReGlyco_Ensemble\Fig_ensemble_visualization.py",
    r"e:\Data\Desktop\Work On\ReGlyco_Ensemble\Fig_glycan_ensemble_stats_visualization.py",
    r"e:\Data\Desktop\Work On\ReGlyco_Ensemble\Fig_hotspot_ensemble_1_visualization.py",
    r"e:\Data\Desktop\Work On\ReGlyco_Ensemble\Fig_hotspot_ensemble_2_visualization.py",
    r"e:\Data\Desktop\Work On\乳突层形态結构\Fig_mammilla_structure_visualization.py",  # may vary
]

INSERT_LINE = 'import matplotlib\nmatplotlib.rcParams["font.family"] = "Times New Roman"\n'

for fpath in SCRIPTS:
    if not os.path.exists(fpath):
        print(f"[SKIP] {os.path.basename(fpath)} — not found")
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    changed = False

    # Apply all font replacements
    for pattern, replacement in FONT_PATTERNS:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            changed = True

    # Check if font.family is now set to Times New Roman
    has_tnr = 'Times New Roman' in content and 'font.family' in content
    if not has_tnr:
        # Need to insert font setting after first matplotlib/plt import
        # Find the last import line and insert after it
        import_match = list(re.finditer(r'^import matplotlib[^\n]*\n', content, re.MULTILINE))
        if import_match:
            pos = import_match[-1].end()
            content = content[:pos] + 'matplotlib.rcParams["font.family"] = "Times New Roman"\n' + content[pos:]
            changed = True
        else:
            # Try plt import
            import_match2 = list(re.finditer(r'^import matplotlib\.pyplot as plt\n', content, re.MULTILINE))
            if import_match2:
                pos = import_match2[-1].end()
                content = content[:pos] + 'import matplotlib\nmatplotlib.rcParams["font.family"] = "Times New Roman"\n' + content[pos:]
                changed = True

    # Also handle mammilla script: has plt.rcParams['font.sans-serif'] but no font.family
    # Add font.family = Times New Roman before the sans-serif line
    content = re.sub(
        r"(plt\.rcParams\['font\.sans-serif'\]\s*=\s*\[.*?\])",
        r'plt.rcParams["font.family"] = "Times New Roman"\n\1',
        content
    )
    if content != original:
        changed = True

    if changed:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK]  {os.path.basename(fpath)}")
    else:
        print(f"[--]  {os.path.basename(fpath)} — no changes needed")

print("\nDone fixing fonts.")
