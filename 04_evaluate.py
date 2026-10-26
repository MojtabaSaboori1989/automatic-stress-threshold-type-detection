# ============================================================
# GENERIC FIXED-SIGNATURE LOYO
# STEP F2 - FIXED-SIGNATURE-DENOMINATOR EVALUATION
#
# Missing crossing / incomplete two-sided rule:
#   use THREE-STATE logic for a PARTIAL two-sided feature:
#     - available side is hit      -> stress vote = 1
#     - available side is not hit  -> UNKNOWN / NA
#   Fully unavailable features are also NA.
#
# IMPORTANT:
#   NA does NOT reduce the majority denominator.
#
# Fixed-signature voting rule:
#   Sh only when MORE THAN HALF of the AUTOMATIC fixed-signature features indicate stress.
#
# Therefore:
#   ORIGINAL_K = number of features in F1's automatic fixed signature
#   REQUIRED_HITS = floor(ORIGINAL_K / 2) + 1
#
# MIN_VALID_FEATURES controls whether a fold has enough actually
# evaluable feature votes to be reported at all. It does NOT change
# REQUIRED_HITS.
#
# Any two-sided feature remains ONE feature vote.
# For a PARTIAL two-sided feature, a hit on the available side is
# accepted as one stress vote; otherwise the feature is UNKNOWN.
#
# Methods:
#   1) fold-specific STi
#   2) fold-specific automated STa
#   3) full-data automated STa diagnostic (NOT independent)
# ============================================================

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1 import make_axes_locatable

from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)

# ============================================================
# BUL2 TEST CONFIGURATION
# Voting rule: STRICT MAJORITY (>50% of AUTOMATIC fixed signature)
# TFY: true-Sh years with exactly 50% of original-signature votes
# ============================================================

# ============================================================
# USER SETTINGS / AUTOMATIC SIGNATURE
# ============================================================
# Case paths and RUN_MODE come from config.py.  F2 never accepts a user-supplied
# feature/STa rule list.  The fixed feature identities and expected directions
# are read directly from F1's automatic_full_data_signature.xlsx.

from config import (
    CASE_DIR,
    REGION_NAME,
    RUN_MODE,
    MIN_VALID_FEATURES,
)

BASE = str(CASE_DIR)
RUN_MODE = str(RUN_MODE).strip().upper()
RUN_LOYO = RUN_MODE in {"LOYO", "BOTH"}
RUN_FULL_DATA = RUN_MODE in {"FULL_DATA", "BOTH"}
RUN_FULL_DATA_AUTO_DIAGNOSTIC = RUN_FULL_DATA

# ============================================================
# PATHS
# ============================================================

STEP2_DIR = os.path.join(
    BASE,
    "02_standardization"
)

THRESHOLD_DIR = os.path.join(
    BASE,
    "03_thresholds_and_signature"
)

OUTPUT_DIR = os.path.join(
    BASE,
    "04_stress_types_and_evaluation"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

# F1 stores its one-time full-data analysis here:
FULL_DATA_THRESHOLD_DIR = os.path.join(
    THRESHOLD_DIR,
    "full_data",
)

FULL_DATA_RULE_FILE = os.path.join(
    FULL_DATA_THRESHOLD_DIR,
    "fixed_signature_rules.xlsx",
)

FULL_DATA_RAW_FILE = os.path.join(
    FULL_DATA_THRESHOLD_DIR,
    "full_data_nonstandardized_with_classes.xlsx",
)

AUTOMATIC_SIGNATURE_FILE = os.path.join(
    THRESHOLD_DIR,
    "automatic_signature_discovery",
    "automatic_full_data_signature.xlsx",
)

if not os.path.exists(AUTOMATIC_SIGNATURE_FILE):
    raise FileNotFoundError(
        "F1 automatic signature file not found:\n"
        f"{AUTOMATIC_SIGNATURE_FILE}\n"
        "Run F1/03_threshold_derivation.py first."
    )

_auto_signature = pd.read_excel(AUTOMATIC_SIGNATURE_FILE)

_required_signature_cols = {"Feature", "Directions"}
_missing_signature_cols = _required_signature_cols - set(_auto_signature.columns)
if _missing_signature_cols:
    raise ValueError(
        "Automatic signature file is missing required columns: "
        f"{sorted(_missing_signature_cols)}"
    )

# Preserve F1-selected feature order (one row per selected feature).
FIXED_FEATURES = []
EXPECTED_DIRECTIONS = {}
for _, _sigrow in _auto_signature.iterrows():
    _feature = str(_sigrow["Feature"]).strip()
    if not _feature or _feature.lower() == "nan":
        continue
    if _feature not in FIXED_FEATURES:
        FIXED_FEATURES.append(_feature)
    _dirs = [
        d.strip().lower()
        for d in str(_sigrow["Directions"]).split(";")
        if d.strip().lower() in {"lower", "upper"}
    ]
    EXPECTED_DIRECTIONS[_feature] = _dirs

if not FIXED_FEATURES:
    raise ValueError("F1 automatic signature contains no selected features.")

EXPECTED_SIDE_COUNT = {
    feature: len(EXPECTED_DIRECTIONS.get(feature, []))
    for feature in FIXED_FEATURES
}

ORIGINAL_SIGNATURE_K = len(FIXED_FEATURES)
ORIGINAL_REQUIRED_HITS = (ORIGINAL_SIGNATURE_K // 2) + 1

print("\nAutomatic fixed signature loaded from F1:")
for feature in FIXED_FEATURES:
    print(
        f"  {feature}: "
        + " + ".join(EXPECTED_DIRECTIONS.get(feature, []))
    )
print(f"\nAutomatic signature k = {ORIGINAL_SIGNATURE_K}")
print(f"Fixed required hits (>50%) = {ORIGINAL_REQUIRED_HITS}")

TITLE_FS = 8.5
AXIS_FS = 7.5
CLASS_FS = 7.0
NUMBER_FS = 6.0
META_FS = 6.0
CBAR_FS = 5.0


def find_excel_file(
    folder,
    preferred_names,
    required_tokens=None,
):
    for name in preferred_names:
        path = os.path.join(
            folder,
            name,
        )
        if os.path.exists(path):
            return path

    if required_tokens is not None:
        candidates = []
        for name in os.listdir(folder):
            low = name.lower()
            if not low.endswith(".xlsx"):
                continue
            if all(
                token.lower() in low
                for token in required_tokens
            ):
                candidates.append(
                    os.path.join(
                        folder,
                        name,
                    )
                )

        if candidates:
            return sorted(candidates)[0]

    raise FileNotFoundError(
        f"Could not locate file in:\n{folder}"
    )


def locate_heldout_raw(
    fold_dir,
):
    try:
        return find_excel_file(
            fold_dir,
            [
                "heldout_nonstandardized.xlsx",
                "heldout_nonstandardized_UPDATED.xlsx",
                "heldout_raw.xlsx",
            ],
            required_tokens=[
                "heldout",
                "nonstandardized",
            ],
        )
    except FileNotFoundError:
        return find_excel_file(
            fold_dir,
            [
                "heldout_nonstandardized.xlsx",
                "heldout_nonstandardized_UPDATED.xlsx",
                "heldout_raw.xlsx",
            ],
            required_tokens=[
                "heldout",
                "raw",
            ],
        )


def get_true_class(
    row,
    columns,
):
    if "True_Class_Binary" in columns:
        value = row[
            "True_Class_Binary"
        ]

        if str(value) in [
            "Sh",
            "NSh",
        ]:
            return str(value)

        try:
            return (
                "Sh"
                if int(value) == 1
                else "NSh"
            )
        except Exception:
            pass

    if "True_Class_3" in columns:
        return (
            "Sh"
            if str(
                row[
                    "True_Class_3"
                ]
            ) == "Sh"
            else "NSh"
        )

    if "Yield_Class" in columns:
        return (
            "Sh"
            if str(
                row[
                    "Yield_Class"
                ]
            ) == "Sh"
            else "NSh"
        )

    raise ValueError(
        "Could not determine held-out true class."
    )


def feature_hit(
    value,
    lower,
    upper,
):
    lower_hit = (
        pd.notna(lower)
        and
        value <= float(lower)
    )

    upper_hit = (
        pd.notna(upper)
        and
        value >= float(upper)
    )

    return int(
        lower_hit
        or
        upper_hit
    )


def evaluate_fold_feature_vote(
    value,
    rule_row,
    method_prefix,
    feature,
):
    """
    Three-state fold-specific feature voting.

    FULL rule:
        all sides expected from the original signature are available.
        -> ordinary binary vote: 1 = stress, 0 = non-stress.

    PARTIAL two-sided rule:
        only one of the two originally expected sides is available.
        -> if the observed held-out value hits the available side:
               vote = 1 and the feature is valid.
        -> otherwise:
               vote = NA / UNKNOWN and the feature is NOT included
               in valid_k, because the missing opposite side could
               still have produced a stress hit.

    UNAVAILABLE rule:
        no expected side is available.
        -> vote = NA / UNKNOWN.

    The held-out TRUE CLASS is never used here.
    """

    expected_lower = (
        "lower" in EXPECTED_DIRECTIONS.get(feature, [])
    )

    expected_upper = (
        "upper" in EXPECTED_DIRECTIONS.get(feature, [])
    )

    expected_count = (
        int(
            expected_lower
        )
        +
        int(
            expected_upper
        )
    )

    if rule_row is None:
        return {
            "Hit":
                np.nan,
            "Is_Valid":
                False,
            "Completeness":
                "UNAVAILABLE",
            "Vote_Status":
                "NO_RULE_ROW",
            "Lower":
                np.nan,
            "Upper":
                np.nan,
            "Expected_Side_Count":
                expected_count,
            "Available_Side_Count":
                0,
        }

    if method_prefix == "STi":
        lower = rule_row.get(
            "Lower_STi",
            np.nan,
        )
        upper = rule_row.get(
            "Upper_STi",
            np.nan,
        )
    elif method_prefix == "STa":
        lower = rule_row.get(
            "Lower_Auto_STa",
            np.nan,
        )
        upper = rule_row.get(
            "Upper_Auto_STa",
            np.nan,
        )
    else:
        raise ValueError(
            method_prefix
        )

    # Ignore a side that was not part of the original fixed signature.
    lower_available = bool(
        expected_lower
        and
        pd.notna(
            lower
        )
    )

    upper_available = bool(
        expected_upper
        and
        pd.notna(
            upper
        )
    )

    available_count = (
        int(
            lower_available
        )
        +
        int(
            upper_available
        )
    )

    lower_for_vote = (
        float(
            lower
        )
        if lower_available
        else np.nan
    )

    upper_for_vote = (
        float(
            upper
        )
        if upper_available
        else np.nan
    )

    if available_count == 0:
        return {
            "Hit":
                np.nan,
            "Is_Valid":
                False,
            "Completeness":
                "UNAVAILABLE",
            "Vote_Status":
                "NO_EXPECTED_SIDE_AVAILABLE",
            "Lower":
                lower_for_vote,
            "Upper":
                upper_for_vote,
            "Expected_Side_Count":
                expected_count,
            "Available_Side_Count":
                available_count,
        }

    if available_count == expected_count:
        hit = feature_hit(
            value,
            lower_for_vote,
            upper_for_vote,
        )

        return {
            "Hit":
                int(
                    hit
                ),
            "Is_Valid":
                True,
            "Completeness":
                "FULL",
            "Vote_Status":
                (
                    "FULL_STRESS_HIT"
                    if hit == 1
                    else "FULL_NONSTRESS"
                ),
            "Lower":
                lower_for_vote,
            "Upper":
                upper_for_vote,
            "Expected_Side_Count":
                expected_count,
            "Available_Side_Count":
                available_count,
        }

    # --------------------------------------------------------
    # PARTIAL rule.
    #
    # This should normally occur only for an originally
    # two-sided feature.  A hit on the available side is
    # definitive stress.  A non-hit is UNKNOWN because the
    # missing opposite side cannot be checked.
    # --------------------------------------------------------
    available_side_hit = bool(
        (
            lower_available
            and
            value <= lower_for_vote
        )
        or
        (
            upper_available
            and
            value >= upper_for_vote
        )
    )

    if available_side_hit:
        return {
            "Hit":
                1,
            "Is_Valid":
                True,
            "Completeness":
                "PARTIAL",
            "Vote_Status":
                "PARTIAL_AVAILABLE_SIDE_STRESS_HIT",
            "Lower":
                lower_for_vote,
            "Upper":
                upper_for_vote,
            "Expected_Side_Count":
                expected_count,
            "Available_Side_Count":
                available_count,
        }

    return {
        "Hit":
            np.nan,
        "Is_Valid":
            False,
        "Completeness":
            "PARTIAL",
        "Vote_Status":
            "PARTIAL_OTHER_SIDE_UNKNOWN",
        "Lower":
            lower_for_vote,
        "Upper":
            upper_for_vote,
        "Expected_Side_Count":
            expected_count,
        "Available_Side_Count":
            available_count,
    }


def read_fold_oob_r2(
    fold_name,
):
    """
    Read OOB-R2 from F1.  Negative-R2 folds remain part of the primary
    analysis; this value is used only for diagnostics/sensitivity.
    """

    model_path = os.path.join(
        THRESHOLD_DIR,
        fold_name,
        "fixed_signature_model_information.xlsx",
    )

    if not os.path.exists(
        model_path
    ):
        return np.nan

    model_df = pd.read_excel(
        model_path
    )

    if (
        model_df.empty
        or
        "OOB_R2"
        not in model_df.columns
    ):
        return np.nan

    value = model_df.iloc[
        0
    ][
        "OOB_R2"
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


def calculate_metrics(
    df,
    prediction_col,
    exact_half_col,
    method_name,
    independence_status,
):
    mapping = {
        "NSh": 0,
        "Sh": 1,
    }

    valid = df[
        df[
            prediction_col
        ].isin(
            [
                "NSh",
                "Sh",
            ]
        )
    ].copy()

    if valid.empty:
        raise ValueError(
            f"No evaluable folds for {method_name}."
        )

    y_true = (
        valid[
            "True_Class"
        ]
        .map(mapping)
        .to_numpy()
    )

    y_pred = (
        valid[
            prediction_col
        ]
        .map(mapping)
        .to_numpy()
    )

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[
            0,
            1,
        ],
    )

    TN, FP, FN, TP = (
        cm.ravel()
    )

    specificity = (
        TN / (TN + FP)
        if (TN + FP) > 0
        else np.nan
    )

    n_total = len(
        df
    )

    n_total_sh = int(
        (
            df[
                "True_Class"
            ]
            == "Sh"
        ).sum()
    )

    n_total_nsh = int(
        (
            df[
                "True_Class"
            ]
            == "NSh"
        ).sum()
    )

    n_eval_sh = int(
        (
            valid[
                "True_Class"
            ]
            == "Sh"
        ).sum()
    )

    n_eval_nsh = int(
        (
            valid[
                "True_Class"
            ]
            == "NSh"
        ).sum()
    )

    return {
        "Method":
            method_name,

        "Independence_Status":
            independence_status,

        "Original_Signature_k":
            ORIGINAL_SIGNATURE_K,

        "Fixed_Required_Hits":
            ORIGINAL_REQUIRED_HITS,

        "N_Total_Folds":
            n_total,

        "N_Evaluated":
            len(valid),

        "Coverage":
            len(valid)
            / n_total,

        "N_Total_Sh":
            n_total_sh,

        "N_Evaluated_Sh":
            n_eval_sh,

        "Sh_Coverage":
            (
                n_eval_sh
                / n_total_sh
                if n_total_sh > 0
                else np.nan
            ),

        "N_Total_NSh":
            n_total_nsh,

        "N_Evaluated_NSh":
            n_eval_nsh,

        "NSh_Coverage":
            (
                n_eval_nsh
                / n_total_nsh
                if n_total_nsh > 0
                else np.nan
            ),

        "TN":
            int(TN),

        "FP":
            int(FP),

        "FN":
            int(FN),

        "TP":
            int(TP),

        "Accuracy":
            accuracy_score(
                y_true,
                y_pred,
            ),

        "Precision_Sh":
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            ),

        "Sensitivity_Sh":
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            ),

        "Specificity":
            specificity,

        "F1_Sh":
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            ),

        "F1_Weighted":
            f1_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0,
            ),

        # Exact half remains NSh under the strict >50% rule.
        # Saved as a diagnostic so true-Sh exact-half years can be reported as TFY.
        "Exact_Half_Years":
            valid.loc[
                valid[
                    exact_half_col
                ] == True,
                "Heldout_Year",
            ]
            .astype(int)
            .tolist(),

        # TFY = true-Sh years with exactly 50% of the ORIGINAL
        # signature votes. Under strict >50%, they remain NSh.
        "TFY":
            valid.loc[
                (
                    valid[
                        exact_half_col
                    ] == True
                )
                &
                (
                    valid[
                        "True_Class"
                    ] == "Sh"
                ),
                "Heldout_Year",
            ]
            .astype(int)
            .tolist(),

        "Confusion_Matrix":
            cm,
    }



