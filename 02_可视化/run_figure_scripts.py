"""
Science Advances Figure Generator
運行所有可視化腳本，將生成的圖片統一複製至 Sci_Adv_Figure 文件夾。
"""

import subprocess
import shutil
import sys
import os
from pathlib import Path

ROOT    = Path(r"D:\system_folder\Desktop\Work On")
OUT_DIR = ROOT / "02_可视化" / "Sci_Adv_Figure"
OUT_DIR.mkdir(exist_ok=True)

PYTHON  = r"python"

# ── 所有可視化腳本列表 ───────────────────────────────────────────
SCRIPTS = [
    ROOT / "01_数据与计算" / "乳突层形态结构"             / "Fig_mammilla_structure_visualization.py",
    ROOT / "01_数据与计算" / "Ortho"                        / "Fig_venn_orthogroups_visualization.py",
    ROOT / "01_数据与计算" / "Ortho" / "Expansions Contractions Results" / "Fig_cafe5_tree_visualization.py",
    ROOT / "01_数据与计算" / "Ortho" / "Phylogenetic"       / "Fig_phylo_tree_visualization.py",
    ROOT / "01_数据与计算" / "Ortho" / "Venn GO" / "常规气泡图" / "Fig_venn_go_visualization.py",
    ROOT / "01_数据与计算" / "同源糖型蛋白圆环大图"         / "Fig_glycan_network_visualization.py",
    ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析"         / "Fig_2d_enrichment_all_pairs_visualization.py",
    ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析"         / "Fig_glycan_profiling_visualization.py",
    ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析"         / "Fig_highlighted_proteins_visualization.py",
    # Fig_single_species_correlation_visualization.py — removed from output
    ROOT / "01_数据与计算" / "ReGlyco_Ensemble"             / "Fig_ensemble_visualization.py",
    ROOT / "01_数据与计算" / "ReGlyco_Ensemble"             / "Fig_glycan_ensemble_stats_visualization.py",
    ROOT / "01_数据与计算" / "ReGlyco_Ensemble"             / "Fig_hotspot_ensemble_1_visualization.py",
    ROOT / "01_数据与计算" / "ReGlyco_Ensemble"             / "Fig_hotspot_ensemble_2_visualization.py",
]

# ── 腳本運行後的預期輸出文件（PNG/PDF/SVG）────────────────────────
# key = 腳本 stem, value = list of expected output paths
SCRIPT_OUTPUTS = {
    "Fig_mammilla_structure_visualization": [
        ROOT / "01_数据与计算" / "乳突层形态结构" / "Fig_mammilla_microstructure_panels.png",
        # Fig_mammilla_density_significance.png disabled
    ],
    "Fig_venn_orthogroups_visualization": [
        ROOT / "01_数据与计算" / "Ortho" / "Fig_venn_orthogroups.pdf",
        ROOT / "01_数据与计算" / "Ortho" / "Fig_venn_orthogroups.svg",
        ROOT / "01_数据与计算" / "Ortho" / "Fig_venn_orthogroups.png",
    ],
    "Fig_cafe5_tree_visualization": [
        ROOT / "01_数据与计算" / "Ortho" / "Expansions Contractions Results" / "Fig_cafe5_expansion_contraction.pdf",
        ROOT / "01_数据与计算" / "Ortho" / "Expansions Contractions Results" / "Fig_cafe5_expansion_contraction.svg",
        ROOT / "01_数据与计算" / "Ortho" / "Expansions Contractions Results" / "Fig_cafe5_expansion_contraction.png",
    ],
    "Fig_venn_go_visualization": [],           # outputs to NC_Figures subfolder — scanned below
    "Fig_glycan_network_visualization": [
        Path(r"D:\system_folder\Desktop\Work On\01_数据与计算\同源糖型蛋白圆环大图\Fig_glycan_network.png"),
    ],
    "Fig_2d_enrichment_all_pairs_visualization": [
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_2d_enrichment_Gallus_vs_Columba.png",
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_2d_enrichment_Gallus_vs_Anas.png",
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_2d_enrichment_Anas_vs_Columba.png",
    ],
    "Fig_glycan_profiling_visualization": [
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_glycan_profiling_OVAL.png",
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_glycan_profiling_OC116.png",
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_glycan_profiling_TRFE.png",
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_glycan_profiling_OC17.png",
    ],
    "Fig_highlighted_proteins_visualization": [
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_highlighted_correlation_Gallus.png",
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_highlighted_correlation_Anas.png",
        ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure" / "Fig_highlighted_correlation_Columba.png",
    ],
    "Fig_single_species_correlation_visualization": [],   # scanned below
    "Fig_ensemble_visualization": [
        ROOT / "01_数据与计算" / "ReGlyco_Ensemble" / "Fig_ensemble_calcium.png",
    ],
    "Fig_glycan_ensemble_stats_visualization": [
        ROOT / "01_数据与计算" / "ReGlyco_Ensemble" / "Fig_glycan_ensemble_stats.png",
    ],
    "Fig_hotspot_ensemble_1_visualization": [
        ROOT / "01_数据与计算" / "ReGlyco_Ensemble" / "Fig_hotspot_ensemble_1.png",
    ],
    "Fig_hotspot_ensemble_2_visualization": [
        ROOT / "01_数据与计算" / "ReGlyco_Ensemble" / "Fig_hotspot_ensemble_2.png",
    ],
}

