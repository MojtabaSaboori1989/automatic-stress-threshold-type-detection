# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 11:28:53 2026

@author: msaboori23
"""

# ============================================================
# GENERIC AUTOMATIC-SIGNATURE LOYO - COMBINED CONFIG + STEP F1
# UPDATED: near-zero negative OOB-R2 tolerance = 0.01 for automatic
# FULL-DATA signature discovery; raw R2 values are preserved.
#
# FOR EACH COUNTRY/REGION, EDIT ONLY THE USER SETTINGS BELOW:
#   1) COUNTRY_FOLDER
#   2) REGION_NAME
#   3) RUN_MODE
#
# Feature identities are discovered automatically from FULL DATA
# using the paper's correlation -> RF/SHAP -> Pareto/Utopia workflow.
# The resulting automatic feature-direction signature is fixed for LOYO.
# No user-supplied feature/STa rule list is required.
#
# Then run this single file. No separate feature-rule file is needed.
#
# RUN_MODE controls execution:
#   "LOYO"      -> LOYO only
#   "FULL_DATA" -> full-data only
#   "BOTH"      -> LOYO first, then full-data
# ============================================================

# ============================================================
# AUTOMATIC-SIGNATURE CONFIGURATION
#
# User-facing case name, input path, and RUN_MODE are read from config.py.
# Feature identities, stress directions, STi, and STa are automatic.
# ============================================================

import os
import re
import math


# ============================================================
# USER SETTINGS
# ============================================================

BASE_PARENT = (
    r"C:\LOYO_based processing_Potato"
)

# Example: FIN2, SWE2, NOR2, etc.
COUNTRY_FOLDER = "ARM3"

# Used only in outputs / figures
REGION_NAME = "ARM-Potato"

# ------------------------------------------------------------
# AUTOMATIC FEATURE DISCOVERY (FULL-DATA FIXED SIGNATURE)
# ------------------------------------------------------------
# REPRODUCIBILITY MODE:
# ONE canonical input is shared by Step 1, Step 2, and FULL_DATA F1:
#     combined_nonstandardized_data.xlsx
# FULL_DATA is built independently from LOYO training folders. By default this
# single F1 script now reproduces the historical preprocessing itself:
# raw climate + detrended yield -> merge/standardize -> historical Spearman
# clustering/filtering -> <COUNTRY>_standardized_UPDATED.xlsx and
# <COUNTRY>_nonstandardized_UPDATED.xlsx -> RF/SHAP/OFS.
#
# This keeps FULL_DATA independent of LOYO and aligns the RF/SHAP input with
# the historical workflow. Tail-stress compatibility is checked only AFTER OFS.
#
# OFS workflow:
#   all predictors already in the standardized file -> RF -> SHAP -> top-k
#   -> Pareto (min true OOB-RMSE, max OOB-R2, min k)
#   -> Entropy-weighted Utopia with all-range scaling.
#
# PDP tail compatibility is checked ONLY AFTER OFS has been fixed. It cannot
# change SHAP ranking, top-k metrics, Utopia k, or the OFS OOB-R2.
#
# AUTOMATIC_FEATURE_DISCOVERY defines the fixed feature-direction signature
# used by both LOYO and FULL_DATA.
AUTOMATIC_FEATURE_DISCOVERY = True

# ------------------------------------------------------------
# STANDALONE FULL-DATA INPUTS
# ------------------------------------------------------------
# BEST reproducibility: put the exact two files used in the historical
# historical RF/SHAP analysis here.
#
# If both explicit paths are left blank, the code searches:
#     <COUNTRY_FOLDER>/full_data_input/
# for one standardized and one non-standardized/raw .xlsx file.
FULL_DATA_STANDARDIZED_FILE = r""
FULL_DATA_NONSTANDARDIZED_FILE = r""
FULL_DATA_INPUT_SUBDIR = "full_data_input"

# ------------------------------------------------------------
# AUTOMATIC FULL-DATA PREPROCESSING
# ------------------------------------------------------------
# When True, F1 itself reproduces the historical preprocessing chain:
#   raw climate indicators + detrended yield
#     -> merge by Year
#     -> combined_nonstandardized_data.xlsx
#     -> StandardScaler (all numeric columns except Year)
#     -> combined_standardized_data.xlsx
#     -> historical Spearman/hierarchical-cluster filtering
#     -> <COUNTRY>_nonstandardized_UPDATED.xlsx
#     -> <COUNTRY>_standardized_UPDATED.xlsx
#
# The UPDATED pair is then used for RF/SHAP/OFS exactly like the historical code.
AUTO_BUILD_FULL_DATA_INPUTS = True

# ------------------------------------------------------------
# CANONICAL FULL-DATA INPUT MODE
# ------------------------------------------------------------
# Recommended workflow: use ONE canonical merged raw dataset as the shared
# starting point for both the historical FULL_DATA branch and the LOYO prep:
#
#     combined_nonstandardized_data.xlsx
#
# It must contain: Year + all climate indicators + Detrended_Yield.
#
# MASTER_COMBINED (recommended):
#   F1 reads combined_nonstandardized_data.xlsx directly, creates the full-data
#   standardized file, applies the historical Spearman filter, and then runs
#   RF/SHAP/OFS/PDP/STi/STa. No second merge is performed.
#
# RAW_CLIMATE_YIELD is only a legacy fallback. In the canonical workflow,
# detrended_yield.xlsx is not an F1 input because yield is already in the master file.
FULL_DATA_INPUT_MODE = "MASTER_COMBINED"  # canonical workflow

# Explicit path to the canonical merged raw file. Leave blank to auto-search
# for combined_nonstandardized_data.xlsx near FULL_DATA_SOURCE_DIR / project.
FULL_DATA_MASTER_FILE = os.path.join(
    BASE_PARENT,
    COUNTRY_FOLDER,
    "combined_nonstandardized_data.xlsx",
)
FULL_DATA_MASTER_FILENAME = "combined_nonstandardized_data.xlsx"

# Optional source directory. In MASTER_COMBINED mode it is searched for the
# master file. In RAW_CLIMATE_YIELD mode it is searched for the two raw inputs.
FULL_DATA_SOURCE_DIR = r""

# Used only when FULL_DATA_INPUT_MODE = "RAW_CLIMATE_YIELD".
FULL_DATA_CLIMATE_FILE = r""
FULL_DATA_YIELD_FILE = r""

# Where generated full-data preprocessing files are saved. Blank = beside
# the canonical master file (or beside the climate file in fallback mode).
FULL_DATA_PREPROCESS_OUTPUT_DIR = r""

# Historical collinearity-screen settings.
FULL_DATA_SPEARMAN_MIN_PERIODS = 8
FULL_DATA_SPEARMAN_LINKAGE_METHOD = "complete"

# Internal cache so preprocessing is performed only once per script run.
_FULL_DATA_PREPARED_PAIR_CACHE = None

# The historical historical code was run AFTER Spearman filtering, so keep True
# when these standalone files are already the filtered files.
FULL_DATA_FILES_ALREADY_SPEARMAN_FILTERED = True

# Leave False to reproduce the old historical SHAP ranking. The heatmap is still
# produced as a diagnostic, but no second collinearity deletion is applied.
APPLY_SPEARMAN_FILTER_AGAIN_IN_F1 = False

CANDIDATE_FEATURE_REGEX = (
    r"^(RX5day|RX1day|CDD|CWD|CSU|CCD|CFD)_\d+$"
)

COLLINEARITY_ABS_RHO = 0.70
FEATURE_K_MIN = 4
FEATURE_K_MAX = 9
TEST_K2_K3_IF_K4_OOB_R2_NEGATIVE = True

# ------------------------------------------------------------
# FEATURE-SET ENTROPY-UTOPIA SETTINGS
# ------------------------------------------------------------
# Reproduce the original historical Entropy workflow exactly:
#   1) build Pareto front on min OOB-RMSE, max OOB-R2, min k
#   2) scale Pareto candidates using the ranges of ALL tested k sets
#   3) compute entropy weights from those all-range-scaled Pareto benefits
#   4) rank Pareto candidates by weighted Utopia distance
#   5) tie-break: smaller k, smaller RMSE, larger R2
FEATURE_SELECTION_USE_ALL_RANGE_SCALING = True
EXCLUDE_IF_ALL_TESTED_OOB_R2_NEGATIVE = True

# Numerical tolerance around zero for the automatic FULL-DATA feature-set
# discovery used to define the fixed LOYO signature. Raw OOB-R2 values are
# NEVER clipped or replaced by zero. This setting affects only the decision
# to stop/continue automatic feature selection.
#
# Rule:
#   best eligible OOB-R2 < -0.01  -> meaningfully negative -> exclude/stop
#   -0.01 <= best eligible OOB-R2 < 0 -> near-zero negative -> retain/continue
#   best eligible OOB-R2 >= 0 -> normal retain/continue
OOB_R2_NEAR_ZERO_TOLERANCE = 0.02

# Minimum number of AVAILABLE FEATURES required in a LOYO fold.
MIN_VALID_FEATURES = 2

# ------------------------------------------------------------
# EXECUTION MODE
#
# Choose ONE:
#
#   "LOYO"      -> run only all LOYO folds
#   "FULL_DATA" -> skip LOYO and run only the one full-data model
#   "BOTH"      -> run LOYO first, then run full-data
#
# This is useful when LOYO has already been completed for a country
# and you only want the new full-data Auto-STa analysis.
# ------------------------------------------------------------

RUN_MODE = "BOTH"

# ============================================================
# FULL-DATA RUN
# ============================================================
# FULL_DATA uses the SAME automatically discovered fixed feature-direction
# signature as the LOYO branch. No user-supplied/historical signature is used.
#
# Quantile definition:
#   - AUTO uses 0.10 / 0.90 normally.
#   - For exactly 29 observations, AUTO uses 0.11 / 0.89,
#     matching the short-series rule used for CZE/SVK.
#
# If a particular original full-data analysis used another cutoff,
# set FULL_DATA_LOW_Q and FULL_DATA_HIGH_Q explicitly.
# ============================================================



# ------------------------------------------------------------
# PACKAGE OVERRIDE
# ------------------------------------------------------------
# The scientific workflow below is unchanged.  The package only supplies
# case paths / run mode so a new user does not edit this long F1 file.
try:
    from config import (
        CASE_DIR as _PKG_CASE_DIR,
        MASTER_FILE as _PKG_MASTER_FILE,
        REGION_NAME as _PKG_REGION_NAME,
        RUN_MODE as _PKG_RUN_MODE,
        MIN_VALID_FEATURES as _PKG_MIN_VALID_FEATURES,
    )

    BASE_PARENT = str(_PKG_CASE_DIR.parent)
    COUNTRY_FOLDER = str(_PKG_CASE_DIR.name)
    REGION_NAME = str(_PKG_REGION_NAME)
    RUN_MODE = str(_PKG_RUN_MODE)
    MIN_VALID_FEATURES = int(_PKG_MIN_VALID_FEATURES)
    FULL_DATA_MASTER_FILE = str(_PKG_MASTER_FILE)
    FULL_DATA_SOURCE_DIR = os.path.dirname(str(_PKG_MASTER_FILE))

    # Package behavior: generated preprocessing artifacts belong under results,
    # never beside the user's raw input workbook.
    FULL_DATA_PREPROCESS_OUTPUT_DIR = os.path.join(
        str(_PKG_CASE_DIR),
        "00_full_data_preprocessing",
    )
except ImportError:
    pass

RUN_MODE = str(
    RUN_MODE
).strip().upper()

VALID_RUN_MODES = {
    "LOYO",
    "FULL_DATA",
    "BOTH",
}

if RUN_MODE not in VALID_RUN_MODES:
    raise ValueError(
        f"Invalid RUN_MODE = {RUN_MODE!r}. "
        "Use 'LOYO', 'FULL_DATA', or 'BOTH'."
    )

RUN_LOYO = (
    RUN_MODE
    in {
        "LOYO",
        "BOTH",
    }
)

RUN_FULL_DATA = (
    RUN_MODE
    in {
        "FULL_DATA",
        "BOTH",
    }
)


FULL_DATA_LOW_Q = None
FULL_DATA_HIGH_Q = None

# Optional documented full-data class overrides.
# Leave empty unless the ORIGINAL full-data classification used them.
FULL_DATA_FORCE_SH_YEARS = []
FULL_DATA_FORCE_BO_YEARS = []

# Build the automatic full-data density figure at the end of FULL_DATA.
MAKE_FULL_DATA_AUTOMATIC_FIGURE = True

# If True, figures are created only for the single FULL_DATA run.
# No figure products are created for the LOYO-only execution path.
GENERATE_FIGURES_ONLY_FOR_FULL_DATA = True

# DISPLAY ONLY:
# Keep KDE density curves unchanged, but draw Sh and Bo observation
# spikes taller than No so rare Sh/Bo observations are visually
# distinguishable, similar to the original density figures.
FULL_DATA_RUG_HEIGHT_FRACTION = {
    "Sh": 0.90,
    "No": 0.18,
    "Bo": 0.90,
}

FULL_DATA_RUG_ALPHA = {
    "Sh": 0.42,
    "No": 0.28,
    "Bo": 0.42,
}

# ------------------------------------------------------------
# FIGURE EXPORT SETTINGS
# ------------------------------------------------------------
# All generated figures are saved as raster images only (no PDF),
# using the requested 300 dpi output.
FIGURE_IMAGE_FORMAT = "png"
FIGURE_DPI = 300
GENERATE_AUTOMATIC_SIGNATURE_FIGURES = True


# ============================================================
# MULTIPLE-PDP-CROSSING HANDLING
# ============================================================
# The original historical PDP workflow retained ALL intersections of
# the mean PDP with PV. The automatic workflow now does the same.
#
# For each mean-PDP crossing:
#   1) bootstrap crossings are aligned to it by nearest distance;
#   2) a candidate uncertainty interval is built;
#   3) Auto-STa is derived inside the expected stress direction;
#   4) candidates are ranked WITHOUT using the historical STa value.
#
# Automatic selection does NOT use the numerical historical STa.
# For each candidate threshold, three equally weighted criteria
# are used:
#
#   C1) close to the center of Sh observations
#       -> minimize distance to median(Sh)
#
#   C2) far from the center of Bo observations
#       -> maximize distance from median(Bo)
#
#   C3) separate Sh from No
#       -> maximize Sh_hit_rate - No_hit_rate
#
# The three criteria are normalized to 0..1 and the candidate
# closest to the Utopia point (1, 1, 1) is selected.
#
# A directional guardrail prevents STa from moving beyond the
# Sh median when that median lies in the expected stress direction.
#
USE_MULTIPLE_STI_CANDIDATES = True
MIN_ALIGNED_BOOTSTRAP_CROSSINGS = 5

# If an OFS feature has valid PDP/PV crossings but the stress region is
# interior (neither outer tail ends below PV), do NOT discard the feature.
# Instead, evaluate the crossing-defined lower/upper candidates, derive an
# Auto-STa for each, and choose ONE direction by the same density-based
# Pareto + Linear 4:2:3 objective used for STa selection. This reproduces
# the historical/historical behavior without letting PDP compatibility alter OFS.
ALLOW_INTERIOR_CROSSING_DENSITY_FALLBACK = True

# ------------------------------------------------------------
# AUTOMATIC PV RESCUE WHEN ORIGINAL PV DOES NOT PRODUCE A VALID
# DIRECTIONAL PDP CROSSING
# ------------------------------------------------------------
# Original PV = mean detrended yield of training/full-data No years.
#
# If original PV does not produce at least one VALID directional crossing
# (lower or upper), move PV toward the mean detrended yield of Sh years in
# fixed increments of 0.05 yield units:
#
#   PV_try = PV_No +/- 0.05, +/- 0.10, +/- 0.15, ...
#
# The sign is determined automatically by the direction from PV_No toward
# Mean_Sh_Yield. Stop at the FIRST stepped PV that produces a valid
# directional crossing. A tangential touch (PDP = PV without a sign change)
# is NOT sufficient.
#
# To preserve the original "closer to No than to Sh" guardrail, the search
# is not allowed to reach or pass the midpoint between PV_No and Mean_Sh_Yield.
#
# The SAME feature-specific rescued PV is then used for:
#   - direction discovery
#   - mean-PDP STi detection
#   - bootstrap crossing alignment / CI
#   - all retained directions of that feature
#
AUTO_ADJUST_PV_IF_NO_CROSSING = True
PV_RESCUE_STEP = 0.05
PV_RESCUE_MAX_FRACTION_TOWARD_SH = 0.50

# ------------------------------------------------------------
# TWO-SIDED OUTER-TAIL DIRECTION SCREEN
# ------------------------------------------------------------
# If the mean PDP supports BOTH lower and upper outer-tail directions,
# evaluate the best Auto-STa for each side using the same full-data Sh/No/Bo
# densities used elsewhere.
#
# Direction screen:
#   1) if at least one side has Sh_Hit > 0, remove any side with Sh_Hit = 0;
#   2) Pareto-screen the remaining directions:
#          maximize Sh_Hit, minimize No_Hit, minimize Bo_Hit;
#   3) retain ALL Pareto-efficient directions.
#
# Therefore one side can be removed (e.g. LTU CWD_7 upper side), while a
# genuinely two-sided feature can retain BOTH directions if both remain
# non-dominated. Linear 4:2:3 is saved as a diagnostic but does not force a
# one-sided result when both directions are Pareto-efficient.
SCREEN_TWO_SIDED_OUTER_DIRECTIONS_BY_DENSITY = True

# ------------------------------------------------------------
# TAIL-STRESS COMPATIBILITY: AFTER OFS ONLY
# ------------------------------------------------------------
# Tail/PDP compatibility must NOT influence RF/SHAP/OFS selection.
# OFS is frozen first; only afterward are lower/upper directions, STi and STa
# evaluated. This preserves the historical historical Top_Features and OOB-R2.
REQUIRE_TAIL_STRESS_COMPATIBILITY_FOR_OFS = False
PDP_TAIL_FRACTION_FOR_DIRECTION = 0.10

# Keep False for strict historical-OFS reproducibility. Unsupported OFS features
# remain part of the predictive OFS but are flagged Threshold_Supported=False
# and receive no threshold rule. No silent feature replacement occurs.
BACKFILL_UNSUPPORTED_FINAL_OFS_FEATURES = False

# ------------------------------------------------------------
# FINAL Auto-STa GLOBAL SELECTOR
# ------------------------------------------------------------
# After STi has already been selected, the final STa selector uses
# a fixed Pareto + Linear 4:2:3 rule:
#
#   Linear score = 4*Sh_Hit - 2*No_Hit - 3*Bo_Hit
#
# Higher score is better.
#
# This encodes the fixed priority:
#   Sh detection > Bo exclusion > No exclusion
#
# The SAME weights are used for every crop-country case.
# They do NOT affect STi selection.
FINAL_STA_LINEAR_W_SH = 4.0
FINAL_STA_LINEAR_W_NO = 2.0
FINAL_STA_LINEAR_W_BO = 3.0

# ------------------------------------------------------------
# STa SEARCH RANGE
# ------------------------------------------------------------
# No hard Sh-median or Sh-quantile guardrail is used.
#
# The STa candidate space is constrained ONLY by the directional
# bootstrap uncertainty interval attached to the selected STi:
#
#   lower stress -> [CI_Lower, STi]
#   upper stress -> [STi, CI_Upper]
#
# This avoids Q25/Q75 becoming artificial thresholds when only a
# few Sh observations are available.
USE_SH_DISTRIBUTION_HARD_GUARDRAIL = False

# ------------------------------------------------------------
# FINAL STa REFINEMENT AFTER STi HAS ALREADY BEEN SELECTED
# ------------------------------------------------------------
# The original STi-selection logic remains unchanged.
#
# Final STa procedure:
#   1) remove Sh_Hit = 0 if Sh-positive candidates exist;
#   2) collapse classification-equivalent thresholds;
#   3) keep the Pareto front:
#          maximize Sh_Hit
#          minimize No_Hit
#          minimize Bo_Hit
#   4) choose the Pareto candidate maximizing:
#
#          4*Sh_Hit - 2*No_Hit - 3*Bo_Hit
#



# ============================================================
# BASE PATH
# ============================================================

BASE = os.path.join(
    BASE_PARENT,
    COUNTRY_FOLDER,
)


# ============================================================
# AUTOMATIC FIXED-SIGNATURE STATE
# ============================================================
# Populated once by prepare_automatic_full_data_signature() before either
# LOYO or FULL_DATA threshold derivation.  There is no historical-rule parser.
FIXED_FEATURES = []
EXPECTED_DIRECTIONS = {}
DIRECTION_REQUIRES_OUTER_TAIL = {}


# ============================================================
# STEP F1 PROCESSING STARTS HERE
# ============================================================

# ============================================================
# GENERIC FIXED-SIGNATURE LOYO
# STEP F1 - AUTO FEATURE DISCOVERY + MULTI-CROSSING STi + AUTO STa
#
# Feature identities and directions are supplied by automatic full-data discovery:
# Missing PDP crossing:
#   - first try automatic feature-level PV rescue toward Sh yield levels;
#   - move PV toward Sh in fixed 0.05 steps and stop at the first valid directional crossing;
#   - if rescue still fails, that feature/side is unavailable;
#   - for any two-sided feature, one available side is sufficient.
#
# STa:
#   - training-only
#   - directional bootstrap interval
#   - if original PV has no valid directional crossing, PV is moved in fixed
#     0.05 steps toward the training-only Sh yield mean, stopping before the midpoint
#   - STi selection after PV resolution is unchanged from the original
#     multi-crossing code
#   - after STi is fixed, STa candidates are restricted ONLY by the
#     directional STi-bootstrap margin
#   - final Auto-STa removes dominated candidates with a Pareto front
#     and selects the global Linear 4:2:3 compromise:
#       4*Sh_Hit - 2*No_Hit - 3*Bo_Hit
##   - negative OOB-R2 folds are retained and flagged, not excluded
# ============================================================

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy.stats import spearmanr
from scipy.cluster.hierarchy import linkage, fcluster
from joblib import Parallel, delayed
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


def save_raster_figure(fig, output_path):
    """Save one raster figure only (PNG/JPG) at the requested dpi."""
    fig.savefig(
        output_path,
        dpi=FIGURE_DPI,
        bbox_inches="tight",
    )


# Configuration is embedded above in this same file.

# ============================================================
# PATHS
# ============================================================

STEP2_DIR = os.path.join(BASE, "02_standardization")
OUTPUT_DIR = os.path.join(BASE, "03_thresholds_and_signature")
os.makedirs(OUTPUT_DIR, exist_ok=True)

YEAR_COL = "Year"
TARGET_COL = "Detrended_Yield"
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

RUN_ONLY_YEAR = None
SKIP_COMPLETED = False
N_BOOTSTRAPS = 100
GRID_RESOLUTION = 100
N_JOBS = -1
INNER_CV = 10

# RF tuning aligned with the requested/historical setup.
# GridSearchCV uses 10-fold CV and R2 scoring.
PARAM_GRID = {
    "n_estimators": [50, 100, 150],
    "max_depth": [4, 6, 10],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
}


def find_excel_file(folder, preferred_names, required_tokens=None):
    for name in preferred_names:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return path

    if required_tokens is not None:
        candidates = []
        for name in os.listdir(folder):
            low = name.lower()
            if not low.endswith(".xlsx"):
                continue
            if all(token.lower() in low for token in required_tokens):
                candidates.append(os.path.join(folder, name))
        if candidates:
            return sorted(candidates)[0]

    raise FileNotFoundError(
        f"Required Excel file not found in:\n{folder}\n"
        f"Preferred names: {preferred_names}\n"
        f"Required tokens: {required_tokens}"
    )


def locate_fold_files(fold_dir):
    train_std = find_excel_file(
        fold_dir,
        ["training_standardized.xlsx", "training_standardized_UPDATED.xlsx"],
        required_tokens=["training", "standardized"],
    )

    try:
        train_raw = find_excel_file(
            fold_dir,
            [
                "training_nonstandardized.xlsx",
                "training_nonstandardized_UPDATED.xlsx",
                "training_raw.xlsx",
            ],
            required_tokens=["training", "nonstandardized"],
        )
    except FileNotFoundError:
        train_raw = find_excel_file(
            fold_dir,
            [
                "training_nonstandardized.xlsx",
                "training_nonstandardized_UPDATED.xlsx",
                "training_raw.xlsx",
            ],
            required_tokens=["training", "raw"],
        )

    scaler_path = os.path.join(fold_dir, "scaler_parameters.xlsx")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Missing scaler_parameters.xlsx in:\n{fold_dir}")

    return train_std, train_raw, scaler_path


def get_training_class_column(df):
    for col in ["Yield_Class", "True_Class_3"]:
        if col in df.columns:
            return col
    raise ValueError("Training class column not found.")


def load_scalers(path):
    df = pd.read_excel(path)
    required = {"Variable", "Training_Mean", "Training_Scale"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing scaler columns: {missing}")

    out = {}
    for _, row in df.iterrows():
        out[str(row["Variable"])] = {
            "mean": float(row["Training_Mean"]),
            "scale": float(row["Training_Scale"]),
        }
    return out


def inverse_scale(values, variable, scalers):
    return (
        np.asarray(values, dtype=float) * scalers[variable]["scale"]
        + scalers[variable]["mean"]
    )


def calculate_oob_metrics(model, y_std, yield_scale):
    pred = np.asarray(model.oob_prediction_, dtype=float)
    truth = np.asarray(y_std, dtype=float)
    valid = np.isfinite(pred)

    if valid.sum() == 0:
        return {
            "OOB_R2": np.nan,
            "OOB_RMSE": np.nan,
            "OOB_MAE": np.nan,
            "OOB_Bias": np.nan,
            "N_OOB": 0,
        }

    rmse_std = np.sqrt(mean_squared_error(truth[valid], pred[valid]))
    mae_std = mean_absolute_error(truth[valid], pred[valid])
    bias_std = np.mean(pred[valid] - truth[valid])

    return {
        "OOB_R2": float(model.oob_score_),
        "OOB_RMSE": float(rmse_std * yield_scale),
        "OOB_MAE": float(mae_std * yield_scale),
        "OOB_Bias": float(bias_std * yield_scale),
        "N_OOB": int(valid.sum()),
    }



def calculate_training_metrics(model, X, y_std, yield_scale):
    """
    Calculate in-sample (training) error metrics in original yield units.

    IMPORTANT
    ---------
    These are saved ONLY for audit/comparison with the historical historical
    subset-results files. They are NOT used as OOB metrics and are NOT used
    for the corrected OFS selection.
    """
    pred = np.asarray(model.predict(X), dtype=float)
    truth = np.asarray(y_std, dtype=float)

    valid = np.isfinite(pred) & np.isfinite(truth)

    if valid.sum() == 0:
        return {
            "Training_RMSE": np.nan,
            "Training_MAE": np.nan,
            "Training_Bias": np.nan,
            "N_Training": 0,
        }

    rmse_std = np.sqrt(mean_squared_error(truth[valid], pred[valid]))
    mae_std = mean_absolute_error(truth[valid], pred[valid])
    bias_std = np.mean(pred[valid] - truth[valid])

    return {
        "Training_RMSE": float(rmse_std * yield_scale),
        "Training_MAE": float(mae_std * yield_scale),
        "Training_Bias": float(bias_std * yield_scale),
        "N_Training": int(valid.sum()),
    }


def fit_tuned_rf(X, y):
    # Historical-historical-compatible RF constructor.
    base_rf = RandomForestRegressor(
        random_state=RANDOM_STATE,
        oob_score=True,
    )

    gs = GridSearchCV(
        estimator=base_rf,
        param_grid=PARAM_GRID,
        cv=INNER_CV,
        scoring="r2",
        n_jobs=-1,
        refit=True,
        return_train_score=False,
    )

    gs.fit(X, y)
    return gs.best_estimator_, gs.best_params_, float(gs.best_score_)


def calculate_pdp(model, X, feature, grid):
    X_np = X.to_numpy(dtype=float)
    n_rows = len(X)
    n_grid = len(grid)
    idx = list(X.columns).index(feature)

    X_big = np.tile(X_np, (n_grid, 1))
    X_big[:, idx] = np.repeat(grid, n_rows)
    X_big = pd.DataFrame(X_big, columns=X.columns)

    pred = model.predict(X_big)

    return pred.reshape(n_grid, n_rows).mean(axis=1)


def interpolate_crossing(x1, x2, y1, y2, pv):
    if np.isclose(y1, y2):
        return (x1 + x2) / 2.0
    frac = (pv - y1) / (y2 - y1)
    return x1 + frac * (x2 - x1)


def find_tail_crossing(x, y, pv, direction):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if len(x) < 2:
        return None

    if direction == "lower":
        if y[0] >= pv:
            return None
        for i in range(len(x) - 1):
            if y[i] <= pv and y[i + 1] > pv:
                return float(
                    interpolate_crossing(
                        x[i], x[i + 1], y[i], y[i + 1], pv
                    )
                )
        return None

    if direction == "upper":
        if y[-1] >= pv:
            return None
        for i in range(len(x) - 2, -1, -1):
            if y[i] > pv and y[i + 1] <= pv:
                return float(
                    interpolate_crossing(
                        x[i], x[i + 1], y[i], y[i + 1], pv
                    )
                )
        return None

    raise ValueError(direction)



def find_all_crossings(
    x,
    y,
    pv,
):
    """Return ALL intersections of a PDP curve with PV."""

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if len(x) < 2:
        return []

    diff = y - float(pv)
    crossings = []

    for i in range(len(x) - 1):
        d1 = diff[i]
        d2 = diff[i + 1]

        if not np.isfinite(d1) or not np.isfinite(d2):
            continue

        if np.isclose(d1, 0.0):
            crossings.append(float(x[i]))

        if d1 * d2 < 0:
            den = d2 - d1
            if np.isclose(den, 0.0):
                continue

            t = -d1 / den
            if 0.0 <= t <= 1.0:
                crossings.append(
                    float(x[i] + t * (x[i + 1] - x[i]))
                )

    if np.isclose(diff[-1], 0.0):
        crossings.append(float(x[-1]))

    if len(crossings) == 0:
        return []

    return (
        np.unique(
            np.round(
                np.asarray(crossings, dtype=float),
                10,
            )
        )
        .astype(float)
        .tolist()
    )



def classify_mean_pdp_crossing_direction(
    x,
    y,
    pv,
    crossing,
):
    """
    Classify ONE PDP/PV crossing by the stress side it defines.

    lower:
        PDP is below PV immediately to the LEFT of the crossing and
        above PV immediately to the RIGHT.

    upper:
        PDP is above PV immediately to the LEFT of the crossing and
        below PV immediately to the RIGHT.

    This makes lower/upper STi candidates crossing-specific instead of
    allowing the same crossing to be selected for both directions.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    pv = float(pv)
    crossing = float(crossing)

    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    if len(x) < 2:
        return None

    order = np.argsort(x)
    x = x[order]
    y = y[order]

    # Use a very small feature-axis offset around the crossing and
    # linearly interpolate the PDP on either side.
    span = float(np.nanmax(x) - np.nanmin(x))
    if (not np.isfinite(span)) or span <= 0:
        return None

    eps = max(span * 1e-7, 1e-10)
    left_x = max(float(np.nanmin(x)), crossing - eps)
    right_x = min(float(np.nanmax(x)), crossing + eps)

    left_y = float(np.interp(left_x, x, y))
    right_y = float(np.interp(right_x, x, y))

    tol = max(1e-10, 1e-9 * max(1.0, abs(pv)))

    left_sign = np.sign(left_y - pv) if abs(left_y - pv) > tol else 0.0
    right_sign = np.sign(right_y - pv) if abs(right_y - pv) > tol else 0.0

    # If the tiny offset lands numerically on a flat/equal segment,
    # search outward for the nearest non-zero sign on each side.
    if left_sign == 0 or right_sign == 0:
        d = y - pv
        idx = int(np.searchsorted(x, crossing, side="left"))

        if left_sign == 0:
            for j in range(min(idx - 1, len(d) - 1), -1, -1):
                if np.isfinite(d[j]) and abs(d[j]) > tol:
                    left_sign = np.sign(d[j])
                    break

        if right_sign == 0:
            for j in range(max(idx, 0), len(d)):
                if np.isfinite(d[j]) and abs(d[j]) > tol:
                    right_sign = np.sign(d[j])
                    break

    if left_sign < 0 and right_sign > 0:
        return "lower"

    if left_sign > 0 and right_sign < 0:
        return "upper"

    return None


