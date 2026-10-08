"""Non-mutating, framework-independent profiling of company/time MMM data."""
import argparse
import json
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


@dataclass(frozen=True)
class AnalysisSchema:
    company: str
    date: str
    target: str
    channels: list[str]
    controls: list[str] = field(default_factory=list)
    date_format: str = "%Y-%m-%d"
    frequency: str = "W-MON"
    correlation_warning: float = 0.9

    def __post_init__(self):
        if not isinstance(self.channels, list) or not isinstance(self.controls, list):
            raise ValueError("channels and controls must be lists of column names.")
        columns = [self.company, self.date, self.target, *self.channels, *self.controls]
        if not self.channels or any(not isinstance(c, str) or not c for c in columns):
            raise ValueError("Specify non-empty column names and at least one channel.")
        if len(columns) != len(set(columns)):
            raise ValueError("Each schema column must have a unique role.")
        if not 0 < self.correlation_warning <= 1:
            raise ValueError("correlation_warning must be in (0, 1].")
        offset = pd.tseries.frequencies.to_offset(self.frequency)
        if offset.n <= 0:
            raise ValueError("frequency must advance forward in time.")


def profile_dataframe(df: pd.DataFrame, schema: AnalysisSchema, *, include_record_findings: bool = False) -> dict:
    """Return aggregate diagnostics; never remove, repair or modify source rows.

    Candidate rows exclude invalid required values, negative channel values and
    all ambiguous company/date duplicates. This is a diagnostic count, not an
    approved cleaning policy or an assertion that a model is ready to fit.
    """
    # Collect the mapped columns and initialize the diagnostic report.
    required = [schema.company, schema.date, schema.target, *schema.channels, *schema.controls]
    report = {"report_version": 1, "rows": len(df), "schema": vars(schema),
              "missing_columns": [c for c in required if c not in df.columns],
              "status": "requires_review", "columns": {}, "companies": []}
    if include_record_findings:
        report["record_findings"] = []

    # Optionally record row positions and exclusion reasons without copying raw values.
    def record_finding(mask, field_name, reason):
        if include_record_findings:
            report["record_findings"].extend(
                {"row_position": int(position), "field": field_name, "reason": reason}
                for position in np.flatnonzero(mask.to_numpy()))

    # Stop if the column structure is ambiguous or required columns are missing.
    if df.columns.has_duplicates:
        raise ValueError("Input column names must be unique.")
    if report["missing_columns"]:
        report["status"] = "blocked_missing_columns"
        return report

    # Reset a copied frame so repeated input index labels cannot affect masks.
    work = df[required].copy().reset_index(drop=True)
    # Mark missing company identifiers and invalid dates as ineligible for candidate rows.
    missing_company = work[schema.company].isna() | work[schema.company].astype(str).str.strip().eq("")
    dates = pd.to_datetime(work[schema.date], format=schema.date_format, errors="coerce", utc=True)
    invalid = missing_company | dates.isna()
    report["missing_company_rows"] = int(missing_company.sum())
    report["invalid_date_rows"] = int(dates.isna().sum())
    record_finding(missing_company, schema.company, "missing_company_identifier")
    record_finding(dates.isna(), schema.date, "missing_or_invalid_date")
    # Check numeric fields for missing, nonnumeric and nonfinite values.
    numeric_columns = [schema.target, *schema.channels, *schema.controls]
    numeric = pd.DataFrame(index=work.index)
    for column in numeric_columns:
        values = pd.to_numeric(work[column], errors="coerce").astype(float)
        nonfinite = values.notna() & ~np.isfinite(values)
        bad = values.isna() | nonfinite
        negative = values.lt(0)
        report["columns"][column] = {
            "missing": int(work[column].isna().sum()),
            "nonnumeric": int((values.isna() & work[column].notna()).sum()),
            "nonfinite": int(nonfinite.sum()), "negative": int(negative.sum())}
        record_finding(work[column].isna(), column, "missing_required_value")
        record_finding(values.isna() & work[column].notna(), column, "nonnumeric_value")
        record_finding(nonfinite, column, "nonfinite_value")
        # Negative channel values are invalid; negative target/control values are only reported.
        if column in schema.channels:
            bad |= negative
            record_finding(negative, column, "negative_channel_value")
        # Combine field failures into a row mask; the source dataframe stays unchanged.
        invalid |= bad
        numeric[column] = values.where(~bad)

    # Flag every copy of a duplicate company/date key rather than choosing a row to keep.
    keys = pd.DataFrame({"company": work[schema.company], "date": dates})
    duplicate = keys.duplicated(keep=False) & ~missing_company & dates.notna()
    record_finding(duplicate, f"{schema.company},{schema.date}", "ambiguous_duplicate_key")
    # Exclude invalid or duplicate rows from candidate diagnostics, without deleting source rows.
    candidate = ~(invalid | duplicate)
    report["invalid_value_rows"] = int(invalid.sum())
    report["duplicate_key_rows"] = int(duplicate.sum())
    report["candidate_rows"] = int(candidate.sum())
    report["excluded_candidate_rows"] = int((~candidate).sum())
    if not candidate.any():
        report["status"] = "blocked_no_candidate_rows"

    # Analyze companies separately, using only candidate rows for numeric summaries.
    for company, group in work.loc[~missing_company].groupby(schema.company, sort=False, observed=True):
        indices = group.index
        usable = indices[candidate.loc[indices]]
        observed = pd.DatetimeIndex(dates.loc[indices].dropna().unique()).sort_values()
        usable_dates = pd.DatetimeIndex(dates.loc[usable].unique()).sort_values()
        # Check the expected calendar within observed coverage for gaps and off-grid dates.
        expected = pd.DatetimeIndex([])
        if len(observed):
            expected = pd.date_range(observed.min(), observed.max(), freq=schema.frequency)
        missing_periods = expected.difference(usable_dates)
        off_grid = observed.difference(expected)
        # Summarize each numeric field using candidate rows for this company.
        values = numeric.loc[usable]
        stats = {}
        for column in numeric_columns:
            series = values[column]
            # Scale before averaging so large finite values cannot overflow a sum.
            scale = float(series.abs().max()) if len(series) else 0.0
            mean = float((series / scale).mean() * scale) if scale else (0.0 if len(series) else None)
            stats[column] = {"min": float(series.min()) if len(series) else None,
                             "max": float(series.max()) if len(series) else None,
                             "mean": mean,
                             "distinct_values": int(series.nunique()),
                             "zero_fraction": float(series.eq(0).mean()) if len(series) else None}
        # Flag channels with no variation and strongly correlated channel pairs.
        constant = [c for c in schema.channels if values[c].nunique() <= 1]
        correlations = []
        for left, right in combinations(schema.channels, 2):
            if len(values) >= 3 and left not in constant and right not in constant:
                # Pearson correlation is scale invariant; avoid overflow in covariance.
                corr = float((values[left] / values[left].abs().max()).corr(
                    values[right] / values[right].abs().max()))
                if np.isfinite(corr) and abs(corr) >= schema.correlation_warning:
                    correlations.append({"left": left, "right": right, "pearson_r": corr})
        # Store the company's diagnostics; candidate counts do not imply MMM suitability.
        report["companies"].append({
            "company": str(company), "rows": len(group), "candidate_rows": len(usable),
            "invalid_value_rows": int(invalid.loc[indices].sum()),
            "duplicate_key_rows": int(duplicate.loc[indices].sum()),
            "observed_periods": len(observed), "candidate_periods": len(usable_dates),
            "start": observed.min().isoformat() if len(observed) else None,
            "end": observed.max().isoformat() if len(observed) else None,
            "missing_candidate_periods": len(missing_periods),
            "off_grid_periods": len(off_grid), "constant_channels": constant,
            "high_channel_correlations": correlations, "numeric_summary": stats,
            "status": "requires_review" if len(usable) else "blocked_no_candidate_rows"})
    return report


def render_markdown(report: dict) -> str:
    """Render a compact meeting-readable report without raw record values."""
    lines = ["# MMM data profile", "", "Diagnostic only: no data was changed or model fitted.",
             "", f"Rows: {report['rows']}; status: {report['status']}."]
    if report["missing_columns"]:
        lines += ["", "Missing required columns: " + ", ".join(report["missing_columns"])]
        return "\n".join(lines) + "\n"
    lines += [f"Candidate rows: {report['candidate_rows']}; excluded from candidate count: "
              f"{report['excluded_candidate_rows']}.", "",
              "Counts of invalid values and duplicate keys can overlap.", "",
              "| Numeric field | Missing | Nonnumeric | Nonfinite | Negative |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for column, counts in report["columns"].items():
        name = column.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {name} | {counts['missing']} | {counts['nonnumeric']} | "
                     f"{counts['nonfinite']} | {counts['negative']} |")
    lines += ["", "Negative target/control values are for review; only negative channel values "
              "are excluded from the candidate count.", "",
              "| Company | Rows | Candidates | Missing candidate periods | Off-grid periods | Constant channels | High correlations |",
              "| --- | ---: | ---: | ---: | ---: | --- | ---: |"]
    for c in report["companies"]:
        company = c["company"].replace("|", "\\|").replace("\n", " ")
        constants = ", ".join(c["constant_channels"]).replace("|", "\\|") or "none"
        lines.append(f"| {company} | {c['rows']} | {c['candidate_rows']} | "
                     f"{c['missing_candidate_periods']} | {c['off_grid_periods']} | "
                     f"{constants} | {len(c['high_channel_correlations'])} |")
    lines += ["", "Review missing periods, duplicate resolution, sample length, currency/units, "
              "target definition and controls before fitting. Correlation is not causality. "
              "No minimum history or rejection threshold has been approved yet."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Local CSV of company/time aggregates")
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Output prefix for JSON and Markdown")
    parser.add_argument("--record-findings", action="store_true",
                        help="Include zero-based row positions, fields and reasons in JSON; no raw values")
    args = parser.parse_args()
    with args.schema.open() as handle:
        schema = AnalysisSchema(**yaml.safe_load(handle))
    # Preserve identifiers such as 001 rather than allowing numeric inference.
    df = pd.read_csv(args.input, dtype={schema.company: "string"})
    report = profile_dataframe(df, schema, include_record_findings=args.record_findings)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    args.output.with_suffix(".md").write_text(render_markdown(report))
    print(f"Profile written: {args.output.with_suffix('.json')} and {args.output.with_suffix('.md')}")


if __name__ == "__main__":
    main()
