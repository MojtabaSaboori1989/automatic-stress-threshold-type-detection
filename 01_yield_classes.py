# -*- coding: utf-8 -*-
"""STEP 1 - Training-only LOYO yield percentile classification.

Input
-----
The single canonical workbook defined in config.py. It must contain at least:
    Year, Detrended_Yield

For each held-out year, P10/P90 and the pivot value (PV) are calculated from
training years only. Outputs are written under results/<CASE_ID>/.
"""

from pathlib import Path
import pandas as pd

from config import (
    MASTER_FILE, CASE_DIR, YEAR_COL, YIELD_COL,
    LOWER_PERCENTILE, UPPER_PERCENTILE,
)

OUTPUT_DIR = Path(CASE_DIR) / "01_yield_classes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not Path(MASTER_FILE).exists():
    raise FileNotFoundError(
        f"Input file not found:\n{MASTER_FILE}\n\n"
        "Place the case workbook in data/ using the filename shown in config.py."
    )

df = pd.read_excel(MASTER_FILE)
required_cols = {YEAR_COL, YIELD_COL}
missing_cols = required_cols - set(df.columns)
if missing_cols:
    raise ValueError(f"Missing required columns: {sorted(missing_cols)}")

df = df[[YEAR_COL, YIELD_COL]].dropna(subset=[YEAR_COL, YIELD_COL]).copy()
df = df.sort_values(YEAR_COL).reset_index(drop=True)

if df[YEAR_COL].duplicated().any():
    duplicate_years = df.loc[df[YEAR_COL].duplicated(), YEAR_COL].tolist()
    raise ValueError(f"Duplicate years detected: {duplicate_years}")

fold_summary = []

for test_year in df[YEAR_COL].tolist():
    print("\n" + "=" * 70)
    print(f"STEP 1 | held-out year = {test_year}")
    print("=" * 70)

    train_df = df[df[YEAR_COL] != test_year].copy()
    test_df = df[df[YEAR_COL] == test_year].copy()

    p10 = train_df[YIELD_COL].quantile(LOWER_PERCENTILE)
    p90 = train_df[YIELD_COL].quantile(UPPER_PERCENTILE)

    train_df["Yield_Class"] = "No"
    train_df.loc[train_df[YIELD_COL] <= p10, "Yield_Class"] = "Sh"
    train_df.loc[train_df[YIELD_COL] >= p90, "Yield_Class"] = "Bo"

    normal_train = train_df[train_df["Yield_Class"] == "No"]
    if normal_train.empty:
        raise ValueError(f"No Normal observations in fold {test_year}")
    pv = normal_train[YIELD_COL].mean()

    test_yield = float(test_df[YIELD_COL].iloc[0])
    if test_yield <= p10:
        test_class = "Sh"
    elif test_yield >= p90:
        test_class = "Bo"
    else:
        test_class = "No"

    test_binary_class = "Sh" if test_class == "Sh" else "NSh"
    test_df["True_Class_3"] = test_class
    test_df["True_Class_Binary"] = test_binary_class
    test_df["Training_P10"] = p10
    test_df["Training_P90"] = p90
    test_df["Training_PV"] = pv

    shocked_class = train_df[train_df["Yield_Class"] == "Sh"].copy()
    normal_class = train_df[train_df["Yield_Class"] == "No"].copy()
    boosted_class = train_df[train_df["Yield_Class"] == "Bo"].copy()

    fold_dir = OUTPUT_DIR / f"heldout_{int(test_year)}"
    fold_dir.mkdir(parents=True, exist_ok=True)

    train_df.to_excel(fold_dir / "training_yield_with_classes.xlsx", index=False)
    shocked_class.to_excel(fold_dir / "shocked_class.xlsx", index=False)
    normal_class.to_excel(fold_dir / "normal_class.xlsx", index=False)
    boosted_class.to_excel(fold_dir / "boosted_class.xlsx", index=False)
    test_df.to_excel(fold_dir / "heldout_year.xlsx", index=False)

    fold_info = {
        "Heldout_Year": test_year,
        "N_Training": len(train_df),
        "P10_Training": p10,
        "P90_Training": p90,
        "PV_Training": pv,
        "N_Sh_Training": len(shocked_class),
        "N_No_Training": len(normal_class),
        "N_Bo_Training": len(boosted_class),
        "Heldout_Yield": test_yield,
        "Heldout_True_Class_3": test_class,
        "Heldout_True_Class_Binary": test_binary_class,
    }
    pd.DataFrame([fold_info]).to_excel(fold_dir / "fold_information.xlsx", index=False)
    fold_summary.append(fold_info)

    print(f"P10/P90 (training): {p10:.4f} / {p90:.4f}")
    print(f"PV (training No mean): {pv:.4f}")
    print(f"Held-out class: {test_class} ({test_binary_class})")

summary_df = pd.DataFrame(fold_summary)
summary_path = OUTPUT_DIR / "yield_classification_all_folds_summary.xlsx"
summary_df.to_excel(summary_path, index=False)

print("\n" + "=" * 70)
print("STEP 1 COMPLETED")
print("=" * 70)
print(f"Number of LOYO folds: {len(summary_df)}")
print(f"Results: {OUTPUT_DIR}")
