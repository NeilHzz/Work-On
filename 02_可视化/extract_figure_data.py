"""
从每张可视化图的计算过程中提取底层数据，保存为 xlsx 文件。
每张图对应一个或多个 Sheet，汇总至同名 xlsx。

输出目录：D:\system_folder\Desktop\Work On\02_可视化\Figure_Data_Tables\
  Fig1_Phylogenetic_Tree.xlsx
  Fig2_Gene_Family_Expansions_Contractions.xlsx
  Fig3_Glycan_Network.xlsx
  Fig4_2D_Enrichment_Gallus_vs_Columba.xlsx
  Fig5_Glycan_Profiling_OVAL.xlsx
  Fig6_Glycan_Profiling_OC116.xlsx
  Fig7_Glycan_Profiling_TRFE.xlsx
  Fig8_Glycan_Profiling_OC17.xlsx
  Fig9_Correlation_Gallus.xlsx
  Fig10_Correlation_Anas.xlsx
  Fig11_Correlation_Columba.xlsx
"""

import os, re, math, warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")

BASE        = Path(r"D:\system_folder\Desktop\Work On")
MS_DATA_DIR = BASE / "01_数据与计算" / "Raw_Data" / "MS_DATA"
FASTA_DIR   = BASE / "01_数据与计算" / "Raw_Data" / "原始fasta"
OUT_DIR     = BASE / "01_数据与计算" / "Figure_Data_Tables"
OUT_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# 通用工具
# ══════════════════════════════════════════════════════════════════════════
def save_xlsx(path: Path, sheets: dict):
    """将多个 DataFrame 写入同一 xlsx，sheets = {sheet_name: df}"""
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for name, df in sheets.items():
            df.to_excel(w, sheet_name=name[:31], index=False)
    print(f"  [OK] {path.name}")


def get_int_cols(df, prefix_list):
    cols = []
    for p in prefix_list:
        cols += [c for c in df.columns if p in c and "Intensity" in c]
    if not cols:
        cols = [c for c in df.columns if "Intensity" in c]
    return list(dict.fromkeys(cols))   # dedup while preserving order


INT_PREFIX = {
    "Gallus":  ["Intensity G"],
    "Anas":    ["Intensity A"],
    "Columba": ["Intensity C"],
}

