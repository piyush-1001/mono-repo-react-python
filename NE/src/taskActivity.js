// A journal of what changed on the board.
//
// stats() says what the board looks like right now. Nothing in the store says
// what happened to get here: updateTask writes over the row in place, so a task
// that moved from pending to in-progress on Monday and to done on Wednesday
// carries only its creation date, and removeTask splices the row out so the
// title itself is gone. A client that missed a response cannot ask what it
// missed, and nobody can say when a task was closed - only that it is.
//
// So the mutation routes report every change here, and this module keeps a
// bounded list of them: enough to answer "what is the recent activity", "what
// has happened to task 7", and "what moved since revision 42, which is as far as
// I had read".
//
// Two things this has to get right, and the rest is detail.
//
// One: an entry stores a copy of the row, never the row. updateTask mutates the
// object in place, so a journal holding the live row would show every past entry
// as the task's current state - the journal would report the same answer for
// every week of its history and look healthy doing it. A shallow copy is enough
// because every field is a string or a number.
//
// Two: like the store, the journal is not persisted. Restarting the server
// empties both, and a revision number from before the restart is a number that
// no longer refers to anything. changesSince() reports that as `reset: true`
// rather than answering with an empty list, because "nothing changed" and "I
// have no record of what you are asking about" are different answers and a
// client that hears the first one will keep believing a board it can no longer
// trust.

import { ValidationError } from './taskStore.js';

// What the journal keeps. Like the store's seed, this dies with the process; the
// number is a ceiling on memory, not a claim about how far back anyone can look.
export const MAX_ENTRIES = 200;

// How many entries a feed returns when the caller did not ask for a number.
export const DEFAULT_FEED_LIMIT = 20;

export const CHANGE_KINDS = ['created', 'updated', 'deleted'];

let entries = [];
let revision = 0;
let dropped = 0;

const copy = (task) => (task ? { ...task } : null);

/**
 * Appends one change.
 *
 * `task` is the row as it stands after the change, or null when the task no
 * longer exists (a deletion). `before` is the row as it stood before, or null
 * for a creation. Both are read for their fields and copied, so whatever the
 * caller's object turns into afterwards, this entry keeps what it saw.
 *
 * Returns the entry, which carries the revision number the caller can hand back
 * later as a cursor.
 */
export function recordChange(kind, task, before = null) {
  if (!CHANGE_KINDS.includes(kind)) {
    throw new ValidationError(`kind must be one of: ${CHANGE_KINDS.join(', ')}`, 'kind');
  }

  const source = task || before;
  if (!source) {
    // An entry with no id is a record in the journal that no task can ever be
    // found again: better to fail the caller that forgot a snapshot than to file
    // something unanswerable.
    throw new ValidationError('a change needs the task it changed', 'task');
  }

  revision += 1;
  const entry = {
    rev: revision,
    at: new Date().toISOString(),
    kind,
    task_id: source.id,
    task: copy(task),
    before: copy(before),
  };

  entries.push(entry);
  if (entries.length > MAX_ENTRIES) {
    entries.shift();
    dropped += 1;
  }

  return entry;
}

/**
 * The recent entries, newest first - a feed.
 *
 * Filters are read here rather than in the route so that a `task` or `kind` the
 * module cannot match is reported in `notes` instead of quietly returning
 * nothing: an empty feed that also says "3 entries, none of them for task 9" is
 * an answer, and an empty feed on its own is not.
 */
export function recentChanges({ task = null, kind = null, limit = DEFAULT_FEED_LIMIT } = {}) {
  const notes = [];
  let rows = entries;

  if (kind) {
    if (!CHANGE_KINDS.includes(kind)) {
      throw new ValidationError(`kind must be one of: ${CHANGE_KINDS.join(', ')}`, 'kind');
    }
    rows = rows.filter((entry) => entry.kind === kind);
  }

  if (task !== null) {
    // Compared as strings, because a query parameter arrives as "7" and the
    // journal holds 7. The difference is only ever the caller's transport, and
    // answering 404-free with the right rows is worth one String() call.
    const wanted = String(task);
    rows = rows.filter((entry) => String(entry.task_id) === wanted);
  }

  const matched = rows.length;
  const capped = limit === null ? matched : Math.min(limit, matched);
  // Walked back from the end: the newest entries are the ones a feed shows, and
  // they are also the ones most likely to have been pushed out of the list.
  const shown = rows.slice(matched - capped);
  shown.reverse();

  if (matched > capped) {
    notes.push(`showing the newest ${capped} of ${matched} matching entries`);
  }

  return {
    entries: shown,
    matched,
    kept: entries.length,
    dropped,
    revision,
    oldest_rev: entries.length ? entries[0].rev : null,
    notes,
  };
}

/**
 * Everything the journal still holds after a revision the caller already has,
 * oldest first, so a client can walk forward from its own cursor instead of
 * refetching the board.
 *
 * The cursor is a revision number, not a timestamp. Two changes in the same
 * millisecond have equal timestamps and different revisions, and a client that
 * polls on a timer is exactly the client that hits that.
 */
export function changesSince(since) {
  const oldest = entries.length ? entries[0].rev : null;

  let reset = false;
  const notes = [];

  if (since > revision) {
    // The caller is ahead of the journal, which cannot happen within one run:
    // revisions only go up. The server restarted, the counter started again, and
    // the number in the query is a leftover.
    reset = true;
    notes.push('this server has not reached that revision, so its counter was reset');
  } else if (dropped > 0 && oldest !== null && since < oldest - 1) {
    // The cursor points below the oldest entry still here, and entries have been
    // dropped before, so some of what happened between then and now is gone from
    // the journal for good.
    reset = true;
    notes.push(`the journal no longer holds changes before revision ${oldest}`);
  }

  const changes = entries.filter((entry) => entry.rev > since);

  if (reset) {
    notes.push('the list below is only what this journal still has: refetch the board');
  }

  return {
    since,
    revision,
    reset,
    changes,
    dropped,
    oldest_rev: oldest,
    notes,
  };
}
