# skilmarillion
Claude plugins curated to enhance your AI workflows

## Recommended .gitignore

Skilmarillion writes all output (state files, specs, ADRs, session artifacts) to `.skilmarillion/` in the target project root. Choose one of these strategies for your `.gitignore`:

### Strategy A -- Ignore everything (simplest)

Best for solo developers or teams that treat all Skilmarillion output as ephemeral.

```gitignore
.skilmarillion/
```

### Strategy B -- Track specs and ADRs, ignore ephemeral

Best for teams that want planning artifacts (specs, ADRs) version-controlled but session state ignored.

```gitignore
.skilmarillion/projects/*/PROJECT-STATE.yaml
.skilmarillion/projects/*/SESSION.md
.skilmarillion/projects/*/reviews/
.skilmarillion/projects/*/impl/
```
