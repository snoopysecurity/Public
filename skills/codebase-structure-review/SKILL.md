---
name: codebase-structure-review
description: Review a codebase for structural friction, identify high-value architectural improvements, and produce a concise Markdown report before exploring a chosen candidate.
disable-model-invocation: true
---

# Codebase Structure Review

Find places where the codebase creates unnecessary cognitive load, weak ownership, awkward testing, or excessive navigation.

Prioritize changes that make important behavior easier to understand, modify, and test.

Do not optimize for abstraction count, file count, or architectural purity.

## Context

Before reviewing an area, read relevant project context when available:

- `GLOSSARY.md`
- ADRs in `docs/adr/`
- nearby documentation
- tests
- recent Git history

Use the project's own domain language.

Treat existing ADRs as constraints unless there is strong evidence they should be revisited.

# Process

## 1. Pick the review area

If the user names a module, feature, subsystem, or pain point, start there.

Otherwise inspect recent history:

```bash
git log --oneline --stat
```

Look for areas that change frequently or files that repeatedly change together.

Prefer reviewing active code over stable areas with little change pressure.

## 2. Explore structural friction

Walk the selected area and look for:

- behavior spread across too many small modules
- abstractions that expose nearly as much complexity as they hide
- callers that must understand internal sequencing
- small changes that require touching many files
- tests coupled to helpers or orchestration details
- repeated data translation between nearby modules
- unclear ownership of important domain concepts

For each suspected problem, ask:

> If this abstraction disappeared or responsibilities moved, would complexity become easier to locate and own, or would it simply move elsewhere?

Discard candidates that only rearrange code.

Prefer a few strong opportunities over many speculative ones.

## 3. Write the report

Create a Markdown file in the OS temp directory:

```text
codebase-structure-review-<timestamp>.md
```

Use `$TMPDIR`, `/tmp`, or `%TEMP%` depending on the platform.

Do not write the report into the repository unless the user asks.

Use this structure:

```markdown
# Codebase Structure Review

## Scope

What was reviewed and why.

## Summary

The main structural pattern or source of friction.

## Opportunity 1 — <title>

**Files**
Relevant files or modules.

**Problem**
What makes the current structure difficult to understand, change, or test.

**Direction**
What responsibility should move, consolidate, or become hidden.

**Why it helps**
Explain the effect on ownership, change locality, navigation, and testing.

**Before**
```text
Current structure
```

**After**
```text
Possible target shape
```

**Evidence**
Concrete observations from code, tests, or Git history.

**Confidence**
High / Medium / Exploratory

**Trade-offs**
What could become worse or more constrained.

**ADR notes**
Mention relevant ADRs or conflicts only when material.
```

Aim for 3–5 opportunities unless fewer are genuinely worthwhile.

Use Mermaid only when it communicates the structure more clearly than text.

## 4. Recommend where to investigate first

End with:

```markdown
# Suggested starting point

## <candidate>

Explain why this area has the strongest combination of current friction, change frequency, expected simplification, and manageable risk.
```

Do not design the final interface yet.

After writing the report, tell the user the absolute path and ask:

> Which opportunity do you want to explore in detail?

# Follow-up design

Once the user picks a candidate, work through:

- what responsibility belongs together
- what should remain outside
- what callers should no longer need to know
- where external dependencies enter
- what tests should survive
- what migration path keeps the change manageable

If there are multiple credible designs, compare at least two before choosing.

Keep `GLOSSARY.md` and ADRs current when a durable architectural decision or important domain term emerges.

# Guardrails

Do not:

- perform unrelated cleanup
- add abstractions just because code is duplicated
- split code only for unit-testability
- merge modules only because they are small
- ignore existing architectural decisions
- redesign stable areas without evidence of friction
- propose detailed interfaces before the user selects a candidate

The output should be a short list of concrete structural improvements, not a general code-quality audit.
