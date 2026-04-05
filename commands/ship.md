---
description: Conventional commit from staged changes, with optional PR opening. Detects breaking changes and PR templates.
argument-hint: "[--pr [base-branch]] [--breaking] [--scope <scope>] [--draft]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - "Bash(git diff:*)"
  - "Bash(git status:*)"
  - "Bash(git log:*)"
  - "Bash(git add:*)"
  - "Bash(git commit:*)"
  - "Bash(git push:*)"
  - "Bash(git branch:*)"
  - "Bash(git remote:*)"
  - "Bash(gh pr:*)"
  - "Bash(GITHUB_TOKEN= gh pr:*)"
  - AskUserQuestion
  - ToolSearch
model: haiku
---

# /fellowship:ship

Generates a conventional commit from staged changes, with optional PR opening. Detects breaking changes, infers type and scope, presents the message for user approval.

**Never commits or pushes automatically.** The user always reviews and approves before anything lands.

> **Personality:** direct, brief. When findings are clean: "Clean run. No issues above threshold."

---

## DISPATCH — Flags

| Flag | Behavior |
|------|----------|
| *(no flag)* | Conventional commit only |
| `--pr [base]` | After commit, push branch and open a PR (detects `.github/PULL_REQUEST_TEMPLATE.md`) |
| `--breaking` | Force the `BREAKING CHANGE:` footer (and `!` after type/scope) |
| `--scope <scope>` | Override auto-detected scope |
| `--draft` | (Only with `--pr`) Open the PR as a draft |

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

---

## STAGE 1 — Conventional Commit

### 1. Check staged changes

```bash
git diff --cached --stat
```

If nothing is staged: show unstaged + untracked via `git diff --stat` and `git status --short`, ask the user which files to stage (**never** `git add -A`), stage, re-confirm. If still nothing: stop with "Nothing to commit."

### 2. Read the full staged diff

```bash
git diff --cached
git log --oneline -5
```

### 3. Determine commit type

| Pattern | Type |
|---------|------|
| New files implementing behavior (not tests) | `feat` |
| Fixed logic, corrected regression, error handling fix | `fix` |
| Code moved or restructured, no behavior change | `refactor` |
| Only test files changed | `test` |
| Only documentation or markdown changed | `docs` |
| Build config, CI pipeline, dependency updates | `chore` |
| CI/CD pipeline definition files specifically | `ci` |
| Measurable performance improvement | `perf` |
| Formatting, whitespace, no logic change | `style` |

**Disambiguation:**
- Code was *wrong* → `fix`. Code was *correct but messy* → `refactor`.
- New public interface exposed → `feat`. Internal restructure → `refactor`.
- `ci` only for CI/CD pipeline files; other build/tooling is `chore`.

### 4. Determine scope

Infer from the primary package/module/directory affected. Lowercase, single word or hyphenated. If `--scope <x>` was passed, use it. If changes span unrelated areas, omit scope.

### 5. Detect breaking changes

A change is breaking if ANY of:

1. Public API signature changed (params, return type, endpoint path/method)
2. Exported type or interface removed or renamed
3. Required configuration added
4. Data format changed incompatibly
5. Default behavior changed
6. Environment variable renamed or removed
7. CLI flag or argument removed or renamed

When detected (or `--breaking` was passed): add `!` after type/scope and a `BREAKING CHANGE:` footer explaining what broke and what consumers must do.

### 6. Draft the commit message

```
<type>(<scope>)[!]: <description>

[optional body — explain WHY, not what]

[BREAKING CHANGE: <explanation>]
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

**Rules:** imperative mood, no trailing period, first line ≤72 chars. Body wraps at 72, explains WHY not what. Include `Fixes #N` / `Closes #N` / `Refs #N` when applicable.

### 7. Present for approval

Show complete message via `AskUserQuestion`:
1. **Commit as-is** — run `git commit`
2. **Edit** — user provides modifications, re-present
3. **Cancel** — abort

