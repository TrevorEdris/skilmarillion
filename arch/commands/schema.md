---
description: Guided database schema design producing PostgreSQL DDL and a zero-downtime migration plan
argument-hint: "[schema name or domain description]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
  - ToolSearch
model: sonnet
---

# /arch:schema

Guided database schema design session. Produces two artifacts:
1. **Schema DDL** — PostgreSQL `CREATE TABLE` statements with constraints and indexes
2. **Migration plan** — Zero-downtime expand-contract migration steps

---

## ON STARTUP

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

---

## Flow

### 1. Input Resolution

- If an argument is provided: use it as the schema name or domain description.
- If no argument: ask the user to describe the domain they want to model.

### 2. Design Interview

Walk through each topic one question at a time. Do not batch — wait for the user's answer before proceeding.

#### 2a. Entities and Relationships

Ask:

> What are the core entities in this domain? For each entity, list the key attributes you know about.

After the user responds, confirm the entity list and ask:

> What are the relationships between these entities? (e.g., "a user has many orders", "an order belongs to one user")

Capture cardinality for each relationship: one-to-one, one-to-many, or many-to-many.

#### 2b. Access Patterns

Ask:

> How will the application query this data? List the most common read and write operations.

Use the answers to inform indexing and denormalization decisions later.

#### 2c. Constraints and Business Rules

Ask:

> Are there any business rules that the schema must enforce? Examples:
> - Uniqueness (email must be unique)
> - Required fields (order must have a total)
> - Value ranges (quantity must be positive)
> - Referential integrity (what happens when a parent record is deleted?)

#### 2d. Scale and Performance

Ask:

> Any scale hints? (expected row counts, read/write ratio, hot tables)

If the user says "not sure" or "typical", assume OLTP workload with moderate scale and note the assumption.

#### 2e. Normalization Trade-offs

If the access patterns suggest read-heavy queries that would require expensive joins, present the trade-off:

> For the `{query}` access pattern, we can:
> 1. **Normalize (3NF)** — no data duplication, but requires a JOIN on every read
> 2. **Denormalize** — duplicate `{field}` on `{table}` to avoid the JOIN, at the cost of maintaining consistency on writes
>
> Which approach fits your use case?

If access patterns are straightforward, skip this question and default to 3NF.

### 3. Schema Generation

Produce a complete PostgreSQL DDL script following these rules:

#### Primary Keys
- Use `BIGINT GENERATED ALWAYS AS IDENTITY` for sequential IDs
- Use `UUID` with `gen_random_uuid()` default if the user specifies distributed systems or external-facing IDs
- Every table must have a primary key

#### Data Types
- Money: `NUMERIC(12,2)`, never `FLOAT` or `REAL`
- Email/URL: `TEXT` with a `CHECK` constraint for length, not `VARCHAR(255)`
- Timestamps: `TIMESTAMPTZ`, never `TIMESTAMP` without timezone
- Booleans: `BOOLEAN` with a `DEFAULT`, never nullable booleans
- Enums: PostgreSQL `CREATE TYPE ... AS ENUM(...)`, not string columns

#### Constraints
- `NOT NULL` on all required fields
- `UNIQUE` where business rules demand it
- `CHECK` constraints for value ranges and format validation
- Foreign keys with explicit `ON DELETE` action (`CASCADE`, `SET NULL`, or `RESTRICT` — never leave it implicit)

#### Indexes
- Every foreign key column gets an index
- Columns in frequent `WHERE` clauses get an index
- Multi-column indexes follow leftmost-prefix order matching the query pattern
- Partial indexes where appropriate (e.g., `WHERE deleted_at IS NULL`)

#### Timestamps
- Every table gets `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
- Every mutable table gets `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` with a note to use a trigger or application-level update

#### Many-to-Many
- Junction tables with a composite primary key `(left_id, right_id)`
- Both foreign key columns indexed (the composite PK covers one direction; add a reverse index)

#### Format

Output the DDL as a single fenced SQL block. Order tables so that referenced tables appear before referencing tables (dependency order).

Example structure:

```sql
-- Schema: {name}
-- Generated: {date}
-- Engine: PostgreSQL 15+

-- Types
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled');

