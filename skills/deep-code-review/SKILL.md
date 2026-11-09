---
name: deep-code-review
description: Evidence-first code reviewer that reviews a branch, GitHub pull request, or GitLab merge request locally and returns the review in the chat, and posts it as one consolidated review with inline comments (gh on GitHub, glab on GitLab) only when asked. Runs the repo's own deterministic checks first, researches current official docs before any claim about external libraries or APIs, then reviews correctness, security, structural quality (code judo, spaghetti growth, file-size limits), and AI slop including useless code comments. Every finding must carry evidence, every comment passes a deterministic noise gate before posting, and the verdict (APPROVE, COMMENT, REQUEST_CHANGES) is weighed by findings. Use when the user says "deep-code-review", "deep code review", "code review profundo", or "revisão profunda do PR". Do NOT use for reviewing prose or documents, fixing CI failures, resolving merge conflicts, writing the fix itself, or responding to review comments (use gh-address-comments).
license: CC-BY-4.0
disable-model-invocation: true
metadata:
  author: Felipe Rodrigues - github.com/felipfr
  version: 1.4.0
---

# Deep Code Review

Review a branch or pull request like a senior engineer with a high conviction bar: few comments, every one backed by evidence, delivered as a single consolidated review. The reviewer would rather post three findings that matter than fifteen observations that waste the author's time.

## Non-Negotiables

These rules override everything else in this skill. Read them before doing anything.

