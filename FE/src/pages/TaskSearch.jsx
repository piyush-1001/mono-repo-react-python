import { useState } from 'react';
import { Link } from 'react-router-dom';
import { searchTasks } from '../api/client';

// A search box over the stored board, backed by BE/task_search.py.
//
// The searching happens in Python, not here: the score needs the same TF-IDF
// vocabulary the rest of the board is measured with, and a browser copy of that
// would drift from the server's the first time either changed. This page sends
// what was typed and renders what came back, including the reasons, so a result
// can be questioned rather than trusted.
const STATUSES = ['pending', 'in-progress', 'done'];
const PRIORITIES = ['high', 'medium', 'low'];

function TaskSearch() {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const search = async (event) => {
    // The form's submit is what an Enter key in the text field fires, and the
    // default action would navigate away and lose the query.
    event.preventDefault();

    const hasQuery = query.trim() !== '';
    if (!hasQuery && !status && !priority) {
      // The API answers this with a 400. Saying it here instead keeps the
      // message next to the field it is about and saves a round trip.
      setError('Type something to search for, or pick a filter.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      setResult(await searchTasks({ query, status, priority }));
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setQuery('');
    setStatus('');
    setPriority('');
    setResult(null);
    setError('');
  };

  const results = result?.results || [];

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Node.js store · Python search</p>
        <h1>Task Search</h1>
        <p className="subtitle">
          Find a task by the words in its title, with the filters stacked on top.
        </p>

        <form className="form" onSubmit={search}>
          <label htmlFor="query">Query</label>
          <input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="tests, api, react..."
          />

          <div className="form-row">
            <div>
              <label htmlFor="status">Status</label>
              <select
                id="status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="">any</option>
                {STATUSES.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="priority">Priority</label>
              <select
                id="priority"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="">any</option>
                {PRIORITIES.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <button type="submit" disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </button>
            <button type="button" onClick={reset} disabled={loading}>
              Clear
            </button>
          </div>
        </form>

        {error && <p className="error-msg">{error}</p>}

        {result && (
          <p className="muted">
            {result.matched} of {result.scanned} searched
            {result.board !== result.scanned ? ` (${result.board} on the board)` : ''}
            {result.query ? ` for “${result.query}”` : ''}
          </p>
        )}

        {/* The notes are the search's own account of what it did: a filter it
            threw away, or a result set cut short by the limit. They are the
            difference between a short list being correct and being misleading. */}
        {result?.notes?.length > 0 && (
          <ul className="muted">
            {result.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        )}

        {results.length > 0 && (
          <div className="task-list">
            {results.map((task, index) => (
              <div key={`${task.id}-${index}`} className={`task-item ${task.status}`}>
                <div className="rank-body">
                  <div className="rank-header">
                    <span className="rank-pos">{index + 1}</span>
                    <span className="task-title">{task.title}</span>
                  </div>
                  {task.reasons.length > 0 && (
                    <p className="muted rank-reasons">{task.reasons.join(' · ')}</p>
                  )}
                  {task.score > 0 && (
                    <span className="bar">
                      <span className="bar-fill" style={{ width: `${task.score}%` }} />
                    </span>
                  )}
                </div>
                <div className="task-meta">
                  <span className={`badge ${task.priority}`}>{task.priority}</span>
                  <span className={`badge status ${task.status}`}>{task.status}</span>
                  <span className="rank-score">{task.score}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {result && results.length === 0 && (
          <p className="empty-msg">
            Nothing on the board matched. The board holds {result.board} task
            {result.board === 1 ? '' : 's'}.
          </p>
        )}

        <Link to="/export" className="nav-link">
          ← Export Center
        </Link>
      </section>
    </main>
  );
}

export default TaskSearch;