def _tail_stress_flags(
    x,
    y,
    pv,
):
    """
    Return lower/upper OUTER-tail stress flags for one mean PDP.

    IMPORTANT
    ---------
    Direction is determined by the actual terminal state of the PDP
    inside the observed feature range, not by the median of a wide
    10%-tail window.

    Why:
    A valid upper-tail crossing can occur late in the feature range.
    In that case, most of the last 10% of grid points may still lie
    above PV even though the PDP has genuinely crossed below PV near
    the high-feature boundary. Using a wide tail median would then
    incorrectly miss the upper stress direction.

    Therefore:
      lower stress -> left endpoint of mean PDP is below PV
      upper stress -> right endpoint of mean PDP is below PV

    A small 3-point terminal median is saved only as a diagnostic;
    it does NOT override the endpoint state.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    pv = float(pv)

    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    if len(x) < 2:
        return {
            "lower": False,
            "upper": False,
            "Lower_Tail_PDP": np.nan,
            "Upper_Tail_PDP": np.nan,
            "Lower_Terminal_Median": np.nan,
            "Upper_Terminal_Median": np.nan,
        }

    order = np.argsort(x)
    y = y[order]

    tol = max(
        1e-10,
        1e-9 * max(1.0, abs(pv)),
    )

    lower_endpoint = float(y[0])
    upper_endpoint = float(y[-1])

    n_terminal = min(
        len(y),
        max(2, min(3, len(y))),
    )

    lower_terminal_median = float(
        np.nanmedian(y[:n_terminal])
    )

    upper_terminal_median = float(
        np.nanmedian(y[-n_terminal:])
    )

    return {
        "lower": bool(
            np.isfinite(lower_endpoint)
            and lower_endpoint < pv - tol
        ),
        "upper": bool(
            np.isfinite(upper_endpoint)
            and upper_endpoint < pv - tol
        ),

        # Keep these established field names for downstream tables,
        # but they now report the actual terminal PDP values.
        "Lower_Tail_PDP": lower_endpoint,
        "Upper_Tail_PDP": upper_endpoint,

        # Additional diagnostics.
        "Lower_Terminal_Median": lower_terminal_median,
        "Upper_Terminal_Median": upper_terminal_median,
    }

def filter_crossings_by_direction(
    crossings,
    x,
    y,
    pv,
    direction,
    require_outer_tail=True,
):
    """
    Return ALL crossings compatible with the requested stress direction.

    By default, the requested OUTER tail must also be stressed. This is
    the normal threshold mode. For an OFS feature with an interior-only
    PDP stress pocket, ``require_outer_tail=False`` keeps crossing-defined
    candidates even when neither endpoint is stress-side. Those candidates
    are then compared by density-based Auto-STa performance and only ONE
    direction is retained for the fixed signature.

    lower crossing: PDP below PV on the left and above PV on the right.
    upper crossing: PDP above PV on the left and below PV on the right.

    Downstream code derives an STa for EACH retained STi and selects the
    STi+STa pair with the best final Sh/No/Bo separation.
    """
    if direction not in {"lower", "upper"}:
        raise ValueError(direction)

    if require_outer_tail:
        tail_flags = _tail_stress_flags(x=x, y=y, pv=pv)
        if not tail_flags[direction]:
            return []

    arr = np.asarray(crossings, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return []

    arr = np.sort(np.unique(np.round(arr, 10)))
    directional = []

    for crossing in arr:
        cdir = classify_mean_pdp_crossing_direction(
            x=x,
            y=y,
            pv=pv,
            crossing=float(crossing),
        )
        if cdir == direction:
            directional.append(float(crossing))

    if directional:
        return (
            np.sort(np.unique(np.round(np.asarray(directional), 10)))
            .astype(float)
            .tolist()
        )

    # Fallback for very flat/step-like PDPs where local sign
    # classification becomes numerically ambiguous.
    direct = find_tail_crossing(x=x, y=y, pv=pv, direction=direction)
    if direct is not None and np.isfinite(direct):
        return [float(direct)]

    return []

def pick_nearest_crossing(
    candidates,
    reference,
):
    if candidates is None or len(candidates) == 0:
        return None

    arr = np.asarray(candidates, dtype=float)
    arr = arr[np.isfinite(arr)]

    if len(arr) == 0:
        return None

    idx = int(np.argmin(np.abs(arr - float(reference))))
    return float(arr[idx])



def _mean_pdp_has_crossing(
    x_raw,
    mean_curve,
    pv,
):
    """True when the supplied PV has any sampled mean-PDP intersection."""
    crossings = find_all_crossings(
        x=x_raw,
        y=mean_curve,
        pv=float(pv),
    )

    return len(crossings) > 0


def _mean_pdp_directional_crossing_info(
    x_raw,
    mean_curve,
    pv,
):
    """
    Return all mean-PDP/PV intersections and the VALID local stress
    directions they define.

    A tangential touch is not a valid directional crossing because the PDP
    remains on the same side of PV on both sides of the contact point.
    """
    crossings = find_all_crossings(
        x=x_raw,
        y=mean_curve,
        pv=float(pv),
    )

    directions = []

    for crossing in crossings:
        cdir = classify_mean_pdp_crossing_direction(
            x=x_raw,
            y=mean_curve,
            pv=float(pv),
            crossing=float(crossing),
        )

        if cdir in {"lower", "upper"} and cdir not in directions:
            directions.append(cdir)

    directions = [d for d in ["lower", "upper"] if d in directions]

    return crossings, directions


def resolve_feature_pv_for_crossing(
    x_raw,
    mean_curve,
    original_pv,
    sh_yield_mean,
):
    """
    Resolve the feature-specific PV BEFORE STi detection.

    Primary rule
    ------------
    Keep the original PV when it already produces at least one VALID
    directional crossing.

    Fixed-step rescue
    -----------------
    Otherwise move PV toward the Sh-yield mean in fixed increments of
    ``PV_RESCUE_STEP`` (0.05 by default) and stop at the FIRST stepped PV
    producing at least one valid lower/upper directional crossing.

    The search cannot reach or pass the midpoint from the original No-mean PV
    to the Sh-yield mean. Thus the rescued PV remains closer to the No mean
    than to the Sh mean.

    ``PV_Adjustment_Alpha`` is retained only as a backward-compatible
    diagnostic fraction. It is NOT used to search for the rescued PV.
    """

    original_pv = float(original_pv)
    sh_yield_mean = float(sh_yield_mean)
    mean_curve = np.asarray(mean_curve, dtype=float)

    finite_curve = mean_curve[np.isfinite(mean_curve)]

    if len(finite_curve) == 0:
        return {
            "Original_PV": original_pv,
            "Sh_Yield_Mean": sh_yield_mean,
            "PV_Used": original_pv,
            "PV_Adjusted": False,
            "PV_Adjustment_Alpha": np.nan,
            "PV_Adjustment_Signed": 0.0,
            "PV_Adjustment_Absolute": 0.0,
            "Original_PV_Has_Crossing": False,
            "PV_Used_Has_Crossing": False,
            "Original_PV_Has_Any_Intersection": False,
            "PV_Used_Has_Any_Intersection": False,
            "PV_Rescue_Step": float(PV_RESCUE_STEP),
            "PV_Rescue_N_Steps": 0,
            "PV_Valid_Directions": "",
            "PV_Adjustment_Status": "NO_FINITE_MEAN_PDP",
        }

    original_any = _mean_pdp_has_crossing(
        x_raw=x_raw,
        mean_curve=mean_curve,
        pv=original_pv,
    )

    _original_crossings, original_dirs = _mean_pdp_directional_crossing_info(
        x_raw=x_raw,
        mean_curve=mean_curve,
        pv=original_pv,
    )

    # Original PV is accepted only for a REAL directional crossing, not merely
    # a tangential contact with the PDP.
    if len(original_dirs) > 0:
        return {
            "Original_PV": original_pv,
            "Sh_Yield_Mean": sh_yield_mean,
            "PV_Used": original_pv,
            "PV_Adjusted": False,
            "PV_Adjustment_Alpha": 0.0,
            "PV_Adjustment_Signed": 0.0,
            "PV_Adjustment_Absolute": 0.0,
            "Original_PV_Has_Crossing": True,
            "PV_Used_Has_Crossing": True,
            "Original_PV_Has_Any_Intersection": bool(original_any),
            "PV_Used_Has_Any_Intersection": bool(original_any),
            "PV_Rescue_Step": float(PV_RESCUE_STEP),
            "PV_Rescue_N_Steps": 0,
            "PV_Valid_Directions": "; ".join(original_dirs),
            "PV_Adjustment_Status": "ORIGINAL_PV_VALID_DIRECTIONAL_CROSSING",
        }

    if not AUTO_ADJUST_PV_IF_NO_CROSSING:
        return {
            "Original_PV": original_pv,
            "Sh_Yield_Mean": sh_yield_mean,
            "PV_Used": original_pv,
            "PV_Adjusted": False,
            "PV_Adjustment_Alpha": np.nan,
            "PV_Adjustment_Signed": 0.0,
            "PV_Adjustment_Absolute": 0.0,
            "Original_PV_Has_Crossing": False,
            "PV_Used_Has_Crossing": False,
            "Original_PV_Has_Any_Intersection": bool(original_any),
            "PV_Used_Has_Any_Intersection": bool(original_any),
            "PV_Rescue_Step": float(PV_RESCUE_STEP),
            "PV_Rescue_N_Steps": 0,
            "PV_Valid_Directions": "",
            "PV_Adjustment_Status": "PV_RESCUE_DISABLED",
        }

    if (
        not np.isfinite(sh_yield_mean)
        or np.isclose(sh_yield_mean, original_pv)
    ):
        return {
            "Original_PV": original_pv,
            "Sh_Yield_Mean": sh_yield_mean,
            "PV_Used": original_pv,
            "PV_Adjusted": False,
            "PV_Adjustment_Alpha": np.nan,
            "PV_Adjustment_Signed": 0.0,
            "PV_Adjustment_Absolute": 0.0,
            "Original_PV_Has_Crossing": False,
            "PV_Used_Has_Crossing": False,
            "Original_PV_Has_Any_Intersection": bool(original_any),
            "PV_Used_Has_Any_Intersection": bool(original_any),
            "PV_Rescue_Step": float(PV_RESCUE_STEP),
            "PV_Rescue_N_Steps": 0,
            "PV_Valid_Directions": "",
            "PV_Adjustment_Status": "NO_VALID_SH_YIELD_LEVEL_FOR_PV_RESCUE",
        }

    step = abs(float(PV_RESCUE_STEP))

    if (not np.isfinite(step)) or step <= 0.0:
        raise ValueError("PV_RESCUE_STEP must be a positive finite number.")

    max_fraction = float(PV_RESCUE_MAX_FRACTION_TOWARD_SH)

    if not (0.0 < max_fraction <= 0.5):
        raise ValueError(
            "PV_RESCUE_MAX_FRACTION_TOWARD_SH must be in (0, 0.5]."
        )

    delta = sh_yield_mean - original_pv
    move_sign = 1.0 if delta > 0 else -1.0
    total_distance = abs(delta)

    # Fixed-step search. We deliberately do NOT evaluate a fractional final
    # step at the midpoint: the user-defined rescue grid is exactly 0.05.
    n_steps = 0
    last_fraction = np.nan
    last_pv = original_pv
    last_any = bool(original_any)

    while True:
        n_steps += 1
        pv_try = original_pv + move_sign * step * n_steps
        fraction_toward_sh = abs(pv_try - original_pv) / total_distance

        # Preserve the original guardrail: rescued PV must remain strictly
        # closer to No than to Sh, so do not reach/pass the midpoint.
        if fraction_toward_sh >= max_fraction:
            break

        last_fraction = float(fraction_toward_sh)
        last_pv = float(pv_try)

        any_intersection = _mean_pdp_has_crossing(
            x_raw=x_raw,
            mean_curve=mean_curve,
            pv=pv_try,
        )

        _crossings, valid_dirs = _mean_pdp_directional_crossing_info(
            x_raw=x_raw,
            mean_curve=mean_curve,
            pv=pv_try,
        )

        last_any = bool(any_intersection)

        if len(valid_dirs) > 0:
            signed_shift = float(pv_try - original_pv)

            return {
                "Original_PV": original_pv,
                "Sh_Yield_Mean": sh_yield_mean,
                "PV_Used": float(pv_try),
                "PV_Adjusted": True,
                "PV_Adjustment_Alpha": float(fraction_toward_sh),
                "PV_Adjustment_Signed": signed_shift,
                "PV_Adjustment_Absolute": abs(signed_shift),
                "Original_PV_Has_Crossing": False,
                "PV_Used_Has_Crossing": True,
                "Original_PV_Has_Any_Intersection": bool(original_any),
                "PV_Used_Has_Any_Intersection": bool(any_intersection),
                "PV_Rescue_Step": step,
                "PV_Rescue_N_Steps": int(n_steps),
                "PV_Valid_Directions": "; ".join(valid_dirs),
                "PV_Adjustment_Status": (
                    "AUTO_ADJUSTED_TOWARD_SH_FIXED_STEP_FIRST_DIRECTIONAL_CROSSING"
                ),
            }

        # Hard safety against malformed numeric inputs. Under the midpoint rule
        # this should never be approached in real data.
        if n_steps > 100000:
            raise RuntimeError("PV fixed-step rescue exceeded 100000 iterations.")

    return {
        "Original_PV": original_pv,
        "Sh_Yield_Mean": sh_yield_mean,
        "PV_Used": original_pv,
        "PV_Adjusted": False,
        "PV_Adjustment_Alpha": (
            float(last_fraction) if np.isfinite(last_fraction) else np.nan
        ),
        "PV_Adjustment_Signed": 0.0,
        "PV_Adjustment_Absolute": 0.0,
        "Original_PV_Has_Crossing": False,
        "PV_Used_Has_Crossing": False,
        "Original_PV_Has_Any_Intersection": bool(original_any),
        "PV_Used_Has_Any_Intersection": bool(last_any),
        "PV_Rescue_Step": step,
        "PV_Rescue_N_Steps": int(max(0, n_steps - 1)),
        "PV_Valid_Directions": "",
        "PV_Adjustment_Status": (
            "NO_VALID_DIRECTIONAL_CROSSING_ON_FIXED_STEP_GRID_BEFORE_MIDPOINT"
        ),
    }


def derive_best_multi_crossing_threshold(
    training_raw,
    class_col,
    feature,
    direction,
    x_raw,
    mean_curve,
    curves_raw,
    pv,
    require_outer_tail=True,
):
    """
    Evaluate every mean-PDP/PV crossing as a possible STi.

    For each STi:
      - align bootstrap crossings to it by nearest distance;
      - derive its own uncertainty interval;
      - select Auto-STa with the 3-criterion Utopia method.

    If multiple STi candidates exist, every same-direction crossing
    is retained. Each crossing derives its own FINAL Auto-STa with
    Pareto + Linear 4:2:3, and the STi+STa pairs are compared using
    the same Sh/No/Bo objectives and final Linear 4:2:3 score.

    Bootstrap support is used only as a tie-breaker.

    """

    all_mean_crossings = find_all_crossings(
        x=x_raw,
        y=mean_curve,
        pv=pv,
    )

    # IMPORTANT: each lower/upper rule may only use crossings that
    # actually define that stress direction. This prevents the same
    # crossing from being selected for both lower and upper STi.
    mean_crossings = filter_crossings_by_direction(
        crossings=all_mean_crossings,
        x=x_raw,
        y=mean_curve,
        pv=pv,
        direction=direction,
        require_outer_tail=require_outer_tail,
    )

    if not USE_MULTIPLE_STI_CANDIDATES:

        one = find_tail_crossing(
            x_raw,
            mean_curve,
            pv,
            direction,
        )

        mean_crossings = (
            []
            if one is None
            else [
                float(
                    one
                )
            ]
        )

    if len(
        mean_crossings
    ) == 0:
        return (
            None,
            pd.DataFrame(),
            pd.DataFrame(),
        )

    candidate_rows = []
    sta_detail_tables = []

    all_crossings_text = "; ".join(
        f"{float(v):.10g}"
        for v
        in mean_crossings
    )

    for candidate_index, sti in enumerate(
        mean_crossings,
        start=1,
    ):

        aligned = []

        for b in range(
            curves_raw.shape[
                0
            ]
        ):

            boot_candidates_all = (
                find_all_crossings(
                    x=x_raw,
                    y=curves_raw[
                        b
                    ],
                    pv=pv,
                )
            )

            boot_candidates = filter_crossings_by_direction(
                crossings=boot_candidates_all,
                x=x_raw,
                y=curves_raw[b],
                pv=pv,
                direction=direction,
                require_outer_tail=require_outer_tail,
            )

            picked = (
                pick_nearest_crossing(
                    candidates=
                        boot_candidates,
                    reference=
                        sti,
                )
            )

            if (
                picked is not None
                and
                np.isfinite(
                    picked
                )
            ):
                aligned.append(
                    float(
                        picked
                    )
                )

        aligned = np.asarray(
            aligned,
            dtype=float,
        )

        n_valid = int(
            len(
                aligned
            )
        )

        support = (
            n_valid
            / curves_raw.shape[
                0
            ]
        )

        if (
            n_valid
            >= MIN_ALIGNED_BOOTSTRAP_CROSSINGS
        ):

            ci_lower = float(
                np.quantile(
                    aligned,
                    0.025,
                )
            )

            ci_upper = float(
                np.quantile(
                    aligned,
                    0.975,
                )
            )

            bootstrap_interval_status = (
                "ALIGNED_BOOTSTRAP_INTERVAL"
            )

        else:

            ci_lower = float(
                sti
            )

            ci_upper = float(
                sti
            )

            bootstrap_interval_status = (
                "INSUFFICIENT_ALIGNED_BOOTSTRAPS_FALLBACK_TO_STi"
            )

        (
            sta,
            sta_reason,
            candidate_df,
        ) = derive_conservative_sta(
            training_raw=
                training_raw,
            class_col=
                class_col,
            feature=
                feature,
            direction=
                direction,
            sti=
                float(
                    sti
                ),
            ci_lower=
                ci_lower,
            ci_upper=
                ci_upper,
        )

        # Evaluate THIS STi with the same final Auto-STa rule used in
        # the published signature: Pareto + Linear 4:2:3.
        final_sta_row_for_sti = None

        if candidate_df is not None and not candidate_df.empty:
            (
                final_sta_row_for_sti,
                candidate_df_linear,
            ) = refine_selected_sta_with_linear_423(
                selected_sti_candidate_df=candidate_df,
                direction=direction,
            )

            if final_sta_row_for_sti is not None:
                sta = float(final_sta_row_for_sti["Candidate"])
                sta_reason = "FINAL_PARETO_LINEAR_4_2_3_PER_STi"
                candidate_df = candidate_df_linear.copy()
                candidate_df["Selected_Auto_STa"] = np.isclose(
                    candidate_df["Candidate"].astype(float),
                    float(sta),
                )

        sti_eval = (
            evaluate_threshold_candidate(
                training_raw=
                    training_raw,
                class_col=
                    class_col,
                feature=
                    feature,
                threshold=
                    float(
                        sti
                    ),
                direction=
                    direction,
                sti=
                    float(
                        sti
                    ),
            )
        )

        auto_eval = (
            evaluate_threshold_candidate(
                training_raw=
                    training_raw,
                class_col=
                    class_col,
                feature=
                    feature,
                threshold=
                    float(
                        sta
                    ),
                direction=
                    direction,
                sti=
                    float(
                        sti
                    ),
            )
        )

        # Auto-STa Utopia diagnostics for this STi.
        if (
            not candidate_df.empty
            and
            "Selected_Auto_STa"
            in candidate_df.columns
            and
            candidate_df[
                "Selected_Auto_STa"
            ].astype(bool).any()
        ):

            auto_row = (
                candidate_df.loc[
                    candidate_df[
                        "Selected_Auto_STa"
                    ].astype(bool)
                ]
                .iloc[0]
            )

            sh_median = float(
                auto_row[
                    "Sh_Median"
                ]
            )

            bo_median = float(
                auto_row[
                    "Bo_Median"
                ]
            )

            distance_to_sh = float(
                auto_row[
                    "Distance_to_Sh_Median"
                ]
            )

            distance_to_bo = float(
                auto_row[
                    "Distance_to_Bo_Median"
                ]
            )

            sh_no_separation = float(
                auto_row[
                    "ShNo_Separation"
                ]
            )

            local_utopia_distance = float(
                auto_row[
                    "Utopia_Distance"
                ]
            )

        else:

            sh_median = np.nan
            bo_median = np.nan
            distance_to_sh = np.nan
            distance_to_bo = np.nan
            sh_no_separation = np.nan
            local_utopia_distance = np.nan

        directional_margin = (
            abs(
                float(
                    sti
                )
                - ci_lower
            )
            if direction
            == "lower"
            else
            abs(
                ci_upper
                - float(
                    sti
                )
            )
        )

        if final_sta_row_for_sti is not None:
            final_linear_score = float(
                final_sta_row_for_sti.get(
                    "Final_Linear_4_2_3_Score",
                    np.nan,
                )
            )
            final_sta_distance_from_sti = float(
                final_sta_row_for_sti.get(
                    "Distance_From_STi",
                    abs(float(sta) - float(sti)),
                )
            )
        else:
            final_linear_score = (
                FINAL_STA_LINEAR_W_SH * float(auto_eval["Sh_Hit"])
                - FINAL_STA_LINEAR_W_NO * float(auto_eval["No_Hit"])
                - FINAL_STA_LINEAR_W_BO * float(auto_eval["Bo_Hit"])
            )
            final_sta_distance_from_sti = abs(float(sta) - float(sti))

        candidate_rows.append({
            "Feature":
                feature,

            "Direction":
                direction,

            "STi_Candidate_Index":
                candidate_index,

            "N_Mean_PDP_Crossings":
                len(
                    mean_crossings
                ),

            "All_Mean_PDP_Crossings":
                all_crossings_text,

            "STi_Candidate":
                float(
                    sti
                ),

            "CI_Lower":
                ci_lower,

            "CI_Upper":
                ci_upper,

            "Directional_Margin":
                directional_margin,

            "Bootstrap_N_Valid":
                n_valid,

            "Bootstrap_Support":
                support,

            "Bootstrap_Interval_Status":
                bootstrap_interval_status,

            "Auto_STa_Candidate":
                float(
                    sta
                ),

            "Auto_STa_Selection":
                sta_reason,

            "STi_Sh_Hit":
                sti_eval[
                    "Sh_Hit"
                ],

            "STi_No_Hit":
                sti_eval[
                    "No_Hit"
                ],

            "STi_Bo_Hit":
                sti_eval[
                    "Bo_Hit"
                ],

            "STi_Separation_Score":
                sti_eval[
                    "Score"
                ],

            "Auto_STa_Sh_Hit":
                auto_eval[
                    "Sh_Hit"
                ],

            "Auto_STa_No_Hit":
                auto_eval[
                    "No_Hit"
                ],

            "Auto_STa_Bo_Hit":
                auto_eval[
                    "Bo_Hit"
                ],

            "Auto_STa_Separation_Score":
                auto_eval[
                    "Score"
                ],

            "Auto_STa_Final_Linear_4_2_3_Score":
                final_linear_score,

            "Auto_STa_Distance_From_STi":
                final_sta_distance_from_sti,

            "Auto_STa_ShNo_Separation":
                sh_no_separation,

            "Auto_STa_Distance_to_Sh_Median":
                distance_to_sh,

            "Auto_STa_Distance_to_Bo_Median":
                distance_to_bo,

            "Auto_STa_Local_Utopia_Distance":
                local_utopia_distance,

            "Sh_Median":
                sh_median,

            "Bo_Median":
                bo_median,
        })

        if not candidate_df.empty:

            detail = candidate_df.copy()

            detail.insert(
                0,
                "STi_Candidate_Index",
                candidate_index,
            )

            detail.insert(
                1,
                "STi_Candidate",
                float(
                    sti
                ),
            )

            detail.insert(
                2,
                "STi_Candidate_CI_Lower",
                ci_lower,
            )

            detail.insert(
                3,
                "STi_Candidate_CI_Upper",
                ci_upper,
            )

            detail.insert(
                4,
                "STi_Candidate_Bootstrap_Support",
                support,
            )

            sta_detail_tables.append(
                detail
            )

    candidate_table = pd.DataFrame(
        candidate_rows
    )

    # --------------------------------------------------------
    # Select among multiple STi+STa pairs by the FINAL STa outcome.
    #
    # Every same-direction crossing is an STi candidate. Each has
    # already generated its own final STa using Pareto + Linear 4:2:3.
    # We first remove dominated STi+STa pairs (maximize Sh_Hit,
    # minimize No_Hit and Bo_Hit), then select the pair with the
    # highest final Linear 4:2:3 score.
    # --------------------------------------------------------

    candidate_table["STi_C1_Sh_Proximity"] = np.nan
    candidate_table["STi_C2_Bo_Distance"] = np.nan
    candidate_table["STi_C3_ShNo_Separation"] = np.nan
    candidate_table["STi_Selection_Utopia_Distance"] = np.nan
    candidate_table["STi_Pareto_Efficient_Final_STa"] = False
    candidate_table["STi_Selection_Method"] = "PARETO_FINAL_STa_LINEAR_4_2_3"

    # Keep the old three-criterion values as diagnostics only.
    diag_valid = candidate_table[
        candidate_table["Auto_STa_Distance_to_Sh_Median"].notna()
        & candidate_table["Auto_STa_Distance_to_Bo_Median"].notna()
        & candidate_table["Auto_STa_ShNo_Separation"].notna()
    ].copy()

    if not diag_valid.empty:
        diag_valid["STi_C1_Sh_Proximity"] = _normalize_benefit(
            -diag_valid["Auto_STa_Distance_to_Sh_Median"].to_numpy(float)
        )
        diag_valid["STi_C2_Bo_Distance"] = _normalize_benefit(
            diag_valid["Auto_STa_Distance_to_Bo_Median"].to_numpy(float)
        )
        diag_valid["STi_C3_ShNo_Separation"] = _normalize_benefit(
            diag_valid["Auto_STa_ShNo_Separation"].to_numpy(float)
        )
        diag_valid["STi_Selection_Utopia_Distance"] = np.sqrt(
            (
                (1.0 - diag_valid["STi_C1_Sh_Proximity"]) ** 2
                + (1.0 - diag_valid["STi_C2_Bo_Distance"]) ** 2
                + (1.0 - diag_valid["STi_C3_ShNo_Separation"]) ** 2
            ) / 3.0
        )
        for col in [
            "STi_C1_Sh_Proximity",
            "STi_C2_Bo_Distance",
            "STi_C3_ShNo_Separation",
            "STi_Selection_Utopia_Distance",
        ]:
            mapping = dict(zip(
                diag_valid["STi_Candidate_Index"].astype(int),
                diag_valid[col],
            ))
            candidate_table[col] = candidate_table["STi_Candidate_Index"].astype(int).map(mapping)

    valid = candidate_table[
        candidate_table["Auto_STa_Final_Linear_4_2_3_Score"].notna()
        & candidate_table["Auto_STa_Sh_Hit"].notna()
        & candidate_table["Auto_STa_No_Hit"].notna()
        & candidate_table["Auto_STa_Bo_Hit"].notna()
    ].copy()

    if not valid.empty:
        pareto_flags = []
        for i, a in valid.iterrows():
            dominated = False
            for j, b in valid.iterrows():
                if i == j:
                    continue
                at_least_as_good = (
                    float(b["Auto_STa_Sh_Hit"]) >= float(a["Auto_STa_Sh_Hit"])
                    and float(b["Auto_STa_No_Hit"]) <= float(a["Auto_STa_No_Hit"])
                    and float(b["Auto_STa_Bo_Hit"]) <= float(a["Auto_STa_Bo_Hit"])
                )
                strictly_better = (
                    float(b["Auto_STa_Sh_Hit"]) > float(a["Auto_STa_Sh_Hit"])
                    or float(b["Auto_STa_No_Hit"]) < float(a["Auto_STa_No_Hit"])
                    or float(b["Auto_STa_Bo_Hit"]) < float(a["Auto_STa_Bo_Hit"])
                )
                if at_least_as_good and strictly_better:
                    dominated = True
                    break
            pareto_flags.append(not dominated)

        valid["STi_Pareto_Efficient_Final_STa"] = pareto_flags
        pareto = valid.loc[valid["STi_Pareto_Efficient_Final_STa"]].copy()
        if pareto.empty:
            pareto = valid.copy()

        pareto_idx = set(pareto["STi_Candidate_Index"].astype(int).tolist())
        candidate_table["STi_Pareto_Efficient_Final_STa"] = (
            candidate_table["STi_Candidate_Index"].astype(int).isin(pareto_idx)
        )

        ranked = pareto.sort_values(
            [
                "Auto_STa_Final_Linear_4_2_3_Score",
                "Auto_STa_Sh_Hit",
                "Auto_STa_Bo_Hit",
                "Auto_STa_No_Hit",
                "Bootstrap_Support",
                "Auto_STa_Distance_From_STi",
                "STi_Candidate_Index",
            ],
            ascending=[False, False, True, True, False, True, True],
        ).reset_index(drop=True)

        selected_index = int(ranked.iloc[0]["STi_Candidate_Index"])
    else:
        ranked = candidate_table.sort_values(
            ["Bootstrap_Support", "STi_Candidate_Index"],
            ascending=[False, True],
        ).reset_index(drop=True)
        selected_index = int(ranked.iloc[0]["STi_Candidate_Index"])

    candidate_table[
        "Selected_Automatically"
    ] = (
        candidate_table[
            "STi_Candidate_Index"
        ].astype(int)
        == selected_index
    )

    selected = (
        candidate_table.loc[
            candidate_table[
                "Selected_Automatically"
            ]
        ]
        .iloc[0]
        .to_dict()
    )

    if sta_detail_tables:

        sta_details = pd.concat(
            sta_detail_tables,
            ignore_index=True,
        )

        sta_details[
            "Selected_STi_Candidate"
        ] = (
            sta_details[
                "STi_Candidate_Index"
            ].astype(int)
            == selected_index
        )

        # ====================================================
        # FINAL STa REFINEMENT
        #
        # STi has ALREADY been selected above by the ORIGINAL
        # uploaded-code logic. Nothing below can change STi.
        # ====================================================

        selected_sti_candidates = (
            sta_details.loc[
                sta_details[
                    "STi_Candidate_Index"
                ].astype(int)
                == int(
                    selected_index
                )
            ]
            .copy()
        )

        (
            final_sta_row,
            final_sta_candidates,
        ) = refine_selected_sta_with_linear_423(
            selected_sti_candidates,
            direction=direction,
        )

        if (
            final_sta_row
            is not None
        ):

            # Final STa only. STi / CI / support remain exactly
            # those selected by the original multi-STi logic.
            selected[
                "Auto_STa_Candidate"
            ] = float(
                final_sta_row[
                    "Candidate"
                ]
            )

            selected[
                "Auto_STa_Selection"
            ] = (
                "FINAL_PARETO_LINEAR_4_2_3"
            )

            selected[
                "Auto_STa_Sh_Hit"
            ] = float(
                final_sta_row[
                    "Sh_Hit"
                ]
            )

            selected[
                "Auto_STa_No_Hit"
            ] = float(
                final_sta_row[
                    "No_Hit"
                ]
            )

            selected[
                "Auto_STa_Bo_Hit"
            ] = float(
                final_sta_row[
                    "Bo_Hit"
                ]
            )

            selected[
                "Auto_STa_ShNo_Separation"
            ] = float(
                final_sta_row[
                    "ShNo_Separation"
                ]
            )

            # Compatibility diagnostic retained from the earlier code.
            selected[
                "Auto_STa_Separation_Score"
            ] = float(
                final_sta_row[
                    "Final_Balanced_Class_Utility"
                ]
            )

            # NEW: actual criterion used for FINAL STa selection.
            selected[
                "Auto_STa_Final_Linear_4_2_3_Score"
            ] = float(
                final_sta_row[
                    "Final_Linear_4_2_3_Score"
                ]
            )

            # Preserve these existing diagnostics if available.
            if (
                "Distance_to_Sh_Median"
                in final_sta_row
            ):
                selected[
                    "Auto_STa_Distance_to_Sh_Median"
                ] = float(
                    final_sta_row[
                        "Distance_to_Sh_Median"
                    ]
                )

            if (
                "Distance_to_Bo_Median"
                in final_sta_row
            ):
                selected[
                    "Auto_STa_Distance_to_Bo_Median"
                ] = float(
                    final_sta_row[
                        "Distance_to_Bo_Median"
                    ]
                )

            if (
                "Utopia_Distance"
                in final_sta_row
            ):
                selected[
                    "Auto_STa_Local_Utopia_Distance"
                ] = float(
                    final_sta_row[
                        "Utopia_Distance"
                    ]
                )

            if (
                "Sh_Median"
                in final_sta_row
            ):
                selected[
                    "Sh_Median"
                ] = float(
                    final_sta_row[
                        "Sh_Median"
                    ]
                )

            if (
                "Bo_Median"
                in final_sta_row
            ):
                selected[
                    "Bo_Median"
                ] = float(
                    final_sta_row[
                        "Bo_Median"
                    ]
                )

            # Update the selected STi row in the candidate table
            # so saved diagnostics show the FINAL STa as well.
            selected_mask = (
                candidate_table[
                    "STi_Candidate_Index"
                ].astype(int)
                == int(
                    selected_index
                )
            )

            candidate_table.loc[
                selected_mask,
                "Auto_STa_Candidate",
            ] = selected[
                "Auto_STa_Candidate"
            ]

            candidate_table.loc[
                selected_mask,
                "Auto_STa_Selection",
            ] = selected[
                "Auto_STa_Selection"
            ]

            candidate_table.loc[
                selected_mask,
                "Auto_STa_Sh_Hit",
            ] = selected[
                "Auto_STa_Sh_Hit"
            ]

            candidate_table.loc[
                selected_mask,
                "Auto_STa_No_Hit",
            ] = selected[
                "Auto_STa_No_Hit"
            ]

            candidate_table.loc[
                selected_mask,
                "Auto_STa_Bo_Hit",
            ] = selected[
                "Auto_STa_Bo_Hit"
            ]

            candidate_table.loc[
                selected_mask,
                "Auto_STa_ShNo_Separation",
            ] = selected[
                "Auto_STa_ShNo_Separation"
            ]

            candidate_table.loc[
                selected_mask,
                "Auto_STa_Separation_Score",
            ] = selected[
                "Auto_STa_Separation_Score"
            ]

            candidate_table.loc[
                selected_mask,
                "Auto_STa_Final_Linear_4_2_3_Score",
            ] = selected[
                "Auto_STa_Final_Linear_4_2_3_Score"
            ]

            # Save the refined candidate diagnostics too.
            sta_details[
                "Selected_Final_STa_Linear_4_2_3"
            ] = False

            if (
                not final_sta_candidates.empty
            ):

                chosen_value = float(
                    selected[
                        "Auto_STa_Candidate"
                    ]
                )

                final_mask = (
                    sta_details[
                        "STi_Candidate_Index"
                    ].astype(int)
                    == int(
                        selected_index
                    )
                ) & (
                    np.isclose(
                        sta_details[
                            "Candidate"
                        ].astype(float),
                        chosen_value,
                    )
                )

                sta_details.loc[
                    final_mask,
                    "Selected_Final_STa_Linear_4_2_3",
                ] = True

    else:

        sta_details = pd.DataFrame()

    return (
        selected,
        candidate_table,
        sta_details,
    )


def bootstrap_pdp_run(seed, X, y, grids_std, best_params):
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(X), size=len(X), replace=True)

    Xb = X.iloc[idx].reset_index(drop=True)
    yb = y.iloc[idx].reset_index(drop=True)

    rf = RandomForestRegressor(
        **best_params,
        random_state=seed,
        bootstrap=True,
        n_jobs=1,
    )

    rf.fit(Xb, yb)

    # IMPORTANT:
    # Evaluate exactly the feature set represented by grids_std.
    # During automatic OFS discovery/backfill, X can contain a temporary
    # selected subset that is different from the global FIXED_FEATURES list.
    # Iterating over FIXED_FEATURES here can therefore request a feature whose
    # grid does not exist and raise KeyError.
    pdp_features = list(grids_std.keys())

    missing_in_X = [
        feature
        for feature in pdp_features
        if feature not in Xb.columns
    ]

    if missing_in_X:
        raise ValueError(
            "bootstrap_pdp_run received PDP grid features missing from X: "
            f"{missing_in_X}"
        )

    return {
        feature: calculate_pdp(
            rf,
            Xb,
            feature,
            grids_std[feature],
        )
        for feature in pdp_features
    }


def class_hit_rate(
    training_raw,
    class_col,
    feature,
    threshold,
    direction,
    class_name,
):
    values = (
        training_raw.loc[
            training_raw[class_col].astype(str) == class_name,
            feature,
        ]
        .dropna()
        .astype(float)
        .to_numpy()
    )

    if len(values) == 0:
        return np.nan

    if direction == "lower":
        return float(np.mean(values <= threshold))

    if direction == "upper":
        return float(np.mean(values >= threshold))

    raise ValueError(direction)


def evaluate_threshold_candidate(
    training_raw,
    class_col,
    feature,
    threshold,
    direction,
    sti,
):
    """
    Diagnostic class-hit statistics for one threshold.

    Score is kept for compatibility, but automatic STa selection
    is performed with the explicit three-criterion Utopia method.
    """

    sh = class_hit_rate(
        training_raw,
        class_col,
        feature,
        threshold,
        direction,
        "Sh",
    )

    no = class_hit_rate(
        training_raw,
        class_col,
        feature,
        threshold,
        direction,
        "No",
    )

    bo = class_hit_rate(
        training_raw,
        class_col,
        feature,
        threshold,
        direction,
        "Bo",
    )

    if (
        np.isfinite(sh)
        and
        np.isfinite(no)
        and
        np.isfinite(bo)
    ):
        sh_no_separation = (
            sh
            - no
        )

        balanced_3class_score = (
            sh
            + (
                1.0
                - no
            )
            + (
                1.0
                - bo
            )
        ) / 3.0

    else:
        sh_no_separation = np.nan
        balanced_3class_score = np.nan

    return {
        "Candidate":
            float(
                threshold
            ),

        "Sh_Hit":
            sh,

        "No_Hit":
            no,

        "Bo_Hit":
            bo,

        "ShNo_Separation":
            sh_no_separation,

        "Balanced_3Class_Score":
            balanced_3class_score,

        # Compatibility field used by some downstream summaries.
        "Score":
            balanced_3class_score,

        "Distance_From_STi":
            abs(
                float(
                    threshold
                )
                - float(
                    sti
                )
            ),
    }


def _normalize_benefit(
    values,
):
    """
    Min-max normalize a BENEFIT criterion to 0..1.

    Higher raw value = better.

    If all valid candidates are identical on one criterion,
    every valid candidate receives 1.0 so that this criterion
    does not artificially favor any threshold.
    """

    arr = np.asarray(
        values,
        dtype=float,
    )

    out = np.full(
        arr.shape,
        np.nan,
        dtype=float,
    )

    valid = np.isfinite(
        arr
    )

    if valid.sum() == 0:
        return out

    lo = float(
        np.nanmin(
            arr[
                valid
            ]
        )
    )

    hi = float(
        np.nanmax(
            arr[
                valid
            ]
        )
    )

    if np.isclose(
        hi,
        lo,
    ):
        out[
            valid
        ] = 1.0

    else:
        out[
            valid
        ] = (
            arr[
                valid
            ]
            - lo
        ) / (
            hi
            - lo
        )

    return out



def select_interior_crossing_direction_by_density(
    training_raw,
    class_col,
    feature,
    x_raw,
    mean_curve,
    curves_raw,
    pv,
):
    """
    Fallback for an interior-only PDP stress pocket.

    Every crossing is classified by its local crossing direction. For each
    available direction, all same-direction STi candidates are evaluated by
    ``derive_best_multi_crossing_threshold`` with the outer-tail requirement
    disabled. Each STi gets its own bootstrap interval and Auto-STa. The best
    LOWER-vs-UPPER direction is then chosen using the same final objectives:

        maximize Sh_Hit, minimize No_Hit, minimize Bo_Hit,
        then maximize 4*Sh_Hit - 2*No_Hit - 3*Bo_Hit.

    Exactly ONE direction is returned. This avoids converting an interior
    pocket into an invalid two-sided OR rule while retaining the historical-style
    option to select the boundary that best separates Sh from No/Bo.
    """

    crossings = find_all_crossings(x=x_raw, y=mean_curve, pv=pv)
    crossing_dirs = []
    for crossing in crossings:
        cdir = classify_mean_pdp_crossing_direction(
            x=x_raw,
            y=mean_curve,
            pv=pv,
            crossing=crossing,
        )
        if cdir in {"lower", "upper"}:
            crossing_dirs.append(cdir)

    available_dirs = [
        d for d in ["lower", "upper"]
        if d in set(crossing_dirs)
    ]

    direction_rows = []
    candidate_tables = []

    for direction in available_dirs:
        selected, candidate_table, _sta_details = (
            derive_best_multi_crossing_threshold(
                training_raw=training_raw,
                class_col=class_col,
                feature=feature,
                direction=direction,
                x_raw=x_raw,
                mean_curve=mean_curve,
                curves_raw=curves_raw,
                pv=pv,
                require_outer_tail=False,
            )
        )

        if candidate_table is not None and not candidate_table.empty:
            tmp = candidate_table.copy()
            tmp["Interior_Fallback_Direction"] = direction
            candidate_tables.append(tmp)

        if selected is None:
            continue

        row = dict(selected)
        row["Direction"] = direction
        direction_rows.append(row)

    if len(direction_rows) == 0:
        diagnostics = (
            pd.concat(candidate_tables, ignore_index=True)
            if candidate_tables else pd.DataFrame()
        )
        return [], diagnostics

    options = pd.DataFrame(direction_rows)

    # Pareto screen across the best candidate from each available direction.
    pareto_flags = []
    for i, a in options.iterrows():
        dominated = False
        for j, b in options.iterrows():
            if i == j:
                continue
            at_least_as_good = (
                float(b["Auto_STa_Sh_Hit"]) >= float(a["Auto_STa_Sh_Hit"])
                and float(b["Auto_STa_No_Hit"]) <= float(a["Auto_STa_No_Hit"])
                and float(b["Auto_STa_Bo_Hit"]) <= float(a["Auto_STa_Bo_Hit"])
            )
            strictly_better = (
                float(b["Auto_STa_Sh_Hit"]) > float(a["Auto_STa_Sh_Hit"])
                or float(b["Auto_STa_No_Hit"]) < float(a["Auto_STa_No_Hit"])
                or float(b["Auto_STa_Bo_Hit"]) < float(a["Auto_STa_Bo_Hit"])
            )
            if at_least_as_good and strictly_better:
                dominated = True
                break
        pareto_flags.append(not dominated)

    options["Interior_Direction_Pareto"] = pareto_flags
    pareto = options.loc[options["Interior_Direction_Pareto"]].copy()
    if pareto.empty:
        pareto = options.copy()

    ranked = pareto.sort_values(
        [
            "Auto_STa_Final_Linear_4_2_3_Score",
            "Auto_STa_Sh_Hit",
            "Auto_STa_Bo_Hit",
            "Auto_STa_No_Hit",
            "Bootstrap_Support",
            "Auto_STa_Distance_From_STi",
            "STi_Candidate",
        ],
        ascending=[False, False, True, True, False, True, True],
    ).reset_index(drop=True)

    chosen_direction = str(ranked.iloc[0]["Direction"])
    options["Selected_Interior_Direction"] = (
        options["Direction"].astype(str) == chosen_direction
    )
    options["Interior_Direction_Selection_Method"] = (
        "PARETO_FINAL_STa_LINEAR_4_2_3_ACROSS_CROSSING_DIRECTIONS"
    )

    diagnostics_parts = [options]
    if candidate_tables:
        all_candidates = pd.concat(candidate_tables, ignore_index=True)
        all_candidates["Selected_Interior_Direction"] = (
            all_candidates["Direction"].astype(str) == chosen_direction
        )
        diagnostics_parts.append(all_candidates)

    diagnostics = pd.concat(
        diagnostics_parts,
        ignore_index=True,
        sort=False,
    )

    return [chosen_direction], diagnostics


def screen_two_sided_outer_directions_by_density(
    training_raw,
    class_col,
    feature,
    directions,
    x_raw,
    mean_curve,
    curves_raw,
    pv,
):
    """
    Density-screen a feature whose mean PDP supports BOTH lower and upper
    OUTER-tail stress directions.

    The aim is NOT to force one-sided behavior. Instead:

      1) derive the best STi + Auto-STa for each direction;
      2) if at least one valid direction has Sh_Hit > 0, remove directions
         with Sh_Hit = 0;
      3) Pareto-screen the remaining directions by:
             maximize Sh_Hit,
             minimize No_Hit,
             minimize Bo_Hit;
      4) retain ALL Pareto-efficient directions.

    Consequently, a direction such as an unsupported upper CWD tail can be
    removed, while a genuinely two-sided feature can keep both sides.

    The existing Linear 4:2:3 score is exported as a diagnostic but is not
    used to force a single winner when both directions are non-dominated.
    """

    ordered_dirs = [
        d for d in ["lower", "upper"]
        if d in set(directions)
    ]

    if len(ordered_dirs) < 2:
        return ordered_dirs, pd.DataFrame()

    direction_rows = []
    candidate_tables = []

    for direction in ordered_dirs:
        selected, candidate_table, _sta_details = (
            derive_best_multi_crossing_threshold(
                training_raw=training_raw,
                class_col=class_col,
                feature=feature,
                direction=direction,
                x_raw=x_raw,
                mean_curve=mean_curve,
                curves_raw=curves_raw,
                pv=pv,
                require_outer_tail=True,
            )
        )

        if candidate_table is not None and not candidate_table.empty:
            tmp = candidate_table.copy()
            tmp["Two_Sided_Outer_Direction"] = direction
            tmp["Diagnostic_Level"] = "STI_STA_CANDIDATE"
            candidate_tables.append(tmp)

        if selected is None:
            direction_rows.append({
                "Feature": feature,
                "Direction": direction,
                "Direction_Threshold_Valid": False,
                "Auto_STa_Sh_Hit": np.nan,
                "Auto_STa_No_Hit": np.nan,
                "Auto_STa_Bo_Hit": np.nan,
                "Auto_STa_Final_Linear_4_2_3_Score": np.nan,
                "STi_Candidate": np.nan,
                "Auto_STa_Candidate": np.nan,
                "Bootstrap_Support": np.nan,
            })
            continue

        row = dict(selected)
        row["Feature"] = feature
        row["Direction"] = direction
        row["Direction_Threshold_Valid"] = True
        row["Diagnostic_Level"] = "BEST_DIRECTION_CANDIDATE"
        direction_rows.append(row)

    options = pd.DataFrame(direction_rows)

    valid = options.loc[
        options["Direction_Threshold_Valid"].fillna(False)
    ].copy()

    if valid.empty:
        options["Dropped_Zero_Sh_When_Positive_Alternative"] = False
        options["Outer_Direction_Pareto"] = False
        options["Selected_Outer_Direction"] = False
        options["Outer_Direction_Selection_Method"] = (
            "NO_VALID_DIRECTION_THRESHOLD__ORIGINAL_DIRECTIONS_RETAINED_FOR_DIAGNOSTIC"
        )

        diagnostics_parts = [options]
        if candidate_tables:
            diagnostics_parts.append(
                pd.concat(candidate_tables, ignore_index=True, sort=False)
            )
        diagnostics = pd.concat(diagnostics_parts, ignore_index=True, sort=False)
        return ordered_dirs, diagnostics

    sh_positive_exists = bool(
        (pd.to_numeric(valid["Auto_STa_Sh_Hit"], errors="coerce") > 0).any()
    )

    if sh_positive_exists:
        working = valid.loc[
            pd.to_numeric(valid["Auto_STa_Sh_Hit"], errors="coerce") > 0
        ].copy()
    else:
        working = valid.copy()

    zero_sh_dropped_dirs = set(valid["Direction"]) - set(working["Direction"])

    # Pareto screen across directions. All non-dominated directions are kept.
    pareto_dirs = []

    for i, a in working.iterrows():
        dominated = False

        for j, b in working.iterrows():
            if i == j:
                continue

            a_sh = float(a["Auto_STa_Sh_Hit"])
            a_no = float(a["Auto_STa_No_Hit"])
            a_bo = float(a["Auto_STa_Bo_Hit"])

            b_sh = float(b["Auto_STa_Sh_Hit"])
            b_no = float(b["Auto_STa_No_Hit"])
            b_bo = float(b["Auto_STa_Bo_Hit"])

            at_least_as_good = (
                b_sh >= a_sh
                and b_no <= a_no
                and b_bo <= a_bo
            )

            strictly_better = (
                b_sh > a_sh
                or b_no < a_no
                or b_bo < a_bo
            )

            if at_least_as_good and strictly_better:
                dominated = True
                break

        if not dominated:
            pareto_dirs.append(str(a["Direction"]))

    if len(pareto_dirs) == 0:
        pareto_dirs = working["Direction"].astype(str).tolist()

    selected_dirs = [
        d for d in ordered_dirs
        if d in set(pareto_dirs)
    ]

    options["Dropped_Zero_Sh_When_Positive_Alternative"] = (
        options["Direction"].astype(str).isin(zero_sh_dropped_dirs)
    )
    options["Outer_Direction_Pareto"] = (
        options["Direction"].astype(str).isin(set(pareto_dirs))
    )
    options["Selected_Outer_Direction"] = (
        options["Direction"].astype(str).isin(set(selected_dirs))
    )
    options["Outer_Direction_Selection_Method"] = (
        "ZERO_SH_FILTER_THEN_PARETO_KEEP_ALL_NONDOMINATED_DIRECTIONS"
    )

    diagnostics_parts = [options]

    if candidate_tables:
        all_candidates = pd.concat(
            candidate_tables,
            ignore_index=True,
            sort=False,
        )
        all_candidates["Selected_Outer_Direction"] = (
            all_candidates["Direction"].astype(str).isin(set(selected_dirs))
        )
        diagnostics_parts.append(all_candidates)

    diagnostics = pd.concat(
        diagnostics_parts,
        ignore_index=True,
        sort=False,
    )

    return selected_dirs, diagnostics


def refine_selected_sta_with_linear_423(
    selected_sti_candidate_df,
    direction,
):
    """
    Final Auto-STa refinement AFTER STi has already been selected.

    IMPORTANT
    ---------
    This function cannot change STi.

    Procedure
    ---------
    1) If Sh-positive candidates exist, remove candidates with
       Sh_Hit = 0.

    2) Collapse thresholds producing exactly the same Sh / No / Bo
       classification:
           upper stress -> retain the larger threshold
           lower stress -> retain the smaller threshold

    3) Build the Pareto front:
           maximize Sh_Hit
           minimize No_Hit
           minimize Bo_Hit

    4) Select the final STa by maximizing the SAME fixed score for
       every crop-country-feature case:

           Linear_4_2_3 =
               4 * Sh_Hit
               - 2 * No_Hit
               - 3 * Bo_Hit

       Thus:
           Sh detection > Bo exclusion > No exclusion.

    5) Tie-breakers:
           higher Sh_Hit
           lower Bo_Hit
           lower No_Hit
           smaller distance from STi
           smaller numeric Candidate

    """

    if (
        selected_sti_candidate_df is None
        or selected_sti_candidate_df.empty
    ):
        return (
            None,
            pd.DataFrame(),
        )

    df = (
        selected_sti_candidate_df
        .copy()
        .reset_index(drop=True)
    )

    required = [
        "Candidate",
        "Sh_Hit",
        "No_Hit",
        "Bo_Hit",
        "Distance_From_STi",
    ]

    missing = [
        col
        for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "Final STa Linear 4:2:3 refinement is missing columns: "
            f"{missing}"
        )

    # ========================================================
    # BASIC DIAGNOSTICS
    # ========================================================

    df["No_Correct"] = (
        1.0
        - df["No_Hit"].astype(float)
    )

    df["Bo_Correct"] = (
        1.0
        - df["Bo_Hit"].astype(float)
    )

    df["ShNo_Separation"] = (
        df["Sh_Hit"].astype(float)
        - df["No_Hit"].astype(float)
    )

    # Kept only as a compatibility / diagnostic field.
    df["Final_Balanced_Class_Utility"] = (
        df["Sh_Hit"].astype(float)
        + df["No_Correct"].astype(float)
        + df["Bo_Correct"].astype(float)
    ) / 3.0

    df["Final_Linear_4_2_3_Score"] = (
        FINAL_STA_LINEAR_W_SH
        * df["Sh_Hit"].astype(float)
        -
        FINAL_STA_LINEAR_W_NO
        * df["No_Hit"].astype(float)
        -
        FINAL_STA_LINEAR_W_BO
        * df["Bo_Hit"].astype(float)
    )

    valid = df[
        df["Sh_Hit"].notna()
        &
        df["No_Hit"].notna()
        &
        df["Bo_Hit"].notna()
        &
        df["Final_Linear_4_2_3_Score"].notna()
    ].copy()

    if valid.empty:
        return (
            None,
            df,
        )

    # ========================================================
    # 1) REMOVE Sh_Hit = 0 IF Sh-POSITIVE CANDIDATES EXIST
    # ========================================================

    positive_sh = valid[
        valid["Sh_Hit"].astype(float) > 0.0
    ].copy()

    if not positive_sh.empty:
        valid = positive_sh

    # ========================================================
    # 2) COLLAPSE CLASSIFICATION-EQUIVALENT THRESHOLDS
    # ========================================================

    valid["_Sh_key"] = np.round(
        valid["Sh_Hit"].astype(float),
        12,
    )

    valid["_No_key"] = np.round(
        valid["No_Hit"].astype(float),
        12,
    )

    valid["_Bo_key"] = np.round(
        valid["Bo_Hit"].astype(float),
        12,
    )

    plateau_rows = []

    for _, group in valid.groupby(
        [
            "_Sh_key",
            "_No_key",
            "_Bo_key",
        ],
        sort=False,
        dropna=False,
    ):

        if direction == "upper":

            chosen_idx = (
                group["Candidate"]
                .astype(float)
                .idxmax()
            )

        elif direction == "lower":

            chosen_idx = (
                group["Candidate"]
                .astype(float)
                .idxmin()
            )

        else:
            raise ValueError(
                f"Unknown direction: {direction}"
            )

        plateau_rows.append(
            valid.loc[chosen_idx]
        )

    reduced = (
        pd.DataFrame(plateau_rows)
        .reset_index(drop=True)
    )

    # ========================================================
    # 3) PARETO FRONT
    #
    # Better means:
    #   higher Sh_Hit
    #   lower No_Hit
    #   lower Bo_Hit
    # ========================================================

    pareto_flags = []

    for i, row_i in reduced.iterrows():

        dominated = False

        for j, row_j in reduced.iterrows():

            if i == j:
                continue

            at_least_as_good = (
                float(row_j["Sh_Hit"])
                >= float(row_i["Sh_Hit"])
                and
                float(row_j["No_Hit"])
                <= float(row_i["No_Hit"])
                and
                float(row_j["Bo_Hit"])
                <= float(row_i["Bo_Hit"])
            )

            strictly_better = (
                float(row_j["Sh_Hit"])
                > float(row_i["Sh_Hit"])
                or
                float(row_j["No_Hit"])
                < float(row_i["No_Hit"])
                or
                float(row_j["Bo_Hit"])
                < float(row_i["Bo_Hit"])
            )

            if (
                at_least_as_good
                and strictly_better
            ):
                dominated = True
                break

        pareto_flags.append(
            not dominated
        )

    reduced["Pareto_Efficient_Final_STa"] = (
        pareto_flags
    )

    pareto = reduced[
        reduced["Pareto_Efficient_Final_STa"]
    ].copy()

    if pareto.empty:
        pareto = reduced.copy()

    # ========================================================
    # 4) GLOBAL LINEAR 4:2:3 SELECTOR
    # ========================================================

    pareto["Final_Linear_4_2_3_Score"] = (
        FINAL_STA_LINEAR_W_SH
        * pareto["Sh_Hit"].astype(float)
        -
        FINAL_STA_LINEAR_W_NO
        * pareto["No_Hit"].astype(float)
        -
        FINAL_STA_LINEAR_W_BO
        * pareto["Bo_Hit"].astype(float)
    )

    ranked = (
        pareto
        .sort_values(
            [
                "Final_Linear_4_2_3_Score",
                "Sh_Hit",
                "Bo_Hit",
                "No_Hit",
                "Distance_From_STi",
                "Candidate",
            ],
            ascending=[
                False,  # larger Linear 4:2:3 score
                False,  # more Sh detection
                True,   # less Bo contamination
                True,   # less No contamination
                True,   # closer to STi
                True,
            ],
        )
        .reset_index(drop=True)
    )

    selected = (
        ranked.iloc[0]
        .to_dict()
    )

    selected_candidate = float(
        selected["Candidate"]
    )

    # ========================================================
    # SAVE DIAGNOSTICS BACK TO COMPLETE CANDIDATE TABLE
    # ========================================================

    df["Pareto_Efficient_Final_STa"] = False

    # Score is defined for every candidate, not just the Pareto front.
    df["Final_Linear_4_2_3_Score"] = (
        FINAL_STA_LINEAR_W_SH
        * df["Sh_Hit"].astype(float)
        -
        FINAL_STA_LINEAR_W_NO
        * df["No_Hit"].astype(float)
        -
        FINAL_STA_LINEAR_W_BO
        * df["Bo_Hit"].astype(float)
    )

    for _, row in pareto.iterrows():

        mask = np.isclose(
            df["Candidate"].astype(float),
            float(row["Candidate"]),
        )

        df.loc[
            mask,
            "Pareto_Efficient_Final_STa",
        ] = True

    df[
        "Selected_Final_STa_Linear_4_2_3"
    ] = np.isclose(
        df["Candidate"].astype(float),
        selected_candidate,
    )

    return (
        selected,
        df,
    )



def derive_conservative_sta(
    training_raw,
    class_col,
    feature,
    direction,
    sti,
    ci_lower,
    ci_upper,
):
    """
    Automatic density-guided STa using a three-criterion Utopia point.

    For every candidate threshold inside the DIRECTIONAL STi
    uncertainty interval:

      C1) Sh proximity
          minimize |candidate - median(Sh)|

      C2) Bo distance
          maximize |candidate - median(Bo)|

      C3) Sh-No separation
          maximize Sh_hit_rate - No_hit_rate

    C1, C2 and C3 are independently min-max scaled to 0..1 and
    receive equal weight. The threshold with the minimum Euclidean
    distance to the ideal point (1,1,1) is selected.

    The candidate range is constrained ONLY by the directional
    STi bootstrap interval. No hard Sh median / Q25 / Q75 bound is used.

    """

    # --------------------------------------------------------
    # Directional STi uncertainty interval
    # --------------------------------------------------------

    if direction == "lower":

        search_min = min(
            float(
                ci_lower
            ),
            float(
                sti
            ),
        )

        search_max = float(
            sti
        )

    elif direction == "upper":

        search_min = float(
            sti
        )

        search_max = max(
            float(
                ci_upper
            ),
            float(
                sti
            ),
        )

    else:
        raise ValueError(
            direction
        )

    # --------------------------------------------------------
    # Class observations
    # --------------------------------------------------------

    def get_class_values(
        class_name,
    ):
        return (
            training_raw.loc[
                training_raw[
                    class_col
                ].astype(str)
                == class_name,
                feature,
            ]
            .dropna()
            .astype(float)
            .to_numpy()
        )

    sh_values = get_class_values(
        "Sh"
    )

    no_values = get_class_values(
        "No"
    )

    bo_values = get_class_values(
        "Bo"
    )

    if (
        len(
            sh_values
        ) == 0
        or
        len(
            no_values
        ) == 0
        or
        len(
            bo_values
        ) == 0
    ):
        return (
            float(
                sti
            ),
            "STa_EQUALS_STi_MISSING_CLASS_OBSERVATIONS",
            pd.DataFrame(),
        )

    sh_median = float(
        np.median(
            sh_values
        )
    )

    bo_median = float(
        np.median(
            bo_values
        )
    )

    # --------------------------------------------------------
    # STa candidate range = ONLY STi + directional bootstrap margin
    #
    # No Sh-median / Q25 / Q75 hard boundary is applied.
    # --------------------------------------------------------

    effective_min = float(
        search_min
    )

    effective_max = float(
        search_max
    )

    guardrail_applied = False

    # --------------------------------------------------------
    # Candidate thresholds
    #
    # Candidate values come from observations inside the valid
    # directional interval, plus STi / interval endpoints /
    # Sh median when allowed.
    # --------------------------------------------------------

    observed = (
        training_raw[
            feature
        ]
        .dropna()
        .astype(float)
        .to_numpy()
    )

    observed = observed[
        (
            observed
            >= effective_min
        )
        &
        (
            observed
            <= effective_max
        )
    ]

    explicit_points = [
        effective_min,
        float(
            sti
        ),
        effective_max,
    ]

    # Keep the Sh median only as an ordinary candidate when it lies
    # inside the STi-bootstrap interval. It does NOT constrain the range.
    if (
        sh_median
        >= effective_min
        and
        sh_median
        <= effective_max
    ):
        explicit_points.append(
            sh_median
        )

    candidates = np.unique(
        np.concatenate(
            [
                observed,
                np.asarray(
                    explicit_points,
                    dtype=float,
                ),
            ]
        )
    )

    # --------------------------------------------------------
    # Raw candidate criteria
    # --------------------------------------------------------

    rows = []

    for candidate in candidates:

        evaluation = (
            evaluate_threshold_candidate(
                training_raw=
                    training_raw,
                class_col=
                    class_col,
                feature=
                    feature,
                threshold=
                    candidate,
                direction=
                    direction,
                sti=
                    sti,
            )
        )

        rows.append({
            **evaluation,

            "Sh_Median":
                sh_median,

            "Bo_Median":
                bo_median,

            "Distance_to_Sh_Median":
                abs(
                    float(
                        candidate
                    )
                    - sh_median
                ),

            "Distance_to_Bo_Median":
                abs(
                    float(
                        candidate
                    )
                    - bo_median
                ),

            "Guardrail_Applied":
                guardrail_applied,

            "Effective_Search_Min":
                effective_min,

            "Effective_Search_Max":
                effective_max,
        })

    candidate_df = pd.DataFrame(
        rows
    )

    candidate_df = candidate_df[
        (
            candidate_df[
                "ShNo_Separation"
            ].notna()
        )
        &
        (
            candidate_df[
                "Distance_to_Sh_Median"
            ].notna()
        )
        &
        (
            candidate_df[
                "Distance_to_Bo_Median"
            ].notna()
        )
    ].copy()

    if candidate_df.empty:
        return (
            float(
                sti
            ),
            "STa_EQUALS_STi_NO_VALID_UTOPIA_CANDIDATES",
            candidate_df,
        )

    # --------------------------------------------------------
    # Convert each objective to a 0..1 BENEFIT criterion.
    # --------------------------------------------------------

    # C1: closer to Sh median = better.
    candidate_df[
        "C1_Sh_Proximity"
    ] = _normalize_benefit(
        -candidate_df[
            "Distance_to_Sh_Median"
        ].to_numpy(
            dtype=float
        )
    )

    # C2: farther from Bo median = better.
    candidate_df[
        "C2_Bo_Distance"
    ] = _normalize_benefit(
        candidate_df[
            "Distance_to_Bo_Median"
        ].to_numpy(
            dtype=float
        )
    )

    # C3: stronger separation of Sh from No = better.
    candidate_df[
        "C3_ShNo_Separation"
    ] = _normalize_benefit(
        candidate_df[
            "ShNo_Separation"
        ].to_numpy(
            dtype=float
        )
    )

    # Equal-weight Euclidean distance to ideal (1,1,1).
    candidate_df[
        "Utopia_Distance"
    ] = np.sqrt(
        (
            (
                1.0
                - candidate_df[
                    "C1_Sh_Proximity"
                ]
            ) ** 2
            +
            (
                1.0
                - candidate_df[
                    "C2_Bo_Distance"
                ]
            ) ** 2
            +
            (
                1.0
                - candidate_df[
                    "C3_ShNo_Separation"
                ]
            ) ** 2
        )
        / 3.0
    )

    candidate_df[
        "Selected_Auto_STa"
    ] = False

    ranked = (
        candidate_df
        .sort_values(
            [
                "Utopia_Distance",
                "C3_ShNo_Separation",
                "C1_Sh_Proximity",
                "C2_Bo_Distance",
                "Distance_From_STi",
                "Candidate",
            ],
            ascending=[
                True,
                False,
                False,
                False,
                True,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    selected_candidate = float(
        ranked.iloc[
            0
        ][
            "Candidate"
        ]
    )

    candidate_df.loc[
        np.isclose(
            candidate_df[
                "Candidate"
            ].astype(float),
            selected_candidate,
        ),
        "Selected_Auto_STa",
    ] = True

    return (
        selected_candidate,
        "UTOPIA_SH_NEAR_BO_FAR_SH_NO_SEPARATION",
        candidate_df,
    )



# ============================================================
# AUTOMATIC FULL-DATA FEATURE DISCOVERY HELPERS
# ============================================================

def detect_candidate_climate_features(columns):
    """Detect month-coded climate indicators from column names."""
    pattern = re.compile(CANDIDATE_FEATURE_REGEX, flags=re.IGNORECASE)
    out = [str(c) for c in columns if pattern.match(str(c))]
    return sorted(out)


def _feature_family(feature):
    return str(feature).split("_")[0]


def filter_collinear_features(training_raw, candidate_features):
    """
    Paper rule for |Spearman rho| >= COLLINEARITY_ABS_RHO:
      - RX5day or CWD is preferred over RX1day;
      - otherwise retain the feature with the stronger absolute
        Spearman association with detrended yield.

    Returns retained feature names and a decision table.
    """
    candidate_features = list(candidate_features)

    if len(candidate_features) <= 1:
        return candidate_features, pd.DataFrame()

    work = training_raw[[TARGET_COL, *candidate_features]].astype(float)
    feature_corr = work[candidate_features].corr(method="spearman")
    yield_assoc = work[candidate_features].corrwith(
        work[TARGET_COL],
        method="spearman",
    ).abs()

    active = set(candidate_features)
    decisions = []

    # Work from the strongest feature-feature correlations downward.
    pairs = []
    for i, f1 in enumerate(candidate_features):
        for f2 in candidate_features[i + 1:]:
            rho = feature_corr.loc[f1, f2]
            if np.isfinite(rho) and abs(float(rho)) >= COLLINEARITY_ABS_RHO:
                pairs.append((abs(float(rho)), f1, f2, float(rho)))

    pairs.sort(reverse=True, key=lambda x: x[0])

    for abs_rho, f1, f2, rho in pairs:
        if f1 not in active or f2 not in active:
            continue

        fam1 = _feature_family(f1)
        fam2 = _feature_family(f2)

        preferred = {"RX5day", "CWD"}

        if fam1 == "RX1day" and fam2 in preferred:
            keep, drop = f2, f1
            reason = "PREFER_RX5day_OR_CWD_OVER_RX1day"

        elif fam2 == "RX1day" and fam1 in preferred:
            keep, drop = f1, f2
            reason = "PREFER_RX5day_OR_CWD_OVER_RX1day"

        else:
            a1 = float(yield_assoc.get(f1, np.nan))
            a2 = float(yield_assoc.get(f2, np.nan))

            if not np.isfinite(a1):
                a1 = -np.inf
            if not np.isfinite(a2):
                a2 = -np.inf

            if a1 > a2:
                keep, drop = f1, f2
            elif a2 > a1:
                keep, drop = f2, f1
            else:
                keep, drop = sorted([f1, f2])[0], sorted([f1, f2])[1]

            reason = "STRONGER_ABS_SPEARMAN_WITH_YIELD"

        active.remove(drop)

        decisions.append({
            "Feature_1": f1,
            "Feature_2": f2,
            "Spearman_rho": rho,
            "Abs_Spearman_rho": abs_rho,
            "Abs_Yield_Assoc_Feature_1": yield_assoc.get(f1, np.nan),
            "Abs_Yield_Assoc_Feature_2": yield_assoc.get(f2, np.nan),
            "Retained": keep,
            "Removed": drop,
            "Decision_Rule": reason,
        })

    retained = [f for f in candidate_features if f in active]
    return retained, pd.DataFrame(decisions)


def calculate_mean_abs_shap_ranking(model, X):
    """Rank RF predictors by mean absolute SHAP magnitude."""
    try:
        import shap
    except ImportError as exc:
        raise ImportError(
            "Automatic feature discovery requires the 'shap' package. "
            "Install it in the Python environment used by Spyder."
        ) from exc

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    arr = np.asarray(shap_values, dtype=float)

    # Current SHAP versions can occasionally return an extra final axis.
    if arr.ndim == 3:
        arr = arr[..., 0]

    if arr.ndim != 2 or arr.shape[1] != X.shape[1]:
        raise ValueError(
            f"Unexpected SHAP array shape {arr.shape} for X shape {X.shape}."
        )

    importance = np.nanmean(np.abs(arr), axis=0)

    ranking = pd.DataFrame({
        "Feature": list(X.columns),
        "Mean_Abs_SHAP": importance,
    }).sort_values(
        ["Mean_Abs_SHAP", "Feature"],
        ascending=[False, True],
    ).reset_index(drop=True)

    ranking["SHAP_Rank"] = np.arange(1, len(ranking) + 1)
    return ranking


def _pareto_mask_feature_sets(df):
    """Pareto: min RMSE, max R2, min k."""
    flags = []

    for i, a in df.iterrows():
        dominated = False

        for j, b in df.iterrows():
            if i == j:
                continue

            at_least_as_good = (
                float(b["OOB_RMSE"]) <= float(a["OOB_RMSE"])
                and float(b["OOB_R2"]) >= float(a["OOB_R2"])
                and int(b["k"]) <= int(a["k"])
            )

            strictly_better = (
                float(b["OOB_RMSE"]) < float(a["OOB_RMSE"])
                or float(b["OOB_R2"]) > float(a["OOB_R2"])
                or int(b["k"]) < int(a["k"])
            )

            if at_least_as_good and strictly_better:
                dominated = True
                break

        flags.append(not dominated)

    return np.asarray(flags, dtype=bool)


def _normalize_benefit_01(values):
    arr = np.asarray(values, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    valid = np.isfinite(arr)

    if valid.sum() == 0:
        return out

    lo = float(np.nanmin(arr[valid]))
    hi = float(np.nanmax(arr[valid]))

    if np.isclose(lo, hi):
        out[valid] = 1.0
    else:
        out[valid] = (arr[valid] - lo) / (hi - lo)

    return out


def entropy_weights_from_benefits(matrix):
    """Entropy weights for already benefit-oriented 0..1 criteria."""
    X = np.asarray(matrix, dtype=float)
    n, m = X.shape

    if n <= 1:
        return np.full(m, 1.0 / m)

    eps = 1e-12
    divergences = np.zeros(m, dtype=float)

    for j in range(m):
        col = np.asarray(X[:, j], dtype=float)
        col = np.where(np.isfinite(col), col, 0.0)
        s = float(col.sum())

        if s <= eps:
            divergences[j] = 0.0
            continue

        p = col / s
        nz = p > eps
        entropy = -np.sum(p[nz] * np.log(p[nz])) / np.log(n)
        divergences[j] = max(0.0, 1.0 - float(entropy))

    total = float(divergences.sum())

    if total <= eps:
        return np.full(m, 1.0 / m)

    return divergences / total


def evaluate_shap_ranked_subsets(X_all, y, shap_ranking, yield_scale):
    """
    Evaluate SHAP-ranked feature subsets and select the OFS using the
    SAME Entropy + Utopia procedure as the original historical workflow.

    Two related outputs are produced from the same fits:

    A) AUDIT TABLE
       k = 2 ... min(FEATURE_K_MAX, n_features) are ALWAYS evaluated so a
       clean '<REGION>_subset_results.xlsx' can be saved in the same shape
       as the historical historical subset-results files.

    B) OFS SELECTION
       The manuscript rule is preserved exactly:
         - main candidate sizes: k = 4 ... 9
         - if OOB-R2 at k=4 is negative, k=2 and k=3 are ALSO allowed into
           the Pareto/Entropy/Utopia selection
         - if fewer than 4 features exist, use the available k >= 2 sets

    Corrected primary metrics
    -------------------------
    OOB_R2 / OOB_RMSE / OOB_MAE / OOB_Bias are calculated from genuine
    OOB predictions.

    Historical audit metrics
    ------------------------
    Training_RMSE / Training_MAE / Training_Bias are also saved so the
    historical historical files can be audited. These in-sample metrics NEVER
    enter corrected OFS selection.

    OFS logic
    ---------
    1) Pareto front:
           minimize TRUE OOB_RMSE
           maximize OOB_R2
           minimize k
    2) Scale Pareto candidates with the FULL range of all OFS-eligible sets.
    3) Compute entropy weights on the Pareto benefit matrix.
    4) Compute weighted Utopia distance with the same all-range scaling.
    5) Tie-break exactly as the historical code:
           Utopia_Distance, k, OOB_RMSE, OOB_R2
       ascending = [True, True, True, False].
    """

    ranked_features = shap_ranking["Feature"].tolist()
    n_features = len(ranked_features)

    if n_features < 2:
        raise ValueError(
            "Need at least 2 post-collinearity features for subset selection."
        )

    # --------------------------------------------------------
    # ALWAYS evaluate 2..9 (or up to the available feature count)
    # for the audit/output Excel. This does NOT mean k=2/3 always
    # participate in OFS selection.
    # --------------------------------------------------------
    audit_ks = list(
        range(
            2,
            min(FEATURE_K_MAX, n_features) + 1,
        )
    )

    rows = []

    def run_k(k):
        features = ranked_features[:k]
        Xk = X_all[features].copy()

        model, best_params, cv_score = fit_tuned_rf(Xk, y)

        oob = calculate_oob_metrics(
            model=model,
            y_std=y,
            yield_scale=yield_scale,
        )

        train_metrics = calculate_training_metrics(
            model=model,
            X=Xk,
            y_std=y,
            yield_scale=yield_scale,
        )

        return {
            "k": int(k),
            "Features": "; ".join(features),
            "Top_Features_List": str(features),

            # Correct OOB metrics used for OFS.
            "OOB_R2": oob["OOB_R2"],
            "OOB_RMSE": oob["OOB_RMSE"],
            "OOB_MAE": oob["OOB_MAE"],
            "OOB_Bias": oob["OOB_Bias"],
            "N_OOB": oob["N_OOB"],

            # Historical/in-sample audit metrics only.
            "Training_RMSE": train_metrics["Training_RMSE"],
            "Training_MAE": train_metrics["Training_MAE"],
            "Training_Bias": train_metrics["Training_Bias"],
            "N_Training": train_metrics["N_Training"],

            "OOB_minus_Training_RMSE": (
                oob["OOB_RMSE"] - train_metrics["Training_RMSE"]
                if np.isfinite(oob["OOB_RMSE"])
                and np.isfinite(train_metrics["Training_RMSE"])
                else np.nan
            ),

            "Inner_CV_Best_Score": cv_score,
            "Best_Params": str(best_params),
        }

    for k in audit_ks:
        rows.append(run_k(k))

    result = (
        pd.DataFrame(rows)
        .sort_values("k")
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Decide which already-evaluated k values may enter OFS.
    # --------------------------------------------------------
    if n_features >= FEATURE_K_MIN:
        primary_ks = list(
            range(
                FEATURE_K_MIN,
                min(FEATURE_K_MAX, n_features) + 1,
            )
        )

        selection_ks = list(primary_ks)

        if (
            TEST_K2_K3_IF_K4_OOB_R2_NEGATIVE
            and 4 in result["k"].astype(int).tolist()
        ):
            r2_k4 = float(
                result.loc[
                    result["k"].astype(int) == 4,
                    "OOB_R2",
                ].iloc[0]
            )

            # Test k=2/3 only when k=4 is meaningfully negative, not when
            # it is merely a tiny numerical negative within the near-zero
            # tolerance used for the original/historical-style interpretation.
            if (
                np.isfinite(r2_k4)
                and r2_k4 < -float(OOB_R2_NEAR_ZERO_TOLERANCE)
            ):
                for small_k in [2, 3]:
                    if small_k <= n_features and small_k not in selection_ks:
                        selection_ks.append(small_k)
    else:
        selection_ks = list(audit_ks)

    selection_ks = sorted(set(int(k) for k in selection_ks))

    result["Eligible_For_OFS_Selection"] = (
        result["k"].astype(int).isin(selection_ks)
    )

    selection_pool = result[
        result["Eligible_For_OFS_Selection"]
    ].copy()

    # --------------------------------------------------------
    # Exclusion safeguard applies to the OFS-eligible set only.
    # Tiny negative values close to zero are retained rather than causing
    # automatic feature discovery to fail. Raw R2 values remain unchanged.
    # --------------------------------------------------------
    result["Best_Eligible_OOB_R2"] = np.nan
    result["OOB_R2_Near_Zero_Tolerance"] = float(
        OOB_R2_NEAR_ZERO_TOLERANCE
    )
    result["OOB_R2_Skill_Flag"] = "NOT_EVALUATED"

    finite_r2 = (
        selection_pool["OOB_R2"]
        .dropna()
        .astype(float)
    )

    if len(finite_r2) > 0:
        best_tested_r2 = float(finite_r2.max())
        result["Best_Eligible_OOB_R2"] = best_tested_r2

        if best_tested_r2 < -float(OOB_R2_NEAR_ZERO_TOLERANCE):
            result["OOB_R2_Skill_Flag"] = (
                "MEANINGFULLY_NEGATIVE_EXCLUDED"
            )

            if EXCLUDE_IF_ALL_TESTED_OOB_R2_NEGATIVE:
                result["Selection_Status"] = (
                    "ALL_ELIGIBLE_OOB_R2_BELOW_NEGATIVE_TOLERANCE"
                )
                result["Pareto"] = False
                result["Selected_Utopia"] = False
                return None, result

        elif best_tested_r2 < 0:
            result["OOB_R2_Skill_Flag"] = (
                "NEAR_ZERO_NEGATIVE_RETAINED"
            )

        else:
            result["OOB_R2_Skill_Flag"] = "NONNEGATIVE"

    valid = selection_pool[
        selection_pool["OOB_RMSE"].notna()
        & selection_pool["OOB_R2"].notna()
    ].copy()

    if valid.empty:
        result["Selection_Status"] = "NO_VALID_OFS_SUBSET"
        result["Pareto"] = False
        result["Selected_Utopia"] = False
        return None, result

    valid["Pareto"] = _pareto_mask_feature_sets(valid)
    pareto = valid[valid["Pareto"]].copy()

    if pareto.empty:
        result["Selection_Status"] = "NO_PARETO_SUBSET"
        result["Pareto"] = False
        result["Selected_Utopia"] = False
        return None, result

    # ========================================================
    # EXACT HISTORICAL ENTROPY WORKFLOW: ALL-RANGE SCALING
    # ========================================================
    # The all-range base means all VALID, OFS-ELIGIBLE feature sets.
    # k=2/3 audit-only rows do not influence scaling unless the paper rule
    # admits them because k=4 has negative OOB-R2.
    # ========================================================

    base = valid if FEATURE_SELECTION_USE_ALL_RANGE_SCALING else pareto

    rmse_min = float(base["OOB_RMSE"].min())
    rmse_max = float(base["OOB_RMSE"].max())
    r2_min = float(base["OOB_R2"].min())
    r2_max = float(base["OOB_R2"].max())
    k_min = float(base["k"].min())
    k_max = float(base["k"].max())

    def _benefit_from_cost(series, lo, hi):
        denom = float(hi - lo)
        if denom <= 0:
            return pd.Series(1.0, index=series.index, dtype=float)
        return (float(hi) - series.astype(float)) / denom

    def _benefit_direct(series, lo, hi):
        denom = float(hi - lo)
        if denom <= 0:
            return pd.Series(1.0, index=series.index, dtype=float)
        return (series.astype(float) - float(lo)) / denom

    def _cost_direct(series, lo, hi):
        denom = float(hi - lo)
        if denom <= 0:
            return pd.Series(0.0, index=series.index, dtype=float)
        return (series.astype(float) - float(lo)) / denom

    pareto["B_RMSE"] = _benefit_from_cost(
        pareto["OOB_RMSE"], rmse_min, rmse_max
    )
    pareto["B_R2"] = _benefit_direct(
        pareto["OOB_R2"], r2_min, r2_max
    )
    pareto["B_k"] = _benefit_from_cost(
        pareto["k"], k_min, k_max
    )

    benefit_matrix = pareto[["B_RMSE", "B_R2", "B_k"]].to_numpy(float)
    weights = entropy_weights_from_benefits(benefit_matrix)

    pareto["Entropy_Weight_RMSE"] = float(weights[0])
    pareto["Entropy_Weight_R2"] = float(weights[1])
    pareto["Entropy_Weight_k"] = float(weights[2])

    pareto["C_RMSE"] = _cost_direct(
        pareto["OOB_RMSE"], rmse_min, rmse_max
    )

    r2_denom = float(r2_max - r2_min)
    if r2_denom <= 0:
        pareto["C_R2"] = 0.0
    else:
        pareto["C_R2"] = (
            r2_max - pareto["OOB_R2"].astype(float)
        ) / r2_denom

    pareto["C_k"] = _cost_direct(
        pareto["k"], k_min, k_max
    )

    pareto["Utopia_Distance"] = np.sqrt(
        weights[0] * pareto["C_RMSE"] ** 2
        + weights[1] * pareto["C_R2"] ** 2
        + weights[2] * pareto["C_k"] ** 2
    )
    pareto["Utopia_Score"] = 1.0 - pareto["Utopia_Distance"]

    pareto["Scaling_RMSE_Min_All"] = rmse_min
    pareto["Scaling_RMSE_Max_All"] = rmse_max
    pareto["Scaling_R2_Min_All"] = r2_min
    pareto["Scaling_R2_Max_All"] = r2_max
    pareto["Scaling_k_Min_All"] = k_min
    pareto["Scaling_k_Max_All"] = k_max
    pareto["Scaling_Base"] = (
        "ALL_OFS_ELIGIBLE_FEATURE_SETS"
        if FEATURE_SELECTION_USE_ALL_RANGE_SCALING
        else "PARETO_ONLY"
    )
    pareto["OFS_Selection_Method"] = "PARETO_ENTROPY_UTOPIA_ALL_RANGE"

    # ========================================================
    # MAP DIAGNOSTICS BACK TO COMPLETE 2..9 AUDIT TABLE
    # ========================================================
    result["Pareto"] = False

    diagnostic_cols = [
        "B_RMSE", "B_R2", "B_k",
        "C_RMSE", "C_R2", "C_k",
        "Entropy_Weight_RMSE", "Entropy_Weight_R2", "Entropy_Weight_k",
        "Utopia_Distance", "Utopia_Score",
        "Scaling_RMSE_Min_All", "Scaling_RMSE_Max_All",
        "Scaling_R2_Min_All", "Scaling_R2_Max_All",
        "Scaling_k_Min_All", "Scaling_k_Max_All",
        "Scaling_Base", "OFS_Selection_Method",
    ]

    for col in diagnostic_cols:
        result[col] = (
            np.nan
            if col not in {"Scaling_Base", "OFS_Selection_Method"}
            else ""
        )

    for _, row in pareto.iterrows():
        mask = result["k"].astype(int) == int(row["k"])
        result.loc[mask, "Pareto"] = True
        for col in diagnostic_cols:
            result.loc[mask, col] = row[col]

    ranked_pareto = pareto.sort_values(
        ["Utopia_Distance", "k", "OOB_RMSE", "OOB_R2"],
        ascending=[True, True, True, False],
        ignore_index=True,
    )

    selected = ranked_pareto.iloc[0].to_dict()

    result["Selected_Utopia"] = (
        result["k"].astype(int) == int(selected["k"])
    )
    result["Selection_Status"] = "VALID"

    return selected, result


def export_subset_results_excel(subset_table, signature_dir):
    """
    Save a clean subset-results workbook matching the historical historical
    output layout, plus an audit workbook that exposes the historical
    training-RMSE issue side-by-side with corrected true OOB RMSE.

    Main historical-layout file columns:
        Num_Features
        OOB R²
        OOB Bias
        OOB RMSE
        OOB MAE
        Best_Params
        Top_Features
    """

    if subset_table is None or subset_table.empty:
        return {
            "subset_results": None,
            "subset_results_audit": None,
        }

    # Country/region token matching the old naming convention, e.g.
    # REGION_NAME='SUI-Wheat' -> SUI_subset_results.xlsx
    region_token = str(REGION_NAME).split("-")[0].strip()
    if not region_token:
        region_token = str(COUNTRY_FOLDER).rstrip("0123456789")

    clean = subset_table.copy().sort_values("k").reset_index(drop=True)

    historical_layout = pd.DataFrame({
        "Num_Features": clean["k"].astype(int),
        "OOB R²": clean["OOB_R2"],
        "OOB Bias": clean["OOB_Bias"],
        "OOB RMSE": clean["OOB_RMSE"],
        "OOB MAE": clean["OOB_MAE"],
        "Best_Params": clean["Best_Params"],
        "Top_Features": clean["Top_Features_List"],
    })

    subset_results_path = os.path.join(
        signature_dir,
        f"{region_token}_subset_results.xlsx",
    )

    historical_layout.to_excel(
        subset_results_path,
        index=False,
    )

    # Extended audit file. OOB columns are corrected genuine OOB metrics;
    # Training RMSE reproduces the type of in-sample error used by the old
    # historical script when it labeled that quantity 'OOB RMSE'.
    audit_layout = historical_layout.copy()
    audit_layout["Training RMSE (legacy/in-sample)"] = clean["Training_RMSE"]
    audit_layout["Training Bias (in-sample)"] = clean["Training_Bias"]
    audit_layout["Training MAE (in-sample)"] = clean["Training_MAE"]
    audit_layout["True OOB RMSE - Training RMSE"] = clean[
        "OOB_minus_Training_RMSE"
    ]
    audit_layout["Eligible_For_OFS_Selection"] = clean[
        "Eligible_For_OFS_Selection"
    ]
    audit_layout["Pareto"] = clean.get("Pareto", False)
    audit_layout["Selected_Utopia"] = clean.get("Selected_Utopia", False)
    audit_layout["Selection_Status"] = clean.get("Selection_Status", "")
    audit_layout["Inner_CV_Best_R2"] = clean["Inner_CV_Best_Score"]

    audit_path = os.path.join(
        signature_dir,
        f"{region_token}_subset_results_audit.xlsx",
    )

    audit_layout.to_excel(
        audit_path,
        index=False,
    )

    print(f"  Subset-results Excel: {subset_results_path}")
    print(f"  Subset audit Excel:   {audit_path}")

    return {
        "subset_results": subset_results_path,
        "subset_results_audit": audit_path,
    }



def infer_stress_directions_from_mean_pdp(
    mean_curve,
    pv,
    x_raw=None,
):
    """
    Infer only OUTER-TAIL stress directions from the mean PDP.

    A lower direction is accepted only when the low-feature tail is
    below PV and has a valid lower-tail boundary crossing.

    An upper direction is accepted only when the high-feature tail is
    below PV and has a valid upper-tail boundary crossing.

    Therefore:
      - genuinely two-sided tail stress -> ["lower", "upper"]
      - one stressed tail -> one direction only
      - interior-only stress pocket -> []
    """

    y = np.asarray(mean_curve, dtype=float)

    if x_raw is None:
        x = np.arange(len(y), dtype=float)
    else:
        x = np.asarray(x_raw, dtype=float)

    if len(y) < 2 or len(x) != len(y):
        return []

    crossings = find_all_crossings(
        x=x,
        y=y,
        pv=pv,
    )

    directions = []

    for direction in ["lower", "upper"]:
        directional = filter_crossings_by_direction(
            crossings=crossings,
            x=x,
            y=y,
            pv=pv,
            direction=direction,
        )

        if len(directional) > 0:
            directions.append(direction)

    return directions




def _country_code_for_full_data_files():
    """Return the country prefix used by the historical UPDATED filenames."""
    code = re.sub(r"\d+$", "", str(COUNTRY_FOLDER).strip())
    if not code:
        code = str(REGION_NAME).split("-")[0].split("_")[0].strip()
    return code


def _find_unique_file_recursively(search_roots, exact_basename):
    """Find one exact basename under the supplied roots; fail on ambiguity."""
    wanted = str(exact_basename).lower()
    matches = []
    seen = set()

    for root in search_roots:
        if not root:
            continue
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if name.lower() == wanted:
                    path = os.path.abspath(os.path.join(dirpath, name))
                    if path not in seen:
                        seen.add(path)
                        matches.append(path)

    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        return None

    raise ValueError(
        f"Multiple files named {exact_basename!r} were found:\n"
        + "\n".join(matches)
        + "\nSet FULL_DATA_SOURCE_DIR or the explicit FULL_DATA_*_FILE setting."
    )


def _resolve_master_full_data_file():
    """Resolve the canonical combined_nonstandardized_data.xlsx input."""
    explicit = str(FULL_DATA_MASTER_FILE).strip()
    if explicit:
        if not os.path.exists(explicit):
            raise FileNotFoundError(
                f"FULL_DATA_MASTER_FILE not found:\n{explicit}"
            )
        return os.path.abspath(explicit)

    source_dir = str(FULL_DATA_SOURCE_DIR).strip()
    if source_dir:
        candidate = os.path.join(
            os.path.abspath(source_dir),
            FULL_DATA_MASTER_FILENAME,
        )
        if not os.path.exists(candidate):
            raise FileNotFoundError(
                f"Expected canonical full-data file not found:\n{candidate}"
            )
        return candidate

    roots = []
    for candidate in [
        os.path.dirname(BASE_PARENT),
        BASE_PARENT,
        os.path.dirname(os.path.dirname(BASE_PARENT)),
    ]:
        if candidate and candidate not in roots:
            roots.append(candidate)

    master = _find_unique_file_recursively(
        roots,
        FULL_DATA_MASTER_FILENAME,
    )
    if master is None:
        raise FileNotFoundError(
            f"Could not automatically find {FULL_DATA_MASTER_FILENAME}.\n"
            "Set FULL_DATA_MASTER_FILE or FULL_DATA_SOURCE_DIR explicitly."
        )
    return master


def _standardize_existing_combined_full_data(master_path, output_dir):
    """Create combined_standardized_data.xlsx from the canonical merged raw file."""
    os.makedirs(output_dir, exist_ok=True)
    df_combined = pd.read_excel(master_path)

    required = [YEAR_COL, TARGET_COL]
    missing = [c for c in required if c not in df_combined.columns]
    if missing:
        raise ValueError(
            f"Canonical full-data file is missing required columns: {missing}"
        )
    if df_combined.empty:
        raise ValueError("Canonical full-data file is empty.")
    if df_combined[YEAR_COL].duplicated().any():
        raise ValueError("Canonical full-data file contains duplicate Year values.")
    if df_combined.isna().any().any():
        bad = df_combined.columns[df_combined.isna().any()].tolist()
        raise ValueError(
            "Missing values detected in canonical full-data file: "
            f"{bad}"
        )

    # Preserve the canonical file exactly as the non-standardized input.
    nonstd_path = os.path.join(output_dir, "combined_nonstandardized_data.xlsx")
    master_abs = os.path.abspath(master_path)
    nonstd_abs = os.path.abspath(nonstd_path)
    if master_abs != nonstd_abs:
        df_combined.to_excel(nonstd_path, index=False)
    else:
        nonstd_path = master_path

    df_standardized = df_combined.copy()
    columns_to_standardize = df_combined.columns.difference([YEAR_COL])
    scaler = StandardScaler()
    df_standardized[columns_to_standardize] = scaler.fit_transform(
        df_combined[columns_to_standardize].astype(float)
    )

    std_path = os.path.join(output_dir, "combined_standardized_data.xlsx")
    df_standardized.to_excel(std_path, index=False)
    return nonstd_path, std_path


def _resolve_raw_full_data_sources():
    """
    Resolve the PRE-SPEARMAN climate and detrended-yield files used to build
    the exact historical-style standardized/non-standardized UPDATED pair.
    """
    explicit_climate = str(FULL_DATA_CLIMATE_FILE).strip()
    explicit_yield = str(FULL_DATA_YIELD_FILE).strip()

    if explicit_climate or explicit_yield:
        if not explicit_climate or not explicit_yield:
            raise ValueError(
                "Set BOTH FULL_DATA_CLIMATE_FILE and FULL_DATA_YIELD_FILE, "
                "or leave both blank."
            )
        if not os.path.exists(explicit_climate):
            raise FileNotFoundError(f"FULL_DATA_CLIMATE_FILE not found:\n{explicit_climate}")
        if not os.path.exists(explicit_yield):
            raise FileNotFoundError(f"FULL_DATA_YIELD_FILE not found:\n{explicit_yield}")
        return os.path.abspath(explicit_climate), os.path.abspath(explicit_yield)

    country_code = _country_code_for_full_data_files()
    climate_name = f"{country_code}_all_data_combined.xlsx"
    yield_name = "detrended_yield.xlsx"

    source_dir = str(FULL_DATA_SOURCE_DIR).strip()
    if source_dir:
        source_dir = os.path.abspath(source_dir)
        climate_path = os.path.join(source_dir, climate_name)
        yield_path = os.path.join(source_dir, yield_name)
        if not os.path.exists(climate_path):
            raise FileNotFoundError(f"Expected climate file not found:\n{climate_path}")
        if not os.path.exists(yield_path):
            raise FileNotFoundError(f"Expected yield file not found:\n{yield_path}")
        return climate_path, yield_path

    # Automatic search is intentionally outside LOYO folders first. In the
    # user's project layout BASE_PARENT is usually .../<macroregion>/LOYO_based processing,
    # while the historical full-data folders sit beside it.
    roots = []
    for candidate in [
        os.path.dirname(BASE_PARENT),
        BASE_PARENT,
        os.path.dirname(os.path.dirname(BASE_PARENT)),
    ]:
        if candidate and candidate not in roots:
            roots.append(candidate)

    climate_path = _find_unique_file_recursively(roots, climate_name)
    if climate_path is None:
        raise FileNotFoundError(
            f"Could not automatically find {climate_name}.\n"
            "Set FULL_DATA_SOURCE_DIR or FULL_DATA_CLIMATE_FILE explicitly."
        )

    # Prefer detrended_yield.xlsx in the SAME directory as the climate file.
    same_dir_yield = os.path.join(os.path.dirname(climate_path), yield_name)
    if os.path.exists(same_dir_yield):
        yield_path = same_dir_yield
    else:
        yield_path = _find_unique_file_recursively(roots, yield_name)
        if yield_path is None:
            raise FileNotFoundError(
                f"Could not automatically find {yield_name}.\n"
                "Set FULL_DATA_SOURCE_DIR or FULL_DATA_YIELD_FILE explicitly."
            )

    return climate_path, yield_path


def _combine_and_standardize_full_data(climate_path, yield_path, output_dir):
    """Reproduce the user's historical combine + StandardScaler script."""
    os.makedirs(output_dir, exist_ok=True)

    df_climate = pd.read_excel(climate_path)
    df_yield = pd.read_excel(yield_path)

    if YEAR_COL not in df_climate.columns:
        raise ValueError(f"Required {YEAR_COL!r} column not found in climate dataset.")
    if YEAR_COL not in df_yield.columns:
        raise ValueError(f"Required {YEAR_COL!r} column not found in yield dataset.")
    if TARGET_COL not in df_yield.columns:
        raise ValueError(f"Column {TARGET_COL!r} not found in yield dataset.")

    if df_climate.isna().any().any():
        raise ValueError("Missing values detected in climate dataset.")
    if df_yield[TARGET_COL].isna().any():
        raise ValueError(f"Missing values detected in {TARGET_COL!r}.")

    df_combined = pd.merge(
        df_climate,
        df_yield[[YEAR_COL, TARGET_COL]],
        on=YEAR_COL,
        how="inner",
    )

    if df_combined.empty:
        raise ValueError("No matching years found between climate and yield datasets.")
    if df_combined[YEAR_COL].duplicated().any():
        raise ValueError("Duplicate Year values produced by climate/yield merge.")

    nonstd_path = os.path.join(output_dir, "combined_nonstandardized_data.xlsx")
    df_combined.to_excel(nonstd_path, index=False)

    df_standardized = df_combined.copy()
    columns_to_standardize = df_combined.columns.difference([YEAR_COL])
    scaler = StandardScaler()
    df_standardized[columns_to_standardize] = scaler.fit_transform(
        df_combined[columns_to_standardize].astype(float)
    )

    std_path = os.path.join(output_dir, "combined_standardized_data.xlsx")
    df_standardized.to_excel(std_path, index=False)

    return nonstd_path, std_path


