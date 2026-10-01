---
name: deslop
description: Remove AI-generated code slop and clean up code style. Use when the user says deslop, /deslop, or asks to clean AI slop from the branch diff.
license: MIT
disable-model-invocation: true
metadata:
  author: Cursor - github.com/cursor/plugins (cursor-team-kit/deslop)
---

# Remove AI code slop

Check the diff against main and remove AI-generated slop introduced in the branch.

## Focus Areas

- Extra comments that are unnecessary or inconsistent with local style
- Defensive checks or try/catch blocks that are abnormal for trusted code paths
- Casts to `any` used only to bypass type issues
- Deeply nested code that should be simplified with early returns
- Other patterns inconsistent with the file and surrounding codebase

## Guardrails

- Keep behavior unchanged unless fixing a clear bug.
- Prefer minimal, focused edits over broad rewrites.
- Keep the final summary concise (1-3 sentences).
