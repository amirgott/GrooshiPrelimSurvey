---
description: "Compile survey schema and HTML into survey.skills.json — a structured field index consumed by generate-persona, generate-test-issue, and other skills. Run once at project setup and after schema changes."
argument-hint: ""
---

## Purpose

Reads the active schema JSON and `index.html`. Produces `survey.skills.json` at the project root so that skills can consume field metadata, persona profile config, and test baseline defaults without hardcoding project-specific field names.

---

## Startup

Read `survey.config.json`. Extract:
- `current_schema` — path to the active schema JSON
- `html_file` key if present; otherwise default to `index.html`

Read the schema JSON and the HTML file.

---

## Step 1 — Build field_index

For every field in schema `properties` and `patternProperties`:

**Step assignment** — from field name prefix:

| Prefix | Step |
|--------|------|
| `1.1_`, `1.2_` | `"1"` |
| `2.1_`, `2.2_`, `2.3_` | `"2"` |
| `3.1_`, `3_` | `"3"` |
| `4_` | `"4"` |
| `5_` | `"5"` |
| other (`survey_id`, `safety_flag`, `_test`) | `"meta"` |

**Type classification:**
- `enum` of consecutive integer strings (`"1"`, `"2"`, ...) → type `"scale"`, compute `range: [min, max]`
- `enum` of non-integer strings → type `"enum"`
- `pattern` only → type `"pattern"`
- `type: "string"` with no enum/pattern → type `"free-text"`

**Label extraction** — parse the HTML: for each form field with a `name` attribute matching the field, find the nearest preceding `<label>` text. For scale fields, also extract the first and last button texts as `scale_labels`.

**Conditional** — copy `shown_when` from schema `x-conditional-fields` if present; otherwise `null`.

**Required** — `true` if field appears in schema `required` array.

Produce `field_index` object keyed by field name. Each entry has keys: `step`, `label`, `type`, `enum` (if enum/scale), `range` (if scale), `scale_labels` (if scale), `required`, `conditional`.

---

## Step 2 — Derive persona_profile

### schema_fields

From `field_index`, select all entries where `step == "1"` AND `type == "enum"` AND `required == true`.

For each, output an object with keys: `field`, `label`, `enum`.

### domain_fields

Examine the full `field_index` and survey context to infer what additional narrative fields a persona needs beyond what is in the schema. Typical patterns:

- Repeating indexed fields (e.g., `1.1_kid_age_*`) → infer an array domain field with `maps_to` and `conversion`
- An enum field whose label implies a duration → infer an integer-months domain field with `maps_to` and `conversion`
- Survey domain context → infer narrative-only domain fields (no `maps_to`)

For each inferred domain field, produce an object with keys:

| Key | Value |
|-----|-------|
| `field` | persona field name |
| `type` | `int`, `array`, or `text` |
| `hint` | one sentence for the persona generator |
| `maps_to` | survey field name or list (omit if narrative-only) |
| `conversion` | rule for converting domain value to survey field value (omit if narrative-only) |

**Show the inferred `domain_fields` to the researcher and ask for confirmation before continuing.**

---

## Step 3 — Derive test_baseline

Choose sensible neutral default values for the standard test respondent (used by `/generate-test-issue` when no persona is provided).

Rules:
- For each required step-1 enum field: choose the most common / least extreme value (e.g., joint custody over sole custody, same city over abroad).
- Always include: `_test: true`, `5_other_filled`, `5_contact_ok`, and `2.1_safety` set to their safe/negative defaults.
- Include placeholder child ages consistent with the neutral profile.

**Show the derived `test_baseline.fields` to the researcher and ask for confirmation before continuing.**

---

## Step 4 — Write survey.skills.json

Assemble the final object with top-level keys: `_meta`, `field_index`, `persona_profile`, `test_baseline`.

`_meta` must include: `schema_version` (from schema filename or description field), `schema_file`, `html_file`, `generated_at` (ISO timestamp).

`persona_profile` has keys: `schema_fields` (array), `domain_fields` (array).

`test_baseline` has keys: `description` (string), `fields` (object).

Write to `survey.skills.json` at the project root using Python heredoc via Bash. Use `json.dumps(..., ensure_ascii=False, indent=2)`.

---

## Step 5 — Report

| Item | Value |
|------|-------|
| Output | `survey.skills.json` |
| Fields indexed | N |
| persona_profile schema_fields | N |
| persona_profile domain_fields | N |
| test_baseline fields | N |

Remind the researcher to:
1. Commit `survey.skills.json`
2. Re-run `/compile-skills` after any schema or HTML change
