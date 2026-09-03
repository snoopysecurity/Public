---

name: migration-commit-audit
description: Audit commits from a source branch one-by-one against a migration branch, verify equivalent behavior exists, and port missing changes without rebasing or merging.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Migration Commit Audit

Use this skill when one branch contains the original application and another branch contains a framework/platform migration of that application.

Typical example:

* Source branch: `dev`
* Migration branch: `react-migration`
* Source application: SvelteKit
* Migration application: React Native

The goal is to inspect every source-branch commit since the branches diverged and ensure its intended behavior is correctly represented in the migration branch.

## Safety rules

Never:

* rebase
* merge
* cherry-pick
* reset
* rewrite Git history
* modify the source branch
* blindly copy framework-specific implementation
* make unrelated refactors

The migration branch must remain checked out while performing the audit.

Changes should be ported manually and idiomatically for the target framework.

## Inputs

Determine or ask for these values if they cannot be inferred:

* `SOURCE_BRANCH`
* `MIGRATION_BRANCH`

Defaults when applicable:

* `SOURCE_BRANCH=dev`
* `MIGRATION_BRANCH=react-migration`

## Step 1: Verify repository state

Run Git commands to determine:

* current branch
* working-tree status
* source branch existence
* migration branch existence

Confirm the current branch is the migration branch.

If there are unrelated uncommitted changes, do not discard or overwrite them. Work around them safely and mention them in the final report.

Do not switch to the source branch unless inspection absolutely requires it. Prefer Git commands that inspect another branch directly.

## Step 2: Find the divergence point

Find the merge base between the source and migration branches.

Example conceptually:

`git merge-base SOURCE_BRANCH MIGRATION_BRANCH`

Then identify all commits on the source branch after that point.

Process commits in chronological order, oldest first.

The audit should effectively inspect:

`MERGE_BASE..SOURCE_BRANCH`

Do not assume commit messages accurately describe all changes. Inspect each diff.

## Step 3: Audit each source commit

Process exactly one source commit at a time.

Before modifying code, report:

`DEV COMMIT: <short hash> <commit message>`

`STATUS BEFORE: ALREADY COVERED | PARTIAL | MISSING | NOT APPLICABLE`

`Source change: <brief explanation of behavior or intent>`

`Migration equivalent: <where and how this behavior should exist>`

Inspect the complete commit diff and determine its actual behavioral intent.

Pay attention to both additions and removals.

## Step 4: Compare behavior, not files

Do not expect filenames, components, directories, routes, or architecture to match between frameworks.

Search the migration application for the equivalent:

* screen
* component
* hook
* context
* store
* reducer
* API client
* service
* utility
* type
* validation rule
* navigation behavior
* state transition
* UI state
* business rule

Translate intent into an idiomatic implementation for the target framework.

For SvelteKit → React Native migrations specifically:

Do not mechanically translate Svelte syntax.

Examples:

* Svelte stores may become React context, Zustand, Redux, hooks, or another existing state solution.
* SvelteKit routes may become React Navigation screens/routes.
* `$page` or route parameters may become navigation/route parameters.
* `load` functions may become hooks, queries, effects, loaders, or service calls.
* browser APIs may require React Native equivalents.
* CSS/layout changes may require React Native styles rather than direct property translation.
* web-only interaction patterns may require a native equivalent.

Preserve behavior rather than implementation shape.

## Step 5: Classify each commit

Use one of these classifications.

### ALREADY COVERED

Use when the migration branch already implements the commit's intended behavior correctly.

Do not modify code unnecessarily.

### PARTIAL

Use when some of the intended behavior exists but part of it is:

* missing
* incorrect
* outdated
* inconsistent with the source change

Implement only the missing or incorrect behavior.

### MISSING

Use when the source change has no equivalent implementation in the migration branch.

Implement the appropriate target-framework equivalent.

### NOT APPLICABLE

Use only when the commit is genuinely specific to the original platform/framework and has no meaningful equivalent.

Examples may include:

