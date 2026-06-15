#!/usr/bin/env python3
"""
create_task.py — Generate a task XML file for the mortgage workflow system.

Usage (AI agent or CLI):
    python create_task.py --help
    python create_task.py \
        --name "Order Appraisal" \
        --type "Processing_ServiceOrders_OrderAppraisal" \
        --description "Order property appraisal and collect required forms" \
        --out "tasks/2_processing/appraisal/order_appraisal_v2.xml"

All flags except --name and --type are optional; sensible defaults are used.

Return value (stdout, JSON):
    {"ok": true, "file": "<path>", "task_id": "<uuid>"}
    {"ok": false, "error": "<message>"}

Exit codes: 0 = success, 1 = error.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_uuid() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def map_priority(p: int) -> int:
    """Map roadmap 1-10 priority to XML 1-5 priority."""
    if p >= 9:
        return 5
    if p >= 7:
        return 4
    if p >= 5:
        return 3
    if p >= 3:
        return 2
    return 1


def _esc(value: str) -> str:
    """XML-escape a string for use inside attribute values."""
    return (
        value
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ---------------------------------------------------------------------------
# Conditions builder
# ---------------------------------------------------------------------------

def _build_conditions(cond: dict) -> str:
    """
    Build the inline <conditions> block from a dict with optional keys:
      priorities  – list of {value, script}
      assignees   – list of {script, entityId, entityType}
      descriptions– list of {value, script}
      dues        – list of {script, duration, durationFormat}

    Returns an empty string if cond is empty / None.
    Any sub-key that is absent or an empty list is omitted entirely.
    """
    if not cond:
        return ""

    parts: list[str] = ["<conditions>"]

    priorities = cond.get("priorities") or []
    if priorities:
        parts.append("<priorities>")
        for p in priorities:
            parts.append(
                f'<priority value="{_esc(str(p["value"]))}"'
                f' script="{_esc(p["script"])}"/>'
            )
        parts.append("</priorities>")

    assignees = cond.get("assignees") or []
    if assignees:
        parts.append("<assignees>")
        for a in assignees:
            parts.append(f'<assignee script="{_esc(a["script"])}">')
            parts.append("<value>")
            parts.append(f'<entityId>{_esc(str(a["entityId"]))}</entityId>')
            parts.append(f'<entityType>{_esc(a["entityType"])}</entityType>')
            parts.append("</value>")
            parts.append("</assignee>")
        parts.append("</assignees>")

    descriptions = cond.get("descriptions") or []
    if descriptions:
        parts.append("<descriptions>")
        for d in descriptions:
            parts.append(
                f'<description value="{_esc(d["value"])}"'
                f' script="{_esc(d["script"])}"/>'
            )
        parts.append("</descriptions>")

    dues = cond.get("dues") or []
    if dues:
        parts.append("<dues>")
        for due in dues:
            parts.append(f'<due script="{_esc(due["script"])}">')
            parts.append("<value>")
            parts.append(f'<duration>{_esc(str(due["duration"]))}</duration>')
            parts.append(f'<durationFormat>{_esc(due["durationFormat"])}</durationFormat>')
            parts.append("</value>")
            parts.append("</due>")
        parts.append("</dues>")

    parts.append("</conditions>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_task_xml(
    *,
    name: str,
    task_type: str,
    description: str = "",
    comments: str = "",
    required: bool = True,
    priority: int = 3,           # XML 1-5 scale
    rank: int = 1,
    created_by: str = "agent",
    autocomplete: bool = False,
    auto_create: bool = False,
    duration: int = 5,
    duration_format: str = "Minute",
    calendar: str = "",
    task_group_template_id: str | None = None,   # pass a shared UUID to group tasks together
    task_group_template_name: str = "",           # display name shown in Encompass
    # Convenience shorthand: adds a workspace association automatically.
    # If you also pass `associations`, the workspace entry is appended to it.
    workspace_uid: str = "",
    # Task-level associations — any entityType/relationship combination.
    # e.g. role Assignee, workspace, etc.
    # Shape: [{entityId, entityType, entityUID, relationship}, ...]
    # entityId is auto-generated (new UUID) if omitted or empty.
    associations: list[dict] | None = None,
    # CAN_CREATE authorizations for roles / usergroups.
    # Shape: [{entityId, entityType, entityUID, relationship}, ...]
    authorizations: list[dict] | None = None,
    # Conditional overrides. Dict with optional keys:
    #   priorities   – [{value, script}, ...]
    #   assignees    – [{script, entityId, entityType}, ...]
    #   descriptions – [{value, script}, ...]
    #   dues         – [{script, duration, durationFormat}, ...]
    conditions: dict | None = None,
    subtasks: list[dict] | None = None,
    created_at: str | None = None,
) -> tuple[str, str]:
    """
    Build a task XML string.

    Returns (xml_string, task_uuid).

    subtasks is a list of dicts with keys:
        name        – subtask display name
        description – subtask description
        type        – "standard" | "conditional" | "later" | "informational"
        category    – override category string (default derived from type)
        required    – bool (default True for standard, False otherwise)
        auto_create – bool
        rank        – int (auto-assigned if omitted)
        associations – list of dicts [{entityId, entityType, entityUID, relationship}]
    """
    subtasks = subtasks or []
    ts = created_at or now_iso()
    task_id = new_uuid()
    tgt_id = task_group_template_id or new_uuid()

    # Category mapping for subtask types
    _category = {
        "standard":      "Regular",
        "conditional":   "Regular",
        "later":         "Regular",
        "informational": "Informational",
    }

    # Build XML via string (keeps output inline / no pretty-print per conventions)
    parts: list[str] = []
    parts.append("<?xml version='1.0' encoding='UTF-8'?>")
    parts.append("<taskTemplates>")

    # --- taskTemplate open tag ---
    attrs = {
        "id": task_id,
        "name": name,
        "description": description,
        "comments": comments,
        "type": task_type,
        "required": str(required).lower(),
        "priority": str(priority),
        "rank": str(rank),
        "created": ts,
        "createdBy": created_by,
        "lastModified": ts,
        "lastModifiedBy": created_by,
        "createdVia": "IMPORT",
        "taskGroupTemplateId": tgt_id,
        "taskGroupTemplateName": task_group_template_name,
        "autocomplete": str(autocomplete).lower(),
        "calendar": calendar,
        "autoCreate": str(auto_create).lower(),
        "duration": str(duration),
        "durationFormat": duration_format,
    }
    attr_str = " ".join(f'{k}="{_esc(str(v))}"' for k, v in attrs.items())
    parts.append(f"<taskTemplate {attr_str}>")

    # --- conditions (before associations, matching Example_Everything order) ---
    if conditions:
        parts.append(_build_conditions(conditions))

    # --- associations (workspace shorthand + explicit list) ---
    all_associations: list[dict] = list(associations or [])
    if workspace_uid:
        all_associations.append({
            "entityId": new_uuid(),
            "entityType": "urn:elli:encompass:workspace",
            "entityUID": workspace_uid,
            "relationship": "workspace",
        })

    if all_associations:
        parts.append("<associations>")
        for assoc in all_associations:
            a_id = assoc.get("entityId") or new_uuid()
            a_type = assoc.get("entityType", "urn:elli:encompass:workspace")
            a_uid = assoc.get("entityUID", "")
            a_rel = assoc.get("relationship", "workspace")
            parts.append(
                f'<association entityId="{_esc(str(a_id))}"'
                f' entityType="{_esc(a_type)}"'
                f' entityUID="{_esc(a_uid)}"'
                f' relationship="{_esc(a_rel)}"/>'
            )
        parts.append("</associations>")

    # --- authorizations ---
    if authorizations:
        parts.append("<authorizations>")
        for auth in authorizations:
            au_id = auth.get("entityId", "")
            au_type = auth.get("entityType", "")
            au_uid = auth.get("entityUID", "")
            au_rel = auth.get("relationship", "CAN_CREATE")
            parts.append(
                f'<authorization entityId="{_esc(str(au_id))}"'
                f' entityType="{_esc(au_type)}"'
                f' entityUID="{_esc(au_uid)}"'
                f' relationship="{_esc(au_rel)}"/>'
            )
        parts.append("</authorizations>")

    # --- subTaskTemplates ---
    parts.append("<subTaskTemplates>")
    for i, st in enumerate(subtasks, start=1):
        st_id = new_uuid()
        st_name = st.get("name", f"Sub-Task {i}")
        st_desc = st.get("description", "")
        st_type_key = st.get("type", "standard")
        # Subtask type attribute uses en-dash convention: "ParentName – SubtaskName"
        st_type_attr = f"{name} \u2013 {st_name}"
        st_required = st.get("required", st_type_key == "standard")
        st_auto_create = st.get("auto_create", st_type_key == "standard")
        st_rank = st.get("rank", i)
        # Allow explicit category override; fall back to type mapping
        st_category = st.get("category") or _category.get(st_type_key, "Regular")

        st_attrs = {
            "id": st_id,
            "name": st_name,
            "description": st_desc,
            "type": st_type_attr,
            "required": str(st_required).lower(),
            "priority": str(i),
            "rank": str(st_rank),
            "created": ts,
            "createdBy": created_by,
            "lastModified": ts,
            "lastModifiedBy": created_by,
            "autoCreate": str(st_auto_create).lower(),
            "category": st_category,
        }
        st_attr_str = " ".join(f'{k}="{_esc(str(v))}"' for k, v in st_attrs.items())

        st_associations = st.get("associations", [])
        if st_associations:
            parts.append(f"<subTaskTemplate {st_attr_str}>")
            parts.append("<associations>")
            for assoc in st_associations:
                a_id = assoc.get("entityId") or new_uuid()
                a_type = assoc.get("entityType", "urn:elli:encompass:document-workspaceoverride-0")
                a_uid = assoc.get("entityUID", "")
                a_rel = assoc.get("relationship", "document-workspaceoverride-0")
                parts.append(
                    f'<association entityId="{_esc(str(a_id))}"'
                    f' entityType="{_esc(a_type)}"'
                    f' entityUID="{_esc(a_uid)}"'
                    f' relationship="{_esc(a_rel)}"/>'
                )
            parts.append("</associations>")
            parts.append("</subTaskTemplate>")
        else:
            parts.append(f"<subTaskTemplate {st_attr_str}/>")

    parts.append("</subTaskTemplates>")
    parts.append("</taskTemplate>")
    parts.append("</taskTemplates>")

    return "".join(parts), task_id


# ---------------------------------------------------------------------------
# File writer
# ---------------------------------------------------------------------------

def write_task_xml(xml_str: str, output_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(xml_str)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Generate a mortgage workflow task XML file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--name", required=True, help="Task display name")
    p.add_argument("--type", dest="task_type", required=True,
                   help="Task type string (e.g. Processing_Credit_Review)")
    p.add_argument("--description", default="", help="Task description")
    p.add_argument("--comments", default="", help="Task comments")
    p.add_argument("--priority", type=int, default=3,
                   help="XML priority 1-5 (or pass --roadmap-priority for auto-map)")
    p.add_argument("--roadmap-priority", type=int, default=None,
                   help="Roadmap priority 1-10; auto-maps to XML 1-5")
    p.add_argument("--rank", type=int, default=1)
    p.add_argument("--created-by", default="agent")
    p.add_argument("--autocomplete", action="store_true", default=False)
    p.add_argument("--auto-create", action="store_true", default=False)
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--duration-format", default="Minute",
                   choices=["Minute", "Hour", "Day", "Week"])
    p.add_argument("--task-group-id", default=None,
                   help=(
                       "taskGroupTemplateId UUID — must be the SAME value for all tasks "
                       "that belong to the same Encompass task group. "
                       "A fresh UUID is auto-generated if omitted (use only for single-task groups)."
                   ))
    p.add_argument("--task-group-name", default="",
                   help="taskGroupTemplateName display label (e.g. 'Service Orders')")
    p.add_argument("--workspace-uid", default="",
                   help="Convenience: adds a workspace association with this entityUID")
    p.add_argument(
        "--associations",
        default=None,
        help=(
            "JSON array of task-level association objects. "
            "Each: {entityId?, entityType, entityUID, relationship}. "
            "entityId is auto-generated if omitted. "
            "Examples: role Assignee, workspace. "
            "--workspace-uid entries are appended automatically."
        ),
    )
    p.add_argument(
        "--authorizations",
        default=None,
        help=(
            "JSON array of authorization objects. "
            "Each: {entityId, entityType, entityUID, relationship}. "
            "relationship is typically CAN_CREATE."
        ),
    )
    p.add_argument(
        "--conditions",
        default=None,
        help=(
            "JSON object for conditional overrides. Optional keys: "
            "priorities [{value, script}], "
            "assignees [{script, entityId, entityType}], "
            "descriptions [{value, script}], "
            "dues [{script, duration, durationFormat}]."
        ),
    )
    p.add_argument(
        "--subtasks",
        default=None,
        help=(
            "JSON array of subtask objects. Each object may have: "
            "name, description, type (standard|conditional|later|informational), "
            "category (overrides type-derived category), "
            "required, auto_create, rank, associations."
        ),
    )
    p.add_argument("--out", required=True, help="Output XML file path")
    p.add_argument("--json", action="store_true",
                   help="Output result as JSON (default: plain text)")
    return p.parse_args(argv)


def _parse_json_arg(raw: str | None, label: str) -> tuple[any, str | None]:
    """Parse a JSON CLI arg. Returns (parsed, error_message)."""
    if raw is None:
        return None, None
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid {label} JSON: {exc}"


def main(argv=None):
    args = parse_args(argv)

    # Priority resolution
    priority = args.priority
    if args.roadmap_priority is not None:
        priority = map_priority(args.roadmap_priority)

    # Parse JSON args
    subtasks, err = _parse_json_arg(args.subtasks, "--subtasks")
    if err:
        print(json.dumps({"ok": False, "error": err}))
        return 1
    subtasks = subtasks or []

    associations, err = _parse_json_arg(args.associations, "--associations")
    if err:
        print(json.dumps({"ok": False, "error": err}))
        return 1

    authorizations, err = _parse_json_arg(args.authorizations, "--authorizations")
    if err:
        print(json.dumps({"ok": False, "error": err}))
        return 1

    conditions, err = _parse_json_arg(args.conditions, "--conditions")
    if err:
        print(json.dumps({"ok": False, "error": err}))
        return 1

    try:
        xml_str, task_id = build_task_xml(
            name=args.name,
            task_type=args.task_type,
            description=args.description,
            comments=args.comments,
            priority=priority,
            rank=args.rank,
            created_by=args.created_by,
            autocomplete=args.autocomplete,
            auto_create=args.auto_create,
            duration=args.duration,
            duration_format=args.duration_format,
            task_group_template_id=args.task_group_id,
            task_group_template_name=args.task_group_name,
            workspace_uid=args.workspace_uid,
            associations=associations,
            authorizations=authorizations,
            conditions=conditions,
            subtasks=subtasks,
        )
        write_task_xml(xml_str, args.out)
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
        print(json.dumps(result))
        return 1

    result = {"ok": True, "file": args.out, "task_id": task_id}
    if args.json:
        print(json.dumps(result))
    else:
        print(f"Created: {args.out}  (task id: {task_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
