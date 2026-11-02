import { useState, useEffect } from 'react';

const API = '/api';

function TaskManager() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');

  const fetchTasks = async () => {
    try {
      const res = await fetch(API + '/tasks');
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch {
      setTasks([]);
    }
  };

  useEffect(() => { fetchTasks(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    try {
      await fetch(API + '/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title.trim(), priority }),
      });
      setTitle('');
      fetchTasks();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleStatus = async (task) => {
    const newStatus = task.status === 'done' ? 'pending' : 'done';
    try {
      await fetch(API + `/tasks/${task.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      fetchTasks();
    } catch (err) {
      console.error(err);
    }
  };

  const deleteTask = async (id) => {
    try {
      await fetch(API + `/tasks/${id}`, { method: 'DELETE' });
      fetchTasks();
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = filter ? tasks.filter((t) => t.status === filter) : tasks;

  const counts = {
    all: tasks.length,
    done: tasks.filter((t) => t.status === 'done').length,
    pending: tasks.filter((t) => t.status === 'pending').length,
    'in-progress': tasks.filter((t) => t.status === 'in-progress').length,
  };

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">React + Node.js</p>
        <h1>Task Manager</h1>
        <p className="subtitle">
          CRUD tasks via a Node.js Express API.
        </p>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-row">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="New task title..."
            />
            <select value={priority} onChange={(e) => setPriority(e.target.value)}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <button type="submit" disabled={loading || !title.trim()}>
              {loading ? 'Adding...' : 'Add Task'}
            </button>
          </div>
        </form>

        <div className="filter-tabs">
          {['all', 'pending', 'in-progress', 'done'].map((f) => (
            <button
              key={f}
              className={filter === f ? 'active' : ''}
              onClick={() => setFilter(filter === f ? '' : f)}
            >
              {f.replace('-', ' ')} ({counts[f]})
            </button>
          ))}
        </div>

        <div className="task-list">
          {filtered.length === 0 ? (
            <p className="empty-msg">No tasks found.</p>
          ) : (
            filtered.map((task) => (
              <div key={task.id} className={`task-item ${task.status}`}>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={task.status === 'done'}
                    onChange={() => toggleStatus(task)}
                  />
                  <span className="task-title">{task.title}</span>
                </label>
                <div className="task-meta">
                  <span className={`badge ${task.priority}`}>{task.priority}</span>
                  <span className={`badge status ${task.status}`}>{task.status}</span>
                  <button className="delete-btn" onClick={() => deleteTask(task.id)}>
                    ✕
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </main>
  );
}

export default TaskManager;
