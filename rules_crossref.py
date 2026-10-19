#!/usr/bin/env python3
"""Cross-reference rules/rules.json against tasks/**.xml and roadmap.json.

Writes docs/rules_crossref.json and docs/RULES_CROSSREF.md. Stdlib only,
deterministic (no timestamps; sorted output).

    python rules_crossref.py [--json]
"""
import argparse
import difflib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(ROOT, "docs", "rules_crossref.json")
OUT_MD = os.path.join(ROOT, "docs", "RULES_CROSSREF.md")

ROLE_ORDER = ["trigger", "required", "creates", "completes",
              "subtask-trigger", "subtask-creates", "subtask-completes"]


def norm(s):
    s = re.sub(r"[‐-―−-]", "-", s or "")
    return re.sub(r"\s+", " ", s).strip().casefold()


def load_tasks():
    """-> (tasks {type: {id, name, file, subs:set}} , dups [(type, files)])"""
    tasks, dups = {}, []
    base = os.path.join(ROOT, "tasks")
    for dp, dn, fn in os.walk(base):
        dn.sort()
        for f in sorted(fn):
            if not f.endswith(".xml"):
                continue
            path = os.path.join(dp, f)
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError as e:
                print(f"WARN: cannot parse {rel}: {e}", file=sys.stderr)
                continue
            for tt in root.iter("taskTemplate"):
                ty = tt.get("type")
                subs = {st.get("type"): st.get("id")
                        for st in tt.iter("subTaskTemplate") if st.get("type")}
                if ty in tasks:
                    dups.append((ty, [tasks[ty]["file"], rel]))
                    tasks[ty]["subs"].update(subs)
                    continue
                tasks[ty] = {"id": tt.get("id"), "name": tt.get("name"),
                             "file": rel, "subs": subs}
    return tasks, dups


def collect_refs(rules):
    """Return list of refs: dict(rule, kind(task|subtask), role, task, sub)."""
    refs = []

    def add(r, role, task, sub=None):
        if not task:
            return
        refs.append({"rule": r["name"], "ruleId": r["id"], "role": role,
                     "task": task, "subtask": sub})

    for r in rules:
        m = r.get("match", {})
        for t in m.get("taskType", []):
            subs = m.get("subtaskType", [])
            if subs:
                for s in subs:
                    add(r, "subtask-trigger", t, s)
            else:
                add(r, "trigger", t)
        for c in r.get("conditions", []):
            for t in c.get("requiredTasks", []) or []:
                add(r, "required", t)
        for e in r.get("effects", []):
            k = e.get("kind")
            t = e.get("taskType")
            if k == "task:create":
                add(r, "creates", t)
            elif k == "task:complete":
                add(r, "completes", t)
            elif k == "subtask:create":
                add(r, "subtask-creates", t, e.get("subtaskType"))
            elif k == "subtask:complete":
                add(r, "subtask-completes", t, e.get("subtaskType"))
    # dedupe
    seen, out = set(), []
    for x in refs:
        key = (x["ruleId"], x["role"], x["task"], x["subtask"])
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def collect_ids(rules):
    """taskTemplateId params on process steps."""
    out, seen = [], set()
    for r in rules:
        for p in r.get("processes", []):
            for s in p.get("steps", []):
                params = s.get("params")
                for pr in (params if isinstance(params, list) else [params]):
                    if not isinstance(pr, dict) or not pr.get("taskTemplateId"):
                        continue
                    t = pr.get("taskTemplateType") or pr.get("type")
                    key = (r["id"], t, pr["taskTemplateId"])
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"rule": r["name"], "task": t,
                                "ruleId": pr["taskTemplateId"]})
    return out


