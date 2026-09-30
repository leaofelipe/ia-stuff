---
name: test-surgery
description: Remove redundant unit test code in a scoped area without dropping use cases or coverage, proven by a per-line coverage diff before and after, and finish with a report of lines removed and coverage. Use when the user says test-surgery, /test-surgery, or asks to shrink, compact, or de-duplicate tests in a path, module, or branch diff.
argument-hint: "[test paths, module, or area]"
license: MIT
disable-model-invocation: true
---

# Test surgery

Cut redundant test code in the scope without losing any behavior, coverage, or failure diagnostics. Run end to end without asking for approval; stop only if the scope is unresolved or the baseline is red. Cutting little or nothing is a valid outcome.

## Scope

First match wins. Never widen to the whole codebase unless asked.

1. Paths or area passed as argument.
2. Test files or area discussed in the conversation.
3. Tests for files changed on the branch (`git diff --name-only $(git merge-base HEAD main)`), plus changed test files.
4. Otherwise, ask.

## Rules

- Never weaken an assertion; exact values stay exact. Tightening is fine.
- Every behavior pinned before stays pinned by a named test. Failing at suite load does not count.
- A surviving test fails at least as specifically as the one it replaces: it names the case and shows the actual value.
- Keep the file's structure: `describe` per unit, naming, order. Do not reorganize.
- Do not touch production code, test or coverage config files, thresholds, skips, or ignore pragmas. If config excludes the scope from coverage, override it with CLI flags, identical in both runs. Install a missing coverage tool without committing it.
- Change test-support helpers only if every caller is in scope.
- Keep bug regression tests unless another test reproduces the same bug.
- Skip cuts that save a few lines but cost readability, failure isolation, or diagnostics. No line target; stop when a pass finds little more.
- No commits unless asked.

## Cuts

- **Tables:** tests that differ only in input and expected output become one `it.each` / `test.each`. Never collapse an existing `.each` into a single test. If a table must live in one test, assert `expect(cases.map(([i]) => [i, fn(i)])).toEqual(cases)`.
- **Merge tests:** only for the same behavior on the same scenario, each checking a different field of one result. If the merged name needs "and" or a comma, keep them apart. Pure functions have no setup, so never merge them for "shared setup".
- **Builders:** repeated 30+ line literals become per-file `make*` builders with the old values as defaults. Expected values stay literal.
- **Delete:** tautologies, copy pins, tests of dead code, the same assertion duplicated across layers, reset boilerplate already done by global config, blanket console silencing.
- **Merge files:** only for the same unit with the same setup.

## Workflow

1. **Baseline.** Run the scoped tests with line and branch coverage, writing an Istanbul `coverage-final.json` or a coverage.py JSON with branch data into `<tmp>/before` under `mktemp -d`, never into the repo. Record test files, tests, cases (table rows plus standalone tests), test lines, covered lines and branches. List each pinned behavior (unit, scenario, expected) with its test names.
2. **Cut** file by file, rerunning those tests after each.
3. **Prove.** Rerun with the same command into `<tmp>/after`, then `python3 <skill-dir>/scripts/compare_coverage.py <tmp>/before <tmp>/after`. It prints the totals for the report and every line and branch covered before and not after; exit 1 means losses, exit 2 means a bad report or a changed source file. For other coverage formats, compare per-line and per-branch hits the same way; percentages are not proof. Restore an assertion for each, unless incidental (an unused `??` fallback, code with no production callers). Confirm every behavior maps to a surviving test.
4. **Report** in the chat, not a file. Write `none` under empty sections.

```markdown
# Test surgery: <scope>

| | Before | After | Δ |
| --- | --- | --- | --- |
| Test files | | | |
| Tests | | | |
| Cases | | | |
| Test lines | | | |
| Line coverage | <covered>/<total> (<%>) | | |
| Branch coverage | <covered>/<total> (<%>) | | |

Diff: +<added> / −<removed> lines, <n> files changed.

## Cuts
| Technique | Files | Net lines |
| --- | --- | --- |

## Judgment calls
- <cut>: <gain> vs <cost>. Revert if <condition>.

## Behavior map (only behaviors whose test changed)
| Behavior | Before (test names) | After (test name) |
| --- | --- | --- |

## Coverage lost and not restored
- <file:line or branch>: <why incidental>

## Residual risk
- <merged tests failing as a unit, shared builders, reliance on global mock config, stricter assertions>

## Found outside the scope
- <production bugs or dead code revealed, left untouched>
```
