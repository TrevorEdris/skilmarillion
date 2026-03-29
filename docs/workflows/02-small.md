# Scenario 2: Small — Single Function / Single File Fix

> *"The getUserProfile endpoint returns 500 when the user has no avatar set"*

**Who:** Any engineer, solo.

**Plugins required:** `plan`, `impl` **(planned)**, `review` **(planned)**

---

## Beginner Path

```
You:   /plan:sdd The getUserProfile endpoint returns 500 when user has no avatar

plan:  Triage result:
         Size: SMALL
         Risk: MODERATE
         Routing: spec-workflow

       [asks 1-3 clarifying questions about expected behavior]

You:   [answers questions]

plan:  [produces lightweight spec with ACs]
       Save to /home/you/project/docs/user-profile/specs/SPEC-001-fix-null-avatar.md?

You:   yes

plan:  PASS — Score: 82/100
       Spec saved. Next step: /impl:tdd docs/user-profile/specs/SPEC-001-fix-null-avatar.md
```

```
You:   /impl:tdd docs/user-profile/specs/SPEC-001-fix-null-avatar.md     (planned)

impl:  [generates IMPL_DETAILS.md from spec]
       [executes RED-GREEN-REFACTOR cycle]
       [runs test suite — all green]
       Ready to commit. Run /impl:commit to generate a commit message.

You:   /impl:commit                                                       (planned)

impl:  Suggested: fix(api): handle null avatar in getUserProfile
       Commit? (yes / edit)

You:   yes
```

### Artifacts

| Artifact | Path |
|----------|------|
| Spec | `docs/user-profile/specs/SPEC-001-fix-null-avatar.md` |
| Impl details | `.ai/sessions/2026-03-29_Fix-Null-Avatar/IMPL_DETAILS.md` |
| Code changes | Committed to feature branch |

---

## Advanced Path (QRSPI — planned)

For experienced users, SMALL tasks can use the faster QRSPI cycle that produces an implementation plan directly (no durable spec):

```
You:   /plan:sdd The getUserProfile endpoint returns 500 when user has no avatar

plan:  Triage: SMALL / MODERATE

       Question phase — design decisions:
       1. Should a missing avatar return null or a default URL?
       2. Should we add a DB default or handle in the service layer?

You:   null, service layer

plan:  Research phase — [reads getUserProfile handler, service, tests]
       Structure phase — single phase, 2 files
       Plan phase:

       IMPL_DETAILS.md produced → Score: 78/100 — PASS
       Save to .ai/sessions/2026-03-29_Fix-Null-Avatar/IMPL_DETAILS.md?

You:   yes

plan:  Execute now or hand to /impl:tdd? (execute / hand off)

You:   execute

plan:  [applies changes inline, runs tests, confirms green]
```

### Artifacts

| Artifact | Path |
|----------|------|
| Impl details | `.ai/sessions/2026-03-29_Fix-Null-Avatar/IMPL_DETAILS.md` |
| Code changes | Committed to feature branch |
