# Analysis Tools — Response Viewer, Dashboard, Contact Manager, Research Analysis

**Status:** Partial

**Context:** Post-collection workflow for analyzing survey responses, managing follow-up contact, and deriving product insights.

---

## Artifacts

| Artifact | File | Status |
|----------|------|--------|
| Response viewer | `analysis/responses.html` | Planned |
| Statistics dashboard | `analysis/dashboard.html` | Planned |
| Contact manager | `analysis/contacts.html` | Planned |
| Research questions | `analysis/questions.md` | Planned |
| Research answers | `analysis/answers.md` | Planned |
| Shared data | `analysis/data.js` | Implemented (via `build_analysis.py`) |

---

## Data Pipeline

`scripts/build_analysis.py` — rebuilds `analysis/data.js` from `responses/survey/raw/` + `responses/survey/processed/`.

- Run with `--data-only` to regenerate `data.js` without touching HTML files (planned flag).
- HTML files are hand-authored or skill-generated; never overwritten by the script.

`SURVEY_DATA` in `data.js` — array of raw response objects, each with an `_analysis` key merged from the processed JSON.

---

## Goal 1 — Response Viewer (`responses.html`)

Static HTML. Loads `SURVEY_DATA` from `data.js`.

- Sidebar: list of responses — issue #, survey ID, category, one-liner.
- Detail panel: renders all fields of the selected response with Hebrew question labels.
- Labels mapped from a hardcoded key→label table derived from `index.html`.
- No server required; open as local file.

---

## Goal 2 — Statistics Dashboard (`dashboard.html`)

Static HTML. Loads `SURVEY_DATA` from `data.js`. Separate page from viewer.

- Summary stat tiles (n, segments, WTP rate, etc.).
- Field picker: select any survey field → renders Chart.js chart (bar/pie for radio/checkbox, histogram for scales).
- Charts rendered client-side from `SURVEY_DATA`; no rebuild needed after field selection.

---

## Goal 3 — Contact Manager (`contacts.html`)

Static HTML. Loads `SURVEY_DATA` from `data.js`; filters to respondents where phone number field is present.

- Table columns: issue #, survey ID, phone, WhatsApp deep-link (pre-filled message), status, notes.
- Status options: not contacted / message sent / replied / call scheduled / done.
- All edits (status, notes) persist to `localStorage` keyed by issue number.
- Export to CSV button.
- WhatsApp link format: `https://wa.me/972XXXXXXXXX?text=<encoded message>`.

---

## Goal 4 — Research Analysis (skill + documents)

`analysis/questions.md` — researcher-authored list of analysis questions (e.g. "Which segment has highest WTP?", "What friction areas appear in safety-critical cases?"). Editable and iterative.

`/analyze` skill (planned) — reads `questions.md` + all processed JSONs → writes `analysis/answers.md`. One section per question, each ending with **Feature implication**.

No Python script; Claude does the synthesis. Rerun skill when questions are added or new responses arrive.

---

## Related

- `design/topics/response-analysis.md` — processing pipeline, schema, validation
- `design/topics/response-segmentation.md` — segment criteria used in analysis key
- `.claude/skills/process-issues/SKILL.md` — upstream skill that produces processed JSONs
