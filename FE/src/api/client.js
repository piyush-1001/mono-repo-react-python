// Thin wrapper around the Python (FastAPI) backend.
// Override the base URL with VITE_API_BASE when the API is not on localhost:8000.

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

async function request(path, { method = 'GET', body } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    // FastAPI puts the reason in `detail`, which may be a string or a list.
    let detail = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      if (typeof data.detail === 'string') detail = data.detail;
      else if (Array.isArray(data.detail)) detail = data.detail.map((d) => d.msg).join('; ');
    } catch {
      // Keep the generic message when the body is not JSON.
    }
    throw new Error(detail);
  }

  return res.json();
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
