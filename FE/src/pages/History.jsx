import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

function History() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem('sentimentHistory') || '[]');
    setHistory(saved);
  }, []);

  const clearHistory = () => {
    localStorage.removeItem('sentimentHistory');
    setHistory([]);
  };

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Analysis</p>
        <h1>History</h1>
        <p className="subtitle">
          Your recent sentiment analysis results.
        </p>

        {history.length === 0 ? (
          <div className="empty-state">
            <p>No analysis history yet.</p>
            <Link to="/" className="nav-link">Start analyzing →</Link>
          </div>
        ) : (
          <>
            <button className="clear-btn" onClick={clearHistory}>
              Clear History
            </button>
            <div className="history-list">
              {history.map((item) => (
                <div key={item.id} className="history-item">
                  <div className="history-header">
                    <span className={`sentiment-badge ${item.analysis?.sentiment}`}>
                      {item.analysis?.sentiment || 'unknown'}
                    </span>
                    <span className="history-time">{item.timestamp}</span>
                  </div>
                  <p className="history-message">"{item.message}"</p>
                  <div className="history-meta">
                    <span>Confidence: {item.analysis?.confidence}%</span>
                    <span>Keywords: {item.analysis?.keywords?.join(', ')}</span>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        <Link to="/" className="nav-link">
          ← Back to Analyzer
        </Link>
      </section>
    </main>
  );
}

export default History;
