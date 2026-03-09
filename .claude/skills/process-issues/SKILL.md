---
description: "Fetch, validate, and analyze unprocessed survey responses from GitHub Issues."
argument-hint: "issue-number, 'all', or leave blank to list and choose"
---

## Startup

Read `survey.config.json` from the project root. Extract:
- `gh_repo` — GitHub repository to query for issues
- `output_dir` — base path for raw and processed response files
- `segmentation_doc` — path to the response segmentation criteria document

Read the file at `segmentation_doc`. This document is the classification reference used throughout Step 3b analysis — keep it in context.

---

## Step 1 — Discover unfinished issues

1. Run `gh issue list --repo {gh_repo} --state open --limit 200 --json number,createdAt`. **Always execute as a live query — never use a cached list.**
2. For each issue number, look for a file matching `{output_dir}/survey/processed/{number}_*.json` or `{output_dir}/test/processed/{number}_*.json` (check both).
3. Classify each issue:
   - **Not processed** — no processed JSON exists
   - **Needs analysis** — processed JSON exists but is missing the `analysis` key (or `analysis` is missing any of `conclusion`, `category`, `conclusion_one_liner`)
   - **Complete** — processed JSON has a complete `analysis` key (including `potential_user` and `potential_payer`) → skip silently
   - **Test** — processed JSON has `"test": true` (file is in `{output_dir}/test/`) → exclude from aggregation; process normally but show in a separate "Test issues" section
4. If no unfinished issues exist, tell the researcher and stop.

---

## Step 2 — Present and choose

Show the researcher a table of unfinished issues:

| Issue | Survey ID | Status |
|-------|-----------|--------|
| #N    | XXXX      | Not processed / Needs analysis |

Then ask the researcher to choose: **process all** unfinished issues, or **select a single issue** to process now.

---

## Execution rules

**Never use `cd`** — run all scripts directly from the working directory.

**Never use Edit or Write tools for file modifications.** Use `PYTHONUTF8=1 python << 'PYEOF' ... PYEOF` via Bash for all file writes and edits.

---

## Step 3 — Process selected issue(s)

Repeat the following for each selected issue (one at a time, in issue-number order):

### 3a — Mechanical processing (if not yet done)

If no processed JSON exists, first check for a raw file at `{output_dir}/{test|survey}/raw/{number}_*.json`. If absent, fetch it (requires network):
```
PYTHONUTF8=1 python scripts/fetch_issues.py {number}
```
Then process it (runs offline):
```
PYTHONUTF8=1 python scripts/process_issue.py {number}
```
Wait for completion, then read the resulting processed JSON and raw JSON. Path rule: if the processed JSON has `"test": true`, files are under `{output_dir}/test/`; otherwise `{output_dir}/survey/`.

**Violation handling rules (no human confirmation required — always proceed to 3b):**

- **Safety routing active**: If `2.1_safety` == `"לא"` in the raw file, missing `3_*` fields are not violations. Proceed to 3b.
- **Missing steps 2–4 fields**: If all violations are missing `2.2_*`, `3_*`, or `4_*` fields:
  - Read `2.2_emotional_tension` and `2.2_org_difficulty` from the raw file.
  - Both `"1"` → proceed to 3b, assign category `low-conflict`.
  - Either > `"1"` → proceed to 3b; add `"All fields from steps 3–4 are missing despite reported conflict"` to `coherence_warnings`.
- **All other violations**: proceed to 3b; violations recorded in `validation.violations`.

### 3b — Qualitative analysis

1. Read `{output_dir}/{test|survey}/raw/{id}.json`.
2. Analyze the response holistically using the segmentation criteria loaded at startup:
   - **Conflict profile**: interpret `2.2_comm_quality`, `2.2_emotional_tension`, and `2.2_org_difficulty`.
   - **Pain hotspots**: highest step 3 friction scores; cross-reference free-text fields.
   - **Need signal**: step 4 responses — unmet need? willingness to pay?
   - **Cross-section coherence**: flag qualitative inconsistencies not caught mechanically.
3. Assign a **category** following the segmentation criteria (Steps 1–4): derive computed values, evaluate each segment, assign primary + optional secondary, apply modifiers, run coherence checks.
4. Write a **conclusion** paragraph (3–5 sentences): who this person is, main pain, product need strength.
5. Write a **conclusion_one_liner** (≤15 words).
6. Set **`potential_user`** (boolean): `true` if (a) friction present — any `2.2_*` scale > 1, any `3_*_friction` > 1, or `2.1_safety` set — AND (b) no explicit/implicit need denial. `false` otherwise, including low-conflict skip cases.
7. Set **`potential_payer`** (boolean): `true` only if `potential_user` is `true` AND `4_wtp` == `"כן"`.
8. **Coherence check** — record triggered patterns in `coherence_warnings`; proceed to 3c without confirmation:

   | Pattern | Trigger | Warning string | Effect |
   |---------|---------|----------------|--------|
   | Friction-denial (explicit) | friction AND `4_wtp`==`"לא"` AND no-need language in barriers | `"Friction detected but respondent explicitly denies need"` | Keep false |
   | Friction-denial (implicit) | friction but need implicitly dismissed | `"Friction detected but respondent implicitly denies need"` | Set `"uncertain"` |
   | Tension-friction gap | tension or org ≥ 3 but all friction = 1, or vice versa | `"Step 2 tension and step 3 friction diverge significantly"` | No change |
   | WTP-without-friction | `4_wtp`==`"כן"` but `potential_user: false` | `"Willing to pay but no friction detected"` | No change |
   | Category-score mismatch | high-conflict but median friction ≤ 2, or low-conflict with any ≥ 4 | `"Assigned category may not match scale data"` | No change |

### 3c — Write result

Merge into `{output_dir}/{test|survey}/processed/{id}.json` — add the `analysis` key **without overwriting** `schema_version`, `validation`, or `inconsistencies`:

```json
"analysis": {
  "conclusion": "...",
  "category": "...",
  "conclusion_one_liner": "...",
  "potential_user": true,
  "potential_payer": false,
  "coherence_warnings": ["..."]
}
```

`coherence_warnings` is omitted when empty.

Confirm completion to the researcher, then move to the next issue if processing all.
