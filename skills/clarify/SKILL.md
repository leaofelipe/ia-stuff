---
name: clarify
description: Clarify a plan, decision, or idea through a relentless interview until shared understanding. Use when the user wants to get clear on a topic, stress-test their thinking, or uses any 'clarify' trigger phrases.
disable-model-invocation: true
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled — the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round. Without a native question tool, work the frontier one question at a time instead (see below).

## How to ask

Every frontier question is a multiple-choice decision with concrete options. Never bury options in a paragraph or an inline list (`A, B, or C`).

**Prefer a native question tool** so the user gets a multiple-choice popup, not chat text. Look for any tool your environment exposes for asking the user structured multiple-choice questions, such as `AskQuestion` in Cursor or `AskUserQuestion` in Claude Code. Recognize it by what it does, not by its name. Then follow its schema:

- Cover the whole frontier in one round. If the tool caps questions per call, issue back-to-back calls in the same turn until the frontier is covered. If it caps options, keep the strongest ones.
- Put the recommended option first and append `(Recommended)` to its label.
- If the schema has a short label field (header, title), use a few words naming the decision, within its length limit.

Do not also print the questions in the chat when the popup is shown. If the tool already offers an Other/custom answer, do not add an Other option yourself.

**If no such tool is available**, ask the frontier one question at a time: one question per message, then wait for the answer before asking the next. After each answer, recompute the frontier before picking the next question, since that answer may settle or reshape others. Print the question as ordinary rendered chat text — never inside a markdown code fence. Bold `[Question N]` and the option letters (`a)`, `b)`, …), numbering questions sequentially across the whole session. Put a blank line after the question and a blank line between every option, otherwise markdown collapses them onto one line:

**[Question 1]**: <question>

**a)** <option> (Recommended)

**b)** <option>

**c)** <option>

Do not use bullets, numbered lists, a separate "recommended" line, or fenced code blocks.

Each round the user answers reshapes the tree — settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it — don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report — ask the rest of the frontier now. The _decisions_ are the user's — put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
