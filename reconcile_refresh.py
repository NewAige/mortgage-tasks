#!/usr/bin/env python3
"""Refresh the reconciliation artefacts when the Encompass exports are unavailable.

`compare_configured.py` is the real thing and needs `../import/Configured Task/`.
When that directory is absent — the usual case in a fresh clone — this script does
a partial refresh instead:

  * the repo side is genuinely re-read from `tasks/`
  * the Encompass side is carried forward from the payload embedded in the previous
    `docs/reconciliation.html`
  * the delta rows for the task types you just reconciled are dropped, since both
    sides now agree
  * all four outputs are re-rendered through compare_configured.py's own writers,
    so the format is identical to a real run

    python reconcile_refresh.py --resolved Processing_FileSetup_PullDeed

Run `python compare_configured.py` against a fresh export whenever you can; it
supersedes this entirely. The generated report carries a note saying which of the
two produced it.

See docs/RECONCILIATION_RUNBOOK.md.
"""
import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_HTML = "docs/reconciliation.html"
TEMPLATE = "docs/reconciliation_template.html"


def load_compare_module():
    spec = importlib.util.spec_from_file_location(
        "compare_configured", os.path.join(HERE, "compare_configured.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_payload(path=PAGE_HTML):
    h = open(path, encoding="utf-8").read()
    i = h.index('{"stats":')
    depth, j, instr, esc = 0, i, False, False
    while j < len(h):
        c = h[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
        j += 1
    return json.loads(h[i:j + 1].replace("\\u003c", "<"))


NOTE_TEMPLATE = (
    "> **Partial refresh — {date}.** `import/Configured Task/` was not available when this\n"
    "> was regenerated, so the Encompass columns are carried forward from the previous run's\n"
    "> recorded snapshot; only the repo side was re-read from `tasks/`. Rows resolved this\n"
    "> pass are recorded in `docs/reconciliation_resolutions.json`. Re-run\n"
    "> `python compare_configured.py` against a fresh export to confirm.\n"
)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--resolved", nargs="*", default=[],
                   help="Task types reconciled this pass; their delta rows are dropped.")
    p.add_argument("--date", default="2026-07-27", help="Date stamped into the report note.")
    p.add_argument("--repo-root", default=HERE)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    os.chdir(args.repo_root)
    cc = load_compare_module()
    old = load_payload()
    resolved = set(args.resolved)

    repo_idx = cc.index_by_type(cc.load_dir("tasks"))
    rows = [r for r in old["rows"] if r["task_type"] not in resolved]

    # Encompass duration/durationFormat only appear as rows where they differ, so
    # seed from the repo first or the SLA table renders "2" instead of "2 Day".
    enc_attrs = {}
    for r in old["rows"]:
        if r["scope"] == "task" and r["field"] in ("duration", "durationFormat"):
            enc_attrs.setdefault(r["task_type"], {})[r["field"]] = r["encompass_value"]

    cfg_idx = {}
    for ttype, d in old["encompass_tasks_detail"].items():
        attrs = {"name": d["name"] or "", "taskGroupTemplateName": d["group"]}
        ra = repo_idx.get(ttype, {}).get("attrs", {})
        for f in ("duration", "durationFormat"):
            if ra.get(f):
                attrs[f] = ra[f]
        attrs.update(enc_attrs.get(ttype, {}))
        cfg_idx[ttype] = {"attrs": attrs, "subs": [{"type": s} for s in d["subs"]],
                          "assoc": [], "file": d["file"]}

    shared = sorted(set(repo_idx) & set(cfg_idx))
    only_cfg = sorted(set(cfg_idx) - set(repo_idx))
    only_repo = sorted(set(repo_idx) - set(cfg_idx))
    differing = {r["task_type"] for r in rows} & set(shared)

    o = old["stats"]
    repo_ws, repo_ws_ovr = cc.workspace_stats(repo_idx)
    stats = {
        "encompass_tasks": o["encompass_tasks"],
        "repo_tasks": len(repo_idx),
        "encompass_subtasks": o["encompass_subtasks"],
        "repo_subtasks": cc.subtask_total(repo_idx),
        "shared": len(shared),
        "only_encompass": len(only_cfg),
        "only_repo": len(only_repo),
        "shared_identical": len(shared) - len(differing),
        "shared_differing": len(differing),
        "subtasks_encompass_only": sum(
            1 for r in rows if r["scope"] == "subtask" and r["status"] == cc.STATUS_ENCOMPASS_ONLY),
        "subtasks_repo_only": sum(
            1 for r in rows if r["scope"] == "subtask" and r["status"] == cc.STATUS_REPO_ONLY),
        "subtask_description_diffs": sum(1 for r in rows if r["scope"] == "subtask_description"),
        "subtask_rank_diffs": sum(1 for r in rows if r["scope"] == "subtask_rank"),
        "rename_pairs": cc.find_rename_pairs(only_cfg, only_repo, cfg_idx, repo_idx),
        "only_encompass_types": only_cfg,
        "only_repo_types": only_repo,
        "shared_types": shared,
        "placeholders": {"encompass": old["placeholders"]["encompass"],
                         "repo": list(cc.placeholder_stats(repo_idx))},
        "namespace_violations": {"encompass": old["namespace_violations"]["encompass"],
                                 "repo": len(cc.namespace_violations(repo_idx))},
        "separators": {"encompass": old["separators"]["encompass"],
                       "repo": cc.separator_stats(repo_idx)},
        "assignees": {"encompass": old["assignees"]["encompass"],
                      "repo": cc.assignee_stats(repo_idx)},
        "groups": {"encompass": old["groups"]["encompass"], "repo": cc.group_stats(repo_idx)},
        "workspaces": {"encompass": old["workspaces"]["encompass"],
                       "repo": [repo_ws, repo_ws_ovr]},
        "duplicate_names": {"encompass": old["duplicate_names"]["encompass"],
                            "repo": cc.duplicate_names(repo_idx)},
    }

    payload = cc.build_payload(rows, stats, repo_idx, cfg_idx, args.repo_root)
    cc.write_csv(rows, "docs/comparison_deltas.csv")
    cc.write_html(payload, TEMPLATE, PAGE_HTML)
    cc.write_markdown(rows, stats, repo_idx, cfg_idx, "docs/COMPARISON_REPORT.md",
                      args.repo_root)

    md = open("docs/COMPARISON_REPORT.md", encoding="utf-8").read()
    anchor = "Per-row detail lives in `comparison_deltas.csv`.\n"
    md = md.replace(anchor, anchor + "\n" + NOTE_TEMPLATE.format(date=args.date), 1)
    open("docs/COMPARISON_REPORT.md", "w", encoding="utf-8").write(md)

    summary = {
        "encompassTasks": stats["encompass_tasks"],
        "repoTasks": stats["repo_tasks"],
        "shared": stats["shared"],
        "sharedDiffering": stats["shared_differing"],
        "onlyEncompass": stats["only_encompass"],
        "onlyRepo": stats["only_repo"],
        "unmatched": stats["only_encompass"] + stats["only_repo"],
        "deltaRows": len(rows),
        "report": PAGE_HTML,
    }
    with open("docs/comparison_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)

    if args.json:
        print(json.dumps({"ok": True, "resolved": sorted(resolved), **summary}, indent=1))
    else:
        print(f"resolved {len(resolved)} type(s) | rows {len(old['rows'])} -> {len(rows)} | "
              f"shared differing {o['shared_differing']} -> {stats['shared_differing']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
