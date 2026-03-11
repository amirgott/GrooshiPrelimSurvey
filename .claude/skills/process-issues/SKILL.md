---
description: "Fetch, validate, and analyze unprocessed survey responses from GitHub Issues."
argument-hint: "issue-number, 'all', or leave blank to list and choose"
---

## Startup

Read `survey.config.json` from the project root. Extract:
- `gh_repo` — GitHub repository to query for issues
- `output_dir` — base path for raw and processed response files
- `segmentation_doc` — path to the response segmentation criteria document

Read the file at `segmentation_doc`. This document is the classification reference used throughout Step 3b analysis — keep it in context.

Write `scripts/fetch_issues.py` and `scripts/process_issue.py` via Python heredoc if they do not exist. Use the script content from the **Script templates** section at the end of this document.

---

## Step 1 — Discover unfinished issues

1. Run `gh issue list --repo {gh_repo} --state open --limit 200 --json number,createdAt`. **Always execute as a live query — never use a cached list.**
2. For each issue number, look for a file matching `{output_dir}/survey/processed/{number}_*.json` or `{output_dir}/test/processed/{number}_*.json` (check both).
3. Classify each issue:
   - **Not processed** — no processed JSON exists
   - **Needs analysis** — processed JSON exists but is missing the `analysis` key (or `analysis` is missing any of `conclusion`, `category`, `conclusion_one_liner`)
   - **Complete** — processed JSON has a complete `analysis` key (including `potential_user` and `potential_payer`) → skip silently
   - **Test** — processed JSON has `"test": true` (file is in `{output_dir}/test/`) → exclude from aggregation; process normally but show in a separate "Test issues" section
4. If no unfinished issues exist, tell the researcher and stop.

---

## Step 2 — Present and choose

Show the researcher a table of unfinished issues:

| Issue | Survey ID | Status |
|-------|-----------|--------|
| #N    | XXXX      | Not processed / Needs analysis |

Then ask the researcher to choose: **process all** unfinished issues, or **select a single issue** to process now.

---

## Execution rules

**Never use `cd`** — run all scripts directly from the working directory.

**Never use Edit or Write tools for file modifications.** Use `PYTHONUTF8=1 python << 'PYEOF' ... PYEOF` via Bash for all file writes and edits.

---

## Step 3 — Process selected issue(s)

Repeat the following for each selected issue (one at a time, in issue-number order):

### 3a — Mechanical processing (if not yet done)

If no processed JSON exists, first check for a raw file at `{output_dir}/{test|survey}/raw/{number}_*.json`. If absent, fetch it (requires network):
```
PYTHONUTF8=1 python scripts/fetch_issues.py {number}
```
Then process it (runs offline):
```
PYTHONUTF8=1 python scripts/process_issue.py {number}
```
Wait for completion, then read the resulting processed JSON and raw JSON. Path rule: if the processed JSON has `"test": true`, files are under `{output_dir}/test/`; otherwise `{output_dir}/survey/`.

**Violation handling rules (no human confirmation required — always proceed to 3b):**

- **Safety routing active**: If `2.1_safety` == `"לא"` in the raw file, missing `3_*` fields are not violations. Proceed to 3b.
- **Missing steps 2–4 fields**: If all violations are missing `2.2_*`, `3_*`, or `4_*` fields:
  - Read `2.2_emotional_tension` and `2.2_org_difficulty` from the raw file.
  - Both `"1"` → proceed to 3b, assign category `low-conflict`.
  - Either > `"1"` → proceed to 3b; add `"All fields from steps 3–4 are missing despite reported conflict"` to `coherence_warnings`.
- **All other violations**: proceed to 3b; violations recorded in `validation.violations`.

### 3b — Qualitative analysis

1. Read `{output_dir}/{test|survey}/raw/{id}.json`.
2. Analyze the response holistically using the segmentation criteria loaded at startup:
   - **Conflict profile**: interpret `2.2_comm_quality`, `2.2_emotional_tension`, and `2.2_org_difficulty`.
   - **Pain hotspots**: highest step 3 friction scores; cross-reference free-text fields.
   - **Need signal**: step 4 responses — unmet need? willingness to pay?
   - **Cross-section coherence**: flag qualitative inconsistencies not caught mechanically.
