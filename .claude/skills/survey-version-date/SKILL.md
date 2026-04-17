---
description: "Derive the survey version date from git history of given file paths."
argument-hint: "--schema <path> --html <path> (either or both)"
---

## Purpose

Outputs a single `YYYY-MM-DD` date representing when the current survey version was established. The caller is responsible for supplying the relevant file paths — this skill does not read any project config.

---

## Steps

1. Parse arguments. Accepted flags (either or both must be provided):
   - `--schema <path>` — path to the active schema file
   - `--html <path>` — path to the survey HTML file

2. For each provided path, run:
   ```
   git log -1 --format=%ci -- <path>
   ```
   Extract the date part (`YYYY-MM-DD`). If a path was not provided or the command returns nothing, skip it.

3. Use the **earlier** of the available dates. Rationale: the schema commit marks when the version contract was established; the HTML may have been updated later for cosmetic reasons unrelated to the version boundary.

4. If no date was obtained from any path, output: `Could not determine survey version date — no git history found for the provided paths.` and stop, letting the caller decide how to proceed.

5. Output the date as a plain string: `YYYY-MM-DD`