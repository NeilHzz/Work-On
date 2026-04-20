"""
Batch-fix all Figure scripts: replace E: drive paths with D: paths,
redirect OUT_DIR to Figure/png, fix __file__-relative data references.
"""
import re

ROOT = r"D:\system_folder\Desktop\Work On"
PNG  = r"D:\system_folder\Desktop\Work On\Figure\png"

# ── Fig1D ──
with open("Fig1D.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(r"e:\Data\Desktop\Work On\乳突层形态结构\specie.xlsx",
              ROOT + r"\乳突层形态结构\specie.xlsx")
t = t.replace(r"e:\Data\Desktop\Work On\乳突层形态结构",
              PNG)
with open("Fig1D.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig1D.py")

# ── Fig2A ── uses __file__-relative Orthogroups.txt.gz.txt
with open("Fig2A.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    'ortho_file = os.path.join(os.path.dirname(__file__), "Orthogroups.txt.gz.txt")',
    f'ortho_file = r"{ROOT}\\Ortho\\Orthogroups.txt.gz.txt"'
)
# redirect output
t = t.replace(
    'out_dir = os.path.dirname(__file__)',
    f'out_dir = r"{PNG}"'
)
with open("Fig2A.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig2A.py")

# ── Fig2B ── uses __file__-relative Species_phylogenetic_tree.nwk.gz
with open("Fig2B.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    'SRC     = ROOT / "Species_phylogenetic_tree.nwk.gz"',
    f'SRC     = Path(r"{ROOT}/Ortho/Phylogenetic/Species_phylogenetic_tree.nwk.gz")'
)
t = t.replace(
    'FIG_DIR = ROOT.parent / "Phylogenetic"',
    f'FIG_DIR = Path(r"{PNG}")'
)
with open("Fig2B.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig2B.py")

# ── Fig2C_F ── DATA_DIR = ROOT.parent  and enrichment in Ortho/Venn GO
with open("Fig2C_F.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    'DATA_DIR = ROOT.parent',
    f'DATA_DIR = Path(r"{ROOT}/Ortho/Venn GO")'
)
t = t.replace(
    'OUT_DIR  = ROOT / "NC_Figures"',
    f'OUT_DIR  = Path(r"{PNG}")'
)
with open("Fig2C_F.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig2C_F.py")

# ── Fig2H ── e:/Data/Desktop/Work On/Ortho/Expansions Contractions Results
with open("Fig2H.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    r"e:/Data/Desktop/Work On/Ortho/Expansions Contractions Results",
    ROOT.replace("\\", "/") + "/Ortho/Expansions Contractions Results"
)
with open("Fig2H.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig2H.py")

# ── Fig3A ── BASE = e:\Data\Desktop\Work On   and out_path
with open("Fig3A.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    r'BASE = r"e:\Data\Desktop\Work On"',
    f'BASE = r"{ROOT}"'
)
# Also fix the Orthogroups path – script uses os.path.join(BASE, "Ortho", ...)
# Fix output path
t = t.replace(
    r'out_path = r"e:\Data\Desktop\Work On\Sci_Adv_Figure\Fig_glycan_network.png"',
    f'out_path = r"{PNG}\\Fig3A.png"'
)
with open("Fig3A.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig3A.py")

# ── Fig3B ── uses _SCRIPT_DIR-relative files, needs blast/ data
with open("Fig3B.py", "r", encoding="utf-8") as f:
    t = f.read()
BLAST = ROOT + r"\blast"
t = t.replace(
    '_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))',
    f'_SCRIPT_DIR = r"{BLAST}"'
)
t = t.replace(
    r'_SA_FIGURE = r"e:\Data\Desktop\Work On\Sci_Adv_Figure"',
    f'_SA_FIGURE = r"{PNG}"'
)
# Fix the output paths that use _SCRIPT_DIR for saving
t = t.replace(
    'out_pdf  = os.path.join(_SCRIPT_DIR, "chord_diagram.pdf")',
    f'out_pdf  = os.path.join(r"{PNG}", "chord_diagram.pdf")'
)
t = t.replace(
    'out_tiff = os.path.join(_SCRIPT_DIR, "chord_diagram.tiff")',
    f'out_tiff = os.path.join(r"{PNG}", "chord_diagram.tiff")'
)
t = t.replace(
    'out_png  = os.path.join(_SCRIPT_DIR, "chord_diagram.png")',
    f'out_png  = os.path.join(r"{PNG}", "chord_diagram.png")'
)
with open("Fig3B.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig3B.py")

