---
description: Security-focused code review identifying vulnerabilities with >80% confidence of real exploitation potential — exploitation chain required for every finding
argument-hint: "[file|directory|PR-number]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git show:*)
  - Bash(git status)
  - Bash(git branch:*)
  - Bash(gh pr view:*)
  - Bash(gh pr diff:*)
  - ToolSearch
model: opus
---

# /review:security

Identify high-confidence security vulnerabilities with real exploitation potential. Every finding must include a concrete exploitation chain — no theoretical concerns, no CWE-number fishing.

**Rule: findings only, no code edits.** This command produces a report. The user decides what to fix.

---

## Flow

### 1. Resolve target

If a PR number is provided: extract changed files via `gh pr diff`.

```bash
gh pr diff <number> --name-only
```

If a file path is provided: use it directly.

If a directory is provided: scan all source files in it.

If no argument is provided: check for staged or recent changes.

```bash
git diff --name-only --cached
git diff --name-only origin/HEAD...HEAD
```

If still nothing: ask the user to provide a target path or PR number.

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. Gather repository security context

Before examining changed code, understand the project's security posture:

- Identify security frameworks and libraries in use (e.g., helmet, csrf, bcrypt, jwt, ORM-based query builders)
- Look for established sanitization and validation patterns already present in the codebase
- Understand the project's trust boundaries: what is user input vs. server-controlled
- Note the language and framework — framework-specific mitigations affect what is exploitable

This context prevents false positives. Code that follows the project's established security patterns is not a finding.

### 3. Analyze each file for vulnerabilities

For every target file, read its full contents and trace data flow from untrusted inputs to sensitive operations. Examine these categories:

#### Input Validation

| Vulnerability | What to look for |
|---------------|-----------------|
| SQL injection | String concatenation in queries, raw SQL with user input |
| Command injection | User input in `child_process`, `subprocess`, `os.system`, `exec` |
| XXE injection | XML parsing without disabling external entities |
| Template injection | User input interpolated into template strings evaluated server-side |
| NoSQL injection | User input directly in MongoDB/Firestore query objects |
| Path traversal | User-controlled file paths without canonicalization |

#### Authentication and Authorization

| Vulnerability | What to look for |
|---------------|-----------------|
| Auth bypass | Logic flaws allowing unauthenticated access to protected resources |
| Privilege escalation | Missing role checks, IDOR without ownership verification |
| Session flaws | Predictable session tokens, missing expiry, insecure cookie flags |
| JWT issues | Missing signature verification, `alg: none` accepted, secrets in code |

#### Cryptography and Secrets

| Vulnerability | What to look for |
|---------------|-----------------|
| Hardcoded credentials | API keys, passwords, tokens in source code |
| Weak algorithms | MD5/SHA1 for passwords, ECB mode, custom crypto |
| Key mismanagement | Private keys in code, shared secrets across environments |

#### Code Execution

| Vulnerability | What to look for |
|---------------|-----------------|
| Deserialization RCE | `pickle.loads`, `yaml.load` without SafeLoader, Java deserialization of untrusted data |
| Eval injection | `eval()`, `exec()`, `Function()` with user-controlled input |
| XSS | `dangerouslySetInnerHTML`, `bypassSecurityTrustHtml`, `innerHTML` with user data |
| SSRF | User-controlled URLs in server-side HTTP requests (must control host or protocol) |

#### Data Exposure

| Vulnerability | What to look for |
|---------------|-----------------|
| Secret logging | Passwords, tokens, or PII written to logs in plaintext |
| Debug endpoints | Debug routes or admin panels accessible without authentication |
| API data leakage | Endpoints returning more data than the caller needs, exposing internal fields |

### 4. Filter false positives

Apply the decision tree to every potential finding before including it in the report:

```
1. Is it in the hard exclusion list? → Discard
2. Is it in test-only code?         → Discard
3. Is there a concrete attack path
   with untrusted input?            → Continue
4. Is confidence >= 0.8?            → Report
   Otherwise                        → Discard
```

#### Hard exclusions — never report these

- Denial of Service or resource exhaustion
- Secrets stored on disk if otherwise secured (handled by secret scanning tools)
- Rate limiting or throttling concerns
- Memory or CPU exhaustion
- Missing hardening measures without a concrete vulnerability
- Theoretical race conditions without a concrete exploit
- Outdated dependencies (handled by dependency scanning)
- Memory safety issues in Rust or other memory-safe languages
- Test-only code (not a production attack surface)
- Log spoofing (unsanitized output to logs)
- SSRF where attacker only controls the path (must control host or protocol)
- User content in AI prompts
- Regex injection or regex DoS
- Documentation files (not executable)
- Missing audit logs (compliance, not vulnerability)

#### Framework-specific mitigations

- **React / Angular:** XSS is mitigated by default. Only flag `dangerouslySetInnerHTML`, `bypassSecurityTrustHtml`, or raw `innerHTML` assignments with user input.
- **Node.js / Express:** Environment variables and CLI arguments are trusted. `child_process` requires user-controlled input to be dangerous.
- **Python:** `pickle` with untrusted input, `yaml.load()` without SafeLoader, `eval()`/`exec()` with user input, and `subprocess` with `shell=True` and user input are all dangerous.
- **Go:** Template injection requires `text/template` with user input; `html/template` auto-escapes.
- **GitHub Actions:** Workflow vulnerabilities need concrete attack paths. `github.event.issue.body` or `github.event.pull_request.title` in `run:` blocks are dangerous.

