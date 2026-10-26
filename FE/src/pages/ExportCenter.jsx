import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  fetchTaskStats,
  fetchTasks,
  rankStoredTasks,
  exportRanking,
} from '../api/client';

// A page over the export endpoints in BE/task_export.py.
//
// The export is produced by the Python side, which owns the ranking, so this
// page never formats a task itself: it asks for a document and either saves it
// or shows it. The two sources of truth stay in one place.
function ExportCenter() {
  const [stats, setStats] = useState(null);
  const [ranking, setRanking] = useState(null);
  const [markdown, setMarkdown] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState('');

  const loadStats = useCallback(async () => {
    try {
      setStats(await fetchTaskStats());
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // One call: the Python server reads the Node.js store and ranks it, so the
  // browser does not fetch every task and post the list straight back.
  const rank = async () => {
    setLoading(true);
    setError('');
    try {
      setRanking(await rankStoredTasks());
    } catch (err) {
      setError(err.message);
      setRanking(null);
    } finally {
      setLoading(false);
    }
  };

  const downloadCsv = async () => {
    setBusy('csv');
    setError('');
    try {
      const tasks = await fetchTasks();
      const csv = await exportRanking(tasks, 'csv');

      // A Blob plus a synthetic anchor is how a browser saves a file that was
      // assembled in the page. Without it the CSV would open as text in a tab
      // and the user would have to save it by hand.
      const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `task-ranking-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      // The object URL keeps the blob alive until it is revoked, so leaving it
      // behind leaks the whole file for the life of the tab.
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  };

  const previewMarkdown = async () => {
    setBusy('markdown');
    setError('');
    try {
      const tasks = await fetchTasks();
      setMarkdown(await exportRanking(tasks, 'markdown'));
    } catch (err) {
      setError(err.message);
      setMarkdown('');
    } finally {
      setBusy('');
    }
  };

  const ranked = ranking?.ranked || [];

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Node.js store · Python ranking</p>
        <h1>Export Center</h1>
        <p className="subtitle">
          Rank the stored tasks and take the result away as a CSV file or a
          Markdown table.
        </p>

        {stats && (
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-value">{stats.total}</span>
              <span className="muted">tasks stored</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.open}</span>
              <span className="muted">still open</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.done}</span>
              <span className="muted">done</span>
            </div>
            {stats.oldest_open_task && (
              <div className="stat-card">
                <span className="stat-value">{stats.oldest_open_task.title}</span>
                <span className="muted">oldest open task</span>
              </div>
            )}
          </div>
        )}

        <div className="form-row">
          <button onClick={rank} disabled={loading}>
            {loading ? 'Ranking...' : 'Rank stored tasks'}
          </button>
          <button onClick={downloadCsv} disabled={busy !== ''}>
            {busy === 'csv' ? 'Preparing...' : 'Download CSV'}
          </button>
          <button onClick={previewMarkdown} disabled={busy !== ''}>
            {busy === 'markdown' ? 'Preparing...' : 'Preview Markdown'}
          </button>
        </div>

        {error && <p className="error-msg">{error}</p>}

        {ranked.length > 0 && (
          <div className="task-list">
            {ranked.map((task, index) => (
              <div key={task.id} className={`task-item ${task.status}`}>
                <div className="rank-body">
                  <div className="rank-header">
                    <span className="rank-pos">{index + 1}</span>
                    <span className="task-title">{task.title}</span>
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
        )}

        {ranking && ranked.length === 0 && (
          <p className="empty-msg">The store is empty. Add a task in the Task Manager first.</p>
        )}

        {markdown && (
          <div className="response-box">
            <h2>Markdown preview</h2>
            <pre className="export-preview">{markdown}</pre>
          </div>
        )}

        <Link to="/insights" className="nav-link">
          ← Task Insights
        </Link>
      </section>
    </main>
  );
}

export default ExportCenter;
