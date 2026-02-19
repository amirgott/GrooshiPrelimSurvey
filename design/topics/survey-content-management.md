# Survey Content Management

Status: Implemented

## Source of Truth

`survey.md` is the sole source of truth for all survey questions, flow, and conditional logic. It must be updated before any change is reflected in the live survey.

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

1. Edit `survey.md` (questions, options, scale endpoints, conditional rules)
2. If HTML behavior changes, edit `html_generation_prompt.md`
3. Regenerate `index.html` in full — do not patch it
4. Push to `main` to publish

## Notes

- `changes.md` is a freeform developer scratchpad; no enforced format, not part of the workflow