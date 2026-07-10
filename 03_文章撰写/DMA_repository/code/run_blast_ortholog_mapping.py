"""
本地 BLASTp 比对脚本
以 GlyGallus_Reference.fasta 为查询，分别与 GlyGallus、GlyAnas、GlyColumba 中的序列进行比对
使用 BLOSUM62 矩阵，结果保存为 TSV 文件
"""

import os
from Bio import SeqIO
from Bio.Align import PairwiseAligner, substitution_matrices

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLAST_DIR = os.path.join(PACKAGE_DIR, "data", "glycoprotein_blast")
QUERY_FILE = os.path.join(BLAST_DIR, "GlyGallus.fasta")
SUBJECT_FILES = {
    "GlyGallus":  os.path.join(BLAST_DIR, "GlyGallus.fasta"),
    "GlyAnas":    os.path.join(BLAST_DIR, "GlyAnas.fasta"),
    "GlyColumba": os.path.join(BLAST_DIR, "GlyColumba.fasta"),
}
OUTPUT_FILE = os.path.join(BLAST_DIR, "blastp_results.tsv")
E_VALUE_CUTOFF = 1e-3   # 仅输出 E-value < 此阈值的结果（近似值）
TOP_N = 5               # 每条 query 每个 subject 文件返回前几名

# ── 配置比对器（模拟 BLASTp 参数）──────────────────────────────────────────
aligner = PairwiseAligner()
aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
aligner.open_gap_score    = -11   # gap open
aligner.extend_gap_score  = -1    # gap extend
aligner.mode              = "local"   # local alignment（Smith-Waterman，BLAST方式）

def parse_id(header: str) -> str:
    """从 FASTA header 中提取简短标识（UniProt accession + protein name）"""
    parts = header.split("|")
    if len(parts) >= 3:
        accession = parts[1]
        desc = parts[2].split(" OS=")[0].strip()
        return f"{accession} {desc}"
    return header[:60]

def pct_identity(aln) -> float:
    """从 Biopython Alignment 对象计算百分比同一性"""
    aligned = str(aln)
    lines = aligned.split("\n")
    # target / query 行 (indices 0, 2)
    target_seq = ""
    query_seq  = ""
    for i, line in enumerate(lines):
        if line.startswith("target") or (i == 0 and not line.startswith("query")):
            target_seq += line.split()[-1] if line.split() else ""
        elif line.startswith("query"):
            query_seq  += line.split()[-1] if line.split() else ""
    matches = sum(t == q and t != "-" for t, q in zip(target_seq, query_seq))
    length  = max(len(target_seq.replace("-", "")), len(query_seq.replace("-", "")))
    return (matches / length * 100) if length > 0 else 0.0

def approx_evalue(score: float, query_len: int, db_size: int) -> float:
    """BLASTp E-value 近似（Karlin-Altschul 公式简化版，K=0.041, lambda=0.267 for BLOSUM62）"""
    import math
    K, lam = 0.041, 0.267
    if score <= 0:
        return 999.0
    return K * query_len * db_size * math.exp(-lam * score)

# ── 读取 query 序列 ─────────────────────────────────────────────────────────
queries = list(SeqIO.parse(QUERY_FILE, "fasta"))
print(f"Query 序列数: {len(queries)} ({os.path.basename(QUERY_FILE)})")

# ── 主循环 ──────────────────────────────────────────────────────────────────
rows = []
header = ["query_id", "query_len", "subject_db", "subject_id", "subject_len",
          "score", "pct_identity", "approx_evalue", "aln_start_query", "aln_end_query"]

total_comparisons = 0
for db_name, db_file in SUBJECT_FILES.items():
    subjects = list(SeqIO.parse(db_file, "fasta"))
    db_total_len = sum(len(s) for s in subjects)
    print(f"\n正在搜索 {db_name} ({len(subjects)} 条序列)...")

    for qi, qrec in enumerate(queries, 1):
        q_id  = parse_id(qrec.description)
        q_len = len(qrec.seq)
        hits  = []

        for srec in subjects:
            score = aligner.score(str(qrec.seq), str(srec.seq))
            hits.append((score, srec))

        # 按得分降序，取前 TOP_N
        hits.sort(key=lambda x: x[0], reverse=True)
        for score, srec in hits[:TOP_N]:
            evalue = approx_evalue(score, q_len, db_total_len)
            if evalue > E_VALUE_CUTOFF:
                continue
            # 计算百分比同一性（对 top hit 做完整比对）
            alignments = aligner.align(str(qrec.seq), str(srec.seq))
            aln = next(iter(alignments))
            coords = aln.coordinates  # shape (2, n)
            q_start = int(coords[0].min()) + 1
            q_end   = int(coords[0].max())

            # 计算比对段内 identity
            aln_target = ""
            aln_query  = ""
            prev_qt, prev_qs = coords[0][0], coords[1][0]
            for (qt, qs) in zip(coords[0][1:], coords[1][1:]):
                seg_t = str(qrec.seq)[int(prev_qt):int(qt)]
                seg_s = str(srec.seq)[int(prev_qs):int(qs)]
                if qt == prev_qt:
                    aln_target += "-" * len(seg_s)
                    aln_query  += seg_s
                elif qs == prev_qs:
                    aln_target += seg_t
                    aln_query  += "-" * len(seg_t)
                else:
                    aln_target += seg_t
                    aln_query  += seg_s
                prev_qt, prev_qs = qt, qs

            aln_len = max(len(aln_target), len(aln_query))
            if aln_len > 0:
                matches = sum(a == b and a != "-" for a, b in zip(aln_target, aln_query))
                identity = matches / aln_len * 100
            else:
                identity = 0.0

            rows.append({
                "query_id":        q_id,
                "query_len":       q_len,
                "subject_db":      db_name,
                "subject_id":      parse_id(srec.description),
                "subject_len":     len(srec.seq),
                "score":           round(score, 1),
                "pct_identity":    round(identity, 1),
                "approx_evalue":   f"{evalue:.2e}",
                "aln_start_query": q_start,
                "aln_end_query":   q_end,
            })
            total_comparisons += 1

        print(f"  [{qi:3d}/{len(queries)}] {q_id[:50]}", end="\r")

print(f"\n\n共找到 {total_comparisons} 条有效比对 (E-value < {E_VALUE_CUTOFF})")

# ── 写出结果 ────────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
    fh.write("\t".join(header) + "\n")
    for row in rows:
        fh.write("\t".join(str(row[k]) for k in header) + "\n")

print(f"结果已保存至: {OUTPUT_FILE}")

# ── 打印预览（前20行）──────────────────────────────────────────────────────
print("\n=== 结果预览（前 20 条，按 score 降序）===")
rows_sorted = sorted(rows, key=lambda x: float(x["score"]), reverse=True)
print("\t".join(header))
for row in rows_sorted[:20]:
    print("\t".join(str(row[k]) for k in header))