# ============================================================
# FULL-DATA AUTOMATIC STa EVALUATION
# ============================================================

def evaluate_full_data_auto_sta():
    """
    Evaluate the automatic STa rules produced by F1's FULL_DATA run.

    Uses:
      THRESHOLD_DIR/full_data/fixed_signature_rules.xlsx
      THRESHOLD_DIR/full_data/full_data_nonstandardized_with_classes.xlsx

    Voting is IDENTICAL to the fold-specific Auto-STa evaluation:
      - same fixed original-signature denominator
      - same strict >50% rule
      - same three-state treatment for incomplete two-sided rules
      - same inclusive threshold comparisons (<= / >=)

    This result is diagnostic only, not independent.
    """

    if not RUN_FULL_DATA_AUTO_DIAGNOSTIC:
        return None

    missing_files = [
        path
        for path in [
            FULL_DATA_RULE_FILE,
            FULL_DATA_RAW_FILE,
        ]
        if not os.path.exists(
            path
        )
    ]

    if missing_files:

        print(
            "\nFULL-DATA automatic STa diagnostic skipped."
        )

        print(
            "Missing F1 full-data output file(s):"
        )

        for path in missing_files:
            print(
                f"  {path}"
            )

        return None

    rules = pd.read_excel(
        FULL_DATA_RULE_FILE
    )

    full_data = pd.read_excel(
        FULL_DATA_RAW_FILE
    )

    if "Feature" not in rules.columns:
        raise ValueError(
            "Full-data fixed_signature_rules.xlsx has no Feature column."
        )

    missing_features = [
        feature
        for feature in FIXED_FEATURES
        if feature not in full_data.columns
    ]

    if missing_features:
        raise ValueError(
            "Full-data raw file is missing fixed-signature features: "
            f"{missing_features}"
        )

    # Year is used only for transparent diagnostics.
    year_col = None

    for candidate in [
        "Year",
        "year",
        "YEAR",
    ]:
        if candidate in full_data.columns:
            year_col = candidate
            break

    if year_col is None:
        full_data = full_data.copy()

        full_data[
            "_FullData_Row"
        ] = np.arange(
            1,
            len(
                full_data
            )
            + 1,
        )

        year_col = "_FullData_Row"

    prediction_rows = []
    vote_rows = []

    for _, row in full_data.iterrows():

        year_value = row[
            year_col
        ]

        try:
            year_value = int(
                year_value
            )
        except Exception:
            pass

        true_class = get_true_class(
            row,
            full_data.columns,
        )

        sta_hits = []
        sta_valid_features = []
        sta_partial_hit_features = []
        sta_partial_unknown_features = []
        sta_unavailable_features = []

        for feature in FIXED_FEATURES:

            fdf = rules[
                rules[
                    "Feature"
                ].astype(str)
                == feature
            ]

            rule_row = (
                None
                if fdf.empty
                else fdf.iloc[
                    0
                ]
            )

            value = float(
                row[
                    feature
                ]
            )

            sta_eval = evaluate_fold_feature_vote(
                value,
                rule_row,
                "STa",
                feature,
            )

            sta_hit = sta_eval[
                "Hit"
            ]

            sta_completeness = sta_eval[
                "Completeness"
            ]

            if sta_eval[
                "Is_Valid"
            ]:

                sta_hits.append(
                    int(
                        sta_hit
                    )
                )

                sta_valid_features.append(
                    feature
                )

                if (
                    sta_completeness
                    == "PARTIAL"
                ):
                    sta_partial_hit_features.append(
                        feature
                    )

            else:

                if (
                    sta_completeness
                    == "PARTIAL"
                ):
                    sta_partial_unknown_features.append(
                        feature
                    )

                else:
                    sta_unavailable_features.append(
                        feature
                    )

            vote_rows.append({
                "Heldout_Year":
                    year_value,

                "True_Class":
                    true_class,

                "Feature":
                    feature,

                "Observed_Value":
                    value,

                "STa_Available_Side_Count":
                    sta_eval[
                        "Available_Side_Count"
                    ],

                "STa_Completeness":
                    sta_completeness,

                "STa_Feature_Available":
                    bool(
                        sta_eval[
                            "Is_Valid"
                        ]
                    ),

                "STa_Vote_Status":
                    sta_eval[
                        "Vote_Status"
                    ],

                "Auto_STa_Hit":
                    sta_hit,

                "Lower_Auto_STa":
                    sta_eval[
                        "Lower"
                    ],

                "Upper_Auto_STa":
                    sta_eval[
                        "Upper"
                    ],
            })

        sta_valid_k = len(
            sta_valid_features
        )

        if (
            sta_valid_k
            >= MIN_VALID_FEATURES
        ):

            sta_total_hits = int(
                np.sum(
                    sta_hits
                )
            )

            pred_sta = (
                "Sh"
                if sta_total_hits
                >= ORIGINAL_REQUIRED_HITS
                else "NSh"
            )

        else:

            sta_total_hits = np.nan
            pred_sta = np.nan

        exact_half = bool(
            np.isfinite(
                sta_total_hits
            )
            and
            ORIGINAL_SIGNATURE_K
            % 2
            == 0
            and
            sta_total_hits
            == ORIGINAL_SIGNATURE_K
            / 2
        )

        prediction_rows.append({
            "Heldout_Year":
                year_value,

            "True_Class":
                true_class,

            "Original_Signature_k":
                ORIGINAL_SIGNATURE_K,

            "Fixed_Required_Hits":
                ORIGINAL_REQUIRED_HITS,

            "STa_Valid_k":
                sta_valid_k,

            "STa_Valid_Features":
                "; ".join(
                    sta_valid_features
                ),

            "STa_Partial_Hit_Features":
                "; ".join(
                    sta_partial_hit_features
                ),

            "STa_Partial_Unknown_Features":
                "; ".join(
                    sta_partial_unknown_features
                ),

            "STa_Unavailable_Features":
                "; ".join(
                    sta_unavailable_features
                ),

            "STa_Stress_Hits":
                sta_total_hits,

            "STa_Required_Hits":
                ORIGINAL_REQUIRED_HITS,

            "Prediction_FullData_Auto_STa":
                pred_sta,

            "FullData_STa_Exact_Half":
                exact_half,
        })

    full_predictions = (
        pd.DataFrame(
            prediction_rows
        )
        .sort_values(
            "Heldout_Year"
        )
        .reset_index(
            drop=True
        )
    )

    full_votes = pd.DataFrame(
        vote_rows
    )

    full_predictions.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "full_data_auto_STa_predictions_DIAGNOSTIC.xlsx",
        ),
        index=False,
    )

    full_votes.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "full_data_auto_STa_feature_vote_details_DIAGNOSTIC.xlsx",
        ),
        index=False,
    )

    full_result = calculate_metrics(
        full_predictions,
        "Prediction_FullData_Auto_STa",
        "FullData_STa_Exact_Half",
        "Full-data automated STa diagnostic",
        "DIAGNOSTIC_ONLY_NOT_INDEPENDENT",
    )

    pd.DataFrame(
        [
            {
                key:
                    value
                for key, value
                in full_result.items()
                if key
                not in [
                    "Confusion_Matrix",
                    "Exact_Half_Years",
                    "TFY",
                ]
            }
        ]
    ).to_excel(
        os.path.join(
            OUTPUT_DIR,
            "full_data_auto_STa_metrics_DIAGNOSTIC.xlsx",
        ),
        index=False,
    )

    return full_result


