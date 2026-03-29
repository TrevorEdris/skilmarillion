# Scenario 5: Green-Field — Full PRD Already Complete

> *"Here's our PRD for the new billing system. It's been approved by stakeholders."*

**Who:** Solo engineer or team lead starting implementation of an approved product spec.

**Plugins required:** `plan`, `arch` **(planned)**, `impl` **(planned)**, `review` **(planned)**

---

## Commands

When the PRD already exists and has been validated:

```
You:   /plan:validate docs/billing/PRD.md
plan:  PASS — Score: 91/100

You:   /plan:roadmap docs/billing/PRD.md
plan:  [decomposes into 4 phases, 12 milestones]
       Save to docs/billing/ROADMAP.md?

You:   yes

You:   /arch:api Design the billing REST API                               (planned)
arch:  [guided interview → billing-api-openapi.yaml]

You:   /arch:schema Design the billing data model                          (planned)
arch:  [guided interview → billing-schema.sql + migration plan]

You:   /plan:sdd Implement Stripe integration for payment processing.
       Endpoints per docs/api/billing-api-openapi.yaml.
       Schema per docs/schema/billing-schema.sql.
plan:  [FEATURE flow → spec ACs reference the API contract and schema]
       [SPEC-001 saved]

You:   /impl:tdd docs/billing/specs/SPEC-001-stripe-integration.md         (planned)
impl:  [TDD cycle — spec references arch artifacts as the source of truth]

You:   /review:review 50                                                    (planned)
review: [code + security + a11y review]
```

---

## Artifacts

| Artifact | Path |
|----------|------|
| PRD | `docs/billing/PRD.md` (pre-existing) |
| Roadmap | `docs/billing/ROADMAP.md` |
| Specs | `docs/billing/specs/SPEC-NNN-{slug}.md` |
| API spec | `docs/api/billing-api-openapi.yaml` |
| DB schema | `docs/schema/billing-schema.sql` |
| Migration plan | `docs/schema/billing-migration.md` |
| Impl details | `.ai/sessions/YYYY-MM-DD_<slug>/IMPL_DETAILS.md` |
| Review reports | `.ai/sessions/YYYY-MM-DD_<slug>/review-{target}.md` |
