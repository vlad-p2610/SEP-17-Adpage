# Proposed analysis data contract

Draft for discussion with the ClickHouse loader and model-wrapper owners.
This is a handoff proposal, not a description of AdPage's actual tables or an
approved client schema. No database queries or endpoint names are invented here.

## Boundary

The loader in issue #4 supplies a pandas dataframe of company/time aggregates.
The analysis component profiles it without database access, aggregation,
imputation or source modifications. Framework adapters remain responsible for
the conversion to framework-specific inputs. The existing PyMC wrapper currently
hardcodes `date_week`, `x1`, `x2` and controls `event_1`, `event_2`, `t`; these are
implementation placeholders, not evidence that AdPage has those fields.

## Proposed dataframe shape

| Role | Suggested representation | Must be confirmed |
| --- | --- | --- |
| Company | Stable anonymized string identifier; preserve leading zeros | Actual field, uniqueness and access scope |
| Period | Explicit date or datetime column, one reporting period per row | Grain, timezone, week boundary and coverage |
| Target | Finite numeric revenue or another agreed business KPI | Exact definition, gross/net treatment, refunds, currency/units |
| Paid channels | One finite nonnegative numeric input per agreed channel | Channel mapping; spend versus exposure; availability and units |
| Controls | Optional numeric covariates, consistently aligned by company/period | What exists, how it is measured and why it is relevant |

For this increment the intended key is `(company, period)`. If raw ClickHouse
tables contain one row per event, campaign or geography, repeated keys are not
automatically duplicates: an agreed aggregation/key expansion must precede this
profiler. Geo-level and reach/frequency structures require an extension.

## Mapping and calendar

Column names are configurable; nothing requires AdPage to rename its source.
The demo YAML maps `company_id`, `date_week`, `revenue`, `search_spend` and
`social_spend`. Its `W-MON` calendar and ISO date format are demonstration choices.
Agree an extraction range and calendar before interpreting missing periods.

Do not fill a missing value with zero merely because a channel is absent in an
export. Confirm whether it means an inactive channel, a failed collection, or
unavailable history. Do not sum rates such as ROAS to make a weekly target or
channel input. Agree treatment of currencies, refunded revenue and data revisions.
Do not derive training controls or transformations from future holdout outcomes.

## Analysis output

The JSON report has `report_version`, `schema`, row/candidate counts, missing
columns, numeric-field issue counts, and per-company diagnostics. Optional
`record_findings` give `row_position` (zero-based within the supplied dataframe),
`field` and `reason`, without copying raw values. Store an extraction/version
reference alongside the report so those positions can be traced to the same
input; the profiler does not create durable source identifiers or version snapshots.

Record reasons: `missing_company_identifier`, `missing_or_invalid_date`,
`missing_required_value`, `nonnumeric_value`, `nonfinite_value`,
`negative_channel_value`, `ambiguous_duplicate_key`.

Candidate exclusions are diagnostic: no source/prepared dataset is written.
`blocked_missing_columns` or `blocked_no_candidate_rows` report structural
blockers. `requires_review` is not permission to run an MMM. All copies of a
duplicate key are excluded from candidate counts until a resolution rule is
agreed; selecting an arbitrary winner would conceal a data decision.

## Acceptance checklist for the first real extract

- [ ] Approved read-only access or bounded anonymized export is provided.
- [ ] Available field definitions and missing fields are documented by AdPage.
- [ ] Company key, period grain/calendar, target definition and units are agreed.
- [ ] Channel and control mappings are reviewed with both framework-wrapper owners.
- [ ] Aggregation avoids double-counted target values and resolves raw-table grain.
- [ ] The profiler runs and produces aggregate counts plus traceable local findings.
- [ ] The team reviews gaps/duplicates before adopting exclusion or imputation rules.
- [ ] Minimum-history and dataset rejection criteria are documented after seeing data.

Keep source extracts, real reports and access credentials in approved storage,
outside Git. CSV input is an offline demo/export path; the confirmed production
source remains ClickHouse.

## Sources

- Current `src/dataloader.py`, `src/MMMAbs.py` and `src/pymcmodel.py` in the checked repository.
- Client answers recorded in this conversation: ClickHouse access, policy-dependent
  row exclusion/company rejection, and team-derived schema after field disclosure.
- [PyMC-Marketing MMM API](https://www.pymc-marketing.io/en/stable/api/generated/pymc_marketing.mmm.mmm.MMM.html).
- [Meridian data organization](https://developers.google.com/meridian/docs/pre-modeling/collect-data).
