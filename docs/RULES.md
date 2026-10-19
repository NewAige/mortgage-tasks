# Workflow Automation Rules

Rules (Encompass "event triggers") are what make the task templates in `tasks/` run on their own:
they create tasks and subtasks, complete them, start timers, update loan fields, send
documents and so on. They reference tasks and subtasks by **`type`** - the same import key used
in the task XMLs - so a type rename silently breaks every rule that points at it.

## Files

| Path | What it is |
|---|---|
| `rules/exports/Rules_{n}_19.xml` | Raw Encompass exports, as received. Never hand-edit. |
| `rules/by_event/{event}/{rule_name}.xml` | One importable file per rule, grouped by trigger event. Generated. |
| `rules/rules.json` | Parsed rules (filters, conditions, `match`, processes/steps, `effects`) plus a `timers` index. Generated. |
| `docs/RULES_CATALOG.md` | Human-readable catalogue: task-type index, timer chains, per-event list. Generated. |
| `docs/RULES_CROSSREF.md`, `docs/rules_crossref.json` | Validation of rule references against `tasks/`. Generated. |
| `parse_rules.py` | Regenerates `by_event/`, `rules.json`, `RULES_CATALOG.md` from `rules/exports/`. |
| `rules_crossref.py` | Regenerates the crossref outputs. |

Never edit generated files; re-run the scripts.

## Model

```
event  ->  eventFilters  ->  workflowProcess[ conditions -> steps ]
```

1. **Event** (`triggerEvent`) - what happened.
2. **Event filters** (`eventFilters/eventFilter/terms/term`) - narrow which occurrences count
   (task type, subtask type, resolution, field id, document title, milestone, timer id).
   Operators seen: `EQUAL_TO`, `NOT_EQUAL_TO`, `IN`, `ANY_CHANGE`, `ENDS_WITH`.
3. **Workflow processes** (`workflowProcesses/workflowProcess`) - a rule holds one or more; each
   process is independent. `execution` is `ALL` (every process whose conditions pass runs).
4. **Conditions** (per process) - an Encompass field-script expression, e.g.
   `[4458]="Declined"` or `Not IsEmpty([Document.DateOrdered.Flood Certificate])`. If it is false
   the process is skipped. No condition means always run.
5. **Steps** - the actions, keyed `taskCreate1`, `subtaskComplete2`, ...; `initialSteps` names the
   first. All steps are `stepType` `action`. Some steps have `onSuccess` / `onFailure` branches.

A rule has `status` (`ACTIVE` / other) and `isInvalid`; check both when auditing.

## Trigger events

| URN | Fires when | Typical filter |
|---|---|---|
| `urn:elli:task:event:task:created` | A task is created | `payload.type` = task type |
| `urn:elli:task:event:task:completed` | A task is completed | `payload.type`, `payload.resolution` IN (`Complete`) |
| `urn:elli:task:event:subtask:completed` | A subtask is resolved | `payload.taskTemplateType` = task type, `payload.type` = subtask type, `payload.resolution` IN (`Done`, `Issue`) |
| `urn:elli:encompass:event:loan:field:modified` | A loan field changes | `fieldChangeEvents.modifiedField` (`/fields/4458`) with `ANY_CHANGE`, or `newValue` `EQUAL_TO` / `NOT_EQUAL_TO` |
| `urn:elli:encompass:event:loan:file:attached` | File attached to an eFolder document | `assignAttachmentsToDocument.title` = document title |
| `urn:elli:encompass:event:loan:milestone:completed` | Milestone finished | `finishMilestones.title` = milestone name |
| `urn:elli:encompass:event:loan:created` | Loan created | origination channel / none |
| `urn:elli:timer:event:timer:completed` | A scheduler (timer) runs out | `payload.resource.id` `ENDS_WITH` timer configuration id |

## Step actions

| URN | Meaning | Key params |
|---|---|---|
| `urn:elli:task:action:task:create` | Create a task | `type` (task type), `noDuplicate` |
| `urn:elli:task:action:task:complete` | Complete a task | `type`, `resolution`, `includeSubtask`, `subtaskResolution` |
| `urn:elli:task:action:subtask:create` | Add a subtask to a task | `taskTemplateType`, `type` (subtask type), `taskTemplateId`, `reopenParentTask` |
| `urn:elli:task:action:subtask:complete` | Resolve a subtask | `taskTemplateType`, `type`, `category`, `resolution` (`Done` / `NA`), `taskTemplateId` |
| `urn:elli:timer:action:timer:start` | Start a scheduler | `timerConfigurationId`, `name` |
| `urn:elli:timer:action:timer:cancel` | Cancel a scheduler | `timerConfigurationId`, `name` |
| `urn:elli:encompass:loan:action:field:update` | Set a loan field | `id` (field id), `value` |
| `urn:elli:encompass:loan:action:role:assign` | Assign a loan team role | `roleId`, `roleName`, `loanAssociateType` |
| `urn:elli:encompass:loan:action:folder:move` | Move loan to a pipeline folder | `folderName` |
| `urn:elli:encompass:loan:action:enhancedcondition:create` | Create an enhanced condition | `conditionType`, `title` |
| `urn:elli:encompass:loan:action:enhancedcondition:updatetracking` | Update a condition's tracking status | `conditionType`, `title`, `status` |
| `urn:elli:communication:action:notification:send` | Send a notification | `templateId` |
| `urn:elli:eds:action:document:sendrequest` | Send documents to borrower(s) | `documents`, `borrowerPair`; `onSuccess` / `onFailure` |
| `urn:elli:eds:action:disclosure:send` | Send a disclosure package | `onSuccess` / `onFailure` |
| `urn:elli:soo:action:order:create` | Order a service | `type`, `serviceRuleIds`; `onSuccess` |

## Resolutions and branching

Resolution drives which rule fires. A subtask carries one resolution when completed:

- **Subtask completed** rules filter `payload.resolution IN (...)`: `Done` (work finished) or
  `Issue` (problem raised). Two rules on the same subtask type with different resolutions are the
  normal way to branch, e.g. `Done` -> continue, `Issue` -> create a remediation task.
- **Task completed** rules filter on `Complete`.
- `subtask:complete` steps record `Done` or `NA` (not applicable) on a subtask; `task:complete`
  steps take a task `resolution` (`Complete`, `NA`, `Issue`) and `subtaskResolution` applied to
  any open subtasks when `includeSubtask` is true.
- A rule with no resolution filter fires on any resolution.

Further branching comes from process `conditions` (loan-field scripts), not from the event.

## Timers (schedulers)

Timers chain rules over time:

```
rule A: timer:start (timerConfigurationId X)
        ... time passes ...
event  timer:completed (resource.id ends with X)  ->  rule B fires
rule C: timer:cancel (X)   (e.g. loan Accepted/Declined stops the warning timer)
```

`rules/rules.json` -> `timers` indexes each timer id with the rules that start it, cancel it, and
fire on its completion; `docs/RULES_CATALOG.md` renders these chains. A timer that is started but
never has a completion rule (or vice versa) is usually a gap.

## Encoding gotcha

Some exports are declared `UTF-8` but arrive Windows-1252-encoded, where the en-dash in subtask
types (`Send Denial – MA Review Board Form`) is the single byte `0x96`. Parsers choke or yield
a replacement character, and the type then fails to match the task XMLs. Files in
`rules/exports/` have been normalized to real UTF-8 (U+2013). When adding a new export, check
for non-UTF-8 bytes (`python3 -c "open(p,'rb').read().decode('utf-8')"`) and re-encode from
cp1252 if needed before parsing. Subtask types must use the en-dash, never a hyphen; the crossref
flags hyphen/en-dash mismatches.

## Ingesting a fresh export

1. Drop the file(s) into `rules/exports/` (keep Encompass's names; confirm UTF-8).
2. `python parse_rules.py` (add `--json` for a machine-readable summary).
3. `python rules_crossref.py`.
4. Review `docs/RULES_CROSSREF.md`: unknown task/subtask types, hyphen/en-dash mismatches,
   tasks with no rule. Also check duplicates across exports (e.g. `Subtask_AppraisalCancel`
   appears twice; identical ids collapse to one rule).
5. Rebuild the map: `python rules_graph.py && python rules_cascades.py && python rules_map.py && python rules_map_docs.py`.
   New fields appear in the map with raw ids; add them to `rules/field_labels.csv` (keep existing labels).
6. Commit exports, `rules/by_event/`, `rules/rules.json`, and the generated docs together.

## Rules map

`docs/rules_map.html` (linked from `roadmap.html`) explains the rules to operations staff:
walkthroughs of named scenarios, a step-by-step trace (pick a loan event, e.g. a field change, then
the field, and click through what each rule does and what that sets off next; the full stage map
sits behind a toggle on the same tab), a "what happens when…" search, and timers.
`docs/RULES_MAP.md` is the GitHub-rendered equivalent. Both are generated from `rules/graph.json`
and `rules/cascades.json`; plain-English labels come from `rules/field_labels.csv` and
`rules/annotations.json`. Plan and design notes: `docs/RULES_MAP_PLAN.md`.

## Renaming types - the rule

**When renaming a task or subtask `type`, first check `rules/rules.json` and
`docs/RULES_CROSSREF.md` for rules that reference it.** Rules match on the exact string, so a
renamed type means the rule never fires (or its create/complete step fails) with no error. Either
keep the type, or update the rule in Encompass, re-export, and re-run the ingest workflow above.
Quick check:

```bash
grep -n "Processing_Misc_SendDenial" docs/RULES_CROSSREF.md
grep -c "OLD_TYPE" rules/rules.json
```
