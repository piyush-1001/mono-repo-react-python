"""What the board looks like right now.

The Node.js API knows how many tasks there are. It does not know how old they
are, how urgent they read, or which one should be picked up next - those need
the clock and the ranker, which live here.

Everything is computed from a list of task dicts, so the same report can be
produced for the stored board or for a list posted by a caller. The endpoint
that reads the store is in main.py; this module only does the arithmetic.
"""

from collections import Counter
from datetime import datetime, timezone

from ml_models import tokenize
from task_fields import (
    PRIORITIES,
    STATUSES,
    age_days,
    is_open,
    normalise_priority,
    normalise_status,
)
from task_ranker import URGENCY_WORDS, rank_tasks

# How long a task may sit before it counts as aging, and before it is stale.
# The ranker uses a seven-day half-life for the same idea, so a task crosses
# from "aging" to "stale" at the point where its staleness weight reaches
# half - which is what makes the two agree.
AGING_AFTER_DAYS = 1.0
STALE_AFTER_DAYS = 7.0

# How many tasks the "do this next" and "left longest" lists show. Three is
# what fits on a phone screen without scrolling.
FOCUS_LIMIT = 3


def _age_bucket(days):
    """Which age group a task falls into."""
    if days is None:
        return "unknown"
    if days < AGING_AFTER_DAYS:
        return "fresh"
    if days < STALE_AFTER_DAYS:
        return "aging"
    return "stale"


def _is_urgent(title):
    """Whether a title says the work is pressing.

    The same word list the ranker scores with, so a task the ranker calls
    urgent is a task this report calls urgent.
    """
    return any(word in URGENCY_WORDS for word in tokenize(title))


def _summary(task, days):
    """The part of a task the report shows."""
    return {
        "id": task.get("id"),
        "title": task.get("title", ""),
        "status": normalise_status(task.get("status")),
        "priority": normalise_priority(task.get("priority")),
        "score": task.get("score"),
        "age_days": round(days, 1) if days is not None else None,
    }


def analyse(tasks, now=None):
    """Summarise a list of tasks: the mix, their ages, and what to do next."""
    now = now or datetime.now(timezone.utc)
    ranked = rank_tasks(tasks)
    rows = ranked["ranked"]

    open_rows = [task for task in rows if is_open(task)]
    closed = [task for task in rows if not is_open(task)]

    by_status = Counter(normalise_status(task.get("status")) for task in rows)
    by_priority = Counter(normalise_priority(task.get("priority")) for task in rows)

    # Open tasks paired with their age, rather than a dict keyed by id: two
    # tasks with the same id (or none) would otherwise share one age.
    dated = [(task, age_days(task.get("created_at"), now)) for task in open_rows]
    buckets = Counter(_age_bucket(days) for _, days in dated)

    urgent = [
        (task, days) for task, days in dated if _is_urgent(task.get("title", ""))
    ]
    oldest = sorted(
        (entry for entry in dated if entry[1] is not None),
        key=lambda entry: entry[1],
        reverse=True,
    )

    scores = [task.get("score", 0.0) for task in open_rows]

    return {
        "total": len(rows),
        "open": len(open_rows),
        "done": len(closed),
        "by_status": {status: by_status.get(status, 0) for status in STATUSES},
        "by_priority": {priority: by_priority.get(priority, 0) for priority in PRIORITIES},
        "age_buckets": {
            "fresh": buckets.get("fresh", 0),
            "aging": buckets.get("aging", 0),
            "stale": buckets.get("stale", 0),
            "unknown": buckets.get("unknown", 0),
        },
        "urgent_open": [
            _summary(task, days) for task, days in urgent[:FOCUS_LIMIT]
        ],
        "oldest_open": [
            _summary(task, days) for task, days in oldest[:FOCUS_LIMIT]
        ],
        "focus": [
            {
                **_summary(task, days),
                "reasons": task.get("reasons", []),
            }
            for task, days in dated[:FOCUS_LIMIT]
        ],
        "mean_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "next_task_id": ranked.get("next_task_id"),
        "duplicates": len(ranked.get("duplicates", [])),
    }
