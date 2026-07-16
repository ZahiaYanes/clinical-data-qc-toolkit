"""
Quality control checks for multi-center clinical datasets.

Implements automated detection of common data quality issues:
- Missing values analysis
- Duplicate detection
- Impossible/out-of-range values
- Date validation
- Consistency checks across sites

Each check returns a structured report with the issue type,
severity, affected records, and suggested action.

Author: Zahia Yanes
"""

import pandas as pd
import numpy as np
from datetime import datetime


class QualityReport:
    """
    Container for quality control results.

    Stores all detected issues and provides summary statistics.
    """

    def __init__(self, dataset_name="dataset"):
        self.dataset_name = dataset_name
        self.issues = []
        self.total_records = 0
        self.total_variables = 0

    def add_issue(self, check_name, severity, n_affected, details, affected_ids=None):
        """
        Record a detected quality issue.

        Parameters
        ----------
        check_name : str
            Name of the QC check that found the issue.
        severity : str
            One of "CRITICAL", "WARNING", "INFO".
        n_affected : int
            Number of records affected.
        details : str
            Human-readable description of the issue.
        affected_ids : list, optional
            List of affected patient IDs.
        """
        self.issues.append({
            "check": check_name,
            "severity": severity,
            "n_affected": n_affected,
            "details": details,
            "affected_ids": affected_ids or [],
        })

    def summary(self):
        """Print a formatted summary of all detected issues."""
        critical = [i for i in self.issues if i["severity"] == "CRITICAL"]
        warnings = [i for i in self.issues if i["severity"] == "WARNING"]
        info = [i for i in self.issues if i["severity"] == "INFO"]

        print(f"\n{'='*60}")
        print(f"  QUALITY CONTROL REPORT — {self.dataset_name}")
        print(f"{'='*60}")
        print(f"  Records scanned:  {self.total_records}")
        print(f"  Variables:        {self.total_variables}")
        print(f"  Issues found:     {len(self.issues)}")
        print(f"    🔴 CRITICAL:    {len(critical)}")
        print(f"    🟡 WARNING:     {len(warnings)}")
        print(f"    🔵 INFO:        {len(info)}")
        print(f"{'='*60}")

        for issue in self.issues:
            icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}[issue["severity"]]
            print(f"\n  {icon} [{issue['severity']}] {issue['check']}")
            print(f"     Affected: {issue['n_affected']} records")
            print(f"     Details: {issue['details']}")
            if issue["affected_ids"]:
                ids_preview = issue["affected_ids"][:5]
                suffix = f" ... (+{len(issue['affected_ids'])-5} more)" if len(issue["affected_ids"]) > 5 else ""
                print(f"     IDs: {ids_preview}{suffix}")

    def to_dataframe(self):
        """Convert issues to a DataFrame for further analysis."""
        return pd.DataFrame(self.issues)


def check_missing_values(df, report, threshold=0.05):
    """
    Check for missing values in each column.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    report : QualityReport
        Report to append issues to.
    threshold : float
        Fraction above which missing data triggers a WARNING.
    """
    for col in df.columns:
        n_missing = df[col].isnull().sum()
        if n_missing > 0:
            pct = n_missing / len(df) * 100
            severity = "WARNING" if pct > threshold * 100 else "INFO"

            affected_ids = df[df[col].isnull()]["patient_id"].tolist()

            report.add_issue(
                check_name=f"Missing values: {col}",
                severity=severity,
                n_affected=n_missing,
                details=f"{n_missing} missing values ({pct:.1f}%) in column '{col}'",
                affected_ids=affected_ids,
            )


def check_duplicates(df, report, subset=None):
    """
    Check for duplicate records.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    report : QualityReport
        Report to append issues to.
    subset : list, optional
        Columns to consider for duplicate detection.
        Defaults to ["patient_id"].
    """
    if subset is None:
        subset = ["patient_id"]

    duplicates = df[df.duplicated(subset=subset, keep=False)]
    n_duplicates = len(duplicates) - duplicates.drop_duplicates(subset=subset).shape[0]

    if n_duplicates > 0:
        affected_ids = duplicates["patient_id"].unique().tolist()
        report.add_issue(
            check_name="Duplicate records",
            severity="CRITICAL",
            n_affected=n_duplicates,
            details=f"{n_duplicates} duplicate records found based on {subset}",
            affected_ids=affected_ids,
        )


def check_value_ranges(df, report):
    """
    Check for impossible or out-of-range values.

    Validates:
    - Age: 0-120 years
    - Weight: > 0
    - Height: > 0
    - Hemoglobin: 3-25 g/dL
    - Creatinine: 0-15 mg/dL
    - LDH: 50-10000 U/L

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    report : QualityReport
        Report to append issues to.
    """
    range_checks = {
        "age": {"min": 0, "max": 120, "label": "Age (years)"},
        "weight": {"min": 0.1, "max": 500, "label": "Weight"},
        "height": {"min": 10, "max": 250, "label": "Height"},
        "hemoglobin": {"min": 3, "max": 25, "label": "Hemoglobin (g/dL)"},
        "creatinine": {"min": 0, "max": 15, "label": "Creatinine (mg/dL)"},
        "ldh": {"min": 50, "max": 10000, "label": "LDH (U/L)"},
    }

    for col, rules in range_checks.items():
        if col not in df.columns:
            continue

        invalid = df[
            (df[col].notna()) &
            ((df[col] < rules["min"]) | (df[col] > rules["max"]))
        ]

        if len(invalid) > 0:
            values = invalid[col].tolist()
            affected_ids = invalid["patient_id"].tolist()
            report.add_issue(
                check_name=f"Out of range: {rules['label']}",
                severity="CRITICAL",
                n_affected=len(invalid),
                details=f"{len(invalid)} values outside [{rules['min']}, {rules['max']}]: {values[:5]}",
                affected_ids=affected_ids,
            )


