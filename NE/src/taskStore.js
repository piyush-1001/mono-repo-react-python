// The in-memory task store behind the Node.js API.
//
// This used to be two variables and a set of `tasks.filter(...)` calls inside
// server.js, which made the data layer and the HTTP layer the same thing: every
// route reached into the array directly, so a second consumer of the board
// meant a second copy of the same mutations. This module owns the data and the
// rules about it; server.js only routes.
//
// Nothing is persisted. Restarting the server empties the board back to the
// seed below, which is what it has always done.

export const STATUSES = ['pending', 'in-progress', 'done'];
export const PRIORITIES = ['high', 'medium', 'low'];

// A task with a status or priority outside those lists is accepted today and
// misread later: the Python ranker weighs priority as {high: 3, medium: 2,
// low: 1} and falls back to medium for anything it does not recognise, so a
// typo'd "High" scores as medium and the task is never promoted. Rejecting it
// here is the only place the vocabulary is enforced for every consumer -
// the React app, the Python API, and the phone.
export class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}

const seed = () => {
  const now = new Date().toISOString();
  return [
    { id: 1, title: 'Learn React', status: 'done', priority: 'high', createdAt: now },
    { id: 2, title: 'Build Node.js API', status: 'in-progress', priority: 'high', createdAt: now },
    { id: 3, title: 'Write unit tests', status: 'pending', priority: 'medium', createdAt: now },
  ];
};

let tasks = seed();
let nextId = 4;

const cleanTitle = (value) => (typeof value === 'string' ? value.trim() : '');

export function listTasks({ status, priority } = {}) {
  let result = tasks;
  if (status) result = result.filter((t) => t.status === status);
  if (priority) result = result.filter((t) => t.priority === priority);
  return result;
}

export function findTask(id) {
  return tasks.find((t) => t.id === id) || null;
}

export function createTask({ title, priority = 'medium' } = {}) {
  const trimmed = cleanTitle(title);
  if (!trimmed) throw new ValidationError('title is required', 'title');
  if (!PRIORITIES.includes(priority)) {
    throw new ValidationError(
      `priority must be one of: ${PRIORITIES.join(', ')}`,
      'priority',
    );
  }

  const task = {
    id: nextId++,
    title: trimmed,
    status: 'pending',
    priority,
    createdAt: new Date().toISOString(),
  };
  tasks.push(task);
  return task;
}

export function updateTask(id, { title, status, priority } = {}) {
  // Looked up before anything is written, so a request for a task that does not
  // exist cannot half-apply an update.
  const task = findTask(id);
  if (!task) return null;

  if (title !== undefined) {
    const trimmed = cleanTitle(title);
    if (!trimmed) throw new ValidationError('title cannot be empty', 'title');
    task.title = trimmed;
  }
  if (status !== undefined) {
    if (!STATUSES.includes(status)) {
      throw new ValidationError(`status must be one of: ${STATUSES.join(', ')}`, 'status');
    }
    task.status = status;
  }
  if (priority !== undefined) {
    if (!PRIORITIES.includes(priority)) {
      throw new ValidationError(
        `priority must be one of: ${PRIORITIES.join(', ')}`,
        'priority',
      );
    }
    task.priority = priority;
  }
  return task;
}

export function removeTask(id) {
  const index = tasks.findIndex((t) => t.id === id);
  if (index === -1) return false;
  tasks.splice(index, 1);
  return true;
}

// Counts for the dashboard. The keys are snake_case to match the Python API's
// vocabulary (next_task_id, open_count), so a page can render a response from
// either backend without translating keys in between.
export function stats() {
  const byStatus = Object.fromEntries(STATUSES.map((status) => [status, 0]));
  const byPriority = Object.fromEntries(PRIORITIES.map((priority) => [priority, 0]));

  for (const task of tasks) {
    if (byStatus[task.status] !== undefined) byStatus[task.status] += 1;
    if (byPriority[task.priority] !== undefined) byPriority[task.priority] += 1;
  }

  const open = tasks.filter((t) => t.status !== 'done');
  // ISO timestamps sort lexicographically, so the oldest is the smallest string.
  const oldest = open.reduce(
    (acc, task) => (!acc || task.createdAt < acc.createdAt ? task : acc),
    null,
  );

  return {
    total: tasks.length,
    open: open.length,
    done: tasks.length - open.length,
    by_status: byStatus,
    by_priority: byPriority,
    oldest_open_task: oldest
      ? { id: oldest.id, title: oldest.title, createdAt: oldest.createdAt }
      : null,
  };
}
