"""Heuristic task ranking for the Task Manager.

Given the tasks stored by the Node.js API, this module decides what to work on
next. It combines a small set of weighted signals into one score per task and
flags titles that look like duplicates of each other (reusing the TF-IDF
vectorizer from ml_models.py).

Scoring is intentionally transparent: every task comes back with the list of
reasons that produced its score, so the frontend can explain the ranking
instead of showing an opaque number.
"""

import math
from datetime import datetime, timezone

from ml_models import tokenize, vectorizer, cosine_similarity

PRIORITY_WEIGHTS = {"high": 3.0, "medium": 2.0, "low": 1.0}
STATUS_WEIGHTS = {"in-progress": 1.5, "pending": 1.0, "done": 0.0}

# Words that people use when a task is actually pressing.
URGENCY_WORDS = {
    "urgent", "asap", "now", "today", "tonight", "immediately",
    "deadline", "due", "overdue", "critical", "blocking", "hotfix",
}

AGE_HALF_LIFE_DAYS = 7.0  # a task ~1 week old has most of its staleness weight
MAX_PRIORITY_SIGNAL = 4.5  # PRIORITY_WEIGHTS["high"] * STATUS_WEIGHTS["in-progress"]


def _age_weight(created_at: str | None, now: datetime):
    """Saturating staleness weight in [0, 1); older tasks approach 1."""
    if not created_at:
        return 0.0
    try:
        stamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)

    days = max((now - stamp).total_seconds() / 86400, 0.0)
    return 1.0 - math.exp(-math.log(2) * days / AGE_HALF_LIFE_DAYS)


def _urgency_terms(title: str):
    return [word for word in tokenize(title) if word in URGENCY_WORDS]


def score_task(task: dict, now: datetime):
    """Return the score and the reasons behind it for a single task."""
    priority = task.get("priority", "medium")
    status = task.get("status", "pending")

    priority_weight = PRIORITY_WEIGHTS.get(priority, PRIORITY_WEIGHTS["medium"])
    status_weight = STATUS_WEIGHTS.get(status, STATUS_WEIGHTS["pending"])
    age_weight = _age_weight(task.get("created_at"), now)
    urgency = _urgency_terms(task.get("title", ""))

    if status == "done":
        return {"score": 0.0, "reasons": ["already done"]}

    reasons = [f"{priority} priority", f"status is {status}"]
    raw = priority_weight * status_weight

    if age_weight > 0.25:
        raw += 2.0 * age_weight
        age_days = round(-math.log(1 - age_weight) * AGE_HALF_LIFE_DAYS / math.log(2))
        reasons.append(f"waiting ~{age_days} days")

    if urgency:
        raw += 1.5
        reasons.append(f"urgent wording: {', '.join(sorted(set(urgency)))}")

    score = round(min(raw / MAX_PRIORITY_SIGNAL, 1.0) * 100, 1)
    return {"score": score, "reasons": reasons}


def find_duplicate_titles(tasks, threshold=0.6):
    """Pairs of task indexes whose titles are near-identical."""
    vectors = [vectorizer.vector(task.get("title", "")) for task in tasks]
    duplicates = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            sim = cosine_similarity(vectors[i], vectors[j])
            if sim >= threshold:
                duplicates.append(
                    {
                        "first": tasks[i]["id"],
                        "second": tasks[j]["id"],
                        "similarity": round(sim * 100, 1),
                    }
                )
    return duplicates


def rank_tasks(tasks):
    """Score every task, order them by score, and report likely duplicates."""
    now = datetime.now(timezone.utc)

    scored = []
    for task in tasks:
        scored.append({**task, **score_task(task, now)})
    scored.sort(key=lambda task: task["score"], reverse=True)

    open_tasks = [task for task in scored if task["status"] != "done"]
    return {
        "ranked": scored,
        "next_task_id": open_tasks[0]["id"] if open_tasks else None,
        "open_count": len(open_tasks),
        "duplicates": find_duplicate_titles(tasks),
    }
