# Conventions for Task XML Files

1. Every `<taskTemplate>` and `<subTaskTemplate>` must have a unique UUID in `id`.
2. Namespace subtask `type` values with the parent task (e.g., `Credit Refresh – Red Flags`).
3. Do not include `taskTemplateId` inside subtasks.
4. Keep formatting inline (attributes on one line, self-closing tags).
5. Use ISO timestamps with Z suffix (e.g., `2025-09-09T21:10:00.000Z`).
6. **Task Groups** — `taskGroupTemplateId` and `taskGroupTemplateName` are sibling attributes on `<taskTemplate>`.
   - `taskGroupTemplateName` is the display label shown in Encompass (e.g. `"Service Orders"`, `"Processing"`).
   - `taskGroupTemplateId` is a **shared UUID** that must be **identical for every task belonging to the same group**. Encompass uses this to associate tasks into a group — if each task has a different UUID, they will not be grouped.
   - Always pass `--task-group-id` with the same UUID when generating multiple tasks for the same group. Generate it once (`python -c "import uuid; print(uuid.uuid4())"`) and reuse it across all calls for that group.