fold_names = (
    sorted([
        name
        for name in os.listdir(STEP2_DIR)
        if (
            name.startswith("heldout_")
            and os.path.isdir(os.path.join(STEP2_DIR, name))
        )
    ])
    if os.path.isdir(STEP2_DIR)
    else []
)

if RUN_LOYO and len(fold_names) == 0:
    raise ValueError(
        f"RUN_MODE includes LOYO but no heldout folders were found in:\n{STEP2_DIR}"
    )

if not RUN_LOYO:
    fold_names = []


prediction_rows = []
vote_rows = []

# Full-data AUTOMATIC rules are the non-independent benchmark that replaces the
# old fixed-threshold diagnostic.  They are never used for fold-specific STi/STa.
if os.path.exists(FULL_DATA_RULE_FILE):
    FULL_DATA_AUTO_RULES = pd.read_excel(FULL_DATA_RULE_FILE)
else:
    FULL_DATA_AUTO_RULES = pd.DataFrame()


for fold_name in fold_names:

    year = int(
        fold_name.replace(
            "heldout_",
            "",
        )
    )

    heldout_path = locate_heldout_raw(
        os.path.join(
            STEP2_DIR,
            fold_name,
        )
    )

    heldout = pd.read_excel(
        heldout_path
    )

    if len(heldout) != 1:
        raise ValueError(
            f"{year}: expected one held-out row."
        )

    row = heldout.iloc[0]

    true_class = get_true_class(
        row,
        heldout.columns,
    )

    model_oob_r2 = read_fold_oob_r2(
        fold_name
    )

    model_skill_status = (
        "NEGATIVE_OOB_R2"
        if (
            np.isfinite(
                model_oob_r2
            )
            and
            model_oob_r2 < 0
        )
        else (
            "NONNEGATIVE_OOB_R2"
            if np.isfinite(
                model_oob_r2
            )
            else "OOB_R2_UNAVAILABLE"
        )
    )

    missing_features = [
        f
        for f in FIXED_FEATURES
        if f not in heldout.columns
    ]

    if missing_features:
        raise ValueError(
            f"{year}: missing held-out features: "
            f"{missing_features}"
        )

    rule_path = os.path.join(
        THRESHOLD_DIR,
        fold_name,
        "fixed_signature_rules.xlsx",
    )

    if not os.path.exists(
        rule_path
    ):
        prediction_rows.append({
            "Heldout_Year": year,
            "True_Class": true_class,
            "Model_OOB_R2": model_oob_r2,
            "Model_Skill_Status": model_skill_status,
            "STi_Valid_k": 0,
            "STi_Stress_Hits": np.nan,
            "STi_Required_Hits": np.nan,
            "Prediction_Fold_STi": np.nan,
            "STa_Valid_k": 0,
            "STa_Stress_Hits": np.nan,
            "STa_Required_Hits": np.nan,
            "Prediction_Fold_Auto_STa": np.nan,
            "FullData_Auto_STa_Valid_k": 0,
            "FullData_Auto_STa_Stress_Hits": np.nan,
            "FullData_Auto_STa_Required_Hits": ORIGINAL_REQUIRED_HITS,
            "Prediction_FullData_Auto_STa_on_Heldout": np.nan,
            "Reason": "NO_THRESHOLD_FILE",
        })
        continue

    rules = pd.read_excel(
        rule_path
    )

    sti_hits = []
    sti_valid_features = []
    sti_partial_hit_features = []
    sti_partial_unknown_features = []
    sti_unavailable_features = []

    sta_hits = []
    sta_valid_features = []
    sta_partial_hit_features = []
    sta_partial_unknown_features = []
    sta_unavailable_features = []

    full_auto_hits = []
    full_auto_valid_features = []

    for feature in FIXED_FEATURES:

        fdf = rules[
            rules[
                "Feature"
            ].astype(str)
            == feature
        ]

        f = (
            None
            if fdf.empty
            else fdf.iloc[0]
        )

        value = float(
            row[
                feature
            ]
        )

        # ---------------- STi ----------------
        sti_eval = evaluate_fold_feature_vote(
            value,
            f,
            "STi",
            feature,
        )

        lower_sti = sti_eval[
            "Lower"
        ]

        upper_sti = sti_eval[
            "Upper"
        ]

        sti_hit = sti_eval[
            "Hit"
        ]

        sti_completeness = sti_eval[
            "Completeness"
        ]

        sti_vote_status = sti_eval[
            "Vote_Status"
        ]

        if sti_eval[
            "Is_Valid"
        ]:
            sti_hits.append(
                int(
                    sti_hit
                )
            )

            sti_valid_features.append(
                feature
            )

            if (
                sti_completeness
                == "PARTIAL"
            ):
                sti_partial_hit_features.append(
                    feature
                )

        else:
            if (
                sti_completeness
                == "PARTIAL"
            ):
                sti_partial_unknown_features.append(
                    feature
                )
            else:
                sti_unavailable_features.append(
                    feature
                )

        # ---------------- STa ----------------
        sta_eval = evaluate_fold_feature_vote(
            value,
            f,
            "STa",
            feature,
        )

        lower_sta = sta_eval[
            "Lower"
        ]

        upper_sta = sta_eval[
            "Upper"
        ]

        sta_hit = sta_eval[
            "Hit"
        ]

        sta_completeness = sta_eval[
            "Completeness"
        ]

        sta_vote_status = sta_eval[
            "Vote_Status"
        ]

        if sta_eval[
            "Is_Valid"
        ]:
            sta_hits.append(
                int(
                    sta_hit
                )
            )

            sta_valid_features.append(
                feature
            )

            if (
                sta_completeness
                == "PARTIAL"
            ):
                sta_partial_hit_features.append(
                    feature
                )

        else:
            if (
                sta_completeness
                == "PARTIAL"
            ):
                sta_partial_unknown_features.append(
                    feature
                )
            else:
                sta_unavailable_features.append(
                    feature
                )

        # -------- full-data automatic STa diagnostic --------
        full_rule_df = FULL_DATA_AUTO_RULES[
            FULL_DATA_AUTO_RULES["Feature"].astype(str) == feature
        ] if (not FULL_DATA_AUTO_RULES.empty and "Feature" in FULL_DATA_AUTO_RULES.columns) else pd.DataFrame()

        full_rule = (
            None
            if full_rule_df.empty
            else full_rule_df.iloc[0]
        )

        full_auto_eval = evaluate_fold_feature_vote(
            value,
            full_rule,
            "STa",
            feature,
        )

        full_auto_hit = full_auto_eval["Hit"]
        if full_auto_eval["Is_Valid"]:
            full_auto_hits.append(int(full_auto_hit))
            full_auto_valid_features.append(feature)

        vote_rows.append({
            "Heldout_Year": year,
            "True_Class": true_class,
            "Feature": feature,
            "Observed_Value": value,

            "Expected_Side_Count":
                EXPECTED_SIDE_COUNT[
                    feature
                ],

            "STi_Available_Side_Count":
                sti_eval[
                    "Available_Side_Count"
                ],
            "STi_Completeness":
                sti_completeness,
            "STi_Feature_Available":
                feature in sti_valid_features,
            "STi_Vote_Status":
                sti_vote_status,
            "STi_Hit":
                sti_hit,
            "Lower_STi":
                lower_sti,
            "Upper_STi":
                upper_sti,

            "STa_Available_Side_Count":
                sta_eval[
                    "Available_Side_Count"
                ],
            "STa_Completeness":
                sta_completeness,
            "STa_Feature_Available":
                feature in sta_valid_features,
            "STa_Vote_Status":
                sta_vote_status,
            "Auto_STa_Hit":
                sta_hit,
            "Lower_Auto_STa":
                lower_sta,
            "Upper_Auto_STa":
                upper_sta,

            "FullData_Auto_STa_Hit":
                full_auto_hit,
            "Lower_FullData_Auto_STa":
                full_auto_eval["Lower"],
            "Upper_FullData_Auto_STa":
                full_auto_eval["Upper"],
        })


    # ========================================================
    # STi prediction
    #
    # valid_k controls ONLY whether the fold is evaluable.
    # The majority denominator NEVER shrinks with missing sides.
    # Required hits are fixed from the AUTOMATIC fixed signature size.
    # ========================================================

    sti_valid_k = len(
        sti_valid_features
    )

    if (
        sti_valid_k
        >= MIN_VALID_FEATURES
    ):
        sti_total_hits = int(
            np.sum(
                sti_hits
            )
        )

        sti_required_hits = (
            ORIGINAL_REQUIRED_HITS
        )

        pred_sti = (
            "Sh"
            if sti_total_hits
            >= sti_required_hits
            else "NSh"
        )
    else:
        sti_total_hits = np.nan
        sti_required_hits = (
            ORIGINAL_REQUIRED_HITS
        )
        pred_sti = np.nan


    # ========================================================
    # STa prediction
    #
    # Same fixed original-signature denominator.
    # ========================================================

    sta_valid_k = len(
        sta_valid_features
    )

    if (
        sta_valid_k
        >= MIN_VALID_FEATURES
    ):
        sta_total_hits = int(
            np.sum(
                sta_hits
            )
        )

        sta_required_hits = (
            ORIGINAL_REQUIRED_HITS
        )

        pred_sta = (
            "Sh"
            if sta_total_hits
            >= sta_required_hits
            else "NSh"
        )
    else:
        sta_total_hits = np.nan
        sta_required_hits = (
            ORIGINAL_REQUIRED_HITS
        )
        pred_sta = np.nan

    # ========================================================
    # Full-data automatic STa diagnostic on held-out observations
    # ========================================================

    full_auto_valid_k = len(full_auto_valid_features)

    if full_auto_valid_k >= MIN_VALID_FEATURES:
        full_auto_total_hits = int(np.sum(full_auto_hits))
        pred_full_auto = (
            "Sh"
            if full_auto_total_hits >= ORIGINAL_REQUIRED_HITS
            else "NSh"
        )
    else:
        full_auto_total_hits = np.nan
        pred_full_auto = np.nan


    prediction_rows.append({
        "Heldout_Year":
            year,

        "True_Class":
            true_class,

        "Model_OOB_R2":
            model_oob_r2,

        "Model_Skill_Status":
            model_skill_status,

        "Original_Signature_k":
            ORIGINAL_SIGNATURE_K,

        "Fixed_Required_Hits":
            ORIGINAL_REQUIRED_HITS,

        "STi_Valid_k":
            sti_valid_k,

        "STi_N_Partial_Hit":
            len(
                sti_partial_hit_features
            ),

        "STi_N_Partial_Unknown":
            len(
                sti_partial_unknown_features
            ),

        "STi_Valid_Features":
            "; ".join(
                sti_valid_features
            ),

        "STi_Partial_Hit_Features":
            "; ".join(
                sti_partial_hit_features
            ),

        "STi_Partial_Unknown_Features":
            "; ".join(
                sti_partial_unknown_features
            ),

        "STi_Unavailable_Features":
            "; ".join(
                sti_unavailable_features
            ),

        "STi_Stress_Hits":
            sti_total_hits,

        "STi_Required_Hits":
            sti_required_hits,

        "Prediction_Fold_STi":
            pred_sti,

        "STa_Valid_k":
            sta_valid_k,

        "STa_N_Partial_Hit":
            len(
                sta_partial_hit_features
            ),

        "STa_N_Partial_Unknown":
            len(
                sta_partial_unknown_features
            ),

        "STa_Valid_Features":
            "; ".join(
                sta_valid_features
            ),

        "STa_Partial_Hit_Features":
            "; ".join(
                sta_partial_hit_features
            ),

        "STa_Partial_Unknown_Features":
            "; ".join(
                sta_partial_unknown_features
            ),

        "STa_Unavailable_Features":
            "; ".join(
                sta_unavailable_features
            ),

        "STa_Stress_Hits":
            sta_total_hits,

        "STa_Required_Hits":
            sta_required_hits,

        "Prediction_Fold_Auto_STa":
            pred_sta,

        "FullData_Auto_STa_Valid_k":
            full_auto_valid_k,

        "FullData_Auto_STa_Stress_Hits":
            full_auto_total_hits,

        "FullData_Auto_STa_Required_Hits":
            ORIGINAL_REQUIRED_HITS,

        "Prediction_FullData_Auto_STa_on_Heldout":
            pred_full_auto,

        # ----------------------------------------------------
        # Exact half of the AUTOMATIC fixed signature.
        #
        # Under the original "at least half" rule, an exact
        # Exact 50% remains NSh under the strict >50% rule.
        # These flags are saved as diagnostics and never alter predictions.
        # ----------------------------------------------------

        "STi_Exact_Half":
            bool(
                np.isfinite(
                    sti_total_hits
                )
                and
                ORIGINAL_SIGNATURE_K % 2 == 0
                and
                sti_total_hits
                == ORIGINAL_SIGNATURE_K / 2
            ),

        "STa_Exact_Half":
            bool(
                np.isfinite(
                    sta_total_hits
                )
                and
                ORIGINAL_SIGNATURE_K % 2 == 0
                and
                sta_total_hits
                == ORIGINAL_SIGNATURE_K / 2
            ),

        "FullData_Auto_STa_Exact_Half":
            bool(
                np.isfinite(full_auto_total_hits)
                and
                ORIGINAL_SIGNATURE_K % 2 == 0
                and
                full_auto_total_hits
                == ORIGINAL_SIGNATURE_K / 2
            ),

        "Reason":
            (
                "INSUFFICIENT_FULL_FEATURES"
                if (
                    (
                        not (
                            pred_sti
                            in [
                                "Sh",
                                "NSh",
                            ]
                        )
                    )
                    or
                    (
                        not (
                            pred_sta
                            in [
                                "Sh",
                                "NSh",
                            ]
                        )
                    )
                )
                else ""
            ),
    })


