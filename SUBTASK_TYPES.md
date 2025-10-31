# Subtask Types Reference

This document explains the three types of subtasks and when they are used in the mortgage workflow system.

## Overview

Subtasks can have one of three types that determine when they are added to a task:

| Type | Badge Color | When Applied | Example |
|------|-------------|--------------|---------|
| `standard` | Green | Always included when parent task is created | "Create Invoice" in Order Appraisal |
| `conditional` | Yellow | Added only when specific conditions are met | "Order 1004" when property is single family |
| `later` | Blue | Added at a later time/stage in the workflow | "Re-verify Income" added during underwriting |

## Type: `standard`

**Definition**: Subtasks that are ALWAYS included when the parent task is created.

**Use Cases**:
- Core, required steps that every instance of the task needs
- Mandatory compliance items
- Standard documentation collection

**Examples**:
```json
{
  "name": "Create Invoice",
  "description": "Generate appraisal invoice for borrower",
  "type": "standard",
  "applicationLogic": "Always included when task is created"
}
```

```json
{
  "name": "Red Flags Review",
  "description": "Review refreshed credit report for red flags",
  "type": "standard",
  "applicationLogic": "Always included when credit refresh task is created"
}
```

## Type: `conditional`

**Definition**: Subtasks that are added ONLY when specific conditions are met during the workflow.

**Use Cases**:
- Property-type specific requirements (e.g., condo vs. single family)
- Loan-type specific steps (e.g., ARM vs. fixed)
- Income-type specific verifications (e.g., self-employed, social security)
- Conditional approvals requiring additional documentation

**Condition Examples**:
- Property type (single family, condo, multi-family)
- Loan type (conventional, FHA, VA, ARM)
- Income source (W-2, self-employed, social security, rental)
- Credit score thresholds
- Loan amount thresholds
- Occupancy type (primary, investment, second home)

**Examples**:
```json
{
  "name": "Send Invoice",
  "description": "Send appraisal invoice to borrower",
  "type": "conditional",
  "applicationLogic": "Added when intent to proceed is received"
}
```

```json
{
  "name": "Order 1004",
  "description": "Order 1004 appraisal form for single family property",
  "type": "conditional",
  "applicationLogic": "Added when payment is received AND property type is single family"
}
```

```json
{
  "name": "Analyze Self-Employment Income",
  "description": "Review tax returns and profit/loss statements for self-employed borrowers",
  "type": "conditional",
  "applicationLogic": "Added when borrower income type includes self-employment"
}
```

## Type: `later`

**Definition**: Subtasks that are added at a future time or different stage in the workflow, not immediately when the parent task is created.

**Use Cases**:
- Follow-up actions triggered by other events
- Re-verification steps
- Updates required by underwriting conditions
- Post-approval documentation
- Quality control checks that happen after initial task completion

**Timing Examples**:
- After underwriting review
- Before closing (but after initial processing)
- When loan is in clear to close status
- After appraisal is received
- When loan is purchased/sold

**Examples**:
```json
{
  "name": "Update Closing Disclosure",
  "description": "Update CD with final loan terms",
  "type": "later",
  "applicationLogic": "Added 3 business days before closing when final terms are confirmed"
}
```

```json
{
  "name": "Re-verify Employment",
  "description": "Re-verify borrower employment before closing",
  "type": "later",
  "applicationLogic": "Added within 10 days of closing date"
}
```

```json
{
  "name": "Clear Title Exceptions",
  "description": "Address any title exceptions found",
  "type": "later",
  "applicationLogic": "Added after preliminary title report is received if exceptions exist"
}
```

## Task Reopening

**Important**: When conditional or later subtasks are added to a task, the task can be **reopened** even if it was previously completed.

### Example Workflow

1. **Initial Creation**: "Order Appraisal" task created with 4 standard subtasks
   - Create Invoice
   - Payment Recording
   - 1004 Form
   - 1025 Form

2. **Task Completed**: All 4 subtasks done, task marked complete

3. **Condition Met**: Intent to proceed received

4. **Task Reopened**: New conditional subtask added
   - Send Invoice (conditional)

5. **Condition Met**: Payment received AND property is single family

6. **Task Reopened Again**: Another conditional subtask added
   - Order 1004 (conditional)

## Best Practices

### When Defining Tasks

1. **Start with standard subtasks**: Identify what ALWAYS happens
2. **Map conditional logic**: Document all possible conditions that trigger additional subtasks
3. **Plan for later additions**: Consider what might be needed in future stages
4. **Be specific with conditions**: Use AND/OR logic clearly in applicationLogic
5. **Document triggers**: Explain exactly what event/data triggers each subtask

### Application Logic Format

Write clear, specific conditions:

**Good**:
- "Added when payment is received AND property type is single family"
- "Added when borrower income includes Social Security benefits"
- "Added within 5 days before closing date"

**Avoid**:
- "Added later"
- "If needed"
- "Sometimes required"

### For AI Agents

When processing tasks:
1. Create XML for **standard** subtasks immediately
2. Document **conditional** subtasks in notes/comments
3. Document **later** subtasks with timeline expectations
4. Update roadmap with all subtasks (standard, conditional, later) so the full scope is visible

## Subtask Type Decision Tree

```
Is this subtask ALWAYS needed for this task?
├─ YES → type: "standard"
└─ NO
   ├─ Is it added based on loan/property/borrower conditions?
   │  └─ YES → type: "conditional"
   └─ Is it added at a future time/stage?
      └─ YES → type: "later"
```

## Visual Indicators in Roadmap

The roadmap dashboard shows subtasks with color-coded badges:

- **✓ Green**: Standard - always included
- **⚡ Yellow**: Conditional - added when conditions met
- **⏰ Blue**: Later - added at future time

Each subtask displays its application logic so you can understand exactly when it applies.
