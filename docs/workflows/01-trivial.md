# Scenario 1: Trivial — One-Line Fix

> *"Fix the typo in the README: 'recieve' → 'receive'"*

**Who:** Any engineer, solo.

**Plugins required:** `plan`

---

## Commands

```
You:   /plan:sdd Fix typo in README — recieve should be receive

plan:  Triage result:
         Size: TRIVIAL
         Risk: LOW
         Routing: direct-apply

       This looks like a trivial change. Ready to apply it now? (yes/no)

You:   yes

plan:  [applies edit] Done. README.md updated.
```

---

## Artifacts

None. No spec, no state file, no PR needed.

---

## Time

~30 seconds.
