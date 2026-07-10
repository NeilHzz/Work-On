# Figure and Result Provenance

This file maps the main manuscript and Supplementary Materials results to the source-data files included in this Zenodo archive.

## Fig. 1 and Species/Mammillary Analyses

- Species-selection space and sensitivity inputs:
  - `data/species_selection/analysis_data.xlsx`
  - `data/species_selection/raw_inputs/AVONET_Supp1.xlsx`
  - `data/species_selection/raw_inputs/pigot_supp.xlsx`
  - `data/species_selection/raw_inputs/Appendix_Sensitivity_Analysis.md`
- Mammillary-layer morphometry:
  - `data/mammillary_morphometry/mammillary_morphometry.xlsx`
  - `data/source_data_tables/Supplementary_Table_7_Finite_Element_Analysis.xlsx` where relevant for mechanical summaries.

## Matrix Proteome, Orthogroups, and GO/CAFE5 Analyses

- Processed protein MS workbooks:
  - `data/ms_processed/Protein_MS_Gallus.xlsx`
  - `data/ms_processed/Protein_MS_Anas.xlsx`
  - `data/ms_processed/Protein_MS_Columba.xlsx`
- Orthogroup, phylogeny, GO, and CAFE5 source/result files:
  - `data/orthology_and_phylogeny/orthofinder_cafe5/`
  - `data/orthology_and_phylogeny/glycoprotein_ortho/`
- Final source-data table:
  - `data/source_data_tables/Supplementary_Table_3_Ortholog_GO_CAFE5.xlsx`

## Glycoproteomics and OVAL Glycan-State Analyses

- Processed glycan MS workbooks:
  - `data/ms_processed/Glycan_MS_Gallus.xlsx`
  - `data/ms_processed/Glycan_MS_Anas.xlsx`
  - `data/ms_processed/Glycan_MS_Columba.xlsx`
- Glycoprotein BLAST and target-protein mapping:
  - `data/glycoprotein_blast/Blast_Ortholog_Mapping.xlsx`
  - `data/glycoprotein_blast/blastp_results.tsv`
  - `data/glycoprotein_blast/three_species_target_blast/`
  - `code/run_blast_ortholog_mapping.py`
- Final source-data tables:
  - `data/source_data_tables/Supplementary_Table_1_Protein_MS.xlsx`
  - `data/source_data_tables/Supplementary_Table_2_Glycan_MS.xlsx`
  - `data/source_data_tables/Supplementary_Table_4_Protein_Glycan_JointAnalysis.xlsx`

## Re-Glyco, APBS, SASA, and Surface-Accessibility Analyses

- PDB ensemble outputs:
  - `data/reglyco_ensemble/PDB/`
- APBS/SASA and glycan-geometry CSV files:
  - `data/reglyco_ensemble/csv/`
- Recomputed source-data workbooks:
  - `data/reglyco_ensemble/Figure1_Glycan_Conformational_Diversity.xlsx`
  - `data/reglyco_ensemble/Figure2_Hotspot_Count_Trajectory.xlsx`
  - `data/reglyco_ensemble/Figure3_Hotspot_Accessibility.xlsx`
  - `data/reglyco_ensemble/Figure4_APBS_Calcium_Ensemble.xlsx`
- Final source-data tables:
  - `data/source_data_tables/Supplementary_Table_5_ReGlyco_Ensemble_Results.xlsx`
  - `data/source_data_tables/Supplementary_Table_6_ReGlyco_Ensemble_Stats.xlsx`
- Main scripts:
  - `code/run_reglyco_source_data_export.py`
  - `code/run_reglyco_ensemble_analysis.py`

## Finite-Element Analyses

- Finite-element force and statistical source workbooks:
  - `data/finite_element/combined_rcforc_yforce.xlsx`
  - `data/finite_element/duncan_comparison.xlsx`
- Project entry files and shared geometry:
  - `models/fea_project_files/chicken_fea_project.wbpj`
  - `models/fea_project_files/duck_fea_project.wbpj`
  - `models/fea_project_files/pigeon_fea_project.wbpj`
  - `models/fea_project_files/eggshell_segment_geometry.x_t`
- Main script:
  - `code/run_fea_postprocessing.py`

The full proprietary solver cache and raw LS-DYNA run directories are not included. The packaged workbooks contain the force, stress-normalized, and statistical source data used for the manuscript and Supplementary Materials.
