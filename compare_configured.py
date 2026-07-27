#!/usr/bin/env python3
"""
compare_configured.py — Diff the Encompass "configured task" exports against the repo library.

`import/Configured Task/*.xml` holds raw exports pulled back **out of** Encompass — what is
actually live in the LOS. `tasks/**/*.xml` is this repo's source-of-truth library. The two
drift. This script produces the reconciliation view: what is live but untracked, what is
tracked but never deployed, and where the same task says different things on each side.

Usage:
    # Defaults (run from the repo root):
    python compare_configured.py

    # Explicit paths / outputs:
    python compare_configured.py \
      --configured-dir "../import/Configured Task" \
      --tasks-dir tasks \
      --out-md  docs/COMPARISON_REPORT.md \
      --out-csv docs/comparison_deltas.csv

    # Machine-readable summary for agent pipelines:
    python compare_configured.py --json

    # Point at the older bundles instead of the current export set:
    python compare_configured.py --configured-dir ../import --out-md /tmp/a.md --out-csv /tmp/b.csv

Tasks are joined on the `type` attribute (the Encompass import key). Where a task exists on
both sides under *different* types, a normalised-name fallback surfaces it as a rename pair
rather than a bogus add/drop pair.

Volatile attributes (`id`, `created*`, `lastModified*`, `createdVia`) are deliberately ignored —
they always differ and would drown the real signal.

Return value (stdout, or JSON with --json):
    {"ok": true, "md": "<path>", "csv": "<path>", "rows": N, ...counts}

Exit codes: 0 = success, 1 = error.
"""

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Task-level attributes worth comparing. Everything else is either volatile
#: (timestamps, ids, createdVia) or not meaningful for reconciliation.
COMPARED_FIELDS = [
    "name",
    "required",
    "priority",
    "rank",
    "duration",
    "durationFormat",
    "calendar",
    "autocomplete",
    "autoCreate",
    "taskGroupTemplateName",
    "comments",
]

#: Attributes intentionally excluded from the diff.
IGNORED_FIELDS = {
    "id",
    "created",
    "createdBy",
    "lastModified",
    "lastModifiedBy",
    "createdVia",
    "taskGroupTemplateId",
    "taskTemplateId",
}

#: Encompass leaves this literal string in the subtask `name` when the display
#: label was never filled in. Users see "Sub-Task Name" in the UI.
PLACEHOLDER_SUBTASK_NAME = "Sub-Task Name"

EN_DASH = "–"

STATUS_ENCOMPASS_ONLY = "ENCOMPASS_ONLY"
STATUS_REPO_ONLY = "REPO_ONLY"
STATUS_BOTH = "BOTH"

CSV_HEADER = [
    "scope",
    "task_type",
    "task_name_repo",
    "task_name_encompass",
    "status",
    "field",
    "repo_value",
    "encompass_value",
    "repo_file",
    "encompass_file",
]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_file(path):
    """Parse one task XML into a list of task dicts. Returns [] on parse error."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        print(f"warning: skipping unparseable {path}: {exc}", file=sys.stderr)
        return []

    tasks = []
    for tt in root.iter("taskTemplate"):
        tasks.append(
            {
                "file": path,
                "attrs": dict(tt.attrib),
                # (relationship, entityUID) is the pair that actually matters —
                # entityId is a system value that legitimately differs per environment.
                "assoc": [
                    (a.get("relationship"), a.get("entityUID"))
                    for a in tt.iter("association")
                ],
                "subs": [dict(s.attrib) for s in tt.iter("subTaskTemplate")],
            }
        )
    return tasks


def load_dir(directory):
    """Load every *.xml under a directory (recursive), sorted for determinism."""
    tasks = []
    pattern = os.path.join(directory, "**", "*.xml")
    for path in sorted(glob.glob(pattern, recursive=True)):
        tasks.extend(parse_file(path))
    return tasks


def index_by_type(tasks):
    """Map type -> task. Later duplicates win but are reported to stderr."""
    out = {}
    for t in tasks:
        ttype = t["attrs"].get("type")
        if ttype in out:
            print(
                f"warning: duplicate task type {ttype!r} in {t['file']}",
                file=sys.stderr,
            )
        out[ttype] = t
    return out


def normalise_name(name):
    """Strip case, punctuation and spacing so 'Review PAR (1st Review)' ~ 'Review PAR'."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def find_rename_pairs(only_encompass, only_repo, cfg_idx, repo_idx):
    """
    Surface tasks present on both sides under different `type` values.

    These are the dangerous ones: re-importing the repo copy creates a *second*
    task in Encompass rather than updating the existing one.
    """
    pairs = []
    for rtype in only_repo:
        rname = normalise_name(repo_idx[rtype]["attrs"].get("name"))
        if not rname:
            continue
        for ctype in only_encompass:
            cname = normalise_name(cfg_idx[ctype]["attrs"].get("name"))
            if not cname:
                continue
            if rname == cname or rname in cname or cname in rname:
                pairs.append((rtype, ctype))
    return pairs


