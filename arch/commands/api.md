---
description: Guided API design session producing an OpenAPI 3.1 specification with pagination, error envelopes, and versioning strategy.
argument-hint: "[api-name]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - ToolSearch
model: sonnet
---

# /arch:api

Design a REST API through a structured interview and produce a complete OpenAPI 3.1 specification saved to `.skilmarillion/projects/{slug}/api/[api-name]-openapi.yaml`.

---

## ON STARTUP

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

If an `[api-name]` argument is provided, use it as the working name.

If no argument is provided, ask:

> What API are we designing? Give me a name and a one-sentence description.

---

## PHASE 1: BOUNDARY

Define what is in scope for this API.

Ask the user (one question at a time, using `AskUserQuestion`):

1. **Resources:** "What are the core resources? (e.g., users, orders, products)"
2. **Relationships:** "How do these resources relate? (e.g., orders belong to users, orders have line items)"
3. **Consumers:** "Who calls this API? (mobile app, web app, service-to-service, public third-party)"
4. **Scope boundary:** "Anything explicitly out of scope for this version?"

Record confirmed answers before proceeding.

---

## PHASE 2: DESIGN DECISIONS

Present trade-offs and let the developer decide. Use `AskUserQuestion` for each.

### Versioning Strategy

Present:

> **Versioning strategy:**
> 1. **URL path** (`/v1/orders`) — visible, cacheable, easiest to test. *Recommended default.*
> 2. **Request header** (`Accept-Version: 2`) — clean URLs, harder to test
> 3. **Content negotiation** (`Accept: application/vnd.api.v2+json`) — standards-compliant, verbose

Default to URL path if the user has no preference.

### Authentication

Present:

> **Auth scheme:**
> 1. **Bearer JWT** — stateless, standard for SPAs and mobile
> 2. **API key** (`X-API-Key` header) — simple for service-to-service
> 3. **OAuth 2.0 flows** — full delegation model for third-party access

### Pagination Model

Present:

> **Pagination:**
> 1. **Cursor-based** — consistent performance on large/live datasets, no skipping/duplicating on concurrent writes. *Recommended for most APIs.*
> 2. **Offset-based** — simpler, supports jump-to-page, degrades on large datasets

Default to cursor-based if the user has no preference.

### Field Casing

Present:

> **JSON field casing:**
> 1. **camelCase** — JavaScript-native, most common for web APIs
> 2. **snake_case** — Python/Ruby-native, common for internal APIs

Default to camelCase if the user has no preference.

---

## PHASE 3: ENDPOINT DESIGN

For each resource identified in Phase 1:

1. Map standard CRUD operations to HTTP methods:
   - `GET /v{n}/{resources}` — list (paginated)
   - `POST /v{n}/{resources}` — create
   - `GET /v{n}/{resources}/{id}` — get by ID
   - `PUT /v{n}/{resources}/{id}` — replace
   - `PATCH /v{n}/{resources}/{id}` — partial update
   - `DELETE /v{n}/{resources}/{id}` — delete

2. For sub-resources (max 2 levels of nesting):
   - `GET /v{n}/{parent}/{id}/{children}` — list children
   - `POST /v{n}/{parent}/{id}/{children}` — create child

3. For non-CRUD actions, use verb suffix as last resort:
   - `POST /v{n}/{resources}/{id}/cancel`
   - `POST /v{n}/{resources}/{id}/verify`

4. Present the endpoint table to the user for confirmation before proceeding.

### Naming Rules

- Plural nouns for collections (`/orders`, not `/order`)
- kebab-case for multi-word segments (`/line-items`)
- No verbs in URL paths (use HTTP methods)
- Opaque IDs (UUIDs or prefixed IDs like `ord_abc123`, not sequential integers)

---

## PHASE 4: SPECIFICATION

Generate a complete OpenAPI 3.1 specification. The spec MUST include all of the following sections.

### Required Sections

#### 1. Info Block

```yaml
openapi: 3.1.0
info:
  title: {API Title}
  version: 1.0.0
  description: |
    {One-paragraph description of the API's purpose and intended consumers.}
  contact:
    name: {team name}
    email: {team email}
servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://api-staging.example.com/v1
    description: Staging
```