def classify_sub(task, sub, tasks, sub_owner):
    if task not in tasks:
        return {"class": "task-missing", "detail": "task type not in tasks/"}
    subs = tasks[task]["subs"]
    if sub in subs:
        return None
    ns = {norm(k): k for k in subs}
    if norm(sub) in ns:
        return {"class": "near-match", "repoValue": ns[norm(sub)],
                "detail": "differs only by dash/whitespace/case"}
    others = sorted(sub_owner.get(sub, []) + sub_owner.get("~" + norm(sub), []))
    others = [o for o in dict.fromkeys(others) if o != task]
    if others:
        return {"class": "other-task", "otherTasks": others,
                "detail": "subtask exists under a different task"}
    close = difflib.get_close_matches(sub, sorted(subs), n=1, cutoff=0.6)
    return {"class": "no-match", "closest": close[0] if close else None,
            "detail": "no matching subtask"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="print JSON summary")
    args = ap.parse_args()

    rj = json.load(open(os.path.join(ROOT, "rules", "rules.json"), encoding="utf-8"))
    rules = sorted(rj["rules"], key=lambda r: (r["name"], r["id"]))
    rule_by_id = {r["id"]: r for r in rules}
    rmap = json.load(open(os.path.join(ROOT, "roadmap.json"), encoding="utf-8"))
    tasks, dup_types = load_tasks()

    sub_owner = defaultdict(list)
    for t, info in tasks.items():
        for s in info["subs"]:
            sub_owner[s].append(t)
            sub_owner["~" + norm(s)].append(t)

    refs = collect_refs(rules)
    ids = collect_ids(rules)

    # --- broken tasks
    bt = defaultdict(list)
    for x in refs:
        if x["task"] not in tasks:
            bt[x["task"]].append(x)
    broken_tasks = []
    for t in sorted(bt):
        close = difflib.get_close_matches(t, sorted(tasks), n=1, cutoff=0.6)
        broken_tasks.append({
            "task": t, "closest": close[0] if close else None,
            "refs": sorted({(x["rule"], x["role"]) for x in bt[t]})})
    for b in broken_tasks:
        b["refs"] = [{"rule": a, "role": b2} for a, b2 in b["refs"]]

    # --- broken subtasks
    bs = defaultdict(list)
    for x in refs:
        if x["subtask"] is None:
            continue
        c = classify_sub(x["task"], x["subtask"], tasks, sub_owner)
        if c:
            bs[(x["task"], x["subtask"], c["class"])].append((x, c))
    broken_subs = []
    for (t, s, cl) in sorted(bs):
        items = bs[(t, s, cl)]
        c = items[0][1]
        e = {"task": t, "subtask": s, **c,
             "refs": [{"rule": a, "role": b} for a, b in
                      sorted({(x["rule"], x["role"]) for x, _ in items})]}
        broken_subs.append(e)

    # --- id mismatches
    idm, seen = [], set()
    for i in ids:
        info = tasks.get(i["task"])
        if not info or info["id"] == i["ruleId"]:
            continue
        key = (i["task"], i["ruleId"])
        if key in seen:
            continue
        seen.add(key)
        idm.append({"task": i["task"], "ruleTaskTemplateId": i["ruleId"],
                    "repoId": info["id"], "file": info["file"],
                    "rules": sorted({j["rule"] for j in ids
                                     if j["task"] == i["task"] and j["ruleId"] == i["ruleId"]})})
    idm.sort(key=lambda e: (e["task"], e["ruleTaskTemplateId"]))
    id_checked = len({(i["task"], i["ruleId"]) for i in ids if i["task"] in tasks})

    # --- per-task linkage
    by_task = defaultdict(lambda: defaultdict(set))
    for x in refs:
        by_task[x["task"]][x["role"]].add(x["rule"])
    file_types = defaultdict(list)
    for t, info in tasks.items():
        file_types[info["file"]].append(t)
    linkage = []
    for st in sorted(rmap["stages"], key=lambda s: s.get("order", 0)):
        for t in st["tasks"]:
            xf = t.get("xmlFile")
            types = sorted(file_types.get(xf, [])) if xf else []
            roles = defaultdict(set)
            for ty in types:
                for role, names in by_task.get(ty, {}).items():
                    roles[role] |= names
            referenced = any(roles.values())
            rs = t.get("ruleStatus")
            flag = None
            if rs in ("Complete", "Partial") and not referenced:
                flag = "no-rules-but-status-" + rs
            elif rs in ("Planned", "Not Started") and referenced:
                flag = "rules-exist-but-status-" + rs
            linkage.append({
                "stage": st["id"], "id": t["id"], "name": t["name"],
                "status": t.get("status"), "xmlFile": xf,
                "taskTypes": types, "ruleStatus": rs, "flag": flag,
                "rules": {r: sorted(roles[r]) for r in ROLE_ORDER if roles[r]}})

    # --- orphans
    orphans = sorted(((t, tasks[t]["file"]) for t in tasks if t not in by_task))
    road_files = {t.get("xmlFile") for st in rmap["stages"] for t in st["tasks"]}
    unlisted = sorted({i["file"] for i in tasks.values()} - road_files)

    # --- anomalies
    meta = rj["metadata"]
    anomalies = meta.get("anomalies", {})
    inactive = [{"name": r["name"], "xmlFile": r["xmlFile"]}
                for r in rules if r.get("status") != "ACTIVE"]

    summary = {
        "rules": len(rules), "taskTypesInRepo": len(tasks),
        "roadmapTasks": len(linkage),
        "distinctTaskTypesReferenced": len({x["task"] for x in refs}),
        "taskReferences": len(refs),
        "brokenTaskTypes": len(broken_tasks),
        "brokenTaskRefs": sum(len(b["refs"]) for b in broken_tasks),
        "brokenSubtaskPairs": len(broken_subs),
        "brokenSubtaskByClass": {c: sum(1 for b in broken_subs if b["class"] == c)
                                 for c in ("task-missing", "near-match", "other-task", "no-match")},
        "taskTemplateIdMismatches": len(idm),
        "taskTemplateIdsChecked": id_checked,
        "flaggedNoRulesButCompleteOrPartial": sum(1 for l in linkage if (l["flag"] or "").startswith("no-rules")),
        "flaggedRulesExistButPlannedOrNotStarted": sum(1 for l in linkage if (l["flag"] or "").startswith("rules-exist")),
        "orphanTaskTypes": len(orphans),
        "inactiveRules": len(inactive),
        "duplicateTaskTypesInRepo": len(dup_types),
    }
    result = {"summary": summary, "brokenTasks": broken_tasks,
              "brokenSubtasks": broken_subs, "taskTemplateIdMismatches": idm,
              "linkage": linkage, "orphanTasks": [{"type": t, "file": f} for t, f in orphans],
              "repoFilesNotInRoadmap": unlisted,
              "anomalies": anomalies, "inactiveRules": inactive,
              "duplicateRepoTaskTypes": [{"type": t, "files": f} for t, f in dup_types]}
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    # ---------------- markdown
    def tl(f):
        return f"[{os.path.basename(f)}](../{f})"

    def rl(name):
        r = next((x for x in rules if x["name"] == name), None)
        return f"[{name}](../{r['xmlFile']})" if r else name

    def rls(refs_):
        return "; ".join(f"{rl(x['rule'])} ({x['role']})" for x in refs_)

    L = ["# Rules Cross-Reference", "",
         "Generated by `rules_crossref.py` from `rules/rules.json`, `tasks/**/*.xml` and `roadmap.json`. "
         "Do not edit by hand. Note: a subtask/task `type` is the Encompass import key; template `id`s may be regenerated on import.", "",
         "## Summary", "", "| Metric | Count |", "|---|---|"]
    lab = [("Rules", "rules"), ("Task types in tasks/", "taskTypesInRepo"),
           ("Roadmap tasks", "roadmapTasks"),
           ("Distinct task types referenced by rules", "distinctTaskTypesReferenced"),
           ("Broken task types", "brokenTaskTypes"),
           ("Broken subtask pairs", "brokenSubtaskPairs"),
           ("taskTemplateId mismatches", "taskTemplateIdMismatches"),
           ("Roadmap tasks Complete/Partial with no rule refs", "flaggedNoRulesButCompleteOrPartial"),
           ("Roadmap tasks Planned/Not Started with rule refs", "flaggedRulesExistButPlannedOrNotStarted"),
           ("Orphan task types (no rule references)", "orphanTaskTypes"),
           ("Inactive rules", "inactiveRules")]
    for a, k in lab:
        L.append(f"| {a} | {summary[k]} |")
    for c, n in summary["brokenSubtaskByClass"].items():
        L.append(f"| &nbsp;&nbsp;subtask pairs: {c} | {n} |")

    L += ["", "## Broken task references", ""]
    if not broken_tasks:
        L.append("None.")
    else:
        L += ["Task types referenced by rules that have no taskTemplate in tasks/.", "",
              "| Task type | Closest in repo | Rules (role) |", "|---|---|---|"]
        for b in broken_tasks:
            L.append(f"| `{b['task']}` | {('`'+b['closest']+'`') if b['closest'] else ''} | {rls(b['refs'])} |")

    L += ["", "## Broken subtask references", ""]
    if not broken_subs:
        L.append("None.")
    titles = {"near-match": "Near match (likely fixable: dash/whitespace/case)",
              "other-task": "Subtask lives under a different task",
              "task-missing": "Parent task missing entirely",
              "no-match": "No match"}
    for cl in ("near-match", "other-task", "no-match", "task-missing"):
        items = [b for b in broken_subs if b["class"] == cl]
        if not items:
            continue
        L += ["", f"### {titles[cl]} ({len(items)})", ""]
        for b in items:
            L.append(f"- Task `{b['task']}` / subtask `{b['subtask']}`")
            if cl == "near-match":
                L.append(f"  - Repo value: `{b['repoValue']}`")
            elif cl == "other-task":
                L.append("  - Found under: " + ", ".join(f"`{o}`" for o in b["otherTasks"]))
            elif cl == "no-match" and b.get("closest"):
                L.append(f"  - Closest: `{b['closest']}`")
            if cl != "task-missing" or True:
                if cl == "task-missing":
                    pass
            L.append(f"  - Rules: {rls(b['refs'])}")

    L += ["", "## taskTemplateId mismatch", "",
          f"Rule `taskTemplateId` params checked against the matching repo taskTemplate `id` "
          f"({id_checked} distinct task/id pairs checked). Informational: `type` is the real key.", ""]
    if not idm:
        L.append("None.")
    else:
        L += ["| Task type | Rule id | Repo id | Rules |", "|---|---|---|---|"]
        for m in idm:
            L.append(f"| `{m['task']}` ([file](../{m['file']})) | `{m['ruleTaskTemplateId']}` | `{m['repoId']}` | "
                     + ", ".join(rl(n) for n in m["rules"]) + " |")

    L += ["", "## Per-task rule linkage", "",
          "Roles: trigger (rule fires off the task), required (condition), creates, completes, "
          "subtask-trigger / subtask-creates / subtask-completes.", ""]
    flagged = [l for l in linkage if l["flag"]]
    L.append("### Flags")
    L.append("")
    if not flagged:
        L.append("None.")
    for l in flagged:
        txt = ("ruleStatus %s but no rule references it" if l["flag"].startswith("no-rules")
               else "ruleStatus %s but rules reference it (status may be stale)") % l["ruleStatus"]
        L.append(f"- `{l['id']}` {l['name']}: {txt}"
                 + (f" ({tl(l['xmlFile'])})" if l["xmlFile"] else ""))
    stage = None
    for l in linkage:
        if l["stage"] != stage:
            stage = l["stage"]
            L += ["", f"### {stage}", ""]
        head = f"**{l['id']} {l['name']}**"
        if l["taskTypes"]:
            head += " - " + ", ".join(f"`{t}`" for t in l["taskTypes"])
        head += f" - ruleStatus: {l['ruleStatus']}"
        if l["xmlFile"]:
            head += f" - {tl(l['xmlFile'])}"
        if l["flag"]:
            head += " **[flag]**"
        L.append("- " + head)
        if not l["xmlFile"]:
            L.append("  - no xmlFile in roadmap")
        for role, names in l["rules"].items():
            L.append(f"  - {role}: " + ", ".join(rl(n) for n in names))
        if not l["rules"] and l["xmlFile"]:
            L.append("  - (no rule references)")

    L += ["", "## Orphan tasks", "",
          "Task types in tasks/ never referenced by any rule.", ""]
    if not orphans:
        L.append("None.")
    for t, f in orphans:
        L.append(f"- `{t}` - {tl(f)}")
    if unlisted:
        L += ["", "Repo task files not listed in roadmap.json: " + ", ".join(tl(f) for f in unlisted)]
    if dup_types:
        L += ["", "Duplicate task types across repo files: " +
              "; ".join(f"`{t}` in {', '.join(f)}" for t, f in dup_types)]

    L += ["", "## Data anomalies", "", "From `rules.json` metadata.anomalies:", ""]
    for k in sorted(anomalies):
        L.append(f"- **{k}**")
        for v in anomalies[k]:
            L.append(f"  - {rl(v.split(':')[0]) if ':' not in v[:0] else v}" if v.split(":")[0] in {r['name'] for r in rules} else f"  - {v}")
    L += ["", "### Inactive rules", ""]
    if not inactive:
        L.append("None.")
    for i in inactive:
        L.append(f"- [{i['name']}](../{i['xmlFile']})")
    L.append("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    if args.json:
        print(json.dumps({"ok": True, "json": "docs/rules_crossref.json",
                          "md": "docs/RULES_CROSSREF.md", **summary}, indent=2, sort_keys=True))
    else:
        print("Wrote docs/RULES_CROSSREF.md and docs/rules_crossref.json")
        for k, v in summary.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
