import { Link } from 'react-router-dom';

function About() {
  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">About</p>
        <h1>NE Fullstack App</h1>
        <p className="subtitle">
          A fullstack app built with Node.js, Express, and React.
        </p>

        <div className="info-grid">
          <div className="info-card">
            <h3>Frontend</h3>
            <p>React 18</p>
            <p>React Router</p>
            <p>Vite bundler</p>
          </div>
          <div className="info-card">
            <h3>Backend</h3>
            <p>Node.js + Express</p>
            <p>REST API</p>
            <p>CORS enabled</p>
          </div>
        </div>

        <div className="info-card">
          <h3>Features</h3>
          <ul className="feature-list">
            <li>Create, read, update, delete tasks</li>
            <li>Filter by status</li>
            <li>Priority levels</li>
            <li>Real-time task counts</li>
          </ul>
        </div>

        <Link to="/" className="nav-link">← Back to Tasks</Link>
      </section>
    </main>
  );
}

export default About;