1. **Evidence or silence.** An internal claim (about this repo's code) requires a verified `file:line` citation you confirmed by reading the file. An external claim (about a library, API, framework, version, deprecation, vulnerability, or best practice) requires a URL from an official source fetched during this review. A finding without evidence is not posted. Period.
2. **Never assert external behavior from memory.** Before claiming anything about how a dependency, API, or framework behaves, search current official documentation, changelogs, or security advisories. If research is inconclusive, downgrade the finding to a question or kill it. Training data is a rumor; the changelog is a source.
3. **Noise budget.** Maximum 5 nit comments inline; overflow becomes a count in the summary. Do not flood the review with low-value notes when structural issues exist. Prefer a small number of high-conviction comments.
4. **Never comment on what the repo's own tooling catches.** Run the repo's linters, type checkers, and focused tests first (Step 1). Anything they flag is out of scope for review comments.
5. **Every comment passes the gate.** All comment bodies and the summary must pass `scripts/review_gate.py` with exit code 0 before posting. No exceptions, no manual overrides.
6. **Language: the user chooses; English is the default.** If the invocation names a language ("deep code review in Portuguese", "code review profundo em português"), write the entire review in it, natively and correctly, with full diacritics; never plain-ASCII degraded text. Absent an explicit request, write in English. Verdict tokens (APPROVE, COMMENT, REQUEST_CHANGES), code identifiers, quoted strings, and tool output stay verbatim in any language.
7. **Spend tokens where judgment lives.** Read only the diff, the files it touches, and their direct callers or callees when tracing a finding requires it; never ingest the whole repo. Detection a regex can do runs in `scripts/scan_bypasses.py`, not in prose. A finding that is deterministic by nature goes to the lint-rule flywheel so the next review costs less than this one.
8. **The first review is the whole review.** Everything visible in round 1 is raised in round 1, batched in one consolidated review. Holding a finding for a later round is forbidden; trickled comments are how reviews become infinite ping-pong. Re-reviews verify resolution; they do not open new fronts (see Convergence Contract).

## Severity and Verdict

| Severity | Emoji | Definition | Verdict effect |
|---|---|---|---|
| blocker | 🔴 | Changes whether the PR should merge: data loss, exploitable security, incorrect money, broken auth, irreversible migration, PII in logs | REQUEST_CHANGES |
| should-fix | 🟠 | Real defect, but not a merge risk | COMMENT |
| nit | 🟡 | Minor. Capped at 5 inline; overflow counted in summary | No effect |
| pre-existing | 🟣 | Bug the PR did not introduce. Summary only, never inline | No effect |

Verdict mapping: any 🔴 present, REQUEST_CHANGES. Zero 🔴 and zero 🟠, APPROVE. Anything else, COMMENT.

**Own-PR fallback:** GitHub returns 422 when you APPROVE or REQUEST_CHANGES your own PR, and GitLab may forbid authors from approving their own MR. Both posting scripts detect when the author equals the authenticated user, post as COMMENT, and append a one-line footer at the end of the summary stating the intended verdict. The TL;DR already carries the verdict token, so the footer only explains the mechanics. Do not fight this; it is API behavior.

## Modes

| | Local (default) | PR (GitHub) | MR (GitLab) |
|---|---|---|---|
| When | Any invocation that does not ask to post | The user asks to post to the PR | The user asks to post to the MR |
| Diff source | `git diff <merge-base>`: committed and uncommitted tracked changes | `gh pr diff <number>` | `glab mr diff <iid> --raw` |
| Pass E | Skipped; note "Pass E skipped (local mode)" in the summary | Runs on the PR description | Runs on the MR description |
| Output | The review in the chat | One GitHub review via `scripts/post_review.py` | Draft notes published at once via `scripts/post_review_gitlab.py` |
| Ledger | `.notebook/reviews/<id>/round-<N>.json` | Previous reviews on the PR, plus the ledger file | Previous summary notes on the MR, plus the ledger file |

A request to post that names neither host ("publish this review") goes to the host of `git remote get-url origin`: `github.com` is PR mode, any GitLab host is MR mode. Ask only when the remote is neither.

`<id>` is always the branch name with `/` replaced by `-`: `git rev-parse --abbrev-ref HEAD` in local mode, the PR's `headRefName` or the MR's `source_branch` in PR and MR modes, where CI checkouts are often a detached `HEAD`. It never depends on whether `gh` or `glab` answers, so every round of a branch lands in the same directory before and after the PR or MR exists. `.notebook/` lives at the root of the reviewed repo. Local mode never writes to the forge; `gh` or `glab` is only used read-only to learn whether a PR or MR is open, and its absence is not an error.

Archiving the ledger means renaming `.notebook/reviews/<id>/` to `.notebook/reviews/<id>-<first 7 characters of its latest head>/`, so old rounds are kept and the next round 1 starts in an empty directory.

In PR and MR modes the forge is the source of truth for rounds, because the ledger file does not survive ephemeral runners such as CI jobs. Still write the ledger file; it costs nothing locally. A local round that never reached the forge is not a previous round there: the author never saw it, so archive the ledger and run the PR or MR review as round 1. To deliver the local round itself, publish it instead.

Publishing a local review is a separate request: "post this review" runs the posting script of the detected host on `.notebook/reviews/<id>/round-<N>.json`, the round already shown, without re-reviewing. Post it only when the round has `"dirty": false` and its `head` equals the forge head (`gh pr view --json headRefOid --jq .headRefOid`, or the MR's `sha`). Otherwise the round describes code the forge does not have: say so and run the review again in PR or MR mode. `post_review_gitlab.py` enforces both conditions; on GitHub, check them before calling `post_review.py`. Pass E did not run in local mode, so offer to run it against the PR or MR description before posting.

## Workflow

### Step 0: Resolve context

Local mode:

```bash
git rev-parse --abbrev-ref HEAD
git symbolic-ref --short refs/remotes/origin/HEAD
git merge-base HEAD <base>
git diff <merge-base>
git diff <merge-base> --name-only
git status --short
gh pr view --json number --jq .number        # GitHub remote
glab mr view --output json                   # GitLab remote, read iid
```

`<base>` is the branch the user names, otherwise the remote default branch. Untracked files are not in the diff; list them from `git status` and read the ones that belong to the change.

PR mode:

```bash
gh pr view --json number,title,body,author,url,baseRefName,headRefName,additions,deletions,changedFiles
gh api user --jq .login
gh pr diff <number>
gh pr view <number> --json files --jq '.files[].path'
```

MR mode:

```bash
glab mr view --output json                   # iid, title, description, author.username
glab api projects/:id/merge_requests/<iid>   # diff_refs, sha, web_url
glab api user                                # username
glab mr diff <iid> --raw
```

Classify every changed file as **core** or **mechanical** (generated code, lockfiles, snapshots, vendored deps, build artifacts, migrations output). Mechanical files are skipped and listed in the summary. Detect moved code: 3+ consecutive lines deleted in one place and added identically elsewhere is a move, not new code; do not re-review it as new.

Determine the round. In local mode, the latest `.notebook/reviews/<id>/round-<N>.json` is the previous review, provided its `head` is in the current history (`git merge-base --is-ancestor <head> HEAD`). If it is not, the branch was rebased or its name was reused for new work: say so and ask whether to continue as round N or archive the ledger and start at round 1. Never decide alone; a rebase keeps the review going, a reused name does not. In PR mode, fetch your own previous reviews on this PR:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews --jq '[.[] | select(.user.login=="<gh-login>" and (.body | test("tl;dr"; "i")) and (.body | test("lint[ -]?rule"; "i"))) | {id, submitted_at, commit_id, body}]'
```

The body filter keeps only reviews carrying the TL;DR and lint-rule sections the gate requires, so manual reviews by the same user do not count as rounds. The round number is the count of matching reviews plus one.

In MR mode, fetch the MR notes and keep those authored by your username that contain the `<!-- deep-code-review head=<sha> round=<N> -->` marker `post_review_gitlab.py` appends to every summary:

```bash
glab api "projects/:id/merge_requests/<iid>/notes?sort=asc&per_page=100" --paginate
```

No previous review: this is round 1, run the full workflow. Previous review exists: this is round N, load the findings ledger (the ID table) from the latest previous summary and follow the Convergence Contract instead of a full re-run. The diff since the last reviewed commit is `git diff <head>`, where `<head>` is the previous round's `head` field, the review's `commit_id` in PR mode, or the marker's `head` in MR mode.

If the diff exceeds roughly 400 changed lines in core files and the harness supports subagents, run the Step 3 passes as parallel subagents. Otherwise run them sequentially. Never make subagent support a requirement.

### Step 1: Deterministic ladder

Detect and run the repo's own checks: lint, typecheck, and tests focused on changed files (look at `package.json` scripts, `Makefile`, `pyproject.toml`, CI config). If the repo already runs security scanners (dependency, IaC, or SAST tools wired into its CI), run them or read their current output as deterministic input too. Record results. Findings these tools produce are excluded from your review scope; you judge only what they cannot. If the repo has no such tooling, note that in the summary and move on; do not install anything.

Then run the deterministic bypass scan:

```bash
git diff <merge-base> | python3 scripts/scan_bypasses.py   # local mode
gh pr diff <number> | python3 scripts/scan_bypasses.py     # PR mode
glab mr diff <iid> --raw | python3 scripts/scan_bypasses.py   # MR mode
```

It prints `path:line  category  content` for every bypass marker added by the diff (suppression directives, dodged tests, TLS and type-check bypasses, swallowed errors, sleep-as-synchronization). Scan hits are candidates for Pass F, not findings: a suppression carrying a justification and an issue link is acceptable; a naked one is not. The scan exists so zero LLM tokens are spent detecting what a regex detects.

### Step 2: Mandatory research

Enumerate every external surface the diff touches: dependencies added or version-bumped (read the manifest/lockfile diff), APIs called, framework features used, language features that are version-sensitive. For each surface, search current official documentation, release notes, and security advisories. Log every consulted URL; the summary includes a research log. This step is not optional and not skippable, even when you feel confident. Confidence from memory is exactly the failure mode this step exists to kill. If the diff touches zero external surfaces, state that in the research log.

### Step 3: Review passes

**Completeness contract:** round 1 covers all core files across all passes, in depth, in one shot. Nothing is deferred to "a later look". A finding you could have raised now and raise later is a broken contract with the author. One exception to volume: do not stack comments on code a structural finding will rewrite; if a 🔴 or 🟠 asks for a block to be restructured, withhold nits inside that block and note "nits withheld on lines the structural fix rewrites" in the summary.

**Read `references/review-standards.md` now.** Run six passes over core files:

- **Pass A. Correctness and logic**: broken invariants, unhandled failure paths that lose data, partial state, concrete concurrency hazards.
- **Pass B. Security**: high-confidence exploitability only, newly introduced by this PR, with the hard exclusion and precedent lists applied.
- **Pass C. Structure and maintainability**: the ambitious structural pass. Code judo, file-size limits, spaghetti growth, boundaries, canonical layer.
- **Pass D. AI slop and useless code comments**: comments that restate code, changelog comments, docstring bloat, commented-out code, defensive try/catch on trusted paths, speculative abstractions.
- **Pass E. PR description claims** (PR and MR modes only): every claim of "fixes X" or "improves Y" needs evidence (test, repro, measurement) or becomes a question.
- **Pass F. Bypasses, duplication, and gambiarras**: suppression directives, dodged tests, type and TLS bypasses, copy-paste duplication, magic values, sleep-as-synchronization, unlabeled workarounds. Seeded by the Step 1 bypass scan; every scan hit gets judged here.

Each pass produces candidate findings: claim, tentative severity, evidence pointer. If the harness supports choosing a model per subagent, use light, fast variants for mechanical work (file classification, dedupe, scan triage) and reserve the strongest model for the judgment passes and verification; burning the heavy model on cheap triage is waste, and burning the light model on judgment is false positives.

### Step 4: Verification pass

For each candidate: re-read the actual code at the cited location and confirm the claim holds. Re-apply the exclusion lists. Kill anything you cannot evidence. Deduplicate across passes. Assign final severity conservatively: a blocker you are not certain of is a should-fix phrased as a question. This pass exists because candidate generation is optimized for recall and posting is optimized for precision.

Two grounding rules:

- **Reproduce when feasible.** A 🔴 from Pass A or Pass B that can be demonstrated locally gets the strongest evidence class there is: a failing test or a short script run inside the repo's own test harness (never network attacks, never outside the sandbox of the checkout). Record the command and its output as `repro` evidence. The inverse binds too: when a reproduction was feasible and failed to reproduce the claim, the finding dies, whatever your reading of the code said.
- **Low risk is not false positive.** Severity and validity are orthogonal axes. A real but minor issue is a 🟡, not a discard; killing findings because they are small is how a filter quietly stops detecting real problems. Kill for lack of evidence, downgrade for lack of impact, never conflate the two.

### Step 5: Write comments

**Read `references/comment-voice.md` now.** Write the summary and every comment body under that spec. Produce `.notebook/reviews/<id>/round-<N>.json`, called `findings.json` below:

```json
{
  "language": "en",
  "round": 1,
  "head": "<commit the round reviewed>",
  "dirty": false,
  "carryover": {"blocker": 0, "should-fix": 0},
  "verdict": "REQUEST_CHANGES",
  "summary": "## TL;DR\n...\n## Findings\n...\n## Promote to lint rule\n...\n## Research log\n...\n## Checks run\n...\n## Skipped files\n...",
  "findings": [
    {
      "id": "F1",
      "path": "src/billing/invoice.ts",
      "line": 142,
      "severity": "blocker",
      "body": "🔴 `applyDiscount` divides by `items.length` with no empty-list guard (src/billing/invoice.ts:142)...",
      "evidence": [
        {"type": "internal", "ref": "src/billing/invoice.ts:142"},
        {"type": "external", "ref": "https://official-docs.example/api#behavior"}
      ]
    }
  ]
}
```

`round` defaults to 1. `head` is the commit the round reviewed: `git rev-parse HEAD` in local mode, the PR's `headRefOid` in PR mode, the MR's `sha` in MR mode; the next round diffs from it. `dirty` is true when a local round included uncommitted changes or untracked files from `git status --short`; that code exists only in the working tree, so the round cannot be posted. `carryover` counts previous-round findings still unresolved (zeros in round 1); the gate uses it to compute the correct verdict when the new-findings list alone would understate open risk. `id` values are stable across rounds (F1 stays F1 forever) so the resolution ledger maps cleanly. Evidence entries accept three types: `internal` (verified `path:line`), `external` (https URL from an official source fetched this review), and `repro` (the local command that demonstrates the claim, with its observed result in the finding body).

Rules the gate enforces (write to them from the start): body starts with the severity emoji; blocker and should-fix require at least one evidence entry; external evidence must be an https URL; pre-existing findings have no `line`; the summary contains a TL;DR section and a lint-rule section.

### Step 6: Gate

```bash
python3 scripts/review_gate.py findings.json
```

Fix every reported violation and re-run until exit code 0. The gate is deterministic; arguing with it is arguing with a regex.

### Step 7: Deliver

Local mode: show the review in the chat. Print the summary as written, then each inline finding under a `path:line` heading with its body verbatim. The text in the chat is the gated text; do not rephrase it. End with the ledger path and one line saying the round can be posted to the PR or MR on request, or, when `dirty` is true, that the changes must be committed, pushed, and reviewed again before anything can be posted.

PR mode:

```bash
python3 scripts/post_review.py findings.json
```

Posts everything as one review (single API call: summary body, verdict event, positioned inline comments), handles the own-PR fallback, prints the review URL. Inline comments only anchor on lines present in the diff; the script tells you which comment failed if GitHub rejects an anchor.

MR mode:

```bash
python3 scripts/post_review_gitlab.py findings.json
```

GitLab has no single-call review, so the script builds one: each inline finding becomes a draft note positioned with the MR's `diff_refs`, then `draft_notes/bulk_publish` publishes all of them at once with the summary as the review note. The verdict maps to `reviewer_state` (`requested_changes` for REQUEST_CHANGES, `reviewed` otherwise); APPROVE also calls `/approve` pinned to the round's `head`. GitLab has no "request changes" without `reviewer_state`, so when the instance rejects it the script publishes without it and the verdict lives in the TL;DR. If any draft fails to anchor, the script deletes the drafts it created and stops, so nothing partial reaches the MR. It refuses to run when you already have pending drafts on the MR, because `bulk_publish` would publish them too, and when the round is `dirty` or its `head` differs from the MR head.

## Summary Body Template

```markdown
## TL;DR
One to three sentences: what the PR does and the verdict with its reason. Must contain the verdict token (APPROVE, COMMENT, or REQUEST_CHANGES) verbatim; the gate checks for it.

## Findings
| ID | Severity | Location | Summary |
|---|---|---|---|

## Resolution (round 2+)
| ID | Status | Note |
|---|---|---|
Every previous finding appears here with status resolved (with the commit), open, or declined-accepted (author's reason held). Omit this section in round 1.

## Promote to lint rule
Findings in this review that are deterministic by nature (banned pattern, naming convention, style rule). For each: the rule, and a one-line sketch of how to lint it. Reviews should get cheaper every cycle; this section is the flywheel. Write "none" if empty.

## Research log
URLs consulted in Step 2, one per line, with the claim each one supports or refutes. Sources that refuted a candidate finding belong here too: a documented non-finding is evidence of diligence and saves a future round. Write "no external surfaces touched" if that is the case.

## Checks run
Deterministic ladder results from Step 1, verbatim numbers with no interpretation: test counts (passed/failed/skipped), linter and typechecker outcome, bypass scan candidate count.

## Skipped files
Mechanical/generated files excluded from review.

## Nit overflow
"N additional nits not posted individually" when the cap was hit. Omit otherwise.
```

## Convergence Contract

The reviewer is decisive: it converges reviews instead of stretching them. Round 1 is exhaustive; every later round shrinks. The failure mode this contract kills is the infinite ping-pong where each round discovers a new front.

**Round N (N >= 2) scope is exactly two things:**

1. **Resolution check.** For every finding in the previous ledger, verify against the new commits: resolved (cite the fixing commit), still open, or declined by the author. Report all of them in the Resolution table. This is the focus of the re-review; it is a checklist verification, not a fresh hunt.
2. **New blockers only.** The diff since the last reviewed commit is examined solely for 🔴 introduced by the fix itself. No new 🟠, no new 🟡, no new 🟣, ever. Code that was visible in round 1 and not flagged then is forfeited: the reviewer eats the miss. The single exception is a genuine 🔴 (exploitable security, data loss, money) discovered late, which is always raised, labeled factually as missed in round 1.

**Declined findings.** When the author declines with a reason, first consider that they are closer to the code and may be right; if the reasoning holds from a code-health perspective, record declined-accepted and drop it permanently. If it does not hold, re-argue once with new evidence, at most once. Still unresolved after that: mark it open, state that the disagreement moves out of the review thread, and stop re-raising. Comment threads do not resolve philosophy.

**Round cap.** By round 3, every remaining open finding is either fixed, converted to a follow-up issue by agreement, or escalated out of the thread. The reviewer never runs a fourth round on the same finding set.

**Approval bar.** Approve as soon as the PR definitely improves overall code health, even if imperfect; perfect code does not exist, only better code. Unresolved 🟡 never blocks an APPROVE (approve with nits). Withholding approval to extract polish beyond the severity table is scope creep by the reviewer.

The gate enforces the mechanical half of this contract: with `"round": 2` or higher it rejects any non-blocker finding, requires the Resolution section, and requires `carryover` so the verdict reflects still-open previous findings.

## Examples

### Example 1: routine review

User says: "code review profundo nessa branch" (no PR yet, 180 changed lines, TypeScript).
Actions: local mode, `<id>` is the branch name. Steps 0-2 (research: one dep bump, checked its changelog), sequential passes with Pass E skipped, 1 should-fix + 2 nits survive verification, gate passes on second run (first run caught an exclamation mark), round 1 saved to `.notebook/reviews/feat-quality-menu/round-1.json`.
Result: the review in the chat with verdict COMMENT, three findings under their `path:line` headings, summary with research log citing the changelog URL. Nothing posted.

### Example 2: blocker found, posted

User says: "deep code review this PR and post it".
Actions: PR mode. Pass A finds an unguarded division in a money path with a traced failing input; verification confirms at `src/billing/invoice.ts:142`; verdict REQUEST_CHANGES; PR author equals gh user, so post_review posts as COMMENT with the TL;DR stating REQUEST_CHANGES and a footer explaining the fallback.
Result: review posted, blocker anchored inline with file:line evidence and the lazy fix (guard clause, three lines).

### Example 3: claims without evidence

User says: "deep code review and publish on the PR". PR description says "fixes the race condition in the worker pool". No test touches the pool.
Actions: Pass E flags the claim; no repro or test exists; the finding becomes a 🟠 question asking for a failing-then-passing test, not an assertion that the fix is wrong.
Result: comment asks for evidence instead of speculating.

### Example 4: round 2

User says: "code review profundo de novo" after pushing fixes.
Actions: Step 0 finds `round-1.json` in `.notebook/reviews/<id>/`; round 2, diffing from its `head`. Resolution check maps the ledger: F1 fixed in commit `a1b2c3d`, F2 declined with a reason that holds (recorded declined-accepted), F3 still open. Diff since last review scanned for new blockers only; none found. `findings` is empty, `carryover` is `{"blocker": 1, "should-fix": 0}` for F3, verdict REQUEST_CHANGES.
Result: a short review with only the Resolution table and TL;DR, saved as `round-2.json`. No new comments, no new fronts, convergence preserved.

### Example 5: publishing a local review

User says: "publica esse review no PR" after a local round 1.
Actions: the PR now exists; the ledger stays in the branch-name directory. The round has `"dirty": false` and its `head` equals the PR's `headRefOid`, so it can be posted as is. Offer to run Pass E against the PR description first; then `python3 scripts/post_review.py .notebook/reviews/<id>/round-1.json`, which re-runs the gate before posting.
Result: the exact review shown in the chat lands on the PR as one review with inline comments.

## Troubleshooting

### Error: HTTP 422 on review submission
Cause: APPROVE/REQUEST_CHANGES on your own PR, or a comment anchored to a line not in the diff.
Solution: `post_review.py` auto-falls back to COMMENT for own PRs. For anchor failures, move the comment to a changed line shown in the patch, or drop `line` and fold it into the summary.

### Error: HTTP 400 creating a draft note on GitLab
Cause: the finding's `line` is not part of the MR diff, so GitLab cannot position it.
Solution: `post_review_gitlab.py` already deleted the drafts it created. Move the comment to a changed line shown in `glab mr diff --raw`, or drop `line` and fold it into the summary.

### Error: pending draft notes on the MR
Cause: the authenticated user has unpublished drafts on the MR, and `bulk_publish` would publish them with the review.
Solution: report it and stop. The user decides whether to publish or delete those drafts; never delete drafts the script did not create.

### Error: round head differs from the PR or MR head
Cause: commits were pushed after the round, the round reviewed uncommitted changes (`"dirty": true`), or the local commits were never pushed.
Solution: do not post the round. Push if the commits are only local, then run the review again in PR or MR mode against the current head.

### Error: GitLab approval failed
Cause: the user is not an eligible approver, the project requires re-authentication to approve, or the MR head moved since the review (409).
Solution: the review is already published; report the approval error verbatim. On 409, re-run the review against the new head instead of approving stale code.

### Error: gh or glab not authenticated
Cause: no `gh auth login` or `glab auth login` session, or no `GITLAB_TOKEN` in a CI job.
Solution: in local mode, continue; the ledger does not need the forge. In PR or MR mode, ask the user to run `gh auth status` or `glab auth status` and authenticate. Do not attempt tokenless calls.

### Error: no PR or MR for the current branch
Cause: branch never pushed, or PR or MR not opened.
Solution: in local mode this is expected. In PR or MR mode, report it and stop. Opening PRs or MRs is out of scope for this skill (that is a different job).

### Gate keeps failing on the same body
Cause: rephrasing around a banned pattern instead of removing it.
Solution: delete the sentence containing the violation. The gate output names the exact pattern and location.
