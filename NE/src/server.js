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
  const { status, priority } = req.query;
  const result = listTasks({ status, priority });
  res.json({ count: result.length, tasks: result });
});

// Declared before /api/tasks/:id on purpose: Express matches routes in the
// order they were declared, so ":id" would swallow "stats" and answer 404 for
// a path that has its own endpoint. A numeric check inside the id route would
// not help, because the id route is still reached first.
app.get('/api/tasks/stats', (_req, res) => {
  res.json(stats());
});

app.post('/api/tasks', (req, res) => {
  try {
    const task = createTask(req.body || {});
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
    const task = updateTask(Number(req.params.id), req.body || {});
    if (!task) return notFound(res);
    res.json({ message: 'Task updated', task });
  } catch (error) {
    if (error instanceof ValidationError) return badRequest(res, error.message);
    throw error;
  }
});

app.delete('/api/tasks/:id', (req, res) => {
  if (!removeTask(Number(req.params.id))) return notFound(res);
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