-- Tables (dependency order)
CREATE TABLE users (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE CHECK (length(email) <= 320),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status      order_status NOT NULL DEFAULT 'pending',
    total       NUMERIC(12,2) NOT NULL CHECK (total >= 0),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
```

### 4. Migration Plan

After presenting the schema, produce a zero-downtime migration plan.

#### 4a. Expand-Contract Pattern

For every schema change that is not purely additive, apply the expand-contract pattern:

**Expand phase** (additive, backward-compatible):
- Add new columns as `NULL` (no `NOT NULL` yet)
- Add new tables
- Add new indexes (`CONCURRENTLY` in PostgreSQL)
- Deploy application code that writes to both old and new locations

**Contract phase** (remove old, after backfill and verification):
- Backfill data from old columns/tables to new
- Verify data integrity (row counts, checksums)
- Switch application reads to new location
- Add `NOT NULL` constraints after backfill
- Drop old columns/tables/indexes

#### 4b. Column Rename (Expand-Contract)

When the schema introduces a column that replaces an existing one (rename), always produce the full expand-contract plan:

```
Expand Phase:
  1. ALTER TABLE {table} ADD COLUMN {new_name} {type};
  2. Deploy: application writes to BOTH {old_name} and {new_name}
  3. UPDATE {table} SET {new_name} = {old_name} WHERE {new_name} IS NULL;
     -- Run in batches for large tables:
     -- UPDATE {table} SET {new_name} = {old_name}
     --   WHERE id BETWEEN {start} AND {end} AND {new_name} IS NULL;
  4. Verify: SELECT count(*) FROM {table} WHERE {new_name} IS NULL; -- expect 0

Contract Phase:
  5. Deploy: application reads from {new_name} only
  6. ALTER TABLE {table} ALTER COLUMN {new_name} SET NOT NULL;
  7. Deploy: application stops writing to {old_name}
  8. ALTER TABLE {table} DROP COLUMN {old_name};
```

#### 4c. Index Creation

Always use `CREATE INDEX CONCURRENTLY` for indexes on existing tables to avoid locking:

```sql
CREATE INDEX CONCURRENTLY idx_{table}_{column} ON {table}({column});
```

Note: `CONCURRENTLY` cannot run inside a transaction. Each index creation must be a separate migration step.

#### 4d. Migration Output Format

Present the migration plan as a numbered sequence of steps, each with:
- **Step N:** Description
- **SQL:** The exact DDL statement(s)
- **Deploy:** Any application code changes required at this step
- **Verify:** How to confirm the step succeeded
- **Rollback:** How to undo this step if needed

### 5. Verification Checklist

After generating both artifacts, run through this checklist and report any violations:

- [ ] Every table has a primary key
- [ ] All foreign keys have explicit `ON DELETE` action
- [ ] All foreign key columns are indexed
- [ ] `NUMERIC` used for monetary values (never `FLOAT`)
- [ ] `TIMESTAMPTZ` used for all timestamps (never `TIMESTAMP`)
- [ ] `NOT NULL` on all required fields
- [ ] `CHECK` constraints for value ranges
- [ ] `created_at` and `updated_at` on every table
- [ ] Tables ordered by dependency (referenced before referencing)
- [ ] Migration plan uses expand-contract for non-additive changes
- [ ] Migration indexes use `CONCURRENTLY`
- [ ] Every migration step has a rollback

If any item fails, fix the artifact before saving.

### 6. Save Artifacts

Resolve the target project root (git root of the project being designed for).

Resolve the active project context: check for an existing `.skilmarillion/projects/` structure. If found, use the active `{slug}`. If not found, ask the user for the feature slug.

Save the schema DDL to:
```
{project_root}/.skilmarillion/projects/{slug}/schema/{name}-schema.sql
```

Save the migration plan to:
```
{project_root}/.skilmarillion/projects/{slug}/schema/{name}-migration.md
```

Create the directory if it does not exist:

```bash
mkdir -p {project_root}/.skilmarillion/projects/{slug}/schema
```

Confirm the file paths with the user before writing. The user may override the name or directory.

### 7. Summary

Display a summary:

> **Schema complete.**
> - Tables: {count}
> - Indexes: {count}
> - Constraints: {count}
> - Migration steps: {count}
>
> Artifacts saved:
> - `{schema-path}`
> - `{migration-path}`

---

## WHAT NOT TO DO

- Do NOT use `FLOAT` or `REAL` for monetary values — always `NUMERIC(12,2)`
- Do NOT use `TIMESTAMP` without timezone — always `TIMESTAMPTZ`
- Do NOT use `VARCHAR(255)` as a default — size columns intentionally or use `TEXT` with `CHECK`
- Do NOT leave foreign keys without an explicit `ON DELETE` action
- Do NOT create indexes inside transactions — use `CONCURRENTLY`
- Do NOT produce a migration plan that requires downtime for column renames — always expand-contract
- Do NOT skip the verification checklist
- Do NOT generate MySQL, SQLite, or other engine syntax — scope to PostgreSQL

---

## NEXT STEP BREADCRUMB

After artifacts are saved, display:

> These artifacts can be passed to `/impl:tdd` as structured context for implementation.

If `impl` is not installed (check for `impl/` in the plugin directory), display instead:

> These artifacts can be passed to `/impl:tdd` as structured context for implementation.
>
> The `impl` plugin is not yet installed. Install it with:
> ```
> claude plugin add impl
> ```

**Spec-exists hint:** After displaying the breadcrumb, check for existing specs in `docs/` (glob for `docs/**/specs/SPEC-*.md` or `docs/**/SDD-*.md`). If a spec is found for a related feature, append:

> A spec exists at `{spec-path}` -- `/impl:tdd {spec-path}` will pick up both the spec and these design artifacts.

If multiple specs exist, list the most recently modified one and note the count:

> {count} specs found. Most recent: `{spec-path}` -- `/impl:tdd {spec-path}` will pick up both the spec and these design artifacts.
