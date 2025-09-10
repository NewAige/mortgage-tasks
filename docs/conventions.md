# Conventions for Task XML Files

1. Every `<taskTemplate>` and `<subTaskTemplate>` must have a unique UUID in `id`.
2. Namespace subtask `type` values with the parent task (e.g., `Credit Refresh – Red Flags`).
3. Do not include `taskTemplateId` inside subtasks.
4. Keep formatting inline (attributes on one line, self-closing tags).
5. Use ISO timestamps with Z suffix (e.g., `2025-09-09T21:10:00.000Z`).