# ── Fig4A_C ──
with open("Fig4A_C.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    r'data_dir = r"e:\Data\Desktop\Work On\Raw_Data\MS_DATA"',
    f'data_dir = r"{ROOT}\\Raw_Data\\MS_DATA"'
)
t = t.replace(
    'out_dir = r"e:\\Data\\Desktop\\Work On\\\u7cd6\u86cb\u767d\u548c\u86cb\u767d\u8054\u5408\u5206\u6790\\Figure"',
    f'out_dir = r"{PNG}"'
)
with open("Fig4A_C.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig4A_C.py")

# ── Fig4D_G ──
with open("Fig4D_G.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    r'DATA_DIR = r"e:\Data\Desktop\Work On\Raw_Data\MS_DATA"',
    f'DATA_DIR = r"{ROOT}\\Raw_Data\\MS_DATA"'
)
t = t.replace(
    'OUT_DIR  = r"e:\\Data\\Desktop\\Work On\\\u7cd6\u86cb\u767d\u548c\u86cb\u767d\u8054\u5408\u5206\u6790\\Figure"',
    f'OUT_DIR  = r"{PNG}"'
)
with open("Fig4D_G.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig4D_G.py")

# ── Fig4H_J ──
with open("Fig4H_J.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    r'BASE           = r"e:\Data\Desktop\Work On"',
    f'BASE           = r"{ROOT}"'
)
with open("Fig4H_J.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig4H_J.py")

# ── Fig5A_D ──
with open("Fig5A_D.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    r'FOLDER  = r"E:\Data\Desktop\Work On\ReGlyco_Ensemble"',
    f'FOLDER  = r"{ROOT}\\ReGlyco_Ensemble"'
)
t = t.replace('OUT_DIR = FOLDER', f'OUT_DIR = r"{PNG}"')
with open("Fig5A_D.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig5A_D.py")

# ── Fig5E_H ──
with open("Fig5E_H.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    r"CSV_DIR = Path(r'E:\Data\Desktop\Work On\ReGlyco_Ensemble\csv')",
    f"CSV_DIR = Path(r'{ROOT}\\ReGlyco_Ensemble\\csv')"
)
t = t.replace(
    r"OUT_DIR = Path(r'E:\Data\Desktop\Work On\ReGlyco_Ensemble')",
    f"OUT_DIR = Path(r'{PNG}')"
)
with open("Fig5E_H.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig5E_H.py")

# ── Fig5I_N ──
with open("Fig5I_N.py", "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace(
    r'FOLDER  = r"E:\Data\Desktop\Work On\ReGlyco_Ensemble"',
    f'FOLDER  = r"{ROOT}\\ReGlyco_Ensemble"'
)
t = t.replace(
    "OUT_PNG = os.path.join(FOLDER, \"Fig_hotspot_ensemble_2.png\")",
    f"OUT_PNG = os.path.join(r\"{PNG}\", \"Fig5I_N.png\")"
)
with open("Fig5I_N.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig5I_N.py")

# ── Fig6A_B ── uses __file__-relative combined_rcforc_yforce.xlsx
with open("Fig6A_B.py", "r", encoding="utf-8") as f:
    t = f.read()
FORCE_DIR = ROOT + r"\20260325力学结果"
t = t.replace(
    'XLSX       = os.path.join(SCRIPT_DIR, "combined_rcforc_yforce.xlsx")',
    f'XLSX       = r"{FORCE_DIR}\\combined_rcforc_yforce.xlsx"'
)
t = t.replace(
    r'OUT_DIR    = r"e:\Data\Desktop\Work On\Sci_Adv_Figure"',
    f'OUT_DIR    = r"{PNG}"'
)
with open("Fig6A_B.py", "w", encoding="utf-8") as f:
    f.write(t)
print("Fixed Fig6A_B.py")

print("\n=== ALL DONE ===")
