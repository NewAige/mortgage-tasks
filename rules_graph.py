#!/usr/bin/env python3
"""
rules_graph.py - Build the rules interaction graph (rules/graph.json).

Reads the parsed workflow rules plus the task templates and joins them into one node/edge
graph that every "rules map" view renders. The graph is generated, never hand-edited; the
only hand-maintained inputs are rules/field_labels.csv and rules/annotations.json (both
optional - missing labels fall back to raw ids and never fail the build).

Inputs
  rules/rules.json            parsed rules + timers index        (parse_rules.py)
  tasks/**/*.xml              task + subtask display names, autoCreate
  roadmap.json                stage + status of each task XML
  docs/rules_crossref.json    broken-reference flags             (rules_crossref.py)
  rules/field_labels.csv      field id -> plain-English label
  rules/annotations.json      milestone stages, notification / service-rule labels

Output
  rules/graph.json            {generatedAt, generatedFrom, coverage, nodes[], edges[]}

Node kinds   rule, taskType, subtaskType, field, timer, document, milestone, external, entry
Edge kinds   triggers      event source -> rule
             effects       rule -> target (task / subtask / field / timer / external action)
             cancels       rule -> timer
             contains      taskType -> subtaskType (from the XML, with autoCreate)
             conditionReads field (or document) -> rule, from [FIELD] tokens in condition scripts
             enters        entry (user / loan_created) -> node whose event is driven from outside
                           the rules (a user completing a subtask, an edit, a file attached ...)

Every edge carries a plain-English `sentence`. Flags (always present on the edges they apply to):
  openEffect   an effect produces an event no active rule listens to
                 (only task:create / task:complete / subtask:complete / field:update / timer:start)
  openTrigger  a rule listens for an event nothing known produces (no rule, not user-driven)
  brokenRef    the edge touches a type rules_crossref.py could not resolve in tasks/
  inactive     the owning rule is not ACTIVE
Listeners and producers are worked out over ACTIVE rules only.

Output is deterministic: sorted keys, sorted lists, ids derived from rule ids / type keys, and
`generatedAt` copied from rules.json (never the wall clock).

Usage (paths default relative to this file):
    python rules_graph.py
    python rules_graph.py --json

Return value (stdout, or JSON with --json):
    {"ok": true, "nodes": N, "edges": N, ...}
    {"ok": false, "error": "<message>"}

Exit codes: 0 = success, 1 = error.
"""

import argparse
import csv
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from xml.etree import ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
DASH = "–"

EXTERNAL_KINDS = OrderedDict([
    ("notification:send", ("notification", "Notification")),
    ("role:assign", ("role", "Role assignment")),
    ("enhancedcondition:create", ("condition", "Condition")),
    ("enhancedcondition:updatetracking", ("condition", "Condition")),
    ("order:create", ("order", "Service order")),
    ("folder:move", ("folder", "Folder move")),
    ("disclosure:send", ("disclosure", "Disclosure package")),
    ("document:sendrequest", ("docRequest", "Document request")),
])
EXTERNAL_LABELS = dict(EXTERNAL_KINDS.values())
EVENT_SOURCE_EFFECTS = ("task:create", "task:complete", "subtask:complete", "field:update", "timer:start")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rel(path):
    try:
        return os.path.relpath(path, ROOT).replace(os.sep, "/")
    except ValueError:
        return path


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def norm_field(raw):
    """Same variant-merging as rules/field_labels.csv: `#16` -> `16`, `cx.x` -> `CX.X`."""
    f = (raw or "").strip()
    if re.match(r"^#\d+$", f):
        f = f[1:]
    if f.lower().startswith("cx."):
        f = f.upper()
    return f


