---
description: Interactive tour of arch plugin capabilities. Detects existing design artifacts and recommends a starting command.
argument-hint: ""
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(ls:*)
  - AskUserQuestion
  - ToolSearch
model: haiku
---

# /arch:help

Interactive, context-aware tour of the `arch` plugin. Scans the project for existing design artifacts, walks through each command, and recommends a starting point.

---

## ON STARTUP -- Project State Scan

Before presenting anything, scan for existing design artifacts to determine context.

### 1. Scan for ADRs

```
Glob: .skilmarillion/projects/*/adrs/*.md
```

Store the count and paths as `{adrs}`.

### 2. Scan for OpenAPI specs

```
Glob: .skilmarillion/projects/*/api/*-openapi.yaml
```

Store the count and paths as `{api_specs}`.

### 3. Scan for schemas

```
Glob: .skilmarillion/projects/*/schema/*-schema.sql
```

Store the count and paths as `{schemas}`.

### 4. Scan for diagrams

```
Glob: .skilmarillion/projects/*/diagrams/*.md
```

Store the count and paths as `{diagrams}`.

### 5. Scan for specs (from plan)

```
Glob: docs/*/specs/SPEC-*.md
```

Store the count and paths as `{specs}`.

### 6. Detect sibling plugins

Check whether sibling lifecycle plugins are installed by looking for their manifests:

