## Overview

Creates a synthetic v2 survey response for a target segment and submits it as a test GitHub Issue (`_test: true`). Processing and analysis are done separately via `/process-issues`.

**Argument ($ARGUMENTS):** either a segment slug, or a path to a persona JSON file (created by `/generate-persona`). If a file path (contains `/` or ends in `.json`): read the persona, extract `persona.segment` as the target segment, and use persona-guided payload construction in Step 3. If a segment slug or absent: standard construction.

---

## Segment menu

| # | Slug | Segment heading in response-segmentation.md |
|---|------|----------------------------------------------|
| 1 | safety-critical | Safety-critical / Coercive Control |
| 2 | high-conflict | High-conflict / Court-adjacent |
| 3 | angry-associates | Angry Associates |
| 4 | cooperative-colleagues | Cooperative Colleagues |
| 5 | boundary-first | Boundary-first / Parallel Parents |
| 6 | financially-stressed | Financially-stressed |
| 7 | complex-care | Complex-care Coordinators |
| 8 | distance | Distance / Relocation |
| 9 | blended-family | Blended-family / New Partners |

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

Otherwise: if $ARGUMENTS matches a slug in the menu (exact match), use it. If absent or unrecognized, display the menu and ask the researcher to choose by number or slug. Wait before continuing.

---

## Step 2 — Read segmentation criteria

Read `design/topics/response-segmentation.md`.

Locate the section for the chosen segment. Extract:
- **Decisive** criteria — all must be satisfied
- **Supporting** criteria — include where they do not conflict with the base profile
- **Notes** — use to avoid accidentally satisfying another segment's decisive criteria
- Whether the segment is [exclusive] or [combinable]

For [combinable] segments: also choose a primary segment to pair with, guided by the Notes field. Use the combinable segment as secondary.

After identifying the criteria, also check the decisive conditions of the other segments to confirm the constructed payload will not accidentally trigger them.

---

## Step 3 — Construct payload

Two paths depending on whether a persona is present.

---

### Without persona (standard)

#### Base profile

| Field | Value |
|-------|-------|
| _test | true (boolean, not string) |
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

Include a plausible step 4 block: `4_wtp`, `4_wtp_range` (if wtp is yes), `4_barriers`. Values should be realistic and consistent with the segment's pain profile.

#### Applying criteria

Set field values to clearly satisfy all decisive criteria — use extreme values within the allowed range rather than borderline ones. For example, if the criterion is comm_quality ≤ 2, set it to 1 rather than 2.

For any area selected in `3.1_areas`, always include the friction field for that area.

For the safety-critical segment: omit all step 3 fields (`3.1_areas` and all `3_*` fields) — safety routing intentionally skips step 3 when `2.1_safety` is set to the unsafe value.

For area string values in `3.1_areas`: read the exact strings from the `x-conditional-fields` section of `responses/schemas/v3.json`. Some values contain special characters — do not retype them; copy directly from the schema.

Override or extend the base profile fields as needed.

**Profile consistency**: Beyond the decisive criteria, always set `2.2_comm_quality`, `2.2_emotional_tension`, and `2.2_org_difficulty` to values that clearly reflect the segment's described typical profile — do not leave these fields absent or at a default. Use the segment description and the scale direction note in `response-segmentation.md` (higher raw `comm_quality` = worse communication) to infer appropriate values. For example: safety-critical → `comm_quality=5`, `emotional_tension=5`; cooperative-colleagues → `comm_quality=1`, `emotional_tension=1`. Also set relevant free-text fields (e.g. `2.1_safety_detail`) with language consistent with the segment's tone. A test issue that only satisfies decisive criteria but misrepresents the broader profile will produce spurious coherence warnings during analysis.

**Step 3 subscale consistency**: For every area selected in `3.1_areas`, set its friction score to a value that matches the segment's conflict level. Scale direction (from the HTML): friction runs 1 (מסתדרים מצוין) → 4 (כמעט תמיד נלחמים). Higher = worse. Examples: high-conflict → friction 4; cooperative-colleagues → friction 2; angry-associates → friction 3.

---

### With persona

#### Step 1 fields (from `persona.profile`)

Map profile fields directly to payload:

| Payload field | Persona source |
|---------------|---------------|
| `1.1_time_since_sep` | Convert `time_since_sep_months`: <12 → `"עד שנה"`; 12–36 → `"1–3 שנים"`; 36–84 → `"3–7 שנים"`; >84 → `"7+ שנים"` |
| `1.1_num_kids` | `len(persona.profile.kids)` as string |
| `1.1_kid_age_N` | `persona.profile.kids[N-1].age` as string |
| `1.1_custody` | `persona.profile.custody` |
| `1.1_distance` | `persona.profile.distance` |
| `1.2_gender` | `persona.profile.gender` |
| `1.2_religious_divorce` | `persona.profile.religious_divorce` |
| `1.2_new_partner` | `persona.profile.new_partner` |

Always set `_test: true`, `5_other_filled: "לא"`.

