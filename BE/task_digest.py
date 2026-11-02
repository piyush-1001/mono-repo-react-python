"""The board, written out for a standup.

The Export Center hands over a ranking: a table, ordered by score, meant for a
file. This is the other kind of document - a short piece of plain text with the
counts a standup actually asks for, ready to be pasted into a chat: what is
done, what is in flight, what has been waiting, and what to pick up next.

The numbers and the titles come from the reports that already exist - the
insights report for the ages and the mix, the ranker for the order - so the
digest cannot disagree with the pages it was built from. It is a summary of the
board, not a second opinion about it.

Where a report caps a list - the insights report shows three tasks of "waiting
longest" - this module counts for itself rather than repeating the cap, so the
text says how many are waiting instead of quietly showing three of them.
"""

from datetime import datetime, timezone

from ml_models import tokenize
from task_fields import age_days, is_open
from task_insights import analyse
from task_ranker import URGENCY_WORDS, rank_tasks

# How many tasks each list shows before it says how many more there are.
LIST_LIMIT = 5

# The headings, kept as constants because the React page shows them as section
# labels too, and two spellings of "Waiting longest" would be a small mess.
HEADING_IN_PROGRESS = "In progress"
HEADING_WAITING = "Waiting longest"
HEADING_NEXT = "Next up"


def _line(task):
    """One task as a single line of the digest."""
    title = (task.get("title") or "").strip() or "untitled"
    line = f"- {title} (#{task.get('id')})"
    age = task.get("age_days")
    if age is not None:
        line = f"{line} - {round(age)} days waiting"
    return line


def _section(heading, tasks, limit=LIST_LIMIT):
    """A heading, its tasks, and an honest count of what was left out."""
    if not tasks:
        return []

    lines = [f"{heading} ({len(tasks)}):"]
    shown = tasks[:limit]
    lines.extend(_line(task) for task in shown)
    if len(tasks) > limit:
        lines.append(f"- ... and {len(tasks) - limit} more")
    return lines


def _empty_digest(now):
    """The digest for a board with nothing on it."""
    lines = [
        f"Task board - {now.strftime('%Y-%m-%d')} (UTC)",
        "0 tasks: 0 open, 0 done",
        "",
        "The board is empty.",
    ]
    return {
        "text": "\n".join(lines) + "\n",
        "generated_at": now.isoformat(),
        "stats": {
            "total": 0,
            "open": 0,
            "done": 0,
            "in_progress": 0,
            "stale": 0,
            "urgent": 0,
            "mean_score": 0.0,
        },
        "next_task_id": None,
    }


def digest(tasks, now=None):
    """Write the board out as plain text.

    `now` is passed in rather than read from the clock so the ages in the text
    match the ages in the report next to it.
    """
    now = now or datetime.now(timezone.utc)
    if not tasks:
        return _empty_digest(now)

    # The ranker is run here as well as inside analyse(), because the digest
    # needs the per-task statuses and the insight report does not list them.
    # Two runs over a board this size cost nothing, and it keeps the insights
    # report's shape from being bent around this one.
    stats = analyse(tasks, now=now)
    ranked = rank_tasks(tasks)["ranked"]

    in_progress = [task for task in ranked if task.get("status") == "in-progress"]

    open_tasks = [task for task in ranked if is_open(task)]
    dated = [(task, age_days(task.get("created_at"), now)) for task in open_tasks]
    dated.sort(key=lambda entry: entry[1] if entry[1] is not None else -1, reverse=True)
    waiting = [
        {
            "id": task.get("id"),
            "title": task.get("title"),
            "age_days": days,
        }
        for task, days in dated
    ]

    # The same word list the ranker scores with, so a task it reads as urgent is
    # a task the digest reads as urgent. Counted here rather than taken from the
    # insights report, which caps that list at three.
    urgent = [
        task
        for task in open_tasks
        if any(word in URGENCY_WORDS for word in tokenize(task.get("title", "")))
    ]

    focus = stats["focus"]

    lines = [
        f"Task board - {now.strftime('%Y-%m-%d')} (UTC)",
        f"{stats['total']} task{'' if stats['total'] == 1 else 's'}: "
        f"{stats['open']} open, {stats['done']} done",
        "",
    ]

    lines.extend(_section(HEADING_IN_PROGRESS, in_progress))
    lines.extend(_section(HEADING_WAITING, waiting))

    if focus:
        lines.append("")
        lines.append(f"{HEADING_NEXT}:")
        task = focus[0]
        reasons = task.get("reasons") or []
        line = _line(task)
        if reasons:
            line = f"{line} - {', '.join(reasons)}"
        lines.append(line)

    stale = stats["age_buckets"].get("stale", 0)
    lines.append("")
    lines.append(
        f"Stale (more than 7 days): {stale}   Reads as urgent: {len(urgent)}"
    )

    return {
        "text": "\n".join(lines) + "\n",
        "generated_at": now.isoformat(),
        "stats": {
            "total": stats["total"],
            "open": stats["open"],
            "done": stats["done"],
            "in_progress": len(in_progress),
            "stale": stale,
            "urgent": len(urgent),
            "mean_score": stats["mean_score"],
        },
        "next_task_id": stats.get("next_task_id"),
    }
