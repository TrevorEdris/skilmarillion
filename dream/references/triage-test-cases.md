# Triage Test Cases

Reference inputs for manual verification of the `triage` agent. Run `/dream:sdd "<Input>"` and compare the returned JSON against the expected output. Fields marked in **Pass Criteria** must match exactly; `rationale` is informational and need not match verbatim.

---

## Case 1 — TRIVIAL / LOW: Typo fix in README

**Input:**
```
Fix typo in README: "recieve" → "receive"
```

**Expected JSON:**
```json
{
  "size": "TRIVIAL",
  "risk": "LOW",
  "routing_decision": "trivial",
  "rationale": "Single-word typo correction in documentation. No behavior change, no code touched.",
  "slug": "fix-typo-in-readme-recieve-receive"
}
```

**Pass Criteria:** `size`, `risk`, `routing_decision`, `slug` must match exactly.

---

## Case 2 — SMALL / LOW: Null check bug fix

**Input:**
```
Add null check in getUserProfile() to prevent crash when user has no address on file
```

**Expected JSON:**
```json
{
  "size": "SMALL",
  "risk": "LOW",
  "routing_decision": "lightweight_spec",
  "rationale": "Fix to existing function in 1–2 files. No new capability, no user-facing change. Crash is internal; fix is contained.",
  "slug": "add-null-check-in-getuserprofile-to-prev"
}
```

**Pass Criteria:** `size`, `risk`, `routing_decision` must match exactly. `slug` must be lowercased, hyphenated, ≤ 40 chars.

---

## Case 3 — FEATURE / MODERATE: Email notification on password change

**Input:**
```
Send an email notification to users when their password is changed
```

**Expected JSON:**
```json
{
  "size": "FEATURE",
  "risk": "MODERATE",
  "routing_decision": "full_workflow",
  "rationale": "New user-visible behavior (email notification) that does not currently exist. Touches auth flow, email service, and potentially template files. User-facing but recoverable.",
  "slug": "send-an-email-notification-to-users-when"
}
```

**Pass Criteria:** `size`, `risk`, `routing_decision` must match exactly.

---

## Case 4 — FEATURE / HIGH: New OAuth2 login option

**Input:**
```
Add OAuth2 login with Google as a new authentication option
```

**Expected JSON:**
```json
{
  "size": "FEATURE",
  "risk": "HIGH",
  "routing_decision": "full_workflow",
  "rationale": "New user-visible auth capability. Touches authentication middleware and session handling. High risk because auth changes are hard to revert and can lock users out.",
  "slug": "add-oauth2-login-with-google-as-a-new-au"
}
```

**Pass Criteria:** `size`, `risk`, `routing_decision` must match exactly.

---

## Case 5 — EPIC / HIGH: Multi-tenant billing system

**Input:**
```
Build a multi-tenant billing system that handles subscriptions, invoicing, and payment processing for multiple organizations
```

**Expected JSON:**
```json
{
  "size": "EPIC",
  "risk": "HIGH",
  "routing_decision": "decompose_first",
  "rationale": "Spans subscriptions, invoicing, and payment processing — at least three distinct features. Touches payment systems (HIGH risk by definition). Must be decomposed into FEATURE-sized chunks before any spec can be written.",
  "slug": "build-a-multi-tenant-billing-system-that"
}
```

**Pass Criteria:** `size`, `risk`, `routing_decision` must match exactly.

---

## Case 6 — Edge Case: Over-classification guard (logging in payment processor)

**Input:**
```
Add logging to the payment processor to track failed transaction attempts
```

**Expected JSON:**
```json
{
  "size": "SMALL",
  "risk": "HIGH",
  "routing_decision": "lightweight_spec",
  "rationale": "Adding logging is a contained change (1–3 files), but the payment processor is HIGH risk by definition. Over-classification rule: must NOT classify as TRIVIAL because it touches payment-adjacent code that is hard to revert if the logging causes a regression.",
  "slug": "add-logging-to-the-payment-processor-to"
}
```

**Pass Criteria:** `size` MUST NOT be `TRIVIAL`. `risk` must be `HIGH`. `routing_decision` must NOT be `trivial`.

**What to verify:** This case catches the over-classification rule. "Add logging" sounds trivial, but the payment processor context raises risk and prevents TRIVIAL routing.
