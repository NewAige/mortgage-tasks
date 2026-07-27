# Reconciliation Runbook — resolving ledger rows

How to take a row from the reconciliation ledger (`docs/reconciliation.html`, section
"The ledger") where Encompass and the repo disagree, apply the winning side to the repo,
and leave the artefacts consistent.

Written after the 2026-07-27 pass that resolved five rows. Read this end to end before
touching a task — most of the value is in [§7 Gotchas](#7-gotchas-read-this-part), which
is the list of things that are not obvious from the code.

---

## 1. What a "row" is

The ledger has one row per task type. A row can be:

| Row kind | Meaning | In scope for this runbook |
|---|---|---|
| **Both sides, disagreeing** | Same `type` in Encompass and the repo, fields differ | **Yes** — this is the normal case |
| Live in Encompass only | Untracked in git; needs a backfill | No — that's authoring a new task |
| Committed to repo only | Never deployed; needs a deploy-or-drop call | No |

As of the last pass: **38 of 43** shared task types still differ, across **197** delta rows.

---

## 2. The decision comes from the user

You do not pick the winner. The user walks the ledger and calls each row —
"copy the Encompass version over the repo version" or the reverse.

**If the transcript is ambiguous, ask before editing.** In the 2026-07-27 pass two of the
five calls were garbled in dictation; asking took one `AskUserQuestion` round and avoided
rewriting 28 subtasks the wrong way. Batch the ambiguous ones into a single question rather
than asking one at a time.

---

## 3. Where the Encompass values actually live

`compare_configured.py` reads raw exports from `../import/Configured Task/`. **That directory
sits outside the repo and is usually absent from a fresh clone**, so you normally cannot read
the Encompass side directly.

What you *can* read, both committed:

| Source | Gives you |
|---|---|
| `docs/comparison_deltas.csv` | Every recorded difference, with `repo_value` and `encompass_value` per field |
| `docs/reconciliation.html` (embedded JSON payload) | Each Encompass task's name, group, file, and **ordered subtask type list** |

Together those are enough to reconstruct the Encompass side of any differing row — that is
exactly what `reconcile_adopt.py` does. Both tools expose `load_payload()` if you need to
poke at the snapshot directly; its keys are `stats`, `rows` (same shape as the CSV),
`encompass_tasks_detail` / `repo_tasks_detail`
(`{type: {name, group, file, subs: [ordered subtask types]}}`), and the aggregate blocks
`assignees`, `groups`, `separators`, `placeholders`, `workspaces`, `namespace_violations`,
`duplicate_names`.

**Only these task attributes are diffed** (`COMPARED_FIELDS` in `compare_configured.py`):
`name`, `required`, `priority`, `rank`, `duration`, `durationFormat`, `calendar`,
`autocomplete`, `autoCreate`, `taskGroupTemplateName`, `comments`.
Subtasks are diffed on `description` and `rank` only. Anything else — subtask `autoCreate`,
`category`, `priority`, per-subtask associations — **is not recorded**, so if Encompass differs
there you cannot know it. Infer from the file's own patterns, and write down what you inferred.

If `../import/Configured Task/` *is* present, ignore all of the above and just read the exports.
They are authoritative and this whole reconstruction step disappears.

---

## 4. Procedure

### Step 0 — Orient
Confirm the branch you have been told to develop on. Find the task types behind the names the
user said; ledger names are display names and several are ambiguous.

> Example: the user said "Order Appraisal, Encompass calls that Appraisal Invoice". That is
> `Processing_Appraisal_Order`. There is *also* an Encompass-only task literally named
> "Order Appraisal" under `Processing_Appraisal_Ordering`. Match on the pair of names the
> user gives you, not on one of them.

### Step 1 — Read the deltas
Dump every row for your task types from `comparison_deltas.csv` and read them. This is the
complete change list; nothing else about the task differs.

### Step 2 — Apply
`python reconcile_adopt.py --types <TYPE> --dry-run`, read the plan, then drop `--dry-run`
([§8](#8-scripts)). Do not hand-edit the XML — the files are single-line and unforgiving.

### Step 3 — Verify every delta is resolved
`reconcile_adopt.py` re-verifies automatically after writing and exits non-zero if anything
is unresolved — so a clean exit *is* this step. Re-run later with `--verify` to re-check
without applying. It must report **0 failures** before you commit.

### Step 4 — Validate
- Every `tasks/**/*.xml` still parses.
- No duplicate `id` across `tasks/`.
- Subtask ranks are `1..N` with no gaps, in the Encompass order.
- `required="true"` on every subtask (see CLAUDE.md — `autoCreate` is the conditional field).

### Step 5 — Sync `roadmap.json`
Regenerate the `subtasks` array of each touched task from the new XML, then update
`metadata.lastUpdated` and append one `activityLog` entry per task with
`"action": "updated"`. Do **not** touch `metadata.completedTasks` — nothing was newly completed.

### Step 6 — Refresh the reconciliation artefacts
If you have the exports: `python compare_configured.py`. Done.

If you do not: `python reconcile_refresh.py --resolved <TYPE>...`. It recomputes the repo side from
`tasks/` for real, carries the Encompass side forward from the stored payload, drops the rows
you just resolved, and re-renders all four outputs through `compare_configured.py`'s own
writers so the format stays identical. It also stamps a "Partial refresh" note into
`COMPARISON_REPORT.md` — leave that note in.

### Step 7 — Record the decision
Append an entry per task to `docs/reconciliation_resolutions.json`: winner, what was applied,
and **`openItems` for anything you could not resolve or had to infer**. This file is the reason
the next person does not re-litigate a row.

### Step 8 — Commit
Follow the commit format in CLAUDE.md. Stage the XML, `roadmap.json`, and the `docs/` artefacts
together — they are one logical change.

---

## 5. Known IDs to reuse

Task group IDs **must be identical** for every task in a group. Reuse these; never generate a
new one for an existing group name.

| Group | `taskGroupTemplateId` |
|---|---|
| Boarding | `e346c086-ced3-42e2-a8aa-a5ee54f62abe` |
| Closing | `66ac117e-fae9-44db-8ef8-eee7e2998286` |
| Disclosures | `e2d58efb-0551-4c93-a924-2e0d1f5ac97e` |
| Document Processing | `782a15d5-a92c-4bc6-9631-c099f47e6e60` |
| Funding | `8997b6dd-74af-420b-9c4f-fc232c95016f` |
| Funding QC | `2ed4e38e-6db0-4490-9de1-0c34c995969e` |
| Quality Assurance | `de9dfa21-754f-496a-9f67-e9f7812bdb95` |
| Service Orders | `2a7c3066-53c3-4740-8d64-1a1676fce1bc` |
| Underwriting | `90000990-4c59-4200-8594-1c10bb6f88f9` |

`Processing` currently has **five** different IDs across tasks — that is a pre-existing bug, not
a pattern to copy. Pick one before adding to that group.

Role `entityId`s are **system integers, not UUIDs**:

| Role | entityId |
|---|---|
| Loan Processor | `5` |
| Underwriter | `6` (one task uses `7`) |

Encompass roles with no known integer — `Funding Approval - Task`, `Closer`, `Disclosers - Task`,
`Pipeline Management - Task`, `Task - Appraisal Reviews`, `Closers -Task` — cannot be written
correctly without a live export. Write `entityId=""`, and record it as an open item. **Do not
invent a UUID**: it would import as a silently broken assignee, which is worse than an obviously
blank one.

---

## 6. Which files are generated

| File | Generated? | Edit by hand? |
|---|---|---|
| `tasks/**/*.xml` | No | Via the applier, not by hand |
| `roadmap.json` | No | Via script — see the formatting note in §7 |
| `docs/COMPARISON_REPORT.md` | **Yes** | Never |
| `docs/comparison_deltas.csv` | **Yes** | Never |
| `docs/reconciliation.html` | **Yes** | Never — edit `reconciliation_template.html` |
| `docs/comparison_summary.json` | **Yes** | Never |
| `docs/reconciliation_resolutions.json` | No | Yes, append per pass |
| `docs/reconciliation_template.html` | No | Yes, this is the page design |

---

## 7. Gotchas (read this part)

**XML serialisation.** `ElementTree` round-trips these files almost exactly, with two
differences you must undo after `tree.write()`:
1. it inserts a newline after the XML declaration — strip it;
2. it writes `" />"` for self-closing tags where the repo uses `"/>"` — `re.sub(r'"\s+/>', '"/>', s)`.

With those two fixes the diff is limited to what you actually changed. Attribute order is
preserved on Python 3.8+. Note `order_appraisal_v1.xml` has newlines between tags where every
other file is fully inline; ET preserves that, so leave it.

**Keep Encompass's subtask `type` keys verbatim**, even when they break repo conventions.
`type` is the import matching key. `Notice of Incomplete - Dates` uses a hyphen where
`docs/conventions.md` requires an en-dash — changing it would make the import create a
duplicate subtask instead of updating the existing one. Same reasoning applies to
`Order Appraisal – Obtain Quote` living under a task now named "Appraisal Invoice": it looks
like a namespacing violation, and it is, but it is Encompass's violation and the repo has to
mirror it. Expect `namespace_violations.repo` to *rise* after a pass like this. That is correct.

**Preserve Encompass description text exactly**, including its typos and whitespace —
`"Red Flag Form– Review..."` (missing space), `"Approve Funding –Task will..."`, trailing
spaces. The verifier compares against the recorded value, so "cleaning up" the text will fail
the check. Fix wording only if the user asks.

**Associations are deduplicated by `(relationship, entityUID)`** in the diff. If both sides
already bind `Credit Report`, you cannot tell from the CSV whether Encompass binds it on 7
subtasks or 8. Do not guess a count — record it as an open item.

**Task-level associations mirror the subtask ones.** In an Encompass-exported file the task's
`<associations>` list is the workspace plus one entry per subtask association, in subtask order,
sharing the same `entityId`. So a task-level document override appearing in the delta means some
subtask owns it. Map it to the owning subtask by name and attach it in both places — a task-level
override with no owning subtask does not match how these files are built.

**Encompass values can violate the documented conventions.** `Notice of Incomplete` has
`priority="6"`, outside the 1–5 XML scale in CLAUDE.md. Copy the live value and flag it; do not
clamp it.

**`roadmap.json` formatting** is exactly `json.dumps(d, indent=2, ensure_ascii=False)` with
**no trailing newline**. Write it that way or the whole file shows as changed.

**`roadmap.json` has pre-existing mojibake** — 91 U+FFFD characters where en-dashes were
mangled by an earlier tool. Repair them in the entries you rewrite; leave the rest alone unless
asked, so the diff stays readable.

**Task names in `roadmap.json` can drift from the XML.** `task_027` is "Approve Funding Figures"
while its template is "Approve Funding". Pre-existing; do not silently fix unrelated ones.

**Do not rename task files casually.** `tasks/2_processing/appraisal/order_appraisal_v1.xml`
holds a task now named "Appraisal Invoice", so it breaks the CLAUDE.md path convention — but
both CLAUDE.md and AGENT_INSTRUCTIONS.md cite that path as a reference example. Renaming is a
separate, user-approved change.

**Adopting Encompass can drop repo work that moved rather than disappeared.** The five ordering
subtasks removed from `Processing_Appraisal_Order` are not gone from production — Encompass keeps
them under `Processing_Appraisal_Ordering`, which is still untracked here. Before deleting
subtasks, check the Encompass-only list for a task that absorbed them, and say so in the commit.

---

## 8. Scripts

Two committed tools cover steps 2, 3 and 6. Both are read-only until you drop `--dry-run`.

### `reconcile_adopt.py` — apply and verify

```bash
# see what would change, write nothing
python reconcile_adopt.py --types Processing_FileSetup_PullDeed --dry-run

# apply, then self-verify against every recorded delta
python reconcile_adopt.py --types Processing_FileSetup_PullDeed

# check already-written files without applying
python reconcile_adopt.py --types Processing_FileSetup_PullDeed --verify

# several rows in one pass, plus a forced override -> subtask mapping
python reconcile_adopt.py \
  --types QualityAssurance_InitialDocReview Processing_FileSetup_ReviewCredit \
  --map "Consumer Handbook on Adjustable-Rate Mortgages=Initial Document Quality Assurance – CHARM Booklet"
```

It applies task attributes, subtask adds/removes/descriptions, Encompass rank order,
and associations — all from `comparison_deltas.csv` plus the payload's ordered subtask
list, so it cannot invent a value that was not recorded. It always re-verifies after
writing and **exits non-zero if any delta is left unresolved**, so a clean exit is your
step-3 check.

Two things it will tell you about rather than guess:

- **New subtasks.** `autoCreate` and `category` are not diffed, so it defaults to
  `autoCreate="true"` / `Regular` and warns. Check the sibling subtasks and fix if wrong.
- **Unmatched workspace overrides.** It matches a task-level override to its owning
  subtask by name overlap (≥ 0.6). Below that it leaves the override at task level and
  tells you to pass `--map`. Names like "Consumer Handbook on Adjustable-Rate Mortgages"
  → "CHARM Booklet" will never match automatically.

It refuses to run if a group name is missing from `GROUP_IDS` — add the id there rather
than letting a task get a fresh random group.

### `reconcile_refresh.py` — regenerate the artefacts

```bash
python reconcile_refresh.py --resolved Processing_FileSetup_PullDeed
```

Use only when `../import/Configured Task/` is absent. With `--resolved` omitted it is a
no-op refresh, which is a useful sanity check: it should leave `docs/` byte-identical.

**If you have the exports, run `python compare_configured.py` instead** — it supersedes
this completely and does not need the carried-forward snapshot.

---

## 9. Open items carried forward

Tracked in `docs/reconciliation_resolutions.json`; summarised here because they need a human.

- **`Funding Approval - Task` role ID.** `Approve Funding` has `entityId=""` on its assignee.
  Needs the integer from a live export before that task is imported.
- **`Processing_Appraisal_Ordering` is untracked.** Holds the appraisal ordering subtasks
  (Automated Order, Manual Order, Quote Assignment, Payment Recording, Order 1004/1025/1073).
  The Business Logic Notes in CLAUDE.md under "Appraisal Task (task_003)" now describe *that*
  task, not `Processing_Appraisal_Order`.
- **`Notice of Incomplete` is defined twice** — `Processing_Misc_NoticeOfIncomplete` (reconciled)
  and `Processing_Disclosures_NoticeOfIncomplete` (repo-only). Still a P0 duplicate.
- **Two rename pairs remain** under section 3 of the report; they would import as new tasks
  rather than updates.
