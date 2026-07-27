#!/usr/bin/env python3
"""Adopt the Encompass side of a ledger row into the repo.

Reconciliation is a two-part problem: deciding which side wins (the user's call,
per row) and applying that decision without hand-editing single-line XML. This
script does the second part for "Encompass wins", driven entirely by the recorded
diff so it cannot invent values.

    python reconcile_adopt.py --types Processing_FileSetup_PullDeed --dry-run
    python reconcile_adopt.py --types Processing_FileSetup_PullDeed
    python reconcile_adopt.py --types Processing_FileSetup_PullDeed --verify

Sources, in order of preference:
  * ../import/Configured Task/ — the raw exports. Authoritative, but usually absent
    from a fresh clone, in which case:
  * docs/comparison_deltas.csv + the payload embedded in docs/reconciliation.html,
    both written by the previous compare_configured.py run.

Only fields compare_configured.py diffs are recoverable from the fallback sources.
Anything else (subtask autoCreate/category, per-subtask associations) is not
recorded — this script leaves those alone and warns when it had to guess.

See docs/RECONCILIATION_RUNBOOK.md for the surrounding procedure.
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import uuid
from xml.etree import ElementTree as ET

DELTAS_CSV = "docs/comparison_deltas.csv"
PAGE_HTML = "docs/reconciliation.html"

#: Task groups are shared: every task in a group must carry the same id.
GROUP_IDS = {
    "Boarding": "e346c086-ced3-42e2-a8aa-a5ee54f62abe",
    "Closing": "66ac117e-fae9-44db-8ef8-eee7e2998286",
    "Disclosures": "e2d58efb-0551-4c93-a924-2e0d1f5ac97e",
    "Document Processing": "782a15d5-a92c-4bc6-9631-c099f47e6e60",
    "Funding": "8997b6dd-74af-420b-9c4f-fc232c95016f",
    "Funding QC": "2ed4e38e-6db0-4490-9de1-0c34c995969e",
    "Quality Assurance": "de9dfa21-754f-496a-9f67-e9f7812bdb95",
    "Service Orders": "2a7c3066-53c3-4740-8d64-1a1676fce1bc",
    "Underwriting": "90000990-4c59-4200-8594-1c10bb6f88f9",
}

#: Role entityIds are system integers. A UUID here imports as a broken assignee,
#: so unknown roles get a blank id and a loud warning instead.
ROLE_IDS = {"Loan Processor": "5", "Underwriter": "6"}


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def load_payload(path=PAGE_HTML):
    """Pull the JSON payload back out of the generated page."""
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


def load_rows(types, path=DELTAS_CSV):
    with open(path, encoding="utf-8-sig") as fh:
        return [r for r in csv.DictReader(fh) if r["task_type"] in types]


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def serialize(tree):
    """Write inline XML the way the repo stores it.

    ElementTree round-trips these files exactly apart from a newline after the
    declaration and a space before '/>' — undo both so the diff shows only real
    changes.
    """
    buf = io.BytesIO()
    tree.write(buf, encoding="UTF-8", xml_declaration=True)
    out = buf.getvalue().decode("utf-8")
    out = out.replace("<?xml version='1.0' encoding='UTF-8'?>\n",
                      "<?xml version='1.0' encoding='UTF-8'?>", 1)
    return re.sub(r'"\s+/>', '"/>', out)


def make_association(relationship, uid, entity_id=None):
    if relationship == "Assignee":
        etype = "urn:elli:encompass:role"
        eid = ROLE_IDS.get(uid, "") if entity_id is None else entity_id
    else:
        etype = "urn:elli:encompass:" + relationship
        eid = str(uuid.uuid4()) if entity_id is None else entity_id
    el = ET.Element("association")
    el.set("entityId", eid)
    el.set("entityType", etype)
    el.set("entityUID", uid)
    el.set("relationship", relationship)
    return el


def subtask_label(stype):
    """The user-facing tail of a subtask type: 'Task – Foo' -> 'Foo'."""
    return stype.split("–")[-1].split(" - ")[-1].strip()


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def guess_owner(uid, subtask_types):
    """Match a task-level workspace override to the subtask that owns it.

    Exported files carry each override twice — once on the task, once on its
    subtask, sharing an entityId — so a task-level override in the diff implies
    an owning subtask. Name matching finds most of them; the rest need --map.
    """
    target = set(_norm(uid).split())
    best, best_score = None, 0.0
    for stype in subtask_types:
        label = set(_norm(subtask_label(stype)).split())
        if not label:
            continue
        overlap = len(target & label) / max(len(target), len(label))
        if overlap > best_score:
            best, best_score = stype, overlap
    return best if best_score >= 0.6 else None


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

def adopt(ttype, rows, payload, explicit_map, dry_run, warn):
    repo_detail = payload["repo_tasks_detail"].get(ttype)
    enc_detail = payload["encompass_tasks_detail"].get(ttype)
    if repo_detail is None or enc_detail is None:
        raise SystemExit(f"{ttype}: not present on both sides — nothing to adopt")

    path = repo_detail["file"]
    tree = ET.parse(path)
    task = tree.getroot().find("taskTemplate")
    changes = []

    # --- task attributes ----------------------------------------------------
    for r in rows:
        if r["scope"] != "task" or r["status"] != "BOTH":
            continue
        task.set(r["field"], r["encompass_value"])
        changes.append(f"attr {r['field']}: {r['repo_value']!r} -> {r['encompass_value']!r}")
        if r["field"] == "taskGroupTemplateName":
            if r["encompass_value"]:
                gid = GROUP_IDS.get(r["encompass_value"])
                if gid is None:
                    raise SystemExit(
                        f"{ttype}: no known taskGroupTemplateId for group "
                        f"{r['encompass_value']!r} — add it to GROUP_IDS first")
                task.set("taskGroupTemplateId", gid)
                changes.append(f"taskGroupTemplateId -> {gid}")
            else:
                # ungrouped in Encompass: drop both halves, not just the label
                task.attrib.pop("taskGroupTemplateName", None)
                task.attrib.pop("taskGroupTemplateId", None)
                changes.append("taskGroupTemplateName/Id removed (ungrouped in Encompass)")

    subs_parent = task.find("subTaskTemplates")
    if subs_parent is None:
        subs_parent = ET.SubElement(task, "subTaskTemplates")
    by_stype = {s.get("type"): s for s in subs_parent.findall("subTaskTemplate")}
    sibling = next(iter(by_stype.values()), None)

    # --- subtask removals and description rewrites --------------------------
    for r in rows:
        if r["scope"] == "subtask" and r["status"] == "REPO_ONLY":
            el = by_stype.pop(r["field"], None)
            if el is not None:
                subs_parent.remove(el)
                changes.append(f"- subtask {r['field']}")
        elif r["scope"] == "subtask_description" and r["status"] == "BOTH":
            by_stype[r["field"]].set("description", r["encompass_value"])
            changes.append(f"~ description {r['field']}")

    # --- subtasks Encompass has and the repo does not -----------------------
    for r in rows:
        if r["scope"] != "subtask" or r["status"] != "ENCOMPASS_ONLY":
            continue
        stype = r["field"]
        el = ET.Element("subTaskTemplate")
        el.set("id", str(uuid.uuid4()))
        el.set("name", subtask_label(stype) or "Sub-Task Name")
        el.set("description", r["encompass_value"])
        el.set("type", stype)
        el.set("required", "true")
        el.set("priority", "1")
        el.set("rank", "1")
        el.set("created", args_now())
        el.set("createdBy", "agent_claude")
        el.set("lastModified", args_now())
        el.set("lastModifiedBy", "agent_claude")
        # match whatever the file already does about this forbidden-but-present attr
        if sibling is not None and sibling.get("taskTemplateId"):
            el.set("taskTemplateId", task.get("id"))
        el.set("autoCreate", "true")
        el.set("category", "Regular")
        subs_parent.append(el)
        by_stype[stype] = el
        changes.append(f"+ subtask {stype}")
        warn(f"{ttype}: new subtask {stype!r} — autoCreate/category are not recorded "
             f"in the diff, defaulted to autoCreate=true/Regular")

    # --- order and rank -----------------------------------------------------
    enc_order = enc_detail["subs"]
    if set(enc_order) != set(by_stype):
        raise SystemExit(
            f"{ttype}: subtask sets disagree after applying deltas — "
            f"only in Encompass: {sorted(set(enc_order) - set(by_stype))}, "
            f"only in repo: {sorted(set(by_stype) - set(enc_order))}")
    for el in list(subs_parent):
        subs_parent.remove(el)
    for i, stype in enumerate(enc_order, 1):
        el = by_stype[stype]
        if el.get("rank") != str(i):
            changes.append(f"~ rank {stype}: {el.get('rank')} -> {i}")
        el.set("rank", str(i))
        if el.get("required") != "true":
            el.set("required", "true")
            changes.append(f"~ required {stype}: false -> true (docs/conventions.md)")
        subs_parent.append(el)

    # --- associations -------------------------------------------------------
    assocs = task.find("associations")
    if assocs is None:
        assocs = ET.Element("associations")
        task.insert(0, assocs)
    kept = list(assocs.findall("association"))

    for r in rows:
        if r["scope"] != "association" or r["status"] != "REPO_ONLY":
            continue
        for el in list(kept):
            if el.get("relationship") == r["field"] and el.get("entityUID") == r["repo_value"]:
                kept.remove(el)
                changes.append(f"- association {r['field']}={r['repo_value']}")

    for r in rows:
        if r["scope"] != "association" or r["status"] != "ENCOMPASS_ONLY":
            continue
        rel, uid = r["field"], r["encompass_value"]
        if rel == "Assignee":
            eid = ROLE_IDS.get(uid, "")
            if not eid:
                warn(f"{ttype}: assignee role {uid!r} has no known system id — wrote "
                     f'entityId="". Read the integer off a live export before importing.')
        else:
            eid = str(uuid.uuid4())
        kept.append(make_association(rel, uid, eid))
        changes.append(f"+ association {rel}={uid}")

        if rel == "Assignee" or rel == "workspace":
            continue
        owner = explicit_map.get(uid) or guess_owner(uid, enc_order)
        if owner is None:
            warn(f"{ttype}: could not match override {uid!r} to a subtask — left at task "
                 f"level only. Pass --map {uid!r}=<subtask type> if it belongs to one.")
            continue
        sub = by_stype[owner]
        sa = sub.find("associations")
        if sa is None:
            sa = ET.SubElement(sub, "associations")
        sa.append(make_association(rel, uid, eid))
        changes.append(f"  ^ attached to subtask {owner}")

    # Task-level list mirrors the subtask associations, in subtask order.
    def bucket(el):
        rel = el.get("relationship")
        return 0 if rel == "Assignee" else 1 if rel == "workspace" else 2

    head = sorted([e for e in kept if bucket(e) < 2], key=bucket)
    for el in list(assocs):
        assocs.remove(el)
    for el in head:
        assocs.append(el)
    seen = set()
    for stype in enc_order:
        for sa in by_stype[stype].findall("./associations/association"):
            assocs.append(make_association(
                sa.get("relationship"), sa.get("entityUID"), sa.get("entityId")))
            seen.add((sa.get("relationship"), sa.get("entityUID"), sa.get("entityId")))
    for el in kept:
        key = (el.get("relationship"), el.get("entityUID"), el.get("entityId"))
        if bucket(el) == 2 and key not in seen:
            assocs.append(el)
    if not list(assocs):
        task.remove(assocs)

    if not dry_run:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(serialize(tree))
    return path, changes


_NOW = None


def args_now():
    return _NOW


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

def verify(types, payload, rows):
    """Re-read the written XML and assert every recorded delta now matches Encompass."""
    failures = []
    for ttype in types:
        path = payload["repo_tasks_detail"][ttype]["file"]
        task = ET.parse(path).getroot().find("taskTemplate")
        subs = {s.get("type"): s for s in task.findall(".//subTaskTemplate")}
        assoc = {(a.get("relationship"), a.get("entityUID"))
                 for a in task.findall("./associations/association")}
        for r in rows:
            if r["task_type"] != ttype:
                continue
            sc, st, f = r["scope"], r["status"], r["field"]
            ev, rv = r["encompass_value"], r["repo_value"]
            if sc == "task" and st == "BOTH":
                if (task.get(f) or "") != ev:
                    failures.append(f"{ttype} attr {f}: want {ev!r} got {task.get(f)!r}")
            elif sc == "subtask" and st == "ENCOMPASS_ONLY":
                if f not in subs:
                    failures.append(f"{ttype} subtask {f}: missing")
                elif subs[f].get("description") != ev:
                    failures.append(f"{ttype} subtask {f}: description mismatch")
            elif sc == "subtask" and st == "REPO_ONLY":
                if f in subs:
                    failures.append(f"{ttype} subtask {f}: should have been removed")
            elif sc == "subtask_description":
                if (subs[f].get("description") or "").strip() != ev:
                    failures.append(f"{ttype} description {f}: want {ev!r}")
            elif sc == "subtask_rank":
                if subs[f].get("rank") != ev:
                    failures.append(f"{ttype} rank {f}: want {ev} got {subs[f].get('rank')}")
            elif sc == "association" and st == "ENCOMPASS_ONLY":
                if (f, ev) not in assoc:
                    failures.append(f"{ttype} association {f}={ev}: missing")
            elif sc == "association" and st == "REPO_ONLY":
                if (f, rv) in assoc:
                    failures.append(f"{ttype} association {f}={rv}: should have been removed")

        enc_order = payload["encompass_tasks_detail"][ttype]["subs"]
        got = [s.get("type") for s in task.findall(".//subTaskTemplate")]
        if got != enc_order:
            failures.append(f"{ttype}: subtask order does not match Encompass")
        ranks = [s.get("rank") for s in task.findall(".//subTaskTemplate")]
        if ranks != [str(i) for i in range(1, len(got) + 1)]:
            failures.append(f"{ttype}: ranks are not 1..N -> {ranks}")
    return failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    global _NOW
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--types", nargs="+", required=True,
                   help="Task types to adopt the Encompass side of.")
    p.add_argument("--map", action="append", default=[], metavar="UID=SUBTASK_TYPE",
                   help="Force a workspace override onto a specific subtask. Repeatable.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the planned changes without writing.")
    p.add_argument("--verify", action="store_true",
                   help="Skip applying; just check the current files against the diff.")
    p.add_argument("--timestamp", default="2026-07-27T00:00:00.000Z",
                   help="created/lastModified stamp for new subtasks.")
    p.add_argument("--json", action="store_true", help="Machine-readable output.")
    args = p.parse_args(argv)
    _NOW = args.timestamp

    for f in (DELTAS_CSV, PAGE_HTML):
        if not os.path.exists(f):
            print(json.dumps({"ok": False, "error": f"missing {f} — run compare_configured.py"}))
            return 1

    payload = load_payload()
    rows = load_rows(set(args.types))
    if not rows:
        print(json.dumps({"ok": False, "error": "no delta rows for those types — "
                                                "already reconciled, or wrong type key"}))
        return 1

    explicit = {}
    for m in args.map:
        uid, _, stype = m.partition("=")
        explicit[uid] = stype

    warnings = []
    if args.verify:
        failures = verify(args.types, payload, rows)
    else:
        touched = []
        for ttype in args.types:
            trows = [r for r in rows if r["task_type"] == ttype]
            path, changes = adopt(ttype, trows, payload, explicit,
                                  args.dry_run, warnings.append)
            touched.append({"type": ttype, "file": path, "changes": changes})
            if not args.json:
                print(f"\n{ttype}  ->  {path}")
                for c in changes:
                    print(f"    {c}")
        failures = [] if args.dry_run else verify(args.types, payload, rows)

    if warnings and not args.json:
        print("\nwarnings:")
        for w in warnings:
            print(f"  ! {w}")
    if failures and not args.json:
        print("\nUNRESOLVED DELTAS:")
        for f in failures:
            print(f"  x {f}")

    ok = not failures
    if args.json:
        print(json.dumps({"ok": ok, "types": args.types, "rows": len(rows),
                          "warnings": warnings, "failures": failures}, indent=1))
    elif not args.dry_run:
        print(f"\n{len(rows)} recorded delta(s) checked — "
              f"{'all resolved' if ok else str(len(failures)) + ' unresolved'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
