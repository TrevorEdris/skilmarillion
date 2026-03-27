---
description: Software-Driven Development entry point. Triages a task and routes it to the appropriate workflow.
argument-hint: "[task description or spec path]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh:*)"
  - AskUserQuestion
  - Task
  - ToolSearch
---

# /dream:sdd

Triage a task and route it to the correct workflow. Run at the start of every development session.

---

## ON STARTUP

Before anything else, run:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh list
```

Parse the output and categorize each result:

1. **Done files** — `current_phase` is `done — shipped` → silently run `clear --slug {slug}` and skip.
2. **Abandoned files** — file age > 30 days → add to abandoned list.
3. **Resume candidates** — all remaining files.

### If abandoned files exist

Ask the user (using `AskUserQuestion`):

> "Found {N} abandoned dream states older than 30 days: {list of feature names}. Remove them?"

Options: **"Yes, clean up"** / **"No, keep them"**

If "Yes": run `clear --slug {slug}` for each abandoned file.

### If resume candidates exist

Ask the user (using `AskUserQuestion`) with a numbered list:

> "Active dream states found. Resume one or start something new?
> 1. {feature name} — phase: {current_phase}
> 2. {feature name} — phase: {current_phase}
> ...
> N. Start something new"

If a resume candidate is selected: load its state with `get --slug {slug}`, display current phase and triage result, and resume from the appropriate P0-C step. Do not re-triage.

If "Start something new": proceed to Entry Mode Detection without clearing any existing state files.

### If no state files

Skip directly to Entry Mode Detection.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

---

## Entry Mode Detection

Inspect the argument passed to `/dream:sdd`:

- **Mode A** — argument ends in `.md` and resolves to an existing file path → the user is providing a pre-written spec. Skip triage. Go to the P0-C stub (not yet implemented).
- **Mode B** — argument is a task description string, or no argument provided → full triage flow. Proceed to MODE B.

---

## MODE B — Triage and Route

### B1 — Triage

Delegate to the `triage` agent using the `Task` tool:

```
Task: triage agent
Input: { "task": "<user's task description or prompted input>", "context": "<any codebase notes>" }
```

The agent returns bare JSON: `{ size, risk, routing_decision, rationale, slug }`.

Parse the JSON. If parsing fails or the output contains prose, ask the user to re-describe the task and retry once.

Initialize state:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh init \
  --slug "{slug}" \
  --feature "{task description}" \
  --size "{size}" \
  --risk "{risk}" \
  --routing "{routing_decision}" \
  --current-phase "triaged"
```

Display the triage result to the user:

> **Triage result:**
> - Size: {size}
> - Risk: {risk}
> - Routing: {routing_decision}
> - Rationale: {rationale}
> - State file: `.dream-state-{slug}.local.yaml`

### B2 — Route by Size

#### TRIVIAL

1. Confirm intent with the user:
   > "This looks like a trivial change. Ready to apply it now? (yes/no)"
2. If yes: apply the change directly (inline edit — no spec). Verify it works.
3. After applying, auto-clear state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh clear --slug "{slug}"
   ```
4. Report completion.

If no: ask what the user would like to do instead.

#### SMALL

> **P0-C not yet implemented.**
>
> This task was classified as SMALL. The lightweight spec workflow (P0-C) is not yet available.
>
> When P0-C ships, this path will generate acceptance criteria and route to a focused implementation session.

Update state:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
  --slug "{slug}" \
  --current-phase "pending P0-C"
```

#### FEATURE

> **P0-C not yet implemented.**
>
> This task was classified as FEATURE. The full specification and workflow (P0-C) is not yet available.
>
> When P0-C ships, this path will produce a full spec with architecture notes and route to a structured development session.

Update state:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
  --slug "{slug}" \
  --current-phase "pending P0-C"
```

#### EPIC

> **P0-C not yet implemented.**
>
> This task was classified as EPIC and must be decomposed into FEATURE-sized chunks before any spec can be written.
>
> When P0-C ships, this path will guide you through decomposition before routing to the full workflow.

Update state:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
  --slug "{slug}" \
  --current-phase "pending P0-C"
```

---

## WHAT NOT TO DO

- Do NOT write a spec in this command — spec writing is P0-C.
- Do NOT re-classify a task that already has an active state file — resume instead.
- Do NOT skip the startup scan — state files from prior sessions must be checked every time.
- Do NOT apply a TRIVIAL change without confirmation from the user.
- Do NOT proceed past triage if the triage agent returns prose instead of JSON — retry once, then ask the user to re-describe the task.