def _historical_style_spearman_filter_full_data(nonstd_path, std_path, output_dir):
    """
    Reproduce the historical Spearman + complete-linkage filtering script.

    This intentionally uses the same cluster winner rules as the uploaded
    historical preprocessing code, so the UPDATED files supplied to RF/SHAP match
    the historical workflow rather than a newer pairwise-filter variant.
    """
    country_code = _country_code_for_full_data_files()
    region_name = str(REGION_NAME)

    df_non = pd.read_excel(nonstd_path)
    df_std = pd.read_excel(std_path)

    if len(df_non) != len(df_std):
        raise ValueError(
            f"Row mismatch: nonstandardized has {len(df_non)} rows, "
            f"standardized has {len(df_std)} rows."
        )
    if YEAR_COL in df_non.columns and YEAR_COL in df_std.columns:
        if not df_non[YEAR_COL].equals(df_std[YEAR_COL]):
            raise ValueError("Year sequences differ between combined files.")

    target_col = TARGET_COL if TARGET_COL in df_std.columns else None
    if target_col is None:
        raise ValueError(f"Target {TARGET_COL!r} not found in standardized file.")

    valid_idx = df_std[target_col].notna()
    df_non = df_non.loc[valid_idx].reset_index(drop=True)
    df_std = df_std.loc[valid_idx].reset_index(drop=True)

    exclude_cols = {
        "Year", "year", "Detrended_Yield", "Weighted_Yield", "Yield",
        "Detrended yield", "weighted_yield", "yield",
    }
    feature_cols = [c for c in df_non.columns if c not in exclude_cols]
    if len(feature_cols) < 2:
        raise ValueError("Need at least two climate features for Spearman filtering.")

    X_non = df_non[feature_cols].copy()
    y = df_std[target_col].astype(float).copy()

    abs_corr = pd.DataFrame(index=feature_cols, columns=feature_cols, dtype=float)
    pvals = pd.DataFrame(index=feature_cols, columns=feature_cols, dtype=float)

    for i, a in enumerate(feature_cols):
        xa = X_non[a]
        for j, b in enumerate(feature_cols):
            if j < i:
                abs_corr.loc[a, b] = abs_corr.loc[b, a]
                pvals.loc[a, b] = pvals.loc[b, a]
                continue
            if a == b:
                abs_corr.loc[a, b] = 1.0
                pvals.loc[a, b] = 0.0
                continue

            both = pd.concat([xa, X_non[b]], axis=1).dropna()
            if len(both) < FULL_DATA_SPEARMAN_MIN_PERIODS:
                rho, p = 0.0, np.nan
            else:
                rho, p = spearmanr(both.iloc[:, 0], both.iloc[:, 1])
                if not np.isfinite(rho):
                    rho = 0.0
                if not np.isfinite(p):
                    p = np.nan

            abs_corr.loc[a, b] = abs(float(rho))
            abs_corr.loc[b, a] = abs(float(rho))
            pvals.loc[a, b] = p
            pvals.loc[b, a] = p

    def square_to_condensed(square):
        iu = np.triu_indices(square.shape[0], 1)
        return square[iu]

    dist = 1.0 - abs_corr.values
    np.fill_diagonal(dist, 0.0)
    dist[~np.isfinite(dist)] = 1.0

    Z = linkage(square_to_condensed(dist), method=FULL_DATA_SPEARMAN_LINKAGE_METHOD)
    labels = fcluster(Z, t=(1.0 - COLLINEARITY_ABS_RHO), criterion="distance")

    clusters = {}
    for feat, lab in zip(feature_cols, labels):
        clusters.setdefault(lab, []).append(feat)

    rx_re = re.compile(r"^(RX(1|5)day|CWD|R10|R20)_(\d{1,2})$")

    def parse_tag_month(feature):
        match = rx_re.match(feature)
        if match:
            return match.group(1), int(match.group(3))
        return None, None

    shortlist = []
    audit_rows = []

    for cid, feats in sorted(clusters.items(), key=lambda kv: len(kv[1]), reverse=True):
        stats_list = []
        for feat in feats:
            xy = pd.concat([X_non[[feat]], y], axis=1).dropna()
            n = len(xy)
            if n >= FULL_DATA_SPEARMAN_MIN_PERIODS:
                rho, p = spearmanr(xy[feat], xy[target_col])
            else:
                rho, p = np.nan, np.nan
            stats_list.append((feat, rho, p, n))

        months_rx1, months_rx5, months_cwd, months_r10, months_r20 = (
            set(), set(), set(), set(), set()
        )
        for feat in feats:
            tag, mon = parse_tag_month(feat)
            if tag == "RX1day" and mon is not None:
                months_rx1.add(mon)
            if tag == "RX5day" and mon is not None:
                months_rx5.add(mon)
            if tag == "CWD" and mon is not None:
                months_cwd.add(mon)
            if tag == "R10" and mon is not None:
                months_r10.add(mon)
            if tag == "R20" and mon is not None:
                months_r20.add(mon)

        drop_feats = set()
        rules_applied = []

        for m in sorted((months_cwd | months_rx5) & months_rx1):
            for feat, _rho, _p, _n in stats_list:
                tag, mon = parse_tag_month(feat)
                if tag == "RX1day" and mon == m:
                    drop_feats.add(feat)
            if m in months_cwd:
                rules_applied.append(f"drop_RX1_due_to_CWD_m{m}")
            if m in months_rx5:
                rules_applied.append(f"drop_RX1_due_to_RX5_m{m}")

        for m in sorted((months_cwd | months_rx5) & months_r10):
            for feat, _rho, _p, _n in stats_list:
                tag, mon = parse_tag_month(feat)
                if tag == "R10" and mon == m:
                    drop_feats.add(feat)
            if m in months_cwd:
                rules_applied.append(f"drop_R10_due_to_CWD_m{m}")
            if m in months_rx5:
                rules_applied.append(f"drop_R10_due_to_RX5_m{m}")

        for m in sorted((months_cwd | months_rx5) & months_r20):
            for feat, _rho, _p, _n in stats_list:
                tag, mon = parse_tag_month(feat)
                if tag == "R20" and mon == m:
                    drop_feats.add(feat)
            if m in months_cwd:
                rules_applied.append(f"drop_R20_due_to_CWD_m{m}")
            if m in months_rx5:
                rules_applied.append(f"drop_R20_due_to_RX5_m{m}")

        rank_pool = [row for row in stats_list if row[0] not in drop_feats]
        if len(rank_pool) == 0:
            rank_pool = stats_list
            rules_applied.append("fallback_all")

        rank_pool = sorted(
            rank_pool,
            key=lambda row: (
                np.inf if not np.isfinite(row[2]) else row[2],
                -(abs(row[1]) if np.isfinite(row[1]) else -np.inf),
                -row[3],
            ),
        )

        winner = rank_pool[0][0] if rank_pool else feats[0]
        shortlist.append(winner)

        rule_str = ";".join(rules_applied) if rules_applied else ""
        for feat, rho, p, n in stats_list:
            tag, mon = parse_tag_month(feat)
            audit_rows.append({
                "cluster_id": cid,
                "feature": feat,
                "n_overlap": n,
                "spearman_rho": rho,
                "spearman_p": p,
                "tag": tag,
                "month": mon,
                "dropped_by_rule": feat in drop_feats,
                "rules_applied": rule_str,
                "is_selected": feat == winner,
            })

    dropped_features = [f for f in feature_cols if f not in shortlist]

    # Diagnostics matching the historical preprocessing outputs.
    pd.Series(dropped_features, name="dropped_feature").to_excel(
        os.path.join(output_dir, f"{region_name}_dropped_features_after_collinearity.xlsx"),
        index=False,
    )
    abs_corr.to_excel(os.path.join(output_dir, f"{region_name}_abs_corr_matrix.xlsx"))
    pvals.to_excel(os.path.join(output_dir, f"{region_name}_abs_corr_pvalues.xlsx"))
    pd.DataFrame(audit_rows).sort_values(
        ["cluster_id", "is_selected"], ascending=[True, False]
    ).to_excel(
        os.path.join(output_dir, f"{region_name}_clusters_spearman_audit.xlsx"),
        index=False,
    )
    pd.Series(shortlist, name="shortlisted_feature").to_excel(
        os.path.join(output_dir, f"{region_name}_shortlist_after_collinearity.xlsx"),
        index=False,
    )

    # Historical lower-triangle heatmap, without introducing seaborn as a
    # runtime dependency in this combined public script.
    data = abs_corr.to_numpy(float).copy()
    data[np.triu_indices_from(data, k=1)] = np.nan
    cmap = plt.cm.viridis.copy()
    cmap.set_bad(color="white")
    fig, ax = plt.subplots(figsize=(15, 9))
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(np.arange(len(feature_cols)))
    ax.set_yticks(np.arange(len(feature_cols)))
    ax.set_xticklabels(feature_cols, rotation=90, fontsize=8, fontweight="bold")
    ax.set_yticklabels(feature_cols, fontsize=8, fontweight="bold")
    ax.set_title(region_name, fontsize=24, fontweight="bold", pad=8)
    for i in range(len(feature_cols)):
        for j in range(i + 1):
            value = abs_corr.iat[i, j]
            if np.isfinite(value) and value >= COLLINEARITY_ABS_RHO:
                label = "1" if np.isclose(value, 1.0) else f"{value:.2f}"
                ax.text(j, i, label, ha="center", va="center", fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=10)
    fig.tight_layout()
    save_raster_figure(
        fig,
        os.path.join(output_dir, f"{region_name}_abs_corr_heatmap.{FIGURE_IMAGE_FORMAT}"),
    )
    plt.close(fig)

    yield_cols = ["Detrended_Yield", "Weighted_Yield", "Yield"]
    keep_non = []
    if YEAR_COL in df_non.columns:
        keep_non.append(YEAR_COL)
    keep_non += [c for c in yield_cols if c in df_non.columns]
    keep_non += shortlist

    keep_std = []
    if YEAR_COL in df_std.columns:
        keep_std.append(YEAR_COL)
    keep_std += [c for c in yield_cols if c in df_std.columns]
    if target_col not in keep_std and target_col in df_std.columns:
        keep_std.append(target_col)
    keep_std += shortlist

    keep_non = [c for c in keep_non if c in df_non.columns]
    keep_std = [c for c in keep_std if c in df_std.columns]

    non_updated = df_non[keep_non].copy()
    std_updated = df_std[keep_std].copy()

    non_updated_path = os.path.join(output_dir, f"{country_code}_nonstandardized_UPDATED.xlsx")
    std_updated_path = os.path.join(output_dir, f"{country_code}_standardized_UPDATED.xlsx")
    non_updated.to_excel(non_updated_path, index=False)
    std_updated.to_excel(std_updated_path, index=False)

    return std_updated_path, non_updated_path, shortlist


