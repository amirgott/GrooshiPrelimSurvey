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
- Extract `persona.segment` — use as the target segment for Step 1.
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

Include a plausible step 4 block: `4_tools`, `4_wtp`, `4_wtp_range` (if wtp is yes), `4_barriers`, `4_neutral_helper`. Values should be realistic and consistent with the segment's pain profile.

#### Applying criteria

Set field values to clearly satisfy all decisive criteria — use extreme values within the allowed range rather than borderline ones. For example, if the criterion is comm_quality ≤ 2, set it to 1 rather than 2.

For any area selected in `3.1_areas`, always include both the quality field and the friction field for that area.

For the safety-critical segment: omit all step 3 fields (`3.1_areas` and all `3_*` fields) — safety routing intentionally skips step 3 when `2.1_safety` is set to the unsafe value.

For area string values in `3.1_areas`: read the exact strings from the `x-conditional-fields` section of `responses/schemas/v2.json`. Some values contain special characters — do not retype them; copy directly from the schema.

Override or extend the base profile fields as needed.

**Profile consistency**: Beyond the decisive criteria, always set `2.2_comm_quality`, `2.2_emotional_tension`, and `2.2_org_difficulty` to values that clearly reflect the segment's described typical profile — do not leave these fields absent or at a default. Use the segment description and the scale direction note in `response-segmentation.md` (higher raw `comm_quality` = worse communication) to infer appropriate values. For example: safety-critical → `comm_quality=5`, `emotional_tension=5`; cooperative-colleagues → `comm_quality=1`, `emotional_tension=1`. Also set relevant free-text fields (e.g. `2.1_safety_detail`) with language consistent with the segment's tone. A test issue that only satisfies decisive criteria but misrepresents the broader profile will produce spurious coherence warnings during analysis.

**Step 3 subscale consistency**: For every area selected in `3.1_areas`, also set its quality and friction scores to values that match the segment's conflict level. Scale directions (from the HTML): quality runs 1 (מצוין — excellent) → 5 (גרוע — terrible); friction runs 1 (manage excellently) → 5 (always fighting). Both scales go in the same direction — higher = worse. Examples: high-conflict → quality 4–5, friction 4–5; cooperative-colleagues → quality 2–3, friction 2–3; angry-associates → quality 3–4, friction 3–4. Do not set quality to 1 (excellent) for a high-conflict or angry-associates profile.

---

### With persona

Start from `persona.profile` and `persona.conflict_baseline`. Apply artifacts to derive field values. Decisive criteria are still enforced.

#### Step 1 fields (from `persona.profile`)

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

#### Step 2 scale fields (baseline + artifacts)

For each of `2.2_comm_quality`, `2.2_emotional_tension`, `2.2_org_difficulty`:
1. Start from the matching `conflict_baseline` avg.
2. Find any artifact whose `field` matches and has a `delta`. Add delta to avg.
3. Round to nearest integer. Clamp to [1, scale_max] (comm_quality max=5; tension and org max=4).
4. Enforce decisive criteria: if the value violates a decisive boundary, clamp to that boundary.

For `2.1_safety`: `"כן"` if `conflict_baseline.safety == true`; otherwise use the unsafe value appropriate for safety-critical.
For `2.3_legal`: `"כן"` if `conflict_baseline.legal == true`; else `"לא"`.

#### Step 3 areas and subscales

Start with the 1–2 friction areas most consistent with `conflict_baseline.narrative` and the segment's pain profile. Then apply any `anchoring` artifact: add `extra_area` to the selection.

Verify area count satisfies decisive criteria (e.g. boundary-first requires ≤1 area).

For area string values in `3.1_areas`: read exact strings from `responses/schemas/v2.json` as in standard flow.

For each selected area's quality and friction subscales: use the same conflict-level calibration as standard flow, but anchor to the clamped baseline rather than the segment extreme. Example: if clamped `comm_quality = 4`, quality subscales should be 3–4, not necessarily 5.

For `3_tasks_not_done`: set to `"כן"` if `conflict_baseline.org_difficulty_avg >= 2.5`; else `"לא"`.

#### Optional text fields

For each optional text field (`3_worst_example`, `4_tools_missing`, `4_neutral_helper`):
- Check `persona.artifacts` for a `skip_optional` entry on this field. If found: omit from payload entirely.
- If not found: write a 1–2 sentence Hebrew answer consistent with `state.recent_incident` and `profile.background`. Calibrate length to `behavioral_params.verbosity` (≤3 = one short phrase; 4–6 = one full sentence; ≥7 = two sentences).

#### Step 4 fields

- `4_tools`: choose tools realistic for the persona's digital comfort and segment (e.g. high digital_comfort → may use calendar apps; low → WhatsApp only).
- `4_barriers`: write a Hebrew phrase reflecting the barrier most salient given `state.recent_incident`. If a `single_selection` artifact is present on `4_barriers`: pick only one barrier even if multiple apply.
- `4_wtp`: `"כן"` if `motivation >= 6` and segment typically has product need; else `"לא"`.
- `4_wtp_range`: if wtp is yes, pick the range consistent with persona's financial situation.

For `5_contact_ok`: check for `privacy_reflex` artifact → `"לא"`. Otherwise derive from `trust_in_survey` (≤5 → `"לא"`; >5 → `"כן"`).

---

### Survey ID

Generate as: T + two-letter abbreviation + timestamp (MMDDHHmm).

Abbreviations matching slug order: sc, hc, aa, cc, bf, fs, cd, dr, bl.

---

## Step 4 — Create GitHub Issue

Write `scripts/_create_test_issue.py` via Bash with a single-quoted heredoc. Constraints for the script:
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

**If a persona was used:** after successful submission, update the persona JSON file with:
```json
"issued_as": {
  "issue_number": N,
  "survey_id": "Taa03051215",
  "issued_at": "YYYY-MM-DDTHH:MM:SS"
}
```
Read the persona file, add the `issued_as` key, write it back. Do NOT delete the persona file.

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
