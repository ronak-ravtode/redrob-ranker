# Honeypot Methodology

Only high-confidence impossible profiles are hard-excluded.

## Flagged conditions
- Job duration does not match the declared dates.
- Total career duration materially disagrees with stated experience.
- Three or more expert skills have zero duration.
- A job start date predates a known company founding year.
- The profile contains contradictory current-job state.
- Future-dated employment records are present.

## Exclusions
- Common synthetic noise such as salary range anomalies or stale activity is not treated as a honeypot by itself.
- Missing fields alone are not enough for exclusion.

## Data source
- The founding-year map is local and checked into `data/company_founding_years.json`.
