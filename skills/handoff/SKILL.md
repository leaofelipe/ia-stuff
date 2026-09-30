---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
license: MIT
disable-model-invocation: true
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to `.notebook/handoff/dd-mm-yy-theme.md`. Ask for the `theme` if it is not obvious; use today's date for `dd-mm-yy`. Create `.notebook/handoff/` if needed. If the file already exists, ask before overwriting. Report the absolute path when done.

Include a "decisions" section listing every settled decision from the conversation (for example, the outcome of a clarify session) as a short list, not a transcript. Keep it complete even when the next session focuses on something narrower.

Include a "suggested skills" section in the document, which suggests skills that the agent should invoke.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
