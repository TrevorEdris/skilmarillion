# Scenario 4: Epic — Multi-Feature Subsystem

> *"Build a webhook delivery system — registration, dispatch, retry with backoff, delivery logs"*

**Who:** Solo engineer or small team.

**Plugins required:** `plan`, `impl` **(planned)**, `review` **(planned)**

---

## Step 1: Define the product (PRD)

```
You:   /plan:prd Build a webhook delivery system for our platform

plan:  Before writing the PRD, I need to understand the problem space:
       1. The Problem — ...
       2. The Stakes — ...
       3. Success Definition — ...
       4. Non-Goals — ...
       5. Constraints — ...

You:   [answers all 5 questions]

plan:  [produces full PRD with FR-001 through FR-008, NFR-001 through NFR-003]
       Validation: PASS — Score: 85/100
       Save to /home/you/project/docs/webhooks/PRD.md?

You:   yes
```

## Step 2: Decompose into milestones (Roadmap)

```
You:   /plan:roadmap docs/webhooks/PRD.md

plan:  PRD validation: PASS (85/100)

       Decomposing into phases...

       Philosophy: "Ship the happy path first. Each phase adds resilience."

       Does this capture the build approach? (yes / revise)

You:   yes

plan:  Phase 0: Core Registration
         P0-A: Webhook endpoint CRUD (FEATURE, no deps)
         P0-B: Event type catalog (SMALL, no deps)

       Phase 1: Dispatch Engine
         P1-A: Synchronous dispatch (FEATURE, depends on P0-A)
         P1-B: Async queue integration (FEATURE, depends on P1-A)

       Phase 2: Resilience
         P2-A: Exponential backoff retry (FEATURE, depends on P1-B)
         P2-B: Circuit breaker per endpoint (FEATURE, depends on P2-A)

       Phase 3: Observability
         P3-A: Delivery log and dashboard (FEATURE, depends on P1-A)

       Critical path: P0-A → P1-A → P1-B → P2-A → P2-B

       Save to /home/you/project/docs/webhooks/ROADMAP.md?

You:   yes

plan:  Roadmap saved. Run /plan:sdd [milestone] to spec each one.
       Start with P0-A: /plan:sdd Webhook endpoint CRUD
```

## Step 3: Spec each milestone, implement, review

```
You:   /plan:sdd Webhook endpoint CRUD
       ... [FEATURE flow produces SPEC-001-webhook-crud.md]

You:   /impl:tdd docs/webhooks/specs/SPEC-001-webhook-crud.md              (planned)
       ... [TDD cycle, commit, PR]

You:   /review:review 43                                                    (planned)
       ... [parallel review, findings report]

       [repeat for each milestone in the roadmap]
```

---

## Artifacts

| Artifact | Path |
|----------|------|
| PRD | `docs/webhooks/PRD.md` |
| Roadmap | `docs/webhooks/ROADMAP.md` |
| Spec (per milestone) | `docs/webhooks/specs/SPEC-001-webhook-crud.md` |
| | `docs/webhooks/specs/SPEC-002-event-catalog.md` |
| | `docs/webhooks/specs/SPEC-003-sync-dispatch.md` |
| | `docs/webhooks/specs/SPEC-004-async-queue.md` |
| | `docs/webhooks/specs/SPEC-005-retry-backoff.md` |
| | `docs/webhooks/specs/SPEC-006-circuit-breaker.md` |
| | `docs/webhooks/specs/SPEC-007-delivery-logs.md` |
| Impl details (per milestone) | `.ai/sessions/YYYY-MM-DD_<slug>/IMPL_DETAILS.md` |
| Review reports (per PR) | `.ai/sessions/YYYY-MM-DD_<slug>/review-{target}.md` |
