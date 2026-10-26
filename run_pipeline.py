# -*- coding: utf-8 -*-
"""Run Automatic Stress Threshold and Type Detection using config.py.

Execution logic
---------------
FULL_DATA : Step 3 -> Step 4
LOYO      : Step 1 -> Step 2 -> Step 3 -> Step 4
BOTH      : Step 1 -> Step 2 -> Step 3 -> Step 4

Step 3 is the user's original F1 workflow with the manual-signature branch removed.
Step 4 is the user's original F2 workflow with manual diagnostics replaced by the
FULL-DATA automatic STa diagnostic. No manual feature-STa rule list is required.
"""

from pathlib import Path
import subprocess
import sys

from config import CASE_ID, MASTER_FILE, CASE_DIR, RUN_MODE

ROOT = Path(__file__).resolve().parent

if RUN_MODE == "FULL_DATA":
    STEPS = [
        "03_threshold_derivation.py",
        "04_evaluate.py",
    ]
else:
    STEPS = [
        "01_yield_classes.py",
        "02_standardize.py",
        "03_threshold_derivation.py",
        "04_evaluate.py",
    ]

print("=" * 78)
print(f"Automatic Stress Threshold and Type Detection | case: {CASE_ID}")
print(f"Run mode : {RUN_MODE}")
print(f"Input    : {MASTER_FILE}")
print(f"Outputs  : {CASE_DIR}")
print("=" * 78)

if not Path(MASTER_FILE).exists():
    raise FileNotFoundError(
        f"Input file not found:\n{MASTER_FILE}\n\n"
        "Either:\n"
        "  1) place your workbook at data/combined_nonstandardized_data.xlsx, or\n"
        "  2) set DATA_FILE in config.py to the exact workbook path."
    )

for i, script in enumerate(STEPS, start=1):
    path = ROOT / script
    print("\n" + "#" * 78)
    print(f"RUNNING {i}/{len(STEPS)}: {script}")
    print("#" * 78)
    subprocess.run([sys.executable, str(path)], cwd=ROOT, check=True)

# Write a compact index of the outputs users most often need.
case_dir = Path(CASE_DIR)
workbook = (
    case_dir
    / "04_stress_types_and_evaluation"
    / f"{CASE_ID}_alignment_results_with_metrics.xlsx"
)
density = (
    case_dir
    / "03_thresholds_and_signature"
    / "full_data"
    / "full_data_automatic_STa.png"
)
signature = (
    case_dir
    / "03_thresholds_and_signature"
    / "automatic_signature_discovery"
    / "automatic_full_data_signature.xlsx"
)
index_lines = [
    "Automatic Stress Threshold and Type Detection",
    f"Case: {CASE_ID}",
    f"Run mode: {RUN_MODE}",
    "",
    "KEY OUTPUTS",
    f"Complete results workbook: {workbook if workbook.exists() else 'not produced'}",
    f"Automatic STa density plot: {density if density.exists() else 'not produced (requires FULL_DATA or BOTH)'}",
    f"Automatic feature-direction signature: {signature if signature.exists() else 'not produced'}",
    f"Generated full-data preprocessing outputs: {case_dir / '00_full_data_preprocessing'}",
    f"Detailed threshold/signature outputs: {case_dir / '03_thresholds_and_signature'}",
    f"Detailed stress-type/evaluation outputs: {case_dir / '04_stress_types_and_evaluation'}",
]
case_dir.mkdir(parents=True, exist_ok=True)
(case_dir / "RESULTS_INDEX.txt").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

print("\n" + "=" * 78)
print("PIPELINE COMPLETED SUCCESSFULLY")
print(f"Run mode : {RUN_MODE}")
print(f"Results  : {CASE_DIR}")
print(f"Workbook : {workbook if workbook.exists() else 'not produced'}")
print(f"Density  : {density if density.exists() else 'not produced for this mode'}")
print(f"Index    : {case_dir / 'RESULTS_INDEX.txt'}")
print("=" * 78)
