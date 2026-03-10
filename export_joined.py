#!/usr/bin/env python3
"""
export_joined.py — Merge one or more task XML files into a single joined XML.

The output matches the format shown in ExampleJoined.xml:
  - Single XML declaration header
  - Single <taskTemplates> root
  - All <taskTemplate> elements (with children) concatenated inside
  - Inline formatting (no pretty-print), per project conventions

Usage (AI agent or CLI):
    # Merge specific files:
    python export_joined.py --files tasks/a.xml tasks/b.xml --out joined.xml

    # Merge all XML files under a directory (recursive):
    python export_joined.py --dir tasks/2_processing --out joined.xml

    # Merge entire tasks/ tree (common export use-case):
    python export_joined.py --dir tasks --out all_tasks_joined.xml

    # Output to stdout instead of a file:
    python export_joined.py --dir tasks --stdout

Return value (stdout when not using --stdout, JSON with --json flag):
    {"ok": true, "file": "<path>", "task_count": N}
    {"ok": false, "error": "<message>"}

Exit codes: 0 = success, 1 = error.
"""

import argparse
import glob
import json
import os
import re
import sys
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# Core merger
# ---------------------------------------------------------------------------

_XML_DECL = "<?xml version='1.0' encoding='UTF-8'?>"
_DECL_RE = re.compile(r"<\?xml[^?]*\?>", re.IGNORECASE)


def _strip_declaration(xml_str: str) -> str:
    """Remove the XML declaration from a string."""
    return _DECL_RE.sub("", xml_str, count=1).lstrip()


def _inner_content(xml_str: str) -> str:
    """
    Return everything between the opening and closing <taskTemplates> tags.
    Works on inline (single-line) XML produced by this project.
    """
    # Use ElementTree to parse reliably, then re-serialise children inline.
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as exc:
        raise ValueError(f"XML parse error: {exc}") from exc

    if root.tag != "taskTemplates":
        raise ValueError(
            f"Expected root element <taskTemplates>, got <{root.tag}>"
        )

    # Serialise each child back to a string (inline, no declaration).
    parts = []
    for child in root:
        chunk = ET.tostring(child, encoding="unicode", xml_declaration=False)
        parts.append(chunk)
    return "".join(parts)


def collect_xml_files(paths: list[str], directories: list[str]) -> list[str]:
    """
    Collect XML file paths from explicit --files and --dir arguments.
    Files are deduplicated while preserving first-seen order.
    """
    seen: set[str] = set()
    result: list[str] = []

    def add(p: str) -> None:
        abs_p = os.path.abspath(p)
        if abs_p not in seen:
            seen.add(abs_p)
            result.append(abs_p)

    for fp in paths:
        add(fp)

    for d in directories:
        # Walk recursively; sort for deterministic order
        for xml_path in sorted(glob.glob(os.path.join(d, "**", "*.xml"), recursive=True)):
            add(xml_path)

    return result


def merge_xml_files(file_paths: list[str]) -> tuple[str, int]:
    """
    Merge multiple task XML files into one joined XML string.

    Returns (joined_xml_string, task_count).
    """
    if not file_paths:
        raise ValueError("No XML files provided to merge.")

    inner_parts: list[str] = []
    task_count = 0

    for fp in file_paths:
        if not os.path.isfile(fp):
            raise FileNotFoundError(f"File not found: {fp}")
        with open(fp, "r", encoding="utf-8") as fh:
            raw = fh.read().strip()

        content = _inner_content(raw)
        # Count <taskTemplate ...> elements (not subTaskTemplate)
        task_count += content.count("<taskTemplate ")
        inner_parts.append(content)

    joined = _XML_DECL + "<taskTemplates>" + "".join(inner_parts) + "</taskTemplates>"
    return joined, task_count


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def write_joined(xml_str: str, output_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(xml_str)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Merge mortgage workflow task XML files into a single joined file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    src = p.add_argument_group("Source (at least one required)")
    src.add_argument(
        "--files", nargs="+", default=[], metavar="FILE",
        help="Explicit XML file path(s) to include.",
    )
    src.add_argument(
        "--dir", nargs="+", default=[], metavar="DIR",
        help="Directory/ies to search recursively for *.xml files.",
    )

    dst = p.add_argument_group("Destination (mutually exclusive)")
    out_group = dst.add_mutually_exclusive_group()
    out_group.add_argument("--out", default=None, metavar="FILE",
                           help="Output file path.")
    out_group.add_argument("--stdout", action="store_true",
                           help="Write joined XML to stdout instead of a file.")

    p.add_argument("--json", action="store_true",
                   help="Print result summary as JSON (ignored when --stdout is set).")

    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if not args.files and not args.dir:
        print(json.dumps({"ok": False, "error": "Provide --files and/or --dir."}))
        return 1

    if not args.stdout and not args.out:
        print(json.dumps({"ok": False, "error": "Provide --out <path> or --stdout."}))
        return 1

    try:
        file_paths = collect_xml_files(args.files, args.dir)
        joined_xml, task_count = merge_xml_files(file_paths)
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
        print(json.dumps(result))
        return 1

    if args.stdout:
        print(joined_xml)
        return 0

    try:
        write_joined(joined_xml, args.out)
    except Exception as exc:
        result = {"ok": False, "error": f"Write failed: {exc}"}
        print(json.dumps(result))
        return 1

    result = {"ok": True, "file": args.out, "task_count": task_count}
    if args.json:
        print(json.dumps(result))
    else:
        print(f"Joined {task_count} task(s) → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
