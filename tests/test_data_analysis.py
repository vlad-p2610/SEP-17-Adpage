import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from src.data_analysis import AnalysisSchema, profile_dataframe, render_markdown


class DataAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.schema = AnalysisSchema("company", "date", "revenue", ["search", "social"])
        self.df = pd.DataFrame({"company": ["001"] * 4,
                                "date": ["2025-01-06", "2025-01-13", "2025-01-20", "2025-01-27"],
                                "revenue": [10, 20, 30, 40], "search": [1, 2, 3, 4],
                                "social": [2, 4, 6, 8]})

    def test_profile_and_nonmutation(self):
        before = self.df.copy(deep=True)
        report = profile_dataframe(self.df, self.schema)
        self.assertEqual(report["candidate_rows"], 4)
        self.assertEqual(report["companies"][0]["missing_candidate_periods"], 0)
        self.assertEqual(len(report["companies"][0]["high_channel_correlations"]), 1)
        self.assertEqual(report["status"], "requires_review")
        assert_frame_equal(before, self.df)

    def test_invalid_values_are_counted_once_per_row(self):
        self.df = self.df.astype({"revenue": float, "social": object})
        self.df.loc[0, ["search", "revenue"]] = [-1, float("inf")]
        self.df.loc[1, "social"] = "bad"
        self.df.loc[2, "revenue"] = None
        report = profile_dataframe(self.df, self.schema)
        self.assertEqual(report["invalid_value_rows"], 3)
        self.assertEqual(report["candidate_rows"], 1)
        self.assertEqual(report["columns"]["revenue"]["nonfinite"], 1)
        self.assertEqual(report["columns"]["social"]["nonnumeric"], 1)
        json.dumps(report, allow_nan=False)

    def test_duplicate_keys_do_not_pick_arbitrary_winner(self):
        df = pd.concat([self.df, self.df.iloc[[0]]], ignore_index=True)
        report = profile_dataframe(df, self.schema)
        self.assertEqual(report["duplicate_key_rows"], 2)
        self.assertEqual(report["candidate_rows"], 3)

    def test_companies_are_not_pooled(self):
        df = pd.concat([self.df, self.df.assign(company="002", social=5)], ignore_index=True)
        report = profile_dataframe(df, self.schema)
        self.assertEqual(report["duplicate_key_rows"], 0)
        self.assertEqual(len(report["companies"]), 2)
        self.assertEqual(report["companies"][1]["constant_channels"], ["social"])

    def test_removed_rows_create_time_gaps(self):
        self.df.loc[1, "revenue"] = None
        report = profile_dataframe(self.df, self.schema)
        self.assertEqual(report["companies"][0]["missing_candidate_periods"], 1)

    def test_missing_week_and_off_grid_dates(self):
        self.df.loc[1, "date"] = "2025-01-14"
        report = profile_dataframe(self.df, self.schema)
        self.assertEqual(report["companies"][0]["missing_candidate_periods"], 1)
        self.assertEqual(report["companies"][0]["off_grid_periods"], 1)

    def test_missing_columns_block_profile(self):
        report = profile_dataframe(self.df.drop(columns="revenue"), self.schema)
        self.assertEqual(report["missing_columns"], ["revenue"])
        self.assertIn("Missing required columns: revenue", render_markdown(report))

    def test_empty_and_fully_invalid_data(self):
        for df in [self.df.iloc[:0], self.df.assign(revenue=None)]:
            report = profile_dataframe(df, self.schema)
            self.assertEqual(report["candidate_rows"], 0)
            self.assertEqual(report["status"], "blocked_no_candidate_rows")
            json.dumps(report, allow_nan=False)

    def test_missing_company_and_bad_date(self):
        self.df.loc[0, "company"] = " "
        self.df.loc[1, "date"] = "nonsense"
        report = profile_dataframe(self.df, self.schema)
        self.assertEqual(report["missing_company_rows"], 1)
        self.assertEqual(report["invalid_date_rows"], 1)
        self.assertEqual(report["candidate_rows"], 2)

    def test_duplicate_dataframe_indices_are_safe(self):
        self.df.index = [0, 0, 1, 1]
        self.assertEqual(profile_dataframe(self.df, self.schema)["candidate_rows"], 4)

    def test_bad_schema_is_rejected(self):
        for kwargs in [{"channels": []}, {"channels": ["revenue"]},
                       {"channels": "abc"}, {"controls": "abc"},
                       {"correlation_warning": 2}, {"frequency": "invalid"},
                       {"frequency": "-1D"}, {"frequency": "0D"}]:
            defaults = dict(company="company", date="date", target="revenue", channels=["search"])
            defaults.update(kwargs)
            with self.assertRaises(ValueError):
                AnalysisSchema(**defaults)

    def test_large_finite_values_still_produce_json(self):
        self.df = self.df.astype({"revenue": float, "search": float, "social": float})
        self.df["revenue"] = 1e308
        self.df["search"] = [1e307, 2e307, 3e307, 4e307]
        self.df["social"] = self.df["search"] * 2
        report = profile_dataframe(self.df, self.schema)
        json.dumps(report, allow_nan=False)
        self.assertAlmostEqual(report["companies"][0]["numeric_summary"]["revenue"]["mean"] / 1e308, 1)
        self.assertEqual(len(report["companies"][0]["high_channel_correlations"]), 1)

    def test_categorical_company_ignores_unused_categories(self):
        self.df["company"] = pd.Categorical(self.df["company"], categories=["001", "unused"])
        report = profile_dataframe(self.df, self.schema)
        self.assertEqual(len(report["companies"]), 1)

    def test_record_findings_locate_exclusions_without_raw_values(self):
        self.df = self.df.astype({"social": object})
        self.df.loc[0, "social"] = "bad"
        self.df.loc[1, "search"] = -1
        self.df.loc[2, "date"] = "invalid"
        report = profile_dataframe(self.df, self.schema, include_record_findings=True)
        findings = {(x["row_position"], x["field"], x["reason"]) for x in report["record_findings"]}
        self.assertEqual(findings, {(0, "social", "nonnumeric_value"),
                                    (1, "search", "negative_channel_value"),
                                    (2, "date", "missing_or_invalid_date")})
        self.assertTrue(all(set(x) == {"row_position", "field", "reason"}
                            for x in report["record_findings"]))
        self.assertNotIn("record_findings", profile_dataframe(self.df, self.schema))

    def test_audit_exclusion_positions_match_candidate_count(self):
        df = pd.concat([self.df, self.df.iloc[[0]]], ignore_index=True)
        df.loc[2, "revenue"] = None
        report = profile_dataframe(df, self.schema, include_record_findings=True)
        positions = {x["row_position"] for x in report["record_findings"]}
        self.assertEqual(len(positions), report["excluded_candidate_rows"])
        self.assertEqual(positions, {0, 2, 4})

    def test_cli_preserves_identifier_and_writes_both_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.df.to_csv(root / "input.csv", index=False)
            (root / "schema.yaml").write_text(
                "company: company\ndate: date\ntarget: revenue\nchannels: [search, social]\n")
            subprocess.run([sys.executable, "-m", "src.data_analysis", str(root / "input.csv"),
                            "--schema", str(root / "schema.yaml"), "--output", str(root / "profile")],
                           check=True, capture_output=True, text=True)
            report = json.loads((root / "profile.json").read_text())
            self.assertEqual(report["companies"][0]["company"], "001")
            self.assertEqual(report["candidate_rows"], 4)
            self.assertIn("| 001 |", (root / "profile.md").read_text())


if __name__ == "__main__":
    unittest.main()
