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
