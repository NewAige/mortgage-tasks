# Mortgage Tasks

This repository contains task templates for the mortgage process, organized by stage (Funding QC, Processing, Underwriting, Closing, etc.).

## Structure
- `docs/` – conventions and import guides
- `tasks/` – active XML task templates, organized by category
- `archive/` – retired/old versions
- `roadmap.json` – task planning and tracking data
- `roadmap.html` – visual dashboard for roadmap
- `AGENT_INSTRUCTIONS.md` – guide for AI agents to create tasks
- `SUBTASK_TYPES.md` – reference guide for standard/conditional/later subtasks

## Roadmap System

The roadmap system helps visualize and plan all mortgage workflow tasks:

### Viewing the Roadmap
1. Open `roadmap.html` in your browser
2. Filter tasks by stage, status, or priority
3. View task details, application logic, and subtasks
4. Track agent activity in the log

### Adding New Tasks
1. Edit `roadmap.json` to add a new task with `status: "planned"`
2. Include task name, priority (1-10), description, notes, and application logic
3. Assign an `order` number and `subcategory` (e.g., "file_setup", "service_orders")
4. Define subtasks with `order`, `type` (`standard`, `conditional`, or `later`), and `applicationLogic` - see `SUBTASK_TYPES.md`
5. Save and refresh `roadmap.html` to see the new task

### Task Organization
- **Ordering**: Tasks and subtasks have an `order` field (1, 2, 3...) to control their sequence
- **Subcategories**: Stages can have subcategories to group related tasks (e.g., Processing has File Setup, Service Orders, Pre-Underwriting, Post-Underwriting)
- The dashboard respects ordering and displays tasks grouped by subcategory

### Subtask Types
- **Standard**: Always included when task is created
- **Conditional**: Added only when specific conditions are met
- **Later**: Added at a future time/stage in the workflow

Tasks can be reopened when new conditional or later subtasks are assigned. See [SUBTASK_TYPES.md](SUBTASK_TYPES.md) for details.

### AI Agent Workflow
1. Agent reads `roadmap.json` for tasks with `status: "planned"`
2. Agent generates XML file following conventions in `docs/conventions.md`
3. Agent updates `roadmap.json` to mark task completed and log activity
4. See `AGENT_INSTRUCTIONS.md` for detailed agent workflow

## Quick Start
1. Copy an existing XML file from `tasks/` as a starting point.
2. Update the task name, type, UUIDs, and timestamps.
3. Namespace subtask `type` with the parent name to avoid cross-parent conflicts.
4. Keep formatting inline (no pretty-print).