- `plan`: check for `plan/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins
- `impl`: check for `impl/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins
- `review`: check for `review/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins

Store availability as `{plugins_installed}`.

---

## GREETING -- Adapt Based on Findings

Choose one greeting based on the scan results:

### Fresh project (no ADRs, no API specs, no schemas, no diagrams)

> **Welcome to `/arch` -- the architecture and design navigator.**
>
> This project has no ADRs, API specs, schemas, or diagrams yet. Let me walk you through what `arch` can do.

### Existing design artifacts found

> **Welcome back.** Found {adrs} ADR(s), {api_specs} API spec(s), {schemas} schema(s), and {diagrams} diagram(s) in this project. Let me show you what else `arch` can do.

### Specs exist but no design artifacts

> **Welcome.** Found {specs} spec(s) from planning but no design artifacts yet. `arch` can help you make architecture decisions before implementation.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

After displaying the greeting, ask:

> "Want the full tour, or jump to a specific command?"
>
> 1. Full tour
> 2. Jump to a command: `design` | `api` | `schema` | `diagram`

If "Full tour": proceed through all commands in order (COMMAND TOUR section).
If a specific command is named: jump directly to that command's section in the tour.

---

## COMMAND TOUR

Walk through each command one at a time. After each command description, ask the user how to proceed before moving to the next.

### Command 1: `/arch:design`

> **`/arch:design [system]`** -- System Design Session
>
> A structured design session that produces an Architecture Decision Record (ADR) and a C4 context diagram in Mermaid format. Walks you through:
>
> - System boundaries and scope
> - Actors and external dependencies
> - Key quality attributes (scalability, reliability, security)
> - Trade-off analysis with alternatives
>
> **Example:** `/arch:design payment-service`
>
> **Produces:** `.skilmarillion/projects/{slug}/adrs/[NNN]-[title].md` + C4 context diagram

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `design`
> 3. Try `/arch:design` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 2.
- If "Tell me more": explain the ADR format (Status, Context, Decision, Consequences), C4 diagram levels, and how the structured interview surfaces trade-offs before committing to a decision. Then re-ask.
- If "Try it now": tell the user to run `/arch:design` with their system name. End the tour.
- If "Skip to": ask which command and jump there.

### Command 2: `/arch:api`

> **`/arch:api [api-name]`** -- API Design Session
>
> A guided API design session that produces an OpenAPI 3.1 specification. Covers:
>
> - Resource naming and HTTP verbs
> - Versioning strategy
> - Pagination model
> - Standard error envelopes
> - Authentication scheme
>
> **Example:** `/arch:api user-management`
>
> **Produces:** `.skilmarillion/projects/{slug}/api/[api-name]-openapi.yaml`

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `api`
> 3. Try `/arch:api` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 3.
- If "Tell me more": explain OpenAPI 3.1 output format, how versioning strategies are compared (URL path vs header vs query), and how the spec integrates with code generation tools. Then re-ask.
- If "Try it now": tell the user to run `/arch:api` with their API name. End the tour.
- If "Skip to": ask which command and jump there.

### Command 3: `/arch:schema`

> **`/arch:schema [name]`** -- Database Schema Design
>
> A guided schema design session that produces PostgreSQL DDL and a zero-downtime migration plan. Covers:
>
> - Entity identification and relationships
> - Normalization decisions
> - Index strategy
> - Constraint definitions
> - Migration ordering for zero-downtime deploys
>
> **Example:** `/arch:schema user-profiles`
>
> **Produces:** `.skilmarillion/projects/{slug}/schema/[name]-schema.sql` + `.skilmarillion/projects/{slug}/schema/[name]-migration.md`

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `schema`
> 3. Try `/arch:schema` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 4.
- If "Tell me more": explain how normalization trade-offs are presented (3NF vs denormalized for read performance), how indexes are recommended based on query patterns, and how the migration plan handles zero-downtime constraints. Then re-ask.
- If "Try it now": tell the user to run `/arch:schema` with their schema name. End the tour.
- If "Skip to": ask which command and jump there.

### Command 4: `/arch:diagram`

> **`/arch:diagram [description]`** -- Mermaid Diagram Generator
>
> General-purpose diagram generation in Mermaid syntax. Supports:
>
> - Flowcharts
> - Sequence diagrams
> - Entity-Relationship Diagrams (ERD)
> - C4 context and container diagrams
>
> **Example:** `/arch:diagram sequence diagram for the checkout flow`
>
> **Produces:** `.skilmarillion/projects/{slug}/diagrams/[name]-[type].md`

Ask (using `AskUserQuestion`):

> "That covers all four commands. Ready for a recommendation, or have questions?"
>
> 1. Give me a recommendation
> 2. Go back to a command
> 3. I'm good -- end tour

- If "Give me a recommendation": proceed to RECOMMENDATION section.
- If "Go back to a command": ask which and jump there.
- If "End tour": display the closing message and stop.

---

## RECOMMENDATION -- Starting Command

Based on the project state scan, recommend the best starting command:

### If no design artifacts exist and no specs exist

> **Recommendation:** Start with `/arch:design [system]` to document your system boundaries and key architecture decisions. ADRs provide the foundation that other design artifacts build on.

### If no design artifacts exist but specs exist

> **Recommendation:** You have specs from planning but no architecture artifacts. Start with `/arch:design` to document key decisions, or jump to `/arch:api` or `/arch:schema` if the spec already implies an API or data model.

### If ADRs exist but no API specs or schemas

> **Recommendation:** You have ADRs in place. Next step depends on your system:
> - Building an API? Run `/arch:api [api-name]` to produce an OpenAPI spec.
> - Need a data model? Run `/arch:schema [name]` to design the schema.
> - Need a visual overview? Run `/arch:diagram [description]`.

### If design artifacts already exist

> **Recommendation:** This project has design artifacts in place. Use `arch` when you need to:
> - Document a new architecture decision: `/arch:design`
> - Design a new API endpoint or service: `/arch:api`
> - Add or modify a schema: `/arch:schema`
> - Create a diagram for documentation or discussion: `/arch:diagram`

---

## UPSTREAM / DOWNSTREAM PLUGIN REFERENCES

After the recommendation, reference upstream and downstream plugins with install hints if not present.

### Upstream: `plan`

#### If `plan` is installed

> **Upstream:** Specs come from `/plan:sdd`. Architecture decisions often emerge during planning -- run `/plan:help` for a tour of planning capabilities.

#### If `plan` is NOT installed

> **Tip:** The `plan` plugin generates specs that may surface architecture questions. Install it for spec-driven planning:
> ```
> /plugin install plan@skilmarillion
> ```

### Downstream: `impl`

#### If `impl` is installed

> **Downstream:** After design is documented, run `/impl:tdd` to implement. Design artifacts provide structured context for implementation.

#### If `impl` is NOT installed

> **Tip:** The `impl` plugin handles implementation from specs and design artifacts. Install it when you are ready to build:
> ```
> /plugin install impl@skilmarillion
> ```

### Downstream: `review`

#### If `review` is installed

> **Downstream:** After implementation, run `/review:review` to check code quality before merging.

#### If `review` is NOT installed

> **Tip:** The `review` plugin handles code review, security audits, and accessibility checks. Install it as your pre-merge quality gate:
> ```
> /plugin install review@skilmarillion
> ```

---

## CLOSING

> Run any command to get started. You can return here anytime with `/arch:help`.

---

## WHAT NOT TO DO

- Do NOT modify any files -- this command is entirely read-only.
- Do NOT create state files -- this is an informational tour only.
- Do NOT skip the project state scan -- the greeting and recommendation depend on it.
- Do NOT present all commands at once -- walk through them one at a time with navigation between each.
- Do NOT assume plugin availability -- always check before referencing upstream/downstream plugins.
