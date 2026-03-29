# Scenario 3: Feature — New Behavior Across Multiple Files

> *"Add rate limiting to the public API — 100 requests per minute per API key"*

**Who:** Any engineer, solo or paired.

**Plugins required:** `plan`, `impl` **(planned)**, `review` **(planned)**

---

## Step 1: Triage and Spec (plan)

```
You:   /plan:sdd Add rate limiting to the public API, 100 req/min per API key

plan:  Triage result:
         Size: FEATURE
         Risk: HIGH
         Routing: full-workflow

       [context-gatherer agent reads entry points, middleware, config]
       [spec-builder agent asks 3-5 clarifying questions across 1-2 rounds]

You:   [answers questions about storage backend, response headers, burst behavior]

plan:  [produces full spec with:]
         - Problem Statement
         - Acceptance Criteria (organized as vertical slices)
         - Architecture Recommendation (via architecture-advisor agent)
         - TDD Plan (via tdd-planner agent)

       Validation: PASS — Score: 88/100
       Save to /home/you/project/docs/rate-limiting/specs/SPEC-001-api-rate-limit.md?

You:   yes

plan:  Spec saved. Next step: /impl:tdd docs/rate-limiting/specs/SPEC-001-api-rate-limit.md
```

## Step 2: Implement (impl — planned)

```
You:   /impl:tdd docs/rate-limiting/specs/SPEC-001-api-rate-limit.md      (planned)

impl:  [generates IMPL_DETAILS.md from spec — translates slices into steps]

       Slice 1/3: Rate limit storage layer
         RED  — writing test... running... FAIL (expected)
         GREEN — implementing... running full suite... PASS
         REFACTOR — cleanup... suite still green

       Slice 2/3: Middleware integration
         RED  → GREEN → REFACTOR ✓

       Slice 3/3: Response headers and 429 handling
         RED  → GREEN → REFACTOR ✓

       All slices complete. Run /impl:pr to generate PR description.

You:   /impl:pr                                                            (planned)

impl:  [detects .github/PULL_REQUEST_TEMPLATE.md, fills sections]
       PR ready. Create with gh pr create? (yes / edit)

You:   yes
```

## Step 3: Review (review — planned)

```
You:   /review:review 42                                                   (planned)

review: [spawns 3 specialist agents in parallel]
        Code quality:  2 findings (MEDIUM)
        Security:      1 finding (HIGH) — timing attack on rate limit comparison
        Accessibility:  N/A (no UI changes)

        Review saved to .ai/sessions/2026-03-29_Rate-Limiting/review-pr-42.md
```

---

## Artifacts

| Artifact | Path |
|----------|------|
| Spec | `docs/rate-limiting/specs/SPEC-001-api-rate-limit.md` |
| Impl details | `.ai/sessions/2026-03-29_Rate-Limiting/IMPL_DETAILS.md` |
| Code changes | Feature branch, PR #42 |
| Review report | `.ai/sessions/2026-03-29_Rate-Limiting/review-pr-42.md` |