if RUN_LOYO:
    predictions = (
        pd.DataFrame(
            prediction_rows
        )
        .sort_values(
            "Heldout_Year"
        )
        .reset_index(
            drop=True
        )
    )

    votes = pd.DataFrame(
        vote_rows
    )

    predictions.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_predictions.xlsx",
        ),
        index=False,
    )

    votes.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_feature_vote_details.xlsx",
        ),
        index=False,
    )


    # ============================================================
    # valid_k distributions
    # ============================================================

    for (
        column,
        filename,
    ) in [
        (
            "STi_Valid_k",
            "STi_valid_k_distribution.xlsx",
        ),
        (
            "STa_Valid_k",
            "STa_valid_k_distribution.xlsx",
        ),
    ]:
        distribution = (
            predictions[
                column
            ]
            .value_counts(
                dropna=False
            )
            .sort_index()
            .rename_axis(
                "Valid_k"
            )
            .reset_index(
                name="N_Folds"
            )
        )

        distribution[
            "Frequency"
        ] = (
            distribution[
                "N_Folds"
            ]
            / len(predictions)
        )

        distribution.to_excel(
            os.path.join(
                OUTPUT_DIR,
                filename,
            ),
            index=False,
        )


    method_specs = [
        (
            "Prediction_Fold_STi",
            "STi_Exact_Half",
            "Fixed-signature fold-specific STi",
            "INDEPENDENT_THRESHOLD_DERIVATION",
        ),
        (
            "Prediction_Fold_Auto_STa",
            "STa_Exact_Half",
            "Fixed-signature fold-specific automated STa",
            "INDEPENDENT_THRESHOLD_DERIVATION",
        ),
        (
            "Prediction_FullData_Auto_STa_on_Heldout",
            "FullData_Auto_STa_Exact_Half",
            "Full-data automated STa diagnostic on held-out observations",
            "DIAGNOSTIC_ONLY_NOT_INDEPENDENT",
        ),
    ]

    # The third diagnostic exists only when F1 FULL_DATA rules were produced.
    if FULL_DATA_AUTO_RULES.empty:
        method_specs = method_specs[:2]

    results = []

    for (
        prediction_col,
        tie_col,
        method_name,
        independence_status,
    ) in method_specs:

        result = calculate_metrics(
            predictions,
            prediction_col,
            tie_col,
            method_name,
            independence_status,
        )

        results.append(
            result
        )

    summary = pd.DataFrame([
        {
            key: value
            for key, value
            in result.items()
            if key
            not in [
                "Confusion_Matrix",
                "Exact_Half_Years",
                "TFY",
            ]
        }
        for result in results
    ])

    summary.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_method_comparison.xlsx",
        ),
        index=False,
    )


else:
    predictions = pd.DataFrame()
    votes = pd.DataFrame()
    results = []
    summary = pd.DataFrame()
    method_specs = []


