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

ROOT = Path.cwd()


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
