"""A query language for the board, and an account of what a query was taken to mean.

/api/tasks/search scores titles: it answers "which tasks are most like these
words". That is the right tool for a person who is not sure what they called the
thing, and the wrong one for a person who knows exactly what they want and wants
nothing else - "open, high priority, not the ones tagged #freeze". A scoring
search cannot say no: it returns the closest ten tasks to a query that matches
none of them, and the reader has to notice the low scores.

This module filters instead. Terms are combined with AND, a leading `-` excludes,
and a query that matches nothing returns nothing.

The parsing is strict on purpose, which is the opposite of the rule
BE/task_search.py follows when it drops an unrecognised filter with a note. The
difference is that a dropped filter still returns results you can look at, while
a *misread term in a filter* returns an empty list, and an empty list from a
filter reads as news about the board rather than news about the query. So a
value that is not one of the board's values raises QueryError instead of
matching no tasks, and an unknown field name says which fields exist.

Nothing here writes: it is a view over the rows the caller fetched. Closing,
re-prioritising, or deleting a task stays the Node store's business.
"""

import re

from task_fields import PRIORITIES, STATUSES, age_days, is_open
from task_tags import tags_in

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

# The fields a term may name. Kept to four: every field is something the board
# actually holds a value for, and a language grows faster than it shrinks.
STATUS_FIELD = "status"
PRIORITY_FIELD = "priority"
TAG_FIELD = "tag"
AGE_FIELDS = ("older", "newer")
FIELDS = (STATUS_FIELD, PRIORITY_FIELD, TAG_FIELD) + AGE_FIELDS

# Not a status the store can hold - `done` is - but the one question a board
# gets asked most, and is_open() already knows how to answer it.
OPEN_ALIAS = "open"

# How many other tags to name when a tag term matches nothing. Enough to spot a
# typo, short enough not to become the tag report (that is /api/tags).
TAG_SUGGESTIONS = 5

TERM_RE = re.compile(r"^(?P<neg>-)?(?P<body>.+)$")


class QueryError(ValueError):
    """The query cannot be read, so it was not run.

    A ValueError subclass so a caller that only catches the general case still
    treats it as a bad request rather than a server fault.
    """


def _field_error(value):
    fields = ", ".join(sorted(FIELDS))
    return (
        f"'{value}' is not a field this board has. Fields: {fields}, "
        "or a bare word to match the title"
    )


def _status_error(value):
    allowed = ", ".join(list(STATUSES) + [OPEN_ALIAS])
    return f"status must be one of: {allowed} (got '{value}')"


def _priority_error(value):
    allowed = ", ".join(PRIORITIES)
    return f"priority must be one of: {allowed} (got '{value}')"


def _days_error(value, field):
    return f"{field} wants a number of days, not '{value}'"


def _parse_day(value, field):
    try:
        days = int(value)
    except ValueError as error:
        raise QueryError(_days_error(value, field)) from error
    if days < 0:
        raise QueryError(f"{field} wants a number of days, not '{value}'")
    return days


def _tag_of(token):
    """The tag a term refers to, with the leading '#' optional."""
    return token[1:] if token.startswith("#") else token


def parse(text):
    """Turn a query string into the terms it means.

    Split on whitespace, so a value with a space in it is two terms - which is
    what a title search wants anyway ("learn react" asks for both words) and
    what a field value never needs, since none of the board's values hold a
    space.
    """
    terms = []

    for token in (text or "").split():
        match = TERM_RE.match(token)
        negated = match.group("neg") is not None
        body = match.group("body")

        if not body:
            raise QueryError("'-' on its own excludes nothing - give it something to exclude")

        if body.startswith("#"):
            tag = _tag_of(body)
            if not tag:
                raise QueryError("'#' names no tag - write it as #something")
            terms.append(
                {
                    "kind": TAG_FIELD,
                    "field": TAG_FIELD,
                    "value": tag.lower(),
                    "negated": negated,
                    "text": ("-" if negated else "") + f"#{tag}",
                }
            )
            continue

        field, separator, value = body.partition(":")
        if not separator:
            # A bare word: matched against the title, the same way the Node
            # store's own q parameter does it, so a phrase typed into either
            # front door asks for the same thing.
            terms.append(
                {
                    "kind": "word",
                    "field": None,
                    "value": body.lower(),
                    "negated": negated,
                    "text": ("-" if negated else "") + body,
                }
            )
            continue

        field = field.strip().lower()
        value = value.strip()

        if field not in FIELDS:
            raise QueryError(_field_error(field))
        if not value:
            raise QueryError(f"'{body}' names the {field} field but gives it no value")

        if field == STATUS_FIELD:
            candidate = value.lower()
            if candidate != OPEN_ALIAS and candidate not in STATUSES:
                raise QueryError(_status_error(value))
        elif field == PRIORITY_FIELD:
            candidate = value.lower()
            if candidate not in PRIORITIES:
                raise QueryError(_priority_error(value))
        elif field == TAG_FIELD:
            candidate = _tag_of(value).lower()
            if not candidate:
                raise QueryError(f"'{body}' names the tag field but gives it no tag")
        else:
            candidate = _parse_day(value, field)

        terms.append(
            {
                "kind": field,
                "field": field,
                "value": candidate,
                "negated": negated,
                "text": ("-" if negated else "") + f"{field}:{value}",
            }
        )

    return terms


