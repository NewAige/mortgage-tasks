# Rules Interaction Map — Work Plan for Sonnet Agents

Goal: a visual map of how the Encompass workflow rules (`rules/`) fire, what they do inside
Encompass, and how they connect to the task templates (`tasks/`) and to each other.

Status: **planning**. 192 rules are imported (exports 1–20). More may follow, so every piece of
work must keep the map regenerable and must show gaps rather than hide them.

**Audience: operations staff learning how the workflow runs.** This decides the design:
- The primary view is the stage swimlanes. The focus view is secondary.
- Every label is plain English. Use the task or subtask display name, never the `type` key,
  and use the field label from `rules/field_labels.csv`. Raw IDs go in tooltips only.
- Each edge reads as a sentence: *"When **Underwrite – Deny** is marked Done → Encompass creates
  **Send Denial**."*
- Show timers by name only, e.g. "⏱ Counteroffer Warning". No durations are needed.
- Add guided walkthroughs: short, named scenarios ("A loan is denied", "Appraisal ordered → received",
  "Counteroffer expires") that step through the chain in order.

---

## Design principles (all agents)

1. **Generated, never hand-drawn.** The map is built from `rules/rules.json`, `tasks/**/*.xml`
   and `roadmap.json` by a script. When the next ~80 rules land, re-running
   `parse_rules.py`, then `rules_crossref.py`, then `rules_graph.py` must refresh everything.
   Nothing in the map is curated by hand. Human annotations go in one separate input file
   (WP-6).
2. **Incompleteness is first-class.** If a rule effect has no listener, or a listener has no
   producer, the map shows a dashed "open edge" labelled *no known rule yet*. It is not
   reported as an error. Each new import should close some of these open edges.
3. **One graph model, many views.** All views read one JSON graph (`rules/graph.json`).
   Views never re-derive logic from `rules.json`.
4. **Follow repo conventions.** Use Python stdlib only. The HTML follows the pattern of
   `docs/reconciliation_template.html`: a `__DATA__` placeholder is replaced with the payload.
   Generated files are never hand-edited. CDN scripts must be pinned to an exact version.

---

## What the data already gives us (from `rules/rules.json`)

| Trigger (event) | Rules | Effects that can cause it (chaining) |
|---|---|---|
| `field_modified` | 58 | `field:update` (27 steps) and user edits |
| `subtask_completed` | 48 | `subtask:complete` (53) and users |
| `file_attached` | 23 | users/vendors only (external) |
| `task_created` | 18 | `task:create` (95) |
| `timer_completed` | 15 | `timer:start` (19); `timer:cancel` (12) suppresses it |
| `milestone_completed` | 15 | users / Encompass milestone logic (external) |
| `task_completed` | 10 | `task:complete` (68) and users |
| `loan_created` | 5 | external |

`subtask:create` (63) adds subtasks to existing tasks; this is the main way conditional subtasks appear.

Terminal effects that leave the rules system (nothing downstream): `notification:send` (50),
`role:assign` (41), `document:sendrequest` (29), `enhancedcondition:*` (47), `order:create` (10),
`folder:move` (7), `disclosure:send` (4).

14 timers: Approval Expiration, Cancel Undisclosed Debt Monitoring, Closing, Counteroffer Closure,
Counteroffer Warning, Day Refresh, File Started Follow Up (15/30 Days) - Pre-Approval, Funding,
Live Follow Up (15/30 Days), Notice of Incomplete Closure, Notice of Incomplete Warning,
SSR Report(s) Available Scheduler.

There are two kinds of link between rules:
- **Direct chains.** An effect produces an event that another rule's filter matches, e.g.
  `task:create X` → a rule on `task_created` with `payload.type = X`.
- **Condition coupling.** A `field:update` of field F changes whether another rule's process
  `conditions` script (which reads `[F]`) passes. This is weaker but matters, so it is shown as
  a separate edge style.

---

## Work packages

The work runs in three waves. Packages in the same wave can run in parallel. Each package
lists its inputs, outputs and acceptance checks so that a Sonnet agent can work from it alone.

### Wave 1 — data model (blocking)

#### WP-1 · Graph builder `rules_graph.py` → `rules/graph.json`
- **Inputs:** `rules/rules.json`, `tasks/**/*.xml` (task `type`, `name`, subtask `type`,
  `autoCreate`), `roadmap.json` (stage, status).