if RUN_LOYO:
    # ============================================================
    # OOB-R2 SENSITIVITY
    #
    # IMPORTANT:
    # Negative-OOB folds remain in the PRIMARY analysis above.
    # This table is only a sensitivity/diagnostic so that low-skill
    # RF folds can be discussed without selectively deleting them.
    # ============================================================

    skill_sensitivity_rows = []

    for (
        prediction_col,
        tie_col,
        method_name,
        independence_status,
    ) in method_specs[:2]:

        for (
            skill_group,
            subset,
        ) in [
            (
                "ALL_FOLDS_PRIMARY",
                predictions.copy(),
            ),
            (
                "OOB_R2_NONNEGATIVE",
                predictions[
                    predictions[
                        "Model_OOB_R2"
                    ].notna()
                    &
                    (
                        predictions[
                            "Model_OOB_R2"
                        ]
                        >= 0
                    )
                ].copy(),
            ),
            (
                "OOB_R2_NEGATIVE",
                predictions[
                    predictions[
                        "Model_OOB_R2"
                    ].notna()
                    &
                    (
                        predictions[
                            "Model_OOB_R2"
                        ]
                        < 0
                    )
                ].copy(),
            ),
        ]:

            if subset.empty:
                continue

            evaluable_subset = subset[
                subset[
                    prediction_col
                ].isin(
                    [
                        "NSh",
                        "Sh",
                    ]
                )
            ].copy()

            if evaluable_subset.empty:
                skill_sensitivity_rows.append({
                    "Method":
                        method_name,
                    "Skill_Group":
                        skill_group,
                    "N_Group_Folds":
                        len(subset),
                    "N_Evaluated":
                        0,
                    "Coverage_Within_Group":
                        0.0,
                    "TN":
                        np.nan,
                    "FP":
                        np.nan,
                    "FN":
                        np.nan,
                    "TP":
                        np.nan,
                    "F1_Weighted":
                        np.nan,
                    "F1_Sh":
                        np.nan,
                    "Sensitivity_Sh":
                        np.nan,
                    "Specificity":
                        np.nan,
                })

                continue

            tmp_result = calculate_metrics(
                subset,
                prediction_col,
                tie_col,
                method_name,
                independence_status,
            )

            skill_sensitivity_rows.append({
                "Method":
                    method_name,
                "Skill_Group":
                    skill_group,
                "N_Group_Folds":
                    len(subset),
                "N_Evaluated":
                    tmp_result[
                        "N_Evaluated"
                    ],
                "Coverage_Within_Group":
                    tmp_result[
                        "Coverage"
                    ],
                "TN":
                    tmp_result[
                        "TN"
                    ],
                "FP":
                    tmp_result[
                        "FP"
                    ],
                "FN":
                    tmp_result[
                        "FN"
                    ],
                "TP":
                    tmp_result[
                        "TP"
                    ],
                "F1_Weighted":
                    tmp_result[
                        "F1_Weighted"
                    ],
                "F1_Sh":
                    tmp_result[
                        "F1_Sh"
                    ],
                "Sensitivity_Sh":
                    tmp_result[
                        "Sensitivity_Sh"
                    ],
                "Specificity":
                    tmp_result[
                        "Specificity"
                    ],
            })


    pd.DataFrame(
        skill_sensitivity_rows
    ).to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_OOB_R2_sensitivity.xlsx",
        ),
        index=False,
    )


    # ============================================================
    # Not-evaluable years
    # ============================================================

    coverage_rows = []

    for (
        prediction_col,
        _,
        method_name,
        _,
    ) in method_specs[:2]:

        not_evaluable = predictions[
            ~predictions[
                prediction_col
            ].isin(
                [
                    "Sh",
                    "NSh",
                ]
            )
        ].copy()

        for _, r in not_evaluable.iterrows():
            coverage_rows.append({
                "Method":
                    method_name,

                "Heldout_Year":
                    int(
                        r[
                            "Heldout_Year"
                        ]
                    ),

                "True_Class":
                    r[
                        "True_Class"
                    ],

                "STi_Valid_k":
                    r[
                        "STi_Valid_k"
                    ],

                "STa_Valid_k":
                    r[
                        "STa_Valid_k"
                    ],

                "STi_Valid_Features":
                    r.get(
                        "STi_Valid_Features",
                        "",
                    ),

                "STa_Valid_Features":
                    r.get(
                        "STa_Valid_Features",
                        "",
                    ),

                "STi_Partial_Hit_Features":
                    r.get(
                        "STi_Partial_Hit_Features",
                        "",
                    ),

                "STi_Partial_Unknown_Features":
                    r.get(
                        "STi_Partial_Unknown_Features",
                        "",
                    ),

                "STa_Partial_Hit_Features":
                    r.get(
                        "STa_Partial_Hit_Features",
                        "",
                    ),

                "STa_Partial_Unknown_Features":
                    r.get(
                        "STa_Partial_Unknown_Features",
                        "",
                    ),

                "Model_OOB_R2":
                    r.get(
                        "Model_OOB_R2",
                        np.nan,
                    ),

                "Model_Skill_Status":
                    r.get(
                        "Model_Skill_Status",
                        "",
                    ),
            })

    pd.DataFrame(
        coverage_rows
    ).to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_not_evaluable_years.xlsx",
        ),
        index=False,
    )


    # ============================================================
    # Feature diagnostics
    # ============================================================

    diagnostic_rows = []

    for feature in FIXED_FEATURES:

        part = votes[
            votes[
                "Feature"
            ] == feature
        ].copy()

        for (
            method_label,
            available_col,
            hit_col,
        ) in [
            (
                "Fold_STi",
                "STi_Feature_Available",
                "STi_Hit",
            ),
            (
                "Fold_Auto_STa",
                "STa_Feature_Available",
                "Auto_STa_Hit",
            ),
        ]:

            available = part[
                part[
                    available_col
                ] == True
            ].copy()

            sh = available[
                available[
                    "True_Class"
                ] == "Sh"
            ][hit_col]

            nsh = available[
                available[
                    "True_Class"
                ] == "NSh"
            ][hit_col]

            diagnostic_rows.append({
                "Feature":
                    feature,

                "Method":
                    method_label,

                "Available_Folds":
                    len(
                        available
                    ),

                "Availability_Frequency":
                    len(
                        available
                    )
                    / len(
                        part
                    ),

                "Sh_Hit_Rate_When_Available":
                    (
                        float(
                            sh.mean()
                        )
                        if len(sh) > 0
                        else np.nan
                    ),

                "NSh_Hit_Rate_When_Available":
                    (
                        float(
                            nsh.mean()
                        )
                        if len(nsh) > 0
                        else np.nan
                    ),

                "Sh_minus_NSh_Hit_Rate":
                    (
                        float(
                            sh.mean()
                            - nsh.mean()
                        )
                        if (
                            len(sh) > 0
                            and
                            len(nsh) > 0
                        )
                        else np.nan
                    ),
            })

    pd.DataFrame(
        diagnostic_rows
    ).to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_feature_diagnostics.xlsx",
        ),
        index=False,
    )


    # ============================================================
    # EXACT-HALF DIAGNOSTICS
    #
    # Strict-majority voting rule:
    #     Sh only when hits > 50% of the AUTOMATIC fixed signature.
    #
    # Therefore exact 50% remains NSh. True-Sh exact-half years
    # are recorded as TFY diagnostics.
    # ============================================================

    exact_half_rows = []

    for result in results:

        method_name = result[
            "Method"
        ]

        for year in result[
            "Exact_Half_Years"
        ]:

            true_class = predictions.loc[
                predictions[
                    "Heldout_Year"
                ] == year,
                "True_Class",
            ].iloc[0]

            exact_half_rows.append({
                "Method":
                    method_name,

                "Heldout_Year":
                    int(
                        year
                    ),

                "True_Class":
                    true_class,

                "Original_Signature_k":
                    ORIGINAL_SIGNATURE_K,

                "Fixed_Required_Hits":
                    ORIGINAL_REQUIRED_HITS,

                "TFY":
                    bool(
                        true_class
                        == "Sh"
                    ),

                "Diagnostic":
                    "EXACT_HALF_OF_ORIGINAL_SIGNATURE",
            })


    pd.DataFrame(
        exact_half_rows,
        columns=[
            "Method",
            "Heldout_Year",
            "True_Class",
            "Original_Signature_k",
            "Fixed_Required_Hits",
            "TFY",
            "Diagnostic",
        ],
    ).to_excel(
        os.path.join(
            OUTPUT_DIR,
            "fixed_signature_exact_half_diagnostics.xlsx",
        ),
        index=False,
    )



# ============================================================
# OLD-STYLE FULL-DATA ALIGNMENT WORKBOOK HELPERS
# ============================================================
# Preserved from the original F2 workbook workflow. The source is now the
# automatic FULL_DATA diagnostic, so it works in FULL_DATA and BOTH modes.

# ============================================================
# FULL-DATA ALIGNMENT WORKBOOK
# ============================================================
# PURPOSE:
# Reproduce the complete alignment/stress-type information in
# alignment_results_with_metrics.xlsx using FULL-DATA AUTOMATIC STa rules.
#
# IMPORTANT:
#   - This workbook uses the FULL-DATA AUTOMATIC STa diagnostic.
#     Fold-specific LOYO STi/STa remain in their dedicated output files.
#   - The current F2 strict-majority rule (>50% of the ORIGINAL
#     signature) is kept unchanged.
#   - No extra audit/LOYO/availability sheets are added.
#
# Output name:
#   <COUNTRY>_<CROP>_alignment_results_with_metrics.xlsx
# Example:
#   ALB_Potato_alignment_results_with_metrics.xlsx
# ============================================================


