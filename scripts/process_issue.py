#!/usr/bin/env python3
"""
process_issue.py <issue_number>

Fetches a GitHub Issue (survey response), validates it against the versioned schema,
and writes raw + processed files plus a pre-filled read-only HTML view.
Idempotent — skips if already processed.

Dependencies: jsonschema  (pip install jsonschema)
Windows note: run with PYTHONIOENCODING=utf-8 and PYTHONUTF8=1 if console errors occur.
"""
import re
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

import jsonschema

REPO = "amirgott/GrooshiSurveyData"
ROOT = Path(__file__).parent.parent
RESPONSES_DIR = ROOT / "responses"
SCHEMAS_DIR = RESPONSES_DIR / "schemas"
INDEX_HTML = ROOT / "index.html"


def fetch_issue(issue_number: int) -> dict:
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", REPO, "--json", "body,createdAt"],
        capture_output=True, text=True, check=True, encoding="utf-8",
    )
    return json.loads(result.stdout)


def parse_payload(issue_data: dict) -> dict:
    body = issue_data["body"]
    # Issue body is a Markdown table; extract the survey_data cell value
    match = re.search(r'\|\s*survey_data\s*\|\s*(\{.*\})\s*\|', body)
    if not match:
        raise ValueError("Could not find survey_data in issue body")
    return json.loads(match.group(1))


def get_schema_version(created_at: str) -> str:
    versions = json.loads((SCHEMAS_DIR / "versions.json").read_text(encoding="utf-8"))
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
    # leaf node
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
            # "required property" violations have the field name embedded in the message
            missing_field = next(
                (f for f in conditional if f"'{f}' is a required property" == v["message"]),
                None,
            )
            if missing_field and not _eval_condition(conditional[missing_field]["shown_when"], payload):
                continue  # field was hidden — not a violation
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
                "message": f"Field present in payload but display condition not met",
            })
    return inconsistencies


