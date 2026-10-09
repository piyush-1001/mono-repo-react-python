import { Link } from 'react-router-dom';

function About() {
  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">About</p>
        <h1>Smart One Page App</h1>
        <p className="subtitle">
          A simple demonstration of React connected to a FastAPI backend with sentiment analysis.
        </p>

        <div className="info-grid">
          <div className="info-card">
            <h3>Frontend</h3>
            <p>React 18 with Vite</p>
            <p>React Router for navigation</p>
          </div>
          <div className="info-card">
            <h3>Backend</h3>
            <p>FastAPI (Python)</p>
            <p>Simple keyword-based analysis</p>
          </div>
        </div>

        <Link to="/" className="nav-link">
          ← Back to Analyzer
        </Link>
      </section>
    </main>
  );
}

export default About;
