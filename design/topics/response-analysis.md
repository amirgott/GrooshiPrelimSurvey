# Response Analysis

Status: Partial

## Storage Layout

```
responses/
  raw/          # {issue_number}.json — parsed payload as received from GitHub Issue
  analyzed/     # {issue_number}.json — validation result, inconsistencies, conclusion
  schemas/      # v1.json, v2.json … — JSON schema per survey version
analysis/
  aggregate.json  # accumulated conclusions across all processed issues
```

`responses/` and `analysis/` are excluded from git (respondent data). Add to `.gitignore`:
```
responses/
analysis/
```

## Schema and Versioning

Schema per survey version lives in `responses/schemas/v{N}.json` (JSON Schema format). Field names and allowed values derived from `name` attributes and valid options in `index.html` at that version.

Version manifest: `responses/schemas/versions.json` — committed to git.
```json
{ "v1": { "active_from": "2026-01-01" }, "v2": { "active_from": "..." } }
```

Schema version for a response is inferred from its submission timestamp against the manifest (responses don't embed a version tag). All schema files are committed to git; prior versions are kept permanently.

**HTML versioning via git tags:** Each survey version is tagged in git as `survey-v{N}` at the point index.html is regenerated and pushed. To process responses collected under an older version, researcher checks out `survey-v{N}` — no HTML archiving needed in the repo.

**When survey changes** (additions to the change-management checklist in `survey-content-management.md`):
1. Tag current commit as `survey-v{N}` before regenerating
2. Add new entry to `versions.json` with today's date
3. Create `v{N+1}.json` schema — derived from updated `index.html`

## Single-Issue Processing Pipeline

Script: `scripts/process_issue.py <issue_number>`

**Filename convention:** `{issue_number}_{survey_id}` (e.g. `15_78F`). Issue number is the GitHub canonical ID (unique, used as script input); survey_id is the respondent-visible code (used for couple linkage). Combined to eliminate collision risk.

**Steps:**
1. Check if `responses/analyzed/{issue_number}_{survey_id}.json` already exists — skip if so (idempotent)
2. `gh issue view <issue_number> --repo amirgott/GrooshiSurveyData --json body` → parse JSON payload from issue body
3. Save to `responses/raw/{issue_number}_{survey_id}.json` (payload + `issue_number` field for traceability)
4. Determine schema version from `versions.json` + submission timestamp
5. Validate against `responses/schemas/v{N}.json` — check required fields, scale ranges, radio/checkbox option sets
6. Save validation result (pass/fail + violations list) to `responses/analyzed/{issue_number}_{survey_id}.json`
7. Generate `responses/analyzed/{issue_number}_{survey_id}.html` — `index.html` pre-filled with response values, all inputs disabled (survey-shaped read-only view); researcher must have correct `survey-v{N}` checked out

## Single-Issue Analysis (Interactive)

Performed inside a Claude Code session — no standalone script. Researcher asks Claude Code to analyze a specific response.

Claude Code:
1. Reads `responses/raw/{id}.json`
2. Reads `index.html` (at the correct `survey-v{N}` checkout) — parses `name` attributes and surrounding label text to build key→question-label mapping at runtime
3. Flags inconsistencies (e.g. scale scores contradicting free-text tone, logically incompatible answers across parts)
4. Generates a conclusion paragraph characterizing the respondent's pain profile
5. Writes output to `responses/analyzed/{id}.json` under `analysis` key: `{ "schema_version": "v1", "inconsistencies": [...], "conclusion": "..." }`

## Fetching Submissions

Each submission is one GitHub Issue. Use `gh` CLI:

```
gh issue list --repo amirgott/GrooshiSurveyData --state open --limit 200
gh issue view <number> --repo amirgott/GrooshiSurveyData --json body
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

## Aggregation

`scripts/aggregate.py` reads all `responses/analyzed/{id}.json` files and updates `analysis/aggregate.json`.

**`analysis/aggregate.json` structure:**
- `meta` — total responses, schema versions covered, last updated
- `statistics` — per question key: distribution + median (scales), frequency counts (radio/checkbox)
- `respondents` — `[{ id, schema_version, category, conclusion_one_liner }]`; category assigned during per-issue analysis (e.g. "low-conflict", "financially-stressed")
- `consensus` — findings where clear majority aligns (derived from statistics thresholds by script)
- `irregularities` — outlier response IDs that contradict the consensus pattern
- `survey_improvements` — accumulated suggestions where per-issue analysis flagged a survey gap or question change; feedback loop back to the change workflow

`analysis/summary.md` — human-readable narrative written interactively by Claude Code after reading the aggregate: overall need statement, category breakdown, key consensus findings, survey improvement recommendations.

**Workflow:** `aggregate.py` handles statistics mechanically; Claude Code handles synthesis of `summary.md`.

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