# ---------------------------------------------------------------------------
# Diffing
# ---------------------------------------------------------------------------

def diff_task(ttype, repo_task, cfg_task):
    """
    Compare one task present on both sides.

    Returns a list of CSV row dicts, one per differing field / association /
    subtask. Empty list means the two sides agree on everything compared.
    """
    rows = []
    r_attrs, c_attrs = repo_task["attrs"], cfg_task["attrs"]
    r_name = r_attrs.get("name", "")
    c_name = c_attrs.get("name", "")

    def row(scope, status, field, repo_value, cfg_value):
        return {
            "scope": scope,
            "task_type": ttype,
            "task_name_repo": r_name,
            "task_name_encompass": c_name,
            "status": status,
            "field": field,
            "repo_value": repo_value or "",
            "encompass_value": cfg_value or "",
            "repo_file": repo_task["file"],
            "encompass_file": cfg_task["file"],
        }

    # --- task attributes
    for field in COMPARED_FIELDS:
        rv, cv = r_attrs.get(field) or "", c_attrs.get(field) or ""
        if rv != cv:
            rows.append(row("task", STATUS_BOTH, field, rv, cv))

    # --- associations (assignee role, workspace, workspace overrides)
    r_assoc, c_assoc = set(repo_task["assoc"]), set(cfg_task["assoc"])
    for rel, uid in sorted(c_assoc - r_assoc):
        rows.append(row("association", STATUS_ENCOMPASS_ONLY, rel, "", uid))
    for rel, uid in sorted(r_assoc - c_assoc):
        rows.append(row("association", STATUS_REPO_ONLY, rel, uid, ""))

    # --- subtasks, keyed on `type` (the stable subtask identifier)
    r_subs = {s.get("type"): s for s in repo_task["subs"]}
    c_subs = {s.get("type"): s for s in cfg_task["subs"]}

    for stype in [s.get("type") for s in cfg_task["subs"] if s.get("type") not in r_subs]:
        rows.append(
            row("subtask", STATUS_ENCOMPASS_ONLY, stype, "", c_subs[stype].get("description"))
        )
    for stype in [s.get("type") for s in repo_task["subs"] if s.get("type") not in c_subs]:
        rows.append(
            row("subtask", STATUS_REPO_ONLY, stype, r_subs[stype].get("description"), "")
        )

    for stype, c_sub in c_subs.items():
        r_sub = r_subs.get(stype)
        if r_sub is None:
            continue
        r_desc = (r_sub.get("description") or "").strip()
        c_desc = (c_sub.get("description") or "").strip()
        if r_desc != c_desc:
            rows.append(row("subtask_description", STATUS_BOTH, stype, r_desc, c_desc))
        if r_sub.get("rank") != c_sub.get("rank"):
            rows.append(
                row("subtask_rank", STATUS_BOTH, stype, r_sub.get("rank"), c_sub.get("rank"))
            )

    return rows


