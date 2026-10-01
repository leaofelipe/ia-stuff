---
name: simplify
description: Simplify the scoped code by using parallel read-only review agents for code quality, performance, and reuse, then make targeted cleanup fixes. Use when the user says simplify, /simplify, or asks to simplify or clean up the current changes.
argument-hint: "[paths, symbols, diff, or area]"
disable-model-invocation: true
metadata:
  source: Adapted from Cursor's built-in /simplify command
---

Simplify the scoped code by using parallel read-only review agents, then make targeted cleanup fixes yourself.

## Scope Selection

1. If the user provided an explicit scope after `/simplify` (paths, symbols, a diff, or a natural-language area), use that scope.
2. Otherwise, inspect local changes with both unstaged and staged diffs so staged work is not missed:
```bash
git diff --no-color
git diff --cached --no-color
```
Treat the combined non-empty output as the scope.
3. If there is no local diff, fall back to concrete files, symbols, or changes mentioned in the conversation.
4. If that also does not exist, fall back to the current HEAD commit using `git show --stat --patch --no-color HEAD`.
5. Preserve unrelated user changes. Do not broaden the scope beyond the selected diff or mentioned files unless needed to understand existing patterns.

## Subagents

Launch the following three subagents in parallel. They must only report findings, use the same model as the parent agent, and must not edit files, run formatters, create worktrees, or commit. Pass the full combined diff when possible; if it is too large, pass the file list, relevant hunks, and scope summary.

If subagents are not available, review the scope against all three angles yourself, one at a time, before fixing anything.

1. Code quality reviewer: look for simplification opportunities, including but not limited to:
- low-information comments: comments that restate the code instead of explaining intent, edge cases, or invariants.
- one-off helpers: small helpers that are only used once and can be inlined to make the flow clearer.
- nullable value proliferation: unnecessary null or undefined states that force defensive checks and make invariants unclear.
- catch-all try/catch blocks: broad error handling that swallows errors without explaining which exceptions are expected.
- unnecessary abstraction: generic wrappers, config objects, or interfaces introduced before there is real reuse.
- weak type escape hatches: avoidable any, casts, non-null assertions, or overly broad types that hide real invariants.
- duplicated state or derived state: storing values that can be computed from source state, creating stale-state risk.
- dead or compatibility code: unused branches, parameters, fallback paths, or old behavior preserved without evidence.

2. Performance reviewer: look for performance issues, including but not limited to:
- blocking operations in hot paths: sync Node.js functions or other blocking work that can stall the event loop.
- uncached expensive operations: repeated computation, parsing, or lookups whose results could be reused safely.
- busy waits: polling or loops that consume CPU while waiting instead of using events, timers, or backoff.
- string concatenation in loops: repeated immutable string allocation that can become quadratic or allocation-heavy.
- N+1 I/O: per-item database, filesystem, network, or RPC calls where batching would reduce latency or load.
- chatty logging/telemetry: high-volume logs or metrics emitted inside tight loops or hot paths.

3. Reuse reviewer: look for existing patterns or helpers that can be reused, either elsewhere in the codebase or already present in the diff.

## Fixing

Aggregate the findings from all subagents. Make targeted fixes that reduce complexity or reuse existing patterns while preserving behavior. Skip issues that need additional user context or require a much larger refactor than the original diff, and include those skipped recommendations in the final summary.

After editing, run the most relevant lightweight checks for the touched files when practical. If checks are skipped or unavailable, say so. Finish by summarizing what you fixed and what you skipped but recommend.
