# arch -- Architecture & Design Plugin

Part of the [Skilmarillion](https://github.com/TrevorEdris/skilmarillion) workflow.

## What It Does

`arch` runs structured design sessions that produce production-ready architecture artifacts: ADRs, OpenAPI specs, database schemas, and Mermaid diagrams. Each session follows a boundary-first interview pattern to ensure decisions are explicit and trade-offs are documented.

## Standalone Entry Conditions

`arch` is independently usable. It has no dependencies -- use it with or without `plan`, `impl`, or `review` installed.

**Input:** A system name, API name, schema name, or diagram description (plain language), or nothing -- each command will ask.
**Output:** Design artifacts saved to `.skilmarillion/projects/{slug}/adrs/`, `api/`, `schema/`, or `diagrams/`.

## Installation

```bash
/plugin marketplace add https://github.com/TrevorEdris/skilmarillion
/plugin install arch@skilmarillion
```

## Commands

| Command | Purpose |
|---------|---------|
| `/arch:design [system]` | Structured design session producing an ADR and C4 context diagram. Saves to `.skilmarillion/projects/{slug}/adrs/`. |
| `/arch:api [api-name]` | Guided API design producing an OpenAPI 3.1 spec. Saves to `.skilmarillion/projects/{slug}/api/`. |
| `/arch:schema [name]` | Database schema design with zero-downtime migration plan. Saves to `.skilmarillion/projects/{slug}/schema/`. |
| `/arch:diagram [description]` | General-purpose Mermaid diagram (flowchart, sequence, ERD, C4). Saves to `.skilmarillion/projects/{slug}/diagrams/`. |
| `/arch:help` | Interactive tour of capabilities. Detects existing design artifacts to tailor guidance. |

## Artifact Paths

All paths are relative to the target project's git root.

```
{project_root}/.skilmarillion/projects/{slug}/
  adrs/
    [NNN]-[title].md              # /arch:design output (auto-incrementing)
  api/
    [api-name]-openapi.yaml       # /arch:api output
  schema/
    [name]-schema.sql             # /arch:schema output (PostgreSQL DDL)
    [name]-migration.md           # /arch:schema migration plan
  diagrams/
    [name]-[type].md              # /arch:diagram output
```

> **Project context resolution:** arch commands resolve `{slug}` from the active `.skilmarillion/projects/` structure. If no active project context exists, the command will ask the user for the feature slug before saving artifacts.

## Workflow Integration

```
plan/  -->  .skilmarillion/projects/{slug}/specs/SPEC-NNN-{slug}.md
  |
arch/  -->  .skilmarillion/projects/{slug}/adrs/, api/, schema/, diagrams/
  |
impl/  -->  committed branch + open PR
  |
review/ --> review report
```

`arch/` is optional in the workflow. It can be invoked before `plan/` when the problem space is large, after `plan/` when a spec reveals architectural questions, or standalone for design-only sessions.
