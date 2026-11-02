// Reading a task query string, and refusing to guess what an unreadable one meant.
//
// The write path is strict. createTask and updateTask reject a status or a
// priority that is not on their list, because a stored typo is misread by
// everything that reads it afterwards: the Python ranker weighs a priority it
// does not recognise as medium, so a task saved as "High" is a task that is
// never promoted.
//
// The read path was the loose one. `GET /api/tasks?status=Done` matches no row,
// answers 200 with an empty list, and the client cannot tell "there are no done
// tasks" from "done is not spelled that way". The second is a bug in the caller
// that arrives looking like news about the board, which is the worse of the two
// ways to be wrong. Unknown values are rejected here for the same reason they
// are rejected on write, with one difference: a read stores nothing, so a value
// that is merely miscased is accepted and folded to the store's spelling rather
// than thrown back.
//
// This module parses, validates, and applies. It never touches the store - the
// caller hands over the rows it already has, so the same filtering applies to a
// live board, a fixture, or a cached response.

import { CHANGE_KINDS } from './taskActivity.js';
import { PRIORITIES, STATUSES, ValidationError } from './taskStore.js';

// The most any one response will carry. A caller who asks for more gets what it
// asked for cut short, with a note saying so: a request for the whole board is
// better answered by paging than by a response that grows without limit.
export const MAX_LIMIT = 200;

// The fields a caller may sort by, and the directions it may sort them in.
export const SORT_KEYS = ['id', 'created', 'title', 'priority'];
export const ORDERS = ['asc', 'desc'];

// A task is open when it is not done, which is the same rule stats() counts
// with. It is written here rather than imported because taskStore does not
// export it, and a list of statuses cannot express "anything but this one".
const isOpenTask = (task) => task.status !== 'done';

const TRUTHY = ['true', '1', 'yes'];
const FALSY = ['false', '0', 'no'];

const compareStrings = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

// Lowest first, so `sort=priority` puts the urgent ones at the top without the
// caller having to ask for desc. Anything off the list ranks last rather than
// throwing the sort open: the store refuses those values on write, but a row
// that predates the check should sink, not break the ordering for everyone.
const PRIORITY_RANK = { high: 0, medium: 1, low: 2 };

const UNRANKED_PRIORITY = PRIORITIES.length;

const rankPriority = (task) =>
  PRIORITY_RANK[task.priority] === undefined ? UNRANKED_PRIORITY : PRIORITY_RANK[task.priority];

// Every comparator ends on the id, so a sort is a total order. Two tasks
// created in the same millisecond have equal timestamps, and a comparator that
// stops there returns them in whatever order the engine happened to reach them.
const COMPARATORS = {
  // The store appends, so id order is the order tasks were added.
  id: (a, b) => a.id - b.id,
  created: (a, b) => compareStrings(a.createdAt, b.createdAt) || a.id - b.id,
  title: (a, b) => a.title.localeCompare(b.title) || a.id - b.id,
  priority: (a, b) => rankPriority(a) - rankPriority(b) || a.id - b.id,
};

// A parameter given twice (`?status=pending&status=done`) arrives from Express
// as an array, which String() would flatten into "pending,done" and report as an
// unknown status. It is not unknown, it is contradictory, and the caller gets to
// hear it that way.
const single = (name, raw) => {
  if (Array.isArray(raw)) {
    throw new ValidationError(`${name} was given more than once, and only one value can filter`, name);
  }
  return raw;
};

// Trimmed, lower-cased, and checked against the store's vocabulary. Case is
// folded because `?status=Done` is a caller that means `done`, and a read has no
// way to carry the mistake forward into the data.
function foldValue(name, raw, allowed) {
  const value = String(single(name, raw)).trim().toLowerCase();
  if (!allowed.includes(value)) {
    throw new ValidationError(`${name} must be one of: ${allowed.join(', ')}`, name);
  }
  return value;
}

function foldBoolean(name, raw) {
  const value = String(single(name, raw)).trim().toLowerCase();
  if (TRUTHY.includes(value)) return true;
  if (FALSY.includes(value)) return false;
  throw new ValidationError(`${name} must be true or false`, name);
}

// Absent is null, not zero: `?limit=` and no limit at all mean different things
// to the caller - one is a dropped query parameter, the other a request for
// everything - and the difference has to survive to the notes.
function parseInteger(name, raw, { min = 0 } = {}) {
  if (raw === undefined || raw === '') return null;
  const value = Number(single(name, raw));
  if (!Number.isInteger(value)) {
    throw new ValidationError(`${name} must be a whole number`, name);
  }
  if (value < min) {
    throw new ValidationError(`${name} must be ${min} or more`, name);
  }
  return value;
}

/**
 * Reads the query string of GET /api/tasks. Throws ValidationError, which is how
 * the store reports a bad value too, so the route answers 400 in the same shape
 * whichever layer noticed.
 */
