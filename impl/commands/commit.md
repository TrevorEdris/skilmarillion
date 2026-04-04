---
description: Generate a conventional commit message from staged changes with automatic breaking change detection
argument-hint: "[--breaking] [--scope <scope>]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - "Bash(git diff:*)"
  - "Bash(git status:*)"
  - "Bash(git log:*)"
  - "Bash(git add:*)"
  - "Bash(git commit:*)"
  - AskUserQuestion
model: haiku
---

# /impl:commit

Generate a conventional commit message from staged changes. Detects breaking changes, infers type and scope, and presents the message for user approval before committing.

**Never commits automatically.** The user always reviews and approves the message first.

---

## Flow

### 1. Check staged changes

Run:

```bash
git diff --cached --stat
```

If nothing is staged:

1. Show unstaged changes: `git diff --stat`
2. Show untracked files: `git status --short`
3. Ask the user which files to stage
4. Stage the selected files with `git add`
5. Re-run `git diff --cached --stat` to confirm

If still nothing staged after prompting, stop: "Nothing to commit."

### 2. Read the full staged diff

```bash
git diff --cached
```

Also gather context:

```bash
git log --oneline -5
```

### 3. Determine commit type

Analyze the staged diff to classify the change:

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

**Disambiguation rules:**
- If the code was *wrong* before, it is a `fix`. If it was *correct but messy*, it is a `refactor`.
- If a new public interface or capability is exposed, it is a `feat`. Internal restructure is `refactor`.
- Use `ci` only for CI/CD pipeline files. Other build/tooling changes are `chore`.

### 4. Determine scope

Infer scope from the primary package, module, or directory affected:

- Use the most specific relevant unit (package name, component, service)
- Lowercase, single word or hyphenated
- If changes span multiple unrelated areas, omit scope
- If all changes are within one directory subtree, use that directory name

Examples: `auth`, `api`, `commands`, `plugin`, `plan`, `impl`

### 5. Detect breaking changes

A change is breaking if ANY of the following are true:

1. **Public API signature changed** — function/method parameters added, removed, or reordered; return type changed; endpoint path or method changed
2. **Exported type or interface removed or renamed** — consumers will break at compile time
3. **Required configuration added** — existing deployments will fail without the new config
4. **Data format changed incompatibly** — existing serialized data cannot be read by the new code
5. **Default behavior changed** — callers relying on previous defaults will see different results
6. **Environment variable renamed or removed** — existing deployments will lose configuration
7. **CLI flag or argument removed or renamed** — scripts calling the tool will break

If a spec file exists in the repo for this feature, also check:
- Any acceptance criterion removed from the spec signals potential breakage

When breaking changes are detected:
- Add `!` after the type/scope: `feat(auth)!: replace session tokens with JWTs`
- Add a `BREAKING CHANGE:` footer explaining what broke and what consumers must do

### 6. Draft the commit message

Format:

```
<type>(<scope>)[!]: <description>

[optional body — explain WHY, not what]

[BREAKING CHANGE: <explanation>]
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Description rules:**
- Imperative mood, present tense ("add", not "added" or "adds")
- No period at end
- First line under 72 characters total
- Focus on *why* the change was made, not *what* the code does

**Body rules (when included):**
- Separate from subject with a blank line
- Explain *why* and *impact*, not the mechanical *what*
- Wrap at 72 characters
- Include issue references with `Fixes #N`, `Closes #N`, or `Refs #N` if applicable

### 7. Present for approval

Show the complete commit message to the user. Offer three options:

1. **Commit as-is** — run `git commit` with this message
2. **Edit** — user provides modifications, re-present
3. **Cancel** — abort without committing

### 8. Commit

Only after explicit user approval:

```bash
git commit -m "<approved message>"
```

Report the commit hash and short stat.

**Suggest next step:** "Consider running `/impl:pr` to open a pull request, or `/review:review` to run quality checks first."

Check whether the `review` plugin is installed (look for a `review/` directory at the skilmarillion plugin root, or check if `/review:review` is a known command). If not installed, append:
> "Install the review plugin: `claude plugin add review`"

---

## Breaking Change Examples

### Breaking — public API parameter added (required)

```diff
-func CreateUser(name string) (*User, error) {
+func CreateUser(name string, orgID string) (*User, error) {
```

Output:

```
feat(users)!: require org ID when creating users

Multi-tenancy requires every user to belong to an organization.
Existing callers must pass the org ID parameter.

BREAKING CHANGE: CreateUser now requires a second parameter (orgID string).
All callers must be updated.
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Breaking — environment variable renamed

```diff
-DB_URL=postgres://...
+DATABASE_URL=postgres://...
```

Output:

```
chore(config)!: rename DB_URL to DATABASE_URL

Aligns with the convention used by most ORMs and hosting platforms.

BREAKING CHANGE: The DB_URL environment variable has been renamed to
DATABASE_URL. Update all deployment configurations.
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Non-breaking — internal refactor

```diff
-func (r *repo) buildQuery(filter Filter) string {
+func (r *repo) buildQuery(filter Filter) *QueryBuilder {
```

(Internal, unexported method — no external consumers.)

Output:

```
refactor(db): return QueryBuilder from buildQuery for composability

Enables chaining filters without rebuilding the SQL string each time.

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## .skilmarillion/ Exclusion

When scanning staged files, explicitly skip paths under `.skilmarillion/`. Do not stage `.skilmarillion/` files unless the user explicitly asks. If `.skilmarillion/` files are already staged, warn the user: "`.skilmarillion/` files are staged. These are local workflow artifacts — unstage them? (yes / no)"

---

## Edge Cases

- **Mixed changes** (feat + fix in same commit): prefer the higher-impact type. If a new feature also fixes a bug, use `feat`. If the fix is the primary intent and the new code is incidental, use `fix`.
- **Revert commits**: use `revert` type and reference the original commit: `revert: feat(auth): add OAuth2 login flow`
- **Empty scope**: omit parentheses entirely: `fix: handle null pointer in middleware`
- **Multiple scopes**: choose the primary affected area. If truly equal, omit scope.