#### Precedents

- Logging high-value secrets in plaintext IS a vulnerability. Logging URLs or request metadata is safe.
- UUIDs are unguessable and do not need additional validation.
- Environment variables and CLI flags are trusted values.
- Resource management issues (memory leaks, file descriptor leaks) are NOT security vulnerabilities.
- Client-side permission checks are NOT vulnerabilities (backend is responsible).
- Only include MEDIUM findings if the attack path is obvious and concrete.

### 5. Assign severity and confidence

**Severity:**

| Level | Criteria |
|-------|----------|
| CRITICAL | Directly exploitable — leads to RCE, data breach, or authentication bypass with no preconditions |
| HIGH | Exploitable under specific but realistic conditions with significant impact |
| MEDIUM | Defense-in-depth issue or lower-impact vulnerability with a concrete (not theoretical) attack path |

**Confidence:**

| Range | Meaning |
|-------|---------|
| 0.9 - 1.0 | Certain exploit path identified |
| 0.8 - 0.9 | Clear vulnerability pattern with known exploitation methods |
| Below 0.8 | Do not report — too speculative |

### 6. Format findings

For every finding, include ALL of:

1. **Vulnerability type** — category name (e.g., SQL Injection, Command Injection)
2. **File and line** — `filename:line`
3. **Severity** — CRITICAL, HIGH, or MEDIUM
4. **Confidence** — decimal (0.8 minimum)
5. **Description** — what the vulnerability is and why it is exploitable in this specific context
6. **Exploitation chain** — step-by-step attack scenario showing how an attacker reaches and triggers the vulnerability, starting from the entry point (e.g., HTTP request, CLI input) through to impact (e.g., data exfiltration, code execution). This is mandatory. A finding without an exploitation chain is not a finding.
7. **Affected code** — the vulnerable code snippet (quoted from source)
8. **Recommendation** — specific, actionable fix

### 7. Clean input handling

If the target has no vulnerabilities above the confidence threshold, report exactly:

> Clean run. No security vulnerabilities detected above the 80% confidence threshold.

Do NOT invent findings to fill a report. A clean result is a good result.

### 8. Produce report

Save the report to the `.skilmarillion/` output directory:

```
.skilmarillion/projects/{slug}/reviews/security-{target}.md
```

Report structure:

```markdown
# Security Review: <target>

**Date:** YYYY-MM-DD
**Files scanned:** N
**Findings:** N (X critical, Y high, Z medium)
**Confidence threshold:** 80%
**Scan surface:** OWASP Top 10 + language/framework-specific patterns

## Repository Security Context

<Brief summary of security frameworks, libraries, and patterns already in use>

## Findings

### CRITICAL

#### <Vulnerability Type>: `<file>:<line>`

**Severity:** CRITICAL | **Confidence:** 0.X

**Description:** <What and why>

**Exploitation chain:**
1. Attacker does X (entry point)
2. Input reaches Y (data flow)
3. Y passes to Z without sanitization (vulnerable operation)
4. Result: <impact — RCE, data breach, auth bypass, etc.>

**Affected code:**
\```
<vulnerable snippet>
\```

**Recommendation:** <specific fix>

---

### HIGH

...

### MEDIUM

...

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
| **Total** | **N** |
```

---

## OWASP Top 10 Scan Surface

Every review covers these categories as a baseline. Not all apply to every codebase — skip categories that are irrelevant to the target's technology stack.

| ID | Category | Focus |
|----|----------|-------|
| A01 | Broken Access Control | Missing auth checks, IDOR, privilege escalation, CORS misconfig |
| A02 | Cryptographic Failures | Hardcoded secrets, weak algorithms, improper key management |
| A03 | Injection | SQL, command, NoSQL, LDAP, XPath injection |
| A04 | Insecure Design | Missing security controls in design (auth rate limiting, brute force) |
| A05 | Security Misconfiguration | Default credentials, verbose errors, unnecessary features |
| A06 | Vulnerable Components | Outdated dependencies with known CVEs (note: defer to dependency scanning) |
| A07 | Auth Failures | Weak passwords, session fixation, missing timeout, insecure tokens |
| A08 | Integrity Failures | Insecure deserialization, unsigned updates, untrusted CI/CD |
| A09 | Logging Failures | Sensitive data in logs, missing security event logging |
| A10 | SSRF | User-controlled URLs in server requests, URL parser bypasses |

---

## WHAT NOT TO DO

- Do NOT modify any file — this command is read-only, findings only.
- Do NOT report findings below 80% confidence — silence is preferable to false positives.
- Do NOT report findings without an exploitation chain — theoretical concerns are noise.
- Do NOT report items from the hard exclusion list regardless of how they look.
- Do NOT flag test-only code as production vulnerabilities.
- Do NOT flag framework-mitigated patterns (e.g., XSS in React without dangerouslySetInnerHTML).
- Do NOT use Write or Edit tools under any circumstances.

---

## NEXT STEP BREADCRUMB

After displaying the report:

- If findings exist: "To address these findings, run `/impl:debug` or `/impl:refactor` on the affected files."
- If clean: "No action needed. Clean security review."
- If `impl` plugin is not installed, include: "Install the impl plugin: `/plugin install impl@skilmarillion`"
