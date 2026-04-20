"""
数据检查脚本汇总
=================
合并自以下文件：
  check_comparable.py      check_data.py
  check_glycan_cols.py     check_glycan_sheets.py
  check_glycan_size.py     check_matrix.py
  check_ortho.py           check_oval_duplicates.py
  check_other_glycans.py   check_prot_cols.py
  check_prot_data.py       check_zhi_xiang_guan.py
  debug_merge.py           debug_oval_glycans.py

每个检查项封装为独立函数，主入口逐节调用并用分隔线标注。
注：check_prot_cols（【5】）与 check_comparable（【8】）均打印 Protein_quant 列名，
    已合并：主入口不再单独调用【5】，保留函数供按需使用。
"""

import pandas as pd
import os

DATA_DIR = r"D:\system_folder\Desktop\Work On\01_数据与计算\Raw_Data\MS_DATA"
SPECIES_LIST = ["Gallus", "Anas", "Columba"]

SEP = "\n" + "=" * 60 + "\n"


# ══════════════════════════════════════════════════════════════════【1】
# 文件结构：Glycan_MS_Gallus.xlsx sheet 列表与各 sheet 形状
# ══════════════════════════════════════════════════════════════════
def check_glycan_sheets(species: str = "Gallus"):
    glyc_file = os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx")
    xl = pd.ExcelFile(glyc_file)
    print(f"Sheets in Glycan_MS_{species}.xlsx: {xl.sheet_names}")
    for sheet in xl.sheet_names:
        df = pd.read_excel(glyc_file, sheet_name=sheet)
        print(f"  Sheet '{sheet}' shape: {df.shape}")


# ══════════════════════════════════════════════════════════════════【2】
# 列名检查：Glycan_MS_Gallus IGP_quant / Site_quant 列名
# ══════════════════════════════════════════════════════════════════
def check_glycan_cols(species: str = "Gallus"):
    glyc_file = os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx")
    df_igp  = pd.read_excel(glyc_file, sheet_name="IGP_quant")
    df_site = pd.read_excel(glyc_file, sheet_name="Site_quant")
    print(f"IGP_quant  columns: {df_igp.columns.tolist()}")
    print(f"Site_quant columns: {df_site.columns.tolist()}")


# ══════════════════════════════════════════════════════════════════【3】
# 数据量：Glycan_MS_Gallus 蛋白 accession 分布
# ══════════════════════════════════════════════════════════════════
def check_glycan_size(species: str = "Gallus"):
    glyc_file = os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx")
    df = pd.read_excel(glyc_file)
    print(f"Glycan_MS_{species}.xlsx shape: {df.shape}")
    if 'Protein accession' in df.columns:
        print(df['Protein accession'].value_counts())


# ══════════════════════════════════════════════════════════════════【4】
# 多物种：Anas / Columba Glycan 文件形状
# ══════════════════════════════════════════════════════════════════
def check_other_glycans():
    for species in ["Anas", "Columba"]:
        glyc_file = os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx")
        try:
            df = pd.read_excel(glyc_file)
            print(f"Glycan_MS_{species}.xlsx shape: {df.shape}")
        except Exception as e:
            print(f"读取 {species} 失败: {e}")


# ══════════════════════════════════════════════════════════════════【5】
# 列名检查：Protein_MS_Gallus.xlsx 列名（前5行）
# 注：列名输出已被【8】check_comparable 覆盖，主入口不重复调用本函数
# ══════════════════════════════════════════════════════════════════
def check_prot_cols(species: str = "Gallus"):
    file_path = os.path.join(DATA_DIR, f"Protein_MS_{species}.xlsx")
    df = pd.read_excel(file_path, sheet_name="Protein_quant", nrows=5)
    print(f"Protein_MS_{species} columns: {df.columns.tolist()}")


# ══════════════════════════════════════════════════════════════════【6】
# 全量数据：Protein_MS_Gallus 所有 sheets（前10行）
# ══════════════════════════════════════════════════════════════════
def check_prot_data(species: str = "Gallus"):
    file_path = os.path.join(DATA_DIR, f"Protein_MS_{species}.xlsx")
    print(f"--- {file_path} ---")
    xl = pd.ExcelFile(file_path)
    print("Sheet names:", xl.sheet_names)
    for sheet in xl.sheet_names:
        print(f"\nSheet: {sheet}")
        df = pd.read_excel(file_path, sheet_name=sheet, nrows=10)
        print(df.head(10))


