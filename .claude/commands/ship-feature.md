---
description: Ship the current feature branch: commit, push, open a PR, squash-merge it, and sync main.
allowed-tools: Bash(git:*), mcp__github__create_pull_request, mcp__github__merge_pull_request, mcp__github__list_branches
---

You are shipping the current feature branch in the Spendly / Expense-Tracker
repo (`milkstard/Expense-Tracker`) end to end: commit, push, open a PR,
squash-merge it, and sync `main` locally. Follow these steps in order and
stop immediately on any failure rather than guessing or working around it.

## Step 1 — Identify the current branch
Run `git branch --show-current` and store it as CURRENT_BRANCH.
If CURRENT_BRANCH is `main` (or `master`), stop immediately and tell the
user to switch to a feature branch first — do not ship main into itself.

## Step 2 — Check the working tree
Run `git status`.
- If there are unmerged paths / merge conflicts, stop and tell the user
  which files have conflicts and ask them to resolve them manually. Do not
  stage or commit anything.
- If there are untracked files, list their paths and ask the user for
  confirmation before including them in the commit. If they decline,
  exclude those files.
- If there is nothing to commit AND CURRENT_BRANCH has no commits ahead of
  `origin/main` (check with `git log origin/main..HEAD --oneline`, treating
  a missing `origin/main` ref as "no commits ahead" too), stop and tell the
  user there is nothing to ship.

## Step 3 — Commit
If Step 2 found tracked changes and/or approved untracked files:
- Stage them (tracked changes, plus only the approved untracked files).
- Review the staged diff to understand what will be committed.
- Generate a concise, conventional commit message (`type: short
  description`) based on the actual staged diff — do not invent changes
  that aren't present in the diff.
- Commit with that message.

If Step 2 found nothing to stage but the branch already has unpushed
commits, skip committing and go straight to Step 4.

## Step 4 — Push
Run `git push -u origin <CURRENT_BRANCH>`.
If this fails, stop, show the error, and do not attempt to open a PR.

## Step 5 — Create the PR
Call `mcp__github__create_pull_request` with:
- `owner`: `milkstard`, `repo`: `Expense-Tracker`
- `head`: CURRENT_BRANCH, `base`: `main`
- `title`: derived from the commit message(s) on the branch
  (see `git log main..HEAD --oneline`)
- `body`: a short bullet summary of the changes on the branch

Store the returned PR number as PR_NUMBER and its URL as PR_URL.

## Step 6 — Merge the PR
Call `mcp__github__merge_pull_request` with `owner: milkstard`,
`repo: Expense-Tracker`, `pullNumber: PR_NUMBER`, and
`merge_method: "squash"`.

If the merge fails (conflicts, required checks, branch protection, etc.),
stop, show the error, and do not touch any local branches.

## Step 7 — Verify remote branch cleanup
Call `mcp__github__list_branches` for `milkstard/Expense-Tracker` and check
whether CURRENT_BRANCH still exists remotely.
- If it's gone, continue silently — the repo's "Automatically delete head
  branches" setting handled it.
- If it still exists, warn the user that this repo setting doesn't appear
  to be enabled, and that they can delete the branch manually
  (`git push origin --delete <branch>` or via GitHub) — do not delete it
  yourself.

## Step 8 — Sync local main
Run:
```
git checkout main
git pull origin main
```

## Step 9 — Delete the local feature branch
Step 6 used a squash merge, so CURRENT_BRANCH's commits are not ancestors of
the new squash commit on `main` — a plain `git branch -d` will refuse with
"not fully merged". Use `git branch -D <CURRENT_BRANCH>` instead; this is
safe here only because Step 6 already confirmed the PR merged successfully.

## Step 10 — Print a final summary
Print exactly this shape, filled in:
```
Branch:   <CURRENT_BRANCH> (deleted locally; remote cleanup per Step 7)
Commit:   <commit message from Step 3, or "no new commit" if Step 3 was skipped>
PR:       #<PR_NUMBER> — <PR_URL> (squash-merged)
Main:     up to date with origin/main
```

## Rules
- Never commit directly to main
- Always use squash merge
- Always delete both remote and local branch after merge
- If GitHub MCP is not connected stop and say:
  "GitHub MCP is not connected. Run /mcp to check connection."
- If push fails due to no upstream, use git push -u origin CURRENT_BRANCH
- Never proceed to merge if PR creation fails