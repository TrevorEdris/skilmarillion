---
description: Route a task description to the appropriate lifecycle plugin command.
argument-hint: "[task description]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(ls:*)
  - AskUserQuestion
  - ToolSearch
model: haiku
---

# /skil (Task Router)

Route a plain-language task description to the correct Skilmarillion lifecycle plugin. This is the default command for the `skil` plugin.

---

## ON STARTUP

You received a task description from the user: `$ARGUMENTS`

If `$ARGUMENTS` is empty, ask the user:

> What would you like to work on? Describe the task in a sentence or two.

Store the task description as `{task}`.

---

## STEP 1 — Detect Installed Plugins

Check which lifecycle plugins are available by looking for their manifests:

```
Glob: */.claude-plugin/plugin.json
```

Build a map of installed plugins:

| Plugin | Manifest Path | Installed? |
|--------|--------------|------------|
| `plan` | `plan/.claude-plugin/plugin.json` | check |
| `arch` | `arch/.claude-plugin/plugin.json` | check |
| `impl` | `impl/.claude-plugin/plugin.json` | check |
| `review` | `review/.claude-plugin/plugin.json` | check |

Store this as `{installed_plugins}`.

---

## STEP 2 — Classify Intent

Classify `{task}` into one of four lifecycle phases using keyword matching. This is a simple heuristic, not deep reasoning.

### Classification Rules

**PLAN** — matches when the task mentions:
- plan, spec, specify, specification, requirements, prd, product requirements, acceptance criteria, user story, feature request, define, scope, what to build, design doc, proposal

Route to: `/plan:sdd {task}`

**ARCH** — matches when the task mentions:
- architecture, design, api, schema, database, diagram, adr, decision record, system design, data model, endpoint, contract, openapi, erd, sequence diagram, component diagram

Route to: `/arch:design {task}` (or `/arch:adr` if the task specifically mentions decision/ADR)

**IMPL** — matches when the task mentions:
- build, implement, code, fix, debug, refactor, test, tdd, write code, add feature, bug fix, patch, migrate code, upgrade, create endpoint, write tests

Route to: `/impl:tdd {task}`

**REVIEW** — matches when the task mentions:
- review, audit, security, accessibility, a11y, check, inspect, code review, pr review, pull request, vulnerability, lint, quality

Route to: `/review:review {task}` (or `/review:security` if the task specifically mentions security/vulnerability)

### Ambiguity Handling

If the task matches multiple categories equally, or matches none clearly, use `AskUserQuestion`:

> I want to route your task to the right tool. What phase best describes what you need?
>
> 1. **Plan** — Define requirements, write specs, scope the work (`/plan:sdd`)
> 2. **Design** — Architecture decisions, API design, data modeling (`/arch:design`)
> 3. **Implement** — Write code, fix bugs, run TDD cycle (`/impl:tdd`)
> 4. **Review** — Code review, security audit, quality check (`/review:review`)

Store the user's choice as the classified intent.

---

## STEP 3 — Route or Install

### If the target plugin IS installed:

Output the routing decision and delegate:

> **Routing:** "{task}" -> `/{plugin}:{command}`
>
> Invoking `/{plugin}:{command} {task}` now.

Then invoke the target command with the task description using the Skill tool.

### If the target plugin is NOT installed:

Tell the user what they need:

> This task needs the **{plugin}** plugin, which is not currently installed.
>
> To install it, run:
> ```
> /install {plugin}
> ```
>
> Once installed, run `/skil {task}` again and I will route you there.

Do NOT attempt to do the work yourself. `skil` is a router, not an executor.

---

## ROUTING EXAMPLES

These examples illustrate expected routing behavior:

| Task Description | Classified As | Route |
|-----------------|---------------|-------|
| "add user authentication" | PLAN | `/plan:sdd add user authentication` |
| "review my PR" | REVIEW | `/review:review review my PR` |
| "design the database schema for orders" | ARCH | `/arch:design design the database schema for orders` |
| "fix the login bug on mobile" | IMPL | `/impl:tdd fix the login bug on mobile` |
| "write an ADR for choosing a message queue" | ARCH | `/arch:adr write an ADR for choosing a message queue` |
| "security audit the payment module" | REVIEW | `/review:security security audit the payment module` |
| "scope out the notification feature" | PLAN | `/plan:sdd scope out the notification feature` |
| "refactor the user service" | IMPL | `/impl:tdd refactor the user service` |

---

## RULES

1. **Never execute work yourself.** You classify and route. The lifecycle plugin does the work.
2. **When in doubt, ask.** A wrong route wastes more time than one clarifying question.
3. **Be brief.** State the routing decision in one line, then delegate.
4. **Default to PLAN for new features.** If the task sounds like new functionality and no stronger signal exists, route to `/plan:sdd`. Spec before code.
5. **Model tier: Haiku.** This is keyword classification. No deep reasoning needed.
