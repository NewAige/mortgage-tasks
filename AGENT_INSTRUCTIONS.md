# AI Agent Instructions for Roadmap Task Creation

This document provides instructions for AI agents to read tasks from the roadmap, create XML task templates, and update the roadmap accordingly.

## Overview

The workflow is:
1. **Read** `roadmap.json` to find tasks with `status: "planned"`
2. **Generate** XML task template following conventions in `docs/conventions.md`
3. **Update** `roadmap.json` to mark task as completed and log the action
4. **Commit** changes to git

## Step 1: Reading the Roadmap

Load `roadmap.json` and search for tasks where `status === "planned"`.

### Task Data Structure

Each task contains:
- `id`: Unique task identifier (e.g., "task_001")
- `name`: Task name (use this for XML `name` attribute)
- `order`: Numeric order for sequencing tasks within a stage/subcategory (1, 2, 3, etc.)
- `subcategory`: Subcategory ID this task belongs to (e.g., "file_setup", "service_orders")
- `status`: Current status ("planned", "in-progress", "completed")
- `priority`: Priority 1-10 (map to XML priority)
- `description`: Task description (use for documentation)
- `notes`: Free-form guidance for the agent on what to include
- `applicationLogic`: When this task should be applied in the workflow
- `subtasks`: Array of subtask objects (see Subtask Structure below)
- `xmlFile`: Path where XML should be created (null for planned tasks)

### Subtask Structure

Each subtask is an object with:
- `name`: Subtask name (used in XML subtask name)
- `order`: Numeric order for sequencing subtasks (1, 2, 3, etc.)
- `description`: Detailed description of what the subtask does
- `type`: One of:
  - `"standard"` - Always included when the task is created
  - `"conditional"` - Added only when specific conditions are met
  - `"later"` - Added at a later time/stage in the workflow
- `applicationLogic`: When this subtask is added to the task

### Stage Subcategories

Stages may contain subcategories to group related tasks. For example, the Processing stage has:
- **File Setup** (order: 1) - Initial loan setup and disclosure tasks
- **Service Orders** (order: 2) - Third-party service orders and verifications
- **Pre-Underwriting** (order: 3) - Documentation verification before underwriting
- **Post-Underwriting** (order: 4) - Tasks after underwriting approval

Each subcategory has:
- `id`: Unique identifier (e.g., "file_setup")
- `name`: Display name (e.g., "File Setup")
- `order`: Numeric order for sequencing subcategories
- `description`: What this subcategory represents

**Important**: Tasks can be **reopened** when new subtasks are assigned based on conditions. For example, "Order Appraisal" may initially have 4 subtasks, but later a conditional subtask "Order 1004" might be added when payment is received AND property is single family.

### Example Task to Process

```json
{
  "id": "task_003",
  "name": "Order Appraisal",
  "order": 1,
  "subcategory": "service_orders",
  "status": "planned",
  "priority": 8,
  "description": "Order property appraisal and collect required forms",
  "notes": "Task can be reopened when new subtasks are assigned based on conditions",
  "applicationLogic": "Applied after disclosures sent and appraisal fee collected.",
  "subtasks": [
    {
      "name": "Create Invoice",
      "order": 1,
      "description": "Generate appraisal invoice for borrower",
      "type": "standard",
      "applicationLogic": "Always included when task is created"
    },
    {
      "name": "Send Invoice",
      "order": 2,
      "description": "Send appraisal invoice to borrower",
      "type": "conditional",
      "applicationLogic": "Added when intent to proceed is received"
    },
    {
      "name": "Payment Recording",
      "order": 3,
      "description": "Record appraisal payment received",
      "type": "standard",
      "applicationLogic": "Always included when task is created"
    },
    {
      "name": "Order 1004",
      "order": 4,
      "description": "Order 1004 appraisal form for single family property",
      "type": "conditional",
      "applicationLogic": "Added when payment is received AND property type is single family"
    }
  ],
  "xmlFile": null,
  "createdBy": null,
  "createdAt": null
}
```

## Step 2: Generating XML Task Template

### XML File Location

Determine the file path based on the task's stage:
- Stage ID is the parent object in `roadmap.json`
- Create file: `tasks/{stage_id}/{task_folder}/{task_name_lowercase}_v1.xml`
- Example: `tasks/2_processing/credit_review/review_credit_v1.xml`

### XML Template Structure