# ══════════════════════════════════════════════════════════════════【7】
# 快速预览：Gallus Protein + Glycan 文件头部
# ══════════════════════════════════════════════════════════════════
def check_data(species: str = "Gallus"):
    print(f"--- Protein_MS_{species}.xlsx ---")
    try:
        df_prot = pd.read_excel(os.path.join(DATA_DIR, f"Protein_MS_{species}.xlsx"))
        print(df_prot.columns.tolist())
        print(df_prot.head(2))
    except Exception as e:
        print(e)

    print(f"\n--- Glycan_MS_{species}.xlsx ---")
    try:
        df_glyc = pd.read_excel(os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx"))
        print(df_glyc.columns.tolist())
        print(df_glyc.head(2))
    except Exception as e:
        print(e)


# ══════════════════════════════════════════════════════════════════【8】
# Number Comparable：Protein / Glycan Number Comparable 值统计
# ══════════════════════════════════════════════════════════════════
def check_comparable(species: str = "Gallus"):
    prot_file = os.path.join(DATA_DIR, f"Protein_MS_{species}.xlsx")
    glyc_file = os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx")

    df_prot = pd.read_excel(prot_file, sheet_name="Protein_quant")
    df_glyc = pd.read_excel(glyc_file, sheet_name="Site_quant")

    print(f"Protein columns: {df_prot.columns.tolist()}")
    print(f"Glycan  columns: {df_glyc.columns.tolist()}")

    if 'Number Comparable' in df_prot.columns:
        print("\nProtein 'Number Comparable' value counts:")
        print(df_prot['Number Comparable'].value_counts())

    if 'Number Comparable' in df_glyc.columns:
        print("\nGlycan 'Number Comparable' value counts:")
        print(df_glyc['Number Comparable'].value_counts())


# ══════════════════════════════════════════════════════════════════【9】
# OVAL 重复：Columba OVAL 候选蛋白的糖基化位点详情
# ══════════════════════════════════════════════════════════════════
def check_oval_duplicates(species: str = "Columba"):
    glyc_file = os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx")
    df_glyc = pd.read_excel(glyc_file, sheet_name="Site_quant")

    oval_accessions = [
        'A0A1R7T3L5', 'A0A2I0MW20', 'A0A2I0MWA2',
        'A0A2I0MED6', 'A0A2I0M204', 'A0A2I0MP02', 'A0A2I0MTU8',
    ]
    df_oval = df_glyc[df_glyc['Protein accession'].isin(oval_accessions)]
    print(f"--- {species} OVAL Glycan Sites ---")
    cols = ['Protein accession', 'Position', 'Amino acid', 'N-glycan types']
    print(df_oval[[c for c in cols if c in df_oval.columns]])


# ══════════════════════════════════════════════════════════════════【10】
# 基质蛋白："基质蛋白三物种糖链汇总.xlsx" 结构
# ══════════════════════════════════════════════════════════════════
def check_matrix():
    file_path = r"D:\system_folder\Desktop\Work On\01_数据与计算\糖蛋白和蛋白联合分析\基质蛋白三物种糖链汇总.xlsx"
    try:
        xl = pd.ExcelFile(file_path)
        print("Sheets:", xl.sheet_names)
        df = pd.read_excel(file_path, sheet_name=xl.sheet_names[0])
        print("Columns:", df.columns.tolist())
        print(df.head(3))
    except Exception as e:
        print(f"读取失败: {e}")


# ══════════════════════════════════════════════════════════════════【11】
# OrthoVenn 参数：OrthoVenn参数确定.xlsx 结构
# ══════════════════════════════════════════════════════════════════
def check_ortho():
    file_path = r"D:\system_folder\Desktop\Work On\01_数据与计算\OrthoVenn参数确定.xlsx"
    try:
        xl = pd.ExcelFile(file_path)
        print("Sheets:", xl.sheet_names)
        df = pd.read_excel(file_path, sheet_name=xl.sheet_names[0], nrows=5)
        print("Columns:", df.columns.tolist())
        print(df.head(3))
    except Exception as e:
        print(f"读取失败: {e}")


# ══════════════════════════════════════════════════════════════════【12】
# 秩相关：秩相关.xlsx Sheet2 结构
# ══════════════════════════════════════════════════════════════════
def check_zhi_xiang_guan():
    file_path = r"D:\system_folder\Desktop\Work On\01_数据与计算\糖蛋白和蛋白联合分析\秩相关\秩相关.xlsx"
    try:
        df = pd.read_excel(file_path, sheet_name='Sheet2')
        print(f"秩相关.xlsx shape: {df.shape}")
        print(df.columns.tolist())
    except Exception as e:
        print(f"读取失败: {e}")


# ══════════════════════════════════════════════════════════════════【13】
# Merge 调试：蛋白/糖链 Protein accession 交集检查
# (原 debug_merge.py)
# ══════════════════════════════════════════════════════════════════
def debug_merge_accessions(species: str = "Gallus"):
    prot_file = os.path.join(DATA_DIR, f"Protein_MS_{species}.xlsx")
    glyc_file = os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx")

    df_prot = pd.read_excel(prot_file, sheet_name="Protein_quant")
    df_glyc = pd.read_excel(glyc_file)

    print("Protein columns:", df_prot.columns.tolist())
    print("Glycan  columns:", df_glyc.columns.tolist())

    print("\nProtein accession sample (Protein):",
          df_prot['Protein accession'].head(5).tolist())
    print("Protein accession sample (Glycan):",
          df_glyc['Protein accession'].head(5).tolist())

    common = set(df_prot['Protein accession']).intersection(
                 set(df_glyc['Protein accession']))
    print(f"\nNumber of common accessions: {len(common)}")


# ══════════════════════════════════════════════════════════════════【14】
# OVAL 修饰调试：Gallus IGP_quant OVAL 蛋白 Modification 列预览
# (原 debug_oval_glycans.py)
# ══════════════════════════════════════════════════════════════════
def debug_oval_modifications(species: str = "Gallus",
                              oval_acc: str = "P01012"):
    file_path = os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx")
    df = pd.read_excel(file_path, sheet_name="IGP_quant")

    df_oval = df[df['Protein accession'] == oval_acc]
    print(f"Columns: {df_oval.columns.tolist()}")

    if 'Assigned Modification' in df_oval.columns:
        print("\nSample Assigned Modification:")
        print(df_oval['Assigned Modification'].head(5).tolist())

    if 'Observed Modification' in df_oval.columns:
        print("\nSample Observed Modification:")
        print(df_oval['Observed Modification'].head(5).tolist())


# ══════════════════════════════════════════════════════════════════
# 主入口：逐节运行所有检查
# ══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print(SEP + "【1】Glycan sheets（Gallus）")
    check_glycan_sheets("Gallus")

    print(SEP + "【2】Glycan 列名 IGP_quant / Site_quant（Gallus）")
    check_glycan_cols("Gallus")

    print(SEP + "【3】Glycan 数据规模 / 蛋白分布（Gallus）")
    check_glycan_size("Gallus")

    print(SEP + "【4】Glycan 文件形状（Anas / Columba）")
    check_other_glycans()

    # 【5】check_prot_cols 已被【8】check_comparable 覆盖，不重复调用

    print(SEP + "【6】Protein 全量数据预览（Gallus）")
    check_prot_data("Gallus")

    print(SEP + "【7】Protein + Glycan 快速预览（Gallus）")
    check_data("Gallus")

    print(SEP + "【8】Number Comparable 统计 + 列名（Gallus）")
    check_comparable("Gallus")

    print(SEP + "【9】OVAL 位点重复检查（Columba）")
    check_oval_duplicates("Columba")

    print(SEP + "【10】基质蛋白三物种糖链汇总.xlsx")
    check_matrix()

    print(SEP + "【11】OrthoVenn 参数确定.xlsx")
    check_ortho()

    print(SEP + "【12】秩相关.xlsx")
    check_zhi_xiang_guan()

    print(SEP + "【13】Protein / Glycan accession 交集（Gallus）")
    debug_merge_accessions("Gallus")

    print(SEP + "【14】OVAL IGP_quant Modification 列预览（Gallus）")
    debug_oval_modifications("Gallus")

    print(SEP + "全部检查完成。")
