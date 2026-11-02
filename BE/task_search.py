"""Search the stored board by what a task says, not by what it is filed under.

The Node.js store already filters by status and priority, and the ranker in
task_ranker.py can order the whole board, but neither answers "which of my tasks
are about tests" - a question about the words in a title. This module scores each
task against a query and says why it matched, in the same shape the ranker uses
so a screen can render both the same way.

Two signals are combined because they fail differently:

  * token overlap is literal. It reports that two of the three words typed
    appear in the title, and it works for words nothing else in the system has
    ever seen.
  * TF-IDF cosine similarity is relative. It discounts a word that appears in
    every title and rewards a rare one, which is why "api" gets past the word
    "build" being common. Fitting it to the board being searched, rather than to
    ml_models' training corpus, is deliberate: idf only means something with
    respect to the documents actually on screen.

Neither is enough alone. Overlap cannot rank two titles that contain the same
words, and cosine on its own reports a confident-looking weak match for a query
whose words appear nowhere.
"""

from ml_models import TfidfVectorizer, cosine_similarity, tokenize
from task_fields import PRIORITIES, STATUSES

# Below this a "match" is noise: one incidental word shared with a three-word
# query. A threshold is needed because cosine never returns exactly zero once two
# texts share a stop-word-ish common noun, so an unfiltered search lists the
# whole board and stops being a search.
MIN_SCORE = 0.05

# Weights on the two signals. They sum to 1 so the combined score stays on the
# same 0..1 scale as a literal title match, which lets a whole-query match sit at
# the top without a special case in the sort.
OVERLAP_WEIGHT = 0.5
SIMILARITY_WEIGHT = 0.5

# A query that names a task's own priority is worth a real score even though the
# word is not in the title, but not a top place: the user more likely meant the
# title. Below 1.0 on purpose.
VOCABULARY_MATCH_SCORE = 0.6

MAX_LIMIT = 100


def _title(task):
    """The text a task is searched over.

    Only the title exists: the Node.js store has no description field, so
    searching more than this would mean inventing a field and then reporting
    every task as a poor match against it.
    """
    value = task.get("title")
    return value if isinstance(value, str) else ""


def _clean_filter(raw, known, label, notes):
    """A filter value, or an empty string meaning "no filter".

    task_fields.normalise_status and normalise_priority are deliberately not
    used here: they replace an unknown value with the default, which for a filter
    would quietly narrow the search to pending or medium tasks nobody asked for.
    A filter that is not understood is dropped and reported instead.
    """
    value = (raw or "").strip().lower()
    if not value:
        return ""
    if value in known:
        return value
    notes.append(
        f"{label} filter '{raw}' is not one of {', '.join(known)}; the filter was ignored"
    )
    return ""


def _coverage(query_tokens, document_tokens):
    """How much of the query the title contains, as a fraction."""
    if not query_tokens:
        return 0.0
    hits = len(query_tokens & document_tokens)
    return hits / len(query_tokens)


def _matched_word(query_tokens, task):
    """A status or priority the query names outright, or None.

    "high" and "done" are words people type meaning the column rather than the
    title, and a search that ignored them would return nothing for the queries
    most likely to be typed at a task board.
    """
    for value in (task.get("priority"), task.get("status")):
        if not isinstance(value, str):
            continue
        # Every word of the value has to be in the query. Matching on any one of
        # them would report "in-progress" for the query "in", and matching only on
        # the value as a whole would miss "in progress", which is how people type
        # it when a hyphen is not on the tip of their fingers.
        value_tokens = set(tokenize(value))
        if value_tokens and value_tokens <= query_tokens:
            return value.lower()
    return None


