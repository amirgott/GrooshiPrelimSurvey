## Overview

Creates a synthetic v2 survey response for a target segment and submits it as a test GitHub Issue (`_test: true`). Processing and analysis are done separately via `/process-issues`.

**Argument ($ARGUMENTS):** segment slug. If absent or unrecognized, display the menu below and wait for researcher input before proceeding.

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

## Step 1 — Identify target segment

If $ARGUMENTS matches a slug in the menu (exact match), use it. Otherwise display the menu and ask the researcher to choose by number or slug. Wait for the response before continuing.

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

### Base profile

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

### Applying criteria

Set field values to clearly satisfy all decisive criteria — use extreme values within the allowed range rather than borderline ones. For example, if the criterion is comm_quality ≤ 2, set it to 1 rather than 2.

For any area selected in `3.1_areas`, always include both the quality field and the friction field for that area.

For the safety-critical segment: omit all step 3 fields (`3.1_areas` and all `3_*` fields) — safety routing intentionally skips step 3 when `2.1_safety` is set to the unsafe value.

For area string values in `3.1_areas`: read the exact strings from the `x-conditional-fields` section of `responses/schemas/v2.json`. Some values contain special characters — do not retype them; copy directly from the schema.

Override or extend the base profile fields as needed.

**Profile consistency**: Beyond the decisive criteria, always set `2.2_comm_quality`, `2.2_emotional_tension`, and `2.2_org_difficulty` to values that clearly reflect the segment's described typical profile — do not leave these fields absent or at a default. Use the segment description and the scale direction note in `response-segmentation.md` (higher raw `comm_quality` = worse communication) to infer appropriate values. For example: safety-critical → `comm_quality=5`, `emotional_tension=5`; cooperative-colleagues → `comm_quality=1`, `emotional_tension=1`. Also set relevant free-text fields (e.g. `2.1_safety_detail`) with language consistent with the segment's tone. A test issue that only satisfies decisive criteria but misrepresents the broader profile will produce spurious coherence warnings during analysis.

**Step 3 subscale consistency**: For every area selected in `3.1_areas`, also set its quality and friction scores to values that match the segment's conflict level. Scale directions (from the HTML): quality runs 1 (מצוין — excellent) → 5 (גרוע — terrible); friction runs 1 (manage excellently) → 5 (always fighting). Both scales go in the same direction — higher = worse. Examples: high-conflict → quality 4–5, friction 4–5; cooperative-colleagues → quality 2–3, friction 2–3; angry-associates → quality 3–4, friction 3–4. Do not leave quality at 1 (excellent) for a high-conflict profile.

**Step 3 subscale consistency**: For every area selected in `3.1_areas`, also set its quality and friction scores to values that match the segment’s conflict level. Scale directions (from the HTML): quality runs 1 (מצוין — excellent) → 5 (גרוע — terrible); friction runs 1 (manage excellently) → 5 (always fighting). Both scales go in the same direction — higher = worse. Examples: high-conflict → quality 4–5, friction 4–5; cooperative-colleagues → quality 2–3, friction 2–3; angry-associates → quality 3–4, friction 3–4. Do not set quality to 1 (excellent) for a high-conflict or angry-associates profile.

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

---

## Step 5 — Report

| Item | Value |
|------|-------|
| Issue | #N |
| Survey ID | (generated) |
| Segment tested | (slug) |
| Expected category after processing | (segment name from response-segmentation.md, noting primary + secondary for combinable) |

Remind the researcher to run `/process-issues` to process and verify the result.
