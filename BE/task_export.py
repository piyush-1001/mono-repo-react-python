"""Serialise ranked tasks for download.

The ranker in task_ranker.py returns dicts that mix the fields stored by the
Node.js API (title, status, priority) with the fields it computed itself (score,
reasons). This module turns those dicts into the two formats people actually
open in a spreadsheet or a README: CSV and Markdown.

Standard library only. Nothing here talks to FastAPI or to storage; the modules
are deliberately separate so the export logic can be reused from a script, a
test, or an endpoint alike.
"""

import csv
from datetime import datetime, timezone
from io import StringIO

# Header row is fixed: export files are diffed and opened in spreadsheets,
# where a changing column order is more annoying than a missing field.
HEADERS = ("id", "title", "status", "priority", "score", "reasons", "created")

REASON_SEPARATOR = "; "

STATUS_LABELS = {
    "pending": "Pending",
    "in-progress": "In progress",
    "done": "Done",
}


def _text(value):
    """Render any value as a plain string, with None becoming empty."""
    if value is None:
        return ""
    return str(value)


def _reasons(task):
    """Flatten the ranker's reason list into one cell."""
    reasons = task.get("reasons") or []
    if isinstance(reasons, str):
        return reasons
    return REASON_SEPARATOR.join(_text(reason) for reason in reasons)


def _created(task):
    """Keep timestamps short and sortable (YYYY-MM-DD)."""
    created_at = _text(task.get("created_at") or task.get("createdAt"))
    if not created_at:
        return ""
    try:
        stamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return created_at
    return stamp.strftime("%Y-%m-%d")


def to_rows(tasks):
    """Normalise task dicts into ordered string rows, header included."""
    rows = [list(HEADERS)]
    for task in tasks:
        rows.append(
            [
                _text(task.get("id")),
                _text(task.get("title")),
                _text(task.get("status")),
                _text(task.get("priority")),
                _text(task.get("score")),
                _reasons(task),
                _created(task),
            ]
        )
    return rows


def to_csv(tasks):
    """Render tasks as a CSV document (RFC 4180 quoting, \\n line endings)."""
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(to_rows(tasks))
    return buffer.getvalue()


def _markdown_cell(value):
    """Escape what would otherwise break a Markdown table row."""
    text = _text(value).replace("|", "\\|")
    # Tables are single-line, so fold newlines into spaces.
    return " ".join(text.split())


def to_markdown(tasks, title="Task ranking"):
    """Render tasks as a Markdown table with a short summary above it."""
    header = "| # | Task | Status | Priority | Score | Why |"
    divider = "| --- | --- | --- | --- | --- | --- |"

    lines = [f"## {title}", ""]
    if not tasks:
        lines.append("_No tasks to export._")
        return "\n".join(lines) + "\n"

    lines.extend([summary(tasks), "", header, divider])

    for position, task in enumerate(tasks, start=1):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(position),
                    _markdown_cell(task.get("title")),
                    STATUS_LABELS.get(
                        _text(task.get("status")), _text(task.get("status"))
                    ),
                    _markdown_cell(task.get("priority")),
                    _markdown_cell(task.get("score")),
                    _markdown_cell(_reasons(task)),
                )
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def summary(tasks):
    """One-line human summary of an export, used above the Markdown table."""
    total = len(tasks)
    open_tasks = [task for task in tasks if _text(task.get("status")) != "done"]
    top = open_tasks[0] if open_tasks else None

    parts = [f"**{total}** task{'' if total == 1 else 's'} exported"]
    parts.append(f"**{len(open_tasks)}** still open")
    if top is not None:
        parts.append(f"next up: **{_text(top.get('title')) or 'untitled'}**")
    return ", ".join(parts) + "."


def export_filename(scope="tasks", when=None):
    """Timestamped file name, so repeated exports do not overwrite each other."""
    stamp = (when or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    safe_scope = "".join(
        character for character in scope if character.isalnum() or character in "-_"
    )
    return f"{safe_scope or 'tasks'}-{stamp}.csv"