def prepare_full_data_historical_style_inputs():
    """
    End-to-end FULL_DATA preprocessing, independent of LOYO folders.

    Recommended mode uses the same canonical merged raw dataset that can also
    feed LOYO Step 1:
        combined_nonstandardized_data.xlsx

    From that one file F1 creates the historical full-data standardized file,
    applies the historical Spearman filter, and generates the UPDATED pair
    consumed by RF/SHAP/OFS.
    """
    mode = str(FULL_DATA_INPUT_MODE).strip().upper()
    valid_modes = {"MASTER_COMBINED", "RAW_CLIMATE_YIELD"}
    if mode not in valid_modes:
        raise ValueError(
            f"Invalid FULL_DATA_INPUT_MODE={FULL_DATA_INPUT_MODE!r}. "
            f"Use one of {sorted(valid_modes)}."
        )

    climate_path = None
    yield_path = None
    master_path = None

    if mode == "MASTER_COMBINED":
        master_path = _resolve_master_full_data_file()
        output_dir = str(FULL_DATA_PREPROCESS_OUTPUT_DIR).strip()
        if output_dir:
            output_dir = os.path.abspath(output_dir)
        else:
            output_dir = os.path.dirname(os.path.abspath(master_path))

        os.makedirs(output_dir, exist_ok=True)

        print("\n" + "=" * 90)
        print("AUTOMATIC FULL-DATA PREPROCESSING")
        print("=" * 90)
        print("  Input mode    : MASTER_COMBINED")
        print(f"  Master input  : {master_path}")
        print(f"  Output folder : {output_dir}")

        combined_nonstd, combined_std = _standardize_existing_combined_full_data(
            master_path=master_path,
            output_dir=output_dir,
        )

    else:
        climate_path, yield_path = _resolve_raw_full_data_sources()
        output_dir = str(FULL_DATA_PREPROCESS_OUTPUT_DIR).strip()
        if output_dir:
            output_dir = os.path.abspath(output_dir)
        else:
            output_dir = os.path.dirname(os.path.abspath(climate_path))

        os.makedirs(output_dir, exist_ok=True)

        print("\n" + "=" * 90)
        print("AUTOMATIC FULL-DATA PREPROCESSING")
        print("=" * 90)
        print("  Input mode    : RAW_CLIMATE_YIELD")
        print(f"  Climate input : {climate_path}")
        print(f"  Yield input   : {yield_path}")
        print(f"  Output folder : {output_dir}")

        combined_nonstd, combined_std = _combine_and_standardize_full_data(
            climate_path=climate_path,
            yield_path=yield_path,
            output_dir=output_dir,
        )

    updated_std, updated_nonstd, shortlist = _historical_style_spearman_filter_full_data(
        nonstd_path=combined_nonstd,
        std_path=combined_std,
        output_dir=output_dir,
    )

    audit = pd.DataFrame([{
        "Input_Mode": mode,
        "Canonical_Master_Input": master_path,
        "Climate_Input": climate_path,
        "Yield_Input": yield_path,
        "Combined_Nonstandardized": combined_nonstd,
        "Combined_Standardized": combined_std,
        "Updated_Nonstandardized": updated_nonstd,
        "Updated_Standardized": updated_std,
        "N_Shortlisted_Features": len(shortlist),
        "Shortlisted_Features": "; ".join(shortlist),
        "Spearman_Threshold": COLLINEARITY_ABS_RHO,
        "Spearman_Linkage_Method": FULL_DATA_SPEARMAN_LINKAGE_METHOD,
        "Preprocessing_Source": (
            "CANONICAL_COMBINED_MASTER"
            if mode == "MASTER_COMBINED"
            else "INTERNAL_RAW_CLIMATE_YIELD_MERGE"
        ),
    }])
    audit.to_excel(
        os.path.join(output_dir, "automatic_full_data_preprocessing_audit.xlsx"),
        index=False,
    )

    print(f"  Generated standardized UPDATED file     : {updated_std}")
    print(f"  Generated non-standardized UPDATED file : {updated_nonstd}")
    return updated_std, updated_nonstd


