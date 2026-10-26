# -*- coding: utf-8 -*-
"""
Created on Sun Oct 11 10:41:03 2026

@author: msaboori23
"""

# ============================================================
# STEP 2 - LOYO training-only standardization FROM CANONICAL MASTER FILE
#
# Input:
#   1. combined_nonstandardized_data.xlsx
#   2. Output folders produced by Step 1
#
# For every held-out year:
#   - Construct training climate + yield data
#   - Attach the Step-1 training Yield_Class
#   - Fit StandardScaler ONLY on training years
#   - Transform training years
#   - Transform held-out year using TRAINING scaler
#   - Save raw + standardized datasets
#   - Save scaler parameters for later PDP back-transformation
# ============================================================

import os
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

from config import MASTER_FILE, CASE_DIR, YEAR_COL, YIELD_COL

# ============================================================
# PATHS FROM CENTRAL CONFIGURATION
# ============================================================

BASE_DIR = str(CASE_DIR)
combined_file = str(MASTER_FILE)
step1_dir = os.path.join(BASE_DIR, "01_yield_classes")
step2_dir = os.path.join(BASE_DIR, "02_standardization")
os.makedirs(step2_dir, exist_ok=True)

if not Path(combined_file).exists():
    raise FileNotFoundError(f"Input file not found:\n{combined_file}")


# ============================================================
# LOAD MASTER DATA
# ============================================================

df = pd.read_excel(combined_file)

required_cols = {YEAR_COL, YIELD_COL}

missing_cols = required_cols - set(df.columns)

if missing_cols:
    raise ValueError(
        f"Missing required columns in combined dataset: {missing_cols}"
    )


# Sort chronologically
df = df.sort_values(YEAR_COL).reset_index(drop=True)


# Check duplicate years
if df[YEAR_COL].duplicated().any():

    duplicate_years = df.loc[
        df[YEAR_COL].duplicated(),
        YEAR_COL
    ].tolist()

    raise ValueError(
        f"Duplicate years detected: {duplicate_years}"
    )


# Check missing values
if df.isna().any().any():

    bad_cols = df.columns[
        df.isna().any()
    ].tolist()

    raise ValueError(
        f"Missing values detected in columns: {bad_cols}"
    )


# ============================================================
# IDENTIFY CLIMATE FEATURES
# ============================================================

# Everything except Year and yield is treated as a climate predictor

feature_cols = [
    c for c in df.columns
    if c not in [YEAR_COL, YIELD_COL]
]

print("\nClimate features detected:")
for f in feature_cols:
    print("  ", f)

print(f"\nNumber of climate features = {len(feature_cols)}")


# ============================================================
# COLUMNS TO STANDARDIZE
# ============================================================

# Same scientific design as your original analysis:
# standardize both predictors and detrended yield.
#
# But now the scaler is fitted separately for every
# training fold.

columns_to_standardize = feature_cols + [YIELD_COL]


# ============================================================
# GET YEARS FROM MASTER DATA
# ============================================================

years = df[YEAR_COL].tolist()

summary_rows = []


# ============================================================
# LOYO LOOP
# ============================================================

