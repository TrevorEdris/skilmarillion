# Skilmarillion Workflows

How the lifecycle plugins chain together for every scale of work — from a typo fix to a full green-field product.

> **Legend:** Commands marked **(planned)** are not yet implemented.

---

## Quick Reference

| Scale | Entry Command | Artifacts Produced |
|-------|---------------|--------------------|
| Trivial | `/plan:sdd [task]` | None |
| Small | `/plan:sdd [task]` | `IMPL_DETAILS.md` (session) |
| Feature | `/plan:sdd [task]` | `SPEC-NNN-{slug}.md` |
| Epic | `/plan:prd` → `/plan:roadmap` → `/plan:sdd` | `PRD.md` + `ROADMAP.md` + per-milestone specs |
| Green-field | `/plan:prd` → `/plan:roadmap` → loop | Full `docs/{feature}/` tree |

---

## Scenarios

| Scenario | Scale | Description |
|----------|-------|-------------|
| [1. Trivial](01-trivial.md) | One-line fix | Typo fix, config change. No artifacts. |
| [2. Small](02-small.md) | Single function / file | Bug fix with 1-3 files. Beginner and advanced (QRSPI) paths. |
| [3. Feature](03-feature.md) | Multi-file new behavior | Full triage → spec → TDD → review pipeline. |
| [4. Epic](04-epic.md) | Multi-feature subsystem | PRD → roadmap → per-milestone spec → implement → review. |
| [5. Green-field](05-green-field.md) | Full product with existing PRD | Architecture artifacts alongside specs. |
| [6. Team Handoff](06-team-handoff.md) | Multi-person workflow | Product → Lead Engineer → Individual Engineers. |

---

## Lifecycle Diagram

```
                    ┌─────────────────────────────────────────────┐
                    │              skil (router)                  │
                    │         /skil [task description]            │
                    └──────┬──────┬──────┬──────┬────────────────┘
                           │      │      │      │
                    ┌──────▼──┐ ┌─▼────┐ │  ┌───▼────┐
                    │  plan   │ │ arch │ │  │ review │
                    └──┬──────┘ └──────┘ │  └────────┘
                       │                 │
          ┌────────────┼────────────┐    │
          │            │            │    │
     ┌────▼───┐  ┌─────▼────┐  ┌───▼────▼──┐
     │  prd   │  │ roadmap  │  │    sdd     │
     │        │  │          │  │            │
     │ PRD.md │  │ROADMAP.md│  │SPEC-NNN.md │
     └────┬───┘  └────┬─────┘  └─────┬──────┘
          │           │               │
          └─────►─────┘               │
                                      │
                               ┌──────▼──────┐
                               │  impl:tdd   │
                               │             │
                               │IMPL_DETAILS │
                               │  + code     │
                               └──────┬──────┘
                                      │
                               ┌──────▼──────┐
                               │impl:commit  │
                               │  impl:pr    │
                               └──────┬──────┘
                                      │
                               ┌──────▼──────┐
                               │review:review│
                               │             │
                               │review report│
                               └─────────────┘
```

**Flow by task size:**

| Size | Path through the diagram |
|------|--------------------------|
| TRIVIAL | `sdd` → apply directly (no downstream) |
| SMALL | `sdd` → `impl:tdd` → `impl:commit` → `review:review` |
| FEATURE | `sdd` → `impl:tdd` → `impl:commit` → `impl:pr` → `review:review` |
| EPIC | `prd` → `roadmap` → `sdd` (per milestone) → `impl:tdd` → ... → `review:review` |

---

## Plugin Installation

Install only what you need. Each plugin works independently.

```bash
# Router (recommended first install for new users)
/plugin install skil@skilmarillion

# Planning (available now)
/plugin install plan@skilmarillion

# Architecture (planned)
/plugin install arch@skilmarillion

# Implementation (planned)
/plugin install impl@skilmarillion

# Review (planned)
/plugin install review@skilmarillion

# Everything
/plugin marketplace add https://github.com/TrevorEdris/skilmarillion
```