- **Nodes:** `rule`, `taskType`, `subtaskType` (keyed `taskType|subtaskType`), `field`,
  `timer`, `document` (eFolder title), `milestone`, `external` (one per terminal action kind:
  notification, role, condition, order, folder, disclosure, docRequest), `user` (manual
  actor).
- **Edges** (each has `kind`, `ruleId`, `processId`, `conditions` text, `resolution`):
  - `triggers`: event source → rule (e.g. subtaskType → rule on `subtask_completed`,
    filtered by resolution).
  - `effects`: rule → target (task:create → taskType, subtask:complete → subtaskType,
    timer:start → timer, field:update → field, terminal actions → external node).
  - `cancels`: rule → timer.
  - `contains`: taskType → subtaskType (from the XML), with `autoCreate`.
  - `conditionReads`: field → rule process, parsed from `[FIELD]` tokens in condition scripts.
- **Derived flags:** `openEffect` (an effect with no listening rule), `openTrigger` (a
  listener with no rule or template producing the event), `brokenRef` (copied from
  `docs/rules_crossref.json`), `inactive` (rule status), and `stage` on every task node.
- **Hooks for growth:** record `sourceFiles` on rule nodes. Add a `coverage` block with counts
  of open edges, rules and exports, so imports can be compared over time.
- **Accept:** the script is deterministic (two runs produce byte-identical output) and supports
  `--json`. Node and edge counts are printed. Every effect and trigger in `rules.json` appears
  as exactly one edge.

#### WP-2 · Chain tracer (part of `rules_graph.py`, run before WP-1 is final)
- Compute **cascades**: starting from each external entry point (`loan_created`,
  `file_attached`, `milestone_completed`, user subtask completion, user field edit), follow
  `effects` → `triggers` edges and timers. Stop at terminal nodes or after a configurable depth.
- Detect **cycles** (A creates X → rule on X completes Y → … → A), and flag rules that create a
  task with `noDuplicate=false`.
- Detect **fan-in conflicts**: two rules that complete or create the same task or subtask with
  different resolutions.
- Write `rules/cascades.json` and a section in `docs/RULES_MAP.md` (WP-5).
- **Accept:** check by hand against 3 known chains: the `Approval Expiration` timer chain,
  `Task_Cancel_AllAdverse`, and the FraudX attach → create → complete chain.

### Wave 2 — views (needs `graph.json`; the three packages run in parallel)

#### WP-3 · Interactive map page `docs/rules_map_template.html` → `docs/rules_map.html`
- Single self-contained page that renders the WP-1 graph. Use pinned Cytoscape.js (with the
  dagre layout) from cdnjs, or plain D3.
- **View A, Lifecycle swimlanes (primary, opens by default):** columns are stages 1–7, task
  nodes sit in their stage, and milestones mark the column boundaries. Rules are drawn as labelled
  arrows, not as boxes, so staff see "this causes that". Loan events (loan created, file attached,
  user edits) enter from the left; outside actions (emails, documents sent, orders, conditions)
  appear as small icons on the task they belong to.
- **View B, "What happens when…" focus:** pick a task, subtask or field. The view shows what
  starts it and what it causes, a few steps each way, with each edge as a one-line sentence.
- **View C, Timers:** "⏱ name" with what starts it, what happens when it runs out, and what
  stops it early.
- **Walkthroughs:** 6–10 named scenarios, generated as chains from WP-2 and titled through
  `rules/annotations.json`. Each is a numbered step list with the map highlighting each step.
- Edge styles: direct chain (solid), condition coupling (dotted), open edge (dashed grey,
  *no known rule yet*), broken ref (red), inactive rule (faded).
- Filters by event type, by stage and by action kind, plus an "only show open edges" toggle.
- Light and dark theme tokens, usable at phone width.
- **Accept:** the page loads offline from file except for the pinned CDN script. It renders
  all 119 rules without overlap in View B, and its search finds any type string.

#### WP-4 · Static diagrams `docs/RULES_MAP.md` (Mermaid)
- Generated from `graph.json`. Produce one Mermaid flowchart per stage and one per timer chain,
  because a single Mermaid chart with 119 rules is unreadable.
- These render directly on GitHub and serve as the review artefact in PRs.
- **Accept:** each chart has at most about 40 nodes and parses with the Mermaid CLI (or keep
  it to syntax that is known to be safe).

