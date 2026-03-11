---
description: "Generate a realistic synthetic user persona for a target segment, for use with /generate-test-issue."
argument-hint: "segment-slug"
---

## Startup

Read `survey.config.json` from the project root. Extract:
- `segmentation_doc` — path to the response segmentation criteria document
- `personas_dir` — directory to write persona files

Read `survey.skills.json` from the project root. It contains `field_index`, `persona_profile`, and `test_baseline`.

Read the file at `segmentation_doc`. It defines the segment list, decisive criteria, and typical conflict profiles.

---

## Step 1 — Identify target segment

Match $ARGUMENTS to a slug in the segmentation doc (exact match). If absent or unrecognized, display the segment list from the segmentation doc and ask the researcher to choose. Wait before continuing.

---

## Step 2 — Read segmentation criteria

Using the segmentation doc already loaded at startup, locate the section for the chosen segment. Extract:
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

**Fixed fields** (universal — always include):

| Field | Notes |
|-------|-------|
| `name` | Hebrew first name |
| `age` | Integer 25–55 |
| `occupation` | Realistic for the demographic |
| `city` | Israeli city |
| `background` | 2–3 sentence narrative of the relationship history and current dynamic |

**Survey-specific fields** — read from `survey.skills.json → persona_profile`:

- **`schema_fields`**: for each entry, include the field using the exact enum string from `field_index[field].enum`. Do not invent values outside the enum.
- **`domain_fields`**: for each entry, generate a value matching the `type` and `hint`. Do not add domain fields not listed here.

Ages in any kids-type domain field must satisfy segment constraints per the segmentation doc.

### `conflict_baseline`

The persona true average experience — not inflated by survey-day state:

| Field | Notes |
|-------|-------|
| `comm_quality_avg` | Float 1.0–5.0. Anchored to segment typical, not necessarily at the decisive extreme. |
| `emotional_tension_avg` | Float 1.0–4.0. Consistent with segment description. |
| `org_difficulty_avg` | Float 1.0–4.0. Consistent with segment description. |
| `safety` | Bool. False only for safety-critical segment. |
| `legal` | Bool. True only for high-conflict or when the plot requires it. |
| `narrative` | 2–3 sentences describing the co-parenting dynamic. |

### `state`

Survey-day context — make it specific and plausible:

| Field | Notes |
|-------|-------|
| `time_of_day` | HH:MM string |
| `day_of_week` | Day name |
| `motivation` | Int 1–10. Why is this person filling the survey right now? |
| `emotional_temp` | Int 1–10. Current emotional state (10 = highly distressed). |
| `fatigue` | Int 1–10. |
| `recent_incident` | A concrete event from the past 24–72 hours consistent with the segment pain profile. |
| `incident_salience` | "low" / "medium" / "high" |
| `trust_in_survey` | Int 1–10. |

Internal consistency: `emotional_temp`, `incident_salience`, and `recent_incident` should reinforce each other.

### `behavioral_params`

All values 1–10:

| Field | Notes |
|-------|-------|
| `digital_comfort` | Familiarity with digital tools and forms |
| `verbosity` | 1–3 = skips most optional text; 4–6 = writes briefly; 7–10 = writes detailed answers |
| `social_desirability_bias` | Tendency to soften negative ratings |
| `self_awareness` | Degree to which persona acknowledges own contribution to friction |
| `survey_patience` | Tolerance for survey length |
| `anchoring_sensitivity` | Degree to which seeing listed options triggers additional selections |

---

## Step 4 — Write and display

### File path

`{personas_dir}/{segment}_{MMDDHHmm}.json` using segment slug and current timestamp. Create the `{personas_dir}` directory if it does not exist.

Write the complete persona JSON using Python heredoc via Bash. Use `json.dumps(persona, ensure_ascii=False, indent=2)`.

### Display

1. The full JSON
2. A one-paragraph plain-language summary: who this person is, what makes the survey-day state distinctive, and how behavioral parameters are likely to shape the answers.

### Report

| Item | Value |
|------|-------|
| Persona file | `{personas_dir}/{segment}_{MMDDHHmm}.json` |
| Segment | (slug) |

Remind the researcher to run `/generate-test-issue {personas_dir}/{segment}_{MMDDHHmm}.json` to create a test issue using this persona.