3. Assign a **category** following the segmentation criteria (Steps 1–4): derive computed values, evaluate each segment, assign primary + optional secondary, apply modifiers, run coherence checks.
4. Write a **conclusion** paragraph (3–5 sentences): who this person is, main pain, product need strength.
5. Write a **conclusion_one_liner** (≤15 words).
6. Set **`potential_user`** (boolean): `true` if (a) friction present — any `2.2_*` scale > 1, any `3_*_friction` > 1, or `2.1_safety` set — AND (b) no explicit/implicit need denial. `false` otherwise, including low-conflict skip cases.
7. Set **`potential_payer`** (boolean): `true` only if `potential_user` is `true` AND `4_wtp` == `"כן"`.
8. **Coherence check** — record triggered patterns in `coherence_warnings`; proceed to 3c without confirmation:

   | Pattern | Trigger | Warning string | Effect |
   |---------|---------|----------------|--------|
   | Friction-denial (explicit) | friction AND `4_wtp`==`"לא"` AND no-need language in barriers | `"Friction detected but respondent explicitly denies need"` | Keep false |
   | Friction-denial (implicit) | friction but need implicitly dismissed | `"Friction detected but respondent implicitly denies need"` | Set `"uncertain"` |
   | Tension-friction gap | tension or org ≥ 3 but all friction = 1, or vice versa | `"Step 2 tension and step 3 friction diverge significantly"` | No change |
   | WTP-without-friction | `4_wtp`==`"כן"` but `potential_user: false` | `"Willing to pay but no friction detected"` | No change |
   | Category-score mismatch | high-conflict but median friction ≤ 2, or low-conflict with any ≥ 4 | `"Assigned category may not match scale data"` | No change |

### 3c — Write result

Merge into `{output_dir}/{test|survey}/processed/{id}.json` — add the `analysis` key **without overwriting** `schema_version`, `validation`, or `inconsistencies`:

```json
"analysis": {
  "conclusion": "...",
  "category": "...",
  "conclusion_one_liner": "...",
  "potential_user": true,
  "potential_payer": false,
  "coherence_warnings": ["..."]
}
```

`coherence_warnings` is omitted when empty.

Confirm completion to the researcher, then move to the next issue if processing all.

---

## Script templates

These scripts are generated artifacts — do not commit them. Write each via Python heredoc at startup if not already present.

### fetch_issues.py

```python
#!/usr/bin/env python3
"""
fetch_issues.py <issue_number> [<issue_number> ...]

Downloads GitHub Issues (survey responses) and saves them as raw JSON files.
Run this when network is available; process_issue.py can then run offline.
Idempotent -- skips if the raw file already exists.

Dependencies: gh CLI authenticated to the repo in survey.config.json.
Windows note: run with PYTHONUTF8=1 if console errors occur.
"""
import re
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_config():
    return json.loads((ROOT / "survey.config.json").read_text(encoding="utf-8"))


CFG = load_config()
REPO = CFG["gh_repo"]
ISSUE_BODY_KEY = CFG["issue_body_key"]
RESPONSES_DIR = ROOT / CFG["output_dir"]


def fetch_issue(issue_number: int) -> dict:
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", REPO, "--json", "body,createdAt"],
        capture_output=True, text=True, check=True, encoding="utf-8",
    )
    return json.loads(result.stdout)


def parse_payload(issue_data: dict) -> dict:
    body = issue_data["body"]
    key = ISSUE_BODY_KEY
    escaped = re.escape(key)
    pat1 = r'\|\s*' + escaped + r'\s*\|\s*(\{.+\})\s*\|'
    pat2 = r'^\|\s*(\{.+\})\s*\|\s*$'
    match = re.search(pat1, body) or re.search(pat2, body, re.MULTILINE)
    if not match:
        raise ValueError("Could not find survey_data in issue body")
    return json.loads(match.group(1))


def fetch_and_save(issue_number: int) -> None:
    print(f"Fetching issue #{issue_number} from {REPO}...")
    issue_data = fetch_issue(issue_number)
    payload = parse_payload(issue_data)
    survey_id = payload.get("survey_id", "unknown")
    file_stem = f"{issue_number}_{survey_id}"
    subdir = "test" if payload.get("_test") else "survey"

    raw_path = RESPONSES_DIR / subdir / "raw" / f"{file_stem}.json"
    if raw_path.exists():
        print(f"Already fetched: {raw_path.relative_to(ROOT)}")
        return

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_data = {"_issue_number": issue_number, "_created_at": issue_data["createdAt"], **payload}
    raw_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {raw_path.relative_to(ROOT)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_issues.py <issue_number> [<issue_number> ...]", file=sys.stderr)
        sys.exit(1)
    for arg in sys.argv[1:]:
        fetch_and_save(int(arg))


if __name__ == "__main__":
    main()
```

### process_issue.py

