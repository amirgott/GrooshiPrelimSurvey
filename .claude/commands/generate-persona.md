## Overview

Generates a synthetic user persona for a target segment and writes it as JSON to `personas/`. The persona captures stable profile, survey-day state, and behavioral parameters — but does NOT fill in survey answers. It is consumed by `/generate-test-issue` (pass the persona file path as the argument) to produce human-realistic payloads.

**Argument ($ARGUMENTS):** segment slug. If absent or unrecognized, display the menu below and wait for researcher input.

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

Match $ARGUMENTS to a slug in the menu (exact match). If absent or unrecognized, display the menu and ask the researcher to choose by number or slug. Wait before continuing.

---

## Step 2 — Read segmentation criteria

Read `design/topics/response-segmentation.md`. Locate the section for the chosen segment. Extract:
- Typical conflict level — communication quality, emotional tension, org difficulty
- Typical demographics and pain profile
- Decisive criteria — these constrain `conflict_baseline` values
- Notes on which other segments to avoid accidentally resembling

---

## Step 3 — Generate persona JSON

Construct a JSON object with the following top-level keys: `input`, `profile`, `conflict_baseline`, `state`, `behavioral_params`.

### `input`

```json
"input": {
  "segment_slug": "angry-associates",
  "generated_at": "YYYY-MM-DDTHH:MM:SS"
}
```

Use current date/time for `generated_at`.

### `profile`

Invent a realistic person for this segment:

| Field | Notes |
|-------|-------|
| `name` | Hebrew first name |
| `age` | Integer 25–55 |
| `occupation` | Realistic occupation for the demographic |
| `city` | Israeli city |
| `time_since_sep_months` | Integer; 6–36 for most segments |
| `kids` | Array of `{"name": "...", "age": N}`. Ages must satisfy segment constraints: cooperative-colleagues requires ≥1 kid under 10; boundary-first works better with older kids (≥10). |
| `gender` | `"נקבה"` or `"זכר"` |
| `custody` | One of: `"משמורת משותפת"`, `"משמורת מלאה אצלי"`, `"משמורת מלאה אצל שותפ/ת ההורות"` |
| `distance` | One of: `"אותה עיר"`, `"עיר אחרת"`, `"מחוץ לארץ"` |
| `religious_divorce` | One of: `"לא רלוונטי"`, `"ממתינ/ת לגט"`, `"קיבלתי גט"`, `"אחר"` |
| `new_partner` | One of: `"לאף אחד"`, `"לי בלבד"`, `"לשותפ/ת ההורות בלבד"`, `"לשנינו"` |
| `co_parent_description` | 1–2 sentences on co-parent personality and behavior |
| `background` | 2–3 sentence narrative of the relationship history and current dynamic |

### `conflict_baseline`

The persona's *true average* experience — not inflated by survey-day state:

| Field | Notes |
|-------|-------|
| `comm_quality_avg` | Float 1.0–5.0. Anchored to segment typical, not necessarily at the decisive extreme. Example: angry-associates decisive is ≥4, so 4.0–4.8 is realistic rather than always 5. |
| `emotional_tension_avg` | Float 1.0–4.0. Consistent with segment description. |
| `org_difficulty_avg` | Float 1.0–4.0. Consistent with segment description. |
| `safety` | Bool. False only for safety-critical segment. |
| `legal` | Bool. True only for high-conflict or when the plot requires it. |
| `narrative` | 2–3 sentences describing the co-parenting dynamic. Must be consistent with all avg values. |

### `state`

Survey-day context — make it specific and plausible:

| Field | Notes |
|-------|-------|
| `time_of_day` | HH:MM string |
| `day_of_week` | Day name |
| `motivation` | Int 1–10. Why is this person filling the survey right now? |
| `emotional_temp` | Int 1–10. Current emotional state (10 = highly distressed). |
| `fatigue` | Int 1–10. |
| `recent_incident` | A concrete event from the past 24–72 hours consistent with the segment's pain profile. This is the main driver of survey-day bias. |
| `incident_salience` | `"low"` / `"medium"` / `"high"` |
| `trust_in_survey` | Int 1–10. |

Internal consistency: `emotional_temp`, `incident_salience`, and `recent_incident` should reinforce each other. `motivation` and `fatigue` should be coherent with the survey-day context.

### `behavioral_params`

All values 1–10:

| Field | Notes |
|-------|-------|
| `digital_comfort` | Familiarity with digital tools and forms |
| `verbosity` | 1–3 = skips most optional text; 4–6 = writes briefly; 7–10 = writes detailed answers |
| `social_desirability_bias` | Tendency to soften negative ratings |
| `self_awareness` | Degree to which persona acknowledges own contribution to friction |
| `survey_patience` | Tolerance for survey length (low → skips more) |
| `anchoring_sensitivity` | Degree to which seeing listed options triggers additional selections |

---

## Step 4 — Write and display

### File path

`personas/{segment}_{MMDDHHmm}.json` using segment slug and current timestamp.

Example: `personas/angry-associates_03051215.json`

Create the `personas/` directory if it does not exist:
```
mkdir -p personas
```

Write the complete persona JSON to the file using the Write tool with literal UTF-8 Hebrew characters — never `\uXXXX` escape sequences. When generating via a Python script, use `json.dumps(persona, ensure_ascii=False, indent=2)`.

### Display

1. The full JSON
2. A one-paragraph plain-language summary: who this person is, what makes their survey-day state distinctive, and how their behavioral parameters are likely to shape their survey answers.

### Report

| Item | Value |
|------|-------|
| Persona file | `personas/{segment}_{MMDDHHmm}.json` |
| Segment | (slug) |

Remind the researcher to run `/generate-test-issue personas/{segment}_{MMDDHHmm}.json` to create a test issue using this persona.