def score_task(task, query_text, query_tokens, query_vector, vectorizer):
    """One task's match against the query: a score and the reasons for it."""
    title = _title(task)
    document_tokens = set(tokenize(title))
    haystack = title.strip().lower()

    # The whole query sitting inside the title is the strongest possible answer,
    # and it is treated separately from the weighted blend because a blend of two
    # partial signals should not out-rank an exact phrase. Checked against the
    # query as typed rather than against its tokens: tokenising loses the order
    # the words were typed in, which is all a phrase is made of.
    phrase = 1.0 if query_text and query_text in haystack else 0.0

    overlap = _coverage(query_tokens, document_tokens)
    similarity = (
        cosine_similarity(query_vector, vectorizer.vector(title))
        if query_vector
        else 0.0
    )

    blended = overlap * OVERLAP_WEIGHT + similarity * SIMILARITY_WEIGHT
    vocabulary = _matched_word(query_tokens, task)

    reasons = []
    if phrase:
        reasons.append("title contains the whole query")
    if overlap:
        words = len(query_tokens)
        hits = round(overlap * words)
        if words == 1:
            reasons.append("the word matches")
        else:
            reasons.append(f"{hits} of {words} words match")
    if similarity:
        reasons.append(f"similar wording ({similarity:.2f})")
    if vocabulary:
        reasons.append(f"the query names this task's '{vocabulary}'")

    score = max(phrase, blended, VOCABULARY_MATCH_SCORE if vocabulary else 0.0)
    return score, reasons


def search(tasks, query="", status=None, priority=None, limit=20):
    """Score every task against a query, after the status/priority filters.

    Returns the matches plus how much of the board they came from, so a caller
    can tell "three tasks matched" from "three tasks matched out of four, and the
    status filter you asked for was thrown away".
    """
    notes = []
    wanted_status = _clean_filter(status, STATUSES, "status", notes)
    wanted_priority = _clean_filter(priority, PRIORITIES, "priority", notes)

    candidates = [
        task
        for task in tasks
        if (not wanted_status or task.get("status") == wanted_status)
        and (not wanted_priority or task.get("priority") == wanted_priority)
    ]

    filtered_out = len(tasks) - len(candidates)
    if filtered_out and (wanted_status or wanted_priority):
        notes.append(
            f"{filtered_out} task{'' if filtered_out == 1 else 's'} excluded by the filters"
        )

    if not candidates:
        return {
            "query": (query or "").strip(),
            "results": [],
            "matched": 0,
            "scanned": 0,
            "board": len(tasks),
            "filters": {"status": wanted_status or None, "priority": wanted_priority or None},
            "notes": notes,
        }

    query_text = (query or "").strip().lower()
    # A set, so a word typed twice counts once: repeating yourself in a search box
    # is emphasis, not a second term to weight.
    query_tokens = set(tokenize(query or ""))

    # Fitted to the titles actually being searched, so a word in every title
    # weighs nothing. The query itself is not part of the corpus: it is what the
    # documents are compared against, not one of the things being ranked.
    vectorizer = TfidfVectorizer([_title(task) for task in candidates])
    # The join order is the set's, not the user's, which does not matter here:
    # a vector counts words, and the order-sensitive check is the phrase test in
    # score_task, which gets the query as typed.
    query_vector = vectorizer.vector(" ".join(query_tokens)) if query_tokens else {}

    if not query_tokens:
        # Filters only. Everything left after them is listed unsorted and scored
        # zero, because a score with no query to compare against would be a
        # number attached to nothing.
        results = [
            {
                "id": task.get("id"),
                "title": _title(task),
                "status": task.get("status"),
                "priority": task.get("priority"),
                "score": 0.0,
                "reasons": ["matches the filters"],
            }
            for task in candidates
        ]
        notes.append("no query: every task matching the filters is listed, unranked")
    else:
        scored = []
        for position, task in enumerate(candidates):
            score, reasons = score_task(
                task, query_text, query_tokens, query_vector, vectorizer
            )
            if score < MIN_SCORE:
                continue
            scored.append((score, position, task, reasons))

        # position as the tie-break keeps the store's own order among tasks that
        # score the same, so the list does not shuffle between two identical
        # searches.
        scored.sort(key=lambda item: (-item[0], item[1]))

        results = [
            {
                "id": task.get("id"),
                "title": _title(task),
                "status": task.get("status"),
                "priority": task.get("priority"),
                "score": round(score * 100, 1),
                "reasons": reasons,
            }
            for score, _position, task, reasons in scored
        ]

    limit = max(1, min(int(limit or 20), MAX_LIMIT))
    if len(results) > limit:
        notes.append(f"showing the first {limit} of {len(results)} matches")
        results = results[:limit]

    return {
        "query": (query or "").strip(),
        "results": results,
        "matched": len(results),
        "scanned": len(candidates),
        "board": len(tasks),
        "filters": {"status": wanted_status or None, "priority": wanted_priority or None},
        "notes": notes,
    }
