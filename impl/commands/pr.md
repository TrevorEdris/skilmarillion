---
description: Generate a pull request description with AC traceability, detecting and following PR templates when present
argument-hint: "[base-branch]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - "Bash(git diff:*)"
  - "Bash(git log:*)"
  - "Bash(git branch:*)"
  - "Bash(git remote:*)"
  - "Bash(gh pr:*)"
  - "Bash(GITHUB_TOKEN= gh pr:*)"
  - AskUserQuestion
model: sonnet
---

# /impl:pr

Generate a pull request description from the current branch's commits and diffs. Detects `.github/PULL_REQUEST_TEMPLATE.md` when present and fills its sections; falls back to a standard format when absent.

**Model selection:** If a PR template is detected, switch to `haiku` — the task becomes mechanical section-fill from diff + spec ACs. If no template exists, stay on `sonnet` — judgment is needed to write a coherent summary without structural guidance.

---

## Flow

### 1. Determine base branch

If the user provided a `[base-branch]` argument, use it. Otherwise:

```bash
git remote show origin | grep 'HEAD branch'
```

Fall back to `main` if detection fails. Confirm with the user: "Creating PR against `<base>` — correct?"

### 2. Gather branch context

```bash
git log <base>..HEAD --oneline
git diff <base>...HEAD --stat
git diff <base>...HEAD
```

If no commits exist ahead of base, stop: "No commits ahead of `<base>`. Nothing to open a PR for."

### 3. Detect PR template

Search for a PR template in the repository:

```
.github/PULL_REQUEST_TEMPLATE.md
.github/pull_request_template.md
.github/PULL_REQUEST_TEMPLATE/default.md
docs/pull_request_template.md
pull_request_template.md
```

Use the first match found. If a template is detected, log: "Found PR template at `<path>`. Filling template sections."

### 4. Find spec or impl-details for traceability

Search for a spec or impl-details file related to this branch:

1. Check for `.impl-state-*.local.yaml` — extract the spec path if present
2. Search `docs/` for spec files matching the branch slug
3. Check the active session directory for `IMPL_DETAILS.md`

If found, extract acceptance criteria for traceability mapping.

### 5. Generate PR description

#### When template is present

Read the template file. For each section heading in the template:

- **Summary / Description / What:** Summarize the changes from the diff, referencing acceptance criteria when available.
- **Test Plan / Testing / How to Test:** List verification steps derived from the test files in the diff. If no tests exist, note that.
- **Checklist / Checks:** Fill checkboxes based on what the diff evidence supports (tests added, docs updated, etc.).
- **Related Issues / Links:** Include the spec path if found. Reference issue numbers from commit messages.
- **Breaking Changes:** Flag if any are detected (same heuristics as `/impl:commit`).

For any template section not matching the above patterns, make a best-effort fill from the diff context or leave the section with a `<!-- TODO: fill this section -->` comment.

#### When no template is present

Use this standard format:

```markdown
## Summary

- <1-3 bullet points describing what changed and why>

## Spec Traceability

**Spec:** `<path-to-spec-or-impl-details>` (or "No spec file found")

### Acceptance Criteria Coverage

| AC | Status | Evidence |
|----|--------|----------|
| <AC text> | Covered / Partial / Not covered | <test file or code reference> |

## Test Plan

- [ ] <verification step from test files>
- [ ] <manual verification step if applicable>

## Changes

<file-level summary grouped by purpose: new files, modified files, deleted files>

## Notes

<any caveats, follow-up work, or deployment considerations>
```

### 6. Present for approval

Show the complete PR description to the user. Offer three options:

1. **Create PR** — open the PR with this description using `gh pr create`
2. **Edit** — user provides modifications, re-present
3. **Copy only** — output the description for the user to paste manually

### 7. Create PR (if approved)

```bash
gh pr create --base <base-branch> --title "<pr-title>" --body "<approved-body>"
```

**PR title rules:**
- Under 70 characters
- Format: `<type>(<scope>): <description>` matching the primary commit type
- Imperative mood, no period

Report the PR URL after creation.

**Suggest next step:** "Consider running `/review:review` on this PR before requesting human review."

---

## Edge Cases

- **Draft PR:** If the user asks for a draft, add `--draft` to the `gh pr create` command.
- **No gh CLI:** If `gh` is not available, output the description for manual use and provide the GitHub URL format for creating a PR in the browser.
- **Multiple specs:** If multiple spec files match, ask the user which one to use for traceability.
- **Large diffs:** If the diff exceeds 500 lines, summarize by file group rather than line-by-line analysis. Focus on the structural changes.
- **Amended history:** If the branch has been rebased, use `git log <base>..HEAD` (two dots) to capture all commits currently on the branch.
