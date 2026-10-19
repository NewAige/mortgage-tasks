#!/usr/bin/env python3
"""
rules_map_docs.py - Generate docs/RULES_MAP.md (Mermaid diagrams + "how each task is driven").

Reads rules/graph.json (rules_graph.py), docs/rules_crossref.json (rules_crossref.py),
roadmap.json and tasks/**/*.xml, and writes one Markdown page for operations staff:

  Part 1  Mermaid flowcharts that render on GitHub
            - one per stage (split by subcategory when a stage would exceed ~40 nodes)
            - one small chart per timer
  Part 2  "How each task is driven": one table row per task template, grouped by stage,
          the roadmap tasks that rules already reference, and a short "Gaps to review" list.

The output is generated, never hand-edited, and deterministic (no wall clock; the
timestamp shown is copied from the graph).

Usage (from the repo root):
    python rules_graph.py && python rules_map_docs.py
    python rules_map_docs.py --json

Return value (stdout, or one JSON line with --json):
    {"ok": true, "file": "docs/RULES_MAP.md", "tasks": N, "stageDiagrams": N, ...}
    {"ok": false, "error": "<message>"}

Exit codes: 0 = success, 1 = error (including a failed structural self-check of a diagram).
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict
from xml.etree import ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = "docs/RULES_MAP.md"
MAX_NODES = 40
STAGES = OrderedDict([
    ("1_origination", "Origination"),
    ("2_processing", "Processing"),
    ("3_underwriting", "Underwriting"),
    ("4_closing", "Closing"),
    ("5_funding", "Funding"),
    ("6_pre-closing-qc", "Pre-Closing QC"),
    ("7_post-closing-qc", "Post-Closing QC"),
])
DASH = "\u2013"


def stage_name(sid):
    if sid in STAGES:
        return "%s %s" % (sid.split("_")[0], STAGES[sid])
    return "outside the template library"


def stage_title(sid):
    return "Stage %s: %s" % (sid.split("_")[0], STAGES[sid])


def load_json(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


# Folder words that are acronyms; .title() would print "Arm", "Uw", "Ssa89".
FOLDER_WORDS = {"Arm": "ARM", "Avm": "AVM", "Uw": "UW", "Ssa89": "SSA-89", "Qc": "QC", "Hmda": "HMDA",
                "Mers": "MERS", "Mi": "MI", "Ucd": "UCD", "Cd": "CD", "Par": "PAR", "Heloc": "HELOC"}


def humanise_folder(f):
    words = re.sub(r"[-_]+", " ", f).strip().title().split()
    return " ".join(FOLDER_WORDS.get(w, w) for w in words)


# ---------------------------------------------------------------------------
# Mermaid helpers
# ---------------------------------------------------------------------------

def mm_text(s, limit=70):
    """Make a string safe inside a double-quoted Mermaid label."""
    s = " ".join((s or "").split())
    if len(s) > limit:
        s = s[: limit - 1].rstrip() + "\u2026"
    s = s.replace("&", "#amp;").replace('"', "'").replace("`", "'")
    s = s.replace("<", "#lt;").replace(">", "#gt;")
    s = s.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    s = s.replace("|", "/").replace("\\", "/").replace(";", ",")
    s = s.replace("%%", "%")
    return s


class Chart:
    """A flowchart: nodes are keyed by an arbitrary hashable, ids are n1, n2, ... in first-use order."""

    def __init__(self):
        self.ids = OrderedDict()
        self.nodes = OrderedDict()   # key -> (shape, text, cls)
        self.edges = OrderedDict()   # (a, b, dotted) -> list of labels

    def node(self, key, shape, text, cls=""):
        if key not in self.nodes:
            self.ids[key] = "n%d" % (len(self.ids) + 1)
            self.nodes[key] = (shape, text, cls)
        return self.ids[key]

    def has(self, key):
        return key in self.nodes

    def edge(self, a, b, label, dotted=False):
        labs = self.edges.setdefault((a, b, dotted), [])
        if label and label not in labs:
            labs.append(label)

    def render(self):
        out = ["flowchart LR"]
        for key, (shape, text, cls) in self.nodes.items():
            t = mm_text(text)
            nid = self.ids[key]
            if shape == "task":
                out.append('    %s["%s"]' % (nid, t))
            elif shape == "round":
                out.append('    %s("%s")' % (nid, t))
            elif shape == "timer":
                out.append('    %s(["%s"])' % (nid, t))
            else:  # stub
                out.append('    %s["%s"]' % (nid, t))
            if cls:
                out.append("    class %s %s" % (nid, cls))
        for (a, b, dotted), labs in self.edges.items():
            arrow = "-.->" if dotted else "-->"
            if labs:
                shown = labs[:3]
                lab = "<br/>".join(mm_text(x, 60) for x in shown)
                if len(labs) > 3:
                    lab += "<br/>+%d more" % (len(labs) - 3)
                out.append('    %s %s|"%s"| %s' % (a, arrow, lab, b))
            else:
                out.append("    %s %s %s" % (a, arrow, b))
        out.append("    classDef stub stroke-dasharray: 4 3")
        out.append("    classDef gap stroke-dasharray: 2 4")
        return "\n".join(out)

    def check(self, title):
        """Structural self-check of the rendered text. Raises ValueError on a problem."""
        text = self.render()
        lines = text.split("\n")
        if lines[0] != "flowchart LR":
            raise ValueError("%s: bad header" % title)
        defined = set()
        for ln in lines[1:]:
            m = re.match(r'^    (n\d+)(\[|\(|\(\[)"([^"]*)"(\]|\)|\]\))$', ln)
            if m:
                if m.group(1) in defined:
                    raise ValueError("%s: duplicate node %s" % (title, m.group(1)))
                defined.add(m.group(1))
                if ln.count('"') != 2:
                    raise ValueError("%s: quote count in %r" % (title, ln))
        for ln in lines[1:]:
            m = re.match(r'^    (n\d+) (-->|-\.->)(?:\|"([^"]*)"\|)? (n\d+)$', ln)
            if m:
                if m.group(1) not in defined or m.group(4) not in defined:
                    raise ValueError("%s: edge to undefined node: %r" % (title, ln))
                continue
            if re.match(r"^    (n\d+\W|class n\d+ |classDef )", ln) is None:
                raise ValueError("%s: unrecognised line %r" % (title, ln))
        for ln in lines[1:]:
            if ln.startswith("    class n"):
                if ln.split()[1] not in defined:
                    raise ValueError("%s: class on undefined node" % title)
        return len(defined)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class Model:
    def __init__(self):
        self.g = load_json("rules/graph.json")
        self.cross = load_json("docs/rules_crossref.json")
        self.road = load_json("roadmap.json")
        self.N = {n["id"]: n for n in self.g["nodes"]}
        self.edges = self.g["edges"]
        self.trig = defaultdict(list)     # ruleId -> triggers edges
        self.eff = defaultdict(list)      # ruleId -> effects edges
        self.canc = defaultdict(list)     # ruleId -> cancels edges
        self.out_eff = defaultdict(list)  # target node id -> effects edges
        self.contains = defaultdict(list)  # task id -> contains edges
        self.sub_trig = defaultdict(list)  # subtask id -> triggers edges
        self.task_enters = defaultdict(list)
        for e in self.edges:
            k = e["kind"]
            if k == "triggers":
                self.trig[e["ruleId"]].append(e)
                if self.N[e["source"]]["kind"] == "subtaskType":
                    self.sub_trig[e["source"]].append(e)
            elif k == "effects":
                self.eff[e["ruleId"]].append(e)
                self.out_eff[e["target"]].append(e)
            elif k == "cancels":
                self.canc[e["ruleId"]].append(e)
            elif k == "contains":
                self.contains[e["source"]].append(e)
            elif k == "enters" and self.N[e["target"]]["kind"] == "taskType":
                self.task_enters[e["target"]].append(e)
        for d in (self.trig, self.eff, self.canc, self.out_eff, self.contains, self.sub_trig):
            for lst in d.values():
                lst.sort(key=lambda x: x["id"])
        # task templates straight from the XML (the row-count authority)
        self.templates = []
        for path in sorted(glob.glob(os.path.join(ROOT, "tasks", "**", "*.xml"), recursive=True)):
            relp = os.path.relpath(path, ROOT).replace(os.sep, "/")
            root = ET.parse(path).getroot()
            for tt in root.iter("taskTemplate"):
                self.templates.append({
                    "file": relp, "type": tt.get("type"), "name": tt.get("name"),
                    "stage": relp.split("/")[1], "sub": relp.split("/")[2] if relp.count("/") > 2 else "",
                })
        self.road_tasks = {}
        for s in self.road["stages"]:
            for t in s["tasks"]:
                self.road_tasks[t["id"]] = t

    # -- node helpers -------------------------------------------------------
    def task_of(self, nid):
        n = self.N[nid]
        if n["kind"] == "taskType":
            return nid
        if n["kind"] == "subtaskType":
            return "task:" + n["taskType"]
        return None

    def task_stage(self, tid):
        n = self.N.get(tid)
        return n.get("stage") if n else None

    def subcat(self, tid):
        n = self.N.get(tid)
        if n and n.get("xmlFile"):
            parts = n["xmlFile"].split("/")
            return parts[2] if len(parts) > 3 else ""
        return ""

    def sub_short(self, nid):
        n = self.N[nid]
        return n.get("shortLabel") or n["label"]

    def trigger_phrase(self, t):
        s = self.N[t["source"]]
        k = s["kind"]
        if k == "subtaskType":
            res = "/".join(t.get("resolutions") or []) or "marked"
            return "%s: %s" % (self.sub_short(t["source"]), res)
        if k == "taskType":
            return {"task_created": "created", "task_completed": "completed"}.get(t["event"], "")
        if k == "timer":
            return "runs out"
        return ""

    def action_phrase(self, f):
        tgt = self.N[f["target"]]
        eff = f["effect"]
        res = f.get("resolution")
        if eff == "task:create":
            return "creates"
        if eff == "task:complete":
            return "closes as N/A" if res == "NA" else "completes"
        if eff == "subtask:create":
            return "adds %s" % self.sub_short(f["target"])
        if eff == "subtask:complete":
            if res == "NA":
                return "marks %s N/A" % self.sub_short(f["target"])
            return "completes %s" % self.sub_short(f["target"])
        if eff == "timer:start":
            return "starts"
        if eff == "field:update":
            return "sets field"
        return eff

    def context_text(self, nid):
        n = self.N[nid]
        k = n["kind"]
        if k == "field":
            return "Field: %s changes" % n["label"]
        if k == "milestone":
            return "Milestone: %s completed" % n["label"]
        if k == "document":
            return "File attached: %s" % n["label"]
        if k == "timer":
            return "\u23f1 %s" % n["label"]
        if k == "entry":
            return n["label"]
        return n["label"]


def ext_text(f):
    eff = f["effect"]
    if eff == "notification:send":
        return "Notification: %s" % (f.get("targetLabel") or "(unnamed)")
    if eff == "order:create":
        return "Service order: %s" % (f.get("targetLabel") or "(unnamed)")
    if eff == "role:assign":
        return "Assigns role %s" % (f.get("roleName") or f.get("roleId") or "?")
    if eff == "folder:move":
        return 'Moves loan to folder "%s"' % (f.get("folderName") or "?")
    if eff == "document:sendrequest":
        return "Sends documents: %s" % (", ".join(f.get("documents") or []) or "(unnamed)")
    if eff == "enhancedcondition:create":
        return "Adds condition: %s" % (f.get("title") or "(unnamed)")
    if eff == "enhancedcondition:updatetracking":
        return "Updates condition: %s" % (f.get("title") or "(unnamed)")
    if eff == "disclosure:send":
        return "Sends a disclosure package"
    return eff


# ---------------------------------------------------------------------------
# Part 1: stage diagrams
# ---------------------------------------------------------------------------

def rule_links(M):
    """Yield (srcNode, tgtNode, label, ruleId, inactive) for every rule trigger x workflow effect."""
    for rid in sorted(M.trig):
        for t in M.trig[rid]:
            for f in M.eff.get(rid, []):
                tk = M.N[f["target"]]["kind"]
                if tk not in ("taskType", "subtaskType", "timer", "field"):
                    continue
                if tk == "field" and not f.get("heardBy"):
                    continue
                tp = M.trigger_phrase(t)
                ap = M.action_phrase(f)
                label = (tp + " \u2192 " + ap) if tp else ap
                if f.get("inactive"):
                    label += " (rule switched off)"
                yield t["source"], f["target"], label, rid


def build_stage_charts(M):
    links = list(rule_links(M))
    tasks_by_stage = defaultdict(list)
    for n in M.g["nodes"]:
        if n["kind"] == "taskType" and n.get("stage") in STAGES:
            tasks_by_stage[n["stage"]].append(n["id"])
    for s in tasks_by_stage:
        tasks_by_stage[s].sort(key=lambda i: (M.subcat(i), M.N[i]["label"], i))
    results = []  # (stage, subcat or None, Chart, title)
    for sid in STAGES:
        tids = tasks_by_stage.get(sid, [])
        full = make_chart(M, links, sid, set(tids), set(tids))
        if len(full.nodes) <= MAX_NODES:
            results.append((sid, None, full))
            continue
        subs = OrderedDict()
        for t in tids:
            subs.setdefault(M.subcat(t), []).append(t)
        # pack neighbouring subcategories into one picture while it stays within MAX_NODES
        bin_names, bin_tasks, bin_chart = [], [], None
        for sc, group in subs.items():
            trial = make_chart(M, links, sid, set(bin_tasks + group), set(tids))
            if bin_names and len(trial.nodes) > MAX_NODES:
                results.append((sid, bin_names, bin_chart))
                bin_names, bin_tasks = [], []
                trial = make_chart(M, links, sid, set(group), set(tids))
            bin_names.append(sc)
            bin_tasks += group
            bin_chart = trial
        if bin_names:
            results.append((sid, bin_names, bin_chart))
    return results


def make_chart(M, links, sid, focus, stage_tasks):
    """Build a chart; other-stage tasks become stubs, grouped per stage when a stage has more than 3."""
    C = make_chart_raw(M, links, sid, focus, stage_tasks, set())
    groups = defaultdict(set)
    for key in C.nodes:
        if isinstance(key, tuple) and key[0] == "stub":
            groups[stub_group(M, key[1], stage_tasks)].add(key[1])
    big = {g for g, mem in groups.items() if len(mem) > 3}
    if big:
        C = make_chart_raw(M, links, sid, focus, stage_tasks, big)
    return C


def stub_group(M, tid, stage_tasks):
    if tid in stage_tasks:
        return "same"
    st = M.N[tid].get("stage")
    return st if st in STAGES else "none"


def make_chart_raw(M, links, sid, focus, stage_tasks, grouped):
    """focus = tasks drawn as full nodes; stage_tasks = every task of the stage."""
    C = Chart()
    members = defaultdict(list)
    for t in sorted(focus, key=lambda i: (M.N[i]["label"], i)):
        C.node(t, "task", M.N[t]["label"])

    def endpoint(nid):
        """Return the diagram key for a graph node, creating it. None = not drawable here."""
        tid = M.task_of(nid)
        if tid is not None:
            if tid in focus:
                return C.node(tid, "task", M.N[tid]["label"])
            n = M.N[tid]
            st = n.get("stage")
            grp = stub_group(M, tid, stage_tasks)
            if grp in grouped:
                members[grp].append(n["label"])
                return C.node(("stubgroup", grp), "stub", "", "stub")
            if tid in stage_tasks:
                return C.node(("stub", tid), "stub", "Same stage \u00b7 %s" % n["label"], "stub")
            if st in STAGES:
                return C.node(("stub", tid), "stub", "\u2192 %s \u00b7 %s" % (stage_title(st), n["label"]), "stub")
            return C.node(("stub", tid), "stub", "\u2192 Not in template library \u00b7 %s" % n["label"], "stub")
        n = M.N[nid]
        if n["kind"] == "timer":
            return C.node(nid, "timer", M.context_text(nid))
        if n["kind"] == "entry" and n.get("entryKind") != "loan_created":
            return None
        return C.node(nid, "round", M.context_text(nid))

    def touches_focus(nid):
        tid = M.task_of(nid)
        return tid is not None and tid in focus

    pending = []
    for s, t, label, rid in links:
        st, tt = M.task_of(s), M.task_of(t)
        if st is not None and st == tt:
            continue  # inside one task: not a link between tasks
        if touches_focus(s) or touches_focus(t):
            a = endpoint(s)
            b = endpoint(t)
            if a and b:
                lab = label
                if M.N[t]["kind"] == "subtaskType" and M.N[s]["kind"] != "subtaskType":
                    pass
                C.edge(a, b, lab)
        else:
            pending.append((s, t, label))
    # second pass: continue from timers / fields already on the chart
    for s, t, label in pending:
        if M.N[s]["kind"] in ("timer", "field") and C.has(s):
            a = C.ids[s]
            b = endpoint(t)
            if b:
                C.edge(a, b, label)
        elif M.N[t]["kind"] in ("timer", "field") and C.has(t) and M.task_of(s) is not None:
            a = endpoint(s)
            if a:
                C.edge(a, C.ids[t], label)
    for grp, names in members.items():
        names = sorted(set(names))
        head = {"same": "Same stage", "none": "\u2192 Not in template library"}.get(grp, "\u2192 " + stage_title(grp) if grp in STAGES else grp)
        shown = ", ".join(names[:3]) + (" +%d more" % (len(names) - 3) if len(names) > 3 else "")
        C.nodes[("stubgroup", grp)] = ("stub", "%s (%d tasks): %s" % (head, len(names), shown), "stub")
    return C


# ---------------------------------------------------------------------------
# Part 1: timer charts
# ---------------------------------------------------------------------------

def build_timer_charts(M):
    out = []
    timers = sorted((n for n in M.g["nodes"] if n["kind"] == "timer"), key=lambda n: (n["label"], n["id"]))
    for tn in timers:
        C = Chart()
        tkey = tn["id"]
        tid = C.node(tkey, "timer", "\u23f1 %s" % tn["label"])

        def src_node(snid):
            sn = M.N[snid]
            if sn["kind"] == "subtaskType":
                return C.node(snid, "task", sn["label"])
            if sn["kind"] == "taskType":
                return C.node(snid, "task", sn["label"])
            if sn["kind"] == "timer":
                return C.node(snid, "timer", "\u23f1 %s" % sn["label"])
            return C.node(snid, "round", M.context_text(snid))

        # what starts it
        started = False
        for f in M.out_eff.get(tkey, []):
            if f["effect"] != "timer:start":
                continue
            for t in M.trig.get(f["ruleId"], []):
                a = src_node(t["source"])
                tp = M.trigger_phrase(t)
                C.edge(a, tid, (tp + " \u2192 starts") if tp else "starts")
                started = True
        if not started:
            g_ = C.node("gap-start", "stub", "No known rule starts this timer", "gap")
            C.edge(g_, tid, "")
        # what stops it
        for e in M.edges:
            if e["kind"] == "cancels" and e["target"] == tkey:
                for t in M.trig.get(e["ruleId"], []):
                    a = src_node(t["source"])
                    tp = M.trigger_phrase(t)
                    C.edge(a, tid, (tp + " \u2192 cancels") if tp else "cancels", dotted=True)
        # what happens when it runs out
        outcomes = OrderedDict()
        for t in M.edges:
            pass
        run_rules = sorted({t["ruleId"] for rid in M.trig for t in M.trig[rid] if t["source"] == tkey})
        for rid in run_rules:
            for f in M.eff.get(rid, []):
                tk = M.N[f["target"]]["kind"]
                if tk == "external":
                    key, shape, text = ("ext", ext_text(f)), "stub", ext_text(f)
                    lab = ""
                elif tk == "field":
                    key, shape, text = (f["target"],), "round", "Field: %s set" % M.N[f["target"]]["label"]
                    lab = "sets field"
                elif tk == "timer":
                    key, shape, text = (f["target"],), "timer", "\u23f1 %s" % M.N[f["target"]]["label"]
                    lab = "starts"
                else:
                    key, shape = (f["target"],), "task"
                    text = M.N[f["target"]]["label"]
                    lab = M.action_phrase(f)
                    if tk == "subtaskType":
                        text = M.N[f["target"]]["label"]
                outcomes.setdefault(key, (shape, text, lab))
        if not run_rules:
            g_ = C.node("gap-end", "stub", "Nothing known happens when it runs out", "gap")
            C.edge(tid, g_, "runs out")
        keys = list(outcomes)
        for key in keys[:12]:
            shape, text, lab = outcomes[key]
            b = C.node(key if key[0] != "ext" else key, "stub" if shape == "stub" else shape, text)
            C.edge(tid, b, ("runs out \u2192 " + lab) if lab else "runs out")
        if len(keys) > 12:
            b = C.node("more", "stub", "+%d more actions" % (len(keys) - 12), "stub")
            C.edge(tid, b, "runs out")
        out.append((tn, C))
    return out


# ---------------------------------------------------------------------------
# Part 2: per-task table
# ---------------------------------------------------------------------------

def cell(s):
    s = (s or "").replace("|", "\\|").replace("\n", " ")
    return s if s else "\u2014"


def when_clause(sentence, cond_limit=90):
    """'When X, Encompass creates the task Y (only if C).' -> 'When X (only if C)'."""
    m = re.match(r"^(.*?), Encompass .*?(\(only if (.*)\))?\.?$", sentence or "")
    if not m:
        return sentence or ""
    when = m.group(1)
    cond = ""
    m2 = re.search(r"\(only if (.*)\)\.?$", sentence)
    if m2:
        c = m2.group(1)
        if len(c) > cond_limit:
            c = c[: cond_limit - 1] + "\u2026"
        cond = " (only if %s)" % c
    return when + cond


def listing(items, cap=4):
    items = list(items)
    if not items:
        return ""
    shown = items[:cap]
    s = "<br>".join(shown)
    if len(items) > cap:
        s += "<br>+%d more" % (len(items) - cap)
    return s


def build_rows(M):
    rows = []
    for tpl in M.templates:
        tid = "task:" + tpl["type"]
        n = M.N.get(tid)
        row = {"tpl": tpl, "node": n, "id": tid}
        creators = [f for f in M.out_eff.get(tid, []) if f["effect"] == "task:create"]
        completers = [f for f in M.out_eff.get(tid, []) if f["effect"] == "task:complete"]
        row["creators"] = creators
        row["completers"] = completers
        subs = []
        for c in M.contains.get(tid, []):
            sid = c["target"]
            adders = [f for f in M.out_eff.get(sid, []) if f["effect"] == "subtask:create"]
            subs.append((sid, c["autoCreate"], adders))
        row["cond_added"] = [(s, a) for s, ac, a in subs if not ac and a]
        row["cond_unadded"] = [s for s, ac, a in subs if not ac and not a]
        row["auto"] = [s for s, ac, a in subs if ac]
        done, issue, other = [], [], []
        for s, ac, a in subs:
            for t in M.sub_trig.get(s, []):
                res = t.get("resolutions") or []
                tag = "%s (%s)" % (M.sub_short(s), M.N[t["target"]]["label"])
                if "Done" in res:
                    done.append(tag)
                if "Issue" in res:
                    issue.append(tag)
                if any(r not in ("Done", "Issue") for r in res):
                    other.append(tag)
        row["done"], row["issue"], row["other"] = sorted(set(done)), sorted(set(issue)), sorted(set(other))
        # any rule reference at all (for reconciliation with the crossref orphan list)
        refs = bool(creators or completers or M.sub_trig_any(tid))
        row["has_rule_ref"] = refs
        rows.append(row)
    return rows


def sub_trig_any(self, tid):
    # task-level trigger, subtask-level trigger/effect, or task effects
    for e in self.edges:
        k = e["kind"]
        if k == "triggers" and e["source"] != e["target"]:
            if self.task_of(e["source"]) == tid:
                return True
        if k == "effects" and self.task_of(e["target"]) == tid:
            return True
    return False


Model.sub_trig_any = sub_trig_any


def render_rows(M, rows):
    lines = []
    by_stage = defaultdict(list)
    for r in rows:
        by_stage[r["tpl"]["stage"]].append(r)
    for sid in STAGES:
        rs = sorted(by_stage.get(sid, []), key=lambda r: (r["tpl"]["sub"], r["tpl"]["name"], r["tpl"]["type"]))
        lines.append("### %s (%d task templates)" % (stage_title(sid), len(rs)))
        lines.append("")
        lines.append("| Task | Created by | Conditional subtasks a rule adds | Conditional subtasks no known rule adds | Subtasks with rules on Done / on Issue | Completed by |")
        lines.append("|---|---|---|---|---|---|")
        for r in rs:
            tpl = r["tpl"]
            name = "**%s**<br>%s<br>`%s`" % (tpl["name"], humanise_folder(tpl["sub"]) if tpl["sub"] else "", tpl["type"])
            if r["creators"]:
                cr = listing(["%s `%s`" % (when_clause(f["sentence"]), f["ruleName"]) for f in r["creators"]], 3)
            else:
                cr = "Nothing known \u2014 probably added by hand"
            ca = listing(["%s (%d rule%s)" % (M.sub_short(s), len(a), "" if len(a) == 1 else "s") for s, a in r["cond_added"]], 6)
            cu = listing([M.sub_short(s) for s in r["cond_unadded"]], 6)
            dn = []
            if r["done"]:
                dn.append("Done: " + "; ".join(r["done"][:4]) + ("; +%d more" % (len(r["done"]) - 4) if len(r["done"]) > 4 else ""))
            if r["issue"]:
                dn.append("Issue: " + "; ".join(r["issue"][:4]) + ("; +%d more" % (len(r["issue"]) - 4) if len(r["issue"]) > 4 else ""))
            if r["other"]:
                dn.append("Other: " + "; ".join(r["other"][:3]))
            if r["completers"]:
                co = listing(["%s `%s`" % (when_clause(f["sentence"]), f["ruleName"]) for f in r["completers"]], 3)
            else:
                co = "Staff (no rule known)"
            lines.append("| %s | %s | %s | %s | %s | %s |" % (
                cell(name), cell(cr), cell(ca), cell(cu), cell("<br>".join(dn)), cell(co)))
        lines.append("")
    return lines


def roadmap_section(M):
    """Roadmap tasks whose rule status is Planned / Not Started but which rules already reference."""
    flagged = [l for l in M.cross["linkage"] if (l.get("flag") or "").startswith("rules-exist")]
    flagged.sort(key=lambda l: (l["stage"] or "", l["id"]))
    planned_status = [l for l in M.cross["linkage"] if l["status"] == "planned"]
    lines = []
    lines.append("Rules are matched to roadmap tasks by `docs/rules_crossref.json`. These roadmap tasks are marked "
                 "*Planned* or *Not Started* for rules, yet at least one rule already refers to them, so the roadmap "
                 "status is probably stale and the rules can be used to fill in their subtasks.")
    lines.append("")
    lines.append("| Roadmap task | Stage | Task status | Rules status | Rules that create it | Rules that complete it | Rules that react to its subtasks |")
    lines.append("|---|---|---|---|---|---|---|")
    for l in flagged:
        rr = l.get("rules", {})
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            cell("**%s** (`%s`)" % (l["name"], l["id"])),
            cell(stage_name(l["stage"]) if l["stage"] else ""), cell(l["status"]), cell(l["ruleStatus"]),
            cell(listing(["`%s`" % x for x in rr.get("creates", [])], 4)),
            cell(listing(["`%s`" % x for x in rr.get("completes", [])], 4)),
            cell(listing(["`%s`" % x for x in rr.get("subtask-trigger", [])], 4))))
    lines.append("")
    refd = [l for l in planned_status if l.get("rules")]
    lines.append("Roadmap tasks with status `planned` (no template yet): **%d**, of which **%d** are referenced by a rule%s." % (
        len(planned_status), len(refd),
        (" (" + ", ".join(l["name"] for l in refd) + ")") if refd else ""))
    lines.append("")
    return lines, flagged, planned_status, refd


def gaps_section(M, rows):
    lines = []
    timers = sorted((n for n in M.g["nodes"] if n["kind"] == "timer"), key=lambda n: n["label"])
    never = [t for t in timers if t.get("neverStarted")]
    nocomp = [t for t in timers if t.get("noCompletionRule")]
    lines.append("**Timers that are never started by a rule (%d)**" % len(never))
    lines.append("")
    lines += ["- \u23f1 %s" % t["label"] for t in never] or ["- None."]
    lines.append("")
    lines.append("**Timers with no rule that runs when they expire (%d)**" % len(nocomp))
    lines.append("")
    lines += ["- \u23f1 %s" % t["label"] for t in nocomp] or ["- None."]
    lines.append("")
    # subtasks created by rules but missing from the template
    miss_sub = OrderedDict()
    for n in sorted((x for x in M.g["nodes"] if x["kind"] == "subtaskType" and not x.get("inRepo")), key=lambda x: x["id"]):
        roles = defaultdict(list)
        for f in M.out_eff.get(n["id"], []):
            roles[f["effect"]].append(f["ruleName"])
        for t in M.sub_trig.get(n["id"], []):
            roles["trigger"].append(t["ruleName"])
        miss_sub[n["id"]] = (n, roles)
    created_miss = [(n, r) for n, r in miss_sub.values() if "subtask:create" in r]
    lines.append("**Subtasks that rules add but the template does not contain (%d)**" % len(created_miss))
    lines.append("")
    for n, r in created_miss:
        tt = M.N.get("task:" + n.get("taskType", ""), {})
        tlabel = tt.get("label") or n.get("taskType")
        where = "task template exists" if tt.get("inRepo") else "task has no template"
        lines.append("- %s \u2014 in task %s (%s); added by %s" % (
            M.sub_short(n["id"]), tlabel, where, ", ".join("`%s`" % x for x in sorted(set(r["subtask:create"])))))
    if not created_miss:
        lines.append("- None.")
    lines.append("")
    other_miss = [(n, r) for n, r in miss_sub.values() if "subtask:create" not in r]
    lines.append("Other rule references to subtasks missing from the templates: **%d** (completed or listened to, never added)." % len(other_miss))
    lines.append("")
    # task types with no template
    miss_task = sorted((n for n in M.g["nodes"] if n["kind"] == "taskType" and not n.get("inRepo")), key=lambda n: (n["label"], n["id"]))
    lines.append("**Task types that rules reference but no template exists for (%d)**" % len(miss_task))
    lines.append("")
    for n in miss_task:
        roles = set()
        names = set()
        for f in M.out_eff.get(n["id"], []):
            roles.add({"task:create": "creates it", "task:complete": "completes it"}.get(f["effect"], f["effect"]))
            names.add(f["ruleName"])
        for e in M.edges:
            if e["kind"] == "triggers" and e["source"] == n["id"]:
                roles.add("reacts to it")
                names.add(e["ruleName"])
        for e in M.edges:
            if e["kind"] == "effects" and e["effect"].startswith("subtask") and M.task_of(e["target"]) == n["id"]:
                roles.add("works on its subtasks")
                names.add(e["ruleName"])
        for e in M.edges:
            if e["kind"] == "triggers" and M.task_of(e["source"]) == n["id"] and e["source"] != n["id"]:
                roles.add("reacts to its subtasks")
                names.add(e["ruleName"])
        lines.append("- %s \u2014 %s (%d rule%s: %s)" % (
            n["label"], ", ".join(sorted(roles)) or "referenced", len(names), "" if len(names) == 1 else "s",
            ", ".join("`%s`" % x for x in sorted(names)[:4]) + (", \u2026" if len(names) > 4 else "")))
    if not miss_task:
        lines.append("- None.")
    lines.append("")
    return lines, never, nocomp, created_miss, other_miss, miss_task


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--json", action="store_true", help="print a one-line JSON summary")
    args = ap.parse_args()
    try:
        M = Model()
        stage_charts = build_stage_charts(M)
        timer_charts = build_timer_charts(M)
        rows = build_rows(M)

        # structural self-check of every diagram
        node_counts = []
        for sid, sc, C in stage_charts:
            node_counts.append(C.check("%s/%s" % (sid, sc)))
        timer_counts = [C.check("timer " + tn["label"]) for tn, C in timer_charts]

        # reconciliation with the crossref
        S = M.cross["summary"]
        if len(rows) != S["taskTypesInRepo"]:
            raise ValueError("row count %d != crossref taskTypesInRepo %d" % (len(rows), S["taskTypesInRepo"]))
        no_rule_rows = sorted(r["tpl"]["type"] for r in rows if not r["has_rule_ref"])
        orphans = sorted(o["type"] for o in M.cross["orphanTasks"])
        road_lines, flagged, planned_status, refd = roadmap_section(M)
        gap_lines, never, nocomp, created_miss, other_miss, miss_task = gaps_section(M, rows)
        recon = OrderedDict([
            ("task templates (XML files)", (len(rows), S["taskTypesInRepo"], "taskTypesInRepo")),
            ("templates no rule references", (len(no_rule_rows), S["orphanTaskTypes"], "orphanTaskTypes")),
            ("task types rules reference with no template", (len(miss_task), S["brokenTaskTypes"], "brokenTaskTypes")),
            ("subtasks missing from templates (pairs)", (len(created_miss) + len(other_miss), S["brokenSubtaskPairs"], "brokenSubtaskPairs")),
            ("roadmap tasks flagged Planned/Not Started with rules", (len(flagged), S["flaggedRulesExistButPlannedOrNotStarted"], "flaggedRulesExistButPlannedOrNotStarted")),
            ("rules", (M.g["coverage"]["rules"], S["rules"], "rules")),
            ("inactive rules", (M.g["coverage"]["inactiveRules"], S["inactiveRules"], "inactiveRules")),
        ])
        recon_ok = all(a == b for a, b, _ in recon.values())
        if sorted(no_rule_rows) != orphans:
            recon_ok = False

        # ----- write the page -----
        L = []
        L.append("<!-- GENERATED FILE - DO NOT EDIT. Regenerate with: python rules_graph.py && python rules_map_docs.py -->")
        L.append("")
        L.append("# Workflow Rules Map")
        L.append("")
        L.append("> Generated by `rules_map_docs.py` from `rules/graph.json`, `docs/rules_crossref.json`, `roadmap.json` and "
                 "`tasks/**/*.xml` (rules data as of %s). Do not edit by hand; re-run `python rules_graph.py && python rules_map_docs.py`." % M.g["generatedAt"])
        L.append("")
        L.append("This page explains how the Encompass workflow rules connect the task templates. Part 1 is a set of "
                 "pictures (one per stage, one per timer). Part 2 is a table that says, for every task, what creates it, "
                 "what adds its optional subtasks, and what completes it. Anything the rules do not yet cover is shown "
                 "as a dashed box or listed under *Gaps to review*, not hidden.")
        L.append("")
        L.append("## How to read the pictures")
        L.append("")
        L.append("- **Square box** = a task. Staff work these; a rule can create them, complete them, or react when one of their subtasks is marked Done or Issue.")
        L.append("- **Rounded box** = something that happens outside a task: a field changes, a file is attached, a milestone completes, or the loan is created.")
        L.append("- **Stadium shape with \u23f1** = a timer. Timers are named only; durations are not shown.")
        L.append("- **Dashed box** = a task in another stage (or one with no template yet), or a gap where no known rule exists.")
        L.append("- **Arrow label** reads as a sentence: *\"Deny: Done \u2192 creates\"* means \"when the Deny subtask is marked Done, Encompass creates the task the arrow points to\". "
                 "*\"adds X\"* means a rule adds the subtask X to the target task. A dotted arrow means \"cancels\".")
        L.append("- Links that stay inside one task (one subtask completing another) are left out of the stage pictures.")
        L.append("")
        L.append("## Part 1: Pictures")
        L.append("")
        L.append("### Stage pictures")
        L.append("")
        cur = None
        stage_index = []
        for (sid, sc, C), cnt in zip(stage_charts, node_counts):
            if sid != cur:
                cur = sid
            title = stage_title(sid) + ((" \u2014 " + " + ".join(humanise_folder(x) for x in sc)) if sc is not None else "")
            L.append("#### %s" % title)
            L.append("")
            L.append("```mermaid")
            L.append(C.render())
            L.append("```")
            L.append("")
            stage_index.append((title, cnt))
        L.append("### Timer pictures")
        L.append("")
        L.append("Each picture shows what starts the timer, what happens when it runs out, and (dotted) what cancels it.")
        L.append("")
        timer_index = []
        for (tn, C), cnt in zip(timer_charts, timer_counts):
            L.append("#### \u23f1 %s" % tn["label"])
            L.append("")
            L.append("```mermaid")
            L.append(C.render())
            L.append("```")
            L.append("")
            timer_index.append((tn["label"], cnt))
        L.append("## Part 2: How each task is driven")
        L.append("")
        L.append("One row per task template (%d templates in `tasks/`). *Created by* lists the rules that create the task; "
                 "if none is known the task is probably added by hand. *Conditional subtasks* are the ones that are not created "
                 "with the task: the first column lists those a rule adds, the second those for which no rule is known yet "
                 "(candidates for the rules still to come). *Done / Issue* lists subtasks whose completion triggers a rule, with the "
                 "task or subtask it affects in brackets. Rule names are in code spans." % len(rows))
        L.append("")
        L += render_rows(M, rows)
        L.append("## Planned roadmap tasks that rules already reference")
        L.append("")
        L += road_lines
        L.append("## Counts that reconcile with the cross-reference")
        L.append("")
        L.append("| Count | This page | `docs/rules_crossref.json` | Source field |")
        L.append("|---|---|---|---|")
        for k, (a, b, f) in recon.items():
            L.append("| %s | %d | %d | `%s` |" % (k, a, b, f))
        L.append("")
        L.append("Templates with no rule reference on this page match the cross-reference orphan list exactly: **%s**." % ("yes" if sorted(no_rule_rows) == orphans else "NO"))
        L.append("")
        L.append("## Gaps to review")
        L.append("")
        L += gap_lines
        text = "\n".join(L).rstrip("\n") + "\n"
        os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
        with open(os.path.join(ROOT, OUT), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

        summary = OrderedDict([
            ("ok", True), ("file", OUT), ("tasks", len(rows)),
            ("stageDiagrams", len(stage_charts)), ("stageNodes", node_counts),
            ("timerDiagrams", len(timer_charts)), ("timerNodes", timer_counts),
            ("reconciled", recon_ok),
            ("flaggedPlanned", len(flagged)), ("tasksNoRule", len(no_rule_rows)),
            ("timersNeverStarted", len(never)), ("timersNoCompletion", len(nocomp)),
            ("subtasksCreatedNotInTemplate", len(created_miss)), ("taskTypesWithoutTemplate", len(miss_task)),
        ])
        if args.json:
            print(json.dumps(summary))
        else:
            print("Wrote %s: %d task rows, %d stage diagrams (nodes %s), %d timer diagrams, reconciled=%s" % (
                OUT, len(rows), len(stage_charts), node_counts, len(timer_charts), recon_ok))
            for k, (a, b, f) in recon.items():
                print("  %-55s page=%d crossref=%d (%s)" % (k, a, b, f))
        return 0 if recon_ok else 1
    except Exception as exc:  # noqa: BLE001
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print("error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