def _resolve_standalone_full_data_paths():
    """Locate or internally generate the independent full-data pair."""
    global _FULL_DATA_PREPARED_PAIR_CACHE

    if _FULL_DATA_PREPARED_PAIR_CACHE is not None:
        return _FULL_DATA_PREPARED_PAIR_CACHE

    if AUTO_BUILD_FULL_DATA_INPUTS:
        _FULL_DATA_PREPARED_PAIR_CACHE = prepare_full_data_historical_style_inputs()
        return _FULL_DATA_PREPARED_PAIR_CACHE

    explicit_std = str(FULL_DATA_STANDARDIZED_FILE).strip()
    explicit_raw = str(FULL_DATA_NONSTANDARDIZED_FILE).strip()

    if explicit_std or explicit_raw:
        if not explicit_std or not explicit_raw:
            raise ValueError(
                "Set BOTH FULL_DATA_STANDARDIZED_FILE and "
                "FULL_DATA_NONSTANDARDIZED_FILE, or leave both blank."
            )
        if not os.path.exists(explicit_std):
            raise FileNotFoundError(f"FULL_DATA_STANDARDIZED_FILE not found:\n{explicit_std}")
        if not os.path.exists(explicit_raw):
            raise FileNotFoundError(f"FULL_DATA_NONSTANDARDIZED_FILE not found:\n{explicit_raw}")
        _FULL_DATA_PREPARED_PAIR_CACHE = (explicit_std, explicit_raw)
        return _FULL_DATA_PREPARED_PAIR_CACHE

    input_dir = os.path.join(BASE, FULL_DATA_INPUT_SUBDIR)
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(
            "Standalone FULL_DATA inputs are required. Either enable "
            "AUTO_BUILD_FULL_DATA_INPUTS, set the two FULL_DATA_*_FILE paths, "
            "or create:\n"
            f"{input_dir}"
        )

    files = [
        os.path.join(input_dir, n)
        for n in os.listdir(input_dir)
        if n.lower().endswith(".xlsx")
    ]
    std_candidates = [
        p for p in files
        if "standardized" in os.path.basename(p).lower()
        and "nonstandardized" not in os.path.basename(p).lower()
        and "non_standardized" not in os.path.basename(p).lower()
    ]
    raw_candidates = [
        p for p in files
        if (
            "nonstandardized" in os.path.basename(p).lower()
            or "non_standardized" in os.path.basename(p).lower()
            or "raw" in os.path.basename(p).lower()
        )
    ]

    if len(std_candidates) != 1 or len(raw_candidates) != 1:
        raise ValueError(
            "Could not uniquely identify the standalone FULL_DATA pair in:\n"
            f"{input_dir}\n"
            f"standardized candidates={std_candidates}\n"
            f"non-standardized/raw candidates={raw_candidates}"
        )

    _FULL_DATA_PREPARED_PAIR_CACHE = (std_candidates[0], raw_candidates[0])
    return _FULL_DATA_PREPARED_PAIR_CACHE


def load_standalone_full_data_pair():
    """
    Load the exact full-data pair used for the historical model.

    The standardized file controls row order and the exact values supplied to
    RF/SHAP. The raw file is reordered to the same Year sequence.
    """
    std_path, raw_path = _resolve_standalone_full_data_paths()
    full_std = pd.read_excel(std_path)
    full_raw = pd.read_excel(raw_path)

    for label, df in [("standardized", full_std), ("non-standardized", full_raw)]:
        missing = [c for c in [YEAR_COL, TARGET_COL] if c not in df.columns]
        if missing:
            raise ValueError(f"{label} FULL_DATA file is missing: {missing}")
        if df[YEAR_COL].duplicated().any():
            raise ValueError(f"{label} FULL_DATA file contains duplicate Year values.")

    # Preserve standardized-file row order. RF bootstrap sampling is based on
    # row positions, so changing row order can alter OOB predictions.
    years = full_std[YEAR_COL].tolist()
    raw_by_year = full_raw.set_index(YEAR_COL, drop=False)
    missing_raw = [y for y in years if y not in raw_by_year.index]
    extra_raw = [y for y in full_raw[YEAR_COL].tolist() if y not in set(years)]
    if missing_raw or extra_raw:
        raise ValueError(
            "Standalone standardized/non-standardized files do not contain "
            "the same years. "
            f"missing_raw={missing_raw[:10]}, extra_raw={extra_raw[:10]}"
        )

    full_raw = raw_by_year.loc[years].reset_index(drop=True)
    full_std = full_std.reset_index(drop=True)

    # Mirror the historical historical RF script: every column except Year/yield
    # bookkeeping is a predictor. The internally generated UPDATED pair already
    # contains only the post-Spearman shortlist, so no regex-based feature loss
    # can alter the SHAP ranking relative to the historical workflow.
    non_feature_cols = {
        "Year", "year", "Detrended_Yield", "Weighted_Yield", "Yield",
        "Detrended yield", "weighted_yield", "yield",
        "Yield_Class", "True_Class_3", "True_Class_Binary",
        "Training_P10", "Training_P90", "Training_PV",
    }
    std_features = [c for c in full_std.columns if c not in non_feature_cols]
    raw_features = set(c for c in full_raw.columns if c not in non_feature_cols)
    candidate_features = [f for f in std_features if f in raw_features]

    if len(candidate_features) < 2:
        raise ValueError("Fewer than 2 common predictors in standalone FULL_DATA files.")

    for c in [TARGET_COL, *candidate_features]:
        full_std[c] = pd.to_numeric(full_std[c], errors="raise")
        full_raw[c] = pd.to_numeric(full_raw[c], errors="raise")
        if full_std[c].isna().any() or full_raw[c].isna().any():
            raise ValueError(f"Missing values in standalone FULL_DATA column: {c}")

    info = {
        "Standardized_File": std_path,
        "Nonstandardized_File": raw_path,
        "N_Years": len(full_std),
        "N_Candidate_Features": len(candidate_features),
        "Auto_Built_From_Raw_Climate_And_Yield": bool(AUTO_BUILD_FULL_DATA_INPUTS),
    }
    return full_std, full_raw, candidate_features, info


def derive_scalers_from_paired_full_data(full_raw, full_std, variables):
    """Recover raw = standardized*scale + mean from the exact file pair."""
    scalers = {}
    rows = []

    for variable in variables:
        x = pd.to_numeric(full_raw[variable], errors="raise").to_numpy(float)
        z = pd.to_numeric(full_std[variable], errors="raise").to_numpy(float)
        finite = np.isfinite(x) & np.isfinite(z)
        x = x[finite]
        z = z[finite]

        if len(x) == 0:
            raise ValueError(f"No finite paired values for {variable}")

        if np.nanstd(z) <= 1e-14:
            scale = float(np.nanstd(x, ddof=1)) if len(x) > 1 else 1.0
            if not np.isfinite(scale) or scale <= 0:
                scale = 1.0
            mean = float(np.nanmean(x))
            max_err = 0.0
        else:
            A = np.column_stack([z, np.ones(len(z))])
            scale, mean = np.linalg.lstsq(A, x, rcond=None)[0]
            scale = float(scale)
            mean = float(mean)
            recon = z * scale + mean
            max_err = float(np.nanmax(np.abs(recon - x)))

        if scale < 0:
            raise ValueError(
                f"{variable}: negative standardized-to-raw scale. "
                "The two FULL_DATA files are probably not a matching pair."
            )

        scalers[variable] = {"mean": mean, "scale": scale}
        rows.append({
            "Variable": variable,
            "Training_Mean": mean,
            "Training_Scale": scale,
            "Max_Reconstruction_Error": max_err,
            "Source": "PAIRED_STANDALONE_FULL_DATA_FILES",
        })

    return scalers, pd.DataFrame(rows)


def _already_filtered_decision_table(candidate_features):
    return pd.DataFrame({
        "Feature": candidate_features,
        "Retained": candidate_features,
        "Removed": [""] * len(candidate_features),
        "Decision_Rule": [
            "PRE_FILTERED_STANDALONE_INPUT__NO_SECOND_F1_FILTER"
        ] * len(candidate_features),
    })


