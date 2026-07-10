"""Create a compact reproducibility summary from packaged source data.

The output is a lightweight audit of the source tables used for the manuscript
and supplementary materials. It does not regenerate figures or PNG files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PACKAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_DIR / "data"
OUT_DIR = PACKAGE_DIR / "outputs"


def workbook_sheets(path: Path) -> list[dict[str, object]]:
    xls = pd.ExcelFile(path)
    rows = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        rows.append({"file": path.name, "sheet": sheet, "rows": len(df), "columns": len(df.columns)})
    return rows


def summarize_workbooks(folder: Path, label: str) -> list[dict[str, object]]:
    rows = []
    for path in sorted(folder.glob("*.xlsx")):
        for row in workbook_sheets(path):
            row["group"] = label
            rows.append(row)
    return rows


def summarize_csv(folder: Path, label: str) -> list[dict[str, object]]:
    rows = []
    for path in sorted(folder.glob("*.csv")):
        df = pd.read_csv(path)
        rows.append({"group": label, "file": path.name, "sheet": "", "rows": len(df), "columns": len(df.columns)})
    return rows


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    rows = []
    rows += summarize_workbooks(DATA_DIR / "source_data_tables", "supplementary_tables")
    rows += summarize_workbooks(DATA_DIR / "ms_processed", "processed_ms")
    rows += summarize_workbooks(DATA_DIR / "species_selection", "species_selection")
    rows += summarize_workbooks(DATA_DIR / "mammillary_morphometry", "mammillary_morphometry")
    rows += summarize_workbooks(DATA_DIR / "reglyco_ensemble", "reglyco_workbooks")
    rows += summarize_workbooks(DATA_DIR / "finite_element", "finite_element")
    rows += summarize_csv(DATA_DIR / "reglyco_ensemble" / "csv", "reglyco_csv")

    summary = pd.DataFrame(rows)
    out_xlsx = OUT_DIR / "packaged_source_data_inventory.xlsx"
    summary.to_excel(out_xlsx, index=False)

    manifest = {
        "supplementary_tables": len(list((DATA_DIR / "source_data_tables").glob("*.xlsx"))),
        "processed_ms_workbooks": len(list((DATA_DIR / "ms_processed").glob("*.xlsx"))),
        "reglyco_csv_files": len(list((DATA_DIR / "reglyco_ensemble" / "csv").glob("*.csv"))),
        "reglyco_pdb_files": len(list((DATA_DIR / "reglyco_ensemble" / "PDB").glob("*.pdb"))),
        "finite_element_workbooks": len(list((DATA_DIR / "finite_element").glob("*.xlsx"))),
    }
    out_json = OUT_DIR / "packaged_source_data_inventory.json"
    out_json.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {out_xlsx}")
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
