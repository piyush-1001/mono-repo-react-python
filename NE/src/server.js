import express from 'express';
import cors from 'cors';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

// Serve React build in production
app.use(express.static(join(__dirname, '../dist')));

// ============================================================
// In-memory data store
// ============================================================

let tasks = [
  { id: 1, title: 'Learn React', status: 'done', priority: 'high', createdAt: new Date().toISOString() },
  { id: 2, title: 'Build Node.js API', status: 'in-progress', priority: 'high', createdAt: new Date().toISOString() },
  { id: 3, title: 'Write unit tests', status: 'pending', priority: 'medium', createdAt: new Date().toISOString() },
];
let nextId = 4;

// ============================================================
// Helper
// ============================================================

const notFound = (res) => res.status(404).json({ error: 'Not found' });
const badRequest = (res, msg) => res.status(400).json({ error: msg });

// ============================================================
// Routes
// ============================================================

app.get('/', (_req, res) => {
  res.json({
    message: 'Node.js Express API is running',
    version: '1.0',
    endpoints: ['GET /', 'GET /api/health', 'GET /api/tasks', 'POST /api/tasks', 'GET /api/tasks/:id', 'PUT /api/tasks/:id', 'DELETE /api/tasks/:id'],
  });
});

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/api/tasks', (req, res) => {
  const { status, priority } = req.query;
  let result = tasks;
  if (status) result = result.filter((t) => t.status === status);
  if (priority) result = result.filter((t) => t.priority === priority);
  res.json({ count: result.length, tasks: result });
});

app.post('/api/tasks', (req, res) => {
  const { title, priority = 'medium' } = req.body;
  if (!title) return badRequest(res, 'title is required');
  const task = { id: nextId++, title: title.trim(), status: 'pending', priority, createdAt: new Date().toISOString() };
  tasks.push(task);
  res.status(201).json({ message: 'Task created', task });
});

app.get('/api/tasks/:id', (req, res) => {
  const task = tasks.find((t) => t.id === Number(req.params.id));
  task ? res.json(task) : notFound(res);
});

app.put('/api/tasks/:id', (req, res) => {
  const idx = tasks.findIndex((t) => t.id === Number(req.params.id));
  if (idx === -1) return notFound(res);
  const { title, status, priority } = req.body;
  if (title !== undefined) tasks[idx].title = title.trim();
  if (status !== undefined) tasks[idx].status = status;
  if (priority !== undefined) tasks[idx].priority = priority;
  res.json({ message: 'Task updated', task: tasks[idx] });
});

app.delete('/api/tasks/:id', (req, res) => {
  const idx = tasks.findIndex((t) => t.id === Number(req.params.id));
  if (idx === -1) return notFound(res);
  tasks.splice(idx, 1);
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
