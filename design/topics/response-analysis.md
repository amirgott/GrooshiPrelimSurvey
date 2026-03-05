# Response Analysis

Status: Partial

## Storage Layout

```
responses/
  test/
    raw/       # {issue_number}_{survey_id}.json — test submissions
    processed/ # {issue_number}_{survey_id}.json/.html — validation + analysis
  survey/
    raw/       # {issue_number}_{survey_id}.json — real submissions
    processed/ # {issue_number}_{survey_id}.json/.html — validation + analysis
  schemas/     # v1.json, v2.json … — JSON schema per survey version (committed)
analysis/
  aggregate.json  # accumulated conclusions across all processed issues
personas/          # synthetic personas for test issue generation (gitignored)
  {segment}_{MMDDHHmm}.json
```

Routing: `_test: true` in payload → `responses/test/`; otherwise → `responses/survey/`.
`responses/test/`, `responses/survey/`, `analysis/`, and `personas/` are excluded from git; `responses/schemas/` is committed. `.gitignore`:
```
responses/test/
responses/survey/
analysis/
personas/
```

**Personas** are created by `/generate-persona <slug>` and consumed by `/generate-test-issue <persona-file>`. Each persona JSON contains: `input` (segment slug + generated_at), `profile` (demographics, narrative), `conflict_baseline` (avg scale values, safety, legal), `state` (survey-day context, recent incident), `behavioral_params` (verbosity, social desirability, etc.), `artifacts` (per-field deviations). After a test issue is submitted from a persona, the file gains an `issued_as` key with the issue number and survey ID.

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

## Conditional Fields and Validation

Some fields in `required` are conditionally shown in the HTML (inside `logic-box` divs). When a user's answers don't meet the display condition, the field is never shown and its absence is not a violation.

**Schema extension:** `x-conditional-fields` top-level key in each schema JSON (e.g. `v1.json`). Maps field name → `shown_when` condition tree:
```json
"x-conditional-fields": {
  "1.2_emotional_event": { "shown_when": { "any": [
    {"field": "1.2_comm_quality", "op": ">=", "value": 4},
    {"field": "1.2_org_level",    "op": ">=", "value": 4}
  ]}},
  "1.3_fatigue": { "shown_when": { "any": [
    {"field": "1.2_tension_emotional",      "op": ">", "value": 1},
    {"field": "1.2_tension_organizational", "op": ">", "value": 1}
  ]}}
}
```

**Condition tree nodes:** `{"any": [...]}` (OR), `{"all": [...]}` (AND), leaf `{"field", "op", "value"}`. `op` ∈ `{>=, >, <=, <, ==, !=, contains}`. Int `value` → int comparison (missing field → 0); string `value` → string comparison (missing field → `""`). `contains` checks if `value` is a member of the comma-separated multi-select string.

**Dual use of `x-conditional-fields`:**
- *Violation filtering* (`validate_payload`): missing required field + condition not met → drop violation silently
- *Phantom detection* (`detect_inconsistencies`): field present in payload + condition not met → flag as inconsistency

When adding a new survey version: enumerate all `logic-box` divs in the new `index.html` and update `x-conditional-fields` accordingly.

When adding a new survey version: update `x-conditional-fields` in the new schema file to match the HTML conditional logic.

## Single-Issue Processing Pipeline

Script: `scripts/process_issue.py <issue_number>`

**Filename convention:** `{issue_number}_{survey_id}` (e.g. `15_78F`). Issue number is the GitHub canonical ID (unique, used as script input); survey_id is the respondent-visible code (used for couple linkage). Combined to eliminate collision risk.

**Steps:**
0. `fetch_issues.py`: fetch issue body + `createdAt` from GitHub; save `responses/{test|survey}/raw/{stem}.json` with `_issue_number`, `_created_at`, and full payload. Idempotent.
1. `process_issue.py`: locate raw file by glob; check if `responses/{test|survey}/processed/{issue_number}_{survey_id}.json` already exists — skip if so. Routing: `_test` flag in payload → `test/`, else `survey/`.
2. `gh issue view <issue_number> --repo amirgott/GrooshiSurveyData --json body` → parse JSON payload from issue body
3. `fetch_issues.py` saves `responses/{test|survey}/raw/{issue_number}_{survey_id}.json` with `_issue_number`, `_created_at`, and full payload
4. Determine schema version from `versions.json` + submission timestamp
5. Load schema from `responses/schemas/v{N}.json`
6. Validate: check required fields (with conditional filtering), scale ranges, radio/checkbox option sets → `validation` key
7. Detect mechanical inconsistencies: phantom conditional values (field present in payload but display condition not met) → `inconsistencies` key (empty list if none)
8. Save both to `responses/{test|survey}/processed/{issue_number}_{survey_id}.json`
9. Generate `responses/{test|survey}/processed/{issue_number}_{survey_id}.html` — `index.html` pre-filled with response values, all inputs disabled. Step 0 (welcome page) is replaced by the analysis card (key-value table, `dir="ltr"`, monospace) when `analysis` is present, or hidden otherwise. Regenerated after analysis via `--update-html <number>`.

