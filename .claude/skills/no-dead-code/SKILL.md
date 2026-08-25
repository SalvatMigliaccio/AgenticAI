---
name: no-dead-code
description: Flags and removes dead code — unused imports/exports, declared-but-unreferenced dependencies, unreachable files, commented-out code left behind. Use after finishing an edit, and whenever you're about to add a new dependency or remove a feature.
---

Code that exists but nothing uses is a maintenance cost with no offsetting benefit. Treat leaving it behind as a bug, not a style nit.

## After finishing an edit

- If you removed the last usage of a function, component, variable, or import, delete the now-unused declaration too — don't leave it "just in case."
- If you removed a feature that was the only consumer of a dependency (an npm package, a Python package), remove that dependency from `package.json` / `pyproject.toml` as well. A dependency that's declared but never imported anywhere in the source tree is dead weight (extra install time, extra attack surface, misleading to future readers about what the project actually uses).
- Delete commented-out code you're replacing rather than leaving it next to the new version. Git history already preserves it if it's ever needed again.
- If an edit leaves a file with no remaining exports anyone imports, or a component that's no longer rendered anywhere, remove the file instead of leaving an orphan.

## Before adding a new dependency

Check whether an existing dependency already covers the need before adding a new one — two libraries doing the same job is its own form of duplication.

## Spot-checking for existing dead code

When you're already working in a file or package, it's reasonable to do a quick check (grep for the import/usage) of anything that looks suspiciously unused nearby, and remove it as part of the same change — but don't go on an unrelated dead-code hunt across the whole repo unless the user asked for that specifically.

## Verifying "unused"

Before deleting something as dead, actually confirm it: grep for every import path an item could be reached by (including re-exports, dynamic `import()`, string-based lookups, and framework auto-registration patterns), not just its literal name. A false positive here breaks the build; check before you cut.
