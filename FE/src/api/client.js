// Thin wrapper around the Python (FastAPI) backend.
// Override the base URL with VITE_API_BASE when the API is not on localhost:8000.

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// The reason a request failed, in the words the API used.
//
// FastAPI puts the reason in `detail`, which is either a string or a list of
// validation errors; the Node.js API uses `error` and has no `detail` at all.
// Both are read here so a page can show one message whichever backend answered.
async function failureMessage(res) {
  let detail = `Request failed with status ${res.status}`;
  try {
    const data = await res.json();
    if (typeof data.detail === 'string') detail = data.detail;
    else if (Array.isArray(data.detail)) detail = data.detail.map((d) => d.msg).join('; ');
    else if (typeof data.error === 'string') detail = data.error;
  } catch {
    // Keep the generic message when the body is not JSON.
  }
  return detail;
}

async function request(path, { method = 'GET', body } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) throw new Error(await failureMessage(res));

  return res.json();
}

// The export endpoint answers with CSV or Markdown text rather than JSON, so it
// cannot go through request() above. Same request, same error handling, a
// different body.
async function requestText(path, { method = 'GET', body } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) throw new Error(await failureMessage(res));

  return res.text();
}

export const listModels = () => request('/api/models');

export const analyzeSentiment = (message) =>
  request('/api/sentiment', { method: 'POST', body: { message } });

export const predictSpam = (message) =>
  request('/api/predict', { method: 'POST', body: { message } });

export const compareTexts = (textA, textB) =>
  request('/api/similarity', { method: 'POST', body: { text_a: textA, text_b: textB } });

export const generateText = (seed, maxWords = 30) =>
  request('/api/generate', { method: 'POST', body: { seed, max_words: maxWords } });

export const clusterTexts = (texts, k = 2) =>
  request('/api/cluster', { method: 'POST', body: { texts, k } });

// Tasks live in the Node.js API; ranking logic lives in Python.
export const TASKS_API_BASE =
  import.meta.env.VITE_TASKS_API_BASE || 'http://localhost:3000';

export const fetchTasks = async () => {
  const res = await fetch(`${TASKS_API_BASE}/api/tasks`);
  if (!res.ok) throw new Error(`Task API failed with status ${res.status}`);
  const data = await res.json();
  return data.tasks || [];
};

// Counts and the oldest open task, read straight from the store.
export const fetchTaskStats = async () => {
  const res = await fetch(`${TASKS_API_BASE}/api/tasks/stats`);
  if (!res.ok) throw new Error(`Task API failed with status ${res.status}`);
  return res.json();
};

// The shape the Python ranker expects: snake_case, and no nulls where the
// FastAPI model declares defaults. Shared by the ranking and export calls, so
// the two cannot drift apart.
const toRankPayload = (task) => ({
  id: task.id,
  title: task.title,
  status: task.status,
  priority: task.priority,
  created_at: task.createdAt,
});

export const rankTasks = (tasks) =>
  request('/api/rank-tasks', {
    method: 'POST',
    body: { tasks: tasks.map(toRankPayload) },
  });

// Ranks whatever is in the Node.js store, in one call. The Python server reads
// the store itself, so the browser does not fetch every task and post the list
// straight back - which is what a phone on a slow connection would rather not
// do.
export const rankStoredTasks = () => request('/api/tasks/ranked');

// Search the stored board by the words in a task title (BE/task_search.py).
//
// Empty filters are left out of the query string rather than sent as blanks:
// `?status=` arrives as an empty value, which the search module cannot match
// against its list of statuses and has to report as an ignored filter. A search
// that says "your filter was ignored" when the user never touched the dropdown
// is a worse answer than one that never saw the parameter.
export const searchTasks = ({ query = '', status = '', priority = '' } = {}) => {
  const params = new URLSearchParams();
  if (query.trim()) params.set('q', query.trim());
  if (status) params.set('status', status);
  if (priority) params.set('priority', priority);
  return request(`/api/tasks/search?${params.toString()}`);
};

// Exports a ranking as CSV or Markdown. The document comes back as text;
// turning it into a download is the page's job, not this module's.
export const exportRanking = (tasks, format = 'csv') =>
  requestText('/api/tasks/export', {
    method: 'POST',
    body: { tasks: tasks.map(toRankPayload), format },
  });

// Latent topics over a set of documents.
export const discoverTopics = (texts, topics = 2) =>
  request('/api/topics', { method: 'POST', body: { texts, topics } });

// Runs any model from the catalogue. The endpoint and the method come from
// /api/models, so a model added on the Python side appears in the app without a
// change to this file.
export const runModel = (model, body) =>
  model.method === 'GET'
    ? request(model.endpoint)
    : request(model.endpoint, { method: 'POST', body });
