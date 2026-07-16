"""
Multi-center clinical data simulator.

Generates realistic synthetic clinical datasets from multiple hospital sites
with intentional data quality issues typical of real-world multi-center studies.

Issues simulated:
- Inconsistent date formats across sites
- Different units for the same measurement
- Missing data with site-specific patterns
- Duplicated records
- Inconsistent categorical coding
- Outliers and impossible values

Author: Zahia Yanes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_site_a(n_patients=80, seed=42):
    """
    Generate clinical data for Site A (Paris, France).

    Site A characteristics:
    - Well-structured data
    - Dates in DD/MM/YYYY format (European)
    - Weight in kg, height in cm
    - Some missing lab values

    Parameters
    ----------
    n_patients : int
        Number of patients to generate.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Simulated clinical data for Site A.
    """
    np.random.seed(seed)

    # Patient IDs
    patient_ids = [f"SITE_A_{str(i).zfill(4)}" for i in range(1, n_patients + 1)]

    # Demographics
    ages = np.random.normal(62, 12, n_patients).astype(int)
    ages = np.clip(ages, 25, 90)
    genders = np.random.choice(["M", "F"], n_patients, p=[0.55, 0.45])

    # Dates — European format DD/MM/YYYY
    base_date = datetime(2022, 1, 1)
    enrollment_dates = [
        (base_date + timedelta(days=int(d))).strftime("%d/%m/%Y")
        for d in np.random.uniform(0, 365, n_patients)
    ]

    # Tumor stage
    stages = np.random.choice(
        ["I", "II", "III", "IV"], n_patients, p=[0.1, 0.25, 0.35, 0.3]
    )

    # Vitals — metric units
    weights = np.round(np.random.normal(72, 15, n_patients), 1)
    heights = np.round(np.random.normal(170, 10, n_patients), 1)

    # Lab values
    hemoglobin = np.round(np.random.normal(12.5, 2.0, n_patients), 1)
    creatinine = np.round(np.random.normal(1.0, 0.3, n_patients), 2)
    ldh = np.round(np.random.normal(220, 80, n_patients), 0)

    # Treatment
    treatments = np.random.choice(
        ["Pembrolizumab", "Nivolumab", "Atezolizumab"],
        n_patients,
        p=[0.4, 0.35, 0.25],
    )

    # Outcome — higher stage = higher mortality
    stage_risk = {"I": 0.1, "II": 0.2, "III": 0.4, "IV": 0.6}
    death = [
        np.random.binomial(1, stage_risk[s]) for s in stages
    ]

    df = pd.DataFrame({
        "patient_id": patient_ids,
        "site": "Site_A",
        "age": ages,
        "gender": genders,
        "enrollment_date": enrollment_dates,
        "tumor_stage": stages,
        "weight": weights,
        "weight_unit": "kg",
        "height": heights,
        "height_unit": "cm",
        "hemoglobin": hemoglobin,
        "creatinine": creatinine,
        "ldh": ldh,
        "treatment": treatments,
        "death": death,
    })

    # --- Introduce quality issues ---

    # Missing hemoglobin (10% randomly)
    missing_idx = np.random.choice(n_patients, size=int(n_patients * 0.10), replace=False)
    df.loc[missing_idx, "hemoglobin"] = np.nan

    # A few outliers in creatinine
    outlier_idx = np.random.choice(n_patients, size=3, replace=False)
    df.loc[outlier_idx, "creatinine"] = np.round(np.random.uniform(8, 15, 3), 2)

    return df


def generate_site_b(n_patients=60, seed=43):
    """
    Generate clinical data for Site B (New York, USA).

    Site B characteristics:
    - Dates in MM/DD/YYYY format (American)
    - Weight in POUNDS, height in INCHES
    - Gender coded as "Male"/"Female" (not M/F)
    - Stage coded as 1/2/3/4 (not I/II/III/IV)
    - More missing data

    Parameters
    ----------
    n_patients : int
        Number of patients to generate.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Simulated clinical data for Site B.
    """
    np.random.seed(seed)

    patient_ids = [f"SITE_B_{str(i).zfill(4)}" for i in range(1, n_patients + 1)]

    ages = np.random.normal(65, 11, n_patients).astype(int)
    ages = np.clip(ages, 28, 92)

    # Gender coded differently!
    genders = np.random.choice(["Male", "Female"], n_patients, p=[0.52, 0.48])

    # Dates — American format MM/DD/YYYY
    base_date = datetime(2022, 1, 15)
    enrollment_dates = [
        (base_date + timedelta(days=int(d))).strftime("%m/%d/%Y")
        for d in np.random.uniform(0, 350, n_patients)
    ]

    # Stage coded as numbers!
    stages = np.random.choice(
        [1, 2, 3, 4], n_patients, p=[0.08, 0.22, 0.38, 0.32]
    )

    # Vitals — IMPERIAL units!
    weights_lbs = np.round(np.random.normal(165, 35, n_patients), 1)
    heights_in = np.round(np.random.normal(67, 4, n_patients), 1)

    # Lab values
    hemoglobin = np.round(np.random.normal(12.0, 2.2, n_patients), 1)
    creatinine = np.round(np.random.normal(1.1, 0.35, n_patients), 2)
    ldh = np.round(np.random.normal(240, 90, n_patients), 0)

    treatments = np.random.choice(
        ["pembrolizumab", "nivolumab", "atezolizumab"],  # lowercase!
        n_patients,
        p=[0.38, 0.37, 0.25],
    )

    stage_risk = {1: 0.1, 2: 0.2, 3: 0.4, 4: 0.6}
    death = [np.random.binomial(1, stage_risk[s]) for s in stages]

    df = pd.DataFrame({
        "patient_id": patient_ids,
        "site": "Site_B",
        "age": ages,
        "gender": genders,
        "enrollment_date": enrollment_dates,
        "tumor_stage": stages,
        "weight": weights_lbs,
        "weight_unit": "lbs",
        "height": heights_in,
        "height_unit": "in",
        "hemoglobin": hemoglobin,
        "creatinine": creatinine,
        "ldh": ldh,
        "treatment": treatments,
        "death": death,
    })

    # --- Quality issues ---

    # More missing data (15%)
    for col in ["hemoglobin", "creatinine", "ldh"]:
        missing_idx = np.random.choice(n_patients, size=int(n_patients * 0.15), replace=False)
        df.loc[missing_idx, col] = np.nan

    # Duplicate records (3 patients appear twice)
    dup_idx = np.random.choice(n_patients, size=3, replace=False)
    duplicates = df.iloc[dup_idx].copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    # One impossible age
    df.loc[0, "age"] = -5

    # One impossible weight
    df.loc[5, "weight"] = 0

    return df


def generate_site_c(n_patients=40, seed=44):
    """
    Generate clinical data for Site C (Berlin, Germany).

    Site C characteristics:
    - Dates in YYYY-MM-DD format (ISO)
    - Weight in kg, height in cm (like Site A)
    - Gender coded as "m"/"f" (lowercase)
    - Stage coded as "Stage I", "Stage II", etc.
    - Some dates in the future (data entry errors)

    Parameters
    ----------
    n_patients : int
        Number of patients to generate.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Simulated clinical data for Site C.
    """
    np.random.seed(seed)

    patient_ids = [f"SITE_C_{str(i).zfill(4)}" for i in range(1, n_patients + 1)]

    ages = np.random.normal(60, 13, n_patients).astype(int)
    ages = np.clip(ages, 30, 88)

    # Gender lowercase
    genders = np.random.choice(["m", "f"], n_patients, p=[0.50, 0.50])

    # Dates — ISO format YYYY-MM-DD
    base_date = datetime(2022, 2, 1)
    enrollment_dates = [
        (base_date + timedelta(days=int(d))).strftime("%Y-%m-%d")
        for d in np.random.uniform(0, 330, n_patients)
    ]

    # Stage with prefix
    stages = np.random.choice(
        ["Stage I", "Stage II", "Stage III", "Stage IV"],
        n_patients,
        p=[0.12, 0.23, 0.33, 0.32],
    )

    weights = np.round(np.random.normal(75, 14, n_patients), 1)
    heights = np.round(np.random.normal(172, 9, n_patients), 1)

    hemoglobin = np.round(np.random.normal(12.2, 1.9, n_patients), 1)
    creatinine = np.round(np.random.normal(1.05, 0.32, n_patients), 2)
    ldh = np.round(np.random.normal(230, 85, n_patients), 0)

    treatments = np.random.choice(
        ["PEMBROLIZUMAB", "NIVOLUMAB", "ATEZOLIZUMAB"],  # UPPERCASE!
        n_patients,
        p=[0.42, 0.33, 0.25],
    )

    stage_risk = {
        "Stage I": 0.1, "Stage II": 0.2,
        "Stage III": 0.4, "Stage IV": 0.6,
    }
    death = [np.random.binomial(1, stage_risk[s]) for s in stages]

    df = pd.DataFrame({
        "patient_id": patient_ids,
        "site": "Site_C",
        "age": ages,
        "gender": genders,
        "enrollment_date": enrollment_dates,
        "tumor_stage": stages,
        "weight": weights,
        "weight_unit": "kg",
        "height": heights,
        "height_unit": "cm",
        "hemoglobin": hemoglobin,
        "creatinine": creatinine,
        "ldh": ldh,
        "treatment": treatments,
        "death": death,
    })

    # --- Quality issues ---

    # Future dates (data entry errors)
    df.loc[2, "enrollment_date"] = "2025-12-15"
    df.loc[8, "enrollment_date"] = "2026-03-01"

    # Missing entire rows of lab data
    missing_idx = np.random.choice(n_patients, size=5, replace=False)
    df.loc[missing_idx, ["hemoglobin", "creatinine", "ldh"]] = np.nan

    # Negative creatinine (impossible)
    df.loc[10, "creatinine"] = -0.5

    return df


def generate_all_sites():
    """
    Generate and combine data from all three clinical sites.

    Returns
    -------
    pd.DataFrame
        Combined multi-center dataset with all quality issues.
    """
    print("🏥 Generating Site A (Paris)... ", end="")
    df_a = generate_site_a()
    print(f"{len(df_a)} patients")

    print("🏥 Generating Site B (New York)... ", end="")
    df_b = generate_site_b()
    print(f"{len(df_b)} patients (including duplicates)")

    print("🏥 Generating Site C (Berlin)... ", end="")
    df_c = generate_site_c()
    print(f"{len(df_c)} patients")

    df_all = pd.concat([df_a, df_b, df_c], ignore_index=True)
    print(f"\n📊 Total records: {len(df_all)}")
    print(f"📊 Expected unique patients: 180")
    print(f"📊 Actual records: {len(df_all)} (duplicates included)")

    return df_all


if __name__ == "__main__":
    print("🔄 Generating multi-center clinical dataset...\n")
    df = generate_all_sites()

    print("\n📋 Data quality issues introduced:")
    print("  ⚠️  3 date formats (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)")
    print("  ⚠️  2 unit systems (kg/cm vs lbs/in)")
    print("  ⚠️  4 gender codings (M/F, Male/Female, m/f)")
    print("  ⚠️  3 stage codings (I/II, 1/2, Stage I/Stage II)")
    print("  ⚠️  3 treatment casings (Title/lower/UPPER)")
    print("  ⚠️  3 duplicate records")
    print("  ⚠️  2 future dates")
    print("  ⚠️  1 negative age, 1 zero weight, 1 negative creatinine")
    print("  ⚠️  Outlier creatinine values")
    print("  ⚠️  Missing data (10-15% per site)")

    print(f"\n📊 Preview:")
    print(df.head(10).to_string())

    print(f"\n📊 Missing values:")
    print(df.isnull().sum().to_string())