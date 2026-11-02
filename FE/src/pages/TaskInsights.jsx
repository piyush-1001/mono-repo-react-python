import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchTasks, rankTasks } from '../api/client';

function TaskInsights() {
  const [ranked, setRanked] = useState([]);
  const [duplicates, setDuplicates] = useState([]);
  const [nextTaskId, setNextTaskId] = useState(null);
  const [openCount, setOpenCount] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      // Tasks come from Node.js; the ranking logic lives in Python.
      const tasks = await fetchTasks();
      const result = await rankTasks(tasks);
      setRanked(result.ranked || []);
      setDuplicates(result.duplicates || []);
      setNextTaskId(result.next_task_id);
      setOpenCount(result.open_count || 0);
    } catch (err) {
      setError(err.message);
      setRanked([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const byId = new Map(ranked.map((task) => [task.id, task]));

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">React + Node.js + Python</p>
        <h1>Task Insights</h1>
        <p className="subtitle">
          Tasks are read from the Node.js API and prioritized by the Python
          ranker, which weighs priority, status, age and urgent wording.
        </p>

        <button onClick={load} disabled={loading}>
          {loading ? 'Ranking...' : 'Re-rank tasks'}
        </button>

        {error && <p className="error-msg">{error}</p>}

        {!loading && !error && ranked.length === 0 && (
          <p className="empty-msg">No tasks stored yet. Add one in the Task Manager.</p>
        )}

        {duplicates.length > 0 && (
          <div className="response-box">
            <h2>{duplicates.length} possible duplicate{duplicates.length > 1 ? 's' : ''}</h2>
            <ul className="feature-list">
              {duplicates.map((pair) => (
                <li key={`${pair.first}-${pair.second}`}>
                  "{byId.get(pair.first)?.title}" and "{byId.get(pair.second)?.title}" are{' '}
                  {pair.similarity}% similar
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="task-list">
          {ranked.map((task, index) => (
            <div
              key={task.id}
              className={`task-item ${task.status}${task.id === nextTaskId ? ' next-up' : ''}`}
            >
              <div className="rank-body">
                <div className="rank-header">
                  <span className="rank-pos">{index + 1}</span>
                  <span className="task-title">{task.title}</span>
                  {task.id === nextTaskId && <span className="badge in-progress">do next</span>}
                </div>
                <p className="muted rank-reasons">{task.reasons.join(' · ')}</p>
                <span className="bar">
                  <span className="bar-fill" style={{ width: `${task.score}%` }} />
                </span>
              </div>
              <div className="task-meta">
                <span className={`badge ${task.priority}`}>{task.priority}</span>
                <span className={`badge status ${task.status}`}>{task.status}</span>
                <span className="rank-score">{task.score}</span>
              </div>
            </div>
          ))}
        </div>

        {ranked.length > 0 && (
          <p className="muted">
            {openCount} open task{openCount === 1 ? '' : 's'} of {ranked.length} ranked.
          </p>
        )}

        <Link to="/" className="nav-link">
          ← Manage tasks
        </Link>
      </section>
    </main>
  );
}

export default TaskInsights;