# ══════════════════════════════════════════════════════════════════════════
# Fig 1  Phylogenetic Tree
# ══════════════════════════════════════════════════════════════════════════
def fig1_phylogenetic_tree():
    src = BASE / "01_数据与计算" / "Ortho" / "Phylogenetic" / "Species_phylogenetic_tree.nwk.gz"
    with open(src, "r", encoding="utf-8", errors="ignore") as f:
        nwk = f.read().strip()

    # 解析 Newick → 节点表
    nwk_clean = nwk.rstrip(";")
    records = []

    def parse(s, parent=""):
        s = s.strip()
        if s.startswith("("):
            depth = i = 0
            for i, c in enumerate(s):
                if c == "(":  depth += 1
                elif c == ")": depth -= 1
                if depth == 0: break
            inner = s[1:i]; rest = s[i+1:]
            parts, buf, d = [], "", 0
            for c in inner:
                if c == "(": d += 1
                elif c == ")": d -= 1
                if c == "," and d == 0:
                    parts.append(buf); buf = ""
                else:
                    buf += c
            parts.append(buf)
            m = re.match(r"([^:]*)?(?::(.+))?$", rest)
            name   = (m.group(1) or "").strip()
            length = float(m.group(2)) if m and m.group(2) else 0.0
            node_id = name or f"Internal_{len(records)+1}"
            records.append({"Node": node_id, "Parent": parent,
                             "Branch_Length_substitutions_per_site": length,
                             "Node_Type": "Internal"})
            for p in parts:
                parse(p, parent=node_id)
        else:
            m = re.match(r"([^:]+)?(?::(.+))?$", s)
            name   = (m.group(1) or "").strip()
            length = float(m.group(2)) if m and m.group(2) else 0.0
            records.append({"Node": name, "Parent": parent,
                             "Branch_Length_substitutions_per_site": length,
                             "Node_Type": "Leaf (Species)"})

    parse(nwk_clean)
    df_tree = pd.DataFrame(records)

    # 物种对比表（拓扑关系描述）
    topology_data = [
        {"Clade":       "Galloanserae",
         "Species_1":   "Gallus gallus",
         "Species_2":   "Anas platyrhynchos",
         "Relationship":"Sister taxa (precocial)",
         "Common_ancestor_node": "Internal_1"},
        {"Clade":       "Galloanserae + Columbiformes",
         "Species_1":   "Gallus/Anas clade",
         "Species_2":   "Columba livia",
         "Relationship":"Outgroup (altricial)",
         "Common_ancestor_node": "Root"},
    ]
    df_topo = pd.DataFrame(topology_data)

    df_summary = pd.DataFrame({
        "Species":              ["Gallus gallus", "Anas platyrhynchos", "Columba livia"],
        "Common_name":          ["Chicken", "Duck", "Pigeon"],
        "Reproductive_strategy":["Precocial", "Precocial", "Altricial"],
        "Color_in_figure":      ["#B54664", "#7895C1", "#F0C284"],
        "Branch_length_to_parent": [
            df_tree.loc[df_tree["Node"]=="Gallus",  "Branch_Length_substitutions_per_site"].values[0],
            df_tree.loc[df_tree["Node"]=="Anas",    "Branch_Length_substitutions_per_site"].values[0],
            df_tree.loc[df_tree["Node"]=="Columba", "Branch_Length_substitutions_per_site"].values[0],
        ],
        "Substitution_model":   ["JTT+CAT"]*3,
        "Inference_method":     ["Maximum Likelihood"]*3,
    })

    save_xlsx(OUT_DIR / "Fig1_Phylogenetic_Tree.xlsx", {
        "Node_Table":    df_tree,
        "Topology":      df_topo,
        "Species_Summary": df_summary,
    })


# ══════════════════════════════════════════════════════════════════════════
# Fig 2  Gene-family Expansions & Contractions
# ══════════════════════════════════════════════════════════════════════════
def parse_enrichment(filepath):
    rows = []
    if not Path(filepath).exists():
        return pd.DataFrame()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 5:
                cat = parts[3]
                ont = "Biological Process" if cat == "biological_process" else (
                      "Cellular Component" if cat == "cellular_component" else "Molecular Function")
                rows.append({
                    "GO_ID":           parts[0],
                    "Protein_count":   int(parts[1]),
                    "GO_description":  parts[2],
                    "GO_ontology":     ont,
                    "Raw_GO_category": cat,
                    "P_value":         float(parts[4]),
                })
    return pd.DataFrame(rows).sort_values("P_value")


