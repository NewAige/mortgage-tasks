#!/usr/bin/env python3
"""
rules_map.py - Build the interactive rules map page (docs/rules_map.html).

Reads the rules graph (rules/graph.json, from rules_graph.py), the milestone annotations
(rules/annotations.json) and, when present, the cascade analysis (rules/cascades.json).
The graph is trimmed to what the page needs and embedded in docs/rules_map_template.html
at the `__DATA__` placeholder, so the output is one self-contained file that opens straight
from disk (no fetch, no CDN).

Missing rules/cascades.json is not an error: the page still renders and its Walkthroughs
tab says that scenarios are not available yet.

Never hand-edit docs/rules_map.html; edit docs/rules_map_template.html instead.

Usage (paths default relative to this file):
    python rules_map.py
    python rules_map.py --json
    python rules_map.py --cascades /path/to/cascades.json

Return value (stdout, or JSON with --json):
    {"ok": true, "out": "...", "bytes": N, "payloadBytes": N, ...}
    {"ok": false, "error": "<message>"}

Exit codes: 0 = success, 1 = error.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

STAGES = [
    ["1_origination", "Origination"],
    ["2_processing", "Processing"],
    ["3_underwriting", "Underwriting"],
    ["4_closing", "Closing"],
    ["5_funding", "Funding"],
    ["6_pre-closing-qc", "Pre-Closing QC"],
    ["7_post-closing-qc", "Post-Closing QC"],
]

KIND_MAP = {
    "taskType": "task", "subtaskType": "subtask", "field": "field", "timer": "timer",
    "rule": "rule", "milestone": "milestone", "document": "document",
    "external": "external", "entry": "entry",
}

_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="rules_map.py">
<style>*,*::before,*::after{box-sizing:border-box}img,svg{max-width:100%}</style>
</head>
<body>
"""
_FOOT = """
</body>
</html>
"""


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def rel(path):
    try:
        return os.path.relpath(path, ROOT).replace(os.sep, "/")
    except ValueError:
        return path