def prepare_automatic_full_data_signature(step2_dir, fold_names, output_dir):
    """
    Discover ONE full-data feature signature and its PDP-derived stress
    directions. That signature is then fixed across all LOYO folds.
    """
    print("\\n" + "=" * 90)
    print("AUTOMATIC FULL-DATA FEATURE DISCOVERY")
    print("=" * 90)

    signature_dir = os.path.join(output_dir, "automatic_signature_discovery")
    os.makedirs(signature_dir, exist_ok=True)

    # A) Independent standalone FULL_DATA pair.
    full_std_input, full_raw, candidate_features, source_info = (
        load_standalone_full_data_pair()
    )
    full_raw, class_info = classify_full_data(full_raw)

    # Use the exact standardized values from the historical-style input file.
    std = full_std_input.copy().reset_index(drop=True)
    std["Yield_Class"] = full_raw["Yield_Class"].to_numpy()

    # B) Do NOT re-filter predictors when the supplied files are already the
    # post-Spearman historical-analysis files.
    if FULL_DATA_FILES_ALREADY_SPEARMAN_FILTERED and not APPLY_SPEARMAN_FILTER_AGAIN_IN_F1:
        retained = list(candidate_features)
        corr_decisions = _already_filtered_decision_table(retained)
    else:
        retained, corr_decisions = filter_collinear_features(
            training_raw=full_raw,
            candidate_features=candidate_features,
        )

    if len(retained) < 2:
        raise ValueError("Fewer than 2 predictors remain for full-data RF/SHAP.")

    # Match pandas Index.difference ordering used by the old historical script.
    retained = sorted(retained)

    scalers, paired_scaler_table = derive_scalers_from_paired_full_data(
        full_raw=full_raw,
        full_std=std,
        variables=[*retained, TARGET_COL],
    )

    X_all = std[retained].astype(float).copy()
    y = std[TARGET_COL].astype(float).copy()
    yield_scale = float(scalers[TARGET_COL]["scale"])
    yield_mean = float(scalers[TARGET_COL]["mean"])

    ranking_model, ranking_params, ranking_cv = fit_tuned_rf(X_all, y)
    shap_ranking = calculate_mean_abs_shap_ranking(ranking_model, X_all)

    pv = float(full_raw.loc[full_raw["Yield_Class"].astype(str) == "No", TARGET_COL].mean())
    sh_yield_mean = float(full_raw.loc[full_raw["Yield_Class"].astype(str) == "Sh", TARGET_COL].mean())

    pd.DataFrame([source_info]).to_excel(
        os.path.join(signature_dir, "standalone_full_data_source.xlsx"), index=False
    )
    paired_scaler_table.to_excel(
        os.path.join(signature_dir, "standalone_full_data_scaler_mapping.xlsx"), index=False
    )

    # C) OFS uses the ORIGINAL SHAP ranking directly. Tail compatibility is
    # deliberately postponed until after selected_k / selected_features exist.
    compatibility_table = pd.DataFrame()
    shap_ranking_for_selection = shap_ranking.copy().reset_index(drop=True)
    shap_ranking_for_selection["OFS_Eligible_Rank"] = shap_ranking_for_selection["SHAP_Rank"]

    selected_row, subset_table = evaluate_shap_ranked_subsets(
        X_all=X_all,
        y=y,
        shap_ranking=shap_ranking_for_selection,
        yield_scale=yield_scale,
    )

    corr_decisions.to_excel(
        os.path.join(signature_dir, "collinearity_filter_decisions.xlsx"),
        index=False,
    )
    shap_ranking.to_excel(
        os.path.join(signature_dir, "shap_feature_ranking.xlsx"),
        index=False,
    )
    # Threshold compatibility is exported after OFS, not before it.
    shap_ranking_for_selection.to_excel(
        os.path.join(signature_dir, "shap_ranking_OFS_eligible.xlsx"),
        index=False,
    )
    subset_table.to_excel(
        os.path.join(signature_dir, "feature_subset_pareto_utopia.xlsx"),
        index=False,
    )

    subset_excel_paths = export_subset_results_excel(
        subset_table=subset_table,
        signature_dir=signature_dir,
    )

    if selected_row is None:
        raise ValueError(
            "Automatic feature selection failed: no valid subset remained, "
            "or the best eligible OOB-R2 was below the negative tolerance "
            f"(-{OOB_R2_NEAR_ZERO_TOLERANCE:g}). See "
            "automatic_signature_discovery/feature_subset_pareto_utopia.xlsx."
        )

    selected_k = int(selected_row["k"])
    selected_features = (
        shap_ranking_for_selection
        .head(selected_k)["Feature"]
        .tolist()
    )

    # --------------------------------------------------------
    # Final OFS RF + AFTER-OFS threshold compatibility.
    # The OFS is already frozen here, so tail logic cannot alter SHAP ranks,
    # subset metrics, Entropy-Utopia selection or OFS OOB-R2.
    # --------------------------------------------------------

    eligible_order = shap_ranking_for_selection["Feature"].tolist()
    backfill_log = []

    max_backfill_rounds = max(1, len(eligible_order) + 1)

    for backfill_round in range(max_backfill_rounds):

        X_sel = std[selected_features].astype(float).copy()
        final_rf, final_params, final_cv = fit_tuned_rf(X_sel, y)

        # ----------------------------------------------------
        # IMPORTANT: infer the final fixed stress directions from
        # the SAME full-data bootstrap-mean PDP that is later used
        # for STi/STa derivation and for the published PDP figure.
        #
        # Earlier versions inferred directions from the single fitted
        # RF PDP here, while STi and the figure used the mean of the
        # bootstrap PDPs later. That could produce an apparent upper
        # crossing in the figure (e.g. RX5day_7) without registering
        # the upper direction in EXPECTED_DIRECTIONS.
        # ----------------------------------------------------

        direction_grids_std = {}
        direction_grids_raw = {}

        for feature in selected_features:
            direction_grids_std[feature] = np.linspace(
                X_sel[feature].min(),
                X_sel[feature].max(),
                GRID_RESOLUTION,
            )

            direction_grids_raw[feature] = (
                direction_grids_std[feature]
                * scalers[feature]["scale"]
                + scalers[feature]["mean"]
            )

        direction_boot_results = Parallel(
            n_jobs=N_JOBS
        )(
            delayed(
                bootstrap_pdp_run
            )(
                RANDOM_STATE
                + 9000000
                + b,
                X_sel,
                y,
                direction_grids_std,
                final_params,
            )
            for b in range(
                N_BOOTSTRAPS
            )
        )

        trial_directions = {}
        trial_direction_requires_outer_tail = {}
        trial_rows = []
        interior_fallback_diagnostics = []
        two_sided_outer_direction_diagnostics = []

        for feature in selected_features:

            curves_std = np.vstack([
                result[feature]
                for result in direction_boot_results
            ])

            curves_raw = (
                curves_std
                * yield_scale
                + yield_mean
            )

            mean_curve = np.nanmean(
                curves_raw,
                axis=0,
            )

            x_raw = direction_grids_raw[feature]

            pv_info = resolve_feature_pv_for_crossing(
                x_raw=x_raw,
                mean_curve=mean_curve,
                original_pv=pv,
                sh_yield_mean=sh_yield_mean,
            )

            dirs = infer_stress_directions_from_mean_pdp(
                mean_curve=mean_curve,
                pv=pv_info["PV_Used"],
                x_raw=x_raw,
            )

            # Preserve the outer-tail discovery result separately so the
            # interior fallback is used ONLY for genuinely interior cases.
            outer_dirs_initial = list(dirs)

            tail_flags = _tail_stress_flags(
                x=x_raw,
                y=mean_curve,
                pv=pv_info["PV_Used"],
            )

            direction_source = "FULL_DATA_BOOTSTRAP_MEAN_PDP_OUTER_TAIL"
            require_outer_tail = True

            # ----------------------------------------------------
            # NEW: density-screen regular two-sided OUTER-tail cases.
            # Do not force one side. Zero-Sh sides are removed when a
            # Sh-positive alternative exists, then all Pareto-efficient
            # directions are retained.
            # ----------------------------------------------------
            if (
                SCREEN_TWO_SIDED_OUTER_DIRECTIONS_BY_DENSITY
                and set(dirs) == {"lower", "upper"}
            ):
                screened_dirs, two_side_diag = (
                    screen_two_sided_outer_directions_by_density(
                        training_raw=full_raw,
                        class_col="Yield_Class",
                        feature=feature,
                        directions=dirs,
                        x_raw=x_raw,
                        mean_curve=mean_curve,
                        curves_raw=curves_raw,
                        pv=pv_info["PV_Used"],
                    )
                )

                dirs = list(screened_dirs)
                direction_source = (
                    "FULL_DATA_BOOTSTRAP_MEAN_PDP_OUTER_TAIL_DENSITY_SCREEN"
                )

                if two_side_diag is not None and not two_side_diag.empty:
                    tmp_two = two_side_diag.copy()
                    tmp_two.insert(0, "Feature_For_Two_Sided_Screen", feature)
                    two_sided_outer_direction_diagnostics.append(tmp_two)

            # Historical-style fallback: if the mean PDP has crossings but NO
            # stressed OUTER tail (a genuinely interior stress pocket), retain
            # the crossing candidates and let density separation decide which
            # single boundary/direction is useful for the fixed signature.
            if (
                len(outer_dirs_initial) == 0
                and ALLOW_INTERIOR_CROSSING_DENSITY_FALLBACK
                and len(find_all_crossings(x=x_raw, y=mean_curve, pv=pv_info["PV_Used"])) > 0
            ):
                dirs, interior_diag = select_interior_crossing_direction_by_density(
                    training_raw=full_raw,
                    class_col="Yield_Class",
                    feature=feature,
                    x_raw=x_raw,
                    mean_curve=mean_curve,
                    curves_raw=curves_raw,
                    pv=pv_info["PV_Used"],
                )
                if len(dirs) > 0:
                    direction_source = "INTERIOR_CROSSING_DENSITY_FALLBACK"
                    require_outer_tail = False
                    if interior_diag is not None and not interior_diag.empty:
                        tmp_diag = interior_diag.copy()
                        tmp_diag.insert(0, "Feature_For_Fallback", feature)
                        interior_fallback_diagnostics.append(tmp_diag)

            trial_directions[feature] = list(dirs)
            trial_direction_requires_outer_tail[feature] = bool(require_outer_tail)

            if len(dirs) == 0:
                direction_status = "NO_VALID_PDP_CROSSING_DIRECTION"
            elif direction_source == "INTERIOR_CROSSING_DENSITY_FALLBACK":
                direction_status = "VALID_INTERIOR_CROSSING_DENSITY_SELECTED"
            elif (
                direction_source
                == "FULL_DATA_BOOTSTRAP_MEAN_PDP_OUTER_TAIL_DENSITY_SCREEN"
                and len(dirs) == 1
            ):
                direction_status = "VALID_ONE_SIDED_AFTER_TWO_SIDED_DENSITY_SCREEN"
            elif (
                direction_source
                == "FULL_DATA_BOOTSTRAP_MEAN_PDP_OUTER_TAIL_DENSITY_SCREEN"
                and len(dirs) == 2
            ):
                direction_status = "VALID_TWO_SIDED_DENSITY_SUPPORTED"
            elif len(dirs) == 1:
                direction_status = "VALID_ONE_SIDED"
            else:
                direction_status = "VALID_TWO_SIDED"

            trial_rows.append({
                "Feature": feature,
                "SHAP_Rank": int(
                    shap_ranking.loc[
                        shap_ranking["Feature"] == feature,
                        "SHAP_Rank",
                    ].iloc[0]
                ),
                "Directions": "; ".join(dirs),
                "Direction_Status": direction_status,
                "Direction_Source": direction_source,
                "Direction_Requires_Outer_Tail": bool(require_outer_tail),
                "Lower_Tail_Stress": tail_flags["lower"],
                "Upper_Tail_Stress": tail_flags["upper"],
                "Lower_Tail_PDP": tail_flags["Lower_Tail_PDP"],
                "Upper_Tail_PDP": tail_flags["Upper_Tail_PDP"],
                "Original_PV": pv_info["Original_PV"],
                "PV_Used": pv_info["PV_Used"],
                "PV_Adjusted": pv_info["PV_Adjusted"],
                "PV_Adjustment_Alpha": pv_info["PV_Adjustment_Alpha"],
                "PV_Rescue_Step": pv_info.get("PV_Rescue_Step", np.nan),
                "PV_Rescue_N_Steps": pv_info.get("PV_Rescue_N_Steps", np.nan),
                "PV_Valid_Directions": pv_info.get("PV_Valid_Directions", ""),
                "PV_Adjustment_Status": pv_info["PV_Adjustment_Status"],
            })

        unsupported = [
            f
            for f in selected_features
            if len(trial_directions.get(f, [])) == 0
        ]

        if (
            len(unsupported) == 0
            or not BACKFILL_UNSUPPORTED_FINAL_OFS_FEATURES
        ):
            directions = trial_directions
            direction_requires_outer_tail = trial_direction_requires_outer_tail
            direction_rows = trial_rows
            break

        available_replacements = [
            f
            for f in eligible_order
            if f not in selected_features
        ]

        if len(available_replacements) == 0:
            directions = trial_directions
            direction_requires_outer_tail = trial_direction_requires_outer_tail
            direction_rows = trial_rows
            break

        changed = False

        for bad_feature in unsupported:
            if len(available_replacements) == 0:
                break

            replacement = available_replacements.pop(0)
            idx_bad = selected_features.index(bad_feature)
            selected_features[idx_bad] = replacement

            backfill_log.append({
                "Round": backfill_round + 1,
                "Removed_Feature": bad_feature,
                "Replacement_Feature": replacement,
            })

            changed = True

        if not changed:
            directions = trial_directions
            direction_requires_outer_tail = trial_direction_requires_outer_tail
            direction_rows = trial_rows
            break

    else:
        directions = trial_directions
        direction_requires_outer_tail = trial_direction_requires_outer_tail
        direction_rows = trial_rows

    supported_features = [
        f
        for f in selected_features
        if len(directions.get(f, [])) > 0
    ]

    compatibility_table = pd.DataFrame(direction_rows)
    compatibility_table["Threshold_Supported"] = compatibility_table["Feature"].isin(
        supported_features
    )

    interior_fallback_path = os.path.join(
        signature_dir, "interior_crossing_direction_selection.xlsx"
    )
    if interior_fallback_diagnostics:
        pd.concat(
            interior_fallback_diagnostics, ignore_index=True, sort=False
        ).to_excel(interior_fallback_path, index=False)
    else:
        pd.DataFrame(columns=[
            "Feature_For_Fallback", "Direction", "STi_Candidate",
            "Auto_STa_Candidate", "Auto_STa_Sh_Hit", "Auto_STa_No_Hit",
            "Auto_STa_Bo_Hit", "Auto_STa_Final_Linear_4_2_3_Score",
            "Selected_Interior_Direction"
        ]).to_excel(interior_fallback_path, index=False)
    two_sided_outer_path = os.path.join(
        signature_dir, "two_sided_outer_direction_density_screen.xlsx"
    )
    if two_sided_outer_direction_diagnostics:
        pd.concat(
            two_sided_outer_direction_diagnostics,
            ignore_index=True,
            sort=False,
        ).to_excel(two_sided_outer_path, index=False)
    else:
        pd.DataFrame(columns=[
            "Feature_For_Two_Sided_Screen", "Direction",
            "Direction_Threshold_Valid", "Auto_STa_Sh_Hit",
            "Auto_STa_No_Hit", "Auto_STa_Bo_Hit",
            "Auto_STa_Final_Linear_4_2_3_Score",
            "Dropped_Zero_Sh_When_Positive_Alternative",
            "Outer_Direction_Pareto", "Selected_Outer_Direction",
            "Outer_Direction_Selection_Method",
        ]).to_excel(two_sided_outer_path, index=False)

    compatibility_table.to_excel(
        os.path.join(signature_dir, "threshold_compatibility_screen_AFTER_OFS.xlsx"),
        index=False,
    )

    backfill_table = pd.DataFrame(backfill_log)
    backfill_table.to_excel(
        os.path.join(signature_dir, "OFS_threshold_backfill_log.xlsx"),
        index=False,
    )

    signature = pd.DataFrame(direction_rows)
    signature["Selected_k_from_Utopia"] = selected_k
    signature["Used_in_RF_OFS"] = True
    signature["Threshold_Supported"] = signature["Feature"].isin(supported_features)
    # Backward-compatible name: the OFS itself remains exactly the
    # Utopia-selected k-feature set. Threshold support is reported separately.
    signature["Used_in_Final_Signature"] = True
    signature.to_excel(
        os.path.join(signature_dir, "automatic_full_data_signature.xlsx"),
        index=False,
    )

    pd.DataFrame([{
        "Selected_k": selected_k,
        "Selected_Features_Before_Direction_Filter": "; ".join(selected_features),
        "OFS_Selected_Features": "; ".join(selected_features),
        "Threshold_Supported_Features": "; ".join(supported_features),
        "Tail_Stress_Compatibility_Required_For_OFS": False,
        "Tail_Stress_Compatibility_Stage": "AFTER_OFS_ONLY",
        "Interior_Crossing_Density_Fallback": ALLOW_INTERIOR_CROSSING_DENSITY_FALLBACK,
        "PV_Rescue_Method": "FIXED_STEP_0.05_TOWARD_SH_FIRST_DIRECTIONAL_CROSSING",
        "PV_Rescue_Step": PV_RESCUE_STEP,
        "PV_Rescue_Max_Fraction_Toward_Sh": PV_RESCUE_MAX_FRACTION_TOWARD_SH,
        "Two_Sided_Outer_Direction_Density_Screen": SCREEN_TWO_SIDED_OUTER_DIRECTIONS_BY_DENSITY,
        "Full_Data_Source": "STANDALONE_HISTORICAL_STYLE_FILES",
        "Full_Data_Already_Spearman_Filtered": FULL_DATA_FILES_ALREADY_SPEARMAN_FILTERED,
        "PDP_Tail_Fraction_for_Direction": PDP_TAIL_FRACTION_FOR_DIRECTION,
        "N_Backfill_Replacements": len(backfill_log),
        "Ranking_RF_Best_Params": str(ranking_params),
        "Ranking_RF_CV_Score": ranking_cv,
        "Final_RF_Best_Params": str(final_params),
        "Final_RF_CV_Score": final_cv,
        "Subset_Utopia_Distance": selected_row.get("Utopia_Distance", np.nan),
        "Entropy_Weight_RMSE": selected_row.get("Entropy_Weight_RMSE", np.nan),
        "Entropy_Weight_R2": selected_row.get("Entropy_Weight_R2", np.nan),
        "Entropy_Weight_k": selected_row.get("Entropy_Weight_k", np.nan),
        "RMSE_Definition": "TRUE_OOB_RMSE_FROM_model.oob_prediction_",
        "OFS_Selection_Method": "PARETO_ENTROPY_UTOPIA_ALL_RANGE",
        "OFS_Scaling_Base": "ALL_TESTED_FEATURE_SETS",
    }]).to_excel(
        os.path.join(signature_dir, "automatic_feature_selection_summary.xlsx"),
        index=False,
    )

    heatmap_path = None
    feature_selection_path = None

    if (
        (not GENERATE_FIGURES_ONLY_FOR_FULL_DATA)
        or RUN_FULL_DATA
    ):
        heatmap_path = plot_spearman_filter_heatmap(
            full_raw=full_raw,
            candidate_features=candidate_features,
            output_dir=signature_dir,
        )

        feature_selection_path = plot_feature_set_selection_figure(
            subset_table=subset_table,
            selected_k=selected_k,
            output_dir=signature_dir,
        )

    print(f"  Candidate indicators: {len(candidate_features)}")
    print(f"  Predictors supplied to RF/SHAP: {len(retained)}")
    print("  Tail compatibility stage: AFTER OFS")
    print(f"  Utopia-selected k: {selected_k}")
    print(f"  OFS selected features: {selected_features}")
    print(f"  Threshold-supported features: {supported_features}")
    print(f"  Directions: {directions}")

    return {
        "Full_Raw": full_raw,
        "Class_Info": class_info,
        "Candidate_Features": candidate_features,
        "Post_Collinearity_Features": retained,
        "SHAP_Ranking": shap_ranking,
        "SHAP_Ranking_OFS_Eligible": shap_ranking_for_selection,
        "Threshold_Compatibility_Table": compatibility_table,
        "Subset_Table": subset_table,
        "Selected_Row": selected_row,
        "Selected_k": selected_k,
        "Selected_Features": selected_features,
        "Threshold_Supported_Features": supported_features,
        "Expected_Directions": directions,
        "Direction_Requires_Outer_Tail": direction_requires_outer_tail,
        "Signature_Dir": signature_dir,
        "Spearman_Heatmap_Path": heatmap_path,
        "Feature_Set_Selection_Figure_Path": feature_selection_path,
        "Subset_Results_Excel_Path": subset_excel_paths.get("subset_results"),
        "Subset_Results_Audit_Excel_Path": subset_excel_paths.get("subset_results_audit"),
    }


# ============================================================
# FULL-DATA HELPERS
# ============================================================

def reconstruct_full_raw_from_loyo_training_files(
    step2_dir,
    fold_names,
):
    """
    Reconstruct the complete raw historical dataset from the UNION of
    LOYO training files, retaining ALL common month-coded climate
    indicators. This makes full-data feature discovery independent of
    any historically supplied feature signature.
    """

    pieces = []
    common_features = None

    for fold_name in fold_names:
        fold_dir = os.path.join(step2_dir, fold_name)

        (
            _train_std_path,
            train_raw_path,
            _scaler_path,
        ) = locate_fold_files(fold_dir)

        raw = pd.read_excel(train_raw_path)

        if YEAR_COL not in raw.columns or TARGET_COL not in raw.columns:
            raise ValueError(
                f"{fold_name}: missing {YEAR_COL!r} or {TARGET_COL!r} in raw training file."
            )

        fold_features = set(
            detect_candidate_climate_features(raw.columns)
        )

        if common_features is None:
            common_features = fold_features
        else:
            common_features = common_features.intersection(fold_features)

        pieces.append(raw.copy())

    common_features = sorted(common_features or [])

    if len(common_features) < 2:
        raise ValueError(
            "Could not find at least 2 common month-coded climate indicators "
            "across the LOYO raw training files."
        )

    required_cols = [YEAR_COL, TARGET_COL, *common_features]

    trimmed = []
    for fold_name, raw in zip(fold_names, pieces):
        missing = [col for col in required_cols if col not in raw.columns]
        if missing:
            raise ValueError(
                f"{fold_name}: cannot reconstruct full data; missing raw columns: {missing}"
            )
        trimmed.append(raw[required_cols].copy())

    stacked = pd.concat(trimmed, ignore_index=True)

    numeric_cols = [TARGET_COL, *common_features]
    inconsistent = []

    for year, group in stacked.groupby(YEAR_COL):
        for col in numeric_cols:
            values = (
                pd.to_numeric(group[col], errors="coerce")
                .dropna()
                .to_numpy(dtype=float)
            )
            if len(values) <= 1:
                continue
            if np.nanmax(values) - np.nanmin(values) > 1e-10:
                inconsistent.append((int(year), col))

    if inconsistent:
        raise ValueError(
            "The same Year has inconsistent raw values across LOYO training files. "
            f"First cases: {inconsistent[:20]}"
        )

    full_raw = (
        stacked
        .sort_values(YEAR_COL)
        .drop_duplicates(subset=[YEAR_COL], keep="first")
        .reset_index(drop=True)
    )

    for col in required_cols:
        full_raw[col] = pd.to_numeric(full_raw[col], errors="coerce")

    bad_cols = [col for col in required_cols if full_raw[col].isna().any()]
    if bad_cols:
        raise ValueError(
            "Missing/non-numeric values in reconstructed full data: "
            f"{bad_cols}"
        )

    if len(full_raw) != len(fold_names):
        print(
            "\\nWARNING: reconstructed full-data year count "
            f"({len(full_raw)}) differs from number of LOYO folds "
            f"({len(fold_names)})."
        )

    return full_raw


def classify_full_data(
    full_raw,
):
    """
    Full-data yield classes used only for the full-data diagnostic.

    AUTO quantiles:
      N == 29 -> 0.11 / 0.89
      otherwise -> 0.10 / 0.90

    Explicit FULL_DATA_LOW_Q / FULL_DATA_HIGH_Q override AUTO.
    """

    n = len(
        full_raw
    )

    if (
        FULL_DATA_LOW_Q is None
        and
        FULL_DATA_HIGH_Q is None
    ):

        if n == 29:
            low_q = 0.11
            high_q = 0.89
            quantile_mode = (
                "AUTO_SHORT_SERIES_11_89"
            )

        else:
            low_q = 0.10
            high_q = 0.90
            quantile_mode = (
                "AUTO_STANDARD_10_90"
            )

    elif (
        FULL_DATA_LOW_Q is not None
        and
        FULL_DATA_HIGH_Q is not None
    ):

        low_q = float(
            FULL_DATA_LOW_Q
        )

        high_q = float(
            FULL_DATA_HIGH_Q
        )

        quantile_mode = (
            "USER_DEFINED"
        )

    else:
        raise ValueError(
            "Set both FULL_DATA_LOW_Q and FULL_DATA_HIGH_Q, "
            "or leave both as None."
        )

    if not (
        0.0
        < low_q
        < high_q
        < 1.0
    ):
        raise ValueError(
            "Need 0 < full-data low quantile < "
            "full-data high quantile < 1."
        )

    low_thr = float(
        full_raw[
            TARGET_COL
        ].quantile(
            low_q
        )
    )

    high_thr = float(
        full_raw[
            TARGET_COL
        ].quantile(
            high_q
        )
    )

    if not (
        low_thr
        < high_thr
    ):
        raise ValueError(
            "Full-data low/high yield thresholds are not ordered."
        )

    out = full_raw.copy()

    out[
        "Yield_Class"
    ] = "No"

    out.loc[
        out[
            TARGET_COL
        ]
        <= low_thr,
        "Yield_Class",
    ] = "Sh"

    out.loc[
        out[
            TARGET_COL
        ]
        >= high_thr,
        "Yield_Class",
    ] = "Bo"

    if FULL_DATA_FORCE_SH_YEARS:

        out.loc[
            out[
                YEAR_COL
            ]
            .astype(int)
            .isin(
                [
                    int(x)
                    for x
                    in FULL_DATA_FORCE_SH_YEARS
                ]
            ),
            "Yield_Class",
        ] = "Sh"

    if FULL_DATA_FORCE_BO_YEARS:

        out.loc[
            out[
                YEAR_COL
            ]
            .astype(int)
            .isin(
                [
                    int(x)
                    for x
                    in FULL_DATA_FORCE_BO_YEARS
                ]
            ),
            "Yield_Class",
        ] = "Bo"

    counts = (
        out[
            "Yield_Class"
        ]
        .value_counts()
        .reindex(
            [
                "Sh",
                "No",
                "Bo",
            ],
            fill_value=0,
        )
    )

    for cls in [
        "Sh",
        "No",
        "Bo",
    ]:

        if int(
            counts[
                cls
            ]
        ) == 0:

            raise ValueError(
                f"Full-data class {cls} has zero observations."
            )

    info = {
        "N_Years":
            int(
                n
            ),
        "Quantile_Mode":
            quantile_mode,
        "Low_Quantile":
            low_q,
        "High_Quantile":
            high_q,
        "Low_Yield_Threshold":
            low_thr,
        "High_Yield_Threshold":
            high_thr,
        "N_Sh":
            int(
                counts[
                    "Sh"
                ]
            ),
        "N_No":
            int(
                counts[
                    "No"
                ]
            ),
        "N_Bo":
            int(
                counts[
                    "Bo"
                ]
            ),
        "Forced_Sh_Years":
            "; ".join(
                str(
                    int(x)
                )
                for x
                in FULL_DATA_FORCE_SH_YEARS
            ),
        "Forced_Bo_Years":
            "; ".join(
                str(
                    int(x)
                )
                for x
                in FULL_DATA_FORCE_BO_YEARS
            ),
    }

    return (
        out,
        info,
    )


def standardize_full_data(
    full_raw,
):
    """
    Fit StandardScaler ONCE on the complete full-data record,
    exactly as required for a non-LOYO full-data model.
    """

    variables = [
        *FIXED_FEATURES,
        TARGET_COL,
    ]

    scaler = StandardScaler()

    z = scaler.fit_transform(
        full_raw[
            variables
        ].astype(
            float
        )
    )

    full_std = full_raw[
        [
            YEAR_COL,
            "Yield_Class",
        ]
    ].copy()

    for i, variable in enumerate(
        variables
    ):

        full_std[
            variable
        ] = z[
            :,
            i,
        ]

    scalers = {
        variable: {
            "mean":
                float(
                    scaler.mean_[
                        i
                    ]
                ),
            "scale":
                float(
                    scaler.scale_[
                        i
                    ]
                ),
        }
        for i, variable
        in enumerate(
            variables
        )
    }

    scaler_table = pd.DataFrame(
        [
            {
                "Variable":
                    variable,
                "Training_Mean":
                    scalers[
                        variable
                    ][
                        "mean"
                    ],
                "Training_Scale":
                    scalers[
                        variable
                    ][
                        "scale"
                    ],
            }
            for variable
            in variables
        ]
    )

    return (
        full_std,
        scalers,
        scaler_table,
    )


def build_rules_from_threshold_table(
    thresholds,
    record_id,
):
    """
    Same rule-assembly logic used in the LOYO loop, but reusable
    for the one full-data run.
    """

    rule_rows = []

    for feature in FIXED_FEATURES:

        part = thresholds[
            thresholds[
                "Feature"
            ]
            == feature
        ].copy()

        expected_dirs = (
            EXPECTED_DIRECTIONS[
                feature
            ]
        )

        lower_row = part[
            part[
                "Direction"
            ]
            == "lower"
        ]

        upper_row = part[
            part[
                "Direction"
            ]
            == "upper"
        ]

        def get_num(
            df,
            column,
        ):

            if df.empty:
                return np.nan

            value = df.iloc[
                0
            ][
                column
            ]

            return (
                float(
                    value
                )
                if pd.notna(
                    value
                )
                else np.nan
            )

        lower_sti = get_num(
            lower_row,
            "STi",
        )

        upper_sti = get_num(
            upper_row,
            "STi",
        )

        lower_sta = get_num(
            lower_row,
            "STa",
        )

        upper_sta = get_num(
            upper_row,
            "STa",
        )

        if (
            np.isfinite(
                lower_sti
            )
            and
            np.isfinite(
                upper_sti
            )
            and
            lower_sti
            >= upper_sti
        ):

            lower_sti = np.nan
            upper_sti = np.nan

        if (
            np.isfinite(
                lower_sta
            )
            and
            np.isfinite(
                upper_sta
            )
            and
            lower_sta
            >= upper_sta
        ):

            if (
                np.isfinite(
                    lower_sti
                )
                and
                np.isfinite(
                    upper_sti
                )
                and
                lower_sti
                < upper_sti
            ):

                lower_sta = lower_sti
                upper_sta = upper_sti

                sta_pair_status = (
                    "AUTO_STa_OVERLAP_FALLBACK_TO_STi"
                )

            else:

                lower_sta = np.nan
                upper_sta = np.nan

                sta_pair_status = (
                    "INVALID_TWO_SIDED_RULE"
                )

        else:
            sta_pair_status = (
                "VALID"
            )

        sti_available_sides = (
            int(
                np.isfinite(
                    lower_sti
                )
            )
            +
            int(
                np.isfinite(
                    upper_sti
                )
            )
        )

        sta_available_sides = (
            int(
                np.isfinite(
                    lower_sta
                )
            )
            +
            int(
                np.isfinite(
                    upper_sta
                )
            )
        )

        expected_side_count = len(
            expected_dirs
        )

        def completeness(
            n_available,
            n_expected,
        ):

            if n_available == 0:
                return "UNAVAILABLE"

            if (
                n_available
                < n_expected
            ):
                return "PARTIAL"

            return "FULL"

        rule_rows.append({
            "Record":
                record_id,
            "Feature":
                feature,
            "Expected_Directions":
                "+".join(
                    expected_dirs
                ),
            "Expected_Side_Count":
                expected_side_count,

            "Lower_STi":
                lower_sti,
            "Upper_STi":
                upper_sti,
            "STi_Available_Sides":
                sti_available_sides,
            "STi_Feature_Available":
                sti_available_sides
                >= 1,
            "STi_Completeness":
                completeness(
                    sti_available_sides,
                    expected_side_count,
                ),

            "Lower_Auto_STa":
                lower_sta,
            "Upper_Auto_STa":
                upper_sta,
            "STa_Available_Sides":
                sta_available_sides,
            "STa_Feature_Available":
                sta_available_sides
                >= 1,
            "STa_Completeness":
                completeness(
                    sta_available_sides,
                    expected_side_count,
                ),
            "STa_Pair_Status":
                sta_pair_status,

        })

    return pd.DataFrame(
        rule_rows
    )



def format_short_number(value):
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "NA"
    value = float(value)
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{value:.2f}".rstrip("0").rstrip(".")


def format_value_list(values):
    clean = [
        float(v)
        for v in values
        if pd.notna(v) and np.isfinite(float(v))
    ]
    if len(clean) == 0:
        return "NA"
    return ", ".join(format_short_number(v) for v in clean)


def simple_gaussian_kde(values, grid):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    grid = np.asarray(grid, dtype=float)

    if len(values) == 0:
        return np.full_like(grid, np.nan, dtype=float)

    if len(values) == 1:
        bw = max(1e-6, np.ptp(grid) / 25 if np.ptp(grid) > 0 else 1.0)
    else:
        sd = float(np.nanstd(values, ddof=1))
        bw = 1.06 * sd * (len(values) ** (-1 / 5))
        if (not np.isfinite(bw)) or bw <= 0:
            bw = max(1e-6, np.ptp(grid) / 25 if np.ptp(grid) > 0 else 1.0)

    z = (grid[:, None] - values[None, :]) / bw
    dens = np.exp(-0.5 * z**2).mean(axis=1) / (bw * np.sqrt(2 * np.pi))
    return dens


def get_feature_axis_label(feature):
    if str(feature).startswith("RX"):
        unit = "mm"
    else:
        unit = "day"
    return f"{feature} ({unit})"


def collect_threshold_info_for_feature(thresholds, feature):
    info = {
        "lower": None,
        "upper": None,
    }

    part = thresholds[thresholds["Feature"] == feature].copy()

    for direction in ["lower", "upper"]:
        row = part[part["Direction"] == direction]
        if len(row) == 0:
            continue
        info[direction] = row.iloc[0].to_dict()

    return info




def plot_spearman_filter_heatmap(full_raw, candidate_features, output_dir):
    """Triangular absolute-Spearman heatmap used for collinearity filtering."""
    if (not GENERATE_AUTOMATIC_SIGNATURE_FIGURES) or len(candidate_features) == 0:
        return None

    corr = (
        full_raw[candidate_features]
        .astype(float)
        .corr(method="spearman")
        .abs()
    )

    n = corr.shape[0]
    mask = np.triu(np.ones((n, n), dtype=bool), k=1)
    data = corr.to_numpy(dtype=float).copy()
    data[mask] = np.nan

    cmap = plt.cm.viridis.copy()
    cmap.set_bad(color="white")

    fig, ax = plt.subplots(
        figsize=(max(8.0, 0.44 * n + 3.0), max(8.0, 0.44 * n + 2.6))
    )

    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(candidate_features, rotation=90, fontsize=8)
    ax.set_yticklabels(candidate_features, fontsize=8)
    ax.set_title(REGION_NAME, fontsize=18, fontweight="bold", pad=10)

    for i in range(n):
        for j in range(i + 1):
            val = corr.iat[i, j]
            if i == j:
                label = "1"
            elif np.isfinite(val) and val >= COLLINEARITY_ABS_RHO - 1e-12:
                label = f"{val:.2f}"
            else:
                label = None

            if label is not None:
                ax.text(
                    j,
                    i,
                    label,
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="black",
                )

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=8)

    fig.tight_layout()
    path = os.path.join(output_dir, f"spearman_filter_heatmap.{FIGURE_IMAGE_FORMAT}")
    save_raster_figure(fig, path)
    plt.close(fig)
    return path


