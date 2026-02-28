# Survey Content Management

Status: Implemented

## Source of Truth

`index.html` is the source of truth for deployed survey structure — field names, question labels, part layout, and conditional logic. It is what respondents see and what the analysis pipeline reads.

`survey.md` is an authoring artifact: the intended input to HTML generation. It may lag behind `index.html` if edits were made directly to the HTML. Do not use `survey.md` as a reference for survey structure; always read `index.html`.

## Rendering Rules

`html_generation_prompt.md` is the source of truth for HTML rendering behavior. It changes only when behavior needs to change — not when question content changes. Read it directly for rendering details.

## Conditional Logic

Conditional logic lives in `index.html` as `logic-box` divs with show/hide behavior driven by earlier input values. This is the authoritative source — not `survey.md`.

## Change Workflow

1. Tag current commit as `survey-v{N}` (before any changes) — establishes the git anchor for this version
2. Edit `index.html` directly, or promote a draft file (e.g. `survey_v2_alt.html`) to `index.html`. Do not use `survey.md` as the starting point — it may be stale.
3. If HTML behavior changes, edit `html_generation_prompt.md`
4. Add new entry to `responses/schemas/versions.json` with today's date
5. Create `responses/schemas/v{N+1}.json` — JSON Schema derived from updated `index.html` field names and valid options; enumerate all `logic-box` divs and update `x-conditional-fields` accordingly
6. Review `design/topics/response-segmentation.md` — update any segment criteria or derivations that reference field names changed or removed in the new version
7. Push to `main` to publish

## Notes

- `changes.md` is a freeform developer scratchpad; no enforced format, not part of the workflow