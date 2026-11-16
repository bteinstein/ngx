#!/usr/bin/env python3
"""PreToolUse hook (Bash): block commits and PR create/edit commands that carry Claude attribution.

The owner's rule (CLAUDE.md): no Co-Authored-By: Claude, Claude-Session:, or
"Generated with/by Claude Code" lines in commits or PRs. Exit 2 blocks the call and
shows the reason to Claude.
"""
import json
import re
import sys

try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "") or ""
except Exception:
    sys.exit(0)

writes_git = re.search(r"\bgit\b[^\n|;&]*\b(commit|tag)\b", cmd) or re.search(
    r"\bgh\s+pr\s+(create|edit)\b|api\.github\.com/repos/[^\s'\"]+/pulls|\bgh\s+api\b[^\n]*pulls", cmd)
bad = re.search(r"Co-Authored-By:\s*Claude|Claude-Session:|Generated (with|by) \[?Claude Code", cmd, re.I)
if writes_git and bad:
    print("Blocked: this repo forbids Claude attribution in commits and PRs (see CLAUDE.md > Rules). "
          f"Remove the line containing '{bad.group(0)}' and run the command again.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