def plot_feature_set_selection_figure(subset_table, selected_k, output_dir):
    """One-panel dual-axis summary of OOB RMSE and OOB R2 vs k."""
    if (not GENERATE_AUTOMATIC_SIGNATURE_FIGURES) or subset_table is None or len(subset_table) == 0:
        return None

    plot_df = subset_table.copy()
    plot_df = plot_df[pd.notna(plot_df["OOB_RMSE"]) & pd.notna(plot_df["OOB_R2"])].copy()

    if plot_df.empty:
        return None

    plot_df = plot_df.sort_values("k").reset_index(drop=True)
    plot_df["Selected"] = plot_df["k"].astype(int) == int(selected_k)

    fig, ax1 = plt.subplots(figsize=(8.4, 5.2))
    ax2 = ax1.twinx()

    ln1 = ax1.plot(
        plot_df["k"],
        plot_df["OOB_RMSE"],
        marker="o",
        linewidth=2.0,
        label="OOB RMSE",
    )

    ln2 = ax2.plot(
        plot_df["k"],
        plot_df["OOB_R2"],
        marker="s",
        linewidth=2.0,
        label="OOB R²",
    )

    ofs = plot_df.loc[plot_df["Selected"]]
    ofs_handles = []

    if not ofs.empty:
        ofs_row = ofs.iloc[0]
        sc1 = ax1.scatter(
            [ofs_row["k"]],
            [ofs_row["OOB_RMSE"]],
            s=65,
            color="black",
            zorder=5,
            label="OFS",
        )
        ax2.scatter(
            [ofs_row["k"]],
            [ofs_row["OOB_R2"]],
            s=65,
            color="black",
            zorder=5,
        )
        ax1.axvline(float(ofs_row["k"]), color="black", linewidth=1.0, alpha=0.35)
        ax1.annotate(
            f"OFS = {int(ofs_row['k'])}",
            xy=(ofs_row["k"], ofs_row["OOB_RMSE"]),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9,
            color="black",
        )
        ofs_handles.append(sc1)

    ax1.set_xlabel("Num. of features", fontsize=12, fontweight="bold")
    ax1.set_ylabel("OOB RMSE (ton/ha)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("OOB R²", fontsize=12, fontweight="bold")
    ax1.set_title(f"{REGION_NAME} | Feature set selection", fontsize=16, fontweight="bold", pad=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(sorted(plot_df["k"].astype(int).tolist()))

    handles = ln1 + ln2 + ofs_handles
    labels = [h.get_label() for h in handles]
    ax1.legend(handles, labels, loc="best", framealpha=0.95, fontsize=10)

    fig.tight_layout()
    path = os.path.join(output_dir, f"feature_set_selection.{FIGURE_IMAGE_FORMAT}")
    save_raster_figure(fig, path)
    plt.close(fig)
    return path


def plot_full_data_pdp_summary_figure(
    full_output,
    full_raw,
    thresholds,
    grids_raw,
    boot_results,
    yield_scale,
    yield_mean,
    model_info,
    shap_ranking,
    selected_row,
    sti_candidates=None,
):
    """Create the historical-like PDP overview figure for the automatic workflow."""
    if (not GENERATE_AUTOMATIC_SIGNATURE_FIGURES) or len(FIXED_FEATURES) == 0:
        return None

    n_features = len(FIXED_FEATURES)
    width_ratios = [1.35] + [1.0] * n_features
    fig, axes = plt.subplots(
        1,
        n_features + 1,
        figsize=(max(14.0, 3.4 * (n_features + 1)), 4.2),
        gridspec_kw={"width_ratios": width_ratios},
    )

    ax0 = axes[0]
    shap_df = shap_ranking.copy()
    shap_df = shap_df[shap_df["Feature"].isin(FIXED_FEATURES)].copy()
    shap_df = shap_df.sort_values("Mean_Abs_SHAP", ascending=True)
    ax0.barh(shap_df["Feature"], shap_df["Mean_Abs_SHAP"], color="skyblue", edgecolor="none")
    ax0.set_xlabel("Importance", fontsize=11, fontweight="bold")
    ax0.set_ylabel("Top features", fontsize=11, fontweight="bold")
    ax0.set_title(REGION_NAME, fontsize=15, fontweight="bold", pad=4)
    ax0.tick_params(axis="both", labelsize=9)

    metric_r2 = selected_row.get("OOB_R2", model_info.get("OOB_R2", np.nan)) if selected_row is not None else model_info.get("OOB_R2", np.nan)
    metric_rmse = selected_row.get("OOB_RMSE", model_info.get("OOB_RMSE", np.nan)) if selected_row is not None else model_info.get("OOB_RMSE", np.nan)

    metric_box = (
        "Metrics\n"
        f"RF R²: {format_short_number(metric_r2)}\n"
        f"RF RMSE: {format_short_number(metric_rmse)}"
    )
    ax0.text(
        0.98,
        0.02,
        metric_box,
        transform=ax0.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="white", edgecolor="0.7", alpha=0.95),
    )

    legend_handles = None

    for col_idx, feature in enumerate(FIXED_FEATURES, start=1):
        ax = axes[col_idx]

        curves_std = np.vstack([result[feature] for result in boot_results])
        curves_raw = curves_std * yield_scale + yield_mean
        mean_curve = np.nanmean(curves_raw, axis=0)
        ci_low = np.nanpercentile(curves_raw, 2.5, axis=0)
        ci_high = np.nanpercentile(curves_raw, 97.5, axis=0)
        x_raw = grids_raw[feature]

        fill_ci = ax.fill_between(x_raw, ci_low, ci_high, color="blue", alpha=0.25)
        line_mean, = ax.plot(x_raw, mean_curve, color="blue", linewidth=1.5)

        feat_thr = thresholds[thresholds["Feature"] == feature].copy()
        feat_thr = feat_thr[feat_thr["Status"] == "VALID"].copy()
        feat_thr = feat_thr.sort_values(["Direction", "STi"])

        pv_used = np.nan
        if not feat_thr.empty and pd.notna(feat_thr.iloc[0].get("PV_Used", np.nan)):
            pv_used = float(feat_thr.iloc[0]["PV_Used"])
        elif "Yield_Class" in full_raw.columns:
            pv_used = float(full_raw.loc[full_raw["Yield_Class"].astype(str) == "No", TARGET_COL].mean())

        line_pv = ax.axhline(pv_used, color="green", linestyle="--", linewidth=1.0)

        box_lines = []
        line_sti = None
        shade = None

        if sti_candidates is not None and not sti_candidates.empty:
            feat_sti = sti_candidates[
                sti_candidates["Feature"].astype(str) == str(feature)
            ].copy()
        else:
            feat_sti = pd.DataFrame()

        if not feat_sti.empty:
            feat_sti = feat_sti.sort_values(["Direction", "STi_Candidate_Index"])
            for _, row in feat_sti.iterrows():
                sti = float(row["STi_Candidate"])
                selected_flag = bool(row.get("Selected_Automatically", False))
                line_sti = ax.axvline(
                    sti,
                    color="red",
                    linestyle="--",
                    linewidth=(1.6 if selected_flag else 0.9),
                    alpha=(1.0 if selected_flag else 0.65),
                )
                if str(row["Direction"]) == "lower":
                    left = min(float(row["CI_Lower"]), sti)
                    right = max(float(row["CI_Lower"]), sti)
                    margin_txt = f"M: -{format_short_number(abs(sti - float(row['CI_Lower'])))}"
                else:
                    left = min(sti, float(row["CI_Upper"]))
                    right = max(sti, float(row["CI_Upper"]))
                    margin_txt = f"M: +{format_short_number(abs(float(row['CI_Upper']) - sti))}"
                shade = ax.axvspan(
                    left,
                    right,
                    color="gray",
                    alpha=(0.30 if selected_flag else 0.12),
                )
                box_lines.append(f"STi: {format_short_number(sti)}")
                box_lines.append(margin_txt)
        else:
            for _, row in feat_thr.iterrows():
                sti = float(row["STi"])
                line_sti = ax.axvline(sti, color="red", linestyle="--", linewidth=1.0)
                if str(row["Direction"]) == "lower":
                    left = min(float(row["CI_Lower"]), sti)
                    right = max(float(row["CI_Lower"]), sti)
                    margin_txt = f"M: -{format_short_number(abs(sti - float(row['CI_Lower'])))}"
                else:
                    left = min(sti, float(row["CI_Upper"]))
                    right = max(sti, float(row["CI_Upper"]))
                    margin_txt = f"M: +{format_short_number(abs(float(row['CI_Upper']) - sti))}"
                shade = ax.axvspan(left, right, color="gray", alpha=0.35)
                box_lines.append(f"STi: {format_short_number(sti)}")
                box_lines.append(margin_txt)

        if box_lines:
            ax.text(
                0.03,
                0.96,
                "\n".join(box_lines),
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=7.5,
                bbox=dict(boxstyle="round", facecolor="white", edgecolor="0.7", alpha=0.95),
            )

        # Feature title only on the bottom x-axis, matching the density plots.
        ax.set_xlabel(get_feature_axis_label(feature), fontsize=10, fontweight="bold")
        if col_idx == 1:
            ax.set_ylabel("Detrended Yield (ton/ha)", fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="both", labelsize=8.5)

        if legend_handles is None:
            legend_handles = [
                line_mean,
                fill_ci,
                line_sti,
                shade,
                line_pv,
            ]
            legend_labels = [
                "PDP mean",
                "95% CI",
                "STi",
                "M",
                f"PV: {format_short_number(pv_used)}",
            ]
            ax.legend(legend_handles, legend_labels, fontsize=8, loc="upper right", framealpha=0.95)

    # No overall figure title: feature labels are shown only on the x-axes.
    fig.tight_layout(rect=[0, 0, 1, 0.99], w_pad=1.1)

    path = os.path.join(full_output, f"automatic_pdp_overview.{FIGURE_IMAGE_FORMAT}")
    save_raster_figure(fig, path)
    plt.close(fig)
    return path


def _prepare_full_data_density_feature(
    full_raw,
    thresholds,
    feature,
):
    """
    Prepare class observations, KDE curves, skewness, and x-range
    for one feature.

    IMPORTANT:
    KDE curves are NOT vertically rescaled by class. Only the
    observation spikes/rugs are displayed at different heights.
    """

    feature_rows = (
        collect_threshold_info_for_feature(
            thresholds=thresholds,
            feature=feature,
        )
    )

    class_values = {}
    all_numeric = []

    for cls in [
        "Sh",
        "No",
        "Bo",
    ]:

        vals = (
            full_raw.loc[
                full_raw[
                    "Yield_Class"
                ].astype(str)
                == cls,
                feature,
            ]
            .dropna()
            .astype(float)
            .to_numpy()
        )

        class_values[
            cls
        ] = vals

        if len(
            vals
        ) > 0:
            all_numeric.extend(
                vals.tolist()
            )

    vertical_refs = []

    for direction in [
        "lower",
        "upper",
    ]:

        row = feature_rows[
            direction
        ]

        if row is None:
            continue

        for key in [
            "STi",
            "CI_Lower",
            "CI_Upper",
            "STa",
        ]:

            if (
                key in row
                and
                pd.notna(
                    row[
                        key
                    ]
                )
            ):
                vertical_refs.append(
                    float(
                        row[
                            key
                        ]
                    )
                )

    if (
        len(
            all_numeric
        ) == 0
        and
        len(
            vertical_refs
        ) == 0
    ):

        xmin = 0.0
        xmax = 1.0

    else:

        pool = np.asarray(
            all_numeric
            + vertical_refs,
            dtype=float,
        )

        xmin = float(
            np.nanmin(
                pool
            )
        )

        xmax = float(
            np.nanmax(
                pool
            )
        )

        if xmin == xmax:
            xmin -= 0.5
            xmax += 0.5

        xpad = (
            0.07
            * (
                xmax
                - xmin
            )
        )

        xmin -= xpad
        xmax += xpad

    x_grid = np.linspace(
        xmin,
        xmax,
        350,
    )

    density_curves = {}
    density_max = 0.0
    skews = {}

    for cls in [
        "Sh",
        "No",
        "Bo",
    ]:

        vals = class_values[
            cls
        ]

        curve = simple_gaussian_kde(
            vals,
            x_grid,
        )

        density_curves[
            cls
        ] = curve

        if np.isfinite(
            curve
        ).any():

            density_max = max(
                density_max,
                float(
                    np.nanmax(
                        curve
                    )
                ),
            )

        if len(
            vals
        ) >= 3:

            skews[
                cls
            ] = float(
                pd.Series(
                    vals
                ).skew()
            )

        else:

            skews[
                cls
            ] = np.nan

    if (
        density_max
        <= 0
        or
        not np.isfinite(
            density_max
        )
    ):

        density_max = 1.0

    return {
        "feature_rows":
            feature_rows,

        "class_values":
            class_values,

        "xmin":
            xmin,

        "xmax":
            xmax,

        "x_grid":
            x_grid,

        "density_curves":
            density_curves,

        "density_max":
            density_max,

        "skews":
            skews,
    }


def _draw_full_data_density_axis(
    ax,
    feature,
    prepared,
    sta_col,
    mode_name,
    show_feature_title=True,
    show_ylabel=False,
):
    """
    Draw one automatic full-data density panel.

    Sh/Bo observation spikes are intentionally taller than No
    observation spikes FOR DISPLAY ONLY. KDE curves are unchanged.
    """

    feature_rows = prepared[
        "feature_rows"
    ]

    class_values = prepared[
        "class_values"
    ]

    xmin = prepared[
        "xmin"
    ]

    xmax = prepared[
        "xmax"
    ]

    x_grid = prepared[
        "x_grid"
    ]

    density_curves = prepared[
        "density_curves"
    ]

    density_max = prepared[
        "density_max"
    ]

    skews = prepared[
        "skews"
    ]

    class_colors = {
        "Sh":
            "red",
        "No":
            "blue",
        "Bo":
            "green",
    }

    legend_handles = []

    # --------------------------------------------------------
    # Density curves + class observation spikes
    #
    # KDE curves remain on their actual density scale.
    # Only spike HEIGHT differs by class for visual separation.
    # --------------------------------------------------------

    for cls in [
        "Sh",
        "No",
        "Bo",
    ]:

        color = class_colors[
            cls
        ]

        curve = density_curves[
            cls
        ]

        if np.isfinite(
            curve
        ).any():

            ax.plot(
                x_grid,
                curve,
                color=color,
                lw=1.6,
                zorder=3,
            )

        vals = class_values[
            cls
        ]

        if len(
            vals
        ) > 0:

            spike_height = (
                FULL_DATA_RUG_HEIGHT_FRACTION[
                    cls
                ]
                * density_max
            )

            ax.vlines(
                vals,
                0,
                spike_height,
                colors=color,
                alpha=
                    FULL_DATA_RUG_ALPHA[
                        cls
                    ],
                lw=1.0,
                zorder=2,
            )

        sk_txt = (
            format_short_number(
                skews[
                    cls
                ]
            )
            if np.isfinite(
                skews[
                    cls
                ]
            )
            else "NA"
        )

        legend_handles.append(
            Line2D(
                [
                    0
                ],
                [
                    0
                ],
                color=color,
                lw=1.6,
                label=
                    f"{cls} "
                    f"(sk: {sk_txt})",
            )
        )

    # --------------------------------------------------------
    # PV rescue diagnostic in AUTOMATIC panels only.
    # --------------------------------------------------------

    if True:

        pv_adjusted_rows = []

        for direction_key in [
            "lower",
            "upper",
        ]:

            row_for_pv = feature_rows[
                direction_key
            ]

            if (
                row_for_pv is not None
                and
                bool(
                    row_for_pv.get(
                        "PV_Adjusted",
                        False,
                    )
                )
            ):

                pv_adjusted_rows.append(
                    row_for_pv
                )

        if len(
            pv_adjusted_rows
        ) > 0:

            row_for_pv = pv_adjusted_rows[
                0
            ]

            alpha_txt = format_short_number(
                row_for_pv.get(
                    "PV_Adjustment_Alpha",
                    np.nan,
                )
            )

            legend_handles.append(
                Line2D(
                    [0],
                    [0],
                    color="none",
                    lw=0,
                    label=
                        f"PV adj. α: {alpha_txt}",
                )
            )

    sti_vals = []
    margin_labels = []
    sta_vals = []

    for direction in [
        "lower",
        "upper",
    ]:

        row = feature_rows[
            direction
        ]

        if row is None:
            continue

        if pd.notna(
            row.get(
                "STi",
                np.nan,
            )
        ):

            sti = float(
                row[
                    "STi"
                ]
            )

            sti_vals.append(
                sti
            )

            ax.axvline(
                sti,
                color="black",
                lw=1.1,
                ls=":",
                zorder=5,
            )

        ci_lower = row.get(
            "CI_Lower",
            np.nan,
        )

        ci_upper = row.get(
            "CI_Upper",
            np.nan,
        )

        sti = row.get(
            "STi",
            np.nan,
        )

        if pd.notna(
            sti
        ):
            sti = float(
                sti
            )

        if pd.notna(
            ci_lower
        ):
            ci_lower = float(
                ci_lower
            )

        if pd.notna(
            ci_upper
        ):
            ci_upper = float(
                ci_upper
            )

        if (
            direction
            == "lower"
            and
            pd.notna(
                sti
            )
            and
            pd.notna(
                ci_lower
            )
        ):

            left = min(
                ci_lower,
                sti,
            )

            right = max(
                ci_lower,
                sti,
            )

            ax.axvspan(
                left,
                right,
                color="0.82",
                alpha=0.9,
                zorder=1,
            )

            margin_labels.append(
                f"-"
                f"{format_short_number(abs(sti - ci_lower))}"
            )

        if (
            direction
            == "upper"
            and
            pd.notna(
                sti
            )
            and
            pd.notna(
                ci_upper
            )
        ):

            left = min(
                sti,
                ci_upper,
            )

            right = max(
                sti,
                ci_upper,
            )

            ax.axvspan(
                left,
                right,
                color="0.82",
                alpha=0.9,
                zorder=1,
            )

            margin_labels.append(
                f"+"
                f"{format_short_number(abs(ci_upper - sti))}"
            )

        sta_val = row.get(
            sta_col,
            np.nan,
        )

        if pd.notna(
            sta_val
        ):

            sta_val = float(
                sta_val
            )

            sta_vals.append(
                sta_val
            )

            ax.axvline(
                sta_val,
                color="black",
                lw=1.6,
                ls="-",
                zorder=6,
            )

    if len(
        sti_vals
    ) > 0:

        legend_handles.append(
            Line2D(
                [
                    0
                ],
                [
                    0
                ],
                color="black",
                lw=1.1,
                ls=":",
                label=
                    f"STi: "
                    f"{format_value_list(sti_vals)}",
            )
        )

    if len(
        margin_labels
    ) > 0:

        legend_handles.append(
            Patch(
                facecolor="0.82",
                edgecolor="0.82",
                label=
                    f"M "
                    f"({', '.join(margin_labels)})",
            )
        )

    if len(
        sta_vals
    ) > 0:

        legend_handles.append(
            Line2D(
                [
                    0
                ],
                [
                    0
                ],
                color="black",
                lw=1.6,
                ls="-",
                label=
                    f"STa: "
                    f"{format_value_list(sta_vals)}",
            )
        )

    ax.set_xlim(
        xmin,
        xmax,
    )

    ax.set_ylim(
        0,
        density_max
        * 1.12,
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    if show_feature_title:

        ax.set_title(
            get_feature_axis_label(
                feature
            ),
            fontsize=10,
            pad=6,
        )

    if show_ylabel:

        ax.set_ylabel(
            f"Density ({REGION_NAME})",
            fontsize=10,
        )

    ax.set_xlabel(
        get_feature_axis_label(
            feature
        ),
        fontsize=9,
    )

    ax.tick_params(
        axis="both",
        labelsize=8,
    )

    ax.legend(
        handles=
            legend_handles,
        fontsize=7,
        loc="upper right",
        framealpha=0.95,
        handlelength=1.5,
    )


def _save_single_full_data_sta_figure(
    full_raw,
    thresholds,
    output_dir,
    mode_name,
    sta_col,
):
    """
    Save the automatic full-data STa density figure.
    """

    n_features = len(
        FIXED_FEATURES
    )

    if n_features == 0:
        return None

    fig, axes = plt.subplots(
        nrows=1,
        ncols=n_features,
        figsize=(
            max(
                3.4
                * n_features,
                8,
            ),
            3.9,
        ),
        squeeze=False,
    )

    for col_idx, feature in enumerate(
        FIXED_FEATURES
    ):

        prepared = (
            _prepare_full_data_density_feature(
                full_raw=
                    full_raw,
                thresholds=
                    thresholds,
                feature=
                    feature,
            )
        )

        _draw_full_data_density_axis(
            ax=
                axes[
                    0,
                    col_idx,
                ],
            feature=
                feature,
            prepared=
                prepared,
            sta_col=
                sta_col,
            mode_name=
                mode_name,
            show_feature_title=
                False,
            show_ylabel=
                (
                    col_idx
                    == 0
                ),
        )
    title_text = (
        f"{REGION_NAME} | Full data | Automatic STa"
    )

    basename = (
        "full_data_automatic_STa"
    )

    fig.suptitle(
        title_text,
        fontsize=14,
        y=0.98,
    )

    fig.tight_layout(
        rect=[
            0,
            0,
            1,
            0.955,
        ],
        w_pad=1.0,
    )

    image_path = os.path.join(
        output_dir,
        f"{basename}.{FIGURE_IMAGE_FORMAT}",
    )

    save_raster_figure(
        fig,
        image_path,
    )

    plt.close(
        fig
    )

    return {
        FIGURE_IMAGE_FORMAT:
            image_path,
    }


def run_full_data_fixed_signature(
    step2_dir,
    fold_names,
    output_dir,
):
    """
    Run the F1 fixed-signature derivation ONCE on the complete
    historical record, after the LOYO folds have finished.
    """

    print(
        "\n"
        + "=" * 90
    )

    print(
        "FULL-DATA FIXED-SIGNATURE F1 RUN"
    )

    print(
        "=" * 90
    )

    full_output = os.path.join(
        output_dir,
        "full_data",
    )

    os.makedirs(
        full_output,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Audit the exact signature used by FULL_DATA.
    # --------------------------------------------------------
    full_signature_audit_rows = []
    for feature in FIXED_FEATURES:
        full_signature_audit_rows.append({
            "Feature": feature,
            "Directions": "; ".join(EXPECTED_DIRECTIONS.get(feature, [])),
            "Require_Outer_Tail": DIRECTION_REQUIRES_OUTER_TAIL.get(feature, True),
            "Signature_Source": "AUTOMATIC_FULL_DATA_RF_SHAP_PARETO_UTOPIA_PDP",
            "Feature_Reselection_Performed_For_FULL_DATA": False,
        })

    pd.DataFrame(full_signature_audit_rows).to_excel(
        os.path.join(full_output, "full_data_signature_used.xlsx"),
        index=False,
    )

    # --------------------------------------------------------
    # A) Independent standalone FULL_DATA pair.
    # --------------------------------------------------------
    full_std_input, full_raw, _standalone_features, source_info = (
        load_standalone_full_data_pair()
    )

    # --------------------------------------------------------
    # B) Full-data Sh / No / Bo classes.
    # --------------------------------------------------------
    full_raw, class_info = classify_full_data(full_raw)

    full_raw.to_excel(
        os.path.join(
            full_output,
            "full_data_nonstandardized_with_classes.xlsx",
        ),
        index=False,
    )

    pd.DataFrame(
        [
            class_info
        ]
    ).to_excel(
        os.path.join(
            full_output,
            "full_data_classification_information.xlsx",
        ),
        index=False,
    )

    # --------------------------------------------------------
    # C) Use exact standalone standardized values; do not re-standardize.
    # --------------------------------------------------------
    full_std = full_std_input.copy().reset_index(drop=True)
    full_std["Yield_Class"] = full_raw["Yield_Class"].to_numpy()

    full_scalers, scaler_table = derive_scalers_from_paired_full_data(
        full_raw=full_raw,
        full_std=full_std,
        variables=[*FIXED_FEATURES, TARGET_COL],
    )

    full_std.to_excel(
        os.path.join(full_output, "full_data_standardized.xlsx"), index=False
    )
    scaler_table.to_excel(
        os.path.join(full_output, "scaler_parameters.xlsx"), index=False
    )
    pd.DataFrame([source_info]).to_excel(
        os.path.join(full_output, "standalone_full_data_source.xlsx"), index=False
    )

    # --------------------------------------------------------
    # D) Full-data PV from full-data Normal years.
    # --------------------------------------------------------

    normal_mask = (
        full_raw[
            "Yield_Class"
        ]
        .astype(str)
        == "No"
    )

    PV = float(
        full_raw.loc[
            normal_mask,
            TARGET_COL,
        ].mean()
    )

    shock_mask = (
        full_raw[
            "Yield_Class"
        ]
        .astype(str)
        == "Sh"
    )

    if shock_mask.sum() == 0:
        raise ValueError(
            "Full data: no Sh years available for automatic PV rescue."
        )

    SH_YIELD_MEAN = float(
        full_raw.loc[
            shock_mask,
            TARGET_COL,
        ].mean()
    )

    # --------------------------------------------------------
    # E) Fit/tune RF using ONLY fixed signature features.
    # --------------------------------------------------------

    X = (
        full_std[
            FIXED_FEATURES
        ]
        .astype(float)
        .copy()
    )

    y = (
        full_std[
            TARGET_COL
        ]
        .astype(float)
        .copy()
    )

    (
        tuned_rf,
        best_params,
        cv_score,
    ) = fit_tuned_rf(
        X,
        y,
    )

    # Diagnostic only: SHAP ranking within the already-fixed FULL_DATA feature
    # set. This ranking is NOT allowed to change feature membership or k.
    full_data_shap_ranking = calculate_mean_abs_shap_ranking(
        tuned_rf,
        X,
    )

    full_data_shap_ranking.to_excel(
        os.path.join(full_output, "full_data_fixed_signature_SHAP_ranking.xlsx"),
        index=False,
    )

    yield_scale = float(
        full_scalers[
            TARGET_COL
        ][
            "scale"
        ]
    )

    yield_mean = float(
        full_scalers[
            TARGET_COL
        ][
            "mean"
        ]
    )

    oob = calculate_oob_metrics(
        tuned_rf,
        y,
        yield_scale,
    )

    model_info = {
        "Run_Type":
            "FULL_DATA",
        "N_Years":
            len(
                full_raw
            ),
        "N_Fixed_Features":
            len(
                FIXED_FEATURES
            ),
        "Fixed_Features":
            "; ".join(
                FIXED_FEATURES
            ),
        "Feature_Discovery_Mode":
            "AUTOMATIC_FULL_DATA_RF_SHAP_ENTROPY_UTOPIA_PDP",
        "Feature_Reselection_Performed_For_FULL_DATA":
            False,
        "Best_Params":
            str(
                best_params
            ),
        "Inner_CV_Best_Score":
            cv_score,
        "Full_Data_PV":
            PV,
        "Low_Quantile":
            class_info[
                "Low_Quantile"
            ],
        "High_Quantile":
            class_info[
                "High_Quantile"
            ],
        "OOB_R2_Negative":
            bool(
                np.isfinite(oob["OOB_R2"])
                and oob["OOB_R2"] < 0
            ),
        "OOB_R2_Near_Zero_Negative":
            bool(
                np.isfinite(oob["OOB_R2"])
                and -float(OOB_R2_NEAR_ZERO_TOLERANCE)
                    <= oob["OOB_R2"] < 0
            ),
        "OOB_R2_Meaningfully_Negative":
            bool(
                np.isfinite(oob["OOB_R2"])
                and oob["OOB_R2"]
                    < -float(OOB_R2_NEAR_ZERO_TOLERANCE)
            ),
        "OOB_R2_Near_Zero_Tolerance":
            float(OOB_R2_NEAR_ZERO_TOLERANCE),
        "Model_Skill_Status":
            (
                "MEANINGFULLY_NEGATIVE_OOB_R2"
                if (
                    np.isfinite(oob["OOB_R2"])
                    and oob["OOB_R2"]
                        < -float(OOB_R2_NEAR_ZERO_TOLERANCE)
                )
                else (
                    "NEAR_ZERO_NEGATIVE_OOB_R2_RETAINED"
                    if (
                        np.isfinite(oob["OOB_R2"])
                        and oob["OOB_R2"] < 0
                    )
                    else "NONNEGATIVE_OOB_R2"
                )
            ),
        **oob,
    }

    pd.DataFrame(
        [
            model_info
        ]
    ).to_excel(
        os.path.join(
            full_output,
            "fixed_signature_model_information.xlsx",
        ),
        index=False,
    )

    # --------------------------------------------------------
    # F) PDP grids.
    # --------------------------------------------------------

    grids_std = {}
    grids_raw = {}

    for feature in FIXED_FEATURES:

        grids_std[
            feature
        ] = np.linspace(
            X[
                feature
            ].min(),
            X[
                feature
            ].max(),
            GRID_RESOLUTION,
        )

        grids_raw[
            feature
        ] = inverse_scale(
            grids_std[
                feature
            ],
            feature,
            full_scalers,
        )

    # --------------------------------------------------------
    # G) Same bootstrap PDP procedure, but on full data.
    # --------------------------------------------------------

    print(
        f"\nRunning {N_BOOTSTRAPS} full-data bootstrap PDP fits..."
    )

    boot_results = Parallel(
        n_jobs=N_JOBS
    )(
        delayed(
            bootstrap_pdp_run
        )(
            RANDOM_STATE
            + 9000000
            + b,
            X,
            y,
            grids_std,
            best_params,
        )
        for b in range(
            N_BOOTSTRAPS
        )
    )

    # --------------------------------------------------------
    # H) STi + margin + Auto-STa.
    # --------------------------------------------------------

    threshold_rows = []
    candidate_tables = []
    sti_candidate_tables = []

    for feature in FIXED_FEATURES:

        curves_std = np.vstack(
            [
                result[
                    feature
                ]
                for result
                in boot_results
            ]
        )

        curves_raw = (
            curves_std
            * yield_scale
            + yield_mean
        )

        mean_curve = curves_raw.mean(
            axis=0
        )

        x_raw = grids_raw[
            feature
        ]

        # ----------------------------------------------------
        # Resolve the feature-specific PV.
        #
        # Original PV is always tried first. Only if it has no
        # mean-PDP crossing do we move it minimally toward the
        # full-data Sh yield mean in fixed 0.05 steps, stopping before the midpoint.
        # ----------------------------------------------------

        pv_info = resolve_feature_pv_for_crossing(
            x_raw=
                x_raw,
            mean_curve=
                mean_curve,
            original_pv=
                PV,
            sh_yield_mean=
                SH_YIELD_MEAN,
        )

        PV_FEATURE = float(
            pv_info[
                "PV_Used"
            ]
        )

        for direction in EXPECTED_DIRECTIONS[
            feature
        ]:

            pdp_min = float(
                np.nanmin(
                    mean_curve
                )
            )

            pdp_max = float(
                np.nanmax(
                    mean_curve
                )
            )

            original_pv_within_pdp_range = bool(
                pdp_min
                <= PV
                <= pdp_max
            )

            pv_within_pdp_range = bool(
                pdp_min
                <= PV_FEATURE
                <= pdp_max
            )

            (
                selected_threshold,
                sti_candidate_df,
                sta_candidate_detail_df,
            ) = derive_best_multi_crossing_threshold(
                training_raw=full_raw,
                class_col="Yield_Class",
                feature=feature,
                direction=direction,
                x_raw=x_raw,
                mean_curve=mean_curve,
                curves_raw=curves_raw,
                pv=PV_FEATURE,
                require_outer_tail=DIRECTION_REQUIRES_OUTER_TAIL.get(feature, True),
            )

            if selected_threshold is None:
                crossing_status = (
                    "NO_VALID_CROSSING_WITHIN_ALLOWED_PV_SHIFT"
                    if (
                        not bool(
                            pv_info[
                                "PV_Used_Has_Crossing"
                            ]
                        )
                    )
                    else (
                        "NO_MEAN_PDP_CROSSING_AFTER_PV_RESOLUTION"
                    )
                )

                threshold_rows.append({
                    "Run_Type": "FULL_DATA",
                    "Feature": feature,
                    "Direction": direction,
                    "Status": "NO_PDP_CROSSING",
                    "Crossing_Status": crossing_status,
                    "PDP_Min": pdp_min,
                    "PDP_Max": pdp_max,
                    "Original_PV_Within_PDP_Range": original_pv_within_pdp_range,
                    "PV_Within_PDP_Range": pv_within_pdp_range,
                    "Original_PV": pv_info["Original_PV"],
                    "Sh_Yield_Mean": pv_info["Sh_Yield_Mean"],
                    "PV_Used": pv_info["PV_Used"],
                    "PV_Adjusted": pv_info["PV_Adjusted"],
                    "PV_Adjustment_Alpha": pv_info["PV_Adjustment_Alpha"],
                    "PV_Adjustment_Signed": pv_info["PV_Adjustment_Signed"],
                    "PV_Adjustment_Absolute": pv_info["PV_Adjustment_Absolute"],
                    "PV_Adjustment_Status": pv_info["PV_Adjustment_Status"],
                    "Original_PV_Has_Crossing": pv_info["Original_PV_Has_Crossing"],
                    "PV_Used_Has_Crossing": pv_info["PV_Used_Has_Crossing"],
                    "N_Mean_PDP_Crossings": 0,
                    "All_Mean_PDP_Crossings": "",
                    "Selected_STi_Candidate_Index": np.nan,
                    "STi": np.nan,
                    "CI_Lower": np.nan,
                    "CI_Upper": np.nan,
                    "Directional_Margin": np.nan,
                    "Bootstrap_N_Valid": 0,
                    "Bootstrap_Support": 0.0,
                    "STa": np.nan,
                    "STa_Selection": "UNAVAILABLE_NO_PDP_CROSSING",
                    "Training_PV": PV_FEATURE,
                })
                continue

            if not sti_candidate_df.empty:
                tmp_sti = sti_candidate_df.copy()
                tmp_sti.insert(0, "Run_Type", "FULL_DATA")
                tmp_sti["Original_PV"] = pv_info["Original_PV"]
                tmp_sti["Sh_Yield_Mean"] = pv_info["Sh_Yield_Mean"]
                tmp_sti["PV_Used"] = pv_info["PV_Used"]
                tmp_sti["PV_Adjusted"] = pv_info["PV_Adjusted"]
                tmp_sti["PV_Adjustment_Alpha"] = pv_info["PV_Adjustment_Alpha"]
                tmp_sti["PV_Adjustment_Status"] = pv_info["PV_Adjustment_Status"]
                sti_candidate_tables.append(tmp_sti)

            if not sta_candidate_detail_df.empty:
                tmp_sta = sta_candidate_detail_df.copy()
                tmp_sta.insert(0, "Run_Type", "FULL_DATA")
                tmp_sta.insert(1, "Feature", feature)
                tmp_sta.insert(2, "Direction", direction)
                tmp_sta["Original_PV"] = pv_info["Original_PV"]
                tmp_sta["Sh_Yield_Mean"] = pv_info["Sh_Yield_Mean"]
                tmp_sta["PV_Used"] = pv_info["PV_Used"]
                tmp_sta["PV_Adjusted"] = pv_info["PV_Adjusted"]
                tmp_sta["PV_Adjustment_Alpha"] = pv_info["PV_Adjustment_Alpha"]
                tmp_sta["PV_Adjustment_Status"] = pv_info["PV_Adjustment_Status"]
                candidate_tables.append(tmp_sta)

            sti = float(selected_threshold["STi_Candidate"])
            ci_lower = float(selected_threshold["CI_Lower"])
            ci_upper = float(selected_threshold["CI_Upper"])
            sta = float(selected_threshold["Auto_STa_Candidate"])
            sta_reason = selected_threshold["Auto_STa_Selection"]
            n_valid = int(selected_threshold["Bootstrap_N_Valid"])
            support = float(selected_threshold["Bootstrap_Support"])
            directional_margin = float(selected_threshold["Directional_Margin"])

            threshold_rows.append({
                "Run_Type": "FULL_DATA",
                "Feature": feature,
                "Direction": direction,
                "Status": "VALID",
                "Crossing_Status": (
                    "VALID_MULTI_CROSSING_SELECTION_ADJUSTED_PV"
                    if pv_info["PV_Adjusted"]
                    else "VALID_MULTI_CROSSING_SELECTION_ORIGINAL_PV"
                ),
                "PDP_Min": pdp_min,
                "PDP_Max": pdp_max,
                "Original_PV_Within_PDP_Range": original_pv_within_pdp_range,
                "PV_Within_PDP_Range": pv_within_pdp_range,
                "Original_PV": pv_info["Original_PV"],
                "Sh_Yield_Mean": pv_info["Sh_Yield_Mean"],
                "PV_Used": pv_info["PV_Used"],
                "PV_Adjusted": pv_info["PV_Adjusted"],
                "PV_Adjustment_Alpha": pv_info["PV_Adjustment_Alpha"],
                "PV_Adjustment_Signed": pv_info["PV_Adjustment_Signed"],
                "PV_Adjustment_Absolute": pv_info["PV_Adjustment_Absolute"],
                "PV_Adjustment_Status": pv_info["PV_Adjustment_Status"],
                "Original_PV_Has_Crossing": pv_info["Original_PV_Has_Crossing"],
                "PV_Used_Has_Crossing": pv_info["PV_Used_Has_Crossing"],
                "N_Mean_PDP_Crossings": int(selected_threshold["N_Mean_PDP_Crossings"]),
                "All_Mean_PDP_Crossings": selected_threshold["All_Mean_PDP_Crossings"],
                "Selected_STi_Candidate_Index": int(selected_threshold["STi_Candidate_Index"]),
                "STi": sti,
                "CI_Lower": ci_lower,
                "CI_Upper": ci_upper,
                "Directional_Margin": directional_margin,
                "Bootstrap_N_Valid": n_valid,
                "Bootstrap_Support": support,
                "STi_Sh_Hit": selected_threshold["STi_Sh_Hit"],
                "STi_No_Hit": selected_threshold["STi_No_Hit"],
                "STi_Bo_Hit": selected_threshold["STi_Bo_Hit"],
                "STi_Separation_Score": selected_threshold["STi_Separation_Score"],
                "STa": sta,
                "STa_Selection": sta_reason,
                "Auto_STa_Sh_Hit": selected_threshold["Auto_STa_Sh_Hit"],
                "Auto_STa_No_Hit": selected_threshold["Auto_STa_No_Hit"],
                "Auto_STa_Bo_Hit": selected_threshold["Auto_STa_Bo_Hit"],
                "Auto_STa_Separation_Score": selected_threshold["Auto_STa_Separation_Score"],
                "Auto_STa_Final_Linear_4_2_3_Score": selected_threshold.get(
                    "Auto_STa_Final_Linear_4_2_3_Score",
                    np.nan,
                ),
                "Auto_STa_ShNo_Separation": selected_threshold["Auto_STa_ShNo_Separation"],
                "Auto_STa_Distance_to_Sh_Median": selected_threshold["Auto_STa_Distance_to_Sh_Median"],
                "Auto_STa_Distance_to_Bo_Median": selected_threshold["Auto_STa_Distance_to_Bo_Median"],
                "Auto_STa_Local_Utopia_Distance": selected_threshold["Auto_STa_Local_Utopia_Distance"],
                "STi_Selection_Utopia_Distance": selected_threshold["STi_Selection_Utopia_Distance"],
                "STi_Selection_Method": selected_threshold.get(
                    "STi_Selection_Method",
                    "PARETO_FINAL_STa_LINEAR_4_2_3",
                ),
                "STi_Pareto_Efficient_Final_STa": selected_threshold.get(
                    "STi_Pareto_Efficient_Final_STa",
                    np.nan,
                ),
                "Sh_Median": selected_threshold["Sh_Median"],
                "Bo_Median": selected_threshold["Bo_Median"],
                "Training_PV": PV_FEATURE,
            })

    thresholds = pd.DataFrame(
        threshold_rows
    )

    thresholds.to_excel(
        os.path.join(
            full_output,
            "fixed_signature_thresholds_long.xlsx",
        ),
        index=False,
    )

    if candidate_tables:

        pd.concat(
            candidate_tables,
            ignore_index=True,
        ).to_excel(
            os.path.join(
                full_output,
                "fixed_signature_STa_candidates.xlsx",
            ),
            index=False,
        )

    if sti_candidate_tables:

        full_sti_candidates = pd.concat(
            sti_candidate_tables,
            ignore_index=True,
        )

        full_sti_candidates.to_excel(
            os.path.join(
                full_output,
                "fixed_signature_STi_candidates.xlsx",
            ),
            index=False,
        )

    else:
        full_sti_candidates = pd.DataFrame()

    # --------------------------------------------------------
    # I) Assemble the full-data rule table.
    # --------------------------------------------------------

    rules = (
        build_rules_from_threshold_table(
            thresholds=
                thresholds,
            record_id=
                "FULL_DATA",
        )
    )

    rules.to_excel(
        os.path.join(
            full_output,
            "fixed_signature_rules.xlsx",
        ),
        index=False,
    )

    pdp_overview_path = None
    if GENERATE_AUTOMATIC_SIGNATURE_FIGURES:
        pdp_overview_path = plot_full_data_pdp_summary_figure(
            full_output=full_output,
            full_raw=full_raw,
            thresholds=thresholds,
            grids_raw=grids_raw,
            boot_results=boot_results,
            yield_scale=yield_scale,
            yield_mean=yield_mean,
            model_info=model_info,
            shap_ranking=full_data_shap_ranking,
            selected_row=None,
            sti_candidates=full_sti_candidates,
        )
    figure_paths = None
    if MAKE_FULL_DATA_AUTOMATIC_FIGURE:
        figure_paths = _save_single_full_data_sta_figure(
            full_raw=full_raw,
            thresholds=thresholds,
            output_dir=full_output,
            mode_name="auto",
            sta_col="STa",
        )

    print(
        "\nFull-data run completed."
    )

    print(
        f"Full-data results saved in:\n{full_output}"
    )

    return {
        "Full_Output":
            full_output,
        "Full_Data":
            full_raw,
        "Class_Info":
            class_info,
        "Model_Info":
            model_info,
        "Thresholds":
            thresholds,
        "Rules":
            rules,
        "Figure_Paths":
            figure_paths,
        "PDP_Overview_Figure_Path":
            pdp_overview_path,
    }


# ============================================================
# FIND ALL AVAILABLE LOYO FOLD INPUTS
#
# all_fold_names is used only for LOYO execution.
# FULL_DATA is independent and comes from the standalone file pair.
# fold_names is the subset actually processed by LOYO.
# ============================================================

if os.path.isdir(STEP2_DIR):
    all_fold_names = sorted([
        name
        for name in os.listdir(STEP2_DIR)
        if (
            name.startswith("heldout_")
            and
            os.path.isdir(os.path.join(STEP2_DIR, name))
        )
    ])
else:
    all_fold_names = []

if RUN_LOYO and len(all_fold_names) == 0:
    raise ValueError(
        f"RUN_MODE includes LOYO but no heldout_* folders were found in:\n{STEP2_DIR}"
    )


# ============================================================
# AUTOMATIC FULL-DATA SIGNATURE DISCOVERY
# ============================================================
# This happens BEFORE the LOYO threshold loop so the same automatically
# discovered full-data signature can be used in every fold.
#
# IMPORTANT: this is a FIXED-SIGNATURE LOYO sensitivity/evaluation.
# Feature discovery itself uses the independent standalone full-data files.
# ============================================================

if AUTOMATIC_FEATURE_DISCOVERY and (RUN_LOYO or RUN_FULL_DATA):

    AUTO_SIGNATURE_RESULT = prepare_automatic_full_data_signature(
        step2_dir=STEP2_DIR,
        fold_names=all_fold_names,
        output_dir=OUTPUT_DIR,
    )

    FIXED_FEATURES = list(
        AUTO_SIGNATURE_RESULT["Selected_Features"]
    )

    EXPECTED_DIRECTIONS = {
        feature: list(directions)
        for feature, directions
        in AUTO_SIGNATURE_RESULT["Expected_Directions"].items()
    }

    DIRECTION_REQUIRES_OUTER_TAIL = {
        feature: bool(value)
        for feature, value
        in AUTO_SIGNATURE_RESULT.get("Direction_Requires_Outer_Tail", {}).items()
    }
    for feature in FIXED_FEATURES:
        DIRECTION_REQUIRES_OUTER_TAIL.setdefault(feature, True)

    print("\nAutomatic fixed signature loaded:")
    for feature in FIXED_FEATURES:
        print(
            f"  {feature:15s}  directions={EXPECTED_DIRECTIONS[feature]}  "
            f"outer_tail_required={DIRECTION_REQUIRES_OUTER_TAIL.get(feature, True)}"
        )


if RUN_LOYO:

    fold_names = list(
        all_fold_names
    )

    if RUN_ONLY_YEAR is not None:

        wanted = (
            f"heldout_{int(RUN_ONLY_YEAR)}"
        )

        if wanted not in fold_names:
            raise ValueError(
                f"{wanted} not found."
            )

        fold_names = [
            wanted
        ]

else:

    # Skip the LOYO loop. FULL_DATA no longer depends on all_fold_names.
    fold_names = []


print(
    "\nExecution mode:"
)

print(
    f"  RUN_MODE      = {RUN_MODE}"
)

print(
    f"  RUN_LOYO      = {RUN_LOYO}"
)

print(
    f"  RUN_FULL_DATA = {RUN_FULL_DATA}"
)

if RUN_LOYO:

    print(
        f"  LOYO folds to run = {len(fold_names)}"
    )

if RUN_FULL_DATA:

    print(f"  FULL_DATA input mode = {FULL_DATA_INPUT_MODE}")


master_threshold_rows = []
master_rule_rows = []
master_model_rows = []


for fold_name in fold_names:

    year = int(
        fold_name.replace("heldout_", "")
    )

    print("\n" + "=" * 90)
    print(
        f"AUTO-DISCOVERED FIXED-SIGNATURE F1 | Held-out year = {year}"
    )
    print("=" * 90)

    fold_input = os.path.join(
        STEP2_DIR,
        fold_name,
    )

    fold_output = os.path.join(
        OUTPUT_DIR,
        fold_name,
    )

    os.makedirs(
        fold_output,
        exist_ok=True,
    )

    final_rule_path = os.path.join(
        fold_output,
        "fixed_signature_rules.xlsx",
    )

    if (
        SKIP_COMPLETED
        and
        os.path.exists(final_rule_path)
    ):
        print("Already completed.")
        continue

    (
        train_std_path,
        train_raw_path,
        scaler_path,
    ) = locate_fold_files(
        fold_input
    )

    train_std_from_step2 = pd.read_excel(
        train_std_path
    )

    train_raw = pd.read_excel(
        train_raw_path
    )

    class_col = get_training_class_column(
        train_raw
    )

    missing_raw_features = [
        feature
        for feature in FIXED_FEATURES
        if feature not in train_raw.columns
    ]

    if missing_raw_features:
        raise ValueError(
            f"{year}: Step 2 raw training file is missing automatically "
            f"selected features: {missing_raw_features}. Step 1/2 must retain "
            "all candidate month-coded climate indicators."
        )

    # Re-standardize the automatically selected features + target INSIDE F1.
    # This keeps Step 1 and Step 2 unchanged even if their standardized file
    # was originally created for another fixed signature.
    f1_variables = [*FIXED_FEATURES, TARGET_COL]
    f1_scaler = StandardScaler()
    f1_z = f1_scaler.fit_transform(
        train_raw[f1_variables].astype(float)
    )

    train_std = train_raw[[YEAR_COL, class_col]].copy()

    for idx, variable in enumerate(f1_variables):
        train_std[variable] = f1_z[:, idx]

    scalers = {
        variable: {
            "mean": float(f1_scaler.mean_[idx]),
            "scale": float(f1_scaler.scale_[idx]),
        }
        for idx, variable in enumerate(f1_variables)
    }

    class_col = get_training_class_column(
        train_raw
    )

    missing_std = [
        f
        for f in FIXED_FEATURES
        if f not in train_std.columns
    ]

    missing_raw = [
        f
        for f in FIXED_FEATURES
        if f not in train_raw.columns
    ]

    if missing_std or missing_raw:
        raise ValueError(
            f"{year}: fixed features missing.\n"
            f"Standardized missing: {missing_std}\n"
            f"Raw missing: {missing_raw}"
        )

    if TARGET_COL not in train_std.columns:
        raise ValueError(
            f"{year}: {TARGET_COL} missing in standardized training."
        )

    if TARGET_COL not in train_raw.columns:
        raise ValueError(
            f"{year}: {TARGET_COL} missing in raw training."
        )

    normal_mask = (
        train_raw[class_col].astype(str)
        == "No"
    )

    if normal_mask.sum() == 0:
        raise ValueError(
            f"{year}: no Normal training years."
        )

    PV = float(
        train_raw.loc[
            normal_mask,
            TARGET_COL,
        ].mean()
    )

    shock_mask = (
        train_raw[
            class_col
        ]
        .astype(str)
        == "Sh"
    )

    if shock_mask.sum() == 0:
        raise ValueError(
            f"{year}: no Sh training years available for automatic PV rescue."
        )

    SH_YIELD_MEAN = float(
        train_raw.loc[
            shock_mask,
            TARGET_COL,
        ].mean()
    )

    X = (
        train_std[
            FIXED_FEATURES
        ]
        .astype(float)
        .copy()
    )

    y = (
        train_std[
            TARGET_COL
        ]
        .astype(float)
        .copy()
    )

    (
        tuned_rf,
        best_params,
        cv_score,
    ) = fit_tuned_rf(
        X,
        y,
    )

    yield_scale = float(
        scalers[TARGET_COL]["scale"]
    )

    yield_mean = float(
        scalers[TARGET_COL]["mean"]
    )

    oob = calculate_oob_metrics(
        tuned_rf,
        y,
        yield_scale,
    )

    model_info = {
        "Heldout_Year": year,
        "N_Fixed_Features": len(FIXED_FEATURES),
        "Fixed_Features": "; ".join(FIXED_FEATURES),
        "Feature_Discovery_Mode": "FULL_DATA_PARETO_UTOPIA_FIXED_ACROSS_FOLDS",
        "Best_Params": str(best_params),
        "Inner_CV_Best_Score": cv_score,

        # Fold-level ORIGINAL training PV (mean No yield).
        # A feature-specific rescued PV does not exist yet at this point.
        # Feature-specific PV_Used values are calculated later inside
        # the feature loop and saved in the threshold/candidate outputs.
        "Training_PV": PV,
        "Training_Sh_Yield_Mean": SH_YIELD_MEAN,

        # Negative OOB-R2 folds are retained in the PRIMARY LOYO
        # analysis.  They are flagged for later sensitivity analysis,
        # not removed here.
        "OOB_R2_Negative":
            bool(
                np.isfinite(oob["OOB_R2"])
                and oob["OOB_R2"] < 0
            ),

        "OOB_R2_Near_Zero_Negative":
            bool(
                np.isfinite(oob["OOB_R2"])
                and -float(OOB_R2_NEAR_ZERO_TOLERANCE)
                    <= oob["OOB_R2"] < 0
            ),

        "OOB_R2_Meaningfully_Negative":
            bool(
                np.isfinite(oob["OOB_R2"])
                and oob["OOB_R2"]
                    < -float(OOB_R2_NEAR_ZERO_TOLERANCE)
            ),

        "OOB_R2_Near_Zero_Tolerance":
            float(OOB_R2_NEAR_ZERO_TOLERANCE),

        "Model_Skill_Status":
            (
                "MEANINGFULLY_NEGATIVE_OOB_R2_RETAINED_FOLD"
                if (
                    np.isfinite(oob["OOB_R2"])
                    and oob["OOB_R2"]
                        < -float(OOB_R2_NEAR_ZERO_TOLERANCE)
                )
                else (
                    "NEAR_ZERO_NEGATIVE_OOB_R2_RETAINED"
                    if (
                        np.isfinite(oob["OOB_R2"])
                        and oob["OOB_R2"] < 0
                    )
                    else "NONNEGATIVE_OOB_R2"
                )
            ),

        **oob,
    }

    pd.DataFrame(
        [model_info]
    ).to_excel(
        os.path.join(
            fold_output,
            "fixed_signature_model_information.xlsx",
        ),
        index=False,
    )

    master_model_rows.append(
        model_info
    )

    grids_std = {}
    grids_raw = {}

    for feature in FIXED_FEATURES:
        grids_std[feature] = np.linspace(
            X[feature].min(),
            X[feature].max(),
            GRID_RESOLUTION,
        )

        grids_raw[feature] = inverse_scale(
            grids_std[feature],
            feature,
            scalers,
        )

    boot_results = Parallel(
        n_jobs=N_JOBS
    )(
        delayed(
            bootstrap_pdp_run
        )(
            RANDOM_STATE
            + year * 1000
            + b,
            X,
            y,
            grids_std,
            best_params,
        )
        for b in range(N_BOOTSTRAPS)
    )

    threshold_rows = []
    candidate_tables = []
    sti_candidate_tables = []

    for feature in FIXED_FEATURES:

        curves_std = np.vstack([
            result[feature]
            for result in boot_results
        ])

        curves_raw = (
            curves_std
            * yield_scale
            + yield_mean
        )

        mean_curve = curves_raw.mean(
            axis=0
        )

        x_raw = grids_raw[feature]

        # ----------------------------------------------------
        # Training-only feature-specific PV rescue.
        #
        # Held-out year is never used here.
        # ----------------------------------------------------

        pv_info = resolve_feature_pv_for_crossing(
            x_raw=
                x_raw,
            mean_curve=
                mean_curve,
            original_pv=
                PV,
            sh_yield_mean=
                SH_YIELD_MEAN,
        )

        PV_FEATURE = float(
            pv_info[
                "PV_Used"
            ]
        )

        for direction in EXPECTED_DIRECTIONS[
            feature
        ]:

            pdp_min = float(
                np.nanmin(mean_curve)
            )
            pdp_max = float(
                np.nanmax(mean_curve)
            )

            original_pv_within_pdp_range = bool(
                pdp_min <= PV <= pdp_max
            )

            pv_within_pdp_range = bool(
                pdp_min <= PV_FEATURE <= pdp_max
            )

            (
                selected_threshold,
                sti_candidate_df,
                sta_candidate_detail_df,
            ) = derive_best_multi_crossing_threshold(
                training_raw=train_raw,
                class_col=class_col,
                feature=feature,
                direction=direction,
                x_raw=x_raw,
                mean_curve=mean_curve,
                curves_raw=curves_raw,
                pv=PV_FEATURE,
                require_outer_tail=DIRECTION_REQUIRES_OUTER_TAIL.get(feature, True),
            )

            if selected_threshold is None:
                crossing_status = (
                    "NO_VALID_CROSSING_WITHIN_ALLOWED_PV_SHIFT"
                    if (
                        not bool(
                            pv_info[
                                "PV_Used_Has_Crossing"
                            ]
                        )
                    )
                    else (
                        "NO_MEAN_PDP_CROSSING_AFTER_PV_RESOLUTION"
                    )
                )

                threshold_rows.append({
                    "Heldout_Year": year,
                    "Feature": feature,
                    "Direction": direction,
                    "Status": "NO_PDP_CROSSING",
                    "Crossing_Status": crossing_status,
                    "PDP_Min": pdp_min,
                    "PDP_Max": pdp_max,
                    "Original_PV_Within_PDP_Range": original_pv_within_pdp_range,
                    "PV_Within_PDP_Range": pv_within_pdp_range,
                    "Original_PV": pv_info["Original_PV"],
                    "Sh_Yield_Mean": pv_info["Sh_Yield_Mean"],
                    "PV_Used": pv_info["PV_Used"],
                    "PV_Adjusted": pv_info["PV_Adjusted"],
                    "PV_Adjustment_Alpha": pv_info["PV_Adjustment_Alpha"],
                    "PV_Adjustment_Signed": pv_info["PV_Adjustment_Signed"],
                    "PV_Adjustment_Absolute": pv_info["PV_Adjustment_Absolute"],
                    "PV_Adjustment_Status": pv_info["PV_Adjustment_Status"],
                    "Original_PV_Has_Crossing": pv_info["Original_PV_Has_Crossing"],
                    "PV_Used_Has_Crossing": pv_info["PV_Used_Has_Crossing"],
                    "N_Mean_PDP_Crossings": 0,
                    "All_Mean_PDP_Crossings": "",
                    "Selected_STi_Candidate_Index": np.nan,
                    "STi": np.nan,
                    "CI_Lower": np.nan,
                    "CI_Upper": np.nan,
                    "Bootstrap_N_Valid": 0,
                    "Bootstrap_Support": 0.0,
                    "STa": np.nan,
                    "STa_Selection": "UNAVAILABLE_NO_PDP_CROSSING",
                    "Training_PV": PV_FEATURE,
                })
                continue

            if not sti_candidate_df.empty:
                tmp_sti = sti_candidate_df.copy()
                tmp_sti.insert(0, "Heldout_Year", year)
                tmp_sti["Original_PV"] = pv_info["Original_PV"]
                tmp_sti["Sh_Yield_Mean"] = pv_info["Sh_Yield_Mean"]
                tmp_sti["PV_Used"] = pv_info["PV_Used"]
                tmp_sti["PV_Adjusted"] = pv_info["PV_Adjusted"]
                tmp_sti["PV_Adjustment_Alpha"] = pv_info["PV_Adjustment_Alpha"]
                tmp_sti["PV_Adjustment_Status"] = pv_info["PV_Adjustment_Status"]
                sti_candidate_tables.append(tmp_sti)

            if not sta_candidate_detail_df.empty:
                tmp_sta = sta_candidate_detail_df.copy()
                tmp_sta.insert(0, "Heldout_Year", year)
                tmp_sta.insert(1, "Feature", feature)
                tmp_sta.insert(2, "Direction", direction)
                tmp_sta["Original_PV"] = pv_info["Original_PV"]
                tmp_sta["Sh_Yield_Mean"] = pv_info["Sh_Yield_Mean"]
                tmp_sta["PV_Used"] = pv_info["PV_Used"]
                tmp_sta["PV_Adjusted"] = pv_info["PV_Adjusted"]
                tmp_sta["PV_Adjustment_Alpha"] = pv_info["PV_Adjustment_Alpha"]
                tmp_sta["PV_Adjustment_Status"] = pv_info["PV_Adjustment_Status"]
                candidate_tables.append(tmp_sta)

            threshold_rows.append({
                "Heldout_Year": year,
                "Feature": feature,
                "Direction": direction,
                "Status": "VALID",
                "Crossing_Status": (
                    "VALID_MULTI_CROSSING_SELECTION_ADJUSTED_PV"
                    if pv_info["PV_Adjusted"]
                    else "VALID_MULTI_CROSSING_SELECTION_ORIGINAL_PV"
                ),
                "PDP_Min": pdp_min,
                "PDP_Max": pdp_max,
                "Original_PV_Within_PDP_Range": original_pv_within_pdp_range,
                "PV_Within_PDP_Range": pv_within_pdp_range,
                "Original_PV": pv_info["Original_PV"],
                "Sh_Yield_Mean": pv_info["Sh_Yield_Mean"],
                "PV_Used": pv_info["PV_Used"],
                "PV_Adjusted": pv_info["PV_Adjusted"],
                "PV_Adjustment_Alpha": pv_info["PV_Adjustment_Alpha"],
                "PV_Adjustment_Signed": pv_info["PV_Adjustment_Signed"],
                "PV_Adjustment_Absolute": pv_info["PV_Adjustment_Absolute"],
                "PV_Adjustment_Status": pv_info["PV_Adjustment_Status"],
                "Original_PV_Has_Crossing": pv_info["Original_PV_Has_Crossing"],
                "PV_Used_Has_Crossing": pv_info["PV_Used_Has_Crossing"],
                "N_Mean_PDP_Crossings": int(selected_threshold["N_Mean_PDP_Crossings"]),
                "All_Mean_PDP_Crossings": selected_threshold["All_Mean_PDP_Crossings"],
                "Selected_STi_Candidate_Index": int(selected_threshold["STi_Candidate_Index"]),
                "STi": float(selected_threshold["STi_Candidate"]),
                "CI_Lower": float(selected_threshold["CI_Lower"]),
                "CI_Upper": float(selected_threshold["CI_Upper"]),
                "Bootstrap_N_Valid": int(selected_threshold["Bootstrap_N_Valid"]),
                "Bootstrap_Support": float(selected_threshold["Bootstrap_Support"]),
                "STi_Sh_Hit": selected_threshold["STi_Sh_Hit"],
                "STi_No_Hit": selected_threshold["STi_No_Hit"],
                "STi_Bo_Hit": selected_threshold["STi_Bo_Hit"],
                "STi_Separation_Score": selected_threshold["STi_Separation_Score"],
                "STa": float(selected_threshold["Auto_STa_Candidate"]),
                "STa_Selection": selected_threshold["Auto_STa_Selection"],
                "Auto_STa_Sh_Hit": selected_threshold["Auto_STa_Sh_Hit"],
                "Auto_STa_No_Hit": selected_threshold["Auto_STa_No_Hit"],
                "Auto_STa_Bo_Hit": selected_threshold["Auto_STa_Bo_Hit"],
                "Auto_STa_Separation_Score": selected_threshold["Auto_STa_Separation_Score"],
                "Auto_STa_Final_Linear_4_2_3_Score": selected_threshold.get(
                    "Auto_STa_Final_Linear_4_2_3_Score",
                    np.nan,
                ),
                "Auto_STa_ShNo_Separation": selected_threshold["Auto_STa_ShNo_Separation"],
                "Auto_STa_Distance_to_Sh_Median": selected_threshold["Auto_STa_Distance_to_Sh_Median"],
                "Auto_STa_Distance_to_Bo_Median": selected_threshold["Auto_STa_Distance_to_Bo_Median"],
                "Auto_STa_Local_Utopia_Distance": selected_threshold["Auto_STa_Local_Utopia_Distance"],
                "STi_Selection_Utopia_Distance": selected_threshold["STi_Selection_Utopia_Distance"],
                "STi_Selection_Method": selected_threshold.get(
                    "STi_Selection_Method",
                    "PARETO_FINAL_STa_LINEAR_4_2_3",
                ),
                "STi_Pareto_Efficient_Final_STa": selected_threshold.get(
                    "STi_Pareto_Efficient_Final_STa",
                    np.nan,
                ),
                "Sh_Median": selected_threshold["Sh_Median"],
                "Bo_Median": selected_threshold["Bo_Median"],
                "Training_PV": PV_FEATURE,
            })

    thresholds = pd.DataFrame(
        threshold_rows
    )

    thresholds.to_excel(
        os.path.join(
            fold_output,
            "fixed_signature_thresholds_long.xlsx",
        ),
        index=False,
    )

    if candidate_tables:
        pd.concat(
            candidate_tables,
            ignore_index=True,
        ).to_excel(
            os.path.join(
                fold_output,
                "fixed_signature_STa_candidates.xlsx",
            ),
            index=False,
        )

    if sti_candidate_tables:
        pd.concat(
            sti_candidate_tables,
            ignore_index=True,
        ).to_excel(
            os.path.join(
                fold_output,
                "fixed_signature_STi_candidates.xlsx",
            ),
            index=False,
        )

    rule_rows = []

    for feature in FIXED_FEATURES:

        part = thresholds[
            thresholds["Feature"]
            == feature
        ].copy()

        expected_dirs = EXPECTED_DIRECTIONS[
            feature
        ]

        lower_row = part[
            part["Direction"]
            == "lower"
        ]

        upper_row = part[
            part["Direction"]
            == "upper"
        ]

        def get_num(df, column):
            if df.empty:
                return np.nan
            value = df.iloc[0][column]
            return (
                float(value)
                if pd.notna(value)
                else np.nan
            )

        lower_sti = get_num(
            lower_row,
            "STi",
        )

        upper_sti = get_num(
            upper_row,
            "STi",
        )

        lower_sta = get_num(
            lower_row,
            "STa",
        )

        upper_sta = get_num(
            upper_row,
            "STa",
        )

        # Reject invalid overlapping two-sided pairs.
        if (
            np.isfinite(lower_sti)
            and
            np.isfinite(upper_sti)
            and
            lower_sti >= upper_sti
        ):
            lower_sti = np.nan
            upper_sti = np.nan

        if (
            np.isfinite(lower_sta)
            and
            np.isfinite(upper_sta)
            and
            lower_sta >= upper_sta
        ):
            if (
                np.isfinite(lower_sti)
                and
                np.isfinite(upper_sti)
                and
                lower_sti < upper_sti
            ):
                lower_sta = lower_sti
                upper_sta = upper_sti
                sta_pair_status = (
                    "AUTO_STa_OVERLAP_FALLBACK_TO_STi"
                )
            else:
                lower_sta = np.nan
                upper_sta = np.nan
                sta_pair_status = (
                    "INVALID_TWO_SIDED_RULE"
                )
        else:
            sta_pair_status = "VALID"

        sti_available_sides = int(
            np.isfinite(lower_sti)
        ) + int(
            np.isfinite(upper_sti)
        )

        sta_available_sides = int(
            np.isfinite(lower_sta)
        ) + int(
            np.isfinite(upper_sta)
        )

        expected_side_count = len(
            expected_dirs
        )

        def completeness(
            n_available,
            n_expected,
        ):
            if n_available == 0:
                return "UNAVAILABLE"
            if n_available < n_expected:
                return "PARTIAL"
            return "FULL"

        rule_row = {
            "Heldout_Year": year,
            "Feature": feature,
            "Expected_Directions":
                "+".join(expected_dirs),
            "Expected_Side_Count":
                expected_side_count,

            "Lower_STi": lower_sti,
            "Upper_STi": upper_sti,
            "STi_Available_Sides":
                sti_available_sides,
            "STi_Feature_Available":
                sti_available_sides >= 1,
            "STi_Completeness":
                completeness(
                    sti_available_sides,
                    expected_side_count,
                ),

            "Lower_Auto_STa": lower_sta,
            "Upper_Auto_STa": upper_sta,
            "STa_Available_Sides":
                sta_available_sides,
            "STa_Feature_Available":
                sta_available_sides >= 1,
            "STa_Completeness":
                completeness(
                    sta_available_sides,
                    expected_side_count,
                ),
            "STa_Pair_Status":
                sta_pair_status,

        }

        rule_rows.append(
            rule_row
        )

        master_rule_rows.append(
            rule_row
        )

    rules = pd.DataFrame(
        rule_rows
    )

    rules.to_excel(
        final_rule_path,
        index=False,
    )

    master_threshold_rows.extend(
        threshold_rows
    )

    print(f"Saved fold {year}.")


if master_model_rows:
    pd.DataFrame(
        master_model_rows
    ).to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_model_information_all_folds.xlsx",
        ),
        index=False,
    )


if master_threshold_rows:

    all_thresholds = pd.DataFrame(
        master_threshold_rows
    )

    all_thresholds.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_thresholds_all_folds.xlsx",
        ),
        index=False,
    )

    valid_thresholds = all_thresholds[
        all_thresholds["Status"] == "VALID"
    ].copy()

    if not valid_thresholds.empty:
        summary = (
            valid_thresholds
            .groupby(["Feature", "Direction"])
            .agg(
                N_Available_Folds=("Heldout_Year", "nunique"),
                Median_STi=("STi", "median"),
                Q1_STi=("STi", lambda x: x.quantile(0.25)),
                Q3_STi=("STi", lambda x: x.quantile(0.75)),
                Median_Auto_STa=("STa", "median"),
                Q1_Auto_STa=("STa", lambda x: x.quantile(0.25)),
                Q3_Auto_STa=("STa", lambda x: x.quantile(0.75)),
                Median_Bootstrap_Support=("Bootstrap_Support", "median"),
            )
            .reset_index()
        )

        summary.to_excel(
            os.path.join(
                OUTPUT_DIR,
                "fixed_signature_threshold_stability.xlsx",
            ),
            index=False,
        )