def _fd_normalize_class3(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    mapping = {
        "Sh": "Sh",
        "Shocked": "Sh",
        "Low": "Sh",

        "No": "No",
        "No.": "No",
        "Normal": "No",

        "Bo": "Bo",
        "Boosted": "Bo",
        "High": "Bo",
    }

    return mapping.get(text, text)


def _fd_get_metadata_from_full_data():
    """Read full-series year, class and detrended-yield metadata from F1."""

    if not os.path.exists(FULL_DATA_RAW_FILE):
        raise FileNotFoundError(
            "F1 full-data raw file not found while building the alignment workbook:\n"
            f"{FULL_DATA_RAW_FILE}"
        )

    full_meta = pd.read_excel(FULL_DATA_RAW_FILE)

    year_col = next(
        (c for c in ["Year", "year", "YEAR"] if c in full_meta.columns),
        None,
    )
    if year_col is None:
        raise ValueError(
            "Could not find a Year column in F1 full-data raw output."
        )

    rows = []
    for _, row in full_meta.iterrows():
        year = row[year_col]
        try:
            year = int(year)
        except Exception:
            pass

        class3 = np.nan
        for col in ["Yield_Class", "True_Class_3"]:
            if col in full_meta.columns:
                class3 = _fd_normalize_class3(row[col])
                break

        if pd.isna(class3):
            class3 = (
                "Sh"
                if get_true_class(row, full_meta.columns) == "Sh"
                else "NSh"
            )

        detrended_yield = np.nan
        for col in ["Detrended_Yield", "Detrended yield", "detrended_yield"]:
            if col in full_meta.columns:
                value = row[col]
                if pd.notna(value):
                    detrended_yield = float(value)
                break

        rows.append({
            "Heldout_Year": year,
            "Yield_Class": class3,
            "Detrended_Yield": detrended_yield,
        })

    return (
        pd.DataFrame(rows)
        .sort_values("Heldout_Year")
        .reset_index(drop=True)
    )

def _fd_fmt_num(value):
    if pd.isna(value):
        return ""

    try:
        value = float(value)
    except Exception:
        return str(value)

    if np.isclose(
        value,
        round(value),
    ):
        return str(
            int(
                round(value)
            )
        )

    return (
        f"{value:.2f}"
        .rstrip("0")
        .rstrip(".")
    )


_FD_MONTH_NAME = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}


def _fd_parse_feature_month(feature):
    text = str(feature)

    if "_" not in text:
        return text.lower(), None

    base, tail = text.rsplit(
        "_",
        1,
    )

    try:
        month = int(tail)
    except Exception:
        month = None

    return base.lower(), month


def _fd_stress_type_from_side(
    feature,
    side,
):
    """
    Convert an automatic STa breach to the same compound-stress terminology
    used in the old alignment workbook.
    """

    base, month = _fd_parse_feature_month(
        feature
    )

    if (
        "rx1" in base
        or
        "rx5" in base
        or
        "precip" in base
        or
        "ppt" in base
        or
        "rain" in base
    ):
        kind = (
            "precipitation-deficit"
            if side == "lower"
            else "precipitation-excess"
        )

    elif "cdd" in base:
        kind = (
            "wet-persistence"
            if side == "lower"
            else "dry-persistence"
        )

    elif "cwd" in base:
        kind = (
            "dry-persistence"
            if side == "lower"
            else "wet-persistence"
        )

    elif (
        "csu" in base
        or
        "ccu" in base
    ):
        kind = (
            "warm-spell deficit"
            if side == "lower"
            else "heatwave"
        )

    elif (
        "ccd" in base
        or
        "cfd" in base
    ):
        kind = (
            "chilling-deficit"
            if side == "lower"
            else "cold-wave"
        )

    else:
        kind = None

    return kind, month


def _fd_compound_stress_types(
    year_votes,
):
    buckets = {}

    for _, vote in year_votes.iterrows():

        if (
            pd.isna(
                vote[
                    "FullData_Auto_STa_Hit"
                ]
            )
            or
            int(
                vote[
                    "FullData_Auto_STa_Hit"
                ]
            )
            != 1
        ):
            continue

        feature = str(
            vote[
                "Feature"
            ]
        )

        value = float(
            vote[
                "Observed_Value"
            ]
        )

        lower = vote[
            "Lower_FullData_Auto_STa"
        ]

        upper = vote[
            "Upper_FullData_Auto_STa"
        ]

        sides = []

        if (
            pd.notna(lower)
            and
            value <= float(lower)
        ):
            sides.append(
                "lower"
            )

        if (
            pd.notna(upper)
            and
            value >= float(upper)
        ):
            sides.append(
                "upper"
            )

        for side in sides:

            kind, month = (
                _fd_stress_type_from_side(
                    feature,
                    side,
                )
            )

            if kind is None:
                continue

            buckets.setdefault(
                kind,
                set(),
            )

            if month is not None:
                buckets[
                    kind
                ].add(
                    month
                )

    order = [
        "wet-persistence",
        "dry-persistence",
        "precipitation-excess",
        "precipitation-deficit",
        "heatwave",
        "cold-wave",
        "chilling-deficit",
        "warm-spell deficit",
    ]

    phrases = []

    for kind in order:

        if kind not in buckets:
            continue

        months = sorted(
            buckets[kind]
        )

        if len(months) == 0:
            phrases.append(
                kind
            )
            continue

        names = [
            _FD_MONTH_NAME.get(
                month,
                str(month),
            )
            for month in months
        ]

        if len(names) == 1:
            month_text = names[0]

        elif len(names) == 2:
            month_text = (
                f"{names[0]} and {names[1]}"
            )

        else:
            month_text = (
                ", ".join(
                    names[:-1]
                )
                + f", and {names[-1]}"
            )

        phrases.append(
            f"{kind} in {month_text}"
        )

    return "; ".join(
        phrases
    )


def _fd_auto_sta_label(
    feature,
):
    if FULL_DATA_AUTO_RULES.empty or "Feature" not in FULL_DATA_AUTO_RULES.columns:
        return ""

    rows = FULL_DATA_AUTO_RULES[
        FULL_DATA_AUTO_RULES["Feature"].astype(str) == str(feature)
    ]
    if rows.empty:
        return ""

    rule = rows.iloc[0]
    lower = rule.get("Lower_Auto_STa", np.nan)
    upper = rule.get("Upper_Auto_STa", np.nan)
    parts = []
    if pd.notna(lower):
        parts.append(f"≲{_fd_fmt_num(lower)}")
    if pd.notna(upper):
        parts.append(f"≳{_fd_fmt_num(upper)}")
    if not parts:
        return ""
    return "(STₐ: " + " or ".join(parts) + ")"


def _fd_write_sheet(
    writer,
    df,
    sheet_name,
    index_flag=False,
):
    """
    Match the old workbook structure: region headline in row 1,
    table header in row 2, left-aligned/wrapped body.
    """

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        startrow=1,
        index=index_flag,
    )

    workbook = writer.book
    ws = writer.sheets[
        sheet_name
    ]

    n_cols = (
        df.shape[1]
        +
        (
            1
            if index_flag
            else 0
        )
    )

    n_cols = max(
        n_cols,
        1,
    )

    title_fmt = workbook.add_format({
        "align":
            "center",
        "valign":
            "vcenter",
        "bold":
            True,
    })

    base_fmt = workbook.add_format({
        "align":
            "left",
        "valign":
            "top",
    })

    wrap_fmt = workbook.add_format({
        "align":
            "left",
        "valign":
            "top",
        "text_wrap":
            True,
    })

    if n_cols > 1:
        ws.merge_range(
            0,
            0,
            0,
            n_cols - 1,
            REGION_NAME,
            title_fmt,
        )
    else:
        ws.write(
            0,
            0,
            REGION_NAME,
            title_fmt,
        )

    ws.set_column(
        0,
        n_cols - 1,
        14,
        base_fmt,
    )

    # Similar to the old workbook: keep text-heavy columns readable.
    for col_name in [
        "Compound stress types",
        "STa_Thresholds",
    ]:
        if col_name in df.columns:

            col_idx = (
                df.columns.get_loc(
                    col_name
                )
                +
                (
                    1
                    if index_flag
                    else 0
                )
            )

            ws.set_column(
                col_idx,
                col_idx,
                32,
                wrap_fmt,
            )

    ws.freeze_panes(
        2,
        0,
    )


