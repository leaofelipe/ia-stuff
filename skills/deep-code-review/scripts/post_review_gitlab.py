#!/usr/bin/env python3
# invariant: refuse to POST if review_gate.py is non-zero so a failed lint cannot reach GitLab.
# invariant: inline comments are drafts until bulk_publish, so the MR author gets one review, not a trickle.
# hazard: bulk_publish publishes every pending draft of the user, so pre-existing drafts abort the run.
# invariant: post only the commit the round reviewed, so anchors and approval never land on unreviewed code.
import json
import os
import subprocess
import sys
import tempfile

MARKER = "<!-- deep-code-review head={head} round={round} -->"
REVIEWER_STATE = {"REQUEST_CHANGES": "requested_changes", "COMMENT": "reviewed", "APPROVE": "reviewed"}


def run(args):
    p = subprocess.run(args, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def glab_json(args):
    rc, out, err = run(["glab"] + args)
    if rc != 0:
        sys.exit(f"glab {' '.join(args)} failed: {err or out}")
    return json.loads(out) if out else {}


def api(method, endpoint, body=None):
    args = ["glab", "api", "--method", method, endpoint]
    tmp_path = None
    if body is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(body, tmp, ensure_ascii=False)
            tmp_path = tmp.name
        args += ["--input", tmp_path]
    rc, out, err = run(args)
    if tmp_path:
        os.unlink(tmp_path)
    return rc, (json.loads(out) if rc == 0 and out else {}), err or out


def main():
    argv = sys.argv[1:]
    if not argv:
        sys.exit("usage: post_review_gitlab.py findings.json [--mr IID]")
    findings_path = argv[0]
    mr_arg = []
    if "--mr" in argv:
        mr_arg = [argv[argv.index("--mr") + 1]]

    gate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_gate.py")
    rc, out, err = run([sys.executable, gate, findings_path])
    if rc != 0:
        sys.exit(f"refusing to post, gate failed:\n{out}{err}")

    data = json.load(open(findings_path, encoding="utf-8"))
    verdict = data["verdict"]
    body = data["summary"]

    iid = glab_json(["mr", "view", *mr_arg, "--output", "json"])["iid"]
    base = f"projects/:id/merge_requests/{iid}"
    mr = glab_json(["api", base])
    author, refs = mr["author"]["username"], mr["diff_refs"]
    me = glab_json(["api", "user"])["username"]

    if data.get("dirty"):
        sys.exit("refusing to post: this round reviewed uncommitted changes that are not on the MR. Re-run the review in MR mode.")
    head = data.get("head") or refs["head_sha"]
    if head != refs["head_sha"]:
        sys.exit(
            f"refusing to post: the round reviewed {head[:12]}, but !{iid} is at {refs['head_sha'][:12]}. "
            "Re-run the review against the current head."
        )

    rc, pending, msg = api("GET", f"{base}/draft_notes")
    if rc != 0:
        sys.exit(f"listing draft notes failed: {msg}")
    if pending:
        sys.exit(
            f"refusing to post: {len(pending)} pending draft note(s) on !{iid} would be published with this review. "
            "Publish or delete them first."
        )

    created = []
    for f in data["findings"]:
        if f.get("severity") == "pre-existing" or not f.get("line"):
            continue
        position = {
            "position_type": "text",
            "base_sha": refs["base_sha"],
            "start_sha": refs["start_sha"],
            "head_sha": refs["head_sha"],
            "old_path": f["path"],
            "new_path": f["path"],
            "new_line": f["line"],
        }
        rc, note, msg = api("POST", f"{base}/draft_notes", {"note": f["body"], "position": position})
        if rc != 0:
            for draft_id in created:
                api("DELETE", f"{base}/draft_notes/{draft_id}")
            sys.exit(
                f"draft note at {f['path']}:{f['line']} failed: {msg}\n"
                "hint: a 400 here usually means the line is not part of the MR diff. "
                "Re-anchor on a changed line from the patch or fold the finding into the summary. No drafts were left behind."
            )
        created.append(note["id"])

    approve = verdict == "APPROVE" and me != author
    if me == author and verdict != "COMMENT":
        body += (
            f"\n\n---\n_Intended verdict: **{verdict}**. "
            f"Posted as a comment because this review was posted by the merge request author._"
        )
    body += "\n\n" + MARKER.format(head=head, round=data.get("round", 1))

    publish = {"note": body}
    if me != author:
        publish["reviewer_state"] = REVIEWER_STATE[verdict]
    rc, _, msg = api("POST", f"{base}/draft_notes/bulk_publish", publish)
    if rc != 0 and "reviewer_state" in publish:
        publish.pop("reviewer_state")
        rc, _, msg = api("POST", f"{base}/draft_notes/bulk_publish", publish)
    if rc != 0:
        sys.exit(f"bulk publish failed: {msg}\nThe {len(created)} draft note(s) are still pending on !{iid}.")

    event = "COMMENT" if me == author else verdict
    if approve:
        rc, _, msg = api("POST", f"{base}/approve", {"sha": head})
        if rc != 0:
            sys.exit(f"review posted on {mr['web_url']}, but approval failed: {msg}")

    print(f"posted: event={event} reviewer_state={publish.get('reviewer_state', 'none')} comments={len(created)} url={mr['web_url']}")


if __name__ == "__main__":
    main()
