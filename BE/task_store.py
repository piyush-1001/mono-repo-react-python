"""Read the task list from the Node.js store, from the server side.

Every ranking endpoint so far makes the caller post the tasks it wants ranked,
which suits a browser that already holds the list. It suits the mobile client
less: there it means fetching every task over the network and posting the whole
list straight back, and a client that only wants "what should I do next" pays
for both hops and for sending data the server could have read itself.

Standard library only, matching the rest of BE - urllib rather than requests, so
this adds no dependency to pyproject.toml.
"""

import json
import os
import urllib.error
import urllib.request

# Overridable by environment rather than by request: a caller choosing which
# store the server talks to would let a request read an arbitrary URL from this
# one (the same shape as a server-side request forgery), which is not a knob the
# ranking feature needs.
DEFAULT_BASE_URL = os.environ.get("TASKS_API_URL", "http://localhost:3000")
TASKS_PATH = "/api/tasks"

# Generous for a local store, short enough that a Node process that is stopped
# rather than refused shows up as a failed request instead of a hung worker.
REQUEST_TIMEOUT_SECONDS = 5.0


class TaskStoreError(Exception):
    """The task list could not be read: refused, timed out, or unparseable.

    Carries status_code when the store answered at all, so a caller can tell
    "nothing is listening" from "listening, but unhappy".
    """

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def normalise_task(raw):
    """Map the store's field spelling onto the ranker's.

    The Node store writes `createdAt`; score_task reads `created_at`. Passing the
    store's dict through unchanged does not fail - `created_at` simply reads as
    absent, the age weight drops to 0, and every task loses its staleness signal
    while the ranking still looks plausible. That is the worst kind of breakage
    here: no error, just a quietly wrong order.
    """
    return {
        "id": raw.get("id"),
        "title": raw.get("title", ""),
        "status": raw.get("status", "pending"),
        "priority": raw.get("priority", "medium"),
        # Accept either spelling so this keeps working if the store is ever
        # renamed on its side.
        "created_at": raw.get("createdAt") or raw.get("created_at"),
    }


def fetch_tasks(base_url=DEFAULT_BASE_URL, timeout=REQUEST_TIMEOUT_SECONDS):
    """Return the stored tasks as ranker-ready dicts.

    Raises TaskStoreError rather than returning an empty list when the store
    cannot be read: an empty list is also what "no tasks yet" looks like, and a
    caller that ranks the two identically reports "nothing to do" exactly when it
    means "I could not tell".
    """
    url = base_url.rstrip("/") + TASKS_PATH
    request = urllib.request.Request(url, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        # Subclass of URLError, so it must be caught first or a 500 from the
        # store would be reported as an unreachable host.
        raise TaskStoreError(
            f"{url} answered {error.code}", status_code=error.code
        ) from error
    except urllib.error.URLError as error:
        raise TaskStoreError(f"Cannot reach {url}: {error.reason}") from error
    except TimeoutError as error:
        # Only reachable on a store that accepts the connection and then stalls;
        # urlopen's own timeout surfaces here rather than as URLError.
        raise TaskStoreError(f"{url} did not answer within {timeout}s") from error

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as error:
        # Usually the store being replaced by a proxy or an HTML error page.
        raise TaskStoreError(f"{url} did not return JSON") from error

    # The store wraps the list as {"tasks": [...], "count": n}; a bare list is
    # tolerated so a change in that envelope does not read as an empty store.
    tasks = payload.get("tasks") if isinstance(payload, dict) else payload
    if not isinstance(tasks, list):
        raise TaskStoreError(f"{url} returned no task list")

    # Non-dict entries are skipped rather than failing the whole read: one
    # malformed row should not hide every other task.
    return [normalise_task(task) for task in tasks if isinstance(task, dict)]