#### WP-5 · Workflow ↔ rules interaction report (section of `docs/RULES_MAP.md`)
For each task template, answer these questions in one table row per task:
- What creates this task: a rule, a manual action or nothing known?
- Which `autoCreate="false"` (conditional/later) subtasks a rule adds, and which **no known rule
  adds** (these are candidates that the missing ~80 rules should cover).
- Which subtasks have rules on `Done` and on `Issue`, and which resolution branches are missing.
- What completes the task.

Also list roadmap tasks still `planned` that rules already reference. These are the 20 in the
crossref, and the rules can be used to define their subtasks.

- **Accept:** every task XML has a row, and the counts reconcile with
  `docs/RULES_CROSSREF.md`.

### Wave 3 — integration and import readiness

#### WP-6 · Labels and annotations (hand-maintained inputs)
- **`rules/field_labels.csv`** has already been seeded with all 121 fields the rules read or
  set: 45 custom `CX.*` fields and 76 standard ones. Spelling variants are merged (`#16` → `16`,
  `cx.` → `CX.`). The user fills in the `label` column. The agent extends this file (it must not
  regenerate it) when new fields appear, and keeps any labels already filled in.
- **`rules/annotations.json`** holds the milestone → stage map (see below), walkthrough titles,
  and labels for notification `templateId`s and `serviceRuleIds` where these can be inferred
  from the rule names.
- `rules_graph.py` merges both files. A missing label falls back to the raw ID and never fails
  the build.
- **Proposed milestone → stage map** (to be confirmed by the user). The *"- E"* suffix is
  assumed to mean the Equity/HELOC track:

  | Milestone | Stage |
  |---|---|
  | Pre-Qual/App, Broker Import | 1 Origination |
  | Pre Processing, Processing, Processing - E | 2 Processing |
  | Submittal - E, Cond. Approval, Cond. Approval - E, Clear to Close - E | 3 Underwriting |
  | Doc Prep - E | 4 Closing |
  | Funding, Boarding - E | 5 Funding |

#### WP-7 · Wiring and docs
- Add a "Rules Map" link to `roadmap.html`, next to the existing Workflow Rules link. Add a
  section to `docs/RULES.md` and a script row in `CLAUDE.md`.
- Extend `RULES.md` → *Ingesting a fresh export* with a step to run `rules_graph.py` and review
  open edges that closed or opened.

#### WP-8 · Import diff `rules_graph.py --diff <old graph.json>`
- For each new batch of the ~80 remaining rules, report new rules, open edges closed, new open
  edges, new broken refs and new cycles. This is the PR summary for every rule import.
- **Accept:** remove one export file, rebuild, re-add it, and diff. The report must list exactly
  that file's rules.

---

## Dependency summary

```
WP-1 ──┬─> WP-2 ──┐
       ├─> WP-3   ├─> WP-7 ─> WP-8
       ├─> WP-4 <─┘
       └─> WP-5
WP-6 can start any time (seeded from rules.json); WP-1 merges it when present.
```

Recommended order: **WP-1 and WP-6** in parallel, then **WP-2, WP-3, WP-4 and WP-5** in
parallel, then **WP-7 and WP-8**. Each package is its own branch, commit and PR. Agents must not
edit `rules/exports/` or the generated docs from other scripts.

## Brief template for each Sonnet agent

> Read `CLAUDE.md`, `docs/RULES.md` and `docs/RULES_MAP_PLAN.md` (your package: WP-n).
> Implement only WP-n. Use Python stdlib only and keep output deterministic. Do not edit
> `rules/exports/` or any file another script generates. Run `parse_rules.py`, then
> `rules_crossref.py`, then your script, and paste the acceptance-check output into your
> final report. List anything the data could not answer as an open question rather than
> guessing.

---

## Decisions and open questions

Decided (user, 2026-10-19):
- The remaining rules are imported (192 total). WP-8 (import diff) is kept but has low priority.
- The audience is operations staff, so the swimlanes and walkthroughs come first.
- Timers are shown by name only.

Open:
1. **Field labels.** The user fills in `rules/field_labels.csv`. Until then the map shows raw IDs.
2. **Milestone → stage map.** Confirm the table in WP-6, including what *"- E"* means.
3. **Hosting.** Is a repo file (`docs/rules_map.html`, opened from `roadmap.html`) enough, or is a
   shareable hosted page also wanted for staff?
