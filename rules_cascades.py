#!/usr/bin/env python3
"""
rules_cascades.py - Trace rule chains over the rules graph (rules/cascades.json).

Reads rules/graph.json (rules_graph.py) and rules/annotations.json and works out, for the
rules map, what each outside event sets off:

  walkthroughs  one ordered step list per annotations.json `walkthroughCandidates` entry,
                started from whatever makes the entry rules fire
  cascades      one per external entry point (a node a user / integration / Encompass drives
                from outside the rules, or "loan created") that leads to >= 2 steps
  cycles        rule chains that come back to a rule already on the path
  conflicts     the same task / subtask completed with different resolutions, or created
                with noDuplicate off, by two or more rules

Traversal (direct causation only):
    node --triggers--> rule --effects/cancels--> target node --triggers--> rule ...
An effect edge's `heardBy` says which active rules hear the event it produces (resolution and
field-value matching is already encoded there), so a chain only continues into those rules.
timer:start -> timer node -> the timer_completed rules works the same way. `conditionReads`,
`contains` and `enters` edges are context, never followed. Inactive rules are skipped.
Breadth-first from the start nodes, each edge visited once, default depth limit 6.

Depth: a rule reached from an entry has depth 0; the effects of a rule carry the rule's depth;
the next rule it triggers is depth + 1. `truncated` / the depth limit cut off a rule beyond it.

Output is deterministic (sorted ids, generatedAt copied from graph.json).

Usage (paths default relative to this file):
    python rules_cascades.py
    python rules_cascades.py --json
    python rules_cascades.py --max-depth 8

Exit codes: 0 = success, 1 = error.
"""

import argparse
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict, deque

ROOT = os.path.dirname(os.path.abspath(__file__))

EFFECT_EVENT = {
    "task:create": "task_created",
    "task:complete": "task_completed",
    "subtask:complete": "subtask_completed",
    "field:update": "field_modified",
    "timer:start": "timer_completed",
}


# A rule doing this many same-kind actions at once is shown as one step.
GROUP_MIN = 5
GROUP_VERBS = {
    ("task:complete", "NA"): "closes %d tasks as not applicable",
    ("task:complete", None): "completes %d tasks",
    ("subtask:complete", "NA"): "marks %d subtasks not applicable",
    ("subtask:complete", None): "marks %d subtasks Done",
    ("task:create", None): "creates %d tasks",
    ("subtask:create", None): "adds %d subtasks",
}


def group_key(eff):
    # only merge actions that share a condition, otherwise the step would hide which applies when
    return (eff["kind"], eff.get("effect"), eff.get("resolution"), eff.get("conditionsText") or "")


TRIGGER_TAIL = re.compile(r', the rule ".*" runs\.$')


def rel(path):
    try:
        return os.path.relpath(path, ROOT).replace(os.sep, "/")
    except ValueError:
        return path


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return s or "walkthrough"


