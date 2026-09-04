import json
import re
import sys

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

# Matches `rm` as a shell command token: at the start of the command, or after
# a separator (;, &, |, newline, `(`, `$(`), optionally preceded by `sudo`.
PATTERN = r'(?:^|[;&|\n(]|\$\()\s*(?:sudo\s+)?rm(?:\s|$)'

if re.search(PATTERN, command):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked by project hook: `rm` is not allowed in this project's "
                "Bash tool calls. See .claude/settings.json / .claude/hooks/block_rm.py."
            ),
        }
    }))
else:
    print("{}")
