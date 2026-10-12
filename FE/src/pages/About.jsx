import { Link } from 'react-router-dom';

function About() {
  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">About</p>
        <h1>Task Manager</h1>
        <p className="subtitle">
          A React + Node.js task management app with full CRUD operations.
        </p>

        <div className="info-grid">
          <div className="info-card">
            <h3>Frontend</h3>
            <p>React 18 with Vite</p>
            <p>React Router for navigation</p>
            <p>LocalStorage for history</p>
          </div>
          <div className="info-card">
            <h3>Backend</h3>
            <p>Node.js + Express</p>
            <p>REST API design</p>
            <p>CORS enabled</p>
          </div>
        </div>

        <div className="info-card">
          <h3>Features</h3>
          <ul className="feature-list">
            <li>Create, read, update, delete tasks</li>
            <li>Filter by status (all / pending / in-progress / done)</li>
            <li>Priority levels (low / medium / high)</li>
            <li>Real-time task count statistics</li>
          </ul>
        </div>

        <Link to="/" className="nav-link">
          ← Back to Tasks
        </Link>
      </section>
    </main>
  );
}

export default About;