def check_dates(df, report, date_col="enrollment_date"):
    """
    Check for date issues: future dates and inconsistent formats.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    report : QualityReport
        Report to append issues to.
    date_col : str
        Name of the date column.
    """
    if date_col not in df.columns:
        return

    # Detect date formats per site
    formats_found = {}
    for site in df["site"].unique():
        sample = df[df["site"] == site][date_col].iloc[0]
        formats_found[site] = sample

    if len(set(formats_found.values())) > 1:
        format_details = ", ".join([f"{k}: '{v}'" for k, v in formats_found.items()])
        report.add_issue(
            check_name="Inconsistent date formats",
            severity="WARNING",
            n_affected=len(df),
            details=f"Different date formats across sites: {format_details}",
        )

    # Try to parse and find future dates
    today = datetime.now()
    future_dates = []

    for idx, row in df.iterrows():
        date_str = row[date_col]
        parsed = None

        for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"]:
            try:
                parsed = datetime.strptime(date_str, fmt)
                break
            except (ValueError, TypeError):
                continue

        if parsed and parsed > today:
            future_dates.append(row["patient_id"])

    if future_dates:
        report.add_issue(
            check_name="Future dates",
            severity="CRITICAL",
            n_affected=len(future_dates),
            details=f"{len(future_dates)} enrollment dates are in the future",
            affected_ids=future_dates,
        )


def check_categorical_consistency(df, report):
    """
    Check for inconsistent categorical coding across sites.

    Checks:
    - Gender coding (M/F vs Male/Female vs m/f)
    - Tumor stage coding (I/II vs 1/2 vs Stage I/Stage II)
    - Treatment name casing

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    report : QualityReport
        Report to append issues to.
    """
    # Gender consistency
    if "gender" in df.columns:
        unique_genders = df["gender"].unique().tolist()
        if len(unique_genders) > 2:
            report.add_issue(
                check_name="Inconsistent gender coding",
                severity="WARNING",
                n_affected=len(df),
                details=f"Multiple gender codings found: {sorted(unique_genders)}",
            )

    # Stage consistency
    if "tumor_stage" in df.columns:
        unique_stages = df["tumor_stage"].unique().tolist()
        unique_types = set(type(s).__name__ for s in unique_stages)
        if len(unique_types) > 1 or len(unique_stages) > 4:
            report.add_issue(
                check_name="Inconsistent stage coding",
                severity="WARNING",
                n_affected=len(df),
                details=f"Multiple stage codings found: {sorted(str(s) for s in unique_stages)}",
            )

    # Treatment consistency
    if "treatment" in df.columns:
        unique_treatments = df["treatment"].unique().tolist()
        lower_treatments = set(t.lower() for t in unique_treatments)
        if len(unique_treatments) > len(lower_treatments):
            report.add_issue(
                check_name="Inconsistent treatment naming",
                severity="WARNING",
                n_affected=len(df),
                details=f"Treatment names differ in casing: {sorted(unique_treatments)}",
            )


def check_unit_consistency(df, report):
    """
    Check for inconsistent measurement units across sites.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    report : QualityReport
        Report to append issues to.
    """
    for unit_col, measure_col in [("weight_unit", "weight"), ("height_unit", "height")]:
        if unit_col not in df.columns:
            continue

        unique_units = df[unit_col].unique().tolist()
        if len(unique_units) > 1:
            unit_counts = df[unit_col].value_counts().to_dict()
            report.add_issue(
                check_name=f"Inconsistent units: {measure_col}",
                severity="CRITICAL",
                n_affected=len(df),
                details=f"Multiple units found for {measure_col}: {unit_counts}",
            )


def run_all_checks(df, dataset_name="Multi-center dataset"):
    """
    Run all quality control checks on a dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    dataset_name : str
        Name for the report header.

    Returns
    -------
    QualityReport
        Complete quality control report.
    """
    report = QualityReport(dataset_name)
    report.total_records = len(df)
    report.total_variables = len(df.columns)

    print("🔍 Running quality control checks...\n")

    print("  1/6 Checking missing values...")
    check_missing_values(df, report)

    print("  2/6 Checking duplicates...")
    check_duplicates(df, report)

    print("  3/6 Checking value ranges...")
    check_value_ranges(df, report)

    print("  4/6 Checking dates...")
    check_dates(df, report)

    print("  5/6 Checking categorical consistency...")
    check_categorical_consistency(df, report)

    print("  6/6 Checking unit consistency...")
    check_unit_consistency(df, report)

    report.summary()
    return report


if __name__ == "__main__":
    from data_simulator import generate_all_sites

    df = generate_all_sites()
    report = run_all_checks(df)