#!/usr/bin/env python3
"""
parse_rules.py — Split Encompass workflow-automation exports into per-rule XML and a catalogue.

`rules/exports/Rules_*.xml` holds raw "eventTriggers" exports pulled out of Encompass
(Workflow Automation / event triggers). Each file wraps many <eventTrigger> elements. This
script de-duplicates them by <id> and regenerates, deterministically:

  1. rules/by_event/{event_slug}/{rule_name_slug}.xml
       One standalone, re-importable file per unique rule. The <eventTrigger> text is copied
       verbatim from the export (never re-serialised), wrapped in
       <?xml ...?><eventTriggers>...</eventTriggers>, inline.
  2. rules/rules.json
       Structured index: filters, conditions, processes/steps, derived `match` and `effects`,
       and a `timers` index (started / cancelled / completed-by).
  3. docs/RULES_CATALOG.md
       Human-readable catalogue (summary, task-type index, timer chains, one entry per rule).

Output is stable: rules are sorted, `generatedAt` is the newest rule `lastModified` (not the wall
clock), so re-running without changing the exports produces no diff.

Usage (run from anywhere; paths default relative to this file):
    python parse_rules.py
    python parse_rules.py --exports-dir rules/exports --out-dir rules/by_event \
        --out-json rules/rules.json --out-md docs/RULES_CATALOG.md
    python parse_rules.py --json

Return value (stdout, or JSON with --json):
    {"ok": true, "rules": N, "duplicates_removed": N, ...}
    {"ok": false, "error": "<message>"}

Exit codes: 0 = success, 1 = error.
"""

import argparse
import glob
import json
import os
import re
import shutil
import sys
from collections import OrderedDict, defaultdict
from xml.etree import ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
XML_DECL = "<?xml version='1.0' encoding='UTF-8'?>"
TRIGGER_RE = re.compile(r"<eventTrigger>.*?</eventTrigger>", re.S)