def build_payload(graph, annotations, cascades):
    ann_ms = (annotations or {}).get("milestones", {})
    # milestone raw name -> (display name, tag)
    equity = {}
    for name, info in sorted(ann_ms.items()):
        if info.get("track") == "equity":
            disp = name[:-4] if name.endswith(" - E") else name
            equity[name] = disp

    def clean(text):
        if not text:
            return text
        for raw in sorted(equity, key=len, reverse=True):
            text = text.replace(raw, equity[raw] + " (Equity track)")
        return text

    nodes = {}
    for n in sorted(graph["nodes"], key=lambda x: x["id"]):
        k = KIND_MAP.get(n["kind"])
        if not k:
            continue
        o = {"k": k, "l": n.get("label") or n["id"]}
        if n.get("stage"):
            o["s"] = n["stage"]
        if n.get("brokenRef"):
            o["rb"] = 1
        if n.get("inactive"):
            o["ia"] = 1
        if k == "task":
            o["raw"] = n.get("type", "")
            if n.get("status"):
                o["st"] = n["status"]
            if n.get("inRepo") is False:
                o["nr"] = 1
        elif k == "subtask":
            o["raw"] = n.get("type", "")
            o["p"] = "task:" + n.get("taskType", "")
            if n.get("autoCreate") is False:
                o["cond"] = 1
        elif k == "field":
            o["raw"] = n.get("fieldId", "")
        elif k == "timer":
            o["raw"] = n.get("timerId", "")
        elif k == "milestone":
            raw = n.get("title") or n["label"]
            if raw in equity:
                o["l"] = equity[raw]
                o["tr"] = "equity"
            else:
                o["raw"] = raw
        elif k == "external":
            o["xk"] = n.get("externalKind", "")
        elif k == "rule":
            o["ev"] = n.get("event", "")
            o["l"] = n.get("label") or n["id"]
        nodes[n["id"]] = o

    edges = []
    for e in sorted(graph["edges"], key=lambda x: x["id"]):
        kind = e["kind"]
        if kind == "contains":
            continue
        o = {"i": e["id"], "k": kind, "s": e["source"], "t": e["target"]}
        if e.get("ruleId"):
            o["r"] = "rule:" + e["ruleId"]
        if kind in ("effects", "cancels"):
            o["ef"] = e.get("effect", "")
            o["sn"] = clean(e.get("sentence", ""))
            if e.get("openEffect"):
                o["oe"] = 1
        elif kind == "enters":
            o["sn"] = clean(e.get("sentence", ""))
            o["ev"] = e.get("event", "")
        elif kind == "triggers":
            o["ev"] = e.get("event", "")
        if e.get("brokenRef"):
            o["rb"] = 1
        if e.get("inactive"):
            o["ia"] = 1
        edges.append(o)

    cov = graph.get("coverage", {})
    payload = {
        "gen": graph.get("generatedAt", ""),
        "stages": STAGES,
        "n": nodes,
        "e": edges,
        "cov": {k: cov.get(k) for k in (
            "activeRules", "rules", "inactiveRules", "openEffects", "openTriggers",
            "brokenRefNodes", "exports", "fieldsWithoutLabel")},
        "hasCasc": bool(cascades),
        "wt": [], "cy": [], "cf": [],
    }
    if cascades:
        for w in cascades.get("walkthroughs", []):
            payload["wt"].append({
                "id": w.get("id"), "title": w.get("title"), "why": w.get("why"),
                "truncated": bool(w.get("truncated")),
                "steps": [{
                    "n": s.get("n"), "e": s.get("edgeIds") or ([s["edgeId"]] if s.get("edgeId") else []),
                    "f": s.get("from"),
                    "t": s.get("toIds") or ([s["to"]] if s.get("to") else []),
                    "sn": clean(s.get("sentence", "")), "k": s.get("kind"),
                    "g": s.get("grouped"), "rn": s.get("ruleName"),
                } for s in w.get("steps", [])],
                "nodes": w.get("nodeIds", []),
            })
        payload["cy"] = [{"nodes": c.get("nodeIds", []), "rules": c.get("ruleNames", [])}
                         for c in cascades.get("cycles", [])]
        payload["cf"] = [{
            "t": c.get("target"), "tl": c.get("targetLabel"), "ef": c.get("effect"),
            "rules": c.get("rules", []), "res": c.get("resolutions", []),
        } for c in cascades.get("conflicts", [])]
    return payload


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build docs/rules_map.html")
    ap.add_argument("--graph", default=os.path.join(ROOT, "rules", "graph.json"))
    ap.add_argument("--annotations", default=os.path.join(ROOT, "rules", "annotations.json"))
    ap.add_argument("--cascades", default=os.path.join(ROOT, "rules", "cascades.json"))
    ap.add_argument("--template", default=os.path.join(ROOT, "docs", "rules_map_template.html"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "rules_map.html"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        graph = load_json(args.graph)
        annotations = load_json(args.annotations) if os.path.exists(args.annotations) else {}
        cascades = load_json(args.cascades) if os.path.exists(args.cascades) else None
        payload = build_payload(graph, annotations, cascades)
        with open(args.template, encoding="utf-8") as fh:
            template = fh.read()
        if "__DATA__" not in template:
            raise ValueError("template missing __DATA__ placeholder: %s" % args.template)
        blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"),
                          sort_keys=True).replace("<", "\\u003c")
        html = _HEAD + template.replace("__DATA__", blob) + _FOOT
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(html)
        result = {
            "ok": True, "out": rel(args.out), "bytes": len(html.encode("utf-8")),
            "payloadBytes": len(blob.encode("utf-8")),
            "nodes": len(payload["n"]), "edges": len(payload["e"]),
            "walkthroughs": len(payload["wt"]), "cycles": len(payload["cy"]),
            "conflicts": len(payload["cf"]), "cascadesPresent": bool(cascades),
        }
    except (OSError, ValueError, KeyError) as exc:
        result = {"ok": False, "error": str(exc)}
        print(json.dumps(result) if args.json else "error: %s" % exc, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("wrote %s (%d bytes; payload %d bytes; %d nodes, %d edges, %d walkthroughs)" % (
            result["out"], result["bytes"], result["payloadBytes"], result["nodes"],
            result["edges"], result["walkthroughs"]))
        if not cascades:
            print("note: %s not found - Walkthroughs tab will be empty" % rel(args.cascades))
    return 0


if __name__ == "__main__":
    sys.exit(main())
