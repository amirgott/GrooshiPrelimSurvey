## Step 1 — Discover unfinished issues

1. Run `gh issue list --repo amirgott/GrooshiSurveyData --state open --limit 200 --json number,createdAt` to get all submitted issues. **Always execute this as a live query — never use a cached or previously known issue list.**
2. For each issue number, look for a file matching `responses/processed/{number}_*.json`.
3. Classify each issue:
   - **Not processed** — no processed JSON exists
   - **Needs analysis** — processed JSON exists but is missing the `analysis` key (or `analysis` is missing any of `conclusion`, `category`, `conclusion_one_liner`)
   - **Complete** — processed JSON has a complete `analysis` key (including `potential_user` and `potential_payer`) → skip silently
4. If no unfinished issues exist, tell the researcher and stop.

---

## Step 2 — Present and choose

Show the researcher a table of unfinished issues:

| Issue | Survey ID | Status |
|-------|-----------|--------|
| #N    | XXXX      | Not processed / Needs analysis |

Then ask the researcher to choose: **process all** unfinished issues, or **select a single issue** to process now.

---

## Step 3 — Process selected issue(s)

Repeat the following for each selected issue (one at a time, in issue-number order):

### 3a — Mechanical processing (if not yet done)

If no processed JSON exists for this issue, run:
```
PYTHONUTF8=1 python scripts/process_issue.py {number}
```
Wait for it to complete, then read the resulting `responses/processed/{id}.json` and `responses/raw/{id}.json` to check for violations and inconsistencies, applying the rules below before surfacing anything to the researcher.

**Violation handling rules (no human confirmation required — always proceed to 3b):**

- **Missing Parts 2–5 fields**: If all violations are "missing required property" for fields whose names start with `2.`, `3.`, `4.`, or `5.`:
  - Read `1.2_tension_emotional` and `1.2_tension_organizational` from the raw file.
  - If **both equal `"1"`**: proceed to 3b, assign category `low-conflict`, note in conclusion that respondent reported no conflicts and skipped Parts 2–5.
  - If **either is > `"1"`**: proceed to 3b with available data; add `"All fields from Parts 2–5 are missing despite reported conflict"` to `coherence_warnings`.

- **All other violations and inconsistencies**: proceed to 3b; violations are already recorded in `validation.violations`.

### 3b — Qualitative analysis

1. Read `responses/raw/{id}.json`.
2. Read `index.html` — for each form field (`input`, `select`, `textarea`) with a `name` attribute, find the nearest preceding label text to build a `{field_key → question_label}` map. Use this map to present field values in human-readable form during analysis.
3. Analyze the response holistically:
   - **Conflict profile**: interpret `1.2_comm_quality`, `1.2_org_level`, and tension scores as a conflict baseline.
   - **Pain hotspots**: identify where scale scores are highest across parts 2–4; cross-reference with any free-text fields in those sections.
   - **Need signal**: assess part 5 responses — does the respondent express a clear unmet need? Is willingness to pay present?
   - **Cross-section coherence**: flag qualitative inconsistencies not caught mechanically (e.g. low conflict scores but strong emotional fatigue language, or high willingness to pay but dismissive free-text tone).
4. Assign a **category** — choose the best fit or combine two:
   `high-conflict`, `low-conflict`, `financially-stressed`, `logistically-overwhelmed`, `emotionally-exhausted`, `disengaged-partner`, `early-stage`
5. Write a **conclusion** paragraph (3–5 sentences) characterizing: who this person is, what their main pain is, and how strong their product need appears.
6. Write a **conclusion_one_liner** (≤15 words) summarizing the pain profile.
7. Set **`potential_user`** (boolean): `true` if **both** conditions hold — (a) some friction is present: any Part 1–4 scale field > 1, or `1.2_emotional_event` / `2.2_tasks_not_done` / `3.3_no_decision` / `4.1_no_refund` == "כן"; **AND** (b) the respondent does not deny needing the product — no explicit denial (`5.2_barriers_other` contains no-need language, or `5.2_other_willing_pay` == "לא לשניהם") and no implicit dismissal (Part 5 is uniformly negative with zero positive signal). `false` in all other cases, including low-conflict skip cases.
8. Set **`potential_payer`** (boolean): `true` only if `potential_user` is `true` AND `5.2_willing_to_pay` == "כן". Otherwise `false`.
9. **Coherence check** — after setting `potential_user`/`potential_payer`, scan for the following contradiction patterns. No human confirmation required: record all triggered patterns in `coherence_warnings` (array of strings) and proceed directly to 3c. Omit `coherence_warnings` from the JSON if the array is empty.

   | Pattern | Trigger | Warning string | Effect on fields |
   |---------|---------|----------------|-----------------|
   | Friction-denial (explicit) | friction found (condition a true) AND explicit denial (`5.2_other_willing_pay` == "לא לשניהם") | `"Friction detected but respondent explicitly denies need"` | Keep `potential_user: false`, `potential_payer: false` |
   | Friction-denial (implicit) | friction found (condition a true) but need implicitly dismissed (condition b fails for non-explicit reasons) | `"Friction detected but respondent implicitly denies need"` | Set `potential_user: "uncertain"`, `potential_payer: "uncertain"` |
   | Tension-friction gap | `1.2_tension_emotional` or `1.2_tension_organizational` ≥ 3 but all Part 2–4 scores = 1, or vice versa | `"Part 1 tension and Part 2–4 friction diverge significantly"` | No change to fields |
   | WTP-without-friction | `5.2_willing_to_pay` == "כן" but `potential_user: false` | `"Willing to pay but no friction detected"` | No change to fields |
   | Category-score mismatch | category is `high-conflict` but median Part 2–4 score ≤ 2, or `low-conflict` with any score ≥ 4 | `"Assigned category may not match scale data"` | No change to fields |

### 3c — Write result

Merge into `responses/processed/{id}.json` — add the `analysis` key **without overwriting** `schema_version`, `validation`, or `inconsistencies`:

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