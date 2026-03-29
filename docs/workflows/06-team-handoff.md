# Scenario 6: Team Workflow — Product to Engineering Handoff

A real team with role separation: Product defines requirements, Lead Engineer decomposes and specs, Individual Engineers implement and review.

**Plugins required:** `plan`, `arch` **(planned)**, `impl` **(planned)**, `review` **(planned)**

---

## Cast

| Role | Person | Plugins Used |
|------|--------|-------------|
| Product Manager | Alice | `plan` (prd, validate) |
| Lead Engineer | Bob | `plan` (roadmap, sdd, validate), `arch` |
| Engineer | Carol | `impl`, `review` |
| Engineer | Dave | `impl`, `review` |

---

## Act 1: Alice defines the product (Product Manager)

Alice works in a product-focused session. She doesn't need `impl` or `review` installed.

```
Alice: /plan:prd We need a notification preferences system so users
       can choose which notifications they receive and how (email, push, in-app)

plan:  [discovery questions → PRD authoring → validation]

       PRD produced — Score: 87/100 — PASS
       Save to docs/notification-preferences/PRD.md?

Alice: yes

plan:  PRD saved. Next step: /plan:roadmap docs/notification-preferences/PRD.md
```

Alice shares the PRD path with Bob.

### Alice's artifacts

| Artifact | Path |
|----------|------|
| PRD | `docs/notification-preferences/PRD.md` |

---

## Act 2: Bob decomposes and specs (Lead Engineer)

Bob receives the PRD, creates the roadmap, then specs each milestone. He may also produce architecture artifacts.

```
Bob:   /plan:validate docs/notification-preferences/PRD.md
plan:  PASS — Score: 87/100

Bob:   /plan:roadmap docs/notification-preferences/PRD.md
plan:  [decomposes into phases]

       Phase 0: Foundation
         P0-A: Preference data model + API (FEATURE)
         P0-B: Default preference seeding (SMALL)

       Phase 1: Delivery Channels
         P1-A: Email channel integration (FEATURE, depends P0-A)
         P1-B: Push notification channel (FEATURE, depends P0-A)
         P1-C: In-app notification feed (FEATURE, depends P0-A)

       Phase 2: User-Facing
         P2-A: Preferences settings UI (FEATURE, depends P0-A)
         P2-B: Unsubscribe link handler (SMALL, depends P1-A)

       Save to docs/notification-preferences/ROADMAP.md?

Bob:   yes
```

Bob designs the API contract first, then specs milestones that reference it:

```
Bob:   /arch:api Design the notification preferences API                   (planned)
arch:  [guided interview: resources, versioning, pagination, auth, error format]
       Save to docs/api/notification-preferences-openapi.yaml?

Bob:   yes
```

Now Bob specs milestones. The specs reference the API contract so engineers implement against a defined interface:

```
Bob:   /plan:sdd Preference data model and CRUD API for notification preferences.
       Endpoints must conform to docs/api/notification-preferences-openapi.yaml.
plan:  [FEATURE flow → context gathering → reads OpenAPI spec as context]
       [spec ACs reference the contract: "GET /preferences returns shape matching
        the Preference schema in the OpenAPI spec"]
       Save to docs/notification-preferences/specs/SPEC-001-preference-model-api.md?

Bob:   yes

Bob:   /plan:sdd Email channel integration for notification delivery.
       Email dispatch endpoint per docs/api/notification-preferences-openapi.yaml.
plan:  [FEATURE flow → SPEC-002-email-channel.md]

Bob:   /plan:sdd Push notification channel integration.
       Push endpoint per docs/api/notification-preferences-openapi.yaml.
plan:  [FEATURE flow → SPEC-003-push-channel.md]
```

Bob assigns specs to engineers: Carol gets SPEC-001 and SPEC-002, Dave gets SPEC-003.

### Bob's artifacts

