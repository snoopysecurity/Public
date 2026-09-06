---
name: database-design-reviewer
description: Review a proposed application database design against the actual repository and identify modeling mistakes, missing constraints, inefficient relationships, indexing problems, integrity risks, concurrency issues, authorization/tenant risks, historical-data problems, overengineering, and mismatches between the schema and real code paths. Use when the user asks Codex to review, audit, critique, validate, or improve a database/schema/data model using the codebase as evidence. Default to read-only analysis and do not modify the repository unless the user explicitly asks for implementation.
---

# Database Design Reviewer

## Objective

Audit a proposed database design against the application that actually exists.

Treat the repository as evidence. Do not review the schema in isolation and do not give generic database advice.

Default to **read-only analysis**. Do not edit migrations, schemas, models, code, or documentation unless the user explicitly asks for implementation.

## Inputs

Determine the database-design source from the user's request.

Prefer, in order:

1. An explicitly supplied Markdown/schema file path.
2. A clearly named database-design document in the repository.
3. Existing schema/ORM/migration files if the user asks for an audit without a separate design document.

If several plausible design documents exist, inspect them and use the one that is clearly authoritative. State any material ambiguity in the final review rather than blocking the analysis unnecessarily.

## Workflow

### 1. Read the proposed design completely

Read the full design before evaluating individual tables.

Capture:

- entities and tables
- fields and types
- primary and foreign keys
- uniqueness rules
- nullable fields
- relationships and cardinalities
- indexes
- enums
- JSON/array fields
- delete behavior
- lifecycle assumptions
- stated invariants
- tenancy/ownership rules

Do not assume the design is correct.

### 2. Build an application model from the repository

Inspect relevant repository areas before reaching conclusions.

Look for:

- ORM/schema definitions
- migrations
- SQL
- repositories and data-access layers
- services/use cases
- API routes/controllers
- server actions
- domain models
- types/interfaces
- validation schemas
- authentication and authorization
- background jobs
- queues
- webhooks
- event handlers
- search
- caching
- analytics/reporting
- seed data
- tests
- existing documentation

Trace important entities through their real lifecycle:

- create
- read
- update
- delete/archive
- restore
- authorize
- filter
- sort
- join
- aggregate
- paginate
- search

Prefer actual executable code and tests over stale comments or docs.

### 3. Compare domain concepts to tables

For each major table/entity:

1. Identify the domain concept it represents.
2. Find the matching code paths.
3. Determine ownership.
4. Determine lifecycle.
5. Determine relationship cardinality.
6. Determine common read/write patterns.
7. Determine invariants.
8. Compare those requirements with the proposed design.
9. Record concrete discrepancies.

Flag concepts required by the codebase but absent from the design.

Flag schema concepts that appear unused, redundant, or overengineered.

### 4. Validate relationships

Explicitly review important relationships as:

- one-to-one
- one-to-many
- many-to-many

Check whether each relationship needs:

- a foreign key
- a join table
- relationship metadata
- ordering
- uniqueness
- composite uniqueness
- restricted deletion
- cascading deletion
- soft deletion
- tenant/owner identity

Challenge suspicious cardinalities.

### 5. Review data integrity

Find application invariants that the database should potentially enforce.

Consider:

- PRIMARY KEY
- FOREIGN KEY
- UNIQUE
- composite UNIQUE
- NOT NULL
- CHECK
- exclusion constraints where supported
- transaction boundaries

Look specifically for invalid states that application-only validation could allow through concurrency, bugs, scripts, jobs, or future code paths.

Also identify constraints that would be unnecessarily restrictive.

### 6. Review sources of truth

Look for duplicated or derivable data.

Classify duplication as:

- intentional denormalization
- cached/derived data
- historical snapshot
- accidental duplication
- synchronization risk

Prefer one authoritative source unless duplication has a concrete reason.

Identify:

- persisted fields that should be derived
- derived fields that should be persisted for historical correctness or performance
- multiple representations of the same business state

### 7. Review query patterns and indexes

Infer indexes from actual access patterns.

For each important query path, consider:

- equality filters
- range filters
- joins
- sorting
- compound filters
- pagination
- uniqueness lookups
- LIKE/search/full-text behavior
- aggregates
- reporting

Do not recommend indexes generically.

For each recommended index, state:

- table
- columns in order
- unique/non-unique
- partial/filtered condition if relevant
- code/query path it supports
- expected benefit
- material write/storage tradeoff if relevant

Look for:

- likely table scans
- poor composite-index ordering
- N+1 access patterns
- expensive joins
- offset-pagination issues on large datasets
- duplicate indexes
- indexes with little realistic value

### 8. Review lifecycle and deletion

For important records determine:

- creation semantics
- mutability
- archival
- soft delete
- hard delete
- restore behavior
- retention requirements

Flag:

- orphan risks
- dangerous cascades
- deletion that destroys required history
- uniqueness behavior with soft-deleted rows

### 9. Review concurrency and transactions

Inspect workflows involving:

- counters
- balances
- inventory
- quotas
- reservations
- status transitions
- payments
- job claiming
- check-then-insert flows
- idempotent requests
- simultaneous edits

Recommend database mechanisms when justified:

- transactions
- atomic updates
- row locks
- optimistic concurrency/version columns
- uniqueness constraints
- idempotency keys

Explain the race condition, not just the mechanism.

### 10. Review historical correctness

Identify records whose historical meaning must not change when referenced mutable data changes.

Check areas such as:

- prices
- product names/descriptions
- addresses
- customer identity
- permissions
- subscription plans
- invoices
- financial values
- configuration
- statuses

