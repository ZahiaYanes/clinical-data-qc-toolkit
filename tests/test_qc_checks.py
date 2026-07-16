"""
Unit tests for the QC checks module.

Tests each quality control check with controlled data
to verify correct detection of issues.

Author: Zahia Yanes
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qc_checks import (
    QualityReport,
    check_missing_values,
    check_duplicates,
    check_value_ranges,
    check_dates,
    check_categorical_consistency,
    check_unit_consistency,
    run_all_checks,
)


@pytest.fixture
def clean_data():
    """Create a small clean dataset with no issues."""
    return pd.DataFrame({
        "patient_id": ["P001", "P002", "P003"],
        "site": ["Site_A", "Site_A", "Site_A"],
        "age": [55, 62, 70],
        "gender": ["M", "F", "M"],
        "enrollment_date": ["01/01/2022", "15/03/2022", "20/06/2022"],
        "tumor_stage": ["I", "II", "III"],
        "weight": [70.0, 65.0, 80.0],
        "weight_unit": ["kg", "kg", "kg"],
        "height": [175.0, 160.0, 180.0],
        "height_unit": ["cm", "cm", "cm"],
        "hemoglobin": [13.0, 12.5, 14.0],
        "creatinine": [1.0, 0.9, 1.1],
        "ldh": [200.0, 180.0, 220.0],
        "treatment": ["Pembrolizumab", "Nivolumab", "Pembrolizumab"],
        "death": [0, 0, 1],
    })


@pytest.fixture
def dirty_data():
    """Create a dataset with known quality issues."""
    return pd.DataFrame({
        "patient_id": ["P001", "P002", "P002", "P003", "P004"],
        "site": ["Site_A", "Site_A", "Site_A", "Site_B", "Site_C"],
        "age": [55, -5, -5, 70, 45],
        "gender": ["M", "F", "F", "Male", "m"],
        "enrollment_date": ["01/01/2022", "15/03/2022", "15/03/2022", "03/20/2022", "2022-06-01"],
        "tumor_stage": ["I", "II", "II", "3", "Stage IV"],
        "weight": [70.0, 0.0, 0.0, 165.0, 75.0],
        "weight_unit": ["kg", "kg", "kg", "lbs", "kg"],
        "height": [175.0, 160.0, 160.0, 67.0, 180.0],
        "height_unit": ["cm", "cm", "cm", "in", "cm"],
        "hemoglobin": [13.0, np.nan, np.nan, 14.0, 12.0],
        "creatinine": [1.0, -0.5, -0.5, 1.1, 0.9],
        "ldh": [200.0, 180.0, 180.0, np.nan, 220.0],
        "treatment": ["Pembrolizumab", "nivolumab", "nivolumab", "NIVOLUMAB", "Pembrolizumab"],
        "death": [0, 0, 0, 1, 0],
    })


class TestQualityReport:
    """Tests for the QualityReport class."""

    def test_empty_report(self):
        report = QualityReport("test")
        assert len(report.issues) == 0

    def test_add_issue(self):
        report = QualityReport("test")
        report.add_issue("test check", "WARNING", 5, "test details")
        assert len(report.issues) == 1
        assert report.issues[0]["severity"] == "WARNING"
        assert report.issues[0]["n_affected"] == 5

    def test_to_dataframe(self):
        report = QualityReport("test")
        report.add_issue("check1", "CRITICAL", 3, "detail1")
        report.add_issue("check2", "WARNING", 5, "detail2")
        df = report.to_dataframe()
        assert len(df) == 2
        assert "severity" in df.columns


class TestMissingValues:
    """Tests for missing value detection."""

    def test_no_missing(self, clean_data):
        report = QualityReport("test")
        check_missing_values(clean_data, report)
        assert len(report.issues) == 0

    def test_detects_missing(self, dirty_data):
        report = QualityReport("test")
        check_missing_values(dirty_data, report)
        missing_issues = [i for i in report.issues if "Missing" in i["check"]]
        assert len(missing_issues) > 0

    def test_reports_affected_ids(self, dirty_data):
        report = QualityReport("test")
        check_missing_values(dirty_data, report)
        for issue in report.issues:
            assert "affected_ids" in issue


class TestDuplicates:
    """Tests for duplicate detection."""

    def test_no_duplicates(self, clean_data):
        report = QualityReport("test")
        check_duplicates(clean_data, report)
        assert len(report.issues) == 0

    def test_detects_duplicates(self, dirty_data):
        report = QualityReport("test")
        check_duplicates(dirty_data, report)
        assert len(report.issues) == 1
        assert report.issues[0]["severity"] == "CRITICAL"

    def test_duplicate_count(self, dirty_data):
        report = QualityReport("test")
        check_duplicates(dirty_data, report)
        assert report.issues[0]["n_affected"] == 1


class TestValueRanges:
    """Tests for value range validation."""

    def test_clean_data_no_issues(self, clean_data):
        report = QualityReport("test")
        check_value_ranges(clean_data, report)
        assert len(report.issues) == 0

    def test_detects_negative_age(self, dirty_data):
        report = QualityReport("test")
        check_value_ranges(dirty_data, report)
        age_issues = [i for i in report.issues if "Age" in i["check"]]
        assert len(age_issues) == 1
        assert age_issues[0]["severity"] == "CRITICAL"

    def test_detects_zero_weight(self, dirty_data):
        report = QualityReport("test")
        check_value_ranges(dirty_data, report)
        weight_issues = [i for i in report.issues if "Weight" in i["check"]]
        assert len(weight_issues) == 1

    def test_detects_negative_creatinine(self, dirty_data):
        report = QualityReport("test")
        check_value_ranges(dirty_data, report)
        creat_issues = [i for i in report.issues if "Creatinine" in i["check"]]
        assert len(creat_issues) == 1


class TestCategoricalConsistency:
    """Tests for categorical coding checks."""

    def test_consistent_gender(self, clean_data):
        report = QualityReport("test")
        check_categorical_consistency(clean_data, report)
        gender_issues = [i for i in report.issues if "gender" in i["check"]]
        assert len(gender_issues) == 0

    def test_detects_inconsistent_gender(self, dirty_data):
        report = QualityReport("test")
        check_categorical_consistency(dirty_data, report)
        gender_issues = [i for i in report.issues if "gender" in i["check"]]
        assert len(gender_issues) == 1


class TestUnitConsistency:
    """Tests for unit consistency checks."""

    def test_consistent_units(self, clean_data):
        report = QualityReport("test")
        check_unit_consistency(clean_data, report)
        assert len(report.issues) == 0

    def test_detects_mixed_units(self, dirty_data):
        report = QualityReport("test")
        check_unit_consistency(dirty_data, report)
        assert len(report.issues) > 0
        assert any(i["severity"] == "CRITICAL" for i in report.issues)


class TestRunAllChecks:
    """Tests for the full QC pipeline."""

    def test_clean_data_minimal_issues(self, clean_data):
        report = run_all_checks(clean_data, "test")
        critical = [i for i in report.issues if i["severity"] == "CRITICAL"]
        assert len(critical) == 0

    def test_dirty_data_finds_issues(self, dirty_data):
        report = run_all_checks(dirty_data, "test")
        assert len(report.issues) > 0
        assert report.total_records == len(dirty_data)