For `2.1_safety`: `"כן"` if `conflict_baseline.safety == true`; otherwise use the unsafe value appropriate for safety-critical.
For `2.3_legal`: `"כן"` if `conflict_baseline.legal == true`; else `"לא"`.

#### Reasoning step — before filling any other field

Read the full persona holistically: `profile`, `conflict_baseline`, `state`, and `behavioral_params` together. Reason about how this specific person would behave when filling the survey on this specific day. Consider:

- Which scale fields they would rate higher or lower than their true baseline, and why (e.g. a recent incident inflating emotional tension; social desirability bias softening a negative self-report; high self-awareness reducing the urge to exaggerate)
- Whether competing effects on the same field cancel or compound (e.g. high `emotional_temp` pushing a rating up while high `social_desirability_bias` pulls it down)
- Which friction areas they would select, and whether seeing the full list would draw out an additional area they hadn't planned to mention
- Which optional text fields they would skip, fill briefly, or fill in detail — based on `verbosity`, `survey_patience`, and whether the field touches the `recent_incident`
- Whether they would name one barrier or several, and which is most salient given the survey-day context
- Whether they would consent to contact, considering `trust_in_survey` and `profile.background`

Use this reasoning to inform every field value constructed below. Decisive criteria are still enforced as hard constraints after reasoning.

#### Step 2 scale fields

For each of `2.2_comm_quality`, `2.2_emotional_tension`, `2.2_org_difficulty`:
1. Start from the matching `conflict_baseline` avg.
2. Apply reasoning from above to determine the survey-day adjustment.
3. Round to nearest integer. Clamp to [1, scale_max] (comm_quality max=5; tension and org max=4).
4. Enforce decisive criteria: if the value violates a decisive boundary, clamp to that boundary.

#### Step 3 areas and subscales

Select friction areas based on `conflict_baseline.narrative` and the segment's pain profile, informed by the reasoning step (e.g. anchoring effects from `anchoring_sensitivity`). Verify area count satisfies decisive criteria.

For area string values in `3.1_areas`: read exact strings from `responses/schemas/v3.json` as in standard flow.

For each selected area's friction subscale: anchor to the clamped baseline rather than the segment extreme. Apply the same reasoning about survey-day bias.

#### Optional text fields

For each optional text field (`3_worst_example`): use the reasoning step to decide whether to omit or fill. If filling, write a Hebrew answer consistent with `state.recent_incident` and `profile.background`, calibrated to `behavioral_params.verbosity` (≤3 = one short phrase; 4–6 = one full sentence; ≥7 = two sentences).

#### Step 4 fields

- `4_barriers`: write Hebrew reflecting the barrier(s) most salient given the reasoning step and `state.recent_incident`. Apply judgment about whether this persona would name one or several.
- `4_wtp`: derive from `state.motivation` and segment need profile.
- `4_wtp_range`: if wtp is yes, pick the range consistent with persona's financial situation.
- `5_contact_ok`: derive from reasoning (considering `trust_in_survey` and privacy disposition from `profile.background`).

---

### Survey ID

Generate as: T + two-letter abbreviation + timestamp (MMDDHHmm).

Abbreviations matching slug order: sc, hc, aa, cc, bf, fs, cd, dr, bl.

---

## Execution rules

**Never use `cd`** — run all scripts directly from the working directory; never prefix Bash commands with `cd DIR &&`.

**Never use Edit or Write tools for file modifications.** Use `PYTHONUTF8=1 python << 'PYEOF' ... PYEOF` via Bash for all file writes and edits.

---

## Step 4 — Create GitHub Issue

Write `scripts/_create_test_issue.py` using a Python heredoc via Bash. Constraints for the script:
- Use single quotes for all Python string literals — never double quotes
- Build the payload using `dict()` and individual key-assignment statements — never brace-literal dict syntax
- Serialize: `json.dumps(payload, ensure_ascii=False)`
- Build the issue body as a Markdown table row with `survey_data` as the key and the serialized payload as the value
- Write body to `_body.md`, then run `gh issue create --repo amirgott/GrooshiSurveyData` with title `[TEST] (slug) — (survey_id)` and `--body-file _body.md`
- Extract the issue number from the returned URL with `re.search`
- Print: `Issue number: (N)`
- Delete `_body.md`

Run:

```
PYTHONUTF8=1 python scripts/_create_test_issue.py
```

Capture the issue number. Delete `scripts/_create_test_issue.py`.

**If a persona was used:** after successful submission, update the persona JSON file's `issued_as` array using a Python heredoc via Bash. Do NOT delete the persona file.

---

## Step 5 — Report

| Item | Value |
|------|-------|
| Issue | #N |
| Survey ID | (generated) |
| Segment tested | (slug) |
| Expected category after processing | (segment name from response-segmentation.md, noting primary + secondary for combinable) |
| Persona file | (path, if persona was used; omit row otherwise) |

Remind the researcher to run `/process-issues` to process and verify the result.
