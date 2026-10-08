# MMM data profile

Diagnostic only: no data was changed or model fitted.

Rows: 32; status: requires_review.
Candidate rows: 28; excluded from candidate count: 4.

Counts of invalid values and duplicate keys can overlap.

| Numeric field | Missing | Nonnumeric | Nonfinite | Negative |
| --- | ---: | ---: | ---: | ---: |
| revenue | 1 | 0 | 0 | 0 |
| search_spend | 0 | 0 | 0 | 1 |
| social_spend | 0 | 0 | 0 | 0 |

Negative target/control values are for review; only negative channel values are excluded from the candidate count.

| Company | Rows | Candidates | Missing candidate periods | Off-grid periods | Constant channels | High correlations |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| synthetic_a | 17 | 13 | 3 | 0 | none | 1 |
| synthetic_b | 15 | 15 | 1 | 0 | social_spend | 0 |

Review missing periods, duplicate resolution, sample length, currency/units, target definition and controls before fitting. Correlation is not causality. No minimum history or rejection threshold has been approved yet.