### 8. Commit

Only after explicit approval:

```bash
git commit -m "<approved message>"
```

Report the commit hash and short stat.

---

## STAGE 2 — Open PR (only if `--pr`)

### 1. Determine base branch

If user provided `[base-branch]` after `--pr`, use it. Otherwise:

```bash
git remote show origin | grep 'HEAD branch'
```

Fall back to `main` if detection fails. Confirm with the user.

### 2. Push the branch

```bash
git push -u origin <current-branch>
```

If no upstream is configured and the user didn't approve `-u`, ask first.

### 3. Gather branch context

```bash
git log <base>..HEAD --oneline
git diff <base>...HEAD --stat
git diff <base>...HEAD
```

### 4. Detect PR template

Check in order:
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/pull_request_template.md`
- `.github/PULL_REQUEST_TEMPLATE/default.md`
- `docs/pull_request_template.md`
- `pull_request_template.md`

If found: fill its sections from the diff + any spec ACs.

### 5. Find spec for traceability

Look for:
- `.skilmarillion/projects/*/PROJECT-STATE.yaml` — extract `spec_path` from the `plan:` or `impl:` section
- `.skilmarillion/projects/*/specs/SPEC-*.md` matching the branch slug

If found, extract ACs for the **AC Traceability** table.

### 6. Generate PR description

**With template:** fill each template section from diff evidence. Any unmatched section gets `<!-- TODO: fill this section -->`.

**Without template:** use the standard format:

```markdown
## Summary

- <1-3 bullets describing what changed and why>

## Spec Traceability

**Spec:** `<path>` (or "No spec file found")

### Acceptance Criteria Coverage

| AC | Status | Evidence |
|----|--------|----------|
| <AC text> | Covered / Partial / Not covered | <test file or code reference> |

## Test Plan

- [ ] <verification step from test files>
- [ ] <manual verification step if applicable>

## Changes

<file-level summary grouped by purpose>

## Notes

<caveats, follow-up work, deployment considerations>
```

### 7. Present for approval

1. **Create PR** — `gh pr create`
2. **Edit** — re-present
3. **Copy only** — output for manual paste

### 8. Create PR

```bash
gh pr create --base <base> --title "<pr-title>" --body "<approved-body>" [--draft]
```

**PR title rules:** under 70 chars, format `<type>(<scope>): <description>` matching the primary commit type, imperative mood, no period.

Report the PR URL.

---

## .skilmarillion/ EXCLUSION POLICY

- When scanning staged files, explicitly skip paths under `.skilmarillion/`.
- Do not stage `.skilmarillion/` files unless the user explicitly asks.
- If `.skilmarillion/` files are already staged, warn: "`.skilmarillion/` files are staged. These are local workflow artifacts — unstage them? (yes / no)"
- When summarizing PR diffs, exclude `.skilmarillion/` paths silently.

---

## GIT SAFETY

- Never push directly to `main` or `master` without explicit approval.
- Never commit `.env` files, credentials, or secrets.
- Prefer specific file staging over `git add -A` or `git add .`.
- On `main`/`master`: STOP and ask before committing.

---

## EDGE CASES

- **Mixed changes** (feat + fix): prefer higher-impact type.
- **Revert**: `revert: <original subject>` referencing the original commit.
- **Empty scope**: omit parens entirely: `fix: handle null pointer`.
- **Multiple scopes**: pick primary affected area; if truly equal, omit.
- **No gh CLI** (for `--pr`): output the description for manual use, provide the GitHub compare URL.
- **Draft PR**: pass `--draft` to the flag.
- **Large diff** (>500 lines): summarize by file group, not line-by-line.

---

## NEXT STEP BREADCRUMB

- After commit only: "Committed. Run `/fellowship:ship --pr` to open a pull request, or `/fellowship:review` to run quality checks first."
- After PR opened: "PR open at `<url>`. Consider `/fellowship:review <pr-number>` before requesting human review."
