---
name: explain-pr
description: Teach a pull/merge request didactically in plain language, one item at a time, from foundation to connected pieces. Understanding beats jargon. Use when the user wants to understand what an MR/PR did — not to review it — or uses explain-pr, /explain-pr, walkthrough, or "explica esse PR".
argument-hint: "PR/MR URL or number"
license: MIT
disable-model-invocation: true
---

Explain a PR/MR as a teacher, not a reviewer. Aim at the middle: clear enough for a junior new to this repo, precise enough that a senior does not feel talked down to. Understanding beats jargon, but cute metaphors also fail — "recipe book", "the file the world downloads", and similar stories usually confuse more than they teach. Say what changed in plain sentences, then use the real names. The reader may be new to this code. Do not judge quality, suggest changes, or write a review.

Build a **teaching tree** and walk it in order: **base**, then each **concept**, then the **connections**. The **frontier** is the single next item whose prerequisites the user already confirmed. Teach that one item. Stop. Do not batch items. Do not advance until the user says this item is clear.

## Inputs

Accept a GitHub/GitLab URL or number, a pasted diff, or the current branch.

- GitHub: `gh pr view` + `gh pr diff`
- GitLab: `glab mr view` + `glab mr diff`
- Else: `git diff origin/main...HEAD` and the title/body if present

Read the surrounding code the diff touches. Facts are your job — do not ask the user to explain the codebase. If the source is missing, ask only for the URL or diff.

## How to teach

Study first, in silence. Then open with a short map of item titles only (`1. … 2. …`) and teach item 1 in the same turn.

Each item:

**[n/N] <kind> — <title>**

`<kind>` is Base, Concept, or Connection — translated to the user's language.

Write for a junior who already knows how to program but not this repo. Lead with one plain sentence of what changed, then the real file and function names. Do not invent a story around the change. An analogy is allowed only when it maps 1:1 to something a developer already does (import, config, build). If the analogy needs explaining, drop it.

Explain the neighborhood that changed: who owns the flow, what called what, what the MR intended. Do not explain what a variable, function, class, or git is.

When structure is the point, draw it (mermaid or ASCII): ownership, before/after flow, who calls whom. Quote the smallest snippet that makes the neighborhood visible. Never dump a file.

After the explanation, wait. Prefer `AskQuestion` with:

- I understood, continue (Recommended)
- I still don't understand, explain it differently
- I still don't understand, show me a more didactic diagram

Translate those labels to the user's language. Do not print them in chat when the popup is shown. If the tool is missing, ask the same three options as ordinary rendered text.

If they pick a different explanation, reteach **this** item from another angle, with less jargon. If they pick a more didactic diagram, redraw this item around a clearer diagram. Do not introduce the next item in either case.

If they ask questions about this item, answer them on this item only — do not open the next one mid-thread. When those questions are settled and the item is understood, **close that branch of the tree** (one short sentence that this **tema** is done) and teach the next item in the same turn. Do not leave a finished tema open for more exploration. Call it a tema, not a piece.

When they confirm with no leftover questions, recompute the frontier and teach the next item.

## Sequence

1. **Base** — what this area of the system already was, why the MR exists, the objective. One item, or two if context and objective cannot share a breath.
2. **Concepts** — one item per real piece (a module, a contract, a new path). Isolation first. Order by dependency: a piece another hangs off comes first.
3. **Connections** — how the confirmed pieces wire together. Name the earlier items. End with one walkthrough of a request through the new path.

Skip an empty layer. Do not invent pieces the diff does not contain.

Language matches the user's request. Write nothing to disk. When the frontier is empty, close with a short restatement of the MR intention — still not a review.