```python
#!/usr/bin/env python3
"""
process_issue.py <issue_number>

Validates a raw survey response JSON against the versioned schema and writes
a processed JSON file with validation results.
Idempotent -- skips if already processed.

Dependencies: jsonschema  (pip install jsonschema)
Windows note: run with PYTHONIOENCODING=utf-8 and PYTHONUTF8=1 if console errors occur.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

import jsonschema

ROOT = Path(__file__).parent.parent


def load_config():
    return json.loads((ROOT / "survey.config.json").read_text(encoding="utf-8"))


CFG = load_config()
RESPONSES_DIR = ROOT / CFG["output_dir"]
SCHEMAS_DIR = ROOT / CFG["schema_dir"]


def get_schema_version(created_at) -> str:
    versions = json.loads((SCHEMAS_DIR / "versions.json").read_text(encoding="utf-8"))
    if created_at is None:
        return max(versions.keys())
    submission_date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
    best_version, best_date = None, None
    for version, meta in versions.items():
        active_from = datetime.fromisoformat(meta["active_from"]).date()
        if active_from <= submission_date and (best_date is None or active_from > best_date):
            best_version, best_date = version, active_from
    if best_version is None:
        raise ValueError(f"No schema version covers submission date {submission_date}")
    return best_version


def _eval_condition(cond: dict, payload: dict) -> bool:
    if "any" in cond:
        return any(_eval_condition(c, payload) for c in cond["any"])
    if "all" in cond:
        return all(_eval_condition(c, payload) for c in cond["all"])
    raw = payload.get(cond["field"], None)
    threshold = cond["value"]
    if isinstance(threshold, int):
        lhs = int(raw) if raw is not None and str(raw).lstrip("-").isdigit() else 0
    else:
        lhs = raw if raw is not None else ""
    op = cond["op"]
    if op == ">=": return lhs >= threshold
    if op == ">":  return lhs > threshold
    if op == "<=": return lhs <= threshold
    if op == "<":  return lhs < threshold
    if op == "==": return lhs == threshold
    if op == "!=": return lhs != threshold
    if op == "contains":
        haystack = raw if raw is not None else ""
        return str(threshold) in haystack.split(", ")
    raise ValueError(f"Unknown op: {op}")


def load_schema(schema_version: str) -> dict:
    return json.loads((SCHEMAS_DIR / f"{schema_version}.json").read_text(encoding="utf-8"))


def validate_payload(payload: dict, schema: dict) -> dict:
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    violations = [
        {"field": ".".join(str(p) for p in e.path) or "(root)", "message": e.message}
        for e in errors
    ]
    conditional = schema.get("x-conditional-fields", {})
    if conditional:
        filtered = []
        for v in violations:
            missing_field = next(
                (f for f in conditional if f"'{f}' is a required property" == v["message"]),
                None,
            )
            if missing_field and not _eval_condition(conditional[missing_field]["shown_when"], payload):
                continue
            filtered.append(v)
        violations = filtered
    return {"valid": not violations, "violations": violations}


def detect_inconsistencies(payload: dict, schema: dict) -> list:
    conditional = schema.get("x-conditional-fields", {})
    inconsistencies = []
    for field, meta in conditional.items():
        if field not in payload:
            continue
        if not _eval_condition(meta["shown_when"], payload):
            inconsistencies.append({
                "field": field,
                "message": "Field present in payload but display condition not met",
            })
    return inconsistencies


def main():
    if len(sys.argv) != 2:
        print("Usage: process_issue.py <issue_number>", file=sys.stderr)
        sys.exit(1)

    issue_number = int(sys.argv[1])

    raw_files = list((RESPONSES_DIR / "test" / "raw").glob(f"{issue_number}_*.json"))
    subdir = "test"
    if not raw_files:
        raw_files = list((RESPONSES_DIR / "survey" / "raw").glob(f"{issue_number}_*.json"))
        subdir = "survey"
    if not raw_files:
        print(f"No raw file for issue #{issue_number}. Run: fetch_issues.py {issue_number}", file=sys.stderr)
        sys.exit(1)

    file_stem = raw_files[0].stem
    raw_path = raw_files[0]
    payload = json.loads(raw_path.read_text(encoding="utf-8"))

    analyzed_json = RESPONSES_DIR / subdir / "processed" / f"{file_stem}.json"
    if analyzed_json.exists():
        print(f"Already processed: {file_stem}. Skipping.")
        sys.exit(0)

    schema_version = get_schema_version(payload.get("_created_at"))
    print(f"Schema version: {schema_version}")

    schema = load_schema(schema_version)
    survey_payload = {k: v for k, v in payload.items() if not k.startswith('_')}

    validation = validate_payload(survey_payload, schema)
    status = "PASS" if validation["valid"] else f"FAIL ({len(validation['violations'])} violations)"
    print(f"Validation: {status}")

    inconsistencies = detect_inconsistencies(survey_payload, schema)
    if inconsistencies:
        print(f"Inconsistencies: {len(inconsistencies)}")

    analyzed_json.parent.mkdir(parents=True, exist_ok=True)
    analyzed_data = {
        "schema_version": schema_version,
        "validation": validation,
        "inconsistencies": inconsistencies,
        **({"test": True} if payload.get("_test") else {}),
    }
    analyzed_json.write_text(json.dumps(analyzed_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {analyzed_json.name}")
    print("Done.")


if __name__ == "__main__":
    main()
```
