# -*- coding: utf-8 -*-
"""Central user configuration for Automatic Stress Threshold and Type Detection.

For a new dataset, normally edit only:
    1) CASE_NAME
    2) RUN_MODE
    3) DATA_FILE (optional; leave blank to use the default data/ workbook)

No user-supplied feature/STa rule list is required. Feature identities, stress
directions, and STi/STa thresholds are discovered automatically from the supplied data.
"""

from pathlib import Path
import re

# ============================================================
# USER SETTINGS
# ============================================================

# A short label used only for output folders and figure titles.
# Examples: "ALB_Potato", "FIN_Potato", "My_New_Case"
CASE_NAME = "ALB_Potato"

# Choose one execution mode:
#   "FULL_DATA" -> automatic full-series feature/threshold derivation + diagnostic
#   "LOYO"      ->  leave-one-year-out threshold robustness only
#   "BOTH"      -> run both FULL_DATA and LOYO analyses
RUN_MODE = "FULL_DATA"

# Optional exact path to the input workbook.
#
# Leave this blank to use:
#     <package>/data/combined_nonstandardized_data.xlsx
#
# Examples of explicit paths:
#   DATA_FILE = r"data/ARM_Potato_combined_nonstandardized_data.xlsx"
#   DATA_FILE = r"C:\\MyProject\\ARM_Potato_combined_nonstandardized_data.xlsx"
#
# Relative paths are interpreted relative to this package directory.
DATA_FILE = r""

# ============================================================
# INPUT FORMAT / COMMON SETTINGS
# ============================================================

YEAR_COL = "Year"
YIELD_COL = "Detrended_Yield"

# Baseline yield-class definition used by LOYO Step 1.
LOWER_PERCENTILE = 0.10
UPPER_PERCENTILE = 0.90

# Minimum number of evaluable feature votes required for a LOYO fold to be
# reported. The strict-majority denominator remains the fixed automatic
# signature and is NOT reduced by unavailable fold-specific thresholds.
MIN_VALID_FEATURES = 2

# ============================================================
# PATHS - NORMALLY DO NOT EDIT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

# Make CASE_NAME filesystem-friendly while preserving a readable label.
CASE_ID = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(CASE_NAME).strip()).strip("_")
if not CASE_ID:
    raise ValueError("CASE_NAME must contain at least one letter or number.")

REGION_NAME = str(CASE_NAME)

if str(DATA_FILE).strip():
    _data_path = Path(str(DATA_FILE).strip()).expanduser()
    if not _data_path.is_absolute():
        _data_path = PROJECT_ROOT / _data_path
    MASTER_FILE = _data_path.resolve()
else:
    MASTER_FILE = (DATA_DIR / "combined_nonstandardized_data.xlsx").resolve()

CASE_DIR = RESULTS_DIR / CASE_ID
BASE_PARENT = RESULTS_DIR
COUNTRY_FOLDER = CASE_ID

# Validate execution mode early so users get a clear error.
RUN_MODE = str(RUN_MODE).strip().upper()
VALID_RUN_MODES = {"FULL_DATA", "LOYO", "BOTH"}
if RUN_MODE not in VALID_RUN_MODES:
    raise ValueError(
        f"Invalid RUN_MODE={RUN_MODE!r}. "
        "Use 'FULL_DATA', 'LOYO', or 'BOTH'."
    )