def _matches(task, term):
    """Whether one term selects one task, before negation is applied."""
    kind = term["kind"]

    if kind == "word":
        return term["value"] in (task.get("title") or "").lower()

    if kind == TAG_FIELD:
        tags = {tag.lower() for tag in tags_in(task.get("title") or "")}
        return term["value"] in tags

    if kind == STATUS_FIELD:
        if term["value"] == OPEN_ALIAS:
            return is_open(task)
        return (task.get("status") or "") == term["value"]

    if kind == PRIORITY_FIELD:
        return (task.get("priority") or "") == term["value"]

    # older / newer never reach here: an age term needs `now` to decide, so the
    # caller sends them to _age_matches() instead. Arriving here means a new term
    # kind was added without a rule for it, which is worth a crash rather than a
    # None that every caller reads as "no".
    raise AssertionError(f"no match rule for a '{kind}' term")


def _age_matches(task, term, now):
    days = age_days(task.get("created_at"), now)
    if days is None:
        return None
    if term["kind"] == "older":
        return days >= term["value"]
    return days < term["value"]


def _explain(task, term):
    """The line a result carries for the term that let it through."""
    if term["kind"] == "word":
        return f"title holds '{term['value']}'"
    if term["kind"] == TAG_FIELD:
        return f"tagged #{term['value']}"
    return term["text"]


def _contradictions(terms):
    """Terms that cancel each other, so the report can say so before the reader
    concludes the board is empty."""
    seen = {}
    found = []
    for term in terms:
        key = (term["kind"], str(term["value"]))
        if key in seen and seen[key]["negated"] != term["negated"]:
            found.append(
                f"'{term['text']}' and '{seen[key]['text']}' cancel each other, "
                "so nothing can match"
            )
        seen.setdefault(key, term)
    return found


def _untouched_tags(tasks, terms):
    """Tags on the board, for when a tag term selected nothing.

    A query for #design that returns nothing is usually a spelling, and naming
    the tags the board does use answers the question the reader is actually
    asking.
    """
    counts = {}
    for task in tasks:
        for tag in tags_in(task.get("title") or ""):
            counts[tag.lower()] = counts.get(tag.lower(), 0) + 1

    wanted = {
        term["value"] for term in terms if term["kind"] == TAG_FIELD and not term["negated"]
    }
    missing = [tag for tag in wanted if tag not in counts]
    if not missing:
        return []

    known = sorted(counts, key=lambda tag: (-counts[tag], tag))
    shown = known[:TAG_SUGGESTIONS]
    if not shown:
        return [f"#{missing[0]} is not on the board, and no task carries a tag at all"]
    note = f"#{missing[0]} is not on the board. Tags in use: " + ", ".join(
        f"#{tag}" for tag in shown
    )
    if len(known) > len(shown):
        note = f"{note} (+{len(known) - len(shown)} more)"
    return [note]


def run_query(tasks, text, limit=DEFAULT_LIMIT, now=None):
    """Filter the board with a query string.

    Raises QueryError when the query cannot be read, which is a complaint about
    the query rather than about the board.
    """
    terms = parse(text)
    limit = max(1, min(int(limit), MAX_LIMIT))
    tasks = list(tasks or [])

    notes = []
    positives = [term for term in terms if not term["negated"]]
    negatives = [term for term in terms if term["negated"]]

    if not terms:
        notes.append("the query held no terms, so every task on the board passed")

    notes.extend(_contradictions(terms))

    matched = []
    undated = 0

    for task in tasks:
        keep = True
        reasons = []

        for term in positives:
            if term["kind"] in AGE_FIELDS:
                outcome = _age_matches(task, term, now)
                if outcome is None:
                    undated += 1
                    keep = False
                    break
                if not outcome:
                    keep = False
                    break
                # Every term that let the task through is listed, so a result says
                # which part of the query it satisfied rather than just "matched".
                reasons.append(_explain(task, term))
            elif not _matches(task, term):
                keep = False
                break
            else:
                reasons.append(_explain(task, term))

        if not keep:
            continue

        excluded = None
        for term in negatives:
            if term["kind"] in AGE_FIELDS:
                outcome = _age_matches(task, term, now)
                if outcome is None:
                    # An undated task cannot be shown to be younger or older than
                    # anything, so a term excluding "older than 30 days" has no
                    # basis to drop it. Excluding on an unknown would hide a task
                    # for a reason the board does not state.
                    continue
                if outcome:
                    excluded = term
                    break
            elif _matches(task, term):
                excluded = term
                break

        if excluded is not None:
            continue

        matched.append(
            {
                "id": task.get("id"),
                "title": task.get("title", ""),
                "status": task.get("status"),
                "priority": task.get("priority"),
                "open": is_open(task),
                "age_days": age_days(task.get("created_at"), now),
                "reasons": reasons,
            }
        )

    # Store order is kept. This is a filter: an order would imply the first task
    # matters more than the last, and nothing here weighed them.
    shown = matched[:limit]
    truncated = len(matched) > len(shown)

    if truncated:
        notes.append(
            f"showing the first {len(shown)} of {len(matched)} matches; the rest are on the board"
        )
    if undated:
        # Worth its own note: the query asked for old tasks (or new ones), and
        # these were turned away for want of a date rather than for want of age.
        # An empty result would otherwise be credited to the age term.
        notes.append(
            f"{undated} task{'s' if undated != 1 else ''} had no created date to measure, "
            "so the age term could not judge them and they are not shown"
        )
    notes.extend(_untouched_tags(tasks, terms))

    if not terms and len(shown) < len(tasks):
        notes.append("an empty query is not a filter: the limit is what cut this list")

    return {
        "query": text or "",
        "terms": terms,
        "results": shown,
        "matched": len(matched),
        "scanned": len(tasks),
        "truncated": truncated,
        "limit": limit,
        "notes": notes,
        "counts": {
            "open": sum(1 for row in shown if row["open"]),
            "closed": sum(1 for row in shown if not row["open"]),
        },
        "statuses": list(STATUSES) + [OPEN_ALIAS],
    }
