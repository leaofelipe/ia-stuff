---
name: clarify
description: Clarify a plan, decision, or idea through a relentless interview until shared understanding. Use when the user wants to get clear on a topic, stress-test their thinking, or uses any 'clarify' trigger phrases.
license: MIT
disable-model-invocation: true
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled — the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round, then wait for the user's answers before the next round.

## Language

Write everything in PT-BR. Use English only when the user's entire prompt is in English. Keep the `[Question N]` label literally as written in both languages; translate everything else, including the recommendation markers.

## How to ask

Always print the questions as ordinary chat text. Never use a native question tool, popup, or any other structured-question UI, and never put the questions inside a markdown code fence.

Every frontier question is a multiple-choice decision with concrete options. Never bury options in a paragraph or an inline list (`A, B, or C`).

Format each question like this, numbering questions sequentially across the whole session (not per round):

**[Question 1] (recomendada)**: <question body, with the context needed to decide>

**a)** <option> (Recomendada)

**b)** <option>

**c)** <option>

---

**[Question 2] (recomendada)**: <question body>

**a)** <option> (Recomendada)

**b)** <option>

Rules for the format:

- Separate consecutive questions in a round with a horizontal rule (`---`) on its own line, with a blank line before and after it.
- Bold the `[Question N]` label together with its `(recomendada)` marker. In English use `(recommended)` in the label and `(Recommended)` on the option.
- Put the recommended option first, as `a)`, with the recommendation marker at the end of its line.
- Put a blank line after the question and a blank line between every option, otherwise markdown collapses them onto one line.
- Word each question so that picking the recommended option is a plain "yes".
- Use backticks for code, identifiers, and file names inside questions and options.
- No emojis, no bullets, no numbered lists, no separate "recommended" line.
- The user may always answer with something that is not among the options; accept it and fold it into the tree.

Print the whole frontier in one message, one question after another. Do not ask a question whose answer depends on another question still open in this round: it belongs to a _later_ round.

## Working the tree

Each round the user answers reshapes the tree — settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it — don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report — ask the rest of the frontier now. The _decisions_ are the user's — put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