def build_full_data_alignment_workbook():
    """
    Build the complete FULL-DATA automatic-STa alignment workbook.
    """

    metadata = _fd_get_metadata_from_full_data()

    diagnostic_predictions_path = os.path.join(
        OUTPUT_DIR,
        "full_data_auto_STa_predictions_DIAGNOSTIC.xlsx",
    )
    diagnostic_votes_path = os.path.join(
        OUTPUT_DIR,
        "full_data_auto_STa_feature_vote_details_DIAGNOSTIC.xlsx",
    )

    missing_diagnostics = [
        path
        for path in [diagnostic_predictions_path, diagnostic_votes_path]
        if not os.path.exists(path)
    ]
    if missing_diagnostics:
        raise FileNotFoundError(
            "Full-data F2 diagnostic tables are required before building the "
            "alignment workbook:\n"
            + "\n".join(missing_diagnostics)
        )

    diagnostic_predictions = pd.read_excel(diagnostic_predictions_path)
    diagnostic_votes = pd.read_excel(diagnostic_votes_path)

    full_auto_pred = (
        diagnostic_predictions[
            [
                "Heldout_Year",
                "True_Class",
                "STa_Stress_Hits",
                "STa_Required_Hits",
                "Prediction_FullData_Auto_STa",
            ]
        ]
        .rename(
            columns={
                "STa_Stress_Hits": "FullData_Auto_STa_Stress_Hits",
                "STa_Required_Hits": "FullData_Auto_STa_Required_Hits",
                "Prediction_FullData_Auto_STa":
                    "Prediction_FullData_Auto_STa_on_Heldout",
            }
        )
        .merge(metadata, on="Heldout_Year", how="left")
        .sort_values("Heldout_Year")
        .reset_index(drop=True)
    )

    full_auto_votes = (
        diagnostic_votes[
            [
                "Heldout_Year",
                "Feature",
                "Observed_Value",
                "Auto_STa_Hit",
                "Lower_Auto_STa",
                "Upper_Auto_STa",
            ]
        ]
        .rename(
            columns={
                "Auto_STa_Hit": "FullData_Auto_STa_Hit",
                "Lower_Auto_STa": "Lower_FullData_Auto_STa",
                "Upper_Auto_STa": "Upper_FullData_Auto_STa",
            }
        )
        .merge(
            metadata[["Heldout_Year", "Yield_Class", "Detrended_Yield"]],
            on="Heldout_Year",
            how="left",
        )
    )

    # ========================================================
    # Old-style Data with Alignment table
    # ========================================================

    data_rows = []

    for _, prow in full_auto_pred.iterrows():

        year = int(
            prow[
                "Heldout_Year"
            ]
        )

        year_votes = full_auto_votes[
            full_auto_votes[
                "Heldout_Year"
            ]
            == year
        ].copy()

        out = {
            "Year":
                year,

            "Detrended_Yield":
                prow[
                    "Detrended_Yield"
                ],

            "Yield_Class":
                prow[
                    "Yield_Class"
                ],
        }

        for feature in FIXED_FEATURES:

            fvote = year_votes[
                year_votes[
                    "Feature"
                ]
                == feature
            ]

            if fvote.empty:
                out[
                    feature
                ] = np.nan

                out[
                    f"Align_{feature}"
                ] = np.nan

                continue

            v = fvote.iloc[
                0
            ]

            out[
                feature
            ] = v[
                "Observed_Value"
            ]

            hit_value = v[
                "FullData_Auto_STa_Hit"
            ]

            out[
                f"Align_{feature}"
            ] = (
                int(hit_value)
                if pd.notna(hit_value)
                else np.nan
            )

        out[
            "Total_Align"
        ] = int(
            prow[
                "FullData_Auto_STa_Stress_Hits"
            ]
        )

        out[
            "Aligned (k/n)"
        ] = (
            f"{int(prow['FullData_Auto_STa_Stress_Hits'])}/"
            f"{ORIGINAL_SIGNATURE_K}"
        )

        out[
            "True_Class"
        ] = (
            "Sh"
            if prow[
                "True_Class"
            ]
            == "Sh"
            else "NSh"
        )

        out[
            "Predicted_Class"
        ] = prow[
            "Prediction_FullData_Auto_STa_on_Heldout"
        ]

        out[
            "True_Class_Binary"
        ] = (
            1
            if out[
                "True_Class"
            ]
            == "Sh"
            else 0
        )

        out[
            "Predicted_Class_Binary"
        ] = (
            1
            if out[
                "Predicted_Class"
            ]
            == "Sh"
            else 0
        )

        out[
            "Prediction_Correct"
        ] = int(
            out[
                "True_Class_Binary"
            ]
            ==
            out[
                "Predicted_Class_Binary"
            ]
        )

        # Compatibility with the old workbook.
        out[
            "Alignment"
        ] = out[
            "Prediction_Correct"
        ]

        out[
            "Compound stress types"
        ] = _fd_compound_stress_types(
            year_votes
        )

        data_rows.append(
            out
        )

    data_all = (
        pd.DataFrame(
            data_rows
        )
        .sort_values(
            "Year"
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Class Counts
    # ========================================================

    class_counts = (
        data_all[
            "Yield_Class"
        ]
        .value_counts()
        .reindex(
            [
                "Bo",
                "No",
                "Sh",
            ]
        )
        .fillna(
            0
        )
        .astype(
            int
        )
        .rename(
            "Count"
        )
        .to_frame()
    )

    class_counts.index.name = (
        "Yield_Class"
    )

    # ========================================================
    # Alignment Summary
    # ========================================================

    alignment_rows = []

    for cls in [
        "Bo",
        "No",
        "Sh",
    ]:

        subset = data_all[
            data_all[
                "Yield_Class"
            ]
            == cls
        ]

        row = {}

        for feature in FIXED_FEATURES:

            hits = pd.to_numeric(
                subset[
                    f"Align_{feature}"
                ],
                errors="coerce",
            ).dropna()

            if hits.empty:
                row[
                    feature
                ] = np.nan

            elif cls == "Sh":
                row[
                    feature
                ] = (
                    hits.mean()
                    * 100.0
                )

            else:
                row[
                    feature
                ] = (
                    (
                        1.0
                        - hits
                    )
                    .mean()
                    * 100.0
                )

        alignment_rows.append(
            pd.Series(
                row,
                name=cls,
            )
        )

    # Old workbook used observation-weighted overall alignment.
    overall_row = {}

    for feature in FIXED_FEATURES:

        hit = pd.to_numeric(
            data_all[
                f"Align_{feature}"
            ],
            errors="coerce",
        )

        valid = hit.notna()

        class_is_sh = (
            data_all[
                "Yield_Class"
            ]
            == "Sh"
        )

        class_aligned = np.where(
            class_is_sh,
            hit,
            1.0 - hit,
        )

        overall_row[
            feature
        ] = (
            np.nanmean(
                np.where(
                    valid,
                    class_aligned,
                    np.nan,
                )
            )
            * 100.0
        )

    alignment_summary = pd.DataFrame(
        alignment_rows
        +
        [
            pd.Series(
                overall_row,
                name="Overall",
            )
        ]
    )

    alignment_summary.loc[
        [
            "Bo",
            "No",
            "Sh",
        ]
    ] = (
        alignment_summary.loc[
            [
                "Bo",
                "No",
                "Sh",
            ]
        ]
        .round(
            1
        )
    )

    alignment_summary.loc[
        "Overall"
    ] = np.ceil(
        alignment_summary.loc[
            "Overall"
        ]
    )

    alignment_summary.index.name = (
        "Yield_Class"
    )

    # ========================================================
    # Per Class Accuracy + Overall Accuracy
    # ========================================================

    per_class_acc_rows = []

    for cls in [
        "Bo",
        "No",
        "Sh",
    ]:

        subset = data_all[
            data_all[
                "Yield_Class"
            ]
            == cls
        ]

        if subset.empty:
            value = np.nan

        else:
            value = (
                subset[
                    "Prediction_Correct"
                ]
                .mean()
                * 100.0
            )

        per_class_acc_rows.append({
            "Yield_Class":
                cls,

            "Per Class Accuracy (%)":
                (
                    round(
                        value,
                        1,
                    )
                    if pd.notna(
                        value
                    )
                    else np.nan
                ),
        })

    per_class_acc_df = (
        pd.DataFrame(
            per_class_acc_rows
        )
        .set_index(
            "Yield_Class"
        )
    )

    overall_acc_df = pd.DataFrame({
        "Overall Accuracy (%)": [
            round(
                data_all[
                    "Prediction_Correct"
                ]
                .mean()
                * 100.0,
                1,
            )
        ]
    })

    # ========================================================
    # Binary Sh metrics + classification report
    # ========================================================

    y_true = (
        data_all[
            "True_Class_Binary"
        ]
        .astype(
            int
        )
    )

    y_pred = (
        data_all[
            "Predicted_Class_Binary"
        ]
        .astype(
            int
        )
    )

    metrics_df = pd.DataFrame({
        "Metric": [
            "Accuracy",
            "Precision",
            "Recall",
            "F1-Score",
        ],

        "Value": [
            accuracy_score(
                y_true,
                y_pred,
            ),

            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            ),

            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            ),

            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            ),
        ],
    })

    class_report_df = (
        pd.DataFrame(
            classification_report(
                y_true,
                y_pred,
                target_names=[
                    "NSh",
                    "Sh",
                ],
                output_dict=True,
                zero_division=0,
            )
        )
        .transpose()
    )

    # ========================================================
    # Pretty Per-Year tables
    # ========================================================

    feature_headers = {
        feature:
            (
                f"{feature}\n"
                f"{_fd_auto_sta_label(feature)}"
            )
        for feature in FIXED_FEATURES
    }

    display_rows = []

    for _, row in data_all.iterrows():

        out = {
            "Year":
                int(
                    row[
                        "Year"
                    ]
                ),

            "Detrended_Yield":
                row[
                    "Detrended_Yield"
                ],
        }

        for feature in FIXED_FEATURES:

            value = row[
                feature
            ]

            hit = row[
                f"Align_{feature}"
            ]

            shown = _fd_fmt_num(
                value
            )

            if (
                pd.notna(
                    hit
                )
                and
                int(
                    hit
                )
                == 1
            ):
                shown += " ✓"

            out[
                feature_headers[
                    feature
                ]
            ] = shown

        out[
            "Aligned (k/n)"
        ] = row[
            "Aligned (k/n)"
        ]

        out[
            "Compound stress types"
        ] = row[
            "Compound stress types"
        ]

        out[
            "Yield_Class"
        ] = row[
            "Yield_Class"
        ]

        display_rows.append(
            out
        )

    per_year_all = pd.DataFrame(
        display_rows
    )

    per_year_sh = (
        per_year_all[
            per_year_all[
                "Yield_Class"
            ]
            == "Sh"
        ]
        .drop(
            columns=[
                "Yield_Class"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Dominant stress types
    # ========================================================

    label_to_code = {
        "wet-persistence":
            "+P",
        "precipitation-excess":
            "+P",
        "dry-persistence":
            "-P",
        "precipitation-deficit":
            "-P",
        "heatwave":
            "+T",
        "warm-spell deficit":
            "+T",
        "cold-wave":
            "-T",
        "chilling-deficit":
            "-T",
    }

    dom_counts = {
        "+P": 0,
        "-P": 0,
        "-T": 0,
        "+T": 0,
    }

    for entry in (
        per_year_sh[
            "Compound stress types"
        ]
        .dropna()
        .astype(
            str
        )
    ):

        for item in [
            x.strip()
            for x in entry.split(
                ";"
            )
            if x.strip()
        ]:

            label = (
                item.split(
                    " in "
                )[0]
                .strip()
            )

            code_name = (
                label_to_code.get(
                    label
                )
            )

            if code_name is not None:
                dom_counts[
                    code_name
                ] += 1

    total_dom = sum(
        dom_counts.values()
    )

    dom_df = pd.DataFrame([
        {
            "Region":
                REGION_NAME,

            "Code":
                code_name,

            "Count":
                dom_counts[
                    code_name
                ],

            "Share_%":
                (
                    round(
                        (
                            dom_counts[
                                code_name
                            ]
                            /
                            total_dom
                            *
                            100.0
                        ),
                        1,
                    )
                    if total_dom > 0
                    else 0.0
                ),
        }
        for code_name in [
            "+P",
            "-P",
            "-T",
            "+T",
        ]
    ])

    # ========================================================
    # STa Summary
    # ========================================================

    sta_expressions = []

    for feature in FIXED_FEATURES:
        if FULL_DATA_AUTO_RULES.empty or "Feature" not in FULL_DATA_AUTO_RULES.columns:
            continue
        rows = FULL_DATA_AUTO_RULES[
            FULL_DATA_AUTO_RULES["Feature"].astype(str) == str(feature)
        ]
        if rows.empty:
            continue
        rule = rows.iloc[0]
        lower = rule.get("Lower_Auto_STa", np.nan)
        upper = rule.get("Upper_Auto_STa", np.nan)
        pieces = []
        if pd.notna(lower):
            pieces.append(f"{feature} ≲{_fd_fmt_num(lower)}")
        if pd.notna(upper):
            pieces.append(f"{feature} ≳{_fd_fmt_num(upper)}")
        if pieces:
            sta_expressions.append(" or ".join(pieces))

    sta_summary_df = pd.DataFrame(
        [
            [
                REGION_NAME,
                ", ".join(
                    sta_expressions
                ),
            ]
        ],
        columns=[
            "Region",
            "STa_Thresholds",
        ],
    )

    # ========================================================
    # Output file name includes country_crop
    # ========================================================

    country_crop_tag = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        str(
            REGION_NAME
        ),
    ).strip(
        "_"
    )

    workbook_path = os.path.join(
        OUTPUT_DIR,
        (
            f"{country_crop_tag}"
            "_alignment_results_with_metrics.xlsx"
        ),
    )

    # ========================================================
    # Write ONLY the old-style information
    # ========================================================

    with pd.ExcelWriter(
        workbook_path,
        engine="xlsxwriter",
    ) as writer:

        _fd_write_sheet(
            writer,
            class_counts,
            "Class Counts",
            index_flag=True,
        )

        _fd_write_sheet(
            writer,
            per_year_sh,
            "Per-Year (Sh)",
            index_flag=False,
        )

        _fd_write_sheet(
            writer,
            per_year_all,
            "Per-Year (All)",
            index_flag=False,
        )

        _fd_write_sheet(
            writer,
            alignment_summary,
            "Alignment Summary",
            index_flag=True,
        )

        _fd_write_sheet(
            writer,
            per_class_acc_df,
            "Per Class Accuracy",
            index_flag=True,
        )

        _fd_write_sheet(
            writer,
            overall_acc_df,
            "Overall Accuracy",
            index_flag=False,
        )

        _fd_write_sheet(
            writer,
            data_all,
            "Data with Alignment",
            index_flag=False,
        )

        _fd_write_sheet(
            writer,
            metrics_df,
            "Sh class_Metrics",
            index_flag=False,
        )

        _fd_write_sheet(
            writer,
            class_report_df,
            "Classification Report",
            index_flag=True,
        )

        _fd_write_sheet(
            writer,
            dom_df,
            "Dominant stress types",
            index_flag=False,
        )

        _fd_write_sheet(
            writer,
            sta_summary_df,
            "STa Summary",
            index_flag=False,
        )

        # As in the old workbook, add the dominant-stress share line
        # below the Sh-year table.
        ws_sh = writer.sheets[
            "Per-Year (Sh)"
        ]

        workbook = writer.book

        bold_wrap = workbook.add_format({
            "bold":
                True,
            "text_wrap":
                True,
            "align":
                "left",
            "valign":
                "top",
        })

        normal_wrap = workbook.add_format({
            "text_wrap":
                True,
            "align":
                "left",
            "valign":
                "top",
        })

        parts = []

        for code_name in [
            "+P",
            "-P",
            "-T",
            "+T",
        ]:

            row = dom_df[
                dom_df[
                    "Code"
                ]
                == code_name
            ]

            if row.empty:
                continue

            share = float(
                row[
                    "Share_%"
                ].iloc[
                    0
                ]
            )

            share_text = (
                str(
                    int(
                        share
                    )
                )
                if float(
                    share
                ).is_integer()
                else f"{share:.1f}"
            )

            parts.append(
                f"{code_name} ({share_text})"
            )

        if (
            "Compound stress types"
            in per_year_sh.columns
        ):

            compound_col = (
                per_year_sh.columns.get_loc(
                    "Compound stress types"
                )
            )

            summary_row = (
                1
                +
                len(
                    per_year_sh
                )
                +
                2
            )

            ws_sh.write_rich_string(
                summary_row,
                compound_col,
                bold_wrap,
                "Dominant stress types (%): ",
                normal_wrap,
                ", ".join(
                    parts
                ),
            )

    print(
        "\nFULL-DATA alignment workbook saved:"
    )

    print(
        workbook_path
    )

    return workbook_path




# ============================================================
# FULL-DATA AUTOMATIC STa DIAGNOSTIC
# ============================================================

full_data_auto_result = (
    evaluate_full_data_auto_sta()
)

FULL_DATA_ALIGNMENT_WORKBOOK = (
    build_full_data_alignment_workbook()
    if (
        RUN_FULL_DATA
        and full_data_auto_result is not None
        and not FULL_DATA_AUTO_RULES.empty
    )
    else None
)


# ============================================================
# Compact confusion matrix
# ============================================================

def save_confusion_matrix(
    result,
    filename,
):

    cm = result[
        "Confusion_Matrix"
    ]

    fig = plt.figure(
        figsize=(
            2.35,
            2.75,
        )
    )

    MATRIX_LEFT = 0.24
    MATRIX_BOTTOM = 0.39
    MATRIX_WIDTH = 0.43
    MATRIX_HEIGHT = 0.43

    MATRIX_CENTER_X = (
        MATRIX_LEFT
        + MATRIX_WIDTH / 2
    )

    ax = fig.add_axes([
        MATRIX_LEFT,
        MATRIX_BOTTOM,
        MATRIX_WIDTH,
        MATRIX_HEIGHT,
    ])

    image = ax.imshow(
        cm,
        interpolation="nearest",
        cmap="Blues",
    )

    divider = make_axes_locatable(
        ax
    )

    cax = divider.append_axes(
        "right",
        size="4%",
        pad=0.03,
    )

    cbar = fig.colorbar(
        image,
        cax=cax,
    )

    cbar.ax.tick_params(
        labelsize=CBAR_FS,
        length=1.8,
        width=0.6,
    )

    ax.set_xticks(
        [0, 1]
    )

    ax.set_yticks(
        [0, 1]
    )

    ax.set_xticklabels(
        ["NSh", "Sh"],
        fontsize=CLASS_FS,
        fontweight="bold",
    )

    ax.set_yticklabels(
        ["NSh", "Sh"],
        fontsize=CLASS_FS,
        fontweight="bold",
    )

    ax.tick_params(
        axis="both",
        length=2.5,
        width=0.7,
        pad=2.5,
    )

    threshold = (
        cm.max() / 2.0
        if cm.size > 0
        else 0
    )

    for i in range(
        cm.shape[0]
    ):
        for j in range(
            cm.shape[1]
        ):
            value = int(
                cm[i, j]
            )

            text_color = (
                "white"
                if value > threshold
                else "#08306b"
            )

            ax.text(
                j,
                i,
                str(value),
                ha="center",
                va="center",
                fontsize=NUMBER_FS,
                fontweight="bold",
                color=text_color,
            )

    ax.set_ylabel(
        "True",
        fontsize=AXIS_FS,
        fontweight="bold",
        labelpad=4,
    )

    ax.set_xlabel(
        "Predicted",
        fontsize=AXIS_FS,
        fontweight="bold",
        labelpad=2,
    )

    fig.text(
        MATRIX_CENTER_X,
        0.80,
        REGION_NAME,
        ha="center",
        va="center",
        fontsize=TITLE_FS,
        fontweight="bold",
    )

    # Show TFY only when true-Sh exact-half years exist.
    tfy_years = result.get(
        "TFY",
        [],
    )

    if len(tfy_years) > 0:
        fig.text(
            MATRIX_CENTER_X,
            0.315,
            "TFY: "
            + ", ".join(
                str(
                    int(year)
                )
                for year in tfy_years
            ),
            ha="center",
            va="center",
            fontsize=META_FS,
        )

    # Weighted F1 is always displayed.
    fig.text(
        MATRIX_CENTER_X,
        0.245,
        f"(F1: {result['F1_Weighted']:.2f})",
        ha="center",
        va="center",
        fontsize=META_FS,
    )

    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_linewidth(
            0.7
        )

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            filename,
        ),
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.02,
    )

    plt.close()


