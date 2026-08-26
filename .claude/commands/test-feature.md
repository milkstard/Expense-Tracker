---
description: Write and run pytest tests for a Spendly feature step, coordinating the spendly-test-writer and spendly-test-runner subagents.
argument-hint: "Step number or feature name, e.g. 5 or profile-backend-implementation"
allowed-tools: Read, Glob, Agent
---

You are coordinating two existing subagents to test a Spendly feature step:
`spendly-test-writer` (writes pytest tests from a spec) and
`spendly-test-runner` (runs pytest and reports results). You do not write or
run tests yourself in this command — you only identify the right spec and
call the two subagents in the correct order.

User input: $ARGUMENTS

## Step 1 — Identify the spec

From $ARGUMENTS, resolve which feature step is meant (a step number, a slug,
or a feature name). List `.claude/specs/*.md` with Glob and match against
`NN-<slug>.md`.

- If exactly one spec matches, proceed with it.
- If none match, list the available specs in `.claude/specs/` and ask the
  user to pick one. Do not guess.
- If more than one plausibly matches, ask the user to disambiguate.

## Step 2 — Run spendly-test-writer

Call the Agent tool with `subagent_type: "spendly-test-writer"`. The prompt
must tell it exactly which spec file to use (its full path, e.g.
`.claude/specs/05-profile-backend-implementation.md`) and remind it of its
own scope: derive tests from that spec only, write/update
`tests/test_<slug>.py` (and `tests/conftest.py` if needed), and do not run
pytest or edit application code — it reports back which files it
created/updated and any spec ambiguities it hit.

Wait for this subagent to finish before continuing. Do not run it in
parallel with the runner — the runner depends on its output existing.

## Step 3 — Run spendly-test-runner

Only after the writer has finished, call the Agent tool with
`subagent_type: "spendly-test-runner"`. The prompt must tell it which test
file to run (`tests/test_<slug>.py`, matching the same slug as the spec) and
remind it of its own scope: run pytest, cross-reference failures against the
spec, and report pass/fail — it must not edit tests or application code.

If the writer reported in Step 2 that it wrote no tests at all (e.g. the
spec was missing or fully ambiguous), skip this step and tell the user why
instead of invoking the runner on a nonexistent file.

## Step 4 — Report to the user

Combine both subagents' reports into one summary:

```
Spec:        .claude/specs/<step_number>-<feature_slug>.md
Tests file:  tests/test_<feature_slug>.py
Writer:      <files created/updated, any ambiguities noted>
Test run:    <N passed, M failed, K errors>
Failures:    <for each: test name, one-line cause, spec item it maps to>
```

If there were failures, remind the user these are spec-vs-implementation
mismatches to fix in the application code — this command does not fix them
itself.
