# Survey Content Management

Status: Implemented

## Source of Truth

`index.html` is the source of truth for deployed survey structure — field names, question labels, part layout, and conditional logic. It is what respondents see and what the analysis pipeline reads.

`survey.md` is an authoring artifact: the intended input to HTML generation. It may lag behind `index.html` if edits were made directly to the HTML. Do not use `survey.md` as a reference for survey structure; always read `index.html`.

## Rendering Rules (html_generation_prompt.md)

`html_generation_prompt.md` contains stable HTML rendering instructions. It changes only when HTML behavior needs to change — not when question content changes. Key rules it defines:

- Scales rendered as `<input type="range">` with endpoint labels as text below; no default value (empty until user interacts)
- Speech-to-text (Web Speech API) enabled on all free-text fields
- Opening screen declares anonymity and offers opt-in recording consent
- Survey ID: random 2-digit + 1-letter code, generated on load, shown in status bar
- Part 5 rendered as accordion (two panels: "חשוב" open by default, "אופציונלי" collapsed)
- End screen shows all collected data with copy/send/delete options; delete requires confirmation
- Submission wired via `onclick="submitSurvey()"` → `user_survey.js`

## Conditional Logic

Conditional branches in `survey.md` are annotated with `[if X]` / `[אם X]` brackets inline in the text. These map to HTML show/hide behavior driven by the values of earlier inputs in the same form.

## Change Workflow

1. Tag current commit as `survey-v{N}` (before any changes) — establishes the git anchor for this version
2. Edit `survey.md` (questions, options, scale endpoints, conditional rules)
3. If HTML behavior changes, edit `html_generation_prompt.md`
4. Regenerate `index.html` in full — do not patch it
5. Add new entry to `responses/schemas/versions.json` with today's date
6. Create `responses/schemas/v{N+1}.json` — JSON Schema derived from updated `index.html` field names and valid options
7. Push to `main` to publish

## Notes

- `changes.md` is a freeform developer scratchpad; no enforced format, not part of the workflow