import express from 'express';
import cors from 'cors';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import {
  listTasks,
  findTask,
  createTask,
  updateTask,
  removeTask,
  stats,
  ValidationError,
} from './taskStore.js';
import { recordChange, recentChanges, changesSince } from './taskActivity.js';
import {
  applyTaskListQuery,
  parseActivityQuery,
  parseTaskListQuery,
} from './taskQuery.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

// Serve React build in production
app.use(express.static(join(__dirname, '../dist')));

// ============================================================
// Data
// ============================================================

// The board itself lives in taskStore.js; this file is only the HTTP layer.

const notFound = (res) => res.status(404).json({ error: 'Not found' });
const badRequest = (res, msg) => res.status(400).json({ error: msg });

// ============================================================
// Routes
// ============================================================

app.get('/', (_req, res) => {
  res.json({
    message: 'Node.js Express API is running',
    version: '1.0',
    endpoints: ['GET /', 'GET /api/health', 'GET /api/tasks', 'GET /api/tasks/stats', 'POST /api/tasks', 'GET /api/tasks/:id', 'PUT /api/tasks/:id', 'DELETE /api/tasks/:id'],
  });
});

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/api/tasks', (req, res) => {
  try {
    // The store is read whole and filtered in taskQuery.js, so the query string
    // is parsed in one place and a value it cannot honour is an error rather
    // than an empty list. listTasks() is given no filters for the same reason:
    // two places folding the same parameters is two places that can disagree.
    res.json(applyTaskListQuery(listTasks(), parseTaskListQuery(req.query)));
  } catch (error) {
    if (error instanceof ValidationError) return badRequest(res, error.message);
    throw error;
  }
});

// Declared before /api/tasks/:id on purpose: Express matches routes in the
// order they were declared, so ":id" would swallow "stats" and answer 404 for
// a path that has its own endpoint. A numeric check inside the id route would
// not help, because the id route is still reached first.
app.get('/api/tasks/stats', (_req, res) => {
  res.json(stats());
});

// The two routes taskActivity.js answers, declared before /api/tasks/:id for the
// same reason stats is: Express matches in declaration order, so ":id" would
// take "activity" for an id and answer 404 about a route that exists.
app.get('/api/tasks/activity', (req, res) => {
  try {
    const { task, kind, limit } = parseActivityQuery(req.query);
    res.json(recentChanges({ task, kind, limit }));
  } catch (error) {
    if (error instanceof ValidationError) return badRequest(res, error.message);
    throw error;
  }
});

app.get('/api/tasks/changes', (req, res) => {
  try {
    const { since } = parseActivityQuery(req.query);
    // Required rather than defaulted: "everything, I lost my cursor" and "what
    // moved since revision 42" are different requests, and answering either with
    // the other is how a fragment of the board gets taken for the board.
    if (since === null) {
      return badRequest(res, 'since is required - the revision you already have');
    }
    res.json(changesSince(since));
  } catch (error) {
    if (error instanceof ValidationError) return badRequest(res, error.message);
    throw error;
  }
});

app.post('/api/tasks', (req, res) => {
  try {
    const task = createTask(req.body || {});
    // Recorded after the store accepted the task, so a rejected title leaves
    // nothing in the journal.
    recordChange('created', task);
    res.status(201).json({ message: 'Task created', task });
  } catch (error) {
    if (error instanceof ValidationError) return badRequest(res, error.message);
    throw error;
  }
});

app.get('/api/tasks/:id', (req, res) => {
  const task = findTask(Number(req.params.id));
  task ? res.json(task) : notFound(res);
});

app.put('/api/tasks/:id', (req, res) => {
  try {
    const id = Number(req.params.id);
    // Copied before updateTask runs: it mutates the row it was given, so read
    // afterwards, "before" would hold the new values and agree with "after" for
    // every entry the journal ever. That is the one mistake a journal must not
    // make, and it is silent when it happens.
    const previous = findTask(id);
    const before = previous ? { ...previous } : null;

    const task = updateTask(id, req.body || {});
    if (!task) return notFound(res);
    recordChange('updated', task, before);
    res.json({ message: 'Task updated', task });
  } catch (error) {
    if (error instanceof ValidationError) return badRequest(res, error.message);
    throw error;
  }
});

app.delete('/api/tasks/:id', (req, res) => {
  const id = Number(req.params.id);
  const removed = findTask(id);
  if (!removed) return notFound(res);
  removeTask(id);
  // The board loses the row here, so for a deleted task the journal is the only
  // place its title still exists.
  recordChange('deleted', null, removed);
  res.json({ message: 'Task deleted' });
});

// Serve React index.html for all non-API routes (SPA)
app.get('*', (_req, res) => {
  res.sendFile(join(__dirname, '../dist/index.html'));
});

// ============================================================
// Start
// ============================================================

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Node.js Express API running on http://0.0.0.0:${PORT}`);
});