Follow the conventions in `docs/conventions.md`. Here's the structure:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<taskTemplates>
  <taskTemplate
    id="[GENERATE_NEW_UUID]"
    name="[TASK_NAME]"
    type="[STAGE]_[TASK_TYPE]"
    required="true"
    priority="[PRIORITY_1_TO_5]"
    rank="1"
    created="[ISO_8601_TIMESTAMP_Z]"
    lastModified="[ISO_8601_TIMESTAMP_Z]"
    duration="5"
    durationFormat="Minutes"
    taskGroupTemplateId="[GENERATE_NEW_UUID]"
    taskGroupTemplateName="[TASK_GROUP_NAME]"
    autocomplete="false"
    autoCreate="false">

    <associations>
      <association
        entityId="[GENERATE_NEW_UUID]"
        entityType="urn:elli:encompass:workspace" />
    </associations>

    <subTaskTemplates>
      <subTaskTemplate
        id="[GENERATE_NEW_UUID]"
        name="[SUBTASK_NAME]"
        description="[SUBTASK_DESCRIPTION]"
        type="[TASK_NAME] – [SUBTASK_NAME]"
        category="Regular"
        required="true"
        priority="[PRIORITY_1_TO_5]"
        rank="1"
        created="[ISO_8601_TIMESTAMP_Z]"
        lastModified="[ISO_8601_TIMESTAMP_Z]"
        duration="5"
        durationFormat="Minutes"
        autocomplete="false"
        autoCreate="false" />

      <!-- Repeat for each subtask -->
    </subTaskTemplates>
  </taskTemplate>
</taskTemplates>
```

### Important XML Conventions

1. **UUIDs**: Generate new UUIDs for every `id`, `taskGroupTemplateId`, and association `entityId`
2. **Timestamps**: Use ISO 8601 format with Z suffix (e.g., `2025-10-30T12:00:00Z`)
3. **Type Naming**:
   - Main task: `{Stage}_{TaskCategory}_{Action}` (e.g., `Processing_Credit_Review`)
   - Subtask: `{TaskName} – {SubtaskName}` (e.g., `Review Credit – Pull Report`)
   - Note: Use en-dash (–) not hyphen (-) between task and subtask names
4. **Priority Mapping**: Roadmap uses 1-10, XML uses 1-5
   - Roadmap 9-10 → XML 5
   - Roadmap 7-8 → XML 4
   - Roadmap 5-6 → XML 3
   - Roadmap 3-4 → XML 2
   - Roadmap 1-2 → XML 1
5. **Subtask Descriptions**: Use the `notes` field and `applicationLogic` to create meaningful descriptions
6. **No taskTemplateId**: Do NOT include `taskTemplateId` inside `<subTaskTemplate>` elements

### Creating Subtasks

The `subtasks` array contains objects with detailed information:

```json
{
  "name": "Create Invoice",
  "description": "Generate appraisal invoice for borrower",
  "type": "standard",
  "applicationLogic": "Always included when task is created"
}
```

**Important Notes:**
1. **Standard subtasks** (`type: "standard"`) should be included in the initial XML when creating the task
2. **Conditional subtasks** (`type: "conditional"`) should be documented but may be added later when conditions are met
3. **Later subtasks** (`type: "later"`) are added at a future time in the workflow
4. Use the `description` field for the XML subtask `description` attribute
5. Use the `applicationLogic` to understand when each subtask applies

**For planned tasks with empty subtasks array:**
If `subtasks` array is empty but `notes` field provides guidance:
- Parse the notes field
- Extract suggested subtask names
- Create appropriate subtask descriptions based on task context
- Determine if each is "standard", "conditional", or "later"
- Generate subtask objects and update roadmap accordingly

## Step 3: Updating roadmap.json

After creating the XML file, update `roadmap.json`:

### 3.1 Update Task Object

Find the task by `id` and update these fields:

```json
{
  "status": "completed",
  "subtasks": [
    {
      "name": "Subtask 1",
      "order": 1,
      "description": "What this subtask does",
      "type": "standard",
      "applicationLogic": "Always included when task is created"
    },
    {
      "name": "Subtask 2",
      "order": 2,
      "description": "What this subtask does",
      "type": "conditional",
      "applicationLogic": "Added when X condition is met"
    }
  ],
  "xmlFile": "tasks/2_processing/credit_review/review_credit_v1.xml",
  "createdBy": "agent_[YOUR_AGENT_ID]",
  "createdAt": "[ISO_8601_TIMESTAMP_Z]"
}
```

**Note**: When creating a new task, you must also assign it an appropriate `order` number and `subcategory` based on where it logically fits in the workflow. Review existing tasks in the same stage to determine the next available order number.

### 3.2 Update Metadata

Update the metadata object:

```json
{
  "lastUpdated": "[ISO_8601_TIMESTAMP_Z]",
  "completedTasks": [INCREMENT_BY_1]
}
```

### 3.3 Append to Agent Log

Add a new entry to the `agentLog` array:

```json
{
  "timestamp": "[ISO_8601_TIMESTAMP_Z]",
  "agent": "agent_[YOUR_AGENT_ID]",
  "action": "created",
  "taskId": "task_001",
  "taskName": "Review Credit",
  "details": "Created review_credit_v1.xml with 4 subtasks: Pull Credit Report, Review Red Flags, Verify Inquiries, Check Credit Scores",
  "xmlFile": "tasks/2_processing/credit_review/review_credit_v1.xml"
}
```

## Step 4: File System Operations

### 4.1 Create Directory Structure

Before writing XML file, ensure directory exists:

```bash
mkdir -p tasks/{stage_id}/{task_folder}
```

### 4.2 Write XML File

Write the generated XML to the determined path.

### 4.3 Update roadmap.json

Read, modify, and write back `roadmap.json` with updated data.

## Step 5: Git Commit (Optional)

If configured to commit changes:

```bash
git add tasks/{stage_id}/{task_folder}/{task_name}_v1.xml
git add roadmap.json
git commit -m "feat: Create {Task Name} task template