**Analyzed JSON structure:**
```json
{
  "schema_version": "v1",
  "validation": { "valid": bool, "violations": [...] },
  "inconsistencies": [
    { "field": "5.2_price_range", "message": "Field present in payload but display condition not met" }
  ]
}
```

## Validation Handling Rules (applied by the skill, not by process_issue.py)

### Kid age validation
Schema `patternProperties` for `1.1_kid_age_*` enforces `^[0-9]+$` — any non-negative integer, including adult ages. No upper bound.

### Missing Parts 2–5 (low-conflict skip pattern)
When ALL violations are "missing required property" for fields whose names start with `2.`, `3.`, `4.`, or `5.`, check Part 1 tension scores:

| Condition | Action |
|-----------|--------|
| `1.2_tension_emotional == "1"` AND `1.2_tension_organizational == "1"` | Do not surface violations. Assign category `low-conflict`. Note in conclusion that respondent reported no conflicts and skipped Parts 2–5. |
| Either tension score > `"1"` | Surface a single consolidated violation: _"All fields from Parts 2–5 are missing despite reported conflict."_ Ask researcher how to proceed. |

## Qualitative Analysis — `/process-issues` skill

Skill: `.claude/commands/process-issues.md`. Invoked via `/process-issues` in a Claude Code session.

**Discovery:** queries `gh issue list`, cross-references `responses/survey/processed/` and `responses/test/processed/` to find issues that are not processed or are missing a complete `analysis` key. Presents researcher with a table and prompts: process all or select one.

**Per-issue steps:**
1. Run `process_issue.py` if mechanical processing not yet done
2. Build key→question-label map from `index.html` at runtime
3. Analyze: conflict profile, pain hotspots, need signal, cross-section coherence
4. Assign category (see below) + write conclusion paragraph + one-liner
5. Merge `analysis` key into `responses/{test|survey}/processed/{id}.json` without overwriting other keys

**`analysis` key structure:**
```json
{
  "conclusion": "...",
  "category": "...",
  "conclusion_one_liner": "...",
  "potential_user": true,
  "potential_payer": false
}
```

`potential_user` (bool): true if **both** — (a) friction present: any Part 1–4 scale > 1 or binary friction flag set; **AND** (b) no need denial: no explicit denial (`5.2_barriers_other` no-need language, `5.2_other_willing_pay` == "לא לשניהם") and no implicit dismissal (Part 5 uniformly negative). false for low-conflict skips and explicit/implicit no-need cases.

`potential_payer` (bool): true only if `potential_user` is true AND `5.2_willing_to_pay` == "כן".

**Coherence check** (step 3b.9): no human confirmation — always proceed to 3c. Triggered patterns recorded in `coherence_warnings` (array of strings; omitted if empty).

| Pattern | Trigger | Effect |
|---------|---------|--------|
| Friction-denial (explicit) | friction found AND `5.2_other_willing_pay` == "לא לשניהם" | `potential_user: false`, `potential_payer: false` (no change) |
| Friction-denial (implicit) | friction found but need implicitly dismissed | `potential_user: "uncertain"`, `potential_payer: "uncertain"` |
| Tension-friction gap | Part 1 tension ≥ 3 but all Part 2–4 = 1, or inverse | warning only |
| WTP-without-friction | willing to pay but `potential_user: false` | warning only |
| Category-score mismatch | `high-conflict` median ≤ 2, or `low-conflict` any score ≥ 4 | warning only |

**HTML analysis card**: static Python-generated HTML (not JS); criteria comment row above data rows (`white-space:pre-wrap`).

**Categories:** `high-conflict`, `low-conflict`, `financially-stressed`, `logistically-overwhelmed`, `emotionally-exhausted`, `disengaged-partner`, `early-stage` (combinable)

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

`scripts/aggregate.py` reads all `responses/survey/processed/{id}.json` files and updates `analysis/aggregate.json`. `responses/test/` is excluded entirely — they are test submissions and must not affect statistics.

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