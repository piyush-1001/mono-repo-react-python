"""Group the tasks that say the same thing, and say which one to keep.

task_ranker.py already reports pairs whose titles look alike. A pair is a hint,
not a decision: three tasks that all match each other are one group of
duplicates rather than three pairs, and the question that is actually worth
answering is "which of these do I keep and which do I close".

So this module clusters the pairs, adds the exact-title duplicates the vector
comparison can miss, and for each cluster names the one to keep:

  * If one of them is already done, that one is the keeper. The others are
    leftovers of work that has already happened, and the useful action is to
    close them.
  * Otherwise the oldest task is the keeper. It carries the age of the work, and
    closing the newer copy instead would throw away the history - the age
    signal the ranker scores with.

Nothing here closes anything. The board is the Node.js store's, and this module
only reads it and reports; a report that quietly merged tasks would be a report
that made decisions nobody asked for.
"""

import re

from task_fields import age_days, is_open
from task_ranker import find_duplicate_titles, rank_tasks

# The same threshold the ranker uses for its duplicate pairs. Loosening it here
# would make this report disagree with the count the insights page shows.
DEFAULT_THRESHOLD = 0.6

# How many tasks of one cluster are listed. A cluster of forty identical tasks
# is a real thing on a real board and still does not need forty lines.
MAX_CLUSTER_TASKS = 8

PUNCTUATION = re.compile(r"[^\w\s]")


def _folded_title(title):
    """A title reduced to what makes two of them the same task.

    Case, punctuation and spacing go, because "Fix login!" and "fix login" are
    the same task written twice. Everything else stays: "Fix bug 2" and "Fix bug
    3" are different tasks, and folding the numbers together would merge them.
    """
    text = PUNCTUATION.sub(" ", (title or "").lower())
    return " ".join(text.split())


class _Groups:
    """Union-find over task ids, so a chain of matches is one group."""

    def __init__(self):
        self.parent = {}

    def add(self, key):
        if key not in self.parent:
            self.parent[key] = key

    def find(self, key):
        self.add(key)
        root = key
        while self.parent[root] != root:
            root = self.parent[root]
        # Path compression: everyone who pointed at the root now points at it.
        while self.parent[key] != root:
            self.parent[key], key = root, self.parent[key]
        return root

    def union(self, first, second):
        root_a = self.find(first)
        root_b = self.find(second)
        if root_a != root_b:
            # The lower id wins the root, so the grouping does not depend on the
            # order the pairs happened to arrive in.
            if str(root_b) < str(root_a):
                root_a, root_b = root_b, root_a
            self.parent[root_b] = root_a

    def clusters(self):
        """The groups with more than one member, keyed by their root."""
        grouped = {}
        for key in self.parent:
            grouped.setdefault(self.find(key), []).append(key)
        return {
            root: members for root, members in grouped.items() if len(members) > 1
        }


def _entry(task, now):
    """The fields a clustered task carries into the response."""
    return {
        "id": task.get("id"),
        "title": task.get("title", ""),
        "status": task.get("status"),
        "priority": task.get("priority"),
        "score": task.get("score", 0.0),
        "age_days": age_days(task.get("created_at"), now),
    }


def _keeper(tasks):
    """The task to keep in a cluster, and why.

    A done task wins: the work it describes has happened, so the open copies of
    it are leftovers. With no done task in the cluster, the oldest wins, because
    it is the one carrying the age of the work.
    """
    done = [task for task in tasks if not is_open(task)]
    if done:
        # The one created longest ago among the finished ones: it is the copy
        # that has been on the board the longest, and the other finished copies
        # are the newer restatements of the same work.
        oldest_done = min(
            done,
            key=lambda task: (task.get("age_days") is None, task.get("age_days") or 0),
        )
        return oldest_done, (
            f"#{oldest_done.get('id')} is already done, so the other "
            f"{len(tasks) - 1} look like leftovers of finished work"
        )

    oldest = min(
        tasks,
        key=lambda task: (task.get("age_days") is None, task.get("age_days") or 0),
    )
    return oldest, (
        f"#{oldest.get('id')} is the oldest of them, so it is the one carrying "
        "the history"
    )


def find_duplicates(tasks, threshold=DEFAULT_THRESHOLD, now=None):
    """Cluster the tasks that look like the same task.

    Returns the clusters, each with the task to keep and the reason for that
    choice, plus the notes that say what the report did and did not do.
    """
    notes = []

    groups = _Groups()
    for task in tasks:
        groups.add(task.get("id"))

    pairs = find_duplicate_titles(tasks, threshold=threshold)
    similarity = {}
    for pair in pairs:
        groups.union(pair["first"], pair["second"])
        for key in (pair["first"], pair["second"]):
            similarity[key] = max(similarity.get(key, 0.0), pair["similarity"])

    # Titles that are identical once folded are duplicates whatever the vector
    # comparison made of them - two tasks whose titles differ only in a
    # character the tokenizer drops would otherwise never meet.
    folded = {}
    for task in tasks:
        key = _folded_title(task.get("title"))
        if not key:
            continue
        if key in folded:
            groups.union(folded[key], task.get("id"))
        else:
            folded[key] = task.get("id")

    clusters = groups.clusters()
    if not clusters:
        notes.append("no duplicate-looking tasks found")

    by_id = {task.get("id"): task for task in tasks}
    ranked_rows = {
        task.get("id"): task for task in rank_tasks(tasks)["ranked"]
    }

    reports = []
    for members in clusters.values():
        entries = []
        for task_id in members:
            source = by_id.get(task_id)
            if source is None:
                continue
            entry = _entry(source, now)
            # The score comes from the ranker, so the cluster can be ordered the
            # same way the rest of the app orders tasks.
            entry["score"] = ranked_rows.get(task_id, {}).get("score", 0.0)
            entries.append(entry)

        if len(entries) < 2:
            continue

        # Highest score first, so the task the app would pick is at the top.
        entries.sort(key=lambda entry: (-entry["score"], entry["id"]))

        exact = len({_folded_title(entry["title"]) for entry in entries}) == 1
        keeper, reason = _keeper(entries)
        reports.append(
            {
                "size": len(entries),
                "exact": exact,
                # An exact duplicate is a perfect match even when the vector
                # comparison never paired it with anything: the titles are the
                # same task, so the similarity is the whole of it, not zero.
                "similarity": 100.0
                if exact
                else round(
                    max(
                        (similarity.get(entry["id"], 0.0) for entry in entries),
                        default=0.0,
                    ),
                    1,
                ),
                "keep_id": keeper["id"],
                "reason": reason,
                "tasks": entries[:MAX_CLUSTER_TASKS],
                "truncated": len(entries) > MAX_CLUSTER_TASKS,
            }
        )

    # Biggest clusters first: a group of six is more worth a decision than a
    # group of two.
    reports.sort(key=lambda report: (-report["size"], report["keep_id"]))

    involved = sum(report["size"] for report in reports)
    if reports:
        notes.append(
            f"{involved} of {len(tasks)} tasks are in {len(reports)} "
            "group{'' if len(reports) == 1 else 's'}; nothing was closed"
        )

    return {
        "clusters": reports,
        "cluster_count": len(reports),
        "duplicate_tasks": involved,
        "board": len(tasks),
        "threshold": threshold,
        "notes": notes,
    }