- Generated XML task template with {N} subtasks
- Updated roadmap status to completed
- Task ID: {task_id}

🤖 Generated by AI Agent"
```

## Example Agent Workflow

### Input: Task from Roadmap

```json
{
  "id": "task_008",
  "name": "Order Tax Transcripts",
  "status": "planned",
  "priority": 7,
  "description": "Request IRS tax transcripts for income verification",
  "notes": "Agent should create subtasks for: 4506-C form completion, IRS transcript request (1040, W-2, 1099), transcript review, income verification against application, self-employed income analysis (if applicable)",
  "applicationLogic": "Applied for most loan types requiring income verification. Triggers after initial disclosures sent or when income documentation is needed.",
  "subtasks": [],
  "xmlFile": null
}
```

### Agent Actions

1. **Parse task data** - Extract name, priority, notes, etc.
2. **Determine file path** - `tasks/2_processing/tax_transcripts/order_tax_transcripts_v1.xml`
3. **Create directory** - `mkdir -p tasks/2_processing/tax_transcripts`
4. **Generate subtasks from notes**:
   - "Complete 4506-C Form"
   - "Request IRS Transcripts"
   - "Review Transcripts"
   - "Verify Income"
   - "Analyze Self-Employment Income"
5. **Generate XML** with proper UUIDs, timestamps, and structure
6. **Write XML file**
7. **Update roadmap.json**:
   - Set status to "completed"
   - Add subtasks array
   - Set xmlFile path
   - Set createdBy and createdAt
   - Increment metadata.completedTasks
   - Update metadata.lastUpdated
   - Append to agentLog
8. **Save roadmap.json**
9. **(Optional)** Commit to git

### Output: Updated Roadmap

```json
{
  "id": "task_008",
  "name": "Order Tax Transcripts",
  "status": "completed",
  "priority": 7,
  "description": "Request IRS tax transcripts for income verification",
  "notes": "Agent should create subtasks for: 4506-C form completion, IRS transcript request (1040, W-2, 1099), transcript review, income verification against application, self-employed income analysis (if applicable)",
  "applicationLogic": "Applied for most loan types requiring income verification. Triggers after initial disclosures sent or when income documentation is needed.",
  "subtasks": [
    "Complete 4506-C Form",
    "Request IRS Transcripts",
    "Review Transcripts",
    "Verify Income",
    "Analyze Self-Employment Income"
  ],
  "xmlFile": "tasks/2_processing/tax_transcripts/order_tax_transcripts_v1.xml",
  "createdBy": "agent_claude_v1",
  "createdAt": "2025-10-30T14:30:00Z"
}
```

## Error Handling

If errors occur:

1. **Task not found**: Log error and exit
2. **Task already completed**: Skip and log warning
3. **Invalid task data**: Request human review
4. **XML generation fails**: Log error details and exit
5. **File write fails**: Log error and attempt retry
6. **JSON update fails**: Restore backup and log error

## Validation Checklist

Before marking complete, verify:

- [ ] XML file created in correct location
- [ ] XML follows all conventions from `docs/conventions.md`
- [ ] All UUIDs are unique and properly formatted
- [ ] Subtasks are properly namespaced with parent task name
- [ ] Timestamps are ISO 8601 with Z suffix
- [ ] Priority correctly mapped from 1-10 to 1-5 scale
- [ ] roadmap.json updated with all required fields
- [ ] Metadata counts are accurate
- [ ] Agent log entry is complete and descriptive
- [ ] No `taskTemplateId` inside subtask elements

## Reference Files

- Task XML examples: `tasks/2_processing/appraisal/order_appraisal_v1.xml`
- XML conventions: `docs/conventions.md`
- Current roadmap: `roadmap.json`
- Visualization: `roadmap.html` (open in browser)

## Questions or Issues?

If you encounter ambiguous task definitions or need clarification:
1. Check similar completed tasks for patterns
2. Review `docs/conventions.md` for XML rules
3. Request human input if critical decisions are needed
4. Log all assumptions made in the agent log `details` field
