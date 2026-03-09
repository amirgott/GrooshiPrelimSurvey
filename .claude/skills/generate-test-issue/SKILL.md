---
description: "Generate a synthetic survey response for a target segment and submit it as a test GitHub Issue."
argument-hint: "segment-slug or path/to/persona.json"
---

## Startup

Read `survey.config.json` from the project root. Extract:
- `gh_repo` — repository to submit the test issue to
- `issue_body_key` — markdown table key for the survey data payload
- `current_schema` — path to the active schema JSON
- `segmentation_doc` — path to the response segmentation criteria document
- `personas_dir` — directory for persona JSON files
- `survey_id_prefix` — prefix for generated survey IDs

Read the file at `segmentation_doc`. It defines the segment list, decisive criteria, and segment abbreviations.

Read the file at `current_schema`. The `x-conditional-fields` section contains exact area string values for `3.1_areas`. Field definitions contain enum values for all Step 1 profile fields.

---

## Step 0 — Persona detection

If $ARGUMENTS contains `/` or ends in `.json`:
- Read the file at the given path. If it does not exist, print an error and stop.
- Extract `input.segment_slug` — use as the target segment for Step 1.
- Store the full persona object and the file path for use in Steps 1–4.

Otherwise: no persona — proceed with standard flow.

---

## Step 1 — Identify target segment

If segment came from a persona (Step 0): use it directly, skip the menu.

Otherwise: if $ARGUMENTS matches a slug in the segmentation doc (exact match), use it. If absent or unrecognized, display the segment list from the segmentation doc and ask the researcher to choose. Wait before continuing.

---

## Step 2 — Read segmentation criteria

Using the segmentation doc already loaded at startup, locate the section for the chosen segment. Extract:
- **Decisive** criteria — all must be satisfied
- **Supporting** criteria — include where they do not conflict with the base profile
- **Notes** — use to avoid accidentally satisfying another segment's decisive criteria
- Whether the segment is [exclusive] or [combinable]

For [combinable] segments: also choose a primary segment to pair with. Use the combinable segment as secondary.

After identifying the criteria, check the decisive conditions of all other segments to confirm no accidental triggers.

---

## Step 3 — Construct payload

Two paths depending on whether a persona is present.

---

### Without persona (standard)

#### Base profile

| Field | Value |
|-------|-------|
| _test | true (boolean) |
| 1.1_time_since_sep | 1–3 שנים |
| 1.1_num_kids | 2 |
| 1.1_kid_age_1 | 6 |
| 1.1_kid_age_2 | 9 |
| 1.1_custody | משמורת משותפת |
| 1.1_distance | אותה עיר |
| 1.2_gender | נקבה |
| 1.2_religious_divorce | לא רלוונטי |
| 1.2_new_partner | לאף אחד |
| 2.1_safety | כן |
| 5_other_filled | לא |
| 5_contact_ok | לא |

For field enum values (custody, distance, religious_divorce, new_partner, time_since_sep, gender): use the exact strings from the schema loaded at startup. Copy directly — do not retype.

Include a plausible step 4 block: `4_wtp`, `4_wtp_range` (if wtp is yes), `4_barriers`. Values should be realistic and consistent with the segment's pain profile.

#### Applying criteria

Set field values to clearly satisfy all decisive criteria — use extreme values rather than borderline ones.

For any area selected in `3.1_areas`, always include the friction field for that area.

For the safety-critical segment: omit all step 3 fields — safety routing skips step 3 when `2.1_safety` is set to the unsafe value.

For area string values in `3.1_areas`: use the exact strings from the `x-conditional-fields` section of the schema loaded at startup.

**Profile consistency**: Always set `2.2_comm_quality`, `2.2_emotional_tension`, and `2.2_org_difficulty` to values reflecting the segment's typical profile. Higher `comm_quality` raw value = worse communication.

**Step 3 subscale consistency**: For every selected area, set its friction score to match the segment's conflict level. Scale: 1 (מסתדרים מצוין) → 4 (כמעט תמיד נלחמים). Higher = worse.

---

### With persona

#### Step 1 fields (from `persona.profile`)

