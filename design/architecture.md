# Architecture: Data Flow Pipeline

## Layers

**Authored layer**
`survey.md` + `html_generation_prompt.md` → (manual regeneration) → `index.html`

**Delivery layer**
`index.html` pushed to `main` → GitHub Pages serves it to respondents

**Submission boundary**
Respondent's browser (`index.html` + `user_survey.js`) collects FormData → serializes to JSON → POSTs to Cloudflare Worker (external, URL hardcoded in `user_survey.js`) → Worker creates one GitHub Issue per submission

**Storage layer**
GitHub Issues — each issue body contains the full JSON payload of one submission

**Insight layer**
`gh` CLI fetches issues → JSON parsed → aggregated per question → conclusions

## Key Boundaries

| Boundary | Input | Output | Where |
|----------|-------|--------|-------|
| Generation | `survey.md` + `html_generation_prompt.md` | `index.html` | Local, manual |
| Submission | Browser FormData | GitHub Issue (JSON body) | `user_survey.js` → Cloudflare Worker |
| Analysis | GitHub Issues | Aggregated findings | `gh` CLI, local |

## External Infrastructure

The Cloudflare Worker is outside this repo. Its URL lives in `user_survey.js`. It handles auth with GitHub and issue creation — no logic for that exists in this codebase.
