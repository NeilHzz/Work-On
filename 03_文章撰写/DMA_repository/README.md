# Processed Source Data and Analysis Code Repository

This Zenodo-ready archive contains processed source data, derived model outputs, finite-element summary inputs, and analysis code used to evaluate and reproduce the numerical results reported in the manuscript and Supplementary Materials. It is not a vendor raw-data archive: raw mass-spectrometry instrument files and full solver cache directories are not included.

Rendered PNG files, exploratory figure versions, article PDFs, HTML reports, manuscript-building scripts, and redundant trial scripts were intentionally excluded.

## Contents

- `data/source_data_tables/`: final Supplementary Tables S1 to S7.
- `data/ms_processed/`: processed protein MS and glycan MS workbooks for Gallus, Anas, and Columba.
- `data/species_selection/`: AVONET-derived species-selection source data and sensitivity-analysis inputs.
- `data/mammillary_morphometry/`: mammillary-layer morphometry source workbook.
- `data/orthology_and_phylogeny/`: orthogroup, phylogeny, GO, and CAFE5 source/result files.
- `data/glycoprotein_blast/`: FASTA files, BLAST/ortholog-mapping tables, and target glycoprotein BLAST results.
- `data/reglyco_ensemble/`: Re-Glyco PDB ensembles, APBS/SASA CSV files, and source-data workbooks.
- `data/finite_element/`: finite-element force and post-processing source workbooks.
- `models/fea_project_files/`: finite-element project entry files and shared geometry.
- `code/`: compact reproducibility scripts.
- `README_figures_to_files.md`: mapping from manuscript/supplementary results to files and scripts.
- `raw_data_availability_note.md`: scope and restrictions for raw data not included in this archive.
- `materials_availability_note.md`: materials availability statement.
- `software_versions.txt` and `requirements.txt`: software and Python dependency information.
- `LICENSE`: reuse terms for data and code.
- `CITATION.cff` and `zenodo_metadata.md`: citation and Zenodo upload metadata template.

## Main Reproduction Entry Points

Install the Python dependencies used by the scripts:

```bash
pip install -r requirements.txt
```

Run these from the package root:

```bash
python code/reproduce_numeric_results.py
python code/run_fea_postprocessing.py
python code/run_reglyco_source_data_export.py
python code/run_blast_ortholog_mapping.py
```

`run_reglyco_ensemble_analysis.py` preserves the original Re-Glyco/APBS workflow logic. Its online GlycoShape submission and APBS steps require the corresponding external services/tools; the PDB ensembles and APBS/SASA-derived CSV outputs used in the paper are already included in `data/reglyco_ensemble/`.

For a full APBS rerun, install APBS/PDB2PQR and set `APBS_BINARY` if the executable is not available as `apbs` on `PATH`. The helper module `external_tools/reglyco_apbs_helpers/glycan_aware_apbs.py` is not included in this processed-data archive; the manuscript source-data tables can be regenerated from the packaged APBS/SASA CSV outputs without rerunning APBS.

For figure/result-level provenance, see `README_figures_to_files.md`.

## Exclusions

This minimal package excludes all `*.png` files, rendered figure drafts, article PDFs, HTML report folders, raw vendor MS files, complete Workbench/LS-DYNA cache directories, old exploratory scripts, and `build_manuscript_en.py` / `build_supplementary_en.py`.