Recommend snapshots or immutable history only where the application's semantics require them.

### 11. Review authorization and tenancy

Map the schema to the authorization model.

Check whether every sensitive record can be unambiguously tied to its:

- user
- account
- workspace
- organization
- tenant

Flag:

- cross-tenant access risks
- ownership inferred through fragile multi-hop joins
- inconsistent tenant keys
- resources with ambiguous ownership
- uniqueness constraints that should be tenant-scoped
- relationships that could cross tenant boundaries accidentally

If row-level security or database policies are used, compare them against application authorization logic.

### 12. Review scalability without premature optimization

Estimate which tables may grow fastest.

Typical candidates:

- events
- logs
- audit records
- messages
- notifications
- analytics
- history
- join tables
- high-frequency transactional tables

Separate recommendations into:

- **Fix now** — correctness or expensive-to-change-later issues
- **Design for now** — modest choices that prevent predictable problems
- **Revisit at scale** — optimizations that should not complicate the current design yet

### 13. Check codebase inconsistencies

While auditing the schema, flag code issues that materially affect the data model:

- inconsistent domain terminology
- duplicate models/types
- conflicting validation
- frontend/backend disagreement
- stale fields
- duplicated business rules
- code compensating for a weak schema
- undocumented query assumptions

Do not turn this into a general code review. Keep findings relevant to persistence and data modeling.

## Evidence Standard

Tie every significant finding to evidence from:

- the proposed design
- repository code
- tests
- migrations
- queries
- validation
- authorization logic

Reference exact file paths and relevant symbols/functions where practical.

Distinguish clearly between:

- **Observed** — directly supported by the repository/design
- **Inferred** — strongly implied by usage
- **Speculative** — possible future concern without current evidence

Do not present speculative scale concerns as current defects.

## Severity

Use:

### CRITICAL
Data corruption, security exposure, fundamental correctness failure, or an unreliable critical workflow.

### HIGH
Major architectural/integrity/performance issue or a decision that becomes costly after production data accumulates.

### MEDIUM
Meaningful weakness worth correcting but unlikely to immediately break the application.

### LOW
Cleanup, simplification, consistency, or non-blocking optimization.

## Required Output

Produce the review using this structure.

# 1. Executive Summary

Include:

- overall assessment
- strongest parts of the design
- largest weaknesses
- 3–7 most important changes before implementation

# 2. Application & Domain Model

Explain the application behavior inferred from the repository.

List major domain entities and relationships.

Call out domain concepts missing from the proposed schema.

# 3. Critical & High-Priority Findings

For each finding use:

**Severity:**  
**Affected tables/entities:**  
**Evidence:**  
**Current design:**  
**Problem:**  
**Why it matters:**  
**Recommended design:**  
**Implementation/migration considerations:**

Order by severity and practical impact.

# 4. Table-by-Table Review

For every proposed table:

## `<table_name>`

**Purpose**  
**Relevant code**  
**Good decisions**  
**Problems**  
**Recommended changes**  
**Constraints**  
**Indexes**

Do not invent criticism merely to fill sections. Say when a table is well designed.

# 5. Relationship Review

Identify incorrect, questionable, or especially important cardinalities and ownership relationships.

Provide the recommended model.

# 6. Missing Database Concepts

List missing:

- tables
- columns
- relationship metadata
- constraints
- historical snapshots
- ownership/tenant fields
- lifecycle fields

Only include items supported by repository behavior.

# 7. Potentially Unnecessary Concepts

Identify redundant tables, columns, abstractions, duplicated state, or overengineering.

# 8. Data Integrity Risks

Use:

`Invalid state -> How it can occur -> Database mechanism that prevents it`

# 9. Query & Index Analysis

For each important pattern include:

- code path
- approximate query shape
- schema impact
- recommended index/schema adjustment

Then provide:

| Table | Index | Type | Supports | Priority |
|---|---|---|---|---|

# 10. Concurrency & Transaction Risks

Explain concrete race conditions and the appropriate transactional/database guarantees.

# 11. Security / Tenant Isolation

Describe persistence-layer authorization and tenant-isolation risks.

# 12. Scalability

Use:

## Fix now

## Design for now

## Revisit at scale

# 13. Proposed Improved Schema

Provide a revised model using the technology already present in the repository when practical:

- SQL DDL
- Prisma
- Drizzle
- ORM models
- Mermaid ER diagram
- concise Markdown schema

Do not rewrite unchanged portions merely for cosmetic consistency.

# 14. Recommended Database Invariants

Provide a concise list such as:

```text
users.email -> UNIQUE
workspace_members(workspace_id, user_id) -> UNIQUE
orders.total_amount >= 0 -> CHECK
```

# 15. Recommended Implementation Order

Describe the safest dependency-aware order for:

- schema changes
- migrations
- backfills
- application changes
- constraints
- indexes

# 16. Open Questions

Only include questions whose answer materially changes the architecture.

For each:

**Question:**  
**Why it matters:**  
**Design A if X:**  
**Design B if Y:**  
**Best current recommendation:**

Do not use questions to avoid making a recommendation.

# 17. Final Verdict

**Keep as-is:**  
**Change before implementation:**  
**Can wait:**

## Operating Principles

- Treat code as evidence.
- Prefer executable behavior and tests over comments.
- Prefer simple relational modeling.
- Protect integrity before optimizing performance.
- Base indexes on real access patterns.
- Challenge the proposed architecture when necessary.
- Avoid speculative complexity.
- Distinguish correctness issues from optional optimizations.
- Explain why each major recommendation matters.
- Do not modify the repository unless explicitly asked.
