---
description: "Answer research questions from questions.md by analyzing all processed survey responses. Outputs analysis/answers.html."
argument-hint: "leave blank to run all questions, or pass a question number (e.g. '4') to re-run a single question"
---

## Startup

Read `survey.config.json` from the project root. Extract:
- `gh_repo` — not needed here, ignore
- `output_dir` — base path; processed files are at `{output_dir}/survey/processed/*.json`

Read `analysis/questions.md`. Parse each numbered question (format: `{N}. {text}`).

Determine run mode from the argument:
- **No argument** — process all questions from `questions.md`
- **Argument is a number** (e.g. `"4"`) — re-run only that question from `questions.md`
- **Argument is free-form text** (e.g. `"What does the data show about fathers vs. mothers in WTP?"`) — treat as an ad-hoc question; derive a short slug for its section id (lowercase, hyphens, max 5 words, e.g. `fathers-vs-mothers-wtp`)

Read all files matching `{output_dir}/survey/processed/*.json`. For each file also read
the corresponding raw file at `{output_dir}/survey/raw/{filename}` to access free-text
fields not present in the processed JSON. Build an in-memory dataset of all responses.

---

## Execution rules

- **Cite numbers.** Every claim must reference a count or percentage (e.g. "23/62 respondents, 37%").
- **Quote sparingly.** At most one short direct quote per question to illustrate a point.
- **Segment cross-tabs.** Where relevant, break down findings by primary segment.
- **Feature implication.** Every answer ends with a bold **Feature implication:** sentence — one concrete product decision or priority that follows from the finding.
- **No speculation beyond the data.** If a question cannot be answered from the available responses, say so briefly.
- **Length.** Each answer: 3–8 sentences. Concise, not exhaustive.

---

## Step 1 — Build dataset summary

Before answering questions, derive these counts (used throughout):

