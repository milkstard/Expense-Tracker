---
description: Generate a concise commit message and commit all intended Git changes.
allowed-tools: Bash(git commands)
---

Review the current Git repository status before making any changes.

Follow these rules:

1. Check the Git working tree status.
   - Identify all modified, deleted, renamed, and untracked files.
   - Distinguish tracked changes from untracked files.

2. Check for merge conflicts.
   - If there are any unmerged paths or merge conflicts, stop immediately.
   - Tell the user which files have conflicts and ask them to resolve the conflicts manually before continuing.
   - Do not stage or commit anything.

3. Handle untracked files.
   - If untracked files exist, list their paths and ask the user for confirmation before including them in the commit.
   - Do not automatically stage untracked files without confirmation.
   - If the user declines, exclude the untracked files from the commit.

4. Stage changes.
   - Stage all tracked changes intended for the commit.
   - Stage only the untracked files explicitly approved by the user.
   - Do not stage files that were not approved.

5. Verify the staged changes.
   - Review the staged diff to understand what will be committed.
   - If there are no staged changes, stop and inform the user that there is nothing to commit.

6. Generate a commit message.
   - Base the message on the actual staged changes.
   - Keep it concise and descriptive.
   - Do not include unnecessary details.
   - Prefer a conventional commit format such as:
     `type: short description`
   - Do not invent changes that are not present in the staged diff.

7. Commit the staged changes using the generated commit message.

8. After a successful commit, print:
   - The commit message
   - The commit hash
   - A brief confirmation that the commit was successful.

9. If the commit fails:
   - Do not claim that the commit was successful.
   - Show the error and explain that the commit was not completed.