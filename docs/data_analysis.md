# Data analysis — first increment for issue #5

Owners: Catalin (`katalin297`) and Victor (`Yogramos`).
Meeting: 8 October 2026. Status: In progress.

## What our task covers

Understand the available company/time data before fitting an MMM, and provide
evidence for the standardized schema and preprocessing decisions. The ClickHouse
connector belongs to issue #4; preprocessing methods belong to issue #6. This
increment profiles the dataframe those components will provide, without building
a second connector or changing their implementation.

The checked repository contains no benchmark dataset and its `DL.load()` method
is still a stub. No AdPage data has been analyzed and no conclusions about its
quality, history length or model suitability can be drawn yet.

## Delivered

- A callable `profile_dataframe(df, schema)` and CSV command-line entry point.
- Per-column missing, nonnumeric, infinite and negative value counts.
- Per-company record counts, date coverage, duplicate company/date keys,
  expected-period gaps, off-grid dates, numeric summaries, constant channels
  and large absolute Pearson correlations between channel inputs.
- JSON output for later integration and Markdown for review, plus optional
  record-level findings (row position, field and reason; no raw values).
- Synthetic demonstration data with known issues and automated regression tests.

Validation on 7 October: all **16 regression tests** passed with warnings treated
as errors, including source non-mutation, invalid values, duplicate keys, company
isolation, time gaps, empty data, categorical identifiers, large finite values,
schema validation and command-line export. A separate synthetic smoke check
profiled **500 companies, 104 weekly periods each (52,000 rows)** and verified every
company/period count and absence of unintended gaps. It took 1.59 seconds in this
workspace; that is a local observation, not a production performance target.

Reports distinguish invalid-value rows from ambiguous duplicate keys. Counts can
overlap. Both copies of a duplicate are excluded from the **candidate count**;
the profiler never chooses which row to keep, cleans the data, or deletes anything.
Removing bad rows can break a regular time series, so the report checks gaps
after candidate exclusion. All companies remain `requires_review` unless there
are no candidates; valid-looking rows alone do not establish MMM suitability.

## Run the demo

From the repository root, with Python 3.10+:

For a one-command synthetic demonstration after installing the analysis dependencies:

```bash
python -m examples.data_analysis.run_demo
```

It creates the synthetic input and both reports under ignored `analysis-output/demo/`.
For the individual steps or an approved offline export:

```bash
python -m pip install pandas numpy pyyaml
python examples/data_analysis/generate_demo.py /tmp/mmm_demo.csv
python -m src.data_analysis /tmp/mmm_demo.csv --schema examples/data_analysis/schema.yaml --record-findings --output /tmp/mmm_profile
python -m unittest discover -s tests -v
```

See `examples/data_analysis/demo_profile.md` and `.json` for the checked synthetic
output. For real data, map actual column names in a local YAML file; the example
names are a proposal, not a confirmed AdPage schema. No PyMC/ Meridian installation
or model execution is needed for profiling.

Dataframe integration after the loader is implemented:

```python
from src.data_analysis import AnalysisSchema, profile_dataframe

schema = AnalysisSchema(
    company="company_id", date="date_week", target="revenue",
    channels=["search_spend", "social_spend"], frequency="W-MON",
)
report = profile_dataframe(df, schema)
```

## Input contract and limits

This increment expects a **wide company/time aggregate**: one row per company and
period, one column per paid channel input, one target column and optional numeric
controls. Raw event/campaign rows need a separately agreed aggregation first;
otherwise repeated company/date keys may be legitimate raw rows, not faulty data.
Geo-level profiling and reach/frequency inputs are not implemented in this increment.

Dates use an explicit format (`%Y-%m-%d` by default) and UTC parsing. The expected
calendar is configurable (`W-MON` in the demonstration). The chosen reporting
calendar and business timezone must be agreed before aggregation. Dates outside
that grid are flagged. Only gaps within observed coverage are counted; missing
periods before/after the export cannot be inferred. Numeric strings are accepted
if parseable; missing/nonfinite values and negative channel values are flagged
as invalid for this candidate count. Negative target/control values are reported
for review rather than automatically rejected.

The correlation warning of 0.9 is an exploratory default, not client-approved.
Correlations use at least three candidate observations per company and do not
establish causal effects. There is no automatic minimum-history threshold,
imputation, outlier removal, scaling, model acceptance or reproducibility test.
Profiling currently operates in memory; obtain bounded aggregated exports before
profiling the full benchmark. Reports include company identifiers and aggregated
business metrics: keep real data and reports in approved storage, never Git.

## Decisions already obtained from the client

- Benchmark access will be through ClickHouse.
- A small number of bad rows should not automatically reject an otherwise useful
  company dataset; fully unsuitable data should be rejected. Detailed rules remain
  to be established. Source rows are not to be deleted by this analysis tool.
- AdPage will explain the available/missing fields; the team will propose the MMM
  input schema based on them and the framework.
- A small numerical tolerance is acceptable for repeated model runs; its metric
  and threshold will be determined during testing. This profiling increment does
  not claim to verify model reproducibility.

## Meeting update and next steps

“We moved Data analysis to In progress and implemented a non-mutating dataframe
profiler with a synthetic demonstration and regression tests. It detects known
data-quality and time-series issues. Real benchmark analysis is waiting for the
field definitions and an approved company/time extract.”

Proposed division for discussion with Victor (not a change to his assigned work):

| Owner | Next deliverable |
| --- | --- |
| Catalin | Maintain the profiler; map received fields into the analysis schema and document validation findings. |
| Victor | Review target/channel definitions, units, coverage and potential controls; investigate anomalies in the first real sample. |
| Both | Agree aggregation/calendar and cleaning rules with the loader/preprocessing owners; review per-company results and propose suitability criteria. |

Ask for an approved schema/sample or a bounded read-only export via the loader
owners. Confirm target definition (e.g. revenue versus conversions), monetary
units, period boundaries, channel mapping and available controls. Establish how
duplicates and missing periods should be resolved, and what minimum history is
needed once the actual framework and data are known. Keep these as decisions
rather than inventing acceptance thresholds before seeing data.

Issue #5 remains open: completion requires running on approved real data,
summarizing coverage/quality across companies and agreeing the schema and
preprocessing recommendations with the team.

## Primary references

- [PyMC-Marketing MMM API](https://www.pymc-marketing.io/en/stable/api/generated/pymc_marketing.mmm.mmm.MMM.html): explicit date, channel, target and optional control columns.
- [Meridian data collection guide](https://developers.google.com/meridian/docs/pre-modeling/collect-data): time/geo aggregation, KPI/media definitions and missing-data considerations.

These informed the diagnostic scope; framework-specific adapters remain the
responsibility of the wrapper tasks. No text or implementation was copied.