# Country-crop tag for confusion-matrix filenames.
# Example:
#   REGION_NAME = "ALB-Potato"
#   -> ALB_Potato_fixed_signature_fold_auto_STa.png
COUNTRY_CROP_TAG = re.sub(
    r"[^A-Za-z0-9]+",
    "_",
    str(REGION_NAME),
).strip("_")


if RUN_LOYO:
    save_confusion_matrix(
        results[0],
        f"{COUNTRY_CROP_TAG}_fixed_signature_fold_STi.png",
    )

    save_confusion_matrix(
        results[1],
        f"{COUNTRY_CROP_TAG}_fixed_signature_fold_auto_STa.png",
    )

if full_data_auto_result is not None:

    save_confusion_matrix(
        full_data_auto_result,
        f"{COUNTRY_CROP_TAG}_full_data_automatic_STa_DIAGNOSTIC.png",
    )


print("\n" + "=" * 105)
print(
    f"{REGION_NAME} FIXED-SIGNATURE LOYO | "
    "FIXED AUTOMATIC-SIGNATURE DENOMINATOR"
)
print("=" * 105)

print(
    f"\nAutomatic signature k = "
    f"{ORIGINAL_SIGNATURE_K}"
)

print(
    f"Fixed required hits (>50%) = "
    f"{ORIGINAL_REQUIRED_HITS}"
)

print(
    f"Minimum actually valid features for evaluability = "
    f"{MIN_VALID_FEATURES}"
)

print(
    "\nVoting rule:"
)

print(
    "Sh if stress_hits > 50% of automatic_signature_k"
)

print(
    "Unknown/NA partial votes do NOT shrink the denominator."
)

if RUN_LOYO:
    print(
        "\n"
        + summary.to_string(
            index=False
        )
    )

if full_data_auto_result is not None:

    print(
        "\nFULL-DATA AUTOMATIC STa DIAGNOSTIC "
        "(not independent):"
    )

    print(
        "  TN={TN}, FP={FP}, FN={FN}, TP={TP}, "
        "F1_weighted={F1:.3f}, "
        "Sensitivity_Sh={Sens:.3f}, "
        "Specificity={Spec:.3f}".format(
            TN=
                full_data_auto_result[
                    "TN"
                ],
            FP=
                full_data_auto_result[
                    "FP"
                ],
            FN=
                full_data_auto_result[
                    "FN"
                ],
            TP=
                full_data_auto_result[
                    "TP"
                ],
            F1=
                full_data_auto_result[
                    "F1_Weighted"
                ],
            Sens=
                full_data_auto_result[
                    "Sensitivity_Sh"
                ],
            Spec=
                full_data_auto_result[
                    "Specificity"
                ],
        )
    )

print("\n" + "=" * 105)
print(f"Results saved in:\n{OUTPUT_DIR}")