def humanise(type_key):
    """Fallback display name for a task type we have no template for."""
    if (type_key or "").startswith("auto_"):
        return "Unknown task (Encompass ID %s)" % type_key[5:13]
    parts = [x for x in (type_key or "").split("_") if x]
    if len(parts) < 2:
        return type_key
    # drop the stage prefix; keep the rest so "PreClosing_Fraud_X_Report" -> "Fraud X Report"
    return " ".join(re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", x) for x in parts[1:])


def uniq_sorted(seq):
    return sorted(set(seq))


def join_and(items, word="and"):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " %s %s" % (word, items[-1])


def short_id(s):
    return (s or "")[:8]


# ---------------------------------------------------------------------------
# Loading the inputs
# ---------------------------------------------------------------------------

def load_templates(tasks_dir, roadmap):
    """Return (tasks, file_info). tasks: type -> dict(name, file, subtasks[ordered])."""
    road_by_file, road_meta = {}, {}
    for stage in roadmap.get("stages", []):
        for t in stage.get("tasks", []):
            if t.get("xmlFile"):
                road_by_file[t["xmlFile"]] = (stage.get("id"), t)
    tasks = OrderedDict()
    files = sorted(glob.glob(os.path.join(tasks_dir, "**", "*.xml"), recursive=True))
    for path in files:
        rp = rel(path)
        root = ET.parse(path).getroot()
        stage_id, rt = road_by_file.get(rp, (None, None))
        if stage_id is None:
            m = re.match(r"^tasks/([^/]+)/", rp)
            stage_id = m.group(1) if m else None
        for tt in root.iter("taskTemplate"):
            ttype = tt.get("type")
            if not ttype or ttype in tasks:
                continue
            subs = []
            seen = set()
            for st in tt.iter("subTaskTemplate"):
                if st.get("type") in seen:
                    continue
                seen.add(st.get("type"))
                subs.append(OrderedDict([("type", st.get("type")), ("name", st.get("name") or ""),
                                         ("autoCreate", st.get("autoCreate") == "true"),
                                         ("category", st.get("category") or "")]))
            tasks[ttype] = OrderedDict([
                ("name", tt.get("name") or ttype), ("file", rp), ("stage", stage_id),
                ("status", rt.get("status") if rt else None),
                ("roadmapId", rt.get("id") if rt else None),
                ("autoCreate", tt.get("autoCreate") == "true"), ("subtasks", subs)])
    return tasks, files


def load_field_labels(path):
    labels, rows, labelled = {}, 0, 0
    if os.path.isfile(path):
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                rows += 1
                fid = norm_field(row.get("field_id"))
                lab = (row.get("label") or "").strip()
                if fid and lab:
                    labels[fid] = lab
                    labelled += 1
    return labels, rows, labelled


def load_annotations(path):
    ann = {"milestones": {}, "notifications": {}, "serviceRules": {}}
    present = os.path.isfile(path)
    if present:
        try:
            raw = load_json(path)
        except (OSError, ValueError):
            raw = {}
        for k in ann:
            v = raw.get(k) if isinstance(raw, dict) else None
            if isinstance(v, dict):
                ann[k] = v
    return ann, present


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def node(self, nid, kind, label, **attrs):
        n = self.nodes.get(nid)
        if n is None:
            n = {"id": nid, "kind": kind, "label": label}
            self.nodes[nid] = n
        for k, v in attrs.items():
            if v is not None or k not in n:
                n[k] = v
        return n

    def edge(self, eid, kind, source, target, **attrs):
        e = {"id": eid, "kind": kind, "source": source, "target": target}
        e.update(attrs)
        self.edges[eid] = e
        return e


def task_nid(t):
    return "task:" + t


def sub_nid(t, s):
    return "subtask:%s|%s" % (t, s)


def build(args):
    rj = load_json(args.rules)
    rules = rj["rules"]
    timers_idx = rj.get("timers", {})
    roadmap = load_json(args.roadmap) if os.path.isfile(args.roadmap) else {"stages": []}
    xref = load_json(args.crossref) if os.path.isfile(args.crossref) else {}
    labels, label_rows, label_filled = load_field_labels(args.labels)
    ann, ann_present = load_annotations(args.annotations)
    tasks, xml_files = load_templates(args.tasks_dir, roadmap)

    G = Graph()
    rules_by_id = OrderedDict((r["id"], r) for r in sorted(rules, key=lambda r: (r["name"], r["id"])))

    # ---- required-field names carried inside rule conditions (label fallback) -------------
    cond_field_names = {}
    for r in rules:
        for c in list(r.get("conditions", [])) + [x for p in r["processes"] for x in p.get("conditions", [])]:
            for f in c.get("requiredFields", []) or []:
                if f.get("fieldId") and f.get("fieldName"):
                    cond_field_names.setdefault(norm_field(f["fieldId"]), f["fieldName"])

    def field_label(fid):
        if labels.get(fid):
            return labels[fid], "csv"
        alt = fid.lstrip("#")
        if labels.get(alt):
            return labels[alt], "csv"
        if cond_field_names.get(fid):
            return cond_field_names[fid], "rule"
        return fid, "id"

    # ---- crossref broken references ---------------------------------------------------------
    broken_task = {}     # task type -> {class, closest, rules}
    broken_sub = {}      # (task, sub) -> {...}
    for b in xref.get("brokenTasks", []):
        broken_task[b["task"]] = {"class": "task-missing", "closest": b.get("closest"),
                                  "rules": uniq_sorted(r["rule"] for r in b.get("refs", []))}
    for b in xref.get("brokenSubtasks", []):
        broken_sub[(b["task"], b["subtask"])] = {
            "class": b.get("class"), "closest": b.get("closest"), "detail": b.get("detail"),
            "rules": uniq_sorted(r["rule"] for r in b.get("refs", []))}
    anomalies_by_rule = defaultdict(list)
    for key, names in (xref.get("anomalies") or {}).items():
        for nm in names:
            anomalies_by_rule[nm.split(":")[0].strip()].append(key)

    # ---- task / subtask nodes from templates -----------------------------------------------
    for ttype, t in tasks.items():
        G.node(task_nid(ttype), "taskType", t["name"], type=ttype, stage=t["stage"], status=t["status"],
               xmlFile=t["file"], roadmapId=t["roadmapId"], inRepo=True, labelSource="xml")
        for s in t["subtasks"]:
            G.node(sub_nid(ttype, s["type"]), "subtaskType", "%s %s %s" % (t["name"], DASH, s["name"]),
                   type=s["type"], taskType=ttype, shortLabel=s["name"], stage=t["stage"],
                   autoCreate=s["autoCreate"], inRepo=True, labelSource="xml")
            G.edge("contains:%s|%s" % (ttype, s["type"]), "contains", task_nid(ttype), sub_nid(ttype, s["type"]),
                   autoCreate=s["autoCreate"], ruleId=None, processId=None, resolution=None, conditions="",
                   sentence="%s includes the subtask %s (%s)." % (
                       t["name"], s["name"],
                       "added automatically when the task is created" if s["autoCreate"]
                       else "only added when a rule or a condition calls for it"),
                   brokenRef=False, inactive=False)

    def ensure_task(ttype):
        nid = task_nid(ttype)
        if nid not in G.nodes:
            is_uuid = bool(re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-", ttype))
            G.node(nid, "taskType", humanise(ttype), type=ttype, stage=None, status=None,
                   xmlFile=None, roadmapId=None, inRepo=False, labelSource="uuid" if is_uuid else "derived")
        return nid

    def ensure_sub(ttype, stype):
        ensure_task(ttype)
        nid = sub_nid(ttype, stype)
        if nid not in G.nodes:
            parent = G.nodes[task_nid(ttype)]
            short = stype.split(" " + DASH + " ", 1)[-1] if (" " + DASH + " ") in stype else stype
            G.node(nid, "subtaskType", stype, type=stype, taskType=ttype, shortLabel=short,
                   stage=parent.get("stage"), autoCreate=None, inRepo=False, labelSource="type")
        return nid

    def ensure_field(fid):
        fid = norm_field(fid)
        nid = "field:" + fid
        if nid not in G.nodes:
            lab, src = field_label(fid)
            G.node(nid, "field", lab, fieldId=fid, stage=None, labelSource=src)
        return nid

    def ensure_timer(tid, name=None):
        nid = "timer:" + tid
        if nid not in G.nodes:
            meta = timers_idx.get(tid, {})
            G.node(nid, "timer", meta.get("name") or name or short_id(tid), timerId=tid, stage=None,
                   startedBy=meta.get("startedBy", []), cancelledBy=meta.get("cancelledBy", []),
                   onCompleteRules=meta.get("onCompleteRules", []),
                   labelSource="timer" if (meta.get("name") or name) else "id")
        return nid

    def ensure_document(title):
        nid = "document:" + title
        if nid not in G.nodes:
            G.node(nid, "document", title, title=title, stage=None, labelSource="title")
        return nid

    def ensure_milestone(title):
        nid = "milestone:" + title
        if nid not in G.nodes:
            a = ann["milestones"].get(title) or {}
            G.node(nid, "milestone", title, title=title, stage=a.get("stage"),
                   stageConfirmed=bool(a.get("confirmed")) if a else None,
                   labelSource="title")
        return nid

    def ensure_external(kind):
        nid = "external:" + kind
        if nid not in G.nodes:
            G.node(nid, "external", EXTERNAL_LABELS[kind], externalKind=kind, stage=None, labelSource="kind")
        return nid

    ENTRY_LABELS = {"loan_created": "Loan created", "user": "A user (or integration)"}

    def ensure_entry(name):
        nid = "entry:" + name
        if nid not in G.nodes:
            G.node(nid, "entry", ENTRY_LABELS[name], entryKind=name, stage=None, labelSource="kind")
        return nid

    # ---- 1. trigger specs (one per source value of each rule) ------------------------------
    specs = []   # dicts: rule, event, source (node id), task, sub, resolutions, field, values, timer
    for rid, r in rules_by_id.items():
        m = r.get("match", {})
        ev = r["eventSlug"]
        res = list(m.get("resolutions", []))
        base = {"rule": r, "event": ev, "resolutions": res}
        mine = []
        if ev == "subtask_completed":
            for t in m.get("taskType", []) or [None]:
                for s in m.get("subtaskType", []) or [None]:
                    if t and s:
                        mine.append(dict(base, task=t, sub=s, source=ensure_sub(t, s)))
                    elif t:
                        mine.append(dict(base, task=t, sub=None, source=ensure_task(t)))
        elif ev in ("task_created", "task_completed"):
            for t in m.get("taskType", []):
                mine.append(dict(base, task=t, source=ensure_task(t)))
        elif ev == "field_modified":
            for f in m.get("fields", []):
                nf = norm_field(f)
                vals = [fv for fv in m.get("fieldValues", []) if norm_field(fv["field"]) == nf]
                mine.append(dict(base, field=nf, values=vals, source=ensure_field(nf)))
        elif ev == "file_attached":
            for title in m.get("documentTitles", []):
                mine.append(dict(base, document=title, source=ensure_document(title)))
        elif ev == "milestone_completed":
            for title in m.get("milestones", []):
                mine.append(dict(base, milestone=title, source=ensure_milestone(title)))
        elif ev == "timer_completed":
            for tid in m.get("timerIds", []):
                mine.append(dict(base, timer=tid, source=ensure_timer(tid)))
        elif ev == "loan_created":
            mine.append(dict(base, source=ensure_entry("loan_created")))
        if not mine:   # rule with a filter we could not turn into a node: hang it off "user"
            mine.append(dict(base, source=ensure_entry("user"), unresolved=True))
        specs.extend(mine)

    specs_by_rule = defaultdict(list)
    for sp in specs:
        specs_by_rule[sp["rule"]["id"]].append(sp)
    active_specs = [sp for sp in specs if sp["rule"]["status"] == "ACTIVE"]

    # ---- 2. effect targets -------------------------------------------------------------------
    def effect_target(e):
        k = e["kind"]
        if k in ("task:create", "task:complete"):
            return ensure_task(e["taskType"])
        if k in ("subtask:create", "subtask:complete"):
            return ensure_sub(e["taskType"], e["subtaskType"])
        if k == "field:update":
            return ensure_field(e["field"])
        if k in ("timer:start", "timer:cancel"):
            return ensure_timer(e["timerId"], e.get("timerName"))
        return ensure_external(EXTERNAL_KINDS[k][0])

    # ---- 3. who listens to an effect / who produces a trigger ----------------------------------
    def value_matches(vals, value):
        if not vals:
            return True
        v = (value or "")
        dynamic = bool(re.search(r"[()\[\]]", v))
        if dynamic:
            return True
        ok = False
        for fv in vals:
            op, want = fv.get("operator"), fv.get("value") or ""
            if op == "EQUAL_TO":
                ok = ok or v.casefold() == want.casefold()
            elif op == "NOT_EQUAL_TO":
                ok = ok or v.casefold() != want.casefold()
            else:
                ok = True
        return ok

    def res_matches(listener_res, produced):
        return (not listener_res) or produced is None or produced in listener_res

    def listeners_of(e):
        k, out = e["kind"], []
        for sp in active_specs:
            if k == "task:create" and sp["event"] == "task_created" and sp.get("task") == e["taskType"]:
                out.append(sp)
            elif k == "task:complete" and sp["event"] == "task_completed" and sp.get("task") == e["taskType"] \
                    and res_matches(sp["resolutions"], e.get("resolution")):
                out.append(sp)
            elif k == "subtask:complete" and sp["event"] == "subtask_completed" and sp.get("sub") == e["subtaskType"] \
                    and sp.get("task") == e["taskType"] and res_matches(sp["resolutions"], e.get("resolution")):
                out.append(sp)
            elif k == "field:update" and sp["event"] == "field_modified" \
                    and sp.get("field") == norm_field(e["field"]) and value_matches(sp.get("values"), e.get("value")):
                out.append(sp)
            elif k == "timer:start" and sp["event"] == "timer_completed" and sp.get("timer") == e["timerId"]:
                out.append(sp)
        return out

    active_effects = [(r, e) for r in rules_by_id.values() if r["status"] == "ACTIVE" for e in r["effects"]]

    def producers_of(sp):
        ev, out = sp["event"], []
        for r, e in active_effects:
            k = e["kind"]
            if ev == "task_created" and k == "task:create" and e["taskType"] == sp.get("task"):
                out.append(r)
            elif ev == "task_completed" and k == "task:complete" and e["taskType"] == sp.get("task") \
                    and res_matches(sp["resolutions"], e.get("resolution")):
                out.append(r)
            elif ev == "subtask_completed" and k == "subtask:complete" and sp.get("sub") \
                    and e["subtaskType"] == sp["sub"] and e["taskType"] == sp.get("task") \
                    and res_matches(sp["resolutions"], e.get("resolution")):
                out.append(r)
            elif ev == "field_modified" and k == "field:update" and norm_field(e["field"]) == sp["field"] \
                    and value_matches(sp.get("values"), e.get("value")):
                out.append(r)
            elif ev == "timer_completed" and k == "timer:start" and e["timerId"] == sp.get("timer"):
                out.append(r)
        return out

    # ---- sentence pieces -------------------------------------------------------------------------
    def nlabel(nid):
        n = G.nodes[nid]
        if n["kind"] == "field" and n["labelSource"] == "id":
            return "field " + n["label"]
        return n["label"]

    def res_phrase(res):
        if not res:
            return "completed"
        return "marked " + " or ".join(res)

    def trigger_phrase(sp):
        ev = sp["event"]
        if ev == "subtask_completed" and sp.get("sub"):
            return "%s is %s" % (nlabel(sp["source"]), res_phrase(sp["resolutions"]))
        if ev == "subtask_completed":
            return "a subtask of %s is %s" % (nlabel(sp["source"]), res_phrase(sp["resolutions"]))
        if ev == "task_created":
            return "%s is created" % nlabel(sp["source"])
        if ev == "task_completed":
            suffix = "" if not sp["resolutions"] else (" as %s" % " or ".join(sp["resolutions"]))
            return "%s is completed%s" % (nlabel(sp["source"]), suffix)
        if ev == "field_modified":
            vals = sp.get("values") or []
            tail = " changes"
            if vals:
                bits = []
                for fv in vals:
                    want = fv.get("value")
                    if fv.get("operator") == "EQUAL_TO":
                        bits.append('to "%s"' % want if want else "to empty")
                    elif fv.get("operator") == "NOT_EQUAL_TO":
                        bits.append('to something other than "%s"' % want if want else "to a value")
                tail = " changes " + " or ".join(bits) if bits else tail
            return "%s%s" % (nlabel(sp["source"]), tail)
        if ev == "file_attached":
            return "a file is attached to the %s document" % nlabel(sp["source"])
        if ev == "milestone_completed":
            return "the %s milestone is completed" % nlabel(sp["source"])
        if ev == "timer_completed":
            return "the %s timer runs out" % nlabel(sp["source"])
        if ev == "loan_created":
            return "a loan is created"
        return "the rule's event happens"

    def rule_trigger_phrase(rid):
        parts = uniq_sorted_keep(trigger_phrase(sp) for sp in specs_by_rule[rid])
        if len(parts) > 3:
            return "any of %d events (%s, ...) occurs" % (len(parts), parts[0])
        return join_and(parts, "or")

    def uniq_sorted_keep(seq):
        seen, out = set(), []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    def doc_titles(e):
        return [d.get("name") for d in e.get("documents", []) or [] if d.get("name")]

    def effect_phrase(e, tgt):
        k = e["kind"]
        if k == "task:create":
            return "Encompass creates the task %s" % nlabel(tgt)
        if k == "task:complete":
            r = e.get("resolution")
            how = {"NA": "closes the task %s as not applicable",
                   "Issue": "closes the task %s with an issue"}.get(r, "completes the task %s")
            return "Encompass " + how % nlabel(tgt)
        if k == "subtask:create":
            return "Encompass adds the subtask %s" % nlabel(tgt)
        if k == "subtask:complete":
            r = e.get("resolution")
            how = {"NA": "marks %s as not applicable", "Issue": "marks %s as Issue"}.get(r, "marks %s as Done")
            return "Encompass " + how % nlabel(tgt)
        if k == "timer:start":
            return "Encompass starts the %s timer" % nlabel(tgt)
        if k == "timer:cancel":
            return "Encompass cancels the %s timer" % nlabel(tgt)
        if k == "field:update":
            return 'Encompass sets %s to "%s"' % (nlabel(tgt), e.get("value", ""))
        if k == "notification:send":
            lab = (ann["notifications"].get(e.get("templateId")) or {}).get("label")
            return "Encompass sends the notification %s" % (
                '"%s"' % lab if lab else "(template %s)" % short_id(e.get("templateId")))
        if k == "role:assign":
            who = e.get("assignee") or "a user"
            return "Encompass assigns %s to the %s role" % (who, e.get("roleName") or e.get("roleId"))
        if k == "enhancedcondition:create":
            return 'Encompass adds the %s condition "%s"' % (e.get("conditionType"), e.get("title"))
        if k == "enhancedcondition:updatetracking":
            return 'Encompass sets the %s condition "%s" to %s' % (e.get("conditionType"), e.get("title"),
                                                                    e.get("status"))
        if k == "order:create":
            ids = [i.strip() for i in str(e.get("serviceRuleIds", "")).split(",") if i.strip()]
            labs = [(ann["serviceRules"].get(i) or {}).get("label") or "(service rule %s)" % short_id(i)
                    for i in ids]
            return "Encompass places the service order %s" % (join_and(labs) or "(unspecified)")
        if k == "folder:move":
            return 'Encompass moves the loan to the "%s" folder' % e.get("folderName")
        if k == "disclosure:send":
            return "Encompass sends a disclosure package"
        if k == "document:sendrequest":
            docs = doc_titles(e)
            return "Encompass sends %s to the borrower" % (join_and(docs) if docs else "documents")
        return "Encompass runs %s" % k

    # ---- condition text --------------------------------------------------------------------------
    TOKEN = re.compile(r"\[([^\[\]]+)\]")

    def humanise_script(script):
        def sub(m):
            raw = m.group(1)
            if raw.startswith("Document."):
                return "[%s]" % raw
            lab, src = field_label(norm_field(raw))
            return "[%s]" % lab if src != "id" else m.group(0)
        return TOKEN.sub(sub, script)

    def cond_text(c):
        t = c.get("type")
        if t == "script":
            return re.sub(r"\s+", " ", humanise_script(c.get("script", ""))).strip()
        if t == "originationChannels":
            return "loan channel is " + join_and(c.get("originationChannels", []), "or")
        if t == "requiredDocuments":
            return "documents present: " + join_and(d.get("title", "") for d in c.get("requiredDocuments", []))
        if t == "requiredTasks":
            return "tasks present: " + join_and(c.get("requiredTasks", []))
        if t == "requiredFields":
            return "fields filled: " + join_and(f.get("fieldName") or f.get("fieldId", "")
                                                 for f in c.get("requiredFields", []))
        return t or "condition"

    def cond_raw(c):
        return re.sub(r"\s+", " ", c.get("script") or "").strip() if c.get("type") == "script" else cond_text(c)

    # ---- 4. rule nodes ----------------------------------------------------------------------------
    for rid, r in rules_by_id.items():
        kinds = Counter(e["kind"] for e in r["effects"])
        G.node("rule:" + rid, "rule", r["name"], ruleId=rid, event=r["eventSlug"], eventName=r.get("eventName"),
               status=r["status"], inactive=r["status"] != "ACTIVE", invalid=bool(r.get("isInvalid")),
               description=r.get("description"), sourceFiles=sorted(r.get("sourceFiles", [])),
               xmlFile=r.get("xmlFile"), processCount=len(r["processes"]),
               effectKinds=dict(sorted(kinds.items())), anomalies=sorted(anomalies_by_rule.get(r["name"], [])),
               channels=sorted(set(ch for c in r.get("conditions", []) if c.get("type") == "originationChannels"
                                   for ch in c.get("originationChannels", []))),
               labelSource="rule")

    def broken_for(rule_name, node_ids):
        for nid in node_ids:
            n = G.nodes.get(nid)
            if not n:
                continue
            if n["kind"] == "taskType":
                b = broken_task.get(n["type"])
                if b and rule_name in b["rules"]:
                    return True
            elif n["kind"] == "subtaskType":
                b = broken_sub.get((n["taskType"], n["type"]))
                if b and rule_name in b["rules"]:
                    return True
        return False

    # ---- 5. triggers edges --------------------------------------------------------------------------
    user_driven = {}   # (node id, event) -> set of resolutions
    for rid, r in rules_by_id.items():
        for i, sp in enumerate(specs_by_rule[rid]):
            ev = sp["event"]
            prods = producers_of(sp) if ev in ("subtask_completed", "task_created", "task_completed",
                                               "field_modified", "timer_completed") else []
            driven = []
            if prods:
                driven.append("rule")
            if sp.get("unresolved"):
                driven.append("open")
            elif ev in ("subtask_completed", "field_modified", "task_completed"):
                driven.append("user")
                user_driven.setdefault((sp["source"], ev), set()).update(sp["resolutions"] or [])
            elif ev in ("file_attached", "milestone_completed"):
                driven.append("external")
                user_driven.setdefault((sp["source"], ev), set()).update(sp["resolutions"] or [])
            elif ev == "loan_created":
                driven.append("external")
            elif not prods:
                driven.append("open")
            open_trigger = driven == ["open"]
            sentence = "When %s, the rule %s runs." % (trigger_phrase(sp), '"%s"' % r["name"])
            if open_trigger:
                sentence += " Nothing known produces this yet (no known rule)."
            vals = [OrderedDict([("operator", fv.get("operator")), ("value", fv.get("value"))])
                    for fv in sp.get("values") or []]
            G.edge("triggers:%s:%d" % (rid, i), "triggers", sp["source"], "rule:" + rid,
                   ruleId=rid, ruleName=r["name"], event=ev, processId=None, resolution=None,
                   resolutions=sorted(sp["resolutions"]), valueFilter=vals, conditions="",
                   drivenBy=sorted(set(driven)), producedByRules=sorted(p["id"] for p in prods),
                   openTrigger=open_trigger, sentence=sentence,
                   brokenRef=broken_for(r["name"], [sp["source"]]), inactive=r["status"] != "ACTIVE")

    # ---- 6. effects / cancels edges ------------------------------------------------------------------
    rule_cond_raw, rule_cond_txt = {}, {}
    for rid, r in rules_by_id.items():
        rule_cond_raw[rid] = " AND ".join(cond_raw(c) for c in r.get("conditions", []))
        rule_cond_txt[rid] = [cond_text(c) for c in r.get("conditions", [])]
    for rid, r in rules_by_id.items():
        procs = {p["id"]: p for p in r["processes"]}
        tphrase = rule_trigger_phrase(rid)
        for idx, e in enumerate(r["effects"]):
            k = e["kind"]
            tgt = effect_target(e)
            p = procs.get(e.get("processId"), {})
            proc_raw = " AND ".join(cond_raw(c) for c in p.get("conditions", []))
            texts = rule_cond_txt[rid] + [cond_text(c) for c in p.get("conditions", [])]
            lis = listeners_of(e) if k in EVENT_SOURCE_EFFECTS else []
            open_effect = k in EVENT_SOURCE_EFFECTS and not lis
            sentence = "When %s, %s" % (tphrase, effect_phrase(e, tgt))
            if texts:
                sentence += " (only if %s)" % " and ".join(texts)
            sentence += "."
            attrs = dict(ruleId=rid, ruleName=r["name"], event=r["eventSlug"], effectIndex=idx, effect=k,
                         processId=e.get("processId"), processName=p.get("description"),
                         conditions=proc_raw, ruleConditions=rule_cond_raw[rid],
                         conditionsText=" and ".join(texts),
                         resolution=e.get("resolution"), openEffect=open_effect,
                         heardBy=sorted(set(sp["rule"]["id"] for sp in lis)), sentence=sentence,
                         brokenRef=broken_for(r["name"], [tgt] + [sp["source"] for sp in specs_by_rule[rid]]),
                         inactive=r["status"] != "ACTIVE")
            for opt in ("noDuplicate", "includeSubtask", "subtaskResolution", "reopenParentTask", "value",
                        "templateId", "roleId", "roleName", "assignee", "loanAssociateType", "conditionType",
                        "title", "status", "serviceRuleIds", "folderName", "borrowerPair"):
                if opt in e:
                    attrs[opt] = e[opt]
            if "documents" in e:
                attrs["documents"] = [d.get("name") for d in e["documents"]]
            if k == "notification:send":
                attrs["targetLabel"] = (ann["notifications"].get(e.get("templateId")) or {}).get("label")
            if k == "order:create":
                ids = [i.strip() for i in str(e.get("serviceRuleIds", "")).split(",") if i.strip()]
                attrs["targetLabel"] = join_and((ann["serviceRules"].get(i) or {}).get("label") or short_id(i)
                                                for i in ids) or None
            kind = "cancels" if k == "timer:cancel" else "effects"
            G.edge("%s:%s:%d" % (kind, rid, idx), kind, "rule:" + rid, tgt, **attrs)

    # ---- 7. condition reads ------------------------------------------------------------------------------
    for rid, r in rules_by_id.items():
        scopes = [(None, None, r.get("conditions", []))] + [(p["id"], p.get("description"), p.get("conditions", []))
                                                           for p in r["processes"]]
        for pid, pname, conds in scopes:
            seen = OrderedDict()
            for c in conds:
                if c.get("type") != "script":
                    continue
                for tok in TOKEN.findall(c.get("script", "")):
                    tok = tok.strip()
                    if tok.startswith("Document."):
                        parts = tok.split(".", 2)
                        title = parts[2] if len(parts) == 3 else tok
                        seen.setdefault(ensure_document(title), (c["script"], parts[1] if len(parts) == 3 else None))
                    else:
                        seen.setdefault(ensure_field(tok), (c["script"], None))
            for src, (script, docfield) in seen.items():
                where = ('before the "%s" step of the rule "%s" runs' % (pname, r["name"])) if pid \
                    else ('before the rule "%s" runs' % r["name"])
                what = ("the %s date of the %s document" % (docfield, nlabel(src))) if docfield \
                    else ("the loan field %s" % G.nodes[src]["label"])
                G.edge("conditionReads:%s:%s:%s" % (src, rid, pid or "rule"), "conditionReads", src, "rule:" + rid,
                       ruleId=rid, ruleName=r["name"], event=r["eventSlug"], processId=pid, processName=pname,
                       resolution=None, conditions=script, conditionsText=humanise_script(script),
                       via="document" if docfield else "field",
                       sentence="Encompass checks %s %s (condition: %s)." % (what, where, re.sub(r"\s+", " ", humanise_script(script)).strip()),
                       brokenRef=False, inactive=r["status"] != "ACTIVE")

    # ---- 8. enters edges (events driven from outside the rules) ---------------------------------------------
    for (nid, ev), ress in sorted(user_driven.items()):
        n = G.nodes[nid]
        res = sorted(ress)
        if ev == "subtask_completed":
            sent = "A user marks %s as %s." % (n["label"], " or ".join(res) if res else "complete")
        elif ev == "task_completed":
            sent = "A user completes the task %s." % n["label"]
        elif ev == "field_modified":
            sent = "A user (or an integration) changes %s." % n["label"]
        elif ev == "file_attached":
            sent = "A user (or an integration) attaches a file to the %s document." % n["label"]
        else:
            sent = "The %s milestone is completed in Encompass." % n["label"]
        G.edge("enters:user:%s:%s" % (nid, ev), "enters", ensure_entry("user"), nid, ruleId=None, event=ev,
               processId=None, resolution=None, resolutions=res, conditions="", sentence=sent,
               brokenRef=bool(n.get("brokenRef")), inactive=False)

    # ---- 9. node flags + stages -------------------------------------------------------------------------------
    for nid, n in G.nodes.items():
        if n["kind"] == "taskType":
            b = broken_task.get(n["type"])
            n["brokenRef"] = bool(b) or any(t == n["type"] for (t, _s) in broken_sub)
            if b:
                n["brokenClass"] = b["class"]
                n["closest"] = b["closest"]
        elif n["kind"] == "subtaskType":
            b = broken_sub.get((n["taskType"], n["type"]))
            n["brokenRef"] = bool(b) or (n["taskType"] in broken_task)
            if b:
                n["brokenClass"] = b["class"]
                n["closest"] = b["closest"]
    started = {t for r in rules_by_id.values() for e in r["effects"] if e["kind"] == "timer:start"
               for t in [e["timerId"]]}
    listened = {sp.get("timer") for sp in specs if sp["event"] == "timer_completed"}
    for nid, n in G.nodes.items():
        if n["kind"] == "timer":
            n["neverStarted"] = n["timerId"] not in started
            n["noCompletionRule"] = n["timerId"] not in listened
            n["inactive"] = False
    in_rule = defaultdict(list)
    for e in G.edges.values():
        if e["kind"] == "triggers":
            in_rule[e["ruleId"]].append(G.nodes[e["source"]].get("stage"))
        elif e["kind"] in ("effects", "cancels"):
            in_rule[e["ruleId"]].append(G.nodes[e["target"]].get("stage"))
    for rid in rules_by_id:
        st = [s for s in in_rule[rid] if s]
        G.nodes["rule:" + rid]["stage"] = Counter(sorted(st)).most_common(1)[0][0] if st else None

    # ---- 10. coverage + metadata -------------------------------------------------------------------------------
    nodes = [G.nodes[k] for k in sorted(G.nodes)]
    edges = [G.edges[k] for k in sorted(G.edges)]
    by_kind_n = Counter(n["kind"] for n in nodes)
    by_kind_e = Counter(e["kind"] for e in edges)
    open_eff = [e for e in edges if e.get("openEffect")]
    open_trig = [e for e in edges if e.get("openTrigger")]
    meta = rj.get("metadata", {})
    coverage = OrderedDict([
        ("nodesByKind", dict(sorted(by_kind_n.items()))),
        ("edgesByKind", dict(sorted(by_kind_e.items()))),
        ("nodeCount", len(nodes)), ("edgeCount", len(edges)),
        ("rules", len(rules_by_id)),
        ("activeRules", sum(1 for r in rules_by_id.values() if r["status"] == "ACTIVE")),
        ("inactiveRules", sum(1 for r in rules_by_id.values() if r["status"] != "ACTIVE")),
        ("rulesByEvent", dict(sorted(Counter(r["eventSlug"] for r in rules_by_id.values()).items()))),
        ("exports", len(meta.get("sourceFiles", []))),
        ("sourceFiles", sorted(meta.get("sourceFiles", []))),
        ("openEffects", len(open_eff)),
        ("openEffectsByKind", dict(sorted(Counter(e["effect"] for e in open_eff).items()))),
        ("effectsCheckedForOpen", sum(1 for e in edges if e["kind"] == "effects" and e["effect"] in EVENT_SOURCE_EFFECTS)),
        ("openTriggers", len(open_trig)),
        ("openTriggersByEvent", dict(sorted(Counter(e["event"] for e in open_trig).items()))),
        ("userDrivenTriggers", sum(1 for e in edges if e["kind"] == "triggers" and "user" in e["drivenBy"])),
        ("externalDrivenTriggers", sum(1 for e in edges if e["kind"] == "triggers" and "external" in e["drivenBy"])),
        ("brokenRefEdges", sum(1 for e in edges if e.get("brokenRef"))),
        ("brokenRefNodes", sum(1 for n in nodes if n.get("brokenRef"))),
        ("inactiveEdges", sum(1 for e in edges if e.get("inactive"))),
        ("taskTypesNotInRepo", sum(1 for n in nodes if n["kind"] == "taskType" and not n["inRepo"])),
        ("subtaskTypesNotInRepo", sum(1 for n in nodes if n["kind"] == "subtaskType" and not n["inRepo"])),
        ("fieldsWithoutLabel", sum(1 for n in nodes if n["kind"] == "field" and n["labelSource"] == "id")),
        ("milestonesWithoutStage", sum(1 for n in nodes if n["kind"] == "milestone" and not n.get("stage"))),
        ("notificationsWithoutLabel", len({e.get("templateId") for e in edges
                                           if e.get("effect") == "notification:send" and not e.get("targetLabel")})),
    ])
    gen_from = OrderedDict([
        ("script", "rules_graph.py"),
        ("rules", OrderedDict([("path", rel(args.rules)), ("sha256", sha256(args.rules)),
                               ("generatedAt", meta.get("generatedAt")), ("ruleCount", meta.get("ruleCount"))])),
        ("tasks", OrderedDict([("dir", rel(args.tasks_dir)), ("xmlFiles", len(xml_files)),
                               ("taskTypes", len(tasks))])),
        ("roadmap", OrderedDict([("path", rel(args.roadmap)),
                                 ("lastUpdated", (roadmap.get("metadata") or {}).get("lastUpdated"))])),
        ("crossref", OrderedDict([("path", rel(args.crossref)), ("present", bool(xref))])),
        ("fieldLabels", OrderedDict([("path", rel(args.labels)), ("rows", label_rows), ("labelled", label_filled)])),
        ("annotations", OrderedDict([("path", rel(args.annotations)), ("present", ann_present)])),
    ])
    graph = OrderedDict([("generatedAt", meta.get("generatedAt")), ("generatedFrom", gen_from),
                         ("coverage", coverage), ("nodes", nodes), ("edges", edges)])
    return graph, rules_by_id


def main():
    ap = argparse.ArgumentParser(description="Build the rules interaction graph (rules/graph.json).")
    ap.add_argument("--rules", default=os.path.join(ROOT, "rules", "rules.json"))
    ap.add_argument("--tasks-dir", default=os.path.join(ROOT, "tasks"))
    ap.add_argument("--roadmap", default=os.path.join(ROOT, "roadmap.json"))
    ap.add_argument("--crossref", default=os.path.join(ROOT, "docs", "rules_crossref.json"))
    ap.add_argument("--labels", default=os.path.join(ROOT, "rules", "field_labels.csv"))
    ap.add_argument("--annotations", default=os.path.join(ROOT, "rules", "annotations.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "rules", "graph.json"))
    ap.add_argument("--json", action="store_true", help="print a machine-readable summary")
    args = ap.parse_args()

    try:
        graph, _ = build(args)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(graph, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
        cov = graph["coverage"]
        summary = OrderedDict([
            ("ok", True), ("nodes", cov["nodeCount"]), ("edges", cov["edgeCount"]),
            ("nodes_by_kind", cov["nodesByKind"]), ("edges_by_kind", cov["edgesByKind"]),
            ("rules", cov["rules"]), ("open_effects", cov["openEffects"]),
            ("open_triggers", cov["openTriggers"]), ("broken_ref_edges", cov["brokenRefEdges"]),
            ("inactive_edges", cov["inactiveEdges"]), ("json", rel(args.out))])
    except Exception as exc:  # noqa: BLE001
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print("error: %s" % exc, file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print("Wrote %d nodes, %d edges (%d open effects, %d open triggers) -> %s"
              % (cov["nodeCount"], cov["edgeCount"], cov["openEffects"], cov["openTriggers"], rel(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