for test_year in years:

    print("\n" + "=" * 75)
    print(f"STEP 2 | Held-out year = {test_year}")
    print("=" * 75)

    # --------------------------------------------------------
    # Corresponding Step-1 folder
    # --------------------------------------------------------

    step1_fold_dir = os.path.join(
        step1_dir,
        f"heldout_{int(test_year)}"
    )

    train_class_file = os.path.join(
        step1_fold_dir,
        "training_yield_with_classes.xlsx"
    )

    heldout_class_file = os.path.join(
        step1_fold_dir,
        "heldout_year.xlsx"
    )

    if not os.path.exists(train_class_file):
        raise FileNotFoundError(
            f"Step-1 training file not found:\n{train_class_file}"
        )

    if not os.path.exists(heldout_class_file):
        raise FileNotFoundError(
            f"Step-1 held-out file not found:\n{heldout_class_file}"
        )


    # --------------------------------------------------------
    # Read Step-1 class information
    # --------------------------------------------------------

    step1_train = pd.read_excel(
        train_class_file
    )

    step1_test = pd.read_excel(
        heldout_class_file
    )


    # --------------------------------------------------------
    # Split master climate/yield dataset
    # --------------------------------------------------------

    train_raw = df[
        df[YEAR_COL] != test_year
    ].copy()

    test_raw = df[
        df[YEAR_COL] == test_year
    ].copy()


    # --------------------------------------------------------
    # Sanity checks
    # --------------------------------------------------------

    if len(test_raw) != 1:
        raise ValueError(
            f"Held-out year {test_year} produced "
            f"{len(test_raw)} rows instead of 1."
        )

    if len(train_raw) != len(df) - 1:
        raise ValueError(
            f"Unexpected training size for year {test_year}."
        )


    # --------------------------------------------------------
    # Attach TRAINING Yield_Class from Step 1
    # --------------------------------------------------------

    class_lookup = step1_train[
        [YEAR_COL, "Yield_Class"]
    ].copy()

    train_raw = train_raw.merge(
        class_lookup,
        on=YEAR_COL,
        how="left",
        validate="one_to_one"
    )

    if train_raw["Yield_Class"].isna().any():
        raise ValueError(
            f"Missing Step-1 Yield_Class after merging "
            f"for held-out year {test_year}."
        )


    # --------------------------------------------------------
    # Attach held-out TRUE class from Step 1
    # --------------------------------------------------------

    test_true_class_3 = step1_test[
        "True_Class_3"
    ].iloc[0]

    test_true_binary = step1_test[
        "True_Class_Binary"
    ].iloc[0]

    test_raw["True_Class_3"] = test_true_class_3
    test_raw["True_Class_Binary"] = test_true_binary


    # ========================================================
    # FIT SCALER USING TRAINING YEARS ONLY
    # ========================================================

    scaler = StandardScaler()

    scaler.fit(
        train_raw[columns_to_standardize]
    )


    # ========================================================
    # STANDARDIZE TRAINING DATA
    # ========================================================

    train_std = train_raw.copy()

    train_std[
        columns_to_standardize
    ] = scaler.transform(
        train_raw[columns_to_standardize]
    )


    # ========================================================
    # STANDARDIZE HELD-OUT YEAR
    #
    # IMPORTANT:
    # transform(), NOT fit_transform()
    # ========================================================

    test_std = test_raw.copy()

    test_std[
        columns_to_standardize
    ] = scaler.transform(
        test_raw[columns_to_standardize]
    )


    # ========================================================
    # SAVE SCALER PARAMETERS
    #
    # These will be useful later for:
    # standardized <-> original-scale conversion,
    # especially PDP / STi / STa.
    # ========================================================

    scaler_parameters = pd.DataFrame({

        "Variable":
            columns_to_standardize,

        "Training_Mean":
            scaler.mean_,

        "Training_Scale":
            scaler.scale_

    })


    # Extract target scaler parameters separately
    yield_idx = columns_to_standardize.index(
        YIELD_COL
    )

    yield_mean = scaler.mean_[yield_idx]
    yield_scale = scaler.scale_[yield_idx]


    # ========================================================
    # CREATE OUTPUT FOLDER
    # ========================================================

    fold_output_dir = os.path.join(
        step2_dir,
        f"heldout_{int(test_year)}"
    )

    os.makedirs(
        fold_output_dir,
        exist_ok=True
    )


    # ========================================================
    # SAVE DATASETS
    # ========================================================

    # Raw training data
    train_raw.to_excel(
        os.path.join(
            fold_output_dir,
            "training_nonstandardized.xlsx"
        ),
        index=False
    )


    # Standardized training data
    train_std.to_excel(
        os.path.join(
            fold_output_dir,
            "training_standardized.xlsx"
        ),
        index=False
    )


    # Raw held-out observation
    test_raw.to_excel(
        os.path.join(
            fold_output_dir,
            "heldout_nonstandardized.xlsx"
        ),
        index=False
    )


    # Standardized held-out observation
    test_std.to_excel(
        os.path.join(
            fold_output_dir,
            "heldout_standardized.xlsx"
        ),
        index=False
    )


    # Scaler parameters
    scaler_parameters.to_excel(
        os.path.join(
            fold_output_dir,
            "scaler_parameters.xlsx"
        ),
        index=False
    )


    # ========================================================
    # SUMMARY INFORMATION
    # ========================================================

    row = {

        "Heldout_Year":
            test_year,

        "N_Training":
            len(train_raw),

        "N_Features":
            len(feature_cols),

        "Yield_Training_Mean":
            yield_mean,

        "Yield_Training_Scale":
            yield_scale,

        "Heldout_Yield_Raw":
            test_raw[YIELD_COL].iloc[0],

        "Heldout_Yield_Standardized":
            test_std[YIELD_COL].iloc[0],

        "Heldout_True_Class_3":
            test_true_class_3,

        "Heldout_True_Class_Binary":
            test_true_binary

    }

    summary_rows.append(row)


    # ========================================================
    # DISPLAY CHECKS
    # ========================================================

    print(
        f"Training observations : {len(train_raw)}"
    )

    print(
        f"Held-out observations : {len(test_raw)}"
    )

    print(
        f"Climate features       : {len(feature_cols)}"
    )

    print(
        f"Yield training mean    : {yield_mean:.6f}"
    )

    print(
        f"Yield training scale   : {yield_scale:.6f}"
    )

    print(
        f"Held-out raw yield     : "
        f"{test_raw[YIELD_COL].iloc[0]:.6f}"
    )

    print(
        f"Held-out std. yield    : "
        f"{test_std[YIELD_COL].iloc[0]:.6f}"
    )

    print(
        f"Held-out true class    : "
        f"{test_true_binary}"
    )


# ============================================================
# SAVE GLOBAL STEP-2 SUMMARY
# ============================================================

summary_df = pd.DataFrame(
    summary_rows
)

summary_file = os.path.join(
    step2_dir,
    "training_standardization_summary.xlsx"
)

summary_df.to_excel(
    summary_file,
    index=False
)


# ============================================================
# FINAL CHECK
# ============================================================

print("\n" + "=" * 75)
print("STEP 2 COMPLETED")
print("=" * 75)

print(
    f"Number of folds processed: "
    f"{len(summary_df)}"
)

print(
    f"\nResults saved in:\n{step2_dir}"
)

print(
    f"\nSummary file:\n{summary_file}"
)