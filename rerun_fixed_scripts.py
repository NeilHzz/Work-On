"""
Re-run the 8 scripts that had font issues fixed, then recopy outputs.
"""
import os, shutil, subprocess

PYTHON = r"E:/PY310/python.exe"
BASE   = r"e:\Data\Desktop\Work On"
OUT    = os.path.join(BASE, "Sci_Adv_Figure")

SCRIPTS = [
    (r"乳突层形态结构\Fig_mammilla_structure_visualization.py",       r"乳突层形态结构"),
    (r"Ortho\Expansions Contractions Results\Fig_cafe5_tree_visualization.py", r"Ortho\Expansions Contractions Results"),
    (r"Ortho\Phylogenetic\Fig_phylo_tree_visualization.py",            r"Ortho\Phylogenetic"),
    (r"Ortho\Venn GO\常规气泡图\Fig_venn_go_visualization.py",         r"Ortho\Venn GO\常规气泡图"),
    (r"糖蛋白和蛋白联合分析\Fig_2d_enrichment_all_pairs_visualization.py",  r"糖蛋白和蛋白联合分析"),
    (r"糖蛋白和蛋白联合分析\Fig_glycan_profiling_visualization.py",          r"糖蛋白和蛋白联合分析"),
    (r"糖蛋白和蛋白联合分析\Fig_highlighted_proteins_visualization.py",       r"糖蛋白和蛋白联合分析"),
    (r"糖蛋白和蛋白联合分析\Fig_single_species_correlation_visualization.py", r"糖蛋白和蛋白联合分析"),
]

ok, fail = [], []
for rel_script, rel_cwd in SCRIPTS:
    sp = os.path.join(BASE, rel_script)
    cw = os.path.join(BASE, rel_cwd)
    name = os.path.basename(rel_script)
    print(f"\n[RUN] {name}")
    r = subprocess.run([PYTHON, sp], cwd=cw, capture_output=True, text=True,
                       timeout=300, encoding='utf-8', errors='replace')
    if r.returncode == 0:
        print(f"  [OK]")
        for line in r.stdout.strip().split('\n')[:3]:
            if line.strip(): print(f"  >> {line}")
        ok.append(name)
    else:
        print(f"  [FAIL] rc={r.returncode}")
        err = ((r.stderr or '') + (r.stdout or ''))[-600:].strip()
        print(f"  {err}")
        fail.append(name)

print(f"\nOK: {len(ok)}  FAIL: {len(fail)}")
for f in fail: print(f"  - {f}")

# Recopy all new outputs
print("\n[COPY] Updating Sci_Adv_Figure...")
EXTS = {'.png', '.pdf', '.svg'}
copied = 0
for root, dirs, files in os.walk(BASE):
    rel = os.path.relpath(root, BASE)
    if rel.startswith('Sci_Adv_Figure') or '0_' in rel or '__pycache__' in rel:
        continue
    for fname in files:
        if os.path.splitext(fname)[1].lower() not in EXTS:
            continue
        if not (fname.startswith('Fig_') or fname.startswith('fig_') or
                fname.startswith('venn_go') or fname.startswith('panel_')):
            continue
        src = os.path.join(root, fname)
        dst = os.path.join(OUT, fname)
        shutil.copy2(src, dst)
        print(f"  -> {fname}")
        copied += 1

print(f"\nCopied/updated {copied} files.")
