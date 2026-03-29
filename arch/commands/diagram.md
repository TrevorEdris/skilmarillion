---
description: Generate a Mermaid diagram from a plain-language description. Supports flowchart, sequence, ERD, C4 context, and C4 container.
argument-hint: "[description of what to diagram]"
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - AskUserQuestion
  - ToolSearch
model: sonnet
---

# /arch:diagram

Generate a syntactically valid Mermaid diagram from a plain-language description. Save it to `docs/diagrams/[name]-[type].md`.

---

## Flow

### 1. Input Resolution

- If an argument is provided: use it as the diagram description.
- If no argument: ask the user what they want to diagram.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. Diagram Type Selection

Determine the diagram type from the description. If ambiguous, ask the user to choose.

**Decision matrix:**

| Signal in description | Diagram type |
|-----------------------|--------------|
| Process, workflow, algorithm, decision tree, pipeline, user journey | `flowchart` |
| API interaction, request/response, message flow, authentication flow, temporal sequence | `sequence` |
| Database, tables, entities, relationships, schema, data model | `erDiagram` |
| System context, actors, external systems, high-level architecture | `C4Context` |
| Containers, applications, databases, services within a system boundary | `C4Container` |

If the description matches multiple types, present the options:

> Your description could be diagrammed as:
> 1. **Flowchart** -- process steps and decision points
> 2. **Sequence diagram** -- interactions between participants over time
>
> Which fits your intent?

### 3. Name Resolution

Extract a short kebab-case name from the description for the filename. Confirm with the user:

> I'll save this as `docs/diagrams/{name}-{type}.md`. Sound right?

### 4. Diagram Generation

Generate the Mermaid diagram following the syntax rules for the selected type. Apply these rules strictly:

#### All diagram types

- Use `%%` comments to explain non-obvious sections
- Keep under 20 nodes/participants for readability -- split into multiple diagrams if larger
- Use meaningful, descriptive labels (not `A`, `B`, `C`)
- No special characters in node IDs -- alphanumeric and underscores only

#### Flowchart

```
flowchart TD
    Start([description]) --> Step1[Action]
    Step1 --> Decision{Condition?}
    Decision -->|Yes| PathA[Action A]
    Decision -->|No| PathB[Action B]
```

**Node shapes:**
- `[Rectangle]` -- process step
- `([Rounded])` -- start/end
- `{Diamond}` -- decision
- `[/Parallelogram/]` -- input/output
- `[(Database)]` -- data store
- `((Circle))` -- connector

**Directions:** `TD` (top-down), `LR` (left-right), `BT` (bottom-up), `RL` (right-left)

Use subgraphs to group related steps:

```
subgraph GroupName
    direction TB
    A --> B
end
```

#### Sequence diagram

```
sequenceDiagram
    actor User
    participant Frontend
    participant API
    participant Database

    User->>Frontend: Action
    Frontend->>+API: POST /endpoint
    API->>+Database: Query
    Database-->>-API: Result
    API-->>-Frontend: Response
    Frontend-->>User: Display result
```

**Arrow types:**
- `->>` solid arrow (synchronous request)
- `-->>` dotted arrow (response/return)
- `-)` solid open arrow (async, fire-and-forget)
- `--)` dotted open arrow (async response)

**Blocks:** `alt`/`else` for conditionals, `opt` for optional, `par`/`and` for parallel, `loop` for repetition, `break` for early exit.

**Activations:** `+` after arrow activates, `-` before arrow deactivates.

Use `autonumber` for complex flows.

#### ERD

```
erDiagram
    ENTITY_A ||--o{ ENTITY_B : "relationship label"

    ENTITY_A {
        uuid id PK
        varchar name "NOT NULL"
        timestamp created_at "DEFAULT NOW()"
    }
```

**Cardinality:**
- `||` exactly one
- `|o` zero or one
- `}|` one or more
- `}o` zero or more

**Attribute format:** `type name constraint "comment"`

**Constraints:** `PK` (primary key), `FK` (foreign key), `UK` (unique key)

Name entities in UPPERCASE singular form (`USER` not `USERS`).

#### C4 Context

```
C4Context
    title System Context - [System Name]

    Person(alias, "Name", "Description")
    Person_Ext(alias, "Name", "Description")
    System(alias, "Name", "Description")
    System_Ext(alias, "Name", "Description")
    SystemDb(alias, "Name", "Description")
    SystemDb_Ext(alias, "Name", "Description")
    SystemQueue(alias, "Name", "Description")
    SystemQueue_Ext(alias, "Name", "Description")

    Rel(from, to, "Label", "Technology")
    BiRel(a, b, "Label")
```

Focus on the system boundary: internal system, its users, and external dependencies.

#### C4 Container

```
C4Container
    title Container Diagram - [System Name]

    Person(alias, "Name")
    System_Ext(alias, "Name")

    Container_Boundary(alias, "Boundary Label") {
        Container(alias, "Name", "Technology", "Description")
        ContainerDb(alias, "Name", "Technology", "Description")
        ContainerQueue(alias, "Name", "Technology", "Description")
    }

    Rel(from, to, "Label", "Protocol")
```

Group containers into boundaries. Specify technology and protocol on every element and relationship.

### 5. Validation

Before presenting the diagram, verify:

1. **Syntax correctness** -- the diagram type keyword matches the content structure
2. **Balanced blocks** -- every `subgraph`/`end`, `alt`/`end`, `loop`/`end`, `Container_Boundary`/`}` is properly closed
3. **No orphan nodes** -- every node participates in at least one relationship (warn if not)
4. **Consistent naming** -- node IDs do not contain spaces or special characters
5. **Relationship completeness** -- all entities referenced in relationships are defined (ERD)
6. **Required elements present:**
   - Flowchart: at least one start node and one end node or decision
   - Sequence: at least two participants and one message
   - ERD: at least two entities and one relationship
   - C4 Context: at least one Person, one System, and one Rel
   - C4 Container: at least one Container_Boundary with contents

If validation finds issues, fix them before presenting.

### 6. Output

Write the diagram to `docs/diagrams/{name}-{type}.md` using this template:

```markdown
# {Title}

{One-sentence description of what this diagram shows.}

```mermaid
{diagram content}
`` `

## Legend

{Brief explanation of key elements, only if the diagram has non-obvious conventions.}
```

Create the `docs/diagrams/` directory if it does not exist.

### 7. Follow-up

After saving, present:

> Diagram saved to `docs/diagrams/{name}-{type}.md`.
>
> Paste into [mermaid.live](https://mermaid.live) to verify rendering.

If related design artifacts exist (ADRs, specs), mention them:

> Related: `docs/adrs/NNN-title.md` covers the architecture decision behind this design.

If `impl` is installed, suggest:

> These design artifacts can inform `/impl:tdd` during implementation.

If `impl` is not installed:

> Tip: Install the `impl` plugin to use these diagrams as implementation context.

**Spec-exists hint:** After displaying the follow-up, check for existing specs in `docs/` (glob for `docs/**/specs/SPEC-*.md` or `docs/**/SDD-*.md`). If a spec is found for a related feature, append:

> A spec exists at `{spec-path}` -- `/impl:tdd {spec-path}` will pick up both the spec and these design artifacts.

If multiple specs exist, list the most recently modified one and note the count:

> {count} specs found. Most recent: `{spec-path}` -- `/impl:tdd {spec-path}` will pick up both the spec and these design artifacts.