def fig2_expansions_contractions():
    ec_dir = BASE / "01_数据与计算" / "Ortho" / "Expansions Contractions Results"

    # 1. Summary statistics
    df_summary = pd.read_csv(ec_dir / "network_sankey_summary.csv")
    df_summary.rename(columns={"Type": "Event_Type"}, inplace=True)

    # 2. GO detailed comparison across species
    df_go_comp = pd.read_csv(ec_dir / "go_detailed_comparison.csv")

    # 3. Per-species enrichment files → 合并为一张大表
    enrichment_rows = []
    for sp in ["Gallus", "Anas", "Pigeon"]:
        for event, label in [("E", "Expansion"), ("C", "Contraction")]:
            fp = ec_dir / sp / f"{event}_enrichment.txt"
            df_e = parse_enrichment(fp)
            if not df_e.empty:
                df_e.insert(0, "Species", sp)
                df_e.insert(1, "Event_Type", label)
                enrichment_rows.append(df_e)

    df_all_enrich = pd.concat(enrichment_rows, ignore_index=True) if enrichment_rows else pd.DataFrame()

    # 4. 集簇成员文件（expansion/contraction cluster lists）
    cluster_rows = []
    for sp in ["Gallus", "Anas", "Pigeon"]:
        for event, label in [("Expensions", "Expansion"), ("Contractions", "Contraction")]:
            fp = ec_dir / f"{sp}_{event}_se_cluster.txt"
            if fp.exists():
                with open(fp, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split("\t") if "\t" in line else line.split()
                            cluster_rows.append({
                                "Species":     sp,
                                "Event_Type":  label,
                                "Cluster_info": line,
                                "Part_1": parts[0] if len(parts) > 0 else "",
                                "Part_2": parts[1] if len(parts) > 1 else "",
                            })
    df_clusters = pd.DataFrame(cluster_rows) if cluster_rows else pd.DataFrame()

    save_xlsx(OUT_DIR / "Fig2_Gene_Family_Expansions_Contractions.xlsx", {
        "Summary_Statistics":  df_summary,
        "GO_Cross_Species":    df_go_comp,
        "GO_Enrichment_All":   df_all_enrich,
        "Cluster_Lists":       df_clusters,
    })


# ══════════════════════════════════════════════════════════════════════════
# Fig 3  Glycan Network
# ══════════════════════════════════════════════════════════════════════════
def load_gly_ids_fasta(fasta_path):
    ids = set()
    with open(fasta_path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith(">"):
                acc = line.split("|")[1].strip() if "|" in line else line[1:].split()[0].strip()
                ids.add(acc)
    return ids


GLYCAN_TYPES_ORDER = [
    "High Mannose", "Pauci-mannose", "Hybrid",
    "Complex-Plain", "Complex-Fucosylated", "Complex-Sialylated", "Other",
]


def classify_glycan_7(g):
    comp = {}
    for k in ("HexNAc", "Hex", "Fuc", "NeuAc"):
        m = re.search(rf"{k}\((\d+)\)", g)
        comp[k] = int(m.group(1)) if m else 0
    h, mn, f, s = comp["HexNAc"], comp["Hex"], comp["Fuc"], comp["NeuAc"]
    if h == 2 and mn >= 5 and f == 0 and s == 0: return "High Mannose"
    if h <= 2 and mn <= 4:                        return "Pauci-mannose"
    if h == 3 and mn >= 5:                        return "Hybrid"
    if h >= 3 and s >= 1:                         return "Complex-Sialylated"
    if h >= 3 and f >= 1 and s == 0:              return "Complex-Fucosylated"
    if h >= 3 and f == 0 and s == 0:              return "Complex-Plain"
    return "Other"


def fig3_glycan_network():
    ortho_path = BASE / "01_数据与计算" / "同源糖型蛋白圆环大图" / "Orthogroups.txt.gz.txt"

    gly_ids = {
        "Gallus":  load_gly_ids_fasta(FASTA_DIR / "GlyGallus.fasta"),
        "Anas":    load_gly_ids_fasta(FASTA_DIR / "GlyAnas.fasta"),
        "Columba": load_gly_ids_fasta(FASTA_DIR / "GlyColumba.fasta"),
    }

    # 解析 orthogroups
    protein_info = {}
    clustered = set()
    with open(ortho_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            sp_members = defaultdict(set)
            for token in re.split(r"\s+", line):
                if "|" in token:
                    sp, acc = token.split("|", 1)
                    sp_members[sp].add(acc)
            sp_present = set(sp_members.keys())
            gly_in_grp = {sp: sp_members[sp] & gly_ids[sp] for sp in sp_present}
            if sum(len(v) for v in gly_in_grp.values()) == 0:
                continue
            ct           = {3: "Three-species", 2: "Two-species"}.get(len(sp_present), "One-species")
            cluster_size = sum(len(v) for v in sp_members.values())
            for sp, accs in gly_in_grp.items():
                for acc in accs:
                    protein_info[acc] = {
                        "Protein_accession": acc,
                        "Species":           sp,
                        "Cluster_type":      ct,
                        "Species_in_cluster":"|".join(sorted(sp_present)),
                        "Cluster_size":      cluster_size,
                    }
                    clustered.add(acc)

    for sp in ["Gallus", "Anas", "Columba"]:
        for acc in gly_ids[sp]:
            if acc not in clustered:
                protein_info[acc] = {
                    "Protein_accession": acc,
                    "Species":           sp,
                    "Cluster_type":      "Singleton",
                    "Species_in_cluster": sp,
                    "Cluster_size":      1,
                }

    df_prot = pd.DataFrame(list(protein_info.values()))

    # 读取糖链数据
    prot_to_gtypes = defaultdict(set)
    glycan_chain_rows = []
    acc_sp = {}
    MS_FILES = {sp: MS_DATA_DIR / f"Glycan_MS_{sp}.xlsx" for sp in ["Gallus","Anas","Columba"]}
    for sp, fp in MS_FILES.items():
        df_igp = pd.read_excel(fp, sheet_name="IGP_quant")
        int_cols = get_int_cols(df_igp, INT_PREFIX[sp])
        for _, row in df_igp.iterrows():
            acc  = str(row["Protein accession"]).strip()
            gstr = str(row.get("Observed Modification", "")).strip()
            if not gstr or gstr == "nan":
                continue
            gt = classify_glycan_7(gstr)
            mean_int = pd.to_numeric(pd.Series([row[c] for c in int_cols if c in row.index]), errors="coerce").mean()
            glycan_chain_rows.append({
                "Species":            sp,
                "Protein_accession":  acc,
                "Glycan_string":      gstr,
                "Glycan_type":        gt,
                "Mean_Intensity":     float(mean_int) if not np.isnan(mean_int) else 0,
            })
            prot_to_gtypes[acc].add(gt)
            acc_sp[acc] = sp

    df_glycan = pd.DataFrame(glycan_chain_rows)

    # 蛋白-糖型关联表（每行: 蛋白 + 糖型 + cluster_type）
    link_rows = []
    for acc, gtypes in prot_to_gtypes.items():
        if acc in protein_info:
            for gt in gtypes:
                r = dict(protein_info[acc])
                r["Glycan_type"] = gt
                link_rows.append(r)
    df_links = pd.DataFrame(link_rows)

    # 糖型汇总统计
    gt_stats = []
    for gt in GLYCAN_TYPES_ORDER:
        prots = {acc for acc, gts in prot_to_gtypes.items() if gt in gts}
        chains = df_glycan[df_glycan["Glycan_type"]==gt]["Glycan_string"].nunique()
        gt_stats.append({
            "Glycan_type":        gt,
            "Number_of_glycoproteins": len(prots),
            "Number_of_distinct_glycan_chains": chains,
            "Gallus_proteins":    sum(1 for a in prots if acc_sp.get(a)=="Gallus"),
            "Anas_proteins":      sum(1 for a in prots if acc_sp.get(a)=="Anas"),
            "Columba_proteins":   sum(1 for a in prots if acc_sp.get(a)=="Columba"),
        })
    df_gt_stats = pd.DataFrame(gt_stats)

    # cluster type 统计
    ct_stats = df_prot.groupby(["Cluster_type","Species"]).size().reset_index(name="Count")

    save_xlsx(OUT_DIR / "Fig3_Glycan_Network.xlsx", {
        "Protein_Cluster_Info":  df_prot,
        "Glycan_Type_Stats":     df_gt_stats,
        "Protein_Glycan_Links":  df_links,
        "Glycan_Detail":         df_glycan,
        "ClusterType_by_Species": ct_stats,
    })


# ══════════════════════════════════════════════════════════════════════════
# Fig 4  2D Enrichment (Gallus vs Columba)
# ══════════════════════════════════════════════════════════════════════════
PREF_MAP = {"Gallus": "G", "Anas": "A", "Columba": "C"}

TARGET_PAIRS = {
    "OVAL":  ("P01012",     "A0A2I0MWA2"),
    "OC116": ("A0A8V0XA58", "A0A2I0MGY6"),
    "TRFE":  ("A0A8V1A6Y9", "A0A2I0LUS7"),
}
TARGET_ACCS = {acc for pair in TARGET_PAIRS.values() for acc in pair}


def load_protein_mean(sp):
    df = pd.read_excel(MS_DATA_DIR / f"Protein_MS_{sp}.xlsx", sheet_name="Protein_quant")
    df = df[df["Number Comparable"] >= 2].copy()
    ic = get_int_cols(df, INT_PREFIX[sp])
    df["prot_mean"] = df[ic].replace(0, np.nan).mean(axis=1)
    df = df[df["prot_mean"] > 0]
    # 返回 Series（index=accession, values=prot_mean），方便 `acc in series` 检查
    return df.set_index("Protein accession")["prot_mean"]


def load_glycan_mean_sum(sp):
    df = pd.read_excel(MS_DATA_DIR / f"Glycan_MS_{sp}.xlsx", sheet_name="Site_quant")
    ic = get_int_cols(df, INT_PREFIX[sp])
    df["glyc_mean"] = df[ic].replace(0, np.nan).mean(axis=1)
    df = df[df["glyc_mean"] > 0]
    return df.groupby("Protein accession")["glyc_mean"].sum()


def extract_acc(s):
    m = re.search(r"\|([A-Z0-9]+)\|", str(s))
    return m.group(1) if m else str(s)


def count_nonoverlap(starts, ends):
    intervals = sorted(zip(starts, ends))
    merged, cur_end = 0, -1
    for s, e in intervals:
        if s > cur_end:
            merged += 1; cur_end = e
        else:
            cur_end = max(cur_end, e)
    return merged


def fig4_2d_enrichment():
    prot_ref  = load_protein_mean("Gallus")
    prot_comp = load_protein_mean("Columba")
    glyc_ref  = load_glycan_mean_sum("Gallus")
    glyc_comp = load_glycan_mean_sum("Columba")

    raw = pd.read_csv(FASTA_DIR / "Result", sep="\t")
    raw["col_acc"] = raw["QueryID"].apply(extract_acc)
    raw["gal_acc"] = raw["SubjectDefID"].apply(extract_acc)

    recs = []
    for (col_a, gal_a), grp in raw.groupby(["col_acc","gal_acc"]):
        q_hsp = count_nonoverlap(grp["QueryStart"],   grp["QueryEnd"])
        s_hsp = count_nonoverlap(grp["SubjectStart"],  grp["SubjectEnd"])
        mean_e = grp["E-value"].mean()
        max_id = grp["Identity"].max()  / 100.0
        avg_id = grp["Identity"].mean() / 100.0
        recs.append({"col_acc": col_a, "gal_acc": gal_a,
                     "mean_evalue": mean_e, "max_identity": max_id,
                     "avg_identity": avg_id, "q_hsp": q_hsp, "s_hsp": s_hsp,
                     "max_bitscore": grp["BitScore"].max()})
    blastp_df = pd.DataFrame(recs)

    def passes(r):
        if r["mean_evalue"] > 1e-5: return False
        if r["q_hsp"] != r["s_hsp"]: return r["max_identity"] >= 0.50
        return r["avg_identity"] >= 0.80

    blastp_df["pass_filter"] = blastp_df.apply(passes, axis=1)
    best = (blastp_df[blastp_df["pass_filter"]]
            .sort_values("max_bitscore", ascending=False)
            .drop_duplicates("col_acc").reset_index(drop=True))
    blastp_map = dict(zip(best["col_acc"], best["gal_acc"]))

    # 读取 gene name
    pg = pd.read_excel(MS_DATA_DIR / "Protein_MS_Gallus.xlsx", sheet_name="Protein_quant")
    acc2gene = dict(zip(pg["Protein accession"], pg["Gene name"].fillna("")))

    records = []
    for col_a, gal_a in blastp_map.items():
        if col_a in TARGET_ACCS or gal_a in TARGET_ACCS:
            continue
        if (gal_a not in prot_ref.index or col_a not in prot_comp.index or
            gal_a not in glyc_ref.index or col_a not in glyc_comp.index):
            continue
        records.append({
            "Gallus_accession":      gal_a,
            "Columba_accession":     col_a,
            "Gene_name":             acc2gene.get(gal_a, ""),
            "Protein_log2FC":        float(np.log2(prot_ref[gal_a]) - np.log2(prot_comp[col_a])),
            "Glycan_log2FC":         float(np.log2(glyc_ref[gal_a]) - np.log2(glyc_comp[col_a])),
            "Gallus_Protein_Mean_Intensity":  float(prot_ref[gal_a]),
            "Columba_Protein_Mean_Intensity": float(prot_comp[col_a]),
            "Gallus_Glycan_Sum_Intensity":    float(glyc_ref[gal_a]),
            "Columba_Glycan_Sum_Intensity":   float(glyc_comp[col_a]),
            "Protein_type": "Background",
        })

    for pname, (acc_ref, acc_comp) in TARGET_PAIRS.items():
        if (acc_ref  not in prot_ref.index  or acc_comp not in prot_comp.index or
            acc_ref  not in glyc_ref.index  or acc_comp not in glyc_comp.index):
            continue
        records.append({
            "Gallus_accession":      acc_ref,
            "Columba_accession":     acc_comp,
            "Gene_name":             pname,
            "Protein_log2FC":        float(np.log2(prot_ref[acc_ref])  - np.log2(prot_comp[acc_comp])),
            "Glycan_log2FC":         float(np.log2(glyc_ref[acc_ref])  - np.log2(glyc_comp[acc_comp])),
            "Gallus_Protein_Mean_Intensity":  float(prot_ref[acc_ref]),
            "Columba_Protein_Mean_Intensity": float(prot_comp[acc_comp]),
            "Gallus_Glycan_Sum_Intensity":    float(glyc_ref[acc_ref]),
            "Columba_Glycan_Sum_Intensity":   float(glyc_comp[acc_comp]),
            "Protein_type": f"Target ({pname})",
        })

    df_enrich = pd.DataFrame(records)
    # 额外标注方向
    df_enrich["Diagonal_deviation"] = df_enrich["Glycan_log2FC"] - df_enrich["Protein_log2FC"]
    df_enrich["Glycan_regulation"]  = df_enrich["Diagonal_deviation"].apply(
        lambda v: "Glycan_enriched_in_Gallus" if v > 0 else "Glycan_suppressed_in_Gallus"
    )

    # BLASTp 过滤详情
    blastp_df_out = blastp_df.rename(columns={
        "col_acc": "Columba_accession", "gal_acc": "Gallus_accession"})

    save_xlsx(OUT_DIR / "Fig4_2D_Enrichment_Gallus_vs_Columba.xlsx", {
        "Enrichment_Plot_Data":  df_enrich,
        "BLASTp_Filtering":      blastp_df_out,
    })


# ══════════════════════════════════════════════════════════════════════════
# Figs 5-8  Glycan Profiling (per target protein)
# ══════════════════════════════════════════════════════════════════════════
TARGET_MAPPING = {
    "Gallus":  {"OVAL":["P01012"],          "OC116":["A0A8V0XA58"], "TRFE":["A0A8V1A6Y9"], "OC17":["V5NUE7"]},
    "Anas":    {"OVAL":["A0A8B9QNT8"],      "OC116":["A0A8B9ZY54"], "TRFE":["A0A493TBB4"], "OC17":[]},
    "Columba": {"OVAL":["A0A2I0MWA2"],      "OC116":["A0A2I0MGY6"], "TRFE":["A0A2I0LUS7"], "OC17":[]},
}

ORDERED_CLASSES = [
    "High-Mannose", "Paucimannose/Truncated",
    "Neutral (Complex/Hybrid)", "Fucosylated (Complex/Hybrid)",
    "Sialylated (Complex/Hybrid)", "Other",
]


def classify_glycan_6(comp_str):
    if pd.isna(comp_str): return "Other"
    comp = {s: int(n) for s, n in re.findall(r"([A-Za-z]+)\((\d+)\)", str(comp_str))}
    hexnac = comp.get("HexNAc", 0)
    hex_   = comp.get("Hex",    0)
    fuc    = comp.get("Fuc",    0)
    neuac  = comp.get("NeuAc",  0) + comp.get("NeuGc", 0)
    if hexnac == 2 and hex_ >= 5 and fuc == 0 and neuac == 0: return "High-Mannose"
    if neuac > 0: return "Sialylated (Complex/Hybrid)"
    if fuc > 0 and neuac == 0: return "Fucosylated (Complex/Hybrid)"
    if hexnac >= 3 and fuc == 0 and neuac == 0: return "Neutral (Complex/Hybrid)"
    if hexnac == 2 and hex_ < 5 and fuc == 0 and neuac == 0: return "Paucimannose/Truncated"
    return "Other"


def fig_glycan_profiling(protein: str, fig_num: int):
    all_species = ["Gallus", "Anas", "Columba"]
    summary_rows = []    # 相对丰度汇总
    raw_rows = []        # 原始每条糖链记录

    for sp in all_species:
        accs = TARGET_MAPPING[sp].get(protein, [])
        if not accs:
            continue
        fp = MS_DATA_DIR / f"Glycan_MS_{sp}.xlsx"
        try:
            df = pd.read_excel(fp, sheet_name="IGP_quant")
        except Exception:
            continue
        df_t = df[df["Protein accession"].isin(accs)].copy()
        if df_t.empty:
            continue
        ic = get_int_cols(df_t, INT_PREFIX[sp])
        df_t["Mean_Intensity"] = df_t[ic].replace(0, np.nan).mean(axis=1)
        df_t = df_t[df_t["Mean_Intensity"] > 0]
        if df_t.empty:
            continue

        df_t["Glycan_class"] = df_t["Observed Modification"].apply(classify_glycan_6)

        # 原始记录
        for _, row in df_t.iterrows():
            raw_rows.append({
                "Species":             sp,
                "Protein_accession":   row["Protein accession"],
                "Protein_description": row.get("Protein description", ""),
                "Gene_name":           row.get("Gene name", ""),
                "Observed_Modification": row.get("Observed Modification", ""),
                "Glycan_class":        row["Glycan_class"],
                "Mean_Intensity":      row["Mean_Intensity"],
                **{c: row[c] for c in ic if c in row.index},
            })

        # 相对丰度
        cls_int  = df_t.groupby("Glycan_class")["Mean_Intensity"].sum()
        total    = cls_int.sum()
        for cls in ORDERED_CLASSES:
            summary_rows.append({
                "Species":              sp,
                "Target_protein":       protein,
                "Glycan_class":         cls,
                "Sum_Intensity":        float(cls_int.get(cls, 0)),
                "Relative_Abundance_%": float(cls_int.get(cls, 0)) / total * 100 if total > 0 else 0,
            })

    df_summary = pd.DataFrame(summary_rows)
    df_raw     = pd.DataFrame(raw_rows)

    # pivot 横向格式（物种为列）
    if not df_summary.empty:
        pivot = df_summary.pivot_table(
            index="Glycan_class", columns="Species",
            values="Relative_Abundance_%", aggfunc="sum"
        ).reindex(ORDERED_CLASSES).fillna(0).reset_index()
    else:
        pivot = pd.DataFrame()

    save_xlsx(OUT_DIR / f"Fig{fig_num}_Glycan_Profiling_{protein}.xlsx", {
        "Relative_Abundance_Pivot": pivot,
        "Relative_Abundance_Detail": df_summary,
        "Raw_Glycan_Intensities":    df_raw,
    })


# ══════════════════════════════════════════════════════════════════════════
# Figs 9-11  Highlighted Correlation Scatter
# ══════════════════════════════════════════════════════════════════════════
def fig_correlation(species: str, fig_num: int):
    prot_fp = MS_DATA_DIR / f"Protein_MS_{species}.xlsx"
    glyc_fp = MS_DATA_DIR / f"Glycan_MS_{species}.xlsx"

    df_prot = pd.read_excel(prot_fp, sheet_name="Protein_quant")
    df_glyc = pd.read_excel(glyc_fp, sheet_name="Site_quant")

    if "Number Comparable" in df_prot.columns:
        df_prot = df_prot[df_prot["Number Comparable"] >= 2]
    if "Number Comparable" in df_glyc.columns:
        df_glyc = df_glyc[df_glyc["Number Comparable"] >= 2]

    prot_ic = get_int_cols(df_prot, INT_PREFIX[species])
    glyc_ic = get_int_cols(df_glyc, INT_PREFIX[species])

    df_prot = df_prot.copy()
    df_glyc = df_glyc.copy()
    df_prot["Protein_Mean_Intensity"] = df_prot[prot_ic].replace(0, np.nan).mean(axis=1)
    df_glyc["Glycan_Mean_Intensity"]  = df_glyc[glyc_ic].replace(0, np.nan).mean(axis=1)
    df_prot = df_prot[df_prot["Protein_Mean_Intensity"] > 0]
    df_glyc = df_glyc[df_glyc["Glycan_Mean_Intensity"]  > 0]

    df_merged = pd.merge(
        df_glyc[["Protein accession","Position","N-glycan types","Glycan_Mean_Intensity"]],
        df_prot[["Protein accession","Protein_Mean_Intensity","Gene name"]],
        on="Protein accession", how="inner"
    )
    df_merged["Log2_Protein_Intensity"] = np.log2(df_merged["Protein_Mean_Intensity"])
    df_merged["Log2_Glycan_Intensity"]  = np.log2(df_merged["Glycan_Mean_Intensity"])

    rho, pval = spearmanr(df_merged["Log2_Protein_Intensity"], df_merged["Log2_Glycan_Intensity"])

    # 标记目标蛋白
    df_merged["Target_protein"] = "Background"
    for tname, accs in TARGET_MAPPING[species].items():
        if accs:
            df_merged.loc[df_merged["Protein accession"].isin(accs), "Target_protein"] = tname

    # 相关性统计摘要
    df_stats = pd.DataFrame([{
        "Species":                     species,
        "N_glycosylation_sites":       len(df_merged),
        "Spearman_rho":                round(rho, 4),
        "P_value":                     pval,
        "Significance":                "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else "ns")),
        "N_background_proteins":       (df_merged["Target_protein"]=="Background").sum(),
        "N_target_sites":              (df_merged["Target_protein"]!="Background").sum(),
    }])

    # 目标蛋白详情
    df_targets = df_merged[df_merged["Target_protein"] != "Background"].copy()

    out_cols = ["Protein accession","Gene name","Position","N-glycan types",
                "Target_protein","Log2_Protein_Intensity","Log2_Glycan_Intensity",
                "Protein_Mean_Intensity","Glycan_Mean_Intensity"]
    df_merged_out = df_merged[[c for c in out_cols if c in df_merged.columns]]

    save_xlsx(OUT_DIR / f"Fig{fig_num}_Correlation_{species}.xlsx", {
        "Correlation_Statistics": df_stats,
        "All_Glycosylation_Sites": df_merged_out,
        "Target_Proteins_Detail": df_targets[[c for c in out_cols if c in df_targets.columns]],
    })


# ══════════════════════════════════════════════════════════════════════════
# 主程序
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== 正在提取可视化数据 ===\n")

    print("Fig 1: 系统发育树...")
    fig1_phylogenetic_tree()

    print("Fig 2: 基因家族扩张/收缩...")
    fig2_expansions_contractions()

    print("Fig 3: 糖蛋白网络...")
    fig3_glycan_network()

    print("Fig 4: 二维富集分析...")
    fig4_2d_enrichment()

    print("Fig 5-8: 糖型谱...")
    for prot, fnum in [("OVAL",5), ("OC116",6), ("TRFE",7), ("OC17",8)]:
        print(f"  {prot}...")
        fig_glycan_profiling(prot, fnum)

    print("Fig 9-11: 蛋白-糖基化相关性...")
    for sp, fnum in [("Gallus",9), ("Anas",10), ("Columba",11)]:
        print(f"  {sp}...")
        fig_correlation(sp, fnum)

    print(f"\n=== 全部完成，文件位于: {OUT_DIR} ===")