# ── scan folders for scripts with unknown outputs ────────────────
SCAN_DIRS = {
    "Fig_venn_go_visualization": ROOT / "01_数据与计算" / "Ortho" / "Venn GO" / "常规气泡图" / "NC_Figures",
    "Fig_single_species_correlation_visualization": ROOT / "01_数据与计算" / "糖蛋白和蛋白联合分析" / "Figure",
    "Fig_phylo_tree_visualization": ROOT / "01_数据与计算" / "Ortho" / "Phylogenetic",
}

def run_script(script: Path) -> bool:
    if not script.exists():
        print(f"  [SKIP] not found: {script}")
        return False
    print(f"\n{'='*60}")
    print(f"Running: {script.name}")
    result = subprocess.run(
        [PYTHON, str(script)],
        cwd=str(script.parent),
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print(f"  [ERROR] exit={result.returncode}")
        print(result.stderr[-800:] if result.stderr else "")
    else:
        print(f"  [OK]")
        if result.stdout:
            print(result.stdout[-300:])
    return result.returncode == 0


EXT_SUBDIR = {".png": "PNG", ".svg": "SVG", ".pdf": "PDF"}

def collect_and_copy(script: Path):
    stem = script.stem
    files = list(SCRIPT_OUTPUTS.get(stem, []))

    # scan dirs
    scan_dir = SCAN_DIRS.get(stem)
    if scan_dir and scan_dir.exists():
        files += [f for f in scan_dir.glob("*.png")] + \
                 [f for f in scan_dir.glob("*.pdf")] + \
                 [f for f in scan_dir.glob("*.svg")]

    copied = 0
    for src in files:
        src = Path(src)
        if src.exists():
            sub = EXT_SUBDIR.get(src.suffix.lower(), "PNG")
            dest_dir = OUT_DIR / sub
            dest_dir.mkdir(exist_ok=True)
            shutil.copy2(src, dest_dir / src.name)
            print(f"  copied → {sub}/{src.name}")
            copied += 1
        else:
            print(f"  [missing] {src.name}")
    return copied


if __name__ == "__main__":
    print(f"Output directory: {OUT_DIR}\n")
    total_copied = 0

    for script in SCRIPTS:
        ok = run_script(script)
        if ok:
            n = collect_and_copy(script)
            total_copied += n

    print(f"\n{'='*60}")
    print(f"Done. {total_copied} figure file(s) copied to:\n  {OUT_DIR}")
    print(f"\nFiles in Sci_Adv_Figure:")
    for f in sorted(OUT_DIR.iterdir()):
        print(f"  {f.name}")
