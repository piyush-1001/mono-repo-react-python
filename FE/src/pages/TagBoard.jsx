import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchTags } from '../api/client';

// The labels people already type, read back off the board.
//
// There is no tags column in the store, so the tags here are the #hashtags in
// task titles, counted by BE/task_tags.py. That makes the report descriptive
// rather than authoritative, which is why the notes are shown above the chips:
// "#API" typed two ways is one label the count had to split by spelling, and a
// chip reading 3 when the user meant 5 is the failure this page has to name.
const MIN_COUNT_CHOICES = [1, 2, 3, 5];

// The chip that is picked gets a stronger fill than .term-chip's. Done inline
// rather than with a new CSS class because it is the only state this page has,
// and a rule that styles one element is a rule nobody will find again.
const ACTIVE_CHIP = {
  background: 'rgba(59, 130, 246, 0.45)',
  borderColor: 'rgba(96, 165, 250, 0.9)',
};

function TagBoard() {
  const [minCount, setMinCount] = useState(1);
  const [report, setReport] = useState(null);
  const [selected, setSelected] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setReport(await fetchTags({ minCount }));
    } catch (err) {
      setError(err.message);
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [minCount]);

  useEffect(() => {
    load();
  }, [load]);

  const tags = report?.tags || [];
  const active = tags.find((tag) => tag.tag === selected) || null;

  const choose = (tag) => {
    // A second click on the picked tag clears it, so there is a way back to the
    // whole list that is not the dropdown.
    setSelected((previous) => (previous === tag ? '' : tag));
  };

  // A picked tag that the new threshold hid is no longer pickable, so the
  // selection is dropped when the list changes underneath it rather than leaving
  // a panel open for a chip that has gone.
  useEffect(() => {
    if (selected && !tags.some((tag) => tag.tag === selected)) {
      setSelected('');
    }
  }, [tags, selected]);

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Node.js store · Python tags</p>
        <h1>Tag Board</h1>
        <p className="subtitle">
          What the board is about, counted from the hashtags in the titles.
        </p>

        <div className="form-row">
          <div>
            <label htmlFor="min-count">Hide tags used fewer than</label>
            <select
              id="min-count"
              value={minCount}
              onChange={(e) => setMinCount(Number(e.target.value))}
            >
              {MIN_COUNT_CHOICES.map((choice) => (
                <option key={choice} value={choice}>
                  {choice} {choice === 1 ? 'time' : 'times'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading && <p className="muted">Reading titles...</p>}
        {error && <p className="error-msg">{error}</p>}

        {report && !loading && (
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-value">{report.board}</span>
              <span className="muted">tasks read</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{report.tagged}</span>
              <span className="muted">have a tag</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{report.untagged}</span>
              <span className="muted">no tag</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{report.distinct}</span>
              <span className="muted">distinct tags</span>
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

        {report && tags.length > 0 && (
          <div className="term-chips">
            {tags.map((entry) => (
              <button
                key={entry.tag}
                type="button"
                className="term-chip"
                style={entry.tag === selected ? ACTIVE_CHIP : undefined}
                onClick={() => choose(entry.tag)}
              >
                #{entry.tag} · {entry.count}
              </button>
            ))}
          </div>
        )}

        {report && tags.length === 0 && (
          <p className="empty-msg">
            No tags to show. Nothing on the board has a hashtag in its title, or
            every tag is below the threshold.
          </p>
        )}

        {active && (
          <div className="response-box">
            <h2>
              #{active.tag}
              <span className="muted">
                {' '}
                · {active.open} open, {active.done} done
              </span>
            </h2>
            <div className="task-list">
              {active.tasks.map((task) => (
                <div key={task.id} className={`task-item ${task.status}`}>
                  <div className="rank-body">
                    <span className="task-title">{task.title}</span>
                  </div>
                  <div className="task-meta">
                    <span className={`badge ${task.priority}`}>{task.priority}</span>
                    <span className={`badge status ${task.status}`}>{task.status}</span>
                  </div>
                </div>
              ))}
            </div>
            {active.truncated && (
              <p className="muted">
                Showing the first {active.tasks.length} of {active.count} tasks.
              </p>
            )}
          </div>
        )}

        <Link to="/search" className="nav-link">
          ← Task Search
        </Link>
      </section>
    </main>
  );
}

export default TagBoard;
