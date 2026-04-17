---
description: "Answer research questions from survey.md by analyzing all processed survey responses. Outputs analysis/answers.md."
argument-hint: "leave blank to run all questions, or pass a question number (e.g. '4') to re-run a single question"
---

## Startup

Read `survey.config.json` from the project root. Extract:
- `gh_repo` — not needed here, ignore
- `output_dir` — base path; processed files are at `{output_dir}/survey/processed/*.json`

Read `analysis/questions.md`. This is the list of research questions to answer. Parse each numbered question.

If a single question number was passed as an argument, process only that question and merge it into the existing `answers.md` (replacing the existing section for that number). Otherwise process all questions.

Read all files matching `{output_dir}/survey/processed/*.json`. For each file also read the corresponding raw file at `{output_dir}/survey/raw/{filename}` to access free-text fields not present in the processed JSON. Build an in-memory dataset of all responses for the analysis below.

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
3. For free-text questions (5, 15): read the relevant raw text fields across all responses, identify recurring themes, name them.
4. For correlation questions (13): compare metric distributions across the two groups being correlated.

---

## Step 3 — Write answers.md

Write `analysis/answers.md` with the following structure:

```markdown
# Survey Research Analysis
_Generated: {YYYY-MM-DD}  |  N={N_total} responses, {N_analyzed} analyzed_

---

## Q1. {question text}

{answer paragraph}

**Feature implication:** {one sentence}

---

## Q2. ...
```

When re-running a single question: read the existing `answers.md`, replace the section for that question number only, preserve all other sections, rewrite the file.

Use `PYTHONUTF8=1 python << 'PYEOF' ... PYEOF` via Bash for writing the file.

Print `answers.md written.` when done.
