import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchPlan } from '../api/client';

// A week laid out over the board, backed by BE/workload.py.
//
// The ranking page answers "what is next"; this answers "what fits before the
// weekend". The order is the ranker's and is not re-decided here - this page only
// chooses the pace, and shows what did not fit as loudly as what did. A plan that
// quietly ended at the capacity would be the misleading version of the same list.
const DAY_CHOICES = [1, 2, 3, 4, 5, 7, 10, 14];
const PACE_CHOICES = [1, 2, 3, 4, 5, 8, 10];

function PlanBoard() {
  const [days, setDays] = useState(5);
  const [perDay, setPerDay] = useState(3);
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setPlan(await fetchPlan({ days, perDay }));
    } catch (err) {
      setError(err.message);
      setPlan(null);
    } finally {
      setLoading(false);
    }
  }, [days, perDay]);

  // Re-planned whenever the pace changes rather than behind a button: the two
  // controls are the whole request, and a plan that waits for a click after the
  // number on screen changed is a plan describing last week.
  useEffect(() => {
    load();
  }, [load]);

  const schedule = plan?.schedule || [];
  const unscheduled = plan?.unscheduled || [];

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Node.js store · Python planning</p>
        <h1>Workload Plan</h1>
        <p className="subtitle">
          The open tasks, in rank order, spread over the next working days at the
          pace you pick.
        </p>

        <div className="form-row">
          <div>
            <label htmlFor="days">Days</label>
            <select id="days" value={days} onChange={(e) => setDays(Number(e.target.value))}>
              {DAY_CHOICES.map((choice) => (
                <option key={choice} value={choice}>
                  {choice} {choice === 1 ? 'day' : 'days'}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="per-day">Tasks per day</label>
            <select
              id="per-day"
              value={perDay}
              onChange={(e) => setPerDay(Number(e.target.value))}
            >
              {PACE_CHOICES.map((choice) => (
                <option key={choice} value={choice}>
                  {choice} {choice === 1 ? 'task' : 'tasks'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading && <p className="muted">Planning...</p>}
        {error && <p className="error-msg">{error}</p>}

        {plan && !loading && (
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-value">{plan.open_count}</span>
              <span className="muted">open tasks</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{plan.scheduled}</span>
              <span className="muted">scheduled</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{unscheduled.length}</span>
              <span className="muted">did not fit</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{plan.capacity}</span>
              <span className="muted">slots in {plan.days_planned} days</span>
            </div>
          </div>
        )}

        {plan?.notes?.length > 0 && (
          <ul className="muted">
            {plan.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        )}

        {plan && schedule.length > 0 && (
          <div className="info-grid">
            {schedule.map((day) => (
              <div key={day.date} className="info-card">
                <h3>
                  {day.weekday}{' '}
                  <span className="muted">{day.date.slice(5)}</span>
                </h3>
                {day.tasks.length === 0 && <p className="muted">Nothing planned.</p>}
                {day.tasks.map((task) => (
                  <div key={task.id} className="task-item">
                    <div className="rank-body">
                      <span className="task-title">{task.title}</span>
                      <p className="muted rank-reasons">{task.reasons.join(' · ')}</p>
                    </div>
                    <div className="task-meta">
                      <span className={`badge ${task.priority}`}>{task.priority}</span>
                      <span className="rank-score">{task.score}</span>
                    </div>
                  </div>
                ))}
                {/* A full day with work still waiting is where the plan slips, so
                    the day says so itself instead of leaving the user to add up
                    two numbers. */}
                {day.full && unscheduled.length > 0 && (
                  <p className="muted">Full - {unscheduled.length} still waiting.</p>
                )}
              </div>
            ))}
          </div>
        )}

        {plan && unscheduled.length > 0 && (
          <div className="response-box">
            <h2>Did not fit</h2>
            <div className="task-list">
              {unscheduled.map((task) => (
                <div key={task.id} className={`task-item ${task.status}`}>
                  <div className="rank-body">
                    <span className="task-title">{task.title}</span>
                    <p className="muted rank-reasons">{task.reasons.join(' · ')}</p>
                  </div>
                  <div className="task-meta">
                    <span className={`badge ${task.priority}`}>{task.priority}</span>
                    <span className="rank-score">{task.score}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {plan && plan.open_count === 0 && (
          <p className="empty-msg">
            Nothing open. Every task on the board is already done.
          </p>
        )}

        <Link to="/insights" className="nav-link">
          ← Task Insights
        </Link>
      </section>
    </main>
  );
}

export default PlanBoard;