def _build_analysis_card(analysis: dict, survey_id: str) -> str:
    """Build the static HTML for the step0 analysis card."""
    criteria_row = (
        '<tr><td colspan="2" style="padding:6px 12px;font-style:italic;color:#9ca3af;'
        'font-size:0.75rem;border-bottom:1px solid #e5e7eb;white-space:pre-wrap">'
        '# potential_user: true if (any Part1\u20134 scale &gt; 1 OR binary friction flag) AND no explicit/implicit need denial\n'
        '# potential_payer: true if potential_user AND 5.2_willing_to_pay == \u05db\u05df'
        '</td></tr>'
    )
    rows = ''.join(
        '<tr>'
        f'<td style="padding:8px 12px;font-weight:600;white-space:nowrap;color:#374151;border-bottom:1px solid #e5e7eb;vertical-align:top">{k}</td>'
        f'<td style="padding:8px 12px;color:#1f2937;border-bottom:1px solid #e5e7eb">{"true" if v is True else "false" if v is False else v}</td>'
        '</tr>'
        for k, v in analysis.items()
    )
    return (
        f'<div class="step active" id="step0">'
        f'<div style="padding:2rem 0">'
        f'<div style="border-bottom:1px solid #e5e7eb;padding-bottom:1rem;margin-bottom:1.5rem">'
        f'<h1 style="font-size:1.25rem;font-weight:700;color:#312e81">\u05e0\u05d9\u05ea\u05d5\u05d7 \u05ea\u05d2\u05d5\u05d1\u05d4 \u2014 {survey_id}</h1>'
        f'</div>'
        f'<div dir="ltr" style="overflow-x:auto">'
        f'<table style="width:100%;border-collapse:collapse;font-size:0.875rem;font-family:monospace">'
        f'<thead><tr>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;color:#6b7280;border-bottom:2px solid #e5e7eb">key</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;color:#6b7280;border-bottom:2px solid #e5e7eb">value</th>'
        f'</tr></thead>'
        f'<tbody>{criteria_row}{rows}</tbody>'
        f'</table>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def generate_prefilled_html(payload: dict, output_path: Path, analysis: dict = None) -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    # Exclude meta fields (underscore-prefixed) — not survey form fields
    form_data = {k: v for k, v in payload.items() if not k.startswith('_')}
    payload_json = json.dumps(form_data, ensure_ascii=False)

    # Replace step0 statically in the HTML (works without JS execution)
    if analysis:
        card = _build_analysis_card(analysis, payload.get("survey_id", ""))
        html = re.sub(
            r'<!-- STEP 0: Welcome -->.*?(?=<!-- STEP 1:)',
            f'<!-- STEP 0: Analysis -->\n            {card}\n\n            ',
            html,
            flags=re.DOTALL,
        )
        step0_css = ""
    else:
        step0_css = "\n#step0 { display: none !important; }"

    # Injected script: restores all field values then disables the form.
    # Schema-independent: no field names or JS function names are hardcoded.
    # Uses string concatenation for querySelector calls (avoids JS template
    # literals conflicting with Python f-string syntax).
    inject = f"""<style>
/* Pre-filled read-only view — show all steps on one page */
.step {{ display: block !important; }}{step0_css}
.scale-btn {{ cursor: default; }}
</style>
<script>
/* Pre-filled read-only view — generated by process_issue.py */
document.addEventListener('DOMContentLoaded', function() {{
  const data = {payload_json};

  function fillFields() {{
    for (const [key, value] of Object.entries(data)) {{
      // Radio buttons
      document.querySelectorAll('input[type="radio"][name="' + key + '"]').forEach(el => {{
        el.checked = (el.value === value);
      }});

      // Checkboxes (payload value is comma-joined)
      const vals = value.split(', ');
      document.querySelectorAll('input[type="checkbox"][name="' + key + '"]').forEach(el => {{
        el.checked = vals.includes(el.value);
      }});

      // Text / number / tel / email / select / textarea
      const textEl = document.querySelector(
        'input[type="text"][name="' + key + '"],' +
        'input[type="number"][name="' + key + '"],' +
        'input[type="tel"][name="' + key + '"],' +
        'input[type="email"][name="' + key + '"],' +
        'textarea[name="' + key + '"],' +
        'select[name="' + key + '"]'
      );
      if (textEl) textEl.value = value;

      // Hidden inputs (scales and toggle-multi fields) — set value and mark buttons
      const hidden = document.querySelector('input[type="hidden"][name="' + key + '"]');
      if (hidden) {{
        hidden.value = value;
        // Scale buttons: matched by hidden input id in onclick
        const hid = hidden.id;
        if (hid) {{
          document.querySelectorAll('.scale-btn').forEach(btn => {{
            const oc = btn.getAttribute('onclick') || '';
            if (btn.dataset.value === value && oc.includes("'" + hid + "'")) {{
              btn.classList.add('selected');
            }}
          }});
        }}
        // Toggle-multi buttons: matched by field name in onclick, value from third arg
        const vals = value.split(', ');
        document.querySelectorAll('.toggle-btn').forEach(btn => {{
          const oc = btn.getAttribute('onclick') || '';
          if (oc.includes("'" + key + "'")) {{
            const m = oc.match(/toggleMulti\(this,'[^']+','([^']+)'\)/);
            if (m && vals.includes(m[1])) btn.classList.add('selected');
          }}
        }});
        // selectSafety single-select buttons: matched by value in onclick
        document.querySelectorAll('.toggle-btn').forEach(btn => {{
          const oc = btn.getAttribute('onclick') || '';
          const m = oc.match(/selectSafety\(this,\s*'([^']+)'\)/);
          if (m && m[1] === value) btn.classList.add('selected');
        }});
      }}
    }}
  }}

  // First pass: fill all static fields
  fillFields();

  // Trigger input events — causes any dynamic field generators to run
  document.querySelectorAll('input, select').forEach(el => {{
    el.dispatchEvent(new Event('input', {{bubbles: true}}));
  }});

  // Second pass: fill any fields that were dynamically generated above
  fillFields();

  // Trigger change events to reveal conditional sections
  document.querySelectorAll('input[type="checkbox"], input[type="radio"], select').forEach(el => {{
    el.dispatchEvent(new Event('change', {{bubbles: true}}));
  }});

  // Disable all interactive elements
  document.querySelectorAll('input, textarea, select, button').forEach(el => {{
    el.disabled = true;
  }});
}});
</script>
"""
    html = html.replace("</body>", inject + "\n</body>")
    output_path.write_text(html, encoding="utf-8")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--update-html":
        issue_number = int(sys.argv[2])
        raw_files = list((RESPONSES_DIR / "raw").glob(f"{issue_number}_*.json"))
        if not raw_files:
            print(f"No raw file found for issue #{issue_number}", file=sys.stderr)
            sys.exit(1)
        stem = raw_files[0].stem
        raw_path = raw_files[0]
        processed_path = RESPONSES_DIR / "processed" / f"{stem}.json"
        html_path = RESPONSES_DIR / "processed" / f"{stem}.html"
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        processed = json.loads(processed_path.read_text(encoding="utf-8"))
        analysis = processed.get("analysis")
        generate_prefilled_html(payload, html_path, analysis=analysis)
        print(f"Updated HTML: {html_path.name}")
        return

    if len(sys.argv) != 2:
        print("Usage: process_issue.py <issue_number>", file=sys.stderr)
        sys.exit(1)

    issue_number = int(sys.argv[1])
    print(f"Fetching issue #{issue_number} from {REPO}...")

    issue_data = fetch_issue(issue_number)
    payload = parse_payload(issue_data)
    survey_id = payload.get("survey_id", "unknown")
    file_stem = f"{issue_number}_{survey_id}"

    # Idempotency check
    analyzed_json = RESPONSES_DIR / "processed" / f"{file_stem}.json"
    if analyzed_json.exists():
        print(f"Already processed: {file_stem}. Skipping.")
        sys.exit(0)

    # Save raw
    raw_path = RESPONSES_DIR / "raw" / f"{file_stem}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_data = {"_issue_number": issue_number, **payload}
    raw_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved raw: {raw_path.name}")

    # Schema version
    schema_version = get_schema_version(issue_data["createdAt"])
    print(f"Schema version: {schema_version}")

    # Load schema once; used for validation and inconsistency detection
    schema = load_schema(schema_version)

    # Strip internal metadata fields before validation
    survey_payload = {k: v for k, v in payload.items() if not k.startswith('_')}

    # Validate
    validation = validate_payload(survey_payload, schema)
    status = "PASS" if validation["valid"] else f"FAIL ({len(validation['violations'])} violations)"
    print(f"Validation: {status}")

    # Mechanical inconsistency detection
    inconsistencies = detect_inconsistencies(survey_payload, schema)
    if inconsistencies:
        print(f"Inconsistencies: {len(inconsistencies)}")

    # Save analyzed
    analyzed_json.parent.mkdir(parents=True, exist_ok=True)  # creates responses/processed/ if needed
    analyzed_data = {
        "schema_version": schema_version,
        "validation": validation,
        "inconsistencies": inconsistencies,
        **({"test": True} if payload.get("_test") else {}),
    }
    analyzed_json.write_text(json.dumps(analyzed_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved analyzed: {analyzed_json.name}")

    # Generate pre-filled HTML
    analyzed_html = RESPONSES_DIR / "processed" / f"{file_stem}.html"
    generate_prefilled_html(payload, analyzed_html)
    print(f"Generated HTML: {analyzed_html.name}")

    print("Done.")


if __name__ == "__main__":
    main()
