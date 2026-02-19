# Response Analysis

Status: Planned

## Fetching Submissions

Each submission is one GitHub Issue. Use `gh` CLI:

```
gh issue list --repo <owner>/<repo> --state open --limit 200
gh issue view <number> --repo <owner>/<repo> --json body
```

The issue body contains the raw JSON payload. Extract and parse it per issue.

## JSON Payload Schema

Flat key-value object. Keys match HTML `name` attributes from `index.html`. Value types:

| Input type | Value format |
|------------|-------------|
| Scale (range) | Numeric string, e.g. `"4"` |
| Radio | Selected option string |
| Checkbox group (same name) | Comma-joined selected values, e.g. `"וואטסאפ, אימייל"` |
| Free text | Raw string (may be voice-transcribed) |
| Numeric field | Numeric string |

Empty/skipped fields are omitted from the payload (filtered in `user_survey.js`).

## Aggregation by Question Type

| Type | Method |
|------|--------|
| Scale | Distribution across values + median |
| Radio | Frequency count per option |
| Checkbox | Frequency count per option (after splitting on `", "`) |
| Free text | Qualitative: group by theme, note recurring phrases |

## Cross-Question Analysis

Key correlations to examine:

- Part 1 communication score (1.2) × Part 5 willingness-to-pay (5.5) — do high-conflict users value the tool more?
- Part 2 agreement difficulty (2.1) × Part 4 emotional load (4.3) — pain severity alignment
- Part 3 financial friction (3.2) × Part 4 fatigue sources (4.1) — financial pain vs. emotional pain

## Couple Linkage

- Each submission carries a generated survey ID (2 digits + 1 letter), shown to the respondent
- Section 6 asks whether the other parent also filled the survey, and if so, their ID
- Use this field to pair two submissions from the same couple for comparative analysis