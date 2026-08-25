---
name: lint-and-format
description: Ensures code compiles clean under the project's linter and formatter before a change is considered done. Use whenever you create or edit source files in any language in this repo (Python, JS/JSX/TS/TSX, etc.), right before wrapping up a coding task.
---

Before treating any code change as finished, run the linter/formatter for every subproject you touched and fix what it reports. Never silence a rule just to make output go away unless you also leave a one-line comment explaining the specific, narrow reason.

## How to detect the right tool

Look for config files in the touched subproject (or its nearest ancestor directory) rather than assuming:

- `pyproject.toml` with `[tool.ruff]` → `ruff check .` and `ruff format .` (or `ruff format --check .` if you only want to verify)
- `pyproject.toml` with `[tool.mypy]` → `mypy .`
- `eslint.config.js` / `.eslintrc*` → `npx eslint .` (or the project's `npm run lint` script if one exists)
- `.prettierrc*` / `prettier` in `package.json` → `npx prettier --check .` (or `npm run format`)
- No config found for the language you're editing → don't invent one silently; flag it to the user instead of skipping the check quietly.

Prefer the project's own `package.json` scripts (`npm run lint`, `npm run format`) over calling the tool directly when a script exists — it already encodes the right flags and target paths.

## Workflow

1. After finishing an edit (or a batch of related edits), identify which subproject(s) changed.
2. Run that subproject's lint command. Run the formatter too if one is configured separately from the linter.
3. Fix reported issues in the code itself, not by widening ignore lists or disabling rules repo-wide.
4. If a tool reports pre-existing issues unrelated to your change, leave those alone — don't turn an unrelated cleanup into scope creep — but don't introduce new ones either.
5. Re-run after fixing to confirm a clean pass before calling the task done.

## When no lint tooling exists yet

If you're adding a new subproject or a language that has no linter configured, and the work you're doing already touches that subproject's tooling/config (e.g., you're setting up its `package.json` or `pyproject.toml` anyway), it's reasonable to add a minimal, standard linter/formatter as part of that work. Otherwise, don't add lint infrastructure as an unrequested side effect of an unrelated change — mention the gap to the user instead.
