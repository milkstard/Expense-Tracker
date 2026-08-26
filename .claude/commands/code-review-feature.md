---
description: Run the Spendly feature code-review pipeline — spendly-quality-reviewer and spendly-security-reviewer in parallel — over a completed feature's changes.
argument-hint: "optional: step number or feature slug — defaults to the current branch's diff against main"
allowed-tools: Read, Glob, Bash(git:*), Agent
---

You are coordinating two existing, read-only subagents to review a
completed Spendly feature: `spendly-quality-reviewer` (clean/maintainable
Flask code) and `spendly-security-reviewer` (security issues). Both were
written to run in parallel and never edit code — you only determine the
review scope, launch both at once, and merge their reports. You do not
review the code yourself and you do not fix anything.

User input: $ARGUMENTS

## Step 1 — Determine the review scope

- If $ARGUMENTS names a step number or feature slug, resolve it against
  `.claude/specs/NN-<slug>.md` with Glob (same convention as
  `/test-feature`) purely for context to pass to the reviewers — neither
  reviewer needs the spec to do its job, but it helps them understand what
  the feature is.
- Otherwise, default to reviewing the current branch's changes. Collect the
  union of all three of these (a file counts as changed if it appears in
  any of them):
  - `git diff main...HEAD --name-only` — committed changes ahead of `main`
  - `git diff --name-only` — unstaged working-tree changes
  - `git diff --cached --name-only` — staged changes
- If that union is empty, output exactly `No changes detected` and stop —
  do not invoke either subagent.

## Step 2 — Launch both reviewers in parallel

Send a single message containing two Agent tool calls, one per subagent —
do not launch them sequentially:

- `subagent_type: "spendly-quality-reviewer"` — prompt it with the list of
  changed files (and the spec context if you found one in Step 1), and
  remind it of its own scope: clean/maintainable Flask code only, read-only,
  report findings ranked by impact.
- `subagent_type: "spendly-security-reviewer"` — prompt it with the same
  list of changed files (and spec context if found), and remind it of its
  own scope: security issues only, read-only, report findings ranked by
  severity.

Wait for both to finish before continuing.

## Step 3 — Merge and report

Combine both reports into one summary for the user:

```
Scope:    <changed files reviewed, and the spec if one was resolved>

Security findings (spendly-security-reviewer):
  <ranked findings, or "none found">

Quality findings (spendly-quality-reviewer):
  <ranked findings, or "none found">
```

List security findings first — they're the higher-priority class. Do not
edit any files yourself; this command only reports what the two subagents
found. If either subagent reports nothing wrong, say so plainly rather than
inventing findings to fill the report.
