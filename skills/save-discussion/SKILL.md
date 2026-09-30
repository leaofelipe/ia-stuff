---
name: save-discussion
description: Persist the settled decisions from a completed clarify session as a discussion note.
disable-model-invocation: true
---

Save the clarify outcome to `.notebook/discussions/dd-mm-yy-tema-da-discussao.md`.

- Only settled decisions for **this discussion**.
- A short decision list, not a transcript of the interview.
- Ask for the `tema` if it is not obvious; use today's date for `dd-mm-yy`.
- If the file already exists, ask before overwriting.
- Report the absolute path when done.
