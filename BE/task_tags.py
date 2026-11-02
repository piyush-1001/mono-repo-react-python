"""Read the #hashtags people already type into task titles.

The board has no labels column: the Node.js store holds id, title, status,
priority and a timestamp, and adding a tags field would mean a schema change in
the store, in the Python request models and on the phone, for something people
write as "#api" in the title anyway. This module reads the tags that are there
rather than waiting for a column that would say the same thing.

Tags are reported, never enforced. Nothing here rejects a task, renames a tag or
suggests a spelling: an invented vocabulary would make the report disagree with
the board, and the board is what the user reads. What the module does say, in
`notes`, is where the typing is inconsistent - two spellings of one tag, a tag
that repeats a status word - because those are the cases where the count on
screen is not the count the user meant.
"""

import re
from collections import Counter, defaultdict

from task_fields import PRIORITIES, STATUSES, is_open

# A tag is a hash followed by a letter, then letters, digits, underscores or
# hyphens. Requiring a letter after the hash is what stops "#1" or a bare "#"
# from becoming a tag, and the character class stops at punctuation, so
# "ship #api." yields "api" and not "api." - a period would otherwise split one
# tag from itself every time a title ended in a full stop.
TAG_RE = re.compile(r"#([A-Za-z][\w-]*)")

# Longer than this is a sentence with a hash in front of it, not a label.
MAX_TAG_LENGTH = 32

MAX_TASKS_PER_TAG = 10

DEFAULT_MIN_COUNT = 1
DEFAULT_LIMIT = 30
MAX_LIMIT = 100


def _clamp(value, default, highest, lowest=1):
    """Keep a caller's numbers inside the range the report is meant for."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(lowest, min(number, highest))


def _tidy(raw):
    """A tag's canonical spelling, or None when it is not usable.

    Lowercased, because "#API" and "#api" are one label wearing two faces and a
    report that counted them apart would understate both. A trailing hyphen is
    dropped - people wrap a tag at the end of a line and the hyphen is theirs,
    not the label's.
    """
    tag = raw.strip().lower().rstrip("-_")
    if not tag or len(tag) > MAX_TAG_LENGTH:
        return None
    return tag


def tags_in(text):
    """The distinct tags in one piece of text, in the order they appear."""
    seen = []
    for match in TAG_RE.finditer(text or ""):
        tag = _tidy(match.group(1))
        if tag and tag not in seen:
            seen.append(tag)
    return seen


def scan(tasks, min_count=DEFAULT_MIN_COUNT, limit=DEFAULT_LIMIT):
    """Group the board by the tags its titles carry.

    `min_count` drops tags that appear less often than a threshold, which is how
    a hundred-one-task board becomes a readable list; `limit` caps how many tags
    come back. Both are reported when they change the answer, so a short list is
    never mistaken for the whole board.
    """
    counts = Counter()
    holders = defaultdict(list)
    # Variants are the as-typed spellings per tag, kept only to be able to say
    # "#API and #api were the same tag" - the count itself stays case-blind.
    variants = defaultdict(set)
    tagged_ids = set()

    for task in tasks:
        title = task.get("title")
        text = title if isinstance(title, str) else ""
        found = tags_in(text)
        if not found:
            continue

        tagged_ids.add(task.get("id"))
        for raw in TAG_RE.findall(text):
            tag = _tidy(raw)
            if tag:
                variants[tag].add(raw)

        for tag in found:
            counts[tag] += 1
            holders[tag].append(
                {
                    "id": task.get("id"),
                    "title": text,
                    "status": task.get("status"),
                    "priority": task.get("priority"),
                }
            )

    # Count first, name second: a tag seen six times is worth reading before one
    # seen once, and the alphabetical tie-break keeps the order stable when two
    # are tied rather than following dictionary insertion order.
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    floor = _clamp(min_count, DEFAULT_MIN_COUNT, 10)
    ceiling = _clamp(limit, DEFAULT_LIMIT, MAX_LIMIT)

    notes = []
    passing = [item for item in ordered if item[1] >= floor]
    hidden = len(ordered) - len(passing)
    if hidden:
        notes.append(
            f"{hidden} tag{'' if hidden == 1 else 's'} used fewer than {floor}"
            f" time{'' if floor == 1 else 's'} were left out"
        )

    shown = passing[:ceiling]
    if len(passing) > ceiling:
        notes.append(
            f"showing {ceiling} of {len(passing)} tags; the rest are less common"
        )

    result = []
    for tag, count in shown:
        held = holders[tag]
        result.append(
            {
                "tag": tag,
                "count": count,
                "open": sum(1 for task in held if is_open(task)),
                "done": sum(1 for task in held if not is_open(task)),
                "variants": sorted(variants[tag] - {tag}),
                "tasks": held[:MAX_TASKS_PER_TAG],
                "truncated": len(held) > MAX_TASKS_PER_TAG,
            }
        )

        if len(held) > MAX_TASKS_PER_TAG:
            # A per-tag note would need a place to live, so this rides on the
            # shared list: the sample is capped, the count is not.
            notes.append(f"'#{tag}' has {count} tasks; showing {MAX_TASKS_PER_TAG}")

        spellings = variants[tag]
        if len(spellings) > 1:
            notes.append(
                f"'#{tag}' is typed as {', '.join('#' + s for s in sorted(spellings))}"
            )

        # A tag that repeats a column is usually someone labelling the column,
        # which reads as content in a report about content.
        if tag in STATUSES or tag in PRIORITIES:
            notes.append(
                f"'#{tag}' repeats the {'status' if tag in STATUSES else 'priority'}"
                " column; the filter already says it"
            )

    if not counts:
        notes.append("no hashtags found in any title")

    return {
        "tags": result,
        "distinct": len(counts),
        "board": len(tasks),
        "tagged": len(tagged_ids),
        "untagged": len(tasks) - len(tagged_ids),
        "min_count": floor,
        "limit": ceiling,
        "notes": notes,
    }
