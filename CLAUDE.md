# Project Overview

Hebrew-language user-research survey for a co-parenting management app (working title: Grooshi). Distributed as a static GitHub Pages site. Respondents fill the survey in-browser; on submit, answers are POSTed to a Cloudflare Worker proxy which creates a GitHub Issue per submission. Researcher (owner) reads and analyzes issues to draw product conclusions.

# Lifecycle Phases

1. **Content** — edit survey questions/structure in `survey.md`
2. **HTML generation** — regenerate `index.html` from `survey.md` + `html_generation_prompt.md`
3. **Publish** — push to `main`; GitHub Pages serves `index.html`
4. **Response collection** — submissions arrive as GitHub Issues (JSON body)
5. **Analysis** — fetch issues via `gh` CLI, parse JSON, aggregate, conclude

# File Map

| File | Role |
|------|------|
| `survey.md` | Source of truth for all survey questions, flow, and conditional logic |
| `html_generation_prompt.md` | Instructions for translating `survey.md` into `index.html` |
| `index.html` | Live survey artifact served by GitHub Pages |
| `user_survey.js` | Client-side submission bridge: collects FormData → POSTs JSON to Cloudflare Worker |
| `changes.md` | Developer scratchpad (not part of any automated workflow) |

# Conventions

Global `~/.claude/CLAUDE.md` intent-resolution rules, design/requirements folder conventions, and coding guidelines all apply here.

See `design/architecture.md` for data flow.
See `design/topics/` for workflow detail on content management and response analysis.

`gh` CLI is the tool for accessing GitHub Issues (survey responses).