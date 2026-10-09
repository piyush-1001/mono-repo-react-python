import { Link } from 'react-router-dom';

function About() {
  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">About</p>
        <h1>Smart One Page App</h1>
        <p className="subtitle">
          A demonstration of React connected to a FastAPI backend.
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
            <p>FastAPI (Python)</p>
            <p>Keyword-based analysis</p>
            <p>CORS enabled</p>
          </div>
        </div>

        <div className="info-card">
          <h3>Features</h3>
          <ul className="feature-list">
            <li>Real-time sentiment analysis</li>
            <li>Keyword extraction</li>
            <li>Analysis history tracking</li>
            <li>Confidence scoring</li>
          </ul>
        </div>

        <Link to="/" className="nav-link">
          ← Back to Analyzer
        </Link>
      </section>
    </main>
  );
}

export default About;