#### 2. Security Schemes

Based on the auth decision from Phase 2. Always include at the top level:

```yaml
security:
  - bearerAuth: []
```

#### 3. Paths

For every endpoint designed in Phase 3. Each operation MUST include:
- `summary` — short description
- `operationId` — unique, camelCase identifier
- `tags` — resource group
- All relevant response codes (2xx, 4xx) with `$ref` to reusable responses
- At least one `example` per request/response
- `parameters` for path, query, and header params

#### 4. Error Envelope (RFC 9457 Problem Details)

Include these reusable response and schema components:

```yaml
components:
  schemas:
    ProblemDetails:
      type: object
      required: [type, title, status]
      description: RFC 9457 Problem Details object
      properties:
        type:
          type: string
          format: uri
          description: URI identifying the error type
        title:
          type: string
          description: Short, human-readable summary
        status:
          type: integer
          description: HTTP status code
        detail:
          type: string
          description: Explanation specific to this occurrence
        instance:
          type: string
          description: URI of the request that produced the error
        requestId:
          type: string
          description: Correlation ID for distributed tracing

    ValidationProblemDetails:
      allOf:
        - $ref: '#/components/schemas/ProblemDetails'
        - type: object
          properties:
            errors:
              type: array
              items:
                $ref: '#/components/schemas/FieldError'

    FieldError:
      type: object
      required: [field, code, message]
      properties:
        field:
          type: string
          description: JSON path of the field that failed validation
        code:
          type: string
          description: Machine-readable error code
        message:
          type: string
          description: Human-readable validation failure description

  responses:
    BadRequest:
      description: Request is malformed or missing required fields
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'

    Unauthorized:
      description: Authentication credentials missing or invalid
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'

    Forbidden:
      description: Caller is authenticated but lacks permission
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'

    NotFound:
      description: The requested resource does not exist
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'

    UnprocessableEntity:
      description: Semantically invalid request (business rule or validation failure)
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationProblemDetails'

    TooManyRequests:
      description: Rate limit exceeded
      headers:
        Retry-After:
          description: Seconds until the client may retry
          schema:
            type: integer
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
```

#### 5. Pagination Components

Based on the pagination decision from Phase 2.

**Cursor-based (default):**

```yaml
components:
  parameters:
    Limit:
      name: limit
      in: query
      description: Number of results per page (max 100)
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20

    After:
      name: after
      in: query
      description: Cursor for the next page (from previous response)
      schema:
        type: string

    Before:
      name: before
      in: query
      description: Cursor for the previous page
      schema:
        type: string

  schemas:
    PaginationMeta:
      type: object
      properties:
        hasNext:
          type: boolean
          description: Whether more results exist after this page
        hasPrev:
          type: boolean
          description: Whether results exist before this page

    PaginationLinks:
      type: object
      properties:
        self:
          type: string
          format: uri
        next:
          type: string
          format: uri
        prev:
          type: string
          format: uri
```

**Offset-based (if selected):**

```yaml
components:
  parameters:
    Page:
      name: page
      in: query
      description: Page number (1-indexed)
      schema:
        type: integer
        minimum: 1
        default: 1

    PerPage:
      name: perPage
      in: query
      description: Items per page (max 100)
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20

  schemas:
    PaginationMeta:
      type: object
      properties:
        total:
          type: integer
          description: Total items matching the query
        page:
          type: integer
        perPage:
          type: integer
        totalPages:
          type: integer

    PaginationLinks:
      type: object
      properties:
        self:
          type: string
          format: uri
        next:
          type: string
          format: uri
        prev:
          type: string
          format: uri
        first:
          type: string
          format: uri
        last:
          type: string
          format: uri
```

#### 6. Response Envelope

All collection endpoints use `data` + `meta` + `links`. All single-resource endpoints use `data` + `meta`.

