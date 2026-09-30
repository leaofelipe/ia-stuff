#!/usr/bin/env python3
"""
compare_coverage.py - per-line and per-branch coverage diff for test-surgery's proof step.

Aggregate percentages can stay flat while specific lines are lost, so this lists every line and
branch covered in the baseline and not covered after the cuts. Pure standard library.

Accepted inputs, detected from the JSON shape:
  - Istanbul `coverage-final.json` (Jest `--coverageReporters=json`, Vitest, nyc, c8)
  - coverage.py JSON (`coverage run --branch ...` then `coverage json -o <file>`)

BEFORE and AFTER are a JSON file or a directory holding `coverage-final.json` or `coverage.json`.
Paths are printed relative to --root (default: current directory). Test files and test-support
helpers are ignored (see DEFAULT_EXCLUDES; add more with --exclude). Totals skip files with no hits
in either run, since no test in the scope reaches them.

Statements and branches are matched by id, which is only stable while the source file is unchanged.
If a file's statement or branch map differs between runs, production code changed and the
comparison stops with exit 2.

Usage:
  python3 <skill-dir>/scripts/compare_coverage.py BEFORE AFTER [--root DIR] [--exclude GLOB ...]

Exit codes: 0 nothing lost, 1 coverage lost (listed), 2 usage, format, or source-changed error.
"""
import argparse
import fnmatch
import json
import os
import sys

CANDIDATE_NAMES = ("coverage-final.json", "coverage.json")
DEFAULT_EXCLUDES = (
    "*.test.*", "*.spec.*", "*/test_*.py", "*_test.py", "*/conftest.py",
    "*/tests/*", "*/test/*", "*/__tests__/*", "*/test-support/*",
)


class CoverageError(Exception):
    pass


def resolve_report(path):
    if os.path.isfile(path):
        return path
    for name in CANDIDATE_NAMES:
        candidate = os.path.join(path, name)
        if os.path.isfile(candidate):
            return candidate
    raise CoverageError(f"no {' or '.join(CANDIDATE_NAMES)} in {path}")


def relative(file, root):
    return os.path.relpath(os.path.abspath(file), root) if os.path.isabs(file) else file


def load_istanbul(data, root):
    files = {}
    for file, fc in data.items():
        lines = {}
        statements = {}
        for sid, loc in fc["statementMap"].items():
            line = loc["start"]["line"]
            lines[line] = max(lines.get(line, 0), fc["s"][sid])
            statements[sid] = (line, fc["s"][sid])
        branches = {}
        labels = {}
        for bid, branch in fc["branchMap"].items():
            start = branch["loc"]["start"]
            for arm, hits in enumerate(fc["b"][bid]):
                key = f"{bid}#{arm}"
                branches[key] = hits
                labels[key] = f"{start['line']}:{start['column']} {branch['type']} arm {arm}"
        shape = json.dumps([fc["statementMap"], fc["branchMap"]], sort_keys=True)
        files[relative(file, root)] = {
            "lines": lines, "statements": statements, "branches": branches, "labels": labels, "shape": shape,
        }
    return files


def load_coveragepy(data, root):
    if not data.get("meta", {}).get("branch_coverage"):
        raise CoverageError("coverage.py report has no branch data; run with `coverage run --branch`")
    files = {}
    for file, fc in data["files"].items():
        lines = {line: 1 for line in fc["executed_lines"]}
        lines.update({line: 0 for line in fc["missing_lines"]})
        branches = {f"{a}->{b}": 1 for a, b in fc["executed_branches"]}
        branches.update({f"{a}->{b}": 0 for a, b in fc["missing_branches"]})
        labels = {key: key for key in branches}
        statements = {line: (line, hits) for line, hits in lines.items()}
        shape = json.dumps(sorted(lines) + sorted(branches))
        files[relative(file, root)] = {
            "lines": lines, "statements": statements, "branches": branches, "labels": labels, "shape": shape,
        }
    return files


def is_excluded(file, globs):
    path = "/" + file.replace(os.sep, "/")
    return any(fnmatch.fnmatch(path, glob) for glob in globs)


def load(path, root, excludes):
    report = resolve_report(path)
    with open(report, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and "files" in data and "meta" in data:
        files = load_coveragepy(data, root)
    elif isinstance(data, dict) and data and all(isinstance(v, dict) and "statementMap" in v for v in data.values()):
        files = load_istanbul(data, root)
    else:
        raise CoverageError(f"{report} is neither Istanbul coverage-final.json nor coverage.py JSON")
    files = {file: fc for file, fc in files.items() if not is_excluded(file, excludes)}
    if not files:
        raise CoverageError(f"{report} has no source files after excluding tests; check the coverage scope")
    return files


def has_hits(fc):
    return any(n > 0 for n in fc["lines"].values())


def totals(files, counted):
    counts = {"lines": [0, 0], "branches": [0, 0]}
    for file, fc in files.items():
        if file not in counted:
            continue
        for kind in counts:
            hits = fc[kind].values()
            counts[kind][0] += sum(1 for n in hits if n > 0)
            counts[kind][1] += len(hits)
    return counts


def format_totals(counts):
    parts = []
    for kind, (covered, total) in counts.items():
        pct = f"{covered / total * 100:.2f}%" if total else "n/a"
        parts.append(f"{kind} {covered}/{total} ({pct})")
    return ", ".join(parts)


def find_losses(before, after):
    losses = {}
    for file, fc in sorted(before.items()):
        now = after.get(file)
        if now is not None and now["shape"] != fc["shape"]:
            raise CoverageError(f"{file} changed between runs; production code must stay untouched")
        now = now or {"statements": {}, "branches": {}}
        lines = sorted({
            line for key, (line, n) in fc["statements"].items()
            if n > 0 and not now["statements"].get(key, (line, 0))[1]
        })
        branches = [fc["labels"][key] for key, n in fc["branches"].items() if n > 0 and not now["branches"].get(key)]
        if lines or branches:
            losses[file] = (lines, branches)
    return losses


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--root", default=os.getcwd())
    parser.add_argument("--exclude", action="append", default=[], help="extra glob of files to ignore")
    args = parser.parse_args(argv)
    root = os.path.abspath(args.root)
    excludes = DEFAULT_EXCLUDES + tuple(args.exclude)

    try:
        before = load(args.before, root, excludes)
        after = load(args.after, root, excludes)
        losses = find_losses(before, after)
    except (CoverageError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    counted = {file for file, fc in [*before.items(), *after.items()] if has_hits(fc)}
    untouched = len(set(before) | set(after)) - len(counted)
    print(f"before: {format_totals(totals(before, counted))}")
    print(f"after:  {format_totals(totals(after, counted))}")
    if untouched:
        print(f"totals skip {untouched} files with no hits in either run")
    if not losses:
        print("lost: none")
        return 0
    print("lost:")
    for file, (lines, branches) in losses.items():
        for line in lines:
            print(f"  {file}:{line} line")
        for label in branches:
            print(f"  {file}:{label}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