export function parseTaskListQuery(query = {}) {
  const notes = [];

  let status = null;
  if (query.status !== undefined) {
    if (query.status === '') notes.push('status was empty, so it filtered nothing');
    else status = foldValue('status', query.status, STATUSES);
  }

  let priority = null;
  if (query.priority !== undefined) {
    if (query.priority === '') notes.push('priority was empty, so it filtered nothing');
    else priority = foldValue('priority', query.priority, PRIORITIES);
  }

  // `open` is the filter a queue wants and the two value lists do not offer:
  // everything not finished, which is pending and in-progress at once. It is
  // refused alongside an explicit status rather than resolved against it,
  // because the two can disagree and silently picking a winner would make the
  // response describe a filter nobody asked for.
  let open = null;
  if (query.open !== undefined) {
    if (query.open === '') {
      notes.push('open was empty, so it filtered nothing');
    } else {
      open = foldBoolean('open', query.open);
      if (status) {
        throw new ValidationError('give either status or open, not both', 'open');
      }
    }
  }

  let sort = null;
  if (query.sort !== undefined && query.sort !== '') {
    sort = foldValue('sort', query.sort, SORT_KEYS);
  }

  let order = 'asc';
  if (query.order !== undefined && query.order !== '') {
    order = foldValue('order', query.order, ORDERS);
    if (!sort) {
      order = 'asc';
      notes.push('order was ignored because no sort was asked for');
    }
  }

  let limit = parseInteger('limit', query.limit, { min: 1 });
  if (limit !== null && limit > MAX_LIMIT) {
    notes.push(`limit was cut to ${MAX_LIMIT}`);
    limit = MAX_LIMIT;
  }
  const offset = parseInteger('offset', query.offset, { min: 0 }) ?? 0;

  // Named q, the same name the Python search endpoint uses, so a client that
  // knows one knows the other. There is no second spelling to keep straight.
  const search = String(single('q', query.q) ?? '').trim();
  if (query.q === '') notes.push('q was empty, so it filtered nothing');

  return { status, priority, open, search, sort, order, limit, offset, notes };
}

/**
 * Filters, sorts, and pages the rows the caller already has.
 *
 * The response keeps the `count` and `tasks` keys the route has always returned,
 * so an existing client reads it unchanged. The rest is what the empty list no
 * longer has to mean on its own: how many rows matched before paging, how many
 * there were to choose from, and what the filters actually did.
 */
export function applyTaskListQuery(tasks, parsed) {
  const notes = [...parsed.notes];
  let rows = tasks;

  // Done here rather than left to listTasks(): one owner of the filter, so the
  // folding above and the matching cannot drift into disagreeing about what
  // `?status=Done` selects. Callers pass every row.
  if (parsed.status) {
    rows = rows.filter((task) => task.status === parsed.status);
  } else if (parsed.open !== null) {
    rows = rows.filter((task) => isOpenTask(task) === parsed.open);
  }
  if (parsed.priority) {
    rows = rows.filter((task) => task.priority === parsed.priority);
  }

  if (parsed.search) {
    const words = parsed.search.toLowerCase().split(/\s+/).filter(Boolean);
    rows = rows.filter((task) => {
      const haystack = (task.title || '').toLowerCase();
      return words.every((word) => haystack.includes(word));
    });
    notes.push('q keeps the tasks whose title holds every word; it is a test for the words, not a ranking');
  }

  if (parsed.sort) {
    const compare = COMPARATORS[parsed.sort];
    rows = [...rows].sort(parsed.order === 'desc' ? (a, b) => -compare(a, b) : compare);
  }

  const matched = rows.length;
  const from = Math.min(parsed.offset, matched);
  const to = parsed.limit === null ? matched : Math.min(from + parsed.limit, matched);
  const page = rows.slice(from, to);

  if (page.length === 0 && matched > 0) {
    // The one empty list that would otherwise read as "nothing matched": the
    // tasks are there, the page just started past the end of them.
    notes.push(`${matched} task${matched === 1 ? '' : 's'} matched, and the offset skipped past all of them`);
  }

  return {
    count: page.length,
    tasks: page,
    matched,
    scanned: tasks.length,
    filters: {
      status: parsed.status,
      priority: parsed.priority,
      open: parsed.open,
      q: parsed.search || null,
      sort: parsed.sort,
      order: parsed.sort ? parsed.order : null,
      limit: parsed.limit,
      offset: parsed.offset,
    },
    notes,
  };
}

/**
 * Reads the query string of the two activity routes. Both take the same
 * parameters and each needs a different subset, so this one parses and the route
 * decides whether it can do without what is missing.
 */
export function parseActivityQuery(query = {}) {
  const notes = [];

  const since = parseInteger('since', query.since, { min: 0 });

  let task = null;
  if (query.task !== undefined && query.task !== '') {
    task = parseInteger('task', query.task, { min: 1 });
  }

  let kind = null;
  if (query.kind !== undefined && query.kind !== '') {
    kind = foldValue('kind', query.kind, CHANGE_KINDS);
  }

  let limit = parseInteger('limit', query.limit, { min: 1 });
  if (limit !== null && limit > MAX_LIMIT) {
    notes.push(`limit was cut to ${MAX_LIMIT}`);
    limit = MAX_LIMIT;
  }

  return { since, task, kind, limit, notes };
}