class Tracer:
    def __init__(self, graph, max_depth):
        self.max_depth = max_depth
        self.nodes = {n["id"]: n for n in graph["nodes"]}
        self.edges = {e["id"]: e for e in graph["edges"]}
        # rule node id -> effects/cancels edges, in effect order
        self.rule_out = defaultdict(list)
        # (source node, rule id) -> triggers edges
        self.trig = defaultdict(list)
        # source node -> triggers edges
        self.trig_from = defaultdict(list)
        self.rules = {}      # rule id -> rule node
        for n in graph["nodes"]:
            if n["kind"] == "rule":
                self.rules[n["ruleId"]] = n
        for e in sorted(graph["edges"], key=lambda x: x["id"]):
            if e["kind"] in ("effects", "cancels") and not e.get("inactive"):
                self.rule_out[e["source"]].append(e)
            elif e["kind"] == "triggers" and not e.get("inactive"):
                self.trig[(e["source"], e["ruleId"])].append(e)
                self.trig_from[e["source"]].append(e)
        for lst in self.rule_out.values():
            lst.sort(key=lambda x: (x.get("effectIndex", 0), x["id"]))

    def heard_edges(self, eff):
        """triggers edges that the effect `eff` sets off (direct chain)."""
        ev = EFFECT_EVENT.get(eff.get("effect"))
        if not ev:
            return []
        out = []
        for rid in sorted(eff.get("heardBy") or []):
            for t in self.trig.get((eff["target"], rid), []):
                if t["event"] == ev:
                    out.append(t)
        return sorted(out, key=lambda x: x["id"])

    def trace(self, first_edges):
        """BFS from a list of triggers edges (depth 0). Returns (steps, truncated)."""
        steps, truncated = [], False
        seen_edges, expanded = set(), set()
        queue = deque((t, 0) for t in sorted(first_edges, key=lambda x: x["id"]))
        while queue:
            t, depth = queue.popleft()
            if t["id"] in seen_edges:
                continue
            seen_edges.add(t["id"])
            steps.append(self._step(t, depth))
            rnode = t["target"]
            if rnode in expanded:
                continue
            expanded.add(rnode)
            effs = [e for e in self.rule_out.get(rnode, []) if e["id"] not in seen_edges]
            groups = OrderedDict()
            for eff in effs:
                seen_edges.add(eff["id"])
                groups.setdefault(group_key(eff), []).append(eff)
            for eff in effs:
                grp = groups[group_key(eff)]
                if len(grp) < GROUP_MIN or (eff.get("effect"), None) not in GROUP_VERBS:
                    steps.append(self._step(eff, depth))
                elif eff is grp[0]:
                    steps.append(self._group_step(grp, depth))
                nxt = [h for h in self.heard_edges(eff) if h["id"] not in seen_edges]
                if nxt and depth + 1 > self.max_depth:
                    truncated = True
                    continue
                for h in nxt:
                    queue.append((h, depth + 1))
        for i, s in enumerate(steps, 1):
            s["n"] = i
        return steps, truncated

    def _step(self, edge, depth):
        sentence = edge["sentence"]
        if edge["kind"] == "triggers":
            # operations staff need the event, not the rule's internal name
            sentence = TRIGGER_TAIL.sub(":", sentence)
        elif ", Encompass " in sentence:
            # the preceding trigger step already says "When ...:"
            sentence = "Encompass " + sentence.split(", Encompass ", 1)[1]
        return OrderedDict([("n", 0), ("depth", depth), ("edgeId", edge["id"]), ("edgeIds", [edge["id"]]),
                            ("from", edge["source"]), ("to", edge["target"]), ("toIds", [edge["target"]]),
                            ("sentence", sentence), ("kind", edge["kind"]), ("ruleName", self.rule_name(edge))])

    def _group_step(self, grp, depth):
        """One step standing for many same-kind effects of one rule (e.g. closing 45 tasks as NA)."""
        first = grp[0]
        labels = [self.label(e["target"]) for e in grp]
        verb = GROUP_VERBS.get((first.get("effect"), first.get("resolution")),
                               GROUP_VERBS[(first.get("effect"), None)])
        cond = first.get("conditionsText")
        sentence = "Encompass %s: %s%s." % (verb % len(grp), ", ".join(labels),
                                            " (only if %s)" % cond if cond else "")
        return OrderedDict([("n", 0), ("depth", depth), ("edgeId", first["id"]),
                            ("edgeIds", [e["id"] for e in grp]), ("from", first["source"]),
                            ("to", first["target"]), ("toIds", [e["target"] for e in grp]),
                            ("sentence", sentence), ("kind", first["kind"]), ("ruleName", self.rule_name(first)),
                            ("grouped", len(grp))])

    def rule_name(self, edge):
        rid = edge["target"] if edge["kind"] == "triggers" else edge["source"]
        return self.nodes.get(rid, {}).get("label", "")

    def label(self, nid):
        return self.nodes.get(nid, {}).get("label", nid)


def collect(steps):
    nids, eids = set(), set()
    for s in steps:
        nids.add(s["from"])
        nids.update(s["toIds"])
        eids.update(s["edgeIds"])
    return sorted(nids), sorted(eids)


