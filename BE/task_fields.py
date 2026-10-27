"""The vocabulary of a task, in one place.

The Node.js store, the FastAPI models and the ranker all have to agree on what a
status and a priority may be. The ranker already knows: it weighs priority as
{high: 3, medium: 2, low: 1} and falls back to medium for anything it does not
recognise, so an unknown priority is not an error but a silent downgrade - a
task called "High" would be accepted and then scored as if it were medium.

This module takes the vocabulary from the ranker's own weights, so there is one
list rather than three that can drift apart. The Node.js store keeps its own
copy of the same lists; they are small and explicit, and the check at the end
of this file is what keeps them honest when the ranker changes.
"""

from datetime import datetime, timezone

from task_ranker import PRIORITY_WEIGHTS, STATUS_WEIGHTS

# The order is the ranker's, not alphabetical: the fallbacks ("pending",
# "medium") are what a task gets when its own value is missing, so they are
# read first.
STATUSES = tuple(STATUS_WEIGHTS)
PRIORITIES = tuple(PRIORITY_WEIGHTS)

# A task is open until it is done. The ranker uses the same rule to decide
# which task comes next.
CLOSED_STATUS = "done"

DEFAULT_STATUS = "pending"
DEFAULT_PRIORITY = "medium"

# Both fallbacks have to be real values, or normalise_* would invent a status
# the rest of the system does not know.
assert DEFAULT_STATUS in STATUSES
assert DEFAULT_PRIORITY in PRIORITIES


def normalise_status(value, default=DEFAULT_STATUS):
    """A known status, or the default.

    Case and surrounding whitespace are tolerated, because a status that reaches
    the API as "Pending" is the same status as "pending" and rejecting it would
    be pedantry rather than validation.
    """
    if isinstance(value, str):
        candidate = value.strip().lower()
        if candidate in STATUSES:
            return candidate
    return default


def normalise_priority(value, default=DEFAULT_PRIORITY):
    """A known priority, or the default. See normalise_status."""
    if isinstance(value, str):
        candidate = value.strip().lower()
        if candidate in PRIORITIES:
            return candidate
    return default


def is_open(task):
    """True while a task still needs doing."""
    return normalise_status(task.get("status")) != CLOSED_STATUS


def age_days(created_at, now=None):
    """How old a task is, in days, or None when it has no usable timestamp.

    The ranker has its own version of this calculation, weighted by how stale
    the task is; this one is the plain age, which is what the insights report
    shows next to a task.
    """
    if not created_at:
        return None
    try:
        stamp = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return max((now - stamp).total_seconds() / 86400, 0.0)