| Metric | How to compute |
|--------|---------------|
| N_total | count of all processed survey files |
| N_analyzed | count with complete `analysis` key |
| segment_dist | freq count of primary segment (first token before space/+/[ in `analysis.category`) |
| friction_freq | freq count of each value in `3.1_areas` (split on ", ") across all responses |
| friction_scores | per area: mean of the corresponding `3_*_friction` field across responses that selected that area |
| wtp_dist | freq count of `4_wtp` values |
| wtp_range_dist | freq count of `4_wtp_range` values (among wtp == "כן") |
| potential_users | count where `analysis.potential_user == true` |
| potential_payers | count where `analysis.potential_payer == true` |
| barriers_freq | split `4_barriers` on ", ", freq count each value |

---

## Step 2 — Answer each question

For each question in `questions.md` (or the single requested question):

1. Print `answering question {N}...`
2. Reason over the dataset to produce the answer following the execution rules above.
3. For free-text questions (mediator role, worst example): read the relevant raw text fields
   across all responses, identify recurring themes, name them.
4. For correlation questions: compare metric distributions across the two groups being correlated.

---

## Step 3 — Compose section HTML

**Questions from `questions.md`** use a numbered id:

```html
<div class="section" id="q{N}">
  <h3>Q{N}. {short title — 4–6 words derived from the question text}</h3>
  <p>{answer paragraph(s) — wrap each sentence or two in a <p>}</p>
  <p><strong>Feature implication:</strong> {one sentence}</p>
</div>
```

**Ad-hoc questions** use a slug id derived from the question text:

```html
<div class="section" id="{slug}">
  <h3>{short title — 4–6 words derived from the question text}</h3>
  <p>{answer paragraph(s)}</p>
  <p><strong>Feature implication:</strong> {one sentence}</p>
</div>
```

Sections added manually (not by this skill) are never modified.

---

## Step 4 — Write answers.html

### If answers.html does not exist

Write a complete file using the structure below. The TOC is built from all sections
(questions-based only, since there are no others yet).

### If answers.html exists and a single question was requested (number)

Parse the existing file. Locate the `<div class="section" id="q{N}">` block for that
question and replace it with the newly generated section. Leave all other sections
untouched. Then rebuild the TOC from all sections present (see TOC spec below).
Rewrite the file.

### If answers.html exists and an ad-hoc question was requested (free-form text)

Parse the existing file. If a section with `id="{slug}"` already exists, replace it.
Otherwise append the new section before `</div>` (end of `.wrap`). Rebuild the TOC.
Rewrite the file.

### If answers.html exists and all questions were requested

Parse the existing file. Replace each `<div class="section" id="q{N}">` block with the
newly generated section for that N. Preserve any sections whose id does not match the
`q{N}` pattern. Then rebuild the TOC. Rewrite the file.

---

## TOC spec

The TOC is a `.section` card with `id="toc"` placed before all answer sections:

```html
<div class="section" id="toc">
  <h3>תוכן עניינים</h3>
  <table class="toc-table">
    <tbody>
      <!-- one row per section present in the file, in document order -->
      <tr>
        <td class="toc-num"><a href="#{id}">Q{N}</a></td>
        <td class="toc-title">{short title}</td>
        <td class="toc-interp">{one sentence — what this section shows}</td>
      </tr>
      <!-- non-question sections use their h3 text as toc-title -->
    </tbody>
  </table>
</div>
```

The `toc-interp` for question sections is a fresh one-sentence synthesis derived from
the answer — not the question text. It answers "what did we find?" not "what did we ask?".
For non-question sections, derive a short interpretation from the section content.

---

## Full file template

```html
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ממצאים — Grooshi Survey</title>
<script src="data.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
       background: #f5f6fa; color: #1a1a2e; direction: rtl; line-height: 1.7; }
.topbar { background: #1a1a2e; color: #fff; padding: 12px 24px;
          display: flex; justify-content: space-between; align-items: center; }
.topbar h1 { font-size: 1rem; font-weight: 600; }
.topbar .snap { font-size: 0.72rem; opacity: 0.4; }
.nav { display: flex; justify-content: space-between; align-items: center;
       padding: 10px 22px; background: #fff; border-bottom: 1px solid #e8e8e8;
       position: sticky; top: 0; z-index: 10; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.nav a { display: inline-block; padding: 6px 16px; border-radius: 6px;
         text-decoration: none; font-size: 0.85rem; color: #555; background: #f0f0f0; }
.nav a:hover { background: #ddd; }
.nav a.primary { background: #1a1a2e; color: #fff; }
.nav .pg { font-size: 0.78rem; color: #bbb; }
.wrap { max-width: 760px; margin: 0 auto; padding: 32px 16px 80px; }
h2.ptitle { font-size: 1.3rem; font-weight: 700; margin-bottom: 24px; }
.section { background: #fff; border-radius: 10px; padding: 24px 28px;
           margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.section h3 { font-size: 1rem; font-weight: 700; color: #555;
              text-transform: uppercase; letter-spacing: 0.04em;
              margin-bottom: 16px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
.section p { font-size: 1rem; margin-bottom: 10px; }
.section p:last-child { margin-bottom: 0; }
.stat { font-weight: 600; color: #1a1a2e; }
.warn { font-weight: 700; color: #c0392b; }
.n { font-size: 0.8rem; color: #aaa; margin-right: 4px; }
.toc-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.toc-table td { padding: 7px 10px; vertical-align: top; border-bottom: 1px solid #f0f0f0; }
.toc-table tr:last-child td { border-bottom: none; }
.toc-num { width: 3rem; font-weight: 700; white-space: nowrap; }
.toc-num a { color: #1a1a2e; text-decoration: none; }
.toc-num a:hover { text-decoration: underline; }
.toc-title { width: 35%; color: #333; font-weight: 600; }
.toc-interp { color: #666; font-style: italic; }
footer { text-align: center; font-size: 0.7rem; color: #ccc; padding: 20px; }
</style>
</head>
<body>
<div class="topbar">
  <h1>Grooshi Survey — ממצאים</h1>
  <span class="snap">{YYYY-MM-DD} · N={N_total}</span>
</div>
<div class="nav">
  <a href="index.html">&#8594; לוח בקרה</a>
  <span class="pg">ממצאים</span>
  <span></span>
</div>
<div class="wrap">
  <h2 class="ptitle">ממצאי מחקר</h2>

  {TOC section}

  {answer sections}

</div>
<footer>Generated: {YYYY-MM-DD}</footer>
</body>
</html>
```

Use `PYTHONUTF8=1 python << 'PYEOF' ... PYEOF` via Bash for writing the file.

Print `answers.html written.` when done.