* browser-only metadata
* SvelteKit-specific build configuration
* server rendering behavior irrelevant to the native application
* web-only accessibility or DOM behavior with no native counterpart
* web deployment configuration

Explain why it is not applicable.

Do not classify something as NOT APPLICABLE merely because the implementation differs between platforms.

## Step 6: Areas requiring extra scrutiny

For every commit, explicitly consider whether it affects:

* API requests
* request payloads
* response handling
* authentication
* session state
* authorization
* state management
* TypeScript types
* schemas
* validation
* calculations
* business rules
* error handling
* loading states
* empty states
* retry behavior
* navigation
* route parameters
* deep linking
* conditional rendering
* feature flags
* permissions
* date/time handling
* timezone behavior
* formatting
* reusable utilities
* constants
* renamed API fields
* removed API fields
* API contracts
* analytics behavior
* caching
* persistence
* deleted or deprecated behavior

A small source diff may represent a significant behavioral change.

## Step 7: Implement the equivalent

For PARTIAL or MISSING commits:

1. Locate the correct target implementation.
2. Make the smallest focused change needed.
3. Preserve existing migration architecture and conventions.
4. Avoid unrelated cleanup.
5. Avoid introducing a second pattern when the React Native project already has an established pattern.
6. Update types when contracts changed.
7. Update or add tests where appropriate.

Do not create a Git commit unless explicitly instructed.

## Step 8: Validate each change

After implementing a source commit's equivalent behavior, run the most relevant available checks.

Prefer, where available:

* targeted tests
* unit tests
* TypeScript typecheck
* lint
* project-specific validation
* React Native tests
* Expo checks
* package scripts

Do not blindly run expensive commands when a narrower validation is sufficient.

If an important business rule changed and no test exists, add a focused test when practical.

If validation cannot be performed, state why.

## Step 9: Report after each commit

After reviewing and, if necessary, implementing the commit, output:

`STATUS AFTER: COVERED | NOT APPLICABLE`

`Files changed: <migration files changed, or none>`

`Validation: <checks performed and results>`

`Notes: <important details, risks, assumptions, or none>`

Then continue immediately to the next source commit.

Do not stop for confirmation between commits unless blocked by something that cannot safely be inferred.

## Step 10: Handle interacting commits

Evaluate each commit independently first, but remember that later commits may:

* modify earlier behavior
* revert earlier behavior
* rename something introduced earlier
* replace an earlier implementation
* fix a bug from an earlier commit

The final state of the source branch is authoritative.

Do not leave the migration branch matching an intermediate source state if a later source commit supersedes it.

## Step 11: Final cross-branch audit

After processing every source commit, perform a second high-level behavioral audit.

Compare the current source branch state against the migration branch and search for changes that commit-by-commit analysis may have missed.

Focus especially on:

* functionality spread across multiple commits
* renamed features
* deleted behavior
* API contract drift
* types that changed incrementally
* navigation differences
* new edge cases
* new validation
* state transitions
* shared utilities
* error/loading states

Fix any remaining clear migration gaps using the same rules.

Do not rebase or merge after the audit.

## Final report

Produce a table containing:

| Source commit | Commit message | Classification | Migration files | Validation | Concerns |
| ------------- | -------------- | -------------- | --------------- | ---------- | -------- |

Then summarize:

### Fully covered

Source changes verified as correctly represented in the migration.

### Not applicable

Source changes intentionally omitted because they are platform/framework specific.

### Remaining concerns

Anything that could not be verified confidently.

### Validation

List the final checks run and whether they passed.

### Git state

Report:

* current branch
* whether the working tree contains changes
* files modified during the audit

Finish with:

`Migration audit complete. No rebase, merge, cherry-pick, reset, or history rewrite was performed.`

## Default behavior for this repository

When this skill is used in the 3pmfootball repository without explicit branch arguments, use:

`SOURCE_BRANCH=dev`

`MIGRATION_BRANCH=react-migration`

Treat `dev` as the SvelteKit implementation and `react-migration` as the React Native implementation.
