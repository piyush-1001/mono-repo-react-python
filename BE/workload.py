"""Spread the open tasks over the next few working days.

task_ranker.py answers "what is next". This answers a different question - "what
fits before Friday" - which the ranking alone cannot: eleven tasks in score order
tells you the top of the list, not that four a day leaves three of them still
sitting here next Monday.

The order is the ranker's, unchanged. Nothing here re-scores anything; it takes
the ranked list, keeps the open tasks, and fills days at a chosen capacity. So a
task the ranker put first is scheduled first, and the reasons the ranker gave
travel with the task into the plan, which is how a plan gets argued with.

What this module is careful about is the overflow. Tasks that do not fit are
listed, counted, and named in the notes; they are never dropped. A plan that
looks like a week you can finish, because the awkward part was left out of the
list, is the one way this feature could actively do harm.
"""

from datetime import date, datetime, timedelta, timezone

from task_fields import is_open
from task_ranker import rank_tasks

DEFAULT_DAYS = 5
MAX_DAYS = 14
DEFAULT_PER_DAY = 3
MAX_PER_DAY = 10

# Monday-first names, indexable by date.weekday(), which is also Monday-first.
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _clamp(value, default, highest):
    """Keep a caller's numbers inside the range the plan is meant for.

    The HTTP layer validates these too. This is here because the function is
    also called from scripts and tests, and a plan over 5,000 days or at zero
    tasks a day is a response nobody meant to ask for.
    """
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(number, highest))


def _upcoming_days(start, count):
    """The next `count` weekdays from `start`, weekend days skipped.

    Weekends are skipped rather than counted, because a plan that puts Tuesday's
    work on a Saturday is a plan the user will silently break on the first week.
    Skipping them means the horizon stretches: five days of work starting on a
    Friday run into the following Wednesday.
    """
    days = []
    cursor = start
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _entry(task):
    """The fields a scheduled task carries into the response.

    The score and the reasons come along deliberately: a day that lists four
    tasks without saying why those four is a list of orders, not a plan.
    """
    return {
        "id": task.get("id"),
        "title": task.get("title"),
        "status": task.get("status"),
        "priority": task.get("priority"),
        "score": task.get("score", 0.0),
        "reasons": task.get("reasons", []),
    }


def plan(tasks, days=DEFAULT_DAYS, per_day=DEFAULT_PER_DAY, start=None):
    """Fill the next working days with the open tasks, highest ranked first.

    Returns the schedule, what did not fit, and the notes that explain the shape
    of both - including the case where there is more capacity than work, because
    an empty last day is a fact worth stating rather than a surprise.
    """
    horizon = _clamp(days, DEFAULT_DAYS, MAX_DAYS)
    capacity = _clamp(per_day, DEFAULT_PER_DAY, MAX_PER_DAY)

    if start is None:
        # UTC, like every other timestamp this service produces. The labels are
        # therefore a day off for anyone far from the meridian, which is stated
        # rather than papered over with a local-time guess.
        start = datetime.now(timezone.utc).date()
    elif isinstance(start, datetime):
        start = start.date()
    elif not isinstance(start, date):
        raise TypeError(f"start must be a date or None, not {type(start).__name__}")

    ranked = rank_tasks(tasks)["ranked"]
    open_tasks = [task for task in ranked if is_open(task)]

    schedule_days = _upcoming_days(start, horizon)

    schedule = []
    for index, day in enumerate(schedule_days):
        slice_start = index * capacity
        slice_end = slice_start + capacity
        # Slicing past the end is how the short list case works: the last days
        # come back with no tasks, and the notes below say why.
        slot = open_tasks[slice_start:slice_end]
        if not slot and not schedule:
            # Nothing scheduled at all, so the board is simply empty.
            break
        schedule.append(
            {
                "date": day.isoformat(),
                "weekday": WEEKDAY_NAMES[day.weekday()],
                "capacity": capacity,
                "tasks": [_entry(task) for task in slot],
                # Full to the brim is a warning, not an achievement: a day at
                # capacity with tasks still waiting is the day the plan slips.
                "full": len(slot) == capacity,
            }
        )

    scheduled = sum(len(day["tasks"]) for day in schedule)
    unscheduled = [_entry(task) for task in open_tasks[scheduled:]]

    notes = []
    if not open_tasks:
        notes.append("nothing open: every task on the board is done")
    elif unscheduled:
        notes.append(
            f"{len(unscheduled)} open task{'' if len(unscheduled) == 1 else 's'} "
            f"do not fit inside {horizon} day{'' if horizon == 1 else 's'} at "
            f"{capacity} a day"
        )
    else:
        # Capacity left over. Report it as slack rather than pretending the
        # horizon was exactly right.
        slack = len(schedule) * capacity - scheduled
        if slack and scheduled:
            notes.append(
                f"{slack} slot{'' if slack == 1 else 's'} spare across the "
                f"{len(schedule)} planned day{'' if len(schedule) == 1 else 's'}"
            )

    span_end = schedule[-1]["date"] if schedule else None
    if span_end and (date.fromisoformat(span_end) - start).days > horizon - 1:
        # The tell-tale of weekend skipping: more calendar days crossed than
        # days of work planned. Said out loud so a reader does not think the
        # plan drifted.
        notes.append(
            f"the horizon runs to {span_end} because weekend days are not planned"
        )

    return {
        "start": start.isoformat(),
        "days_planned": len(schedule),
        "days_requested": horizon,
        "per_day": capacity,
        "capacity": len(schedule) * capacity,
        "open_count": len(open_tasks),
        "scheduled": scheduled,
        "schedule": schedule,
        "unscheduled": unscheduled,
        "notes": notes,
    }