```yaml
# Collection response pattern
{Resource}ListResponse:
  type: object
  required: [data, meta]
  properties:
    data:
      type: array
      items:
        $ref: '#/components/schemas/{Resource}'
    meta:
      $ref: '#/components/schemas/PaginationMeta'
    links:
      $ref: '#/components/schemas/PaginationLinks'

# Single resource response pattern
{Resource}Response:
  type: object
  required: [data]
  properties:
    data:
      $ref: '#/components/schemas/{Resource}'
    meta:
      type: object
      properties:
        requestId:
          type: string
        timestamp:
          type: string
          format: date-time
```

#### 7. Resource Schemas

For each resource, generate:
- The resource schema with required fields, types, formats, and examples
- Create request schema (required fields only)
- Update request schema (all fields optional)
- Enum schemas for status fields

Field rules:
- ISO 8601 dates in UTC (`format: date-time`)
- Money as integer cents (never float)
- Opaque string IDs with prefix examples (`ord_abc123`)
- Empty arrays as `[]`, never null

---

## PHASE 5: VALIDATION

After generating the spec, verify it:

1. **Structural check:** Confirm the YAML is syntactically valid by reading it back.
2. **OpenAPI 3.1 compliance check:** Verify `openapi: 3.1.0` is set and all `$ref` targets resolve.
3. **Completeness checklist:**
   - [ ] All resource URLs use plural nouns
   - [ ] No verbs in URL paths
   - [ ] Nesting depth is 2 levels maximum
   - [ ] HTTP methods match CRUD semantics
   - [ ] Every mutating endpoint requires auth
   - [ ] Error responses use ProblemDetails schema
   - [ ] Validation errors include field-level detail
   - [ ] Pagination on all collection endpoints
   - [ ] Every endpoint has at least one example
   - [ ] Dates use ISO 8601 in UTC
   - [ ] Money fields use integer cents (if applicable)
   - [ ] Rate limiting headers documented
   - [ ] `operationId` is unique across all operations

4. Report any checklist failures and fix them before saving.

---

## SAVE

Save the validated spec to:

Resolve the active project context: check for an existing `.skilmarillion/projects/` structure. If found, use the active `{slug}`. If not found, ask the user for the feature slug.

```
{project_root}/.skilmarillion/projects/{slug}/api/{api-name}-openapi.yaml
```

Create the directory if it does not exist:

```bash
mkdir -p {project_root}/.skilmarillion/projects/{slug}/api
```

Confirm the save path with the user before writing:

> Saving OpenAPI spec to `.skilmarillion/projects/{slug}/api/{api-name}-openapi.yaml`. Proceed?

---

## WHAT NOT TO DO

- Do NOT skip the interview phases and jump straight to spec generation.
- Do NOT use OpenAPI 3.0 features. Pin to 3.1.0 (e.g., use `type: ["string", "null"]` instead of `nullable: true`).
- Do NOT omit error responses from any endpoint.
- Do NOT omit pagination from collection endpoints.
- Do NOT use float for monetary values.
- Do NOT nest sub-resources deeper than 2 levels.
- Do NOT put sequential integer IDs in examples (use opaque prefixed IDs).

---

## NEXT STEP BREADCRUMB

After saving the spec:

> API spec saved to `.skilmarillion/projects/{slug}/api/{api-name}-openapi.yaml`.
>
> Next steps:
> - **Implement:** Run `/impl:tdd` to scaffold controllers and tests from this spec.
> - **Schema:** Run `/arch:schema` to design the database schema for these resources.
> - **Diagram:** Run `/arch:diagram` to visualize the API architecture.

If `impl` is not installed, include:

> Install `impl` with: `/plugin marketplace add https://github.com/TrevorEdris/skilmarillion` and select the `impl` plugin.

**Spec-exists hint:** After displaying the next steps, check for existing specs in `docs/` (glob for `docs/**/specs/SPEC-*.md` or `docs/**/SDD-*.md`). If a spec is found for a related feature, append:

> A spec exists at `{spec-path}` -- `/impl:tdd {spec-path}` will pick up both the spec and these design artifacts.

If multiple specs exist, list the most recently modified one and note the count:

> {count} specs found. Most recent: `{spec-path}` -- `/impl:tdd {spec-path}` will pick up both the spec and these design artifacts.