if master_rule_rows:

    all_rules = pd.DataFrame(
        master_rule_rows
    )

    all_rules.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_rules_all_folds.xlsx",
        ),
        index=False,
    )

    n_folds = all_rules[
        "Heldout_Year"
    ].nunique()

    availability = (
        all_rules
        .groupby(
            "Feature"
        )
        .agg(
            STi_Available_Folds=(
                "STi_Feature_Available",
                "sum",
            ),
            STa_Available_Folds=(
                "STa_Feature_Available",
                "sum",
            ),
            STi_Full_Folds=(
                "STi_Completeness",
                lambda x:
                    int(
                        (
                            x == "FULL"
                        ).sum()
                    ),
            ),
            STi_Partial_Folds=(
                "STi_Completeness",
                lambda x:
                    int(
                        (
                            x == "PARTIAL"
                        ).sum()
                    ),
            ),
            STa_Full_Folds=(
                "STa_Completeness",
                lambda x:
                    int(
                        (
                            x == "FULL"
                        ).sum()
                    ),
            ),
            STa_Partial_Folds=(
                "STa_Completeness",
                lambda x:
                    int(
                        (
                            x == "PARTIAL"
                        ).sum()
                    ),
            ),
        )
        .reset_index()
    )

    availability[
        "N_Folds"
    ] = n_folds

    availability[
        "STi_Availability_Frequency"
    ] = (
        availability[
            "STi_Available_Folds"
        ]
        / n_folds
    )

    availability[
        "STa_Availability_Frequency"
    ] = (
        availability[
            "STa_Available_Folds"
        ]
        / n_folds
    )

    availability.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_feature_availability_summary.xlsx",
        ),
        index=False,
    )



# ============================================================
# AFTER ALL LOYO FOLDS: RUN ON THE COMPLETE FULL DATA
# ============================================================

FULL_DATA_RESULT = None

if RUN_FULL_DATA:

    print("\nFULL_DATA signature mode: AUTOMATIC FIXED SIGNATURE")
    print(f"  N features = {len(FIXED_FEATURES)}")
    for _feature in FIXED_FEATURES:
        print(
            f"  {_feature:15s} directions={EXPECTED_DIRECTIONS[_feature]}"
        )

    FULL_DATA_RESULT = run_full_data_fixed_signature(
        step2_dir=STEP2_DIR,
        fold_names=all_fold_names,
        output_dir=OUTPUT_DIR,
    )


print("\n" + "=" * 90)
print(
    f"{REGION_NAME} FIXED-SIGNATURE THRESHOLD DERIVATION COMPLETE"
)
print("=" * 90)

print(
    f"\nExecution mode: {RUN_MODE}"
)

if RUN_LOYO:
    print(
        f"\nLOYO results saved in:\n{OUTPUT_DIR}"
    )

if FULL_DATA_RESULT is not None:
    print(
        f"\nFull-data results saved in:\n"
        f"{FULL_DATA_RESULT['Full_Output']}"
    )
