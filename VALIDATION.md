# Validation performed

- All package Python files passed `py_compile`.
- F2 was smoke-tested in LOYO mode with no FULL_DATA threshold rules; the two primary fold-specific methods completed and produced the detailed F2 outputs.
- F2 was smoke-tested in BOTH mode; the complete alignment workbook was created with these sheets:
  - Class Counts
  - Per-Year (Sh)
  - Per-Year (All)
  - Alignment Summary
  - Per Class Accuracy
  - Overall Accuracy
  - Data with Alignment
  - Sh class_Metrics
  - Classification Report
  - Dominant stress types
  - STa Summary
- F1 was smoke-tested in FULL_DATA mode and created the automatic signature, automatic thresholds/rules, PDP outputs and `full_data_automatic_STa.png`.
- The complete `run_pipeline.py` path (Step 1 -> Step 2 -> F1 -> F2) was smoke-tested end-to-end in BOTH mode.

For runtime-only smoke tests, bootstrap count / RF grid were temporarily reduced in a separate test copy. The final package retains the supplied F1 settings, including `N_BOOTSTRAPS = 100`, `GRID_RESOLUTION = 100`, `INNER_CV = 10`, and the original RF grid.


## 2026-10-26 output-path / F2 workbook fix
- Verified `04_evaluate.py` in `FULL_DATA` mode creates `<CASE>_alignment_results_with_metrics.xlsx`.
- Verified the workbook contains the same 11 core sheets as the supplied ALB_Potato example.
- Verified automatic features with unavailable STa votes remain NA rather than crashing workbook creation.
- F1 generated preprocessing outputs are routed to `results/<CASE>/00_full_data_preprocessing/`.