| Artifact | Path |
|----------|------|
| Roadmap | `docs/notification-preferences/ROADMAP.md` |
| Spec (milestone 1) | `docs/notification-preferences/specs/SPEC-001-preference-model-api.md` |
| Spec (milestone 2) | `docs/notification-preferences/specs/SPEC-002-email-channel.md` |
| Spec (milestone 3) | `docs/notification-preferences/specs/SPEC-003-push-channel.md` |
| API spec | `docs/api/notification-preferences-openapi.yaml` |

---

## Act 3: Carol implements SPEC-001 (Engineer)

Carol picks up the spec and runs the full TDD cycle.

```
Carol: /impl:tdd docs/notification-preferences/specs/SPEC-001-preference-model-api.md
                                                                           (planned)
impl:  [generates IMPL_DETAILS.md from spec]
       [executes slice-by-slice TDD: model → service → API → validation]

       Slice 1/4: Preference model and migrations — RED → GREEN → REFACTOR ✓
       Slice 2/4: CRUD service layer — RED → GREEN → REFACTOR ✓
       Slice 3/4: REST endpoints — RED → GREEN → REFACTOR ✓
       Slice 4/4: Input validation and error handling — RED → GREEN → REFACTOR ✓

       All slices complete.

Carol: /impl:commit                                                        (planned)
impl:  feat(api): add notification preference model and CRUD endpoints
       Commit? (yes / edit)

Carol: yes

Carol: /impl:pr                                                            (planned)
impl:  [fills PR template from diff + spec ACs]
       Create PR? (yes / edit)

Carol: yes → PR #55 created
```

---

## Act 4: Dave reviews Carol's PR (Engineer)

```
Dave:  /review:review 55                                                   (planned)

review: Reviewing PR #55: feat(api): notification preference CRUD

        What's Working:
        - Clean vertical slice structure matching spec
        - Comprehensive test coverage for all ACs

        Code Quality (2 findings):
        - [MEDIUM] Preference service missing pagination on list endpoint
        - [LOW] Consider extracting validation to shared middleware

        Security (1 finding):
        - [HIGH] Preference update endpoint lacks ownership check —
          user A can modify user B's preferences via direct ID

        Accessibility: N/A (API only, no UI)

        Review saved to .ai/sessions/2026-03-29_Review-PR-55/review-pr-55.md
```

Carol addresses the security finding, pushes a fix, Dave re-reviews.

---

## Act 5: Meanwhile, Dave implements SPEC-003 (in parallel)

```
Dave:  /impl:tdd docs/notification-preferences/specs/SPEC-003-push-channel.md
                                                                           (planned)
impl:  [TDD cycle for push notification integration]
       ...

Dave:  /impl:pr → PR #57 created                                          (planned)

Carol: /review:review 57                                                   (planned)
       [reviews Dave's push channel PR]
```

---

## Full Team Artifact Map

```
docs/notification-preferences/
  PRD.md                                          ← Alice (Product)
  ROADMAP.md                                      ← Bob (Lead)
  specs/
    SPEC-001-preference-model-api.md              ← Bob (Lead)
    SPEC-002-email-channel.md                     ← Bob (Lead)
    SPEC-003-push-channel.md                      ← Bob (Lead)

docs/api/
  notification-preferences-openapi.yaml           ← Bob (Lead)

.ai/sessions/
  2026-03/
    29-1400_SPEC-001_Preference-Model/
      SESSION.md                                  ← Carol (auto)
      IMPL_DETAILS.md                             ← Carol (/impl:tdd)
    29-1600_Review-PR-55/
      review-pr-55.md                             ← Dave (/review:review)
    29-1430_SPEC-003_Push-Channel/
      SESSION.md                                  ← Dave (auto)
      IMPL_DETAILS.md                             ← Dave (/impl:tdd)
    29-1700_Review-PR-57/
      review-pr-57.md                             ← Carol (/review:review)

Feature branches:
  feat/preference-model-api    → PR #55           ← Carol
  feat/push-channel            → PR #57           ← Dave
```
