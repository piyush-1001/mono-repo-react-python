import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listModels } from '../api/client';

function Models() {
  const [models, setModels] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    listModels()
      .then((data) => {
        if (!cancelled) setModels(data.models || []);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Python backend</p>
        <h1>Available Models</h1>
        <p className="subtitle">
          The machine learning endpoints the FastAPI backend currently exposes.
        </p>

        {loading && <p className="muted">Loading models...</p>}
        {!loading && error && <p className="error-msg">{error}</p>}
        {!loading && !error && models.length === 0 && (
          <p className="empty-msg">No models reported by the backend.</p>
        )}

        <div className="info-grid">
          {models.map((model) => (
            <div key={model.id} className="info-card">
              <h3>{model.name}</h3>
              <p className="muted">
                <code>{model.method} {model.endpoint}</code>
              </p>
              <p>{model.description}</p>
            </div>
          ))}
        </div>

        <Link to="/ml" className="nav-link">
          Try them in the ML Lab →
        </Link>
      </section>
    </main>
  );
}

export default Models;
