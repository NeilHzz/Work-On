"""
Master runner: re-generate all visualization figures with SA font settings,
then copy everything to Sci_Adv_Figure/.
"""
import os, shutil, subprocess, sys

PYTHON = r"E:/PY310/python.exe"
BASE   = r"e:\Data\Desktop\Work On"
OUT    = os.path.join(BASE, "Sci_Adv_Figure")
os.makedirs(OUT, exist_ok=True)

# (script_path, cwd, expected_outputs)
SCRIPTS = [
    # 糖蛋白和蛋白联合分析
    (r"糖蛋白和蛋白联合分析\Fig_2d_enrichment_all_pairs_visualization.py",
     r"糖蛋白和蛋白联合分析", None),
    (r"糖蛋白和蛋白联合分析\Fig_glycan_profiling_visualization.py",
     r"糖蛋白和蛋白联合分析", None),
    (r"糖蛋白和蛋白联合分析\Fig_highlighted_proteins_visualization.py",
     r"糖蛋白和蛋白联合分析", None),
    (r"糖蛋白和蛋白联合分析\Fig_single_species_correlation_visualization.py",
     r"糖蛋白和蛋白联合分析", None),
    # Ortho
    (r"Ortho\Fig_venn_orthogroups_visualization.py",
     r"Ortho", None),
    (r"Ortho\Expansions Contractions Results\Fig_cafe5_tree_visualization.py",
     r"Ortho\Expansions Contractions Results", None),
    (r"Ortho\Phylogenetic\Fig_phylo_tree_visualization.py",
     r"Ortho\Phylogenetic", None),
    (r"Ortho\Venn GO\常规气泡图\Fig_venn_go_visualization.py",
     r"Ortho\Venn GO\常规气泡图", None),
    # ReGlyco_Ensemble
    (r"ReGlyco_Ensemble\Fig_ensemble_visualization.py",
     r"ReGlyco_Ensemble", None),
    (r"ReGlyco_Ensemble\Fig_glycan_ensemble_stats_visualization.py",
     r"ReGlyco_Ensemble", None),
    (r"ReGlyco_Ensemble\Fig_hotspot_ensemble_1_visualization.py",
     r"ReGlyco_Ensemble", None),
    (r"ReGlyco_Ensemble\Fig_hotspot_ensemble_2_visualization.py",
     r"ReGlyco_Ensemble", None),
    # 乳突层形态结构
    (r"乳突层形态结构\Fig_mammilla_structure_visualization.py",
     r"乳突层形态结构", None),
    # 同源糖型蛋白
    (r"同源糖型蛋白圆环大图\Fig_glycan_network_visualization.py",
     r"同源糖型蛋白圆环大图", None),
]

print("=" * 60)
print("Running all visualization scripts (Times New Roman font)")
print("=" * 60)

ok_scripts = []
fail_scripts = []

for rel_script, rel_cwd, _ in SCRIPTS:
    script_path = os.path.join(BASE, rel_script)
    cwd_path    = os.path.join(BASE, rel_cwd)
    if not os.path.exists(script_path):
        print(f"[MISS] {rel_script}")
        fail_scripts.append(rel_script)
        continue
    print(f"\n[RUN]  {os.path.basename(rel_script)}")
    result = subprocess.run(
        [PYTHON, script_path],
        cwd=cwd_path,
        capture_output=True, text=True, timeout=300,
        encoding='utf-8', errors='replace'
    )
    if result.returncode == 0:
        print(f"  [OK]")
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n')[:5]:
                print(f"  >> {line}")
        ok_scripts.append(rel_script)
    else:
        print(f"  [FAIL] rc={result.returncode}")
        err = (result.stderr or result.stdout)[-500:].strip()
        print(f"  {err}")
        fail_scripts.append(rel_script)

print("\n" + "=" * 60)
print(f"Scripts OK: {len(ok_scripts)} / {len(SCRIPTS)}")
if fail_scripts:
    print("Failed:")
    for f in fail_scripts: print(f"  - {f}")

# ─────────────────────────────────────────────────────────────
# Copy all PNG/PDF/SVG outputs to Sci_Adv_Figure
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Collecting figures to Sci_Adv_Figure")
print("=" * 60)

EXTS = {'.png', '.pdf', '.svg'}
copied = 0
for root, dirs, files in os.walk(BASE):
    # Skip the output dir itself and the __pycache__ / 0_ unused dirs
    rel_root = os.path.relpath(root, BASE)
    if rel_root.startswith('Sci_Adv_Figure'):
        continue
    if '0_' in rel_root or '__pycache__' in rel_root:
        continue
    for fname in files:
        ext = os.path.splitext(fname)[1].lower()
        if ext not in EXTS:
            continue
        # Only copy files whose names start with "Fig_" or match our patterns
        if not (fname.startswith('Fig_') or fname.startswith('fig_') or
                fname.startswith('venn_go') or fname.startswith('panel_')):
            continue
        src = os.path.join(root, fname)
        dst = os.path.join(OUT, fname)
        try:
            shutil.copy2(src, dst)
            print(f"  -> {fname}")
            copied += 1
        except Exception as e:
            print(f"  [ERR] {fname}: {e}")

print(f"\nCopied {copied} files to {OUT}")
print("\nDone.")