EVENT_SLUGS = {
    "urn:elli:task:event:subtask:completed": "subtask_completed",
    "urn:elli:task:event:task:created": "task_created",
    "urn:elli:task:event:task:completed": "task_completed",
    "urn:elli:encompass:event:loan:field:modified": "field_modified",
    "urn:elli:encompass:event:loan:file:attached": "file_attached",
    "urn:elli:encompass:event:loan:milestone:completed": "milestone_completed",
    "urn:elli:encompass:event:loan:created": "loan_created",
    "urn:elli:timer:event:timer:completed": "timer_completed",
}
EVENT_TITLES = {
    "subtask_completed": "Subtask completed",
    "task_created": "Task created",
    "task_completed": "Task completed",
    "field_modified": "Loan field modified",
    "file_attached": "File attached",
    "milestone_completed": "Milestone completed",
    "loan_created": "Loan created",
    "timer_completed": "Timer completed",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")
    return s or "unnamed"


def event_slug(urn):
    if urn in EVENT_SLUGS:
        return EVENT_SLUGS[urn]
    parts = [p for p in (urn or "").split(":") if p]
    return slugify("_".join(parts[-3:-1] + parts[-1:])) if parts else "unknown"


def rel(path):
    try:
        return os.path.relpath(path, ROOT).replace(os.sep, "/")
    except ValueError:
        return path.replace(os.sep, "/")


def to_bool(text):
    return (text or "").strip().lower() == "true"


def elem_to_value(el):
    """Leaf -> text; branch -> dict (repeated child tags become lists)."""
    kids = list(el)
    if not kids:
        return el.text or ""
    out = OrderedDict()
    for k in kids:
        v = elem_to_value(k)
        if k.tag in out:
            if not isinstance(out[k.tag], _Multi):
                out[k.tag] = _Multi([out[k.tag]])
            out[k.tag].append(v)
        else:
            out[k.tag] = v
    return OrderedDict((k, list(v) if isinstance(v, _Multi) else v) for k, v in out.items())


class _Multi(list):
    pass


def field_of(object_value):
    m = re.match(r"^/fields/(.+)$", object_value or "")
    return m.group(1) if m else None


def uniq(seq):
    seen, out = set(), []
    for x in seq:
        key = json.dumps(x, sort_keys=True) if not isinstance(x, str) else x
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def action_slug(urn):
    parts = (urn or "").split(":")
    return ":".join(parts[-2:]) if len(parts) >= 2 else urn


# ---------------------------------------------------------------------------
# Parsing one eventTrigger
# ---------------------------------------------------------------------------

def parse_term(term):
    d = OrderedDict()
    d["variable"] = term.findtext("variable")
    d["operator"] = term.findtext("operator")
    vals = term.find("values")
    if vals is not None:
        d["values"] = [v.text or "" for v in vals.findall("values")] or [vals.text or ""]
    elif term.find("value") is not None:
        d["value"] = term.findtext("value") or ""
    ov = term.findtext("objectValue")
    if ov is not None:
        f = field_of(ov)
        if f is not None:
            d["field"] = f
        d["objectKey"] = term.findtext("objectKey")
        d["objectValue"] = ov
    if term.find("type") is not None:
        d["type"] = term.findtext("type")
    return d


def parse_filters(trig):
    out = []
    for ef in trig.findall("./eventFilters/eventFilter"):
        out.append(OrderedDict([
            ("operator", ef.findtext("operator")),
            ("terms", [parse_term(t) for t in ef.findall("./terms/term")]),
        ]))
    return out


def parse_conditions(parent):
    out = []
    for c in parent.findall("./conditions/condition"):
        d = OrderedDict([("type", c.findtext("type"))])
        p = c.find("parameters")
        if p is not None:
            if p.find("script") is not None:
                d["script"] = p.findtext("script") or ""
            for tag in ("id", "operator", "value"):
                if p.find(tag) is not None:
                    d["field" if tag == "id" else tag] = p.findtext(tag)
            if p.find("requiredTasks") is not None:
                d["requiredTasks"] = [
                    r.findtext("type") for r in p.findall("requiredTasks")]
            if p.find("requiredDocuments") is not None:
                d["requiredDocuments"] = [
                    OrderedDict([("title", r.findtext("title")),
                                 ("isAttachmentRequired", to_bool(r.findtext("isAttachmentRequired")))])
                    for r in p.findall("requiredDocuments")]
            if p.find("originationChannels") is not None:
                d["originationChannels"] = [
                    o.text or "" for o in p.findall("originationChannels")]
        out.append(d)
    return out


def merge_params(step):
    plist = [elem_to_value(p) if len(p) else OrderedDict() for p in step.findall("parameters")]
    plist = [p if isinstance(p, dict) else OrderedDict() for p in plist]
    if not plist:
        return OrderedDict()
    return plist[0] if len(plist) == 1 else plist


def parse_process(wp):
    d = OrderedDict()
    d["id"] = wp.findtext("processId")
    d["description"] = wp.findtext("description")
    d["configurationDescription"] = wp.findtext("configurationDescription")
    d["conditions"] = parse_conditions(wp)
    d["initialSteps"] = [i.text or "" for i in wp.findall("./initialSteps/initialStep")]
    steps = []
    st = wp.find("steps")
    for s in (list(st) if st is not None else []):
        act = s.findtext("action")
        steps.append(OrderedDict([
            ("key", s.tag),
            ("action", act),
            ("actionSlug", action_slug(act)),
            ("stepType", s.findtext("stepType")),
            ("configurationDescription", s.findtext("configurationDescription")),
            ("params", merge_params(s)),
            ("onSuccess", s.findtext("onSuccess")),
            ("onFailure", s.findtext("onFailure")),
        ]))
    d["steps"] = steps
    return d


def derive_match(slug, filters):
    m = OrderedDict([("taskType", []), ("subtaskType", []), ("resolutions", []),
                     ("fields", []), ("fieldValues", []), ("documentTitles", []),
                     ("milestones", []), ("timerIds", [])])
    is_subtask = slug == "subtask_completed"
    for f in filters:
        for t in f["terms"]:
            var = t["variable"] or ""
            vals = t.get("values") if "values" in t else [t.get("value", "")]
            if var.endswith("payload.taskTemplateType}}"):
                m["taskType"] += vals
            elif var.endswith("payload.type}}"):
                m["subtaskType" if is_subtask else "taskType"] += vals
            elif var.endswith("payload.resolution}}"):
                m["resolutions"] += vals
            elif var.endswith("modifiedField}}"):
                if t.get("field"):
                    m["fields"].append(t["field"])
            elif var.endswith("fieldChangeEvents.newValue}}"):
                fld = t.get("field")
                if fld:
                    m["fields"].append(fld)
                for v in vals:
                    m["fieldValues"].append(OrderedDict(
                        [("field", fld), ("operator", t["operator"]), ("value", v)]))
            elif var.endswith("assignAttachmentsToDocument.title}}"):
                m["documentTitles"] += vals
            elif var.endswith("finishMilestones.title}}"):
                m["milestones"] += vals
            elif var.endswith("resource.id}}"):
                m["timerIds"] += [re.sub(r"^.*?([0-9a-f]{8}-[0-9a-f-]{27}).*$", r"\1", v) for v in vals]
    return OrderedDict((k, uniq(v)) for k, v in m.items() if v)


def step_effects(proc_id, step):
    slug = step["actionSlug"]
    plist = step["params"] if isinstance(step["params"], list) else [step["params"]]
    out = []
    for p in plist:
        e = OrderedDict([("kind", slug)])
        if slug == "task:create":
            e["taskType"] = p.get("type")
            e["noDuplicate"] = to_bool(p.get("noDuplicate"))
        elif slug == "task:complete":
            e["taskType"] = p.get("type")
            e["resolution"] = p.get("resolution")
            e["includeSubtask"] = to_bool(p.get("includeSubtask"))
            e["subtaskResolution"] = p.get("subtaskResolution")
        elif slug == "subtask:create":
            e["taskType"] = p.get("taskTemplateType")
            e["subtaskType"] = p.get("type")
            if p.get("reopenParentTask") is not None:
                e["reopenParentTask"] = to_bool(p.get("reopenParentTask"))
        elif slug == "subtask:complete":
            e["taskType"] = p.get("taskTemplateType")
            e["subtaskType"] = p.get("type")
            e["resolution"] = p.get("resolution")
            e["category"] = p.get("category")
        elif slug == "field:update":
            e["field"] = p.get("id")
            e["value"] = p.get("value")
        elif slug in ("timer:start", "timer:cancel"):
            e["timerId"] = p.get("timerConfigurationId")
            e["timerName"] = p.get("name")
        elif slug == "notification:send":
            e["templateId"] = p.get("templateId")
        elif slug == "document:sendrequest":
            docs = p.get("documents", [])
            docs = docs if isinstance(docs, list) else [docs]
            e["documents"] = [OrderedDict([("name", d.get("name")), ("type", d.get("type"))])
                              for d in docs]
            e["borrowerPair"] = p.get("borrowerPair")
        elif slug == "enhancedcondition:create":
            e["conditionType"] = p.get("conditionType")
            e["title"] = p.get("title")
        elif slug == "enhancedcondition:updatetracking":
            e["conditionType"] = p.get("conditionType")
            e["title"] = p.get("title")
            e["status"] = p.get("status")
        elif slug == "role:assign":
            e["roleId"] = p.get("roleId")
            e["roleName"] = p.get("roleName")
            e["assignee"] = p.get("id")
            e["loanAssociateType"] = p.get("loanAssociateType")
        elif slug == "folder:move":
            e["folderName"] = p.get("folderName")
        elif slug == "order:create":
            e["serviceRuleIds"] = p.get("serviceRuleIds")
        else:
            e["params"] = p
        e["processId"] = proc_id
        out.append(e)
    return out


def parse_trigger(raw, source_file):
    el = ET.fromstring(raw)
    slug = event_slug(el.findtext("triggerEvent"))
    filters = parse_filters(el)
    procs = [parse_process(wp) for wp in el.findall("./workflowProcesses/workflowProcess")]
    effects = []
    for p in procs:
        for s in p["steps"]:
            effects += step_effects(p["id"], s)
    r = OrderedDict()
    r["id"] = el.findtext("id")
    r["name"] = el.findtext("name")
    r["description"] = el.findtext("description")
    r["status"] = el.findtext("status")
    r["triggerEvent"] = el.findtext("triggerEvent")
    r["eventSlug"] = slug
    r["eventName"] = el.findtext("eventName")
    r["highPriority"] = to_bool(el.findtext("highPriorityFlag"))
    r["isInvalid"] = to_bool(el.findtext("isInvalid"))
    r["created"] = el.findtext("created")
    r["lastModified"] = el.findtext("lastModified")
    r["createdBy"] = el.findtext("createdBy")
    r["lastModifiedBy"] = el.findtext("lastModifiedBy")
    r["sourceFiles"] = [source_file]
    r["xmlFile"] = None
    r["tags"] = [t.text or "" for t in el.findall("./tags/tag")]
    r["filters"] = filters
    r["conditions"] = parse_conditions(el)
    r["match"] = derive_match(slug, filters)
    r["processes"] = procs
    r["effects"] = effects
    return r


# ---------------------------------------------------------------------------
# Loading + dedupe
# ---------------------------------------------------------------------------

def load_rules(exports_dir):
    files = sorted(glob.glob(os.path.join(exports_dir, "*.xml")),
                   key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", os.path.basename(p))])
    if not files:
        raise RuntimeError("no *.xml files in %s" % exports_dir)
    best, raws, seen_in, total = {}, {}, defaultdict(list), 0
    for f in files:
        with open(f, encoding="utf-8", newline="") as fh:
            text = fh.read()
        for raw in TRIGGER_RE.findall(text):
            total += 1
            r = parse_trigger(raw, rel(f))
            seen_in[r["id"]].append(rel(f))
            cur = best.get(r["id"])
            if cur is None or (r["lastModified"] or "") > (cur["lastModified"] or ""):
                best[r["id"]] = r
                raws[r["id"]] = raw
    dups = []
    for rid, r in best.items():
        r["sourceFiles"] = seen_in[rid]
        if len(seen_in[rid]) > 1:
            dups.append(OrderedDict([("id", rid), ("name", r["name"]),
                                     ("sourceFiles", seen_in[rid]),
                                     ("keptLastModified", r["lastModified"])]))
    dups.sort(key=lambda d: d["id"])
    order = sorted(best.values(), key=lambda r: (r["eventSlug"], (r["name"] or "").lower(), r["id"]))
    return order, raws, dups, [rel(f) for f in files], total


def assign_paths(rules, out_dir):
    used = defaultdict(int)
    base_count = defaultdict(int)
    for r in rules:
        base_count[(r["eventSlug"], slugify(r["name"]))] += 1
    for r in rules:
        key = (r["eventSlug"], slugify(r["name"]))
        name = key[1]
        if base_count[key] > 1:
            name += "_" + r["id"][:8]
        r["xmlFile"] = "%s/%s/%s.xml" % (rel(out_dir), r["eventSlug"], name)
        used[r["xmlFile"]] += 1
    dupe = [k for k, v in used.items() if v > 1]
    if dupe:
        raise RuntimeError("slug collision remains: %s" % dupe)


def write_xml(rules, raws):
    for r in rules:
        path = os.path.join(ROOT, r["xmlFile"])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(XML_DECL + "<eventTriggers>" + raws[r["id"]] + "</eventTriggers>")


# ---------------------------------------------------------------------------
# Derived indexes
# ---------------------------------------------------------------------------

def build_timers(rules):
    timers = {}

    def get(tid):
        return timers.setdefault(tid, OrderedDict([
            ("name", None), ("startedBy", set()), ("cancelledBy", set()), ("onCompleteRules", set())]))
    for r in rules:
        for e in r["effects"]:
            if e["kind"] in ("timer:start", "timer:cancel"):
                t = get(e["timerId"])
                t["name"] = t["name"] or e.get("timerName")
                t["startedBy" if e["kind"] == "timer:start" else "cancelledBy"].add(r["name"])
        for tid in r["match"].get("timerIds", []):
            get(tid)["onCompleteRules"].add(r["name"])
    return OrderedDict(
        (k, OrderedDict((f, sorted(v) if isinstance(v, set) else v) for f, v in timers[k].items()))
        for k in sorted(timers, key=lambda k: ((timers[k]["name"] or "~").lower(), k)))


def find_anomalies(rules):
    a = OrderedDict()

    def add(key, rule, detail=None):
        a.setdefault(key, []).append(rule["name"] if detail is None else "%s: %s" % (rule["name"], detail))
    for r in rules:
        if r["status"] != "ACTIVE":
            add("inactiveRules", r)
        if r["isInvalid"]:
            add("isInvalid", r)
        if (r["name"] or "").lower().startswith("copy_"):
            add("copyPrefixedNames", r)
        blob = json.dumps([r["conditions"], [p["conditions"] for p in r["processes"]]])
        if re.search(r"\[CX\.UDPilot\]", blob):
            add("mixedCaseCxUdPilot", r)
        for e in r["effects"]:
            if e["kind"] == "role:assign" and e.get("roleId") in ("undefined", "", None):
                add("roleIdUndefined", r, e.get("roleName"))
            for k in ("subtaskType",):
                v = e.get(k) or ""
                if v and "–" not in v and " - " in v:
                    add("subtaskTypeHyphenNotEnDash", r, v)
        for v in r["match"].get("subtaskType", []):
            if "–" not in v and " - " in v:
                add("subtaskTypeHyphenNotEnDash", r, v)
    return OrderedDict((k, sorted(set(v))) for k, v in sorted(a.items()))


# ---------------------------------------------------------------------------
# English rendering
# ---------------------------------------------------------------------------

def cs(s):
    return "`%s`" % s


def join_or(items, word="or"):
    items = [cs(i) for i in items]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " %s " % word + items[-1]


def trigger_summary(r):
    m, slug = r["match"], r["eventSlug"]
    tt = m.get("taskType", [])
    res = m.get("resolutions", [])
    on = " on task %s" % join_or(tt) if tt else ""
    rs = " with resolution %s" % join_or(res) if res else ""
    if slug == "subtask_completed":
        st = m.get("subtaskType", [])
        sub = "subtask %s" % join_or(st) if st else "any subtask"
        return "When %s%s is completed%s" % (sub, on, rs)
    if slug == "task_created":
        return "When task %s is created" % (join_or(tt) if tt else "(any)")
    if slug == "task_completed":
        return "When task %s is completed%s" % (join_or(tt) if tt else "(any)", rs)
    if slug == "field_modified":
        parts = []
        any_change = [f for f in m.get("fields", [])
                      if not any(v["field"] == f for v in m.get("fieldValues", []))]
        if any_change:
            parts.append("field %s changes (any change)" % join_or(any_change, "or"))
        by_field = OrderedDict()
        for v in m.get("fieldValues", []):
            by_field.setdefault((v["field"], v["operator"]), []).append(v["value"])
        for (f, op), vals in by_field.items():
            if op == "NOT_EQUAL_TO":
                parts.append("field %s changes to anything other than %s" % (cs(f), join_or(vals, "and")))
            else:
                parts.append("field %s changes to %s" % (cs(f), join_or(vals)))
        return "When " + " and ".join(parts) if parts else "When a loan field is modified"
    if slug == "file_attached":
        d = m.get("documentTitles", [])
        return "When a file is attached to document %s" % join_or(d) if d else "When a file is attached"
    if slug == "milestone_completed":
        ms = m.get("milestones", [])
        return "When milestone %s is finished" % join_or(ms) if ms else "When a milestone is finished"
    if slug == "loan_created":
        return "When a loan is created"
    if slug == "timer_completed":
        ids = m.get("timerIds", [])
        return "When timer %s completes" % join_or(ids) if ids else "When a timer completes"
    return "When `%s`" % r["triggerEvent"]


def effect_text(e, tname=None):
    k = e["kind"]
    if k == "task:create":
        return "Create task %s%s" % (cs(e["taskType"]), " (unless one already exists)" if e.get("noDuplicate") else "")
    if k == "task:complete":
        s = "Complete task %s" % cs(e["taskType"])
        if e.get("resolution"):
            s += " with resolution %s" % cs(e["resolution"])
        if e.get("includeSubtask"):
            s += ", also completing its subtasks"
            if e.get("subtaskResolution"):
                s += " as %s" % cs(e["subtaskResolution"])
        return s
    if k == "subtask:create":
        s = "Add subtask %s to task %s" % (cs(e["subtaskType"]), cs(e["taskType"]))
        if e.get("reopenParentTask"):
            s += " (reopens the parent task)"
        return s
    if k == "subtask:complete":
        return "Complete subtask %s on task %s with resolution %s" % (
            cs(e["subtaskType"]), cs(e["taskType"]), cs(e["resolution"]))
    if k == "field:update":
        return "Set field %s to %s" % (cs(e["field"]), cs(e["value"]))
    if k == "timer:start":
        return "Start timer %s (%s)" % (cs(e.get("timerName")), e["timerId"])
    if k == "timer:cancel":
        return "Cancel timer %s (%s)" % (cs(e.get("timerName")), e["timerId"])
    if k == "notification:send":
        return "Send notification template %s" % cs(e["templateId"])
    if k == "document:sendrequest":
        docs = ", ".join("%s (%s)" % (d["name"], d["type"]) for d in e["documents"])
        return "Send document request to borrower pair %s: %s" % (cs(e.get("borrowerPair")), docs)
    if k == "disclosure:send":
        return "Send disclosures"
    if k == "enhancedcondition:create":
        return "Create %s condition %s" % (cs(e["conditionType"]), cs(e["title"]))
    if k == "enhancedcondition:updatetracking":
        return "Set %s condition %s to %s" % (cs(e["conditionType"]), cs(e["title"]), cs(e["status"]))
    if k == "role:assign":
        return "Assign %s role (%s %s) to %s" % (
            cs(e.get("roleName")), e.get("loanAssociateType") or "", "id " + cs(e.get("roleId")), cs(e.get("assignee")))
    if k == "folder:move":
        return "Move loan to folder %s" % cs(e["folderName"])
    if k == "order:create":
        return "Create service order using rule %s" % cs(e["serviceRuleIds"])
    return "%s" % k


def cond_md(c, indent=""):
    t = c["type"]
    if t == "script":
        s = c.get("script", "")
        if "\n" in s or "`" in s:
            return "%s```\n%s\n%s```" % (indent, s, indent)
        return "%sScript: `%s`" % (indent, s)
    if t == "requiredTasks":
        return "%sRequires task(s): %s" % (indent, join_or(c.get("requiredTasks", []), "and"))
    if t == "requiredDocuments":
        return "%sRequires document(s): %s" % (indent, ", ".join(
            "`%s`%s" % (d["title"], " (attachment required)" if d["isAttachmentRequired"] else "")
            for d in c.get("requiredDocuments", [])))
    if t == "originationChannels":
        return "%sOrigination channel: %s" % (indent, join_or(c.get("originationChannels", [])))
    return "%s%s" % (indent, json.dumps(c, ensure_ascii=False))


def build_catalog(rules, meta, timers):
    L = []
    w = L.append
    w("# Workflow Automation Rules Catalogue")
    w("")
    w("> Generated by `parse_rules.py` from `rules/exports/` — do not edit by hand. "
      "Machine-readable version: [`rules/rules.json`](../rules/rules.json).")
    w("")
    w("## Summary")
    w("")
    w("- **%d unique rules** (%d export entries, %d duplicate removed) from %d export files"
      % (meta["ruleCount"], meta["exportEntries"], len(meta["duplicatesRemoved"]), len(meta["sourceFiles"])))
    w("")
    w("| Event | Rules |")
    w("|---|---|")
    for k, v in meta["countsByEvent"].items():
        w("| %s (`%s`) | %d |" % (EVENT_TITLES.get(k, k), k, v))
    w("")
    w("| Status | Rules |")
    w("|---|---|")
    for k, v in meta["countsByStatus"].items():
        w("| %s | %d |" % (k, v))
    w("")
    if meta["duplicatesRemoved"]:
        w("Duplicates removed: " + "; ".join(
            "`%s` (%s) appeared in %s" % (d["name"], d["id"], ", ".join("`%s`" % f for f in d["sourceFiles"]))
            for d in meta["duplicatesRemoved"]))
        w("")

    # ---- Rules by task type
    by_type = defaultdict(lambda: defaultdict(set))
    for r in rules:
        for t in r["match"].get("taskType", []):
            by_type[t]["triggers"].add(r["name"])
        for c in r["conditions"] + [c for p in r["processes"] for c in p["conditions"]]:
            for t in c.get("requiredTasks", []) or []:
                by_type[t]["requiredBy"].add(r["name"])
        for e in r["effects"]:
            t = e.get("taskType")
            if not t:
                continue
            if e["kind"] == "task:create":
                by_type[t]["creates"].add(r["name"])
            elif e["kind"] == "task:complete":
                by_type[t]["completes"].add(r["name"])
            elif e["kind"] == "subtask:create":
                by_type[t]["addsSubtask"].add(r["name"])
            elif e["kind"] == "subtask:complete":
                by_type[t]["completesSubtask"].add(r["name"])
    w("## Rules by task type")
    w("")
    w("%d task types are referenced by at least one rule filter, condition or effect." % len(by_type))
    w("")
    labels = [("triggers", "Triggered by"), ("creates", "Created by"), ("completes", "Completed by"),
              ("addsSubtask", "Subtasks added by"), ("completesSubtask", "Subtasks completed by"),
              ("requiredBy", "Required by condition in")]
    for t in sorted(by_type, key=str.lower):
        w("### `%s`" % t)
        w("")
        for key, label in labels:
            if by_type[t].get(key):
                w("- **%s:** %s" % (label, ", ".join("`%s`" % n for n in sorted(by_type[t][key]))))
        w("")

    # ---- Timer chains
    rule_by_name = {r["name"]: r for r in rules}
    w("## Timer chains")
    w("")
    w("Each timer is started by one or more rules; when it completes, the rules in *Fires* run.")
    w("")
    for tid, t in timers.items():
        w("### %s" % (cs(t["name"]) if t["name"] else "(unnamed timer)"))
        w("")
        w("- **Timer id:** `%s`" % tid)
        w("- **Started by:** %s" % (", ".join("`%s`" % n for n in t["startedBy"]) or "_none in these exports_"))
        w("- **Cancelled by:** %s" % (", ".join("`%s`" % n for n in t["cancelledBy"]) or "_none_"))
        w("- **Fires:** %s" % ("" if t["onCompleteRules"] else "_no rule listens for it_"))
        for n in t["onCompleteRules"]:
            r = rule_by_name[n]
            w("  - `%s`%s" % (n, " (INACTIVE)" if r["status"] != "ACTIVE" else ""))
            seen = set()
            for e in r["effects"]:
                tx = effect_text(e)
                if tx not in seen:
                    seen.add(tx)
                    w("    - %s" % tx)
        w("")

    # ---- Per event
    for slug in meta["countsByEvent"]:
        group = [r for r in rules if r["eventSlug"] == slug]
        w("## %s (%d)" % (EVENT_TITLES.get(slug, slug), len(group)))
        w("")
        w("Event: `%s`" % group[0]["triggerEvent"])
        w("")
        for r in group:
            flag = " — INACTIVE" if r["status"] != "ACTIVE" else ""
            w("### %s%s" % (r["name"], flag))
            w("")
            w("- **Status:** %s%s%s" % (r["status"], "; high priority" if r["highPriority"] else "",
                                       "; **invalid**" if r["isInvalid"] else ""))
            if r["description"] and r["description"] != r["eventName"]:
                w("- **Description:** %s" % r["description"])
            if r["tags"]:
                w("- **Tags:** %s" % ", ".join("`%s`" % t for t in r["tags"]))
            w("- **Trigger:** %s." % trigger_summary(r))
            w("- **Last modified:** %s by %s" % (r["lastModified"], r["lastModifiedBy"]))
            w("- **File:** [`%s`](../%s)" % (r["xmlFile"], r["xmlFile"]))
            if r["conditions"]:
                w("- **Trigger conditions:**")
                for c in r["conditions"]:
                    w(cond_md(c, "  - ") if c["type"] != "script" or "\n" not in c.get("script", "")
                      else "  - Script:\n\n" + cond_md(c, "    ") + "\n")
            w("")
            if r["processes"]:
                w("**Processes**")
                w("")
            for i, p in enumerate(r["processes"], 1):
                label = p["configurationDescription"] or p["description"] or p["id"]
                w("%d. **%s** (%s)" % (i, label, p["description"]))
                if p["conditions"]:
                    w("   - *Condition:*")
                    for c in p["conditions"]:
                        if c["type"] == "script" and ("\n" in c.get("script", "") or "`" in c.get("script", "")):
                            w("")
                            w(cond_md(c, "     "))
                            w("")
                        else:
                            w(cond_md(c, "     - "))
                else:
                    w("   - *Condition:* none (always runs)")
                for s in p["steps"]:
                    for e in step_effects(p["id"], s):
                        extra = ""
                        if s["onFailure"]:
                            extra += " (on failure: `%s`)" % s["onFailure"]
                        if s["onSuccess"]:
                            extra += " (on success: `%s`)" % s["onSuccess"]
                        if s["configurationDescription"]:
                            extra += " [%s]" % s["configurationDescription"]
                        w("   - %s%s" % (effect_text(e), extra))
            w("")
    return "\n".join(L).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Split Encompass eventTrigger exports into per-rule XML, JSON and a catalogue.")
    ap.add_argument("--exports-dir", default=os.path.join(ROOT, "rules", "exports"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "rules", "by_event"))
    ap.add_argument("--out-json", default=os.path.join(ROOT, "rules", "rules.json"))
    ap.add_argument("--out-md", default=os.path.join(ROOT, "docs", "RULES_CATALOG.md"))
    ap.add_argument("--json", action="store_true", help="print a machine-readable summary")
    args = ap.parse_args()

    try:
        rules, raws, dups, files, total = load_rules(args.exports_dir)
        assign_paths(rules, args.out_dir)

        if os.path.isdir(args.out_dir):
            shutil.rmtree(args.out_dir)
        write_xml(rules, raws)

        timers = build_timers(rules)
        by_event, by_status = OrderedDict(), OrderedDict()
        for r in rules:
            by_event[r["eventSlug"]] = by_event.get(r["eventSlug"], 0) + 1
        for r in sorted(rules, key=lambda r: r["status"]):
            by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        meta = OrderedDict([
            ("generatedAt", max(r["lastModified"] for r in rules)),
            ("sourceFiles", files),
            ("exportEntries", total),
            ("ruleCount", len(rules)),
            ("duplicatesRemoved", dups),
            ("countsByEvent", by_event),
            ("countsByStatus", by_status),
            ("anomalies", find_anomalies(rules)),
        ])
        os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
        with open(args.out_json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(OrderedDict([("metadata", meta), ("rules", rules), ("timers", timers)]),
                      fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
        with open(args.out_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(build_catalog(rules, meta, timers))

        summary = OrderedDict([("ok", True), ("rules", len(rules)), ("export_entries", total),
                               ("duplicates_removed", len(dups)), ("by_event", by_event),
                               ("by_status", by_status), ("timers", len(timers)),
                               ("json", rel(args.out_json)), ("md", rel(args.out_md)),
                               ("xml_dir", rel(args.out_dir))])
    except Exception as exc:  # noqa: BLE001
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print("error: %s" % exc, file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print("Wrote %d rules (%d duplicates removed) -> %s, %s, %s"
              % (len(rules), len(dups), rel(args.out_dir), rel(args.out_json), rel(args.out_md)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
