## Step 1 — Discover unfinished issues

1. Run `gh issue list --repo amirgott/GrooshiSurveyData --state open --limit 200 --json number,createdAt` to get all submitted issues. **Always execute this as a live query — never use a cached or previously known issue list.**
2. For each issue number, look for a file matching `responses/survey/processed/{number}_*.json` or `responses/test/processed/{number}_*.json` (check both).
3. Classify each issue:
   - **Not processed** — no processed JSON exists
   - **Needs analysis** — processed JSON exists but is missing the `analysis` key (or `analysis` is missing any of `conclusion`, `category`, `conclusion_one_liner`)
   - **Complete** — processed JSON has a complete `analysis` key (including `potential_user` and `potential_payer`) → skip silently
   - **Test** — processed JSON has `"test": true` (file is in `responses/test/`) → exclude from aggregation; process normally but show in a separate "Test issues" section in the table
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

**Never use `cd`** — run all scripts directly from the working directory; never prefix Bash commands with `cd DIR &&`.

**Never use Edit or Write tools for file modifications.** Both crash on content containing braces or quotes. Default for all file writes (processed JSON, persona updates, etc.): write `scripts/_patch.py` using the Write tool with single-quoted Python strings and dict() syntax (no braces in source), run it with Bash, then delete it.

---

## Step 3 — Process selected issue(s)

Repeat the following for each selected issue (one at a time, in issue-number order):

### 3a — Mechanical processing (if not yet done)

If no processed JSON exists for this issue, first check whether a raw file exists at `responses/{test|survey}/raw/{number}_*.json`. If not, fetch it (requires network):
```
PYTHONUTF8=1 python scripts/fetch_issues.py {number}
```
Then process it (runs offline):
```
PYTHONUTF8=1 python scripts/process_issue.py {number}
```
Wait for it to complete, then read the resulting processed JSON and raw JSON to check for violations and inconsistencies. Path lookup rule: if the processed JSON has `"test": true`, files are under `responses/test/`; otherwise `responses/survey/`. So: `responses/{test|survey}/processed/{id}.json` and `responses/{test|survey}/raw/{id}.json`. Apply the rules below before surfacing anything to the researcher.

**Violation handling rules (no human confirmation required — always proceed to 3b):**

- **Missing step 3 fields when safety routing active**: If `2.1_safety` == `"לא"` in the raw file, step 3 was intentionally skipped — missing `3_*` fields are not violations. Proceed to 3b.

- **Missing steps 2–4 fields**: If all violations are "missing required property" for fields whose names start with `2.2_`, `3`, or `4_`:
  - Read `2.2_emotional_tension` and `2.2_org_difficulty` from the raw file.
  - If **both equal `"1"`**: proceed to 3b, assign category `low-conflict`, note in conclusion that respondent reported no conflicts and skipped steps 3–4.
  - If **either is > `"1"`**: proceed to 3b with available data; add `"All fields from steps 3–4 are missing despite reported conflict"` to `coherence_warnings`.

- **All other violations and inconsistencies**: proceed to 3b; violations are already recorded in `validation.violations`.

### 3b — Qualitative analysis

1. Read `responses/{test|survey}/raw/{id}.json` (use `test/` if `"test": true` in processed JSON, else `survey/`).
2. Read `index.html` — for each form field (`input`, `select`, `textarea`) with a `name` attribute, find the nearest preceding label text to build a `{field_key → question_label}` map. Use this map to present field values in human-readable form during analysis.
3. Analyze the response holistically:
   - **Conflict profile**: interpret `2.2_comm_quality`, `2.2_emotional_tension`, and `2.2_org_difficulty` as a conflict baseline.
   - **Pain hotspots**: identify where scale scores are highest across step 3 quality fields; cross-reference with free-text fields in those sections.
   - **Need signal**: assess step 4 responses — does the respondent express a clear unmet need? Is willingness to pay present?
   - **Cross-section coherence**: flag qualitative inconsistencies not caught mechanically (e.g. low conflict scores but strong emotional fatigue language, or high willingness to pay but dismissive free-text tone).
4. Assign a **category** — follow `design/topics/response-segmentation.md` (Steps 1–4): derive computed values, evaluate each segment, assign primary + optional secondary, apply modifiers, run coherence checks.
5. Write a **conclusion** paragraph (3–5 sentences) characterizing: who this person is, what their main pain is, and how strong their product need appears.
6. Write a **conclusion_one_liner** (≤15 words) summarizing the pain profile.
7. Set **`potential_user`** (boolean): `true` if **both** conditions hold — (a) some friction is present: any `2.2_*` scale > 1, or any `3_*_friction` field > 1, or `2.1_safety` is set; **AND** (b) the respondent does not deny needing the product — no explicit denial (`4_wtp` == "לא" AND `4_barriers` contains no-need language) and no implicit dismissal (step 4 is uniformly negative with zero positive signal). `false` in all other cases, including low-conflict skip cases.
8. Set **`potential_payer`** (boolean): `true` only if `potential_user` is `true` AND `4_wtp` == "כן". Otherwise `false`.
9. **Coherence check** — after setting `potential_user`/`potential_payer`, scan for the following contradiction patterns. No human confirmation required: record all triggered patterns in `coherence_warnings` (array of strings) and proceed directly to 3c. Omit `coherence_warnings` from the JSON if the array is empty.

   | Pattern | Trigger | Warning string | Effect on fields |
   |---------|---------|----------------|-----------------|
   | Friction-denial (explicit) | friction found (condition a true) AND `4_wtp` == "לא" AND `4_barriers` contains no-need language | `"Friction detected but respondent explicitly denies need"` | Keep `potential_user: false`, `potential_payer: false` |
   | Friction-denial (implicit) | friction found (condition a true) but need implicitly dismissed (condition b fails for non-explicit reasons) | `"Friction detected but respondent implicitly denies need"` | Set `potential_user: "uncertain"`, `potential_payer: "uncertain"` |
   | Tension-friction gap | `2.2_emotional_tension` or `2.2_org_difficulty` ≥ 3 but all step 3 friction scores = 1, or vice versa | `"Step 2 tension and step 3 friction diverge significantly"` | No change to fields |
   | WTP-without-friction | `4_wtp` == "כן" but `potential_user: false` | `"Willing to pay but no friction detected"` | No change to fields |
   | Category-score mismatch | category is `high-conflict` but median step 3 score ≤ 2, or `low-conflict` with any score ≥ 4 | `"Assigned category may not match scale data"` | No change to fields |

### 3c — Write result

Merge into `responses/{test|survey}/processed/{id}.json` — add the `analysis` key **without overwriting** `schema_version`, `validation`, or `inconsistencies`:

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

Then regenerate the HTML with the analysis card:
```
PYTHONUTF8=1 python scripts/process_issue.py --update-html {number}
```

Confirm completion to the researcher, then move to the next issue if processing all.