def build_rows(repo_idx, cfg_idx):
    """Build every CSV row: unmatched tasks on both sides, then field-level diffs."""
    rows = []

    for ttype in sorted(set(cfg_idx) - set(repo_idx)):
        t = cfg_idx[ttype]
        rows.append(
            {
                "scope": "task",
                "task_type": ttype,
                "task_name_repo": "",
                "task_name_encompass": t["attrs"].get("name", ""),
                "status": STATUS_ENCOMPASS_ONLY,
                "field": "",
                "repo_value": "",
                "encompass_value": f"{len(t['subs'])} subtask(s)",
                "repo_file": "",
                "encompass_file": t["file"],
            }
        )

    for ttype in sorted(set(repo_idx) - set(cfg_idx)):
        t = repo_idx[ttype]
        rows.append(
            {
                "scope": "task",
                "task_type": ttype,
                "task_name_repo": t["attrs"].get("name", ""),
                "task_name_encompass": "",
                "status": STATUS_REPO_ONLY,
                "field": "",
                "repo_value": f"{len(t['subs'])} subtask(s)",
                "encompass_value": "",
                "repo_file": t["file"],
                "encompass_file": "",
            }
        )

    for ttype in sorted(set(repo_idx) & set(cfg_idx)):
        rows.extend(diff_task(ttype, repo_idx[ttype], cfg_idx[ttype]))

    return rows


# ---------------------------------------------------------------------------
# Aggregate statistics
# ---------------------------------------------------------------------------

def placeholder_stats(index):
    """Tasks/subtasks still carrying the literal 'Sub-Task Name' display label."""
    tasks, subs = 0, 0
    for t in index.values():
        n = sum(1 for s in t["subs"] if s.get("name") == PLACEHOLDER_SUBTASK_NAME)
        if n:
            tasks += 1
            subs += n
    return tasks, subs


def namespace_violations(index):
    """
    Subtask `type`s not prefixed with the parent task name.

    docs/conventions.md rule 2 requires `{Task Name} – {Subtask Name}`.
    """
    out = []
    for ttype, t in index.items():
        parent = t["attrs"].get("name") or ""
        for s in t["subs"]:
            stype = s.get("type") or ""
            if not stype.startswith(parent):
                out.append((ttype, parent, stype))
    return out


def separator_stats(index):
    counts = Counter()
    for t in index.values():
        for s in t["subs"]:
            stype = s.get("type") or ""
            if EN_DASH in stype:
                counts["en_dash"] += 1
            elif " - " in stype:
                counts["hyphen"] += 1
            else:
                counts["none"] += 1
    return counts


def assignee_stats(index):
    counts = Counter()
    for t in index.values():
        roles = [uid for rel, uid in t["assoc"] if rel == "Assignee"]
        counts[roles[0] if roles else "(unassigned)"] += 1
    return counts


def group_stats(index):
    return Counter(
        t["attrs"].get("taskGroupTemplateName") or "(ungrouped)" for t in index.values()
    )


def workspace_stats(index):
    bound = sum(1 for t in index.values() if any(r == "workspace" for r, _ in t["assoc"]))
    overrides = sum(
        1 for t in index.values() if any("workspaceoverride" in (r or "") for r, _ in t["assoc"])
    )
    return bound, overrides


def duplicate_names(index):
    by_name = defaultdict(list)
    for ttype, t in index.items():
        by_name[t["attrs"].get("name")].append((ttype, t["file"]))
    return {n: v for n, v in by_name.items() if len(v) > 1}


def subtask_total(index):
    return sum(len(t["subs"]) for t in index.values())


def compute_stats(repo_idx, cfg_idx, rows):
    """Everything the Markdown report and artifact need, in one dict."""
    shared = sorted(set(repo_idx) & set(cfg_idx))
    only_cfg = sorted(set(cfg_idx) - set(repo_idx))
    only_repo = sorted(set(repo_idx) - set(cfg_idx))

    # A shared task only produces rows when something about it differs, so the set of
    # shared types appearing in `rows` is exactly the set of shared tasks that disagree.
    shared_set = set(shared)
    tasks_with_diffs = {r["task_type"] for r in rows} & shared_set

    cfg_ph_tasks, cfg_ph_subs = placeholder_stats(cfg_idx)
    repo_ph_tasks, repo_ph_subs = placeholder_stats(repo_idx)
    cfg_ws, cfg_ws_ovr = workspace_stats(cfg_idx)
    repo_ws, repo_ws_ovr = workspace_stats(repo_idx)

    return {
        "encompass_tasks": len(cfg_idx),
        "repo_tasks": len(repo_idx),
        "encompass_subtasks": subtask_total(cfg_idx),
        "repo_subtasks": subtask_total(repo_idx),
        "shared": len(shared),
        "only_encompass": len(only_cfg),
        "only_repo": len(only_repo),
        "shared_identical": len(shared) - len(tasks_with_diffs),
        "shared_differing": len(tasks_with_diffs),
        "subtasks_encompass_only": sum(
            1 for r in rows if r["scope"] == "subtask" and r["status"] == STATUS_ENCOMPASS_ONLY
        ),
        "subtasks_repo_only": sum(
            1 for r in rows if r["scope"] == "subtask" and r["status"] == STATUS_REPO_ONLY
        ),
        "subtask_description_diffs": sum(1 for r in rows if r["scope"] == "subtask_description"),
        "subtask_rank_diffs": sum(1 for r in rows if r["scope"] == "subtask_rank"),
        "rename_pairs": find_rename_pairs(only_cfg, only_repo, cfg_idx, repo_idx),
        "only_encompass_types": only_cfg,
        "only_repo_types": only_repo,
        "shared_types": shared,
        "placeholders": {
            "encompass": (cfg_ph_tasks, cfg_ph_subs),
            "repo": (repo_ph_tasks, repo_ph_subs),
        },
        "namespace_violations": {
            "encompass": len(namespace_violations(cfg_idx)),
            "repo": len(namespace_violations(repo_idx)),
        },
        "separators": {
            "encompass": separator_stats(cfg_idx),
            "repo": separator_stats(repo_idx),
        },
        "assignees": {"encompass": assignee_stats(cfg_idx), "repo": assignee_stats(repo_idx)},
        "groups": {"encompass": group_stats(cfg_idx), "repo": group_stats(repo_idx)},
        "workspaces": {
            "encompass": (cfg_ws, cfg_ws_ovr),
            "repo": (repo_ws, repo_ws_ovr),
        },
        "duplicate_names": {
            "encompass": duplicate_names(cfg_idx),
            "repo": duplicate_names(repo_idx),
        },
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def build_payload(rows, stats, repo_idx, cfg_idx, base):
    """Flatten the analysis into the JSON shape the HTML page and --out-json consume."""
    scalar_stats = {
        k: (dict(v) if isinstance(v, Counter) else v)
        for k, v in stats.items()
        if k
        not in {
            "assignees",
            "groups",
            "separators",
            "duplicate_names",
            "placeholders",
            "workspaces",
            "namespace_violations",
        }
    }

    def detail(index, path_fn):
        return {
            ttype: {
                "name": t["attrs"].get("name"),
                "group": t["attrs"].get("taskGroupTemplateName"),
                "file": path_fn(t["file"]),
                "subs": [s.get("type") for s in t["subs"]],
            }
            for ttype, t in index.items()
        }

    return {
        "stats": scalar_stats,
        "assignees": {k: dict(v) for k, v in stats["assignees"].items()},
        "groups": {k: dict(v) for k, v in stats["groups"].items()},
        "separators": {k: dict(v) for k, v in stats["separators"].items()},
        "placeholders": stats["placeholders"],
        "workspaces": stats["workspaces"],
        "namespace_violations": stats["namespace_violations"],
        "duplicate_names": stats["duplicate_names"],
        "encompass_tasks_detail": detail(cfg_idx, os.path.basename),
        "repo_tasks_detail": detail(repo_idx, lambda p: _rel(p, base)),
        "rows": rows,
    }


def write_csv(rows, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    # newline="" keeps csv from doubling line endings on Windows;
    # utf-8-sig so Excel opens the en-dashes correctly on a double-click.
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(rows)


#: The page template holds the body content (styles + markup + script) with a
#: `__DATA__` placeholder where the payload is injected. It is shared with the
#: hosted artifact build, which supplies its own document skeleton — so the
#: standalone wrapper below lives here rather than in the template.
#: Split rather than str.format — the body is full of CSS braces, which format() would
#: try to interpret as replacement fields.
_HTML_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="compare_configured.py">
<style>*,*::before,*::after{box-sizing:border-box}img,svg{max-width:100%}</style>
</head>
<body>
"""

_HTML_FOOT = """
</body>
</html>
"""


def write_html(payload, template_path, out_path):
    """
    Render the self-contained reconciliation page.

    Everything is inlined — no fetch, no CDN — so the file opens straight from
    disk over file:// and survives being committed and moved around.
    """
    with open(template_path, "r", encoding="utf-8") as fh:
        template = fh.read()

    if "__DATA__" not in template:
        raise ValueError(f"template missing __DATA__ placeholder: {template_path}")

    # Compact, and neutralise '<' so the payload can never terminate the <script>.
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    body = template.replace("__DATA__", blob)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(_HTML_HEAD + body + _HTML_FOOT)


def _rel(path, base):
    """Present paths relative to the repo root so the report is portable."""
    try:
        return os.path.relpath(path, base).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def write_markdown(rows, stats, repo_idx, cfg_idx, path, base):
    """Render the narrative report. The CSV carries the exhaustive per-row detail."""
    out = []
    w = out.append

    w("# Encompass Configured Tasks vs. Repo Library\n")
    w(
        "Generated by `compare_configured.py`. Compares the live Encompass exports in\n"
        "`import/Configured Task/` against this repo's `tasks/` library.\n"
        "Per-row detail lives in `comparison_deltas.csv`.\n"
    )

    w("\n## 1. Baseline\n")
    w("| | Encompass (live) | Repo (`tasks/`) |")
    w("|---|---|---|")
    w(f"| Task templates | **{stats['encompass_tasks']}** | **{stats['repo_tasks']}** |")
    w(f"| Subtask templates | **{stats['encompass_subtasks']}** | **{stats['repo_subtasks']}** |")
    w(f"| Shared task types | **{stats['shared']}** | |")
    w(f"| Only in Encompass | **{stats['only_encompass']}** | |")
    w(f"| Only in repo | | **{stats['only_repo']}** |")
    w(
        f"| Shared tasks that differ | **{stats['shared_differing']} of {stats['shared']}** | |"
    )
    w("")
    w(
        f"Subtask deltas across shared tasks: **{stats['subtasks_encompass_only']}** exist only in "
        f"Encompass, **{stats['subtasks_repo_only']}** only in the repo, "
        f"**{stats['subtask_description_diffs']}** have differing description text, "
        f"**{stats['subtask_rank_diffs']}** differ in rank."
    )

    w("\n## 2. Coverage gaps\n")
    w(f"### In Encompass, absent from the repo ({stats['only_encompass']})\n")
    w("| Task | Type | Subtasks | Export file |")
    w("|---|---|---|---|")
    for ttype in stats["only_encompass_types"]:
        t = cfg_idx[ttype]
        w(
            f"| {t['attrs'].get('name','')} | `{ttype}` | {len(t['subs'])} "
            f"| {os.path.basename(t['file'])} |"
        )

    w(f"\n### In the repo, absent from Encompass ({stats['only_repo']})\n")
    w("| Task | Type | Subtasks | File |")
    w("|---|---|---|---|")
    for ttype in stats["only_repo_types"]:
        t = repo_idx[ttype]
        w(
            f"| {t['attrs'].get('name','')} | `{ttype}` | {len(t['subs'])} "
            f"| {_rel(t['file'], base)} |"
        )

    w("\n## 3. Naming drift\n")

    if stats["rename_pairs"]:
        w("### Same task, different `type` — re-import would create duplicates\n")
        w("| Repo type | Repo name | Encompass type | Encompass name |")
        w("|---|---|---|---|")
        for rtype, ctype in stats["rename_pairs"]:
            w(
                f"| `{rtype}` | {repo_idx[rtype]['attrs'].get('name','')} "
                f"| `{ctype}` | {cfg_idx[ctype]['attrs'].get('name','')} |"
            )
        w("")

    name_rows = [r for r in rows if r["scope"] == "task" and r["field"] == "name"]
    if name_rows:
        w("### Same `type`, different display name\n")
        w("| Type | Repo name | Encompass name |")
        w("|---|---|---|")
        for r in name_rows:
            w(f"| `{r['task_type']}` | {r['repo_value']} | {r['encompass_value']} |")
        w("")

    ph_c, ph_r = stats["placeholders"]["encompass"], stats["placeholders"]["repo"]
    w(
        f"- **Placeholder subtask labels** (`name=\"{PLACEHOLDER_SUBTASK_NAME}\"`, shown verbatim "
        f"to users): Encompass **{ph_c[1]}** subtasks across **{ph_c[0]}** tasks; "
        f"repo **{ph_r[1]}** across **{ph_r[0]}**."
    )
    w(
        f"- **Subtask namespacing** (`docs/conventions.md` rule 2): Encompass violates it "
        f"**{stats['namespace_violations']['encompass']}** times, repo "
        f"**{stats['namespace_violations']['repo']}**."
    )
    sep_c, sep_r = stats["separators"]["encompass"], stats["separators"]["repo"]
    w(
        f"- **Separators in subtask types**: Encompass en-dash {sep_c['en_dash']}, "
        f"hyphen {sep_c['hyphen']}, none {sep_c['none']}; "
        f"repo en-dash {sep_r['en_dash']}, hyphen {sep_r['hyphen']}, none {sep_r['none']}."
    )

    for side, label in (("repo", "Repo"), ("encompass", "Encompass")):
        dupes = stats["duplicate_names"][side]
        for name, entries in dupes.items():
            listed = ", ".join(f"`{tt}`" for tt, _ in entries)
            w(f"- **{label} duplicate name** — {name!r} defined twice: {listed}.")

    w("\n### Task group labels\n")
    w("| Group | Encompass | Repo |")
    w("|---|---|---|")
    all_groups = sorted(set(stats["groups"]["encompass"]) | set(stats["groups"]["repo"]))
    for g in all_groups:
        w(f"| {g} | {stats['groups']['encompass'].get(g, 0)} | {stats['groups']['repo'].get(g, 0)} |")

    w("\n## 4. Subtask content deltas\n")
    sub_rows = [r for r in rows if r["scope"] == "subtask"]
    if sub_rows:
        w("| Task | Subtask | Present only in |")
        w("|---|---|---|")
        for r in sub_rows:
            side = "Encompass" if r["status"] == STATUS_ENCOMPASS_ONLY else "Repo"
            name = r["task_name_repo"] or r["task_name_encompass"]
            w(f"| {name} | {r['field']} | {side} |")
    w(
        f"\n{stats['subtask_description_diffs']} shared subtasks have differing description text — "
        "see `comparison_deltas.csv`, rows with `scope=subtask_description`."
    )

    w("\n## 5. Metadata deltas\n")
    w("### Assignee roles\n")
    w("| Role | Encompass | Repo |")
    w("|---|---|---|")
    all_roles = sorted(set(stats["assignees"]["encompass"]) | set(stats["assignees"]["repo"]))
    for role in all_roles:
        w(
            f"| {role} | {stats['assignees']['encompass'].get(role, 0)} "
            f"| {stats['assignees']['repo'].get(role, 0)} |"
        )

    ws_c, ws_r = stats["workspaces"]["encompass"], stats["workspaces"]["repo"]
    w(
        f"\n- **Workspaces**: Encompass binds {ws_c[0]}/{stats['encompass_tasks']} tasks "
        f"({ws_c[1]} with field overrides); repo binds {ws_r[0]}/{stats['repo_tasks']} "
        f"({ws_r[1]} with overrides)."
    )

    # Duration is meaningless without its unit — "5 vs 1" hides "5 Minute vs 1 Day".
    # Recombine the two attributes and report the SLA as a single value per side.
    sla = sorted(
        {
            r["task_type"]
            for r in rows
            if r["scope"] == "task" and r["field"] in ("duration", "durationFormat")
        }
    )
    if sla:
        w(f"\n### Duration / SLA — {len(sla)} disagreement(s)\n")
        w("| Task | Repo | Encompass |")
        w("|---|---|---|")
        for ttype in sla:
            ra, ca = repo_idx[ttype]["attrs"], cfg_idx[ttype]["attrs"]
            w(
                f"| {ra.get('name') or ttype} "
                f"| {ra.get('duration','')} {ra.get('durationFormat','')} "
                f"| {ca.get('duration','')} {ca.get('durationFormat','')} |"
            )

    for field, label in (
        ("autocomplete", "`autocomplete`"),
        ("priority", "Priority"),
        ("calendar", "Calendar"),
        ("rank", "Rank"),
        ("required", "`required`"),
    ):
        frows = [r for r in rows if r["scope"] == "task" and r["field"] == field]
        if not frows:
            continue
        w(f"\n### {label} — {len(frows)} disagreement(s)\n")
        w("| Task | Repo | Encompass |")
        w("|---|---|---|")
        for r in frows:
            w(
                f"| {r['task_name_repo'] or r['task_type']} | {r['repo_value'] or '(unset)'} "
                f"| {r['encompass_value'] or '(unset)'} |"
            )

    w("\n## 6. Reconciliation backlog\n")
    w(
        "**P0 — type-key mismatches.** The rename pairs in section 3 would import as *new* "
        "Encompass tasks rather than updates. Pick a canonical type per pair before the next import."
    )
    w(
        "\n**P0 — duplicate definitions.** Resolve any duplicate-name entries listed in section 3."
    )
    w(
        f"\n**P1 — backfill.** {stats['only_encompass']} live tasks are untracked in git. "
        "Export them into `tasks/` so the repo reflects production."
    )
    w(
        f"\n**P1 — deploy or drop.** {stats['only_repo']} repo tasks have never reached Encompass. "
        "Confirm each is intended for deployment."
    )
    w(
        "\n**P2 — metadata alignment.** Assignee roles, workspace UIDs, durations and "
        "`autocomplete` flags per section 5."
    )
    w(
        f"\n**P2 — naming hygiene.** {ph_c[1]} placeholder subtask labels are live in production; "
        f"{stats['namespace_violations']['encompass']} subtask types break the namespacing rule."
    )

    w("")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Diff the Encompass configured-task exports against the repo library.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--configured-dir",
        default=os.path.join("..", "import", "Configured Task"),
        help="Directory of Encompass export XML (default: ../import/Configured Task).",
    )
    p.add_argument("--tasks-dir", default="tasks", help="Repo task library (default: tasks).")
    p.add_argument("--out-md", default=os.path.join("docs", "COMPARISON_REPORT.md"))
    p.add_argument("--out-csv", default=os.path.join("docs", "comparison_deltas.csv"))
    p.add_argument(
        "--out-html",
        default=os.path.join("docs", "reconciliation.html"),
        help="Self-contained browser report, linked from roadmap.html. Pass '' to skip.",
    )
    p.add_argument(
        "--template",
        default=os.path.join("docs", "reconciliation_template.html"),
        help="Page template containing the __DATA__ placeholder.",
    )
    p.add_argument(
        "--out-summary",
        default=os.path.join("docs", "comparison_summary.json"),
        help="Small headline-counts file that roadmap.html reads for its badge. Pass '' to skip.",
    )
    p.add_argument(
        "--out-json",
        default=None,
        help="Optional path to dump the full stats + rows as JSON (same payload the page embeds).",
    )
    p.add_argument("--json", action="store_true", help="Print the summary as JSON.")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    for label, d in (("--configured-dir", args.configured_dir), ("--tasks-dir", args.tasks_dir)):
        if not os.path.isdir(d):
            print(json.dumps({"ok": False, "error": f"{label} not found: {d}"}))
            return 1

    cfg_idx = index_by_type(load_dir(args.configured_dir))
    repo_idx = index_by_type(load_dir(args.tasks_dir))

    if not cfg_idx or not repo_idx:
        print(json.dumps({"ok": False, "error": "No task templates found on one or both sides."}))
        return 1

    rows = build_rows(repo_idx, cfg_idx)
    stats = compute_stats(repo_idx, cfg_idx, rows)

    base = os.path.abspath(os.path.dirname(args.tasks_dir.rstrip("/\\")) or ".")

    # Repo paths relative to the repo root, Encompass paths as bare export filenames —
    # keeps the CSV readable and portable across machines.
    for r in rows:
        if r["repo_file"]:
            r["repo_file"] = _rel(r["repo_file"], base)
        if r["encompass_file"]:
            r["encompass_file"] = os.path.basename(r["encompass_file"])

    payload = build_payload(rows, stats, repo_idx, cfg_idx, base)

    try:
        write_csv(rows, args.out_csv)
        write_markdown(rows, stats, repo_idx, cfg_idx, args.out_md, base)

        if args.out_html:
            if not os.path.isfile(args.template):
                raise FileNotFoundError(f"template not found: {args.template}")
            write_html(payload, args.template, args.out_html)

        if args.out_summary:
            # Small enough for roadmap.html to fetch just to fill its badge.
            os.makedirs(os.path.dirname(os.path.abspath(args.out_summary)), exist_ok=True)
            with open(args.out_summary, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "encompassTasks": stats["encompass_tasks"],
                        "repoTasks": stats["repo_tasks"],
                        "shared": stats["shared"],
                        "sharedDiffering": stats["shared_differing"],
                        "onlyEncompass": stats["only_encompass"],
                        "onlyRepo": stats["only_repo"],
                        "unmatched": stats["only_encompass"] + stats["only_repo"],
                        "deltaRows": len(rows),
                        "report": "docs/reconciliation.html",
                    },
                    fh,
                    indent=1,
                )

        if args.out_json:
            os.makedirs(os.path.dirname(os.path.abspath(args.out_json)), exist_ok=True)
            with open(args.out_json, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=1)
    except Exception as exc:  # noqa: BLE001 - surface any write failure as JSON
        print(json.dumps({"ok": False, "error": f"Write failed: {exc}"}))
        return 1

    summary = {
        "ok": True,
        "md": args.out_md,
        "csv": args.out_csv,
        "html": args.out_html or None,
        "rows": len(rows),
        "encompass_tasks": stats["encompass_tasks"],
        "repo_tasks": stats["repo_tasks"],
        "encompass_subtasks": stats["encompass_subtasks"],
        "repo_subtasks": stats["repo_subtasks"],
        "shared": stats["shared"],
        "only_encompass": stats["only_encompass"],
        "only_repo": stats["only_repo"],
        "shared_differing": stats["shared_differing"],
        "subtasks_encompass_only": stats["subtasks_encompass_only"],
        "subtasks_repo_only": stats["subtasks_repo_only"],
        "subtask_description_diffs": stats["subtask_description_diffs"],
        "subtask_rank_diffs": stats["subtask_rank_diffs"],
    }

    if args.json:
        print(json.dumps(summary, indent=1))
    else:
        print(
            f"Encompass {stats['encompass_tasks']} tasks / {stats['encompass_subtasks']} subtasks  "
            f"vs  repo {stats['repo_tasks']} / {stats['repo_subtasks']}\n"
            f"  shared {stats['shared']} ({stats['shared_differing']} differ) | "
            f"Encompass-only {stats['only_encompass']} | repo-only {stats['only_repo']}\n"
            f"  {len(rows)} delta rows -> {args.out_csv}\n"
            f"  report -> {args.out_md}"
            + (f"\n  page   -> {args.out_html}" if args.out_html else "")
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
