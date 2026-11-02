import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchDuplicates } from '../api/client';

// A look at the tasks that say the same thing, backed by BE/task_dedup.py.
//
// The report does not close anything: it groups the look-alikes and says which
// one to keep, because closing a task is the store's business and a report that
// quietly did it would be a report nobody could check. What the page shows is
// the decision and the reason for it, so "keep #4, close #7" can be argued with.
const THRESHOLDS = [40, 50, 60, 70, 80, 90];

function DuplicateReview() {
  const [threshold, setThreshold] = useState(60);
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setReport(await fetchDuplicates({ threshold }));
    } catch (err) {
      setError(err.message);
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [threshold]);

  useEffect(() => {
    load();
  }, [load]);

  const clusters = report?.clusters || [];

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Node.js store · Python duplicates</p>
        <h1>Duplicate Review</h1>
        <p className="subtitle">
          The tasks whose titles say the same thing, grouped, with the one to
          keep marked.
        </p>

        <div className="form-row">
          <div>
            <label htmlFor="threshold">Treat titles as alike above</label>
            <select
              id="threshold"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
            >
              {THRESHOLDS.map((value) => (
                <option key={value} value={value}>
                  {value}%
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading && <p className="muted">Comparing titles...</p>}
        {error && <p className="error-msg">{error}</p>}

        {report && !loading && (
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-value">{report.cluster_count}</span>
              <span className="muted">groups</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{report.duplicate_tasks}</span>
              <span className="muted">tasks involved</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{report.board}</span>
              <span className="muted">on the board</span>
            </div>
          </div>
        )}

        {report?.notes?.length > 0 && (
          <ul className="muted">
            {report.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        )}

        {report && clusters.length > 0 && (
          <div className="info-grid">
            {clusters.map((cluster) => (
              <div key={cluster.keep_id} className="info-card">
                <h3>
                  {cluster.size} tasks
                  <span className="muted">
                    {' '}
                    · {cluster.exact ? 'identical titles' : `${cluster.similarity}% alike`}
                  </span>
                </h3>
                <p className="muted">{cluster.reason}</p>

                <div className="task-list">
                  {cluster.tasks.map((task) => {
                    const keep = task.id === cluster.keep_id;
                    return (
                      <div key={task.id} className={`task-item ${task.status}`}>
                        <div className="rank-body">
                          <span className="task-title">{task.title}</span>
                          <span className="label">
                            {keep ? 'keep' : 'close'} #{task.id}
                          </span>
                        </div>
                        <div className="task-meta">
                          <span className={`badge ${task.priority}`}>{task.priority}</span>
                          <span className={`badge status ${task.status}`}>{task.status}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {cluster.truncated && (
                  <p className="muted">
                    Showing {cluster.tasks.length} of {cluster.size} tasks in this group.
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {report && clusters.length === 0 && (
          <p className="empty-msg">
            Nothing looks like a duplicate at {threshold}%. Every title on the
            board is its own task.
          </p>
        )}

        <Link to="/insights" className="nav-link">
          ← Task Insights
        </Link>
      </section>
    </main>
  );
}

export default DuplicateReview;
