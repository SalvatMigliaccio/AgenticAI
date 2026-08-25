---
name: no-duplicate-code
description: Enforces DRY (don't repeat yourself) before adding new code. Use whenever you're about to write a new function, component, hook, class, or non-trivial block of logic anywhere in this repo.
---

Before writing new logic, search the codebase for something that already does it, or most of it.

## Before writing anything new

1. Grep/search for existing functions, components, hooks, or utilities with a similar name or similar purpose in the subproject you're editing (and in shared/`lib`/`utils`/`common` locations if the subproject has one).
2. If something close already exists:
   - If it does exactly what you need: import and reuse it, don't re-implement it.
   - If it does almost what you need: extend it (add a parameter, an option) rather than forking a near-copy.
   - Only write a parallel implementation when the existing one is a genuinely different concern that happens to look similar — and say why, briefly, in a comment or in your summary to the user.

## Spotting duplication you're about to introduce

Treat these as signals you're duplicating rather than reusing:

- Copy-pasting a block of code from one file to another and changing a few identifiers.
- Two functions/components in the same subproject with near-identical bodies (parsing the same shape of data, building the same kind of request, rendering the same layout with slightly different labels).
- Re-deriving a constant, config value, or mapping (e.g. a color map, a set of API routes, a domain registry) that already lives somewhere else in the codebase.

## When to extract a shared abstraction

Don't pre-emptively extract a helper the first time you see similar code — two similar-looking call sites are often a coincidence. Extract a shared function/component/hook once you have a **third** real call site, or once you're about to add a second copy of something that's already non-trivial (more than a few lines, or with any branching logic). Name the extracted piece for what it does, not for the callers that happen to use it today.

## During review

When reviewing a diff (yours or someone else's), flag any newly added block that closely mirrors existing code elsewhere in the same subproject, and suggest the concrete reuse instead of describing the problem abstractly.
