"""
Data harmonization module for multi-center clinical datasets.

Standardizes heterogeneous clinical data from multiple sites into
a unified, analysis-ready format:
- Date format standardization
- Unit conversion (imperial → metric)
- Categorical coding harmonization
- Duplicate removal
- Impossible value handling

Each transformation is logged for full traceability.

Author: Zahia Yanes
"""

import pandas as pd
import numpy as np
from datetime import datetime


class HarmonizationLog:
    """
    Tracks all transformations applied during harmonization.

    Provides full traceability of every change made to the data,
    which is essential for clinical data audit trails.
    """

    def __init__(self):
        self.transformations = []

    def log(self, step, n_affected, details):
        """
        Record a transformation step.

        Parameters
        ----------
        step : str
            Name of the harmonization step.
        n_affected : int
            Number of records modified.
        details : str
            Human-readable description of the change.
        """
        self.transformations.append({
            "step": step,
            "n_affected": n_affected,
            "details": details,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def summary(self):
        """Print a formatted summary of all transformations."""
        print(f"\n{'='*60}")
        print(f"  HARMONIZATION LOG")
        print(f"{'='*60}")
        print(f"  Total steps: {len(self.transformations)}")
        print(f"{'='*60}")

        for i, t in enumerate(self.transformations, 1):
            print(f"\n  Step {i}: {t['step']}")
            print(f"    Affected: {t['n_affected']} records")
            print(f"    Details: {t['details']}")

    def to_dataframe(self):
        """Convert log to DataFrame."""
        return pd.DataFrame(self.transformations)


def remove_duplicates(df, log, subset=None):
    """
    Remove duplicate records, keeping the first occurrence.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    log : HarmonizationLog
        Log to record the transformation.
    subset : list, optional
        Columns to check for duplicates. Defaults to ["patient_id"].

    Returns
    -------
    pd.DataFrame
        Dataset with duplicates removed.
    """
    if subset is None:
        subset = ["patient_id"]

    n_before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
    n_removed = n_before - len(df)

    log.log(
        step="Remove duplicates",
        n_affected=n_removed,
        details=f"Removed {n_removed} duplicate records based on {subset}",
    )

    return df


def fix_impossible_values(df, log):
    """
    Handle impossible/out-of-range values by setting them to NaN.

    Clinical rationale:
    - Negative age, weight, creatinine → data entry error
    - Zero weight → data entry error
    - These cannot be imputed reliably, so we set to NaN

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    log : HarmonizationLog
        Log to record the transformation.

    Returns
    -------
    pd.DataFrame
        Dataset with impossible values replaced by NaN.
    """
    df = df.copy()
    total_fixed = 0

    # Age < 0 or > 120
    mask = (df["age"] < 0) | (df["age"] > 120)
    n_fixed = mask.sum()
    if n_fixed > 0:
        df.loc[mask, "age"] = np.nan
        total_fixed += n_fixed

    # Weight <= 0
    mask = df["weight"] <= 0
    n_fixed = mask.sum()
    if n_fixed > 0:
        df.loc[mask, "weight"] = np.nan
        total_fixed += n_fixed

    # Creatinine < 0
    mask = df["creatinine"] < 0
    n_fixed = mask.sum()
    if n_fixed > 0:
        df.loc[mask, "creatinine"] = np.nan
        total_fixed += n_fixed

    log.log(
        step="Fix impossible values",
        n_affected=total_fixed,
        details=f"Set {total_fixed} impossible values to NaN (negative age/weight/creatinine)",
    )

    return df


def standardize_dates(df, log, date_col="enrollment_date"):
    """
    Parse all date formats and standardize to ISO format (YYYY-MM-DD).

    Handles:
    - DD/MM/YYYY (European, Site A)
    - MM/DD/YYYY (American, Site B)
    - YYYY-MM-DD (ISO, Site C)

    Strategy: use the site column to determine the format,
    since date parsing is ambiguous (e.g., 05/04/2022).

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    log : HarmonizationLog
        Log to record the transformation.
    date_col : str
        Name of the date column.

    Returns
    -------
    pd.DataFrame
        Dataset with standardized dates.
    """
    df = df.copy()

    site_formats = {
        "Site_A": "%d/%m/%Y",
        "Site_B": "%m/%d/%Y",
        "Site_C": "%Y-%m-%d",
    }

    parsed_dates = []
    n_converted = 0

    for _, row in df.iterrows():
        date_str = row[date_col]
        site = row["site"]
        fmt = site_formats.get(site)

        try:
            parsed = datetime.strptime(date_str, fmt)
            parsed_dates.append(parsed.strftime("%Y-%m-%d"))
            n_converted += 1
        except (ValueError, TypeError):
            parsed_dates.append(None)

    df[date_col] = parsed_dates

    log.log(
        step="Standardize dates",
        n_affected=n_converted,
        details=f"Converted {n_converted} dates to ISO format (YYYY-MM-DD)",
    )

    return df


def flag_future_dates(df, log, date_col="enrollment_date"):
    """
    Flag records with future enrollment dates.

    Does not remove them — flags for manual review.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    log : HarmonizationLog
        Log to record the transformation.
    date_col : str
        Name of the date column.

    Returns
    -------
    pd.DataFrame
        Dataset with 'future_date_flag' column added.
    """
    df = df.copy()
    today = datetime.now().strftime("%Y-%m-%d")
    df["future_date_flag"] = df[date_col] > today

    n_future = df["future_date_flag"].sum()

    log.log(
        step="Flag future dates",
        n_affected=n_future,
        details=f"Flagged {n_future} records with enrollment dates in the future",
    )

    return df


def standardize_gender(df, log):
    """
    Harmonize gender coding to M/F.

    Mapping:
    - "Male", "m" → "M"
    - "Female", "f" → "F"

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    log : HarmonizationLog
        Log to record the transformation.

    Returns
    -------
    pd.DataFrame
        Dataset with standardized gender coding.
    """
    df = df.copy()

    gender_map = {
        "M": "M", "Male": "M", "m": "M",
        "F": "F", "Female": "F", "f": "F",
    }

    n_before = df["gender"].nunique()
    df["gender"] = df["gender"].map(gender_map)
    n_after = df["gender"].nunique()

    log.log(
        step="Standardize gender",
        n_affected=len(df),
        details=f"Harmonized {n_before} gender codings to {n_after} (M/F)",
    )

    return df


def standardize_stage(df, log):
    """
    Harmonize tumor stage to Roman numerals (I, II, III, IV).

    Mapping:
    - 1, "Stage I" → "I"
    - 2, "Stage II" → "II"
    - etc.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    log : HarmonizationLog
        Log to record the transformation.

    Returns
    -------
    pd.DataFrame
        Dataset with standardized stage coding.
    """
    df = df.copy()

    stage_map = {
        "I": "I", "II": "II", "III": "III", "IV": "IV",
        1: "I", 2: "II", 3: "III", 4: "IV",
        "Stage I": "I", "Stage II": "II",
        "Stage III": "III", "Stage IV": "IV",
    }

    n_before = df["tumor_stage"].nunique()
    df["tumor_stage"] = df["tumor_stage"].map(stage_map)
    n_after = df["tumor_stage"].nunique()

    log.log(
        step="Standardize tumor stage",
        n_affected=len(df),
        details=f"Harmonized {n_before} stage codings to {n_after} (I/II/III/IV)",
    )

    return df


def standardize_treatment(df, log):
    """
    Harmonize treatment names to title case.

    Example: "pembrolizumab", "PEMBROLIZUMAB" → "Pembrolizumab"

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    log : HarmonizationLog
        Log to record the transformation.

    Returns
    -------
    pd.DataFrame
        Dataset with standardized treatment names.
    """
    df = df.copy()

    n_before = df["treatment"].nunique()
    df["treatment"] = df["treatment"].str.title()
    n_after = df["treatment"].nunique()

    log.log(
        step="Standardize treatment names",
        n_affected=len(df),
        details=f"Harmonized {n_before} treatment names to {n_after} (title case)",
    )

    return df


def convert_units(df, log):
    """
    Convert imperial units to metric.

    Conversions:
    - Weight: lbs → kg (1 lb = 0.4536 kg)
    - Height: inches → cm (1 in = 2.54 cm)

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    log : HarmonizationLog
        Log to record the transformation.

    Returns
    -------
    pd.DataFrame
        Dataset with all measurements in metric units.
    """
    df = df.copy()

    # Weight: lbs → kg
    lbs_mask = df["weight_unit"] == "lbs"
    n_weight = lbs_mask.sum()
    df.loc[lbs_mask, "weight"] = np.round(df.loc[lbs_mask, "weight"] * 0.4536, 1)
    df.loc[lbs_mask, "weight_unit"] = "kg"

    # Height: inches → cm
    in_mask = df["height_unit"] == "in"
    n_height = in_mask.sum()
    df.loc[in_mask, "height"] = np.round(df.loc[in_mask, "height"] * 2.54, 1)
    df.loc[in_mask, "height_unit"] = "cm"

    log.log(
        step="Convert units to metric",
        n_affected=n_weight + n_height,
        details=f"Converted {n_weight} weights (lbs→kg) and {n_height} heights (in→cm)",
    )

    return df


def harmonize(df):
    """
    Run the full harmonization pipeline.

    Applies all standardization steps in the correct order:
    1. Remove duplicates
    2. Fix impossible values
    3. Standardize dates
    4. Flag future dates
    5. Standardize gender
    6. Standardize tumor stage
    7. Standardize treatment names
    8. Convert units to metric

    Parameters
    ----------
    df : pd.DataFrame
        Raw multi-center dataset.

    Returns
    -------
    tuple[pd.DataFrame, HarmonizationLog]
        Harmonized dataset and transformation log.
    """
    log = HarmonizationLog()

    print("🔧 Running harmonization pipeline...\n")

    n_before = len(df)
    df = remove_duplicates(df, log)
    df = fix_impossible_values(df, log)
    df = standardize_dates(df, log)
    df = flag_future_dates(df, log)
    df = standardize_gender(df, log)
    df = standardize_stage(df, log)
    df = standardize_treatment(df, log)
    df = convert_units(df, log)

    print(f"\n✅ Harmonization complete: {n_before} → {len(df)} records")

    log.summary()

    return df, log


if __name__ == "__main__":
    from data_simulator import generate_all_sites
    from qc_checks import run_all_checks

    # Generate raw data
    print("=" * 60)
    print("  STEP 1: Generate raw data")
    print("=" * 60)
    df_raw = generate_all_sites()

    # QC before harmonization
    print("\n" + "=" * 60)
    print("  STEP 2: QC before harmonization")
    print("=" * 60)
    report_before = run_all_checks(df_raw, "Raw multi-center data")

    # Harmonize
    print("\n" + "=" * 60)
    print("  STEP 3: Harmonize")
    print("=" * 60)
    df_clean, harm_log = harmonize(df_raw)

    # QC after harmonization
    print("\n" + "=" * 60)
    print("  STEP 4: QC after harmonization")
    print("=" * 60)
    report_after = run_all_checks(df_clean, "Harmonized data")

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    n_before = len(report_before.issues)
    n_after = len(report_after.issues)
    print(f"  Issues before: {n_before}")
    print(f"  Issues after:  {n_after}")
    print(f"  Issues resolved: {n_before - n_after}")