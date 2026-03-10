# CLAUDE.md — Mortgage Task Agent Guide

This file is the primary reference for any AI agent working in this repository.
Read it fully before taking any action.

---

## What This Repo Is

A library of XML task templates for import into an Encompass LOS (Loan Origination System).
Each XML file defines one mortgage workflow task and its subtasks.
Tasks are tracked in `roadmap.json` and visualised in `roadmap.html`.

---

## Repo Layout

```
mortgage-tasks/
├── CLAUDE.md                  ← you are here
├── AGENT_INSTRUCTIONS.md      ← detailed step-by-step agent workflow
├── SUBTASK_TYPES.md           ← standard / conditional / later reference
├── docs/
│   └── conventions.md         ← XML formatting rules (always follow)
├── roadmap.json               ← source of truth for task status
├── roadmap.html               ← visual dashboard (browser only)
├── tasks/
│   ├── 1_origination/
│   ├── 2_processing/
│   ├── 3_underwriting/
│   ├── 4_closing/
│   ├── 5_funding/
│   ├── 6_pre-closing-qc/
│   └── 7_post-closing-qc/
├── Example files/
│   ├── Example_Everything.xml ← full-featured task example
│   ├── ExampleSimple.xml      ← minimal task example
│   └── ExampleJoined.xml      ← merged export example
├── create_task.py             ← script: create a single task XML
└── export_joined.py           ← script: merge XMLs into one joined file
```

---

## Core Agent Workflow

```
1. Read roadmap.json → find tasks where status == "planned"
2. Pick one task (highest priority first)
3. Generate XML via create_task.py  OR  write it directly
4. Write the file to the correct path (see Path Rules below)
5. Update roadmap.json (status, xmlFile, createdBy, createdAt, metadata, agentLog)
6. Commit with the standard message format
```

See `AGENT_INSTRUCTIONS.md` for the complete, step-by-step version.

---

## Python Scripts

### create_task.py — Generate a task XML

```bash
python create_task.py \
  --name        "Review Credit" \
  --type        "Processing_FileSetup_ReviewCredit" \
  --description "Review borrower credit report for accuracy and issues" \
  --roadmap-priority 9 \
  --rank        1 \
  --duration    5 \
  --duration-format Minute \
  --task-group-id   "2a7c3066-53c3-4740-8d64-1a1676fce1bc" \
  --task-group-name "Processing" \
  --workspace-uid   "Credit Review" \
  --associations '[
    {"entityId":"5","entityType":"urn:elli:encompass:role","entityUID":"Loan Processor","relationship":"Assignee"}
  ]' \
  --authorizations '[
    {"entityId":"24","entityType":"urn:elli:encompass:usergroup","entityUID":"TPO Admins","relationship":"CAN_CREATE"}
  ]' \
  --conditions '{
    "priorities":   [{"value":"1","script":"[4002]=\"TEST\""}],
    "assignees":    [{"script":"[4002]=\"TEST\"","entityId":"7","entityType":"urn:elli:encompass:role"}],
    "descriptions": [{"value":"Conditional description","script":"[4002]=\"TEST\""}],
    "dues":         [{"script":"[4002]=\"TEST\"","duration":"2","durationFormat":"Day"}]
  }' \
  --subtasks '[
    {"name":"Red Flags Review","description":"Review credit report for red flags","type":"standard"},
    {"name":"OFAC","description":"OFAC screening for all parties","type":"standard"},
    {"name":"Fraud Alerts","description":"Review and address fraud alerts","type":"standard"}
  ]' \
  --out tasks/2_processing/credit_review/review_credit_v1.xml \
  --json
```

Returns JSON: `{"ok": true, "file": "...", "task_id": "<uuid>"}`

**Key flags:**
| Flag | Notes |
|---|---|
| `--name` | Required. Task display name. |
| `--type` | Required. Type string — see Type Naming below. |
| `--roadmap-priority N` | 1-10 scale; auto-maps to XML 1-5. Use instead of `--priority`. |
| `--subtasks JSON` | JSON array of subtask objects (see Subtask Object Shape). |
| `--workspace-uid TEXT` | Convenience: adds a workspace association. Stacks with `--associations`. |
| `--associations JSON` | Task-level associations — any entityType/relationship (role Assignee, workspace, etc.). `entityId` is auto-generated if omitted. |
| `--authorizations JSON` | `CAN_CREATE` entries for roles or usergroups. |
| `--conditions JSON` | Conditional overrides: priorities, assignees, descriptions, dues. All sub-keys optional. |
| `--task-group-id UUID` | **Shared UUID for the task group.** Must be identical for every task in the same group. Generate once and reuse — do not omit when creating multiple tasks for the same group. |
| `--task-group-name TEXT` | Task group display label shown in Encompass (e.g. `"Service Orders"`, `"Processing"`). Always pair with `--task-group-id`. |
| `--out PATH` | Output file. Parent dirs are created automatically. |
| `--json` | Machine-readable output. Always use this in agent pipelines. |

**`--associations` object shape (task-level):**
```json
[
  {"entityId": "5",  "entityType": "urn:elli:encompass:role",      "entityUID": "Loan Processor", "relationship": "Assignee"},
  {"entityId": "<omit to auto-generate>", "entityType": "urn:elli:encompass:workspace", "entityUID": "Credit Review", "relationship": "workspace"}
]
```
`entityId` may be omitted — a fresh UUID is generated automatically. Use a fixed integer/UUID when Encompass requires a specific system ID (e.g. role IDs).

**`--authorizations` object shape:**
```json
[
  {"entityId": "24", "entityType": "urn:elli:encompass:usergroup", "entityUID": "TPO Admins",    "relationship": "CAN_CREATE"},
  {"entityId": "5",  "entityType": "urn:elli:encompass:role",      "entityUID": "Loan Processor","relationship": "CAN_CREATE"}
]
```

**`--conditions` object shape:**
```json
{
  "priorities":   [{"value": "1", "script": "[4002]=\"TEST\""}],
  "assignees":    [{"script": "[4002]=\"TEST\"", "entityId": "7", "entityType": "urn:elli:encompass:role"}],
  "descriptions": [{"value": "Conditional description text", "script": "[4002]=\"TEST\""}],
  "dues":         [{"script": "[4002]=\"TEST\"", "duration": "2", "durationFormat": "Day"}]
}
```
All four sub-keys are optional. Omit any you don't need.

**Subtask object shape:**
```json
{
  "name": "Red Flags Review",
  "description": "Review credit report for red flags, name/address/SSN discrepancies",
  "type": "standard",
  "category": "Regular",
  "associations": [
    {
      "entityId": "bb67dc76-ccf6-450e-aa18-cf3e829f0338",
      "entityType": "urn:elli:encompass:document-workspaceoverride-0",
      "entityUID": "Credit Report",
      "relationship": "document-workspaceoverride-0"
    }
  ]
}
```
`associations` and `category` are optional. `category` overrides the value derived from `type` (see Subtask Types below).

---

### export_joined.py — Merge XMLs into one file

```bash
# Merge specific files:
python export_joined.py \
  --files tasks/a.xml tasks/b.xml \
  --out export/joined.xml --json

# Merge an entire stage directory:
python export_joined.py \
  --dir tasks/6_pre-closing-qc \
  --out export/pre_closing_qc_all.xml --json

# Merge the entire tasks/ tree:
python export_joined.py \
  --dir tasks \
  --out export/all_tasks.xml --json
```

Returns JSON: `{"ok": true, "file": "...", "task_count": N}`

Output format matches `Example files/ExampleJoined.xml`:
single XML declaration → single `<taskTemplates>` root → all `<taskTemplate>` elements inline.

---

## UI Visibility Rules

- The subtask `description` is the **only field visible to end users** in the Encompass interface. The `name`, `type`, and other attributes are not displayed.
- Because `type` serves as an internal ID/title but is hidden from users, always prefix the subtask `description` with the subtask `name` (the portion after `Initial Document Quality Assurance – ` in the type), followed by ` – `, then the actual description text.
  - Example: `name="ARM Disclosure"` → `description="ARM Disclosure – ARM Disclosure sent same day as application; matches product and index as of day sent"`
- The task-level `description` follows normal conventions and does not require this prefix.

---

## XML Conventions (always follow — from docs/conventions.md)

1. **UUIDs** — every `id`, `taskGroupTemplateId`, and association `entityId` must be a unique UUID v4. Never reuse UUIDs across tasks.
2. **Timestamps** — ISO 8601 with Z suffix: `2025-09-09T21:10:00.000Z`
3. **Inline formatting** — no pretty-print, no line breaks between tags. All attributes on one tag, self-closing where there are no children.
4. **No `taskTemplateId` inside `<subTaskTemplate>`** — the example files include it but it is explicitly forbidden by conventions. Do not add it.
5. **Encoding** — `<?xml version='1.0' encoding='UTF-8'?>` header required on every standalone file.

---

## Type Naming Rules

### Task `type` attribute
```
{Stage}_{Subcategory}_{Action}
```
Examples:
- `Processing_FileSetup_ReviewCredit`
- `Processing_ServiceOrders_OrderAppraisal`
- `FundingQC_Credit_Refresh`
- `Underwriting_Submittal_Underwrite`
- `PostClosingQC_DocumentProcessing_RecordMortgage`

### Subtask `type` attribute
```
{Task Name} – {Subtask Name}
```
- Use an **en-dash** (–, U+2013), not a hyphen.
- The task name is the full display name (the `name` attribute of the parent `<taskTemplate>`).

Examples:
- `Review Credit – Red Flags Review`
- `Order Appraisal – Create Invoice`
- `Credit Refresh – Red Flags`

---

## Priority Mapping

| roadmap.json (1-10) | XML priority (1-5) |
|---|---|
| 9–10 | 5 |
| 7–8 | 4 |
| 5–6 | 3 |
| 3–4 | 2 |
| 1–2 | 1 |

Use `--roadmap-priority` with `create_task.py` and it maps automatically.

---

## Subtask Types

| Type | XML `required` | XML `autoCreate` | XML `category` | When to use |
|---|---|---|---|---|
| `standard` | `true` | `true` | `Regular` | Always needed; created with the task |
| `conditional` | `false` | `false` | `Regular` | Added only when specific loan/property/borrower conditions are met |
| `later` | `false` | `false` | `Regular` | Added at a future workflow stage |
| `informational` | `false` | `false` | `Informational` | Read-only reference subtask; not a work item |

For `conditional` and `later` subtasks: include them in the XML even though `autoCreate="false"`. This makes them available for the system to add when conditions are met.

Override `category` directly on any subtask object with `"category": "Informational"` (or any valid string) to bypass the type-derived default.

See `SUBTASK_TYPES.md` for full decision tree and examples.

---

## File Path Rules

```
tasks/{stage_id}/{task_folder}/{task_name_snake_case}_v1.xml
```

| Stage | stage_id |
|---|---|
| Origination | `1_origination` |
| Processing | `2_processing` |
| Underwriting | `3_underwriting` |
| Closing | `4_closing` |
| Funding | `5_funding` |
| Pre-Closing QC | `6_pre-closing-qc` |
| Post-Closing QC | `7_post-closing-qc` |

**Examples:**
- `tasks/2_processing/credit_review/review_credit_v1.xml`
- `tasks/2_processing/appraisal/order_appraisal_v1.xml`
- `tasks/6_pre-closing-qc/funding-qc/credit-refresh_v1.xml`
- `tasks/7_post-closing-qc/document_processing/record_mortgage_v1.xml`

Use `mkdir -p` (or let `create_task.py` handle it) before writing the file.

---

## roadmap.json Update Checklist

After creating an XML file, update `roadmap.json` with **all** of these:

```json
// On the task object:
"status":    "completed",
"xmlFile":   "tasks/2_processing/credit_review/review_credit_v1.xml",
"createdBy": "agent_claude",
"createdAt": "2025-10-30T12:00:00.000Z",
"subtasks":  [ /* full subtask array, including conditional/later */ ]

// On metadata:
"lastUpdated":    "2025-10-30T12:00:00.000Z",
"completedTasks": /* increment by 1 */

// Append to agentLog array:
{
  "timestamp": "2025-10-30T12:00:00.000Z",
  "agent":     "agent_claude",
  "action":    "created",
  "taskId":    "task_001",
  "taskName":  "Review Credit",
  "details":   "Created review_credit_v1.xml with 5 subtasks: Red Flags Review, OFAC, Fraud Alerts, Frozen Score, Review Liens",
  "xmlFile":   "tasks/2_processing/credit_review/review_credit_v1.xml"
}
```

---

## Git Commit Format

```
feat: Create {Task Name} task template

- Generated XML task template with {N} subtasks
- Updated roadmap status to completed
- Task ID: {task_id}

🤖 Generated by AI Agent
```

Stage the XML file and `roadmap.json` together. Do not stage unrelated files.

---

## Current Task Status (as of last roadmap sync)

39 of 44 tasks remain **planned**. 5 are completed:
- `task_001` Review Credit — `tasks/2_processing/credit_review/review_credit_v1.xml`
- `task_003` Order Appraisal — `tasks/2_processing/appraisal/order_appraisal_v1.xml`
- `task_006` ARM Disclosure — `tasks/2_processing/arm_disclosure/arm_disclosure_v1.xml`
- `task_009` Credit Refresh — `tasks/6_pre-closing-qc/funding-qc/credit-refresh_v1.xml`
- `task_010` Fraud X Report — `tasks/6_pre-closing-qc/funding-qc/fraudx_v1.xml`

Highest-priority planned tasks (work these first):
1. `task_002` Send Disclosures — priority 10, Processing / File Setup
2. `task_017` Underwrite — priority 10, Underwriting / Submittal
3. `task_027` Approve Funding Figures — priority 10, Funding
4. `task_028` Fund Loan — priority 10, Funding
5. `task_021` Clear to Close — priority 10, Underwriting / Resubmittal
6. `task_011` Run AUS — priority 9, Processing / File Setup
7. `task_014` Verify Income — priority 9, Processing / Pre-Underwriting
8. `task_023` Send Initial CD — priority 9, Closing
9. `task_024` Balance CD — priority 9, Closing
10. `task_039` Record Mortgage — priority 9, Post-Closing QC

---

## Validation Checklist (run before marking any task complete)

- [ ] XML file exists at the path stored in `xmlFile`
- [ ] All UUIDs are unique v4 strings — no duplicates within the file or across existing files
- [ ] Every `<subTaskTemplate>` type attribute uses en-dash (–), not hyphen (-)
- [ ] No `taskTemplateId` attribute inside any `<subTaskTemplate>`
- [ ] Timestamps are ISO 8601 with `.000Z` suffix
- [ ] Priority is 1-5 (XML scale), not the roadmap 1-10 scale
- [ ] `roadmap.json` updated: status, xmlFile, createdBy, createdAt, subtasks, metadata, agentLog
- [ ] `agentLog` entry is descriptive (lists subtask names in `details`)
- [ ] XML parses cleanly: `python -c "from xml.etree import ElementTree as ET; ET.parse('path/to/file.xml'); print('OK')"`

---

## Common Mistakes to Avoid

| Mistake | Correct approach |
|---|---|
| Reusing a UUID from an example file | Always generate a fresh UUID (`import uuid; str(uuid.uuid4())`) |
| Using a hyphen in subtask type: `Task - Sub` | Use en-dash: `Task – Sub` (U+2013) |
| Adding `taskTemplateId` to subtask elements | Do not include this attribute |
| Pretty-printing the XML | Keep everything inline — no newlines between tags |
| Using the roadmap 1-10 priority in XML | Map to 1-5 scale (see Priority Mapping table above) |
| Skipping `conditional`/`later` subtasks | Include them in XML with `autoCreate="false"` |
| Forgetting to update `metadata.completedTasks` | Always increment this counter |
| Committing without updating agentLog | Always append a log entry |
| Confusing `--workspace-uid` with `--associations` | `--workspace-uid` is a shorthand that appends one workspace entry; use `--associations` for role assignees or multiple association types |
| Hardcoding a UUID for a role entityId | Role IDs are system integers (e.g. `"5"` for Loan Processor); do not generate a UUID for these |
| Omitting `--task-group-id` when creating a group | Always generate one UUID and pass it to every `create_task.py` call in the same group — without it each task gets a random ID and Encompass will not group them |
| Using a different `--task-group-id` per task in the same group | The ID must be **identical** across all tasks in the group; generate it once before the loop |

---

## Reference Files

| File | Purpose |
|---|---|
| `Example files/Example_Everything.xml` | Full-featured task with conditions, associations, authorizations |
| `Example files/ExampleSimple.xml` | Minimal task with no subtasks |
| `Example files/ExampleJoined.xml` | Two tasks merged into one file |
| `tasks/2_processing/credit_review/review_credit_v1.xml` | Real task with role Assignee + workspace associations |
| `tasks/6_pre-closing-qc/funding-qc/credit-refresh_v1.xml` | Real task with subtask associations |
| `tasks/6_pre-closing-qc/funding-qc/fraudx_v1.xml` | Real task with multiple subtask associations |
| `docs/conventions.md` | Authoritative XML rules |
| `AGENT_INSTRUCTIONS.md` | Full agent workflow with examples |
| `SUBTASK_TYPES.md` | Subtask type decision tree |