| Payload field | Persona source |
|---------------|---------------|
| `1.1_time_since_sep` | Convert `time_since_sep_months`: <12 → "עד שנה"; 12–36 → "1–3 שנים"; 36–84 → "3–7 שנים"; >84 → "7+ שנים" |
| `1.1_num_kids` | `len(persona.profile.kids)` as string |
| `1.1_kid_age_N` | `persona.profile.kids[N-1].age` as string |
| `1.1_custody` | `persona.profile.custody` |
| `1.1_distance` | `persona.profile.distance` |
| `1.2_gender` | `persona.profile.gender` |
| `1.2_religious_divorce` | `persona.profile.religious_divorce` |
| `1.2_new_partner` | `persona.profile.new_partner` |

Always set `_test: true`, `5_other_filled: "לא"`.

For `2.1_safety`: "כן" if `conflict_baseline.safety == true`; otherwise use the unsafe value.
For `2.3_legal`: "כן" if `conflict_baseline.legal == true`; else "לא".

#### Reasoning step — before filling any other field

Read the full persona holistically: `profile`, `conflict_baseline`, `state`, and `behavioral_params`. Reason about how this specific person would behave filling the survey on this day. Consider:

- Which scale fields they would rate higher or lower than baseline, and why
- Whether competing effects cancel or compound
- Which friction areas they would select
- Which optional text fields they would skip, fill briefly, or fill in detail
- Whether they would name one barrier or several
- Whether they would consent to contact

Use this reasoning to inform every field value. Decisive criteria are still enforced as hard constraints.

#### Step 2 scale fields

For each of `2.2_comm_quality`, `2.2_emotional_tension`, `2.2_org_difficulty`:
1. Start from the matching `conflict_baseline` avg.
2. Apply reasoning to determine the survey-day adjustment.
3. Round to nearest integer. Clamp to [1, scale_max] (comm_quality max=5; tension and org max=4).
4. Enforce decisive criteria: clamp to boundary if violated.

#### Step 3 areas and subscales

Select friction areas based on `conflict_baseline.narrative` and the segment pain profile, informed by the reasoning step. Verify area count satisfies decisive criteria.

For area string values: use exact strings from the schema loaded at startup.

For the friction subscale of each selected area: anchor to the clamped baseline rather than the segment extreme.

#### Optional text fields

For each optional text field (`3_worst_example`): use the reasoning step to decide whether to omit or fill. If filling, write Hebrew consistent with `state.recent_incident` and `profile.background`, calibrated to `behavioral_params.verbosity` (≤3 = one short phrase; 4–6 = one sentence; ≥7 = two sentences).

#### Step 4 fields

- `4_barriers`: Hebrew reflecting the most salient barrier given the reasoning step and `state.recent_incident`.
- `4_wtp`: derive from `state.motivation` and segment need profile.
- `4_wtp_range`: if wtp is yes, pick range consistent with the persona financial situation.
- `5_contact_ok`: derive from reasoning (considering `trust_in_survey` and privacy disposition).

---

### Survey ID

Generate as: `{survey_id_prefix}` + two-letter segment abbreviation + timestamp (MMDDHHmm).

Segment abbreviations are in the "Segment abbreviations" table in the segmentation doc loaded at startup.

---

## Execution rules

**Never use `cd`** — run all scripts from the working directory.

**Never use Edit or Write tools for file modifications.** Use Python heredoc via Bash for all file writes and edits.

---

## Step 4 — Create GitHub Issue

Write `scripts/_create_test_issue.py` using a Python heredoc via Bash. Constraints:
- Use single quotes for all Python string literals — never double quotes
- Build the payload using `dict()` and individual key-assignment statements
- Serialize: `json.dumps(payload, ensure_ascii=False)`
- Build the issue body as a Markdown table row with `{issue_body_key}` (from config) as the key and the serialized payload as the value
- Write body to `_body.md`, then run `gh issue create --repo {gh_repo}` with title `[TEST] (slug) — (survey_id)` and `--body-file _body.md`
- Extract the issue number from the returned URL with `re.search`
- Print: `Issue number: (N)`
- Delete `_body.md`

Run:
```
PYTHONUTF8=1 python scripts/_create_test_issue.py
```

Capture the issue number. Delete `scripts/_create_test_issue.py`.

**If a persona was used:** after successful submission, update the persona JSON file `issued_as` key using a Python heredoc via Bash. Do NOT delete the persona file.

---

## Step 5 — Report

| Item | Value |
|------|-------|
| Issue | #N |
| Survey ID | (generated) |
| Segment tested | (slug) |
| Expected category after processing | (segment name, noting primary + secondary for combinable) |
| Persona file | (path, if persona was used; omit row otherwise) |

Remind the researcher to run `/process-issues` to process and verify the result.