def build(args):
    graph = load_json(args.graph)
    ann = load_json(args.annotations) if os.path.isfile(args.annotations) else {}
    T = Tracer(graph, args.max_depth)
    rules_by_name = defaultdict(list)
    for rid, n in T.rules.items():
        rules_by_name[n["label"]].append(rid)

    # ---- walkthroughs ---------------------------------------------------------------------------
    walks, used_ids = [], set()
    for cand in ann.get("walkthroughCandidates", []):
        entry_names = list(cand.get("entryRules", []))
        first = []
        for nm in entry_names:
            for rid in rules_by_name.get(nm, []):
                for (src, r), lst in T.trig.items():
                    if r == rid:
                        first.extend(lst)
        steps, trunc = T.trace(first)
        nids, eids = collect(steps)
        wid = slugify(cand.get("title"))
        base, k = wid, 2
        while wid in used_ids:
            wid, k = "%s-%d" % (base, k), k + 1
        used_ids.add(wid)
        walks.append(OrderedDict([("id", wid), ("title", cand.get("title")), ("why", cand.get("why")),
                                  ("entryRules", entry_names), ("steps", steps), ("nodeIds", nids),
                                  ("edgeIds", eids), ("truncated", trunc)]))

    # ---- cascades -------------------------------------------------------------------------------
    entry_nodes = {}
    for e in graph["edges"]:
        if e["kind"] == "enters":
            entry_nodes[e["target"]] = e["sentence"].rstrip(".")
    if "entry:loan_created" in T.nodes and T.trig_from.get("entry:loan_created"):
        entry_nodes["entry:loan_created"] = "A loan is created"
    cascades = []
    for nid in sorted(entry_nodes):
        steps, _ = T.trace(T.trig_from.get(nid, []))
        if len(steps) < 2:
            continue
        nids, eids = collect(steps)
        cascades.append(OrderedDict([("entry", nid), ("label", entry_nodes[nid]),
                                     ("maxDepth", max(s["depth"] for s in steps)),
                                     ("nodeIds", nids), ("edgeIds", eids)]))

    # ---- cycles (strongly connected rule groups) --------------------------------------------------
    succ = defaultdict(set)         # rule node -> rule nodes it can set off
    via = defaultdict(list)         # (rule node, rule node) -> [(effect edge, target)]
    for rnode, effs in T.rule_out.items():
        for eff in effs:
            for h in T.heard_edges(eff):
                succ[rnode].add(h["target"])
                via[(rnode, h["target"])].append(eff)
    cycles = []
    for comp in sccs(sorted(T.rule_out), succ):
        comp_set = set(comp)
        if len(comp) == 1 and comp[0] not in succ[comp[0]]:
            continue
        nids = set(comp)
        for a in comp:
            for b in succ[a]:
                if b in comp_set:
                    nids.update(eff["target"] for eff in via[(a, b)])
        cycles.append(OrderedDict([
            ("nodeIds", sorted(nids)),
            ("ruleNames", sorted(T.nodes[c]["label"] for c in comp))]))
    cycles.sort(key=lambda c: (c["ruleNames"], c["nodeIds"]))

    # ---- conflicts ----------------------------------------------------------------------------------
    groups = defaultdict(list)
    for e in graph["edges"]:
        if e["kind"] == "effects" and not e.get("inactive") and \
                e.get("effect") in ("task:create", "subtask:create", "task:complete", "subtask:complete"):
            groups[(e["target"], e["effect"])].append(e)
    conflicts = []
    for (tgt, eff), lst in sorted(groups.items()):
        names = sorted({e["ruleName"] for e in lst})
        if len(names) < 2:
            continue
        if eff.endswith(":complete"):
            res = sorted({e.get("resolution") or "(default)" for e in lst})
            if len(res) < 2:
                continue
        else:
            dup = sorted({e["ruleName"] for e in lst if e.get("noDuplicate") is False})
            if len(dup) < 2:
                continue
            names, res = dup, ["noDuplicate=false"]
        conflicts.append(OrderedDict([("target", tgt), ("targetLabel", T.nodes[tgt]["label"]), ("effect", eff),
                                      ("rules", names), ("resolutions", res)]))

    out = OrderedDict([("generatedAt", graph.get("generatedAt")), ("walkthroughs", walks),
                       ("cascades", cascades), ("cycles", cycles), ("conflicts", conflicts)])
    return out


def sccs(nodes, succ):
    """Tarjan, iterative; returns components as sorted lists, deterministic order."""
    index, low, on, stack, out, counter = {}, {}, set(), [], [], [0]
    allnodes = sorted(set(nodes) | set(x for s in succ.values() for x in s))
    for root in allnodes:
        if root in index:
            continue
        work = [(root, iter(sorted(succ.get(root, ()))))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on.add(root)
        while work:
            v, it = work[-1]
            adv = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]
                    counter[0] += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter(sorted(succ.get(w, ())))))
                    adv = True
                    break
                if w in on:
                    low[v] = min(low[v], index[w])
            if adv:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                out.append(sorted(comp))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description="Trace rule cascades (rules/cascades.json).")
    ap.add_argument("--graph", default=os.path.join(ROOT, "rules", "graph.json"))
    ap.add_argument("--annotations", default=os.path.join(ROOT, "rules", "annotations.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "rules", "cascades.json"))
    ap.add_argument("--max-depth", type=int, default=6)
    ap.add_argument("--json", action="store_true", help="print a machine-readable summary")
    args = ap.parse_args()
    try:
        res = build(args)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=False)
            fh.write("\n")
        summary = OrderedDict([
            ("ok", True), ("walkthroughs", len(res["walkthroughs"])),
            ("walkthrough_steps", sum(len(w["steps"]) for w in res["walkthroughs"])),
            ("truncated_walkthroughs", sum(1 for w in res["walkthroughs"] if w["truncated"])),
            ("cascades", len(res["cascades"])), ("cycles", len(res["cycles"])),
            ("conflicts", len(res["conflicts"])), ("json", rel(args.out))])
    except Exception as exc:  # noqa: BLE001
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print("error: %s" % exc, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print("Wrote %d walkthroughs, %d cascades, %d cycles, %d conflicts -> %s" % (
            summary["walkthroughs"], summary["cascades"], summary["cycles"], summary["conflicts"], summary["json"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
