import { useState } from 'react';

function App() {
  const [message, setMessage] = useState('This app is amazing and very fast');
  const [response, setResponse] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [mlPrediction, setMlPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse('');
    setAnalysis(null);
    setMlPrediction(null);

    try {
      const res = await fetch('http://localhost:8000/api/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();
      setResponse(data.reply || 'No response from backend');
      setAnalysis(data.analysis || null);
      setMlPrediction(data.ml_prediction || null);
    } catch (error) {
      setResponse('Error connecting to backend: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">AI + ML + React + FastAPI</p>
        <h1>AI Prediction App</h1>
        <p className="subtitle">
          Type some text and the backend will run both rule-based AI analysis and a small ML model.
        </p>

        <form onSubmit={handleSubmit} className="form">
          <label htmlFor="message">Text to analyze</label>
          <input
            id="message"
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your text here..."
          />

          <button type="submit" disabled={loading}>
            {loading ? 'Predicting...' : 'Run AI + ML'}
          </button>
        </form>

        <div className="response-box">
          <h2>Response</h2>
          <p>{response || 'Waiting for results...'}</p>

          {analysis && (
            <div className="analysis-grid">
              <div>
                <span className="label">Sentiment</span>
                <strong>{analysis.sentiment}</strong>
              </div>
              <div>
                <span className="label">Confidence</span>
                <strong>{analysis.confidence}%</strong>
              </div>
              <div>
                <span className="label">Words</span>
                <strong>{analysis.word_count}</strong>
              </div>
              <div>
                <span className="label">Keywords</span>
                <strong>{analysis.keywords.join(', ')}</strong>
              </div>
            </div>
          )}

          {mlPrediction && (
            <div className="ml-box">
              <h3>ML Prediction</h3>
              <p>
                <strong>Label:</strong> {mlPrediction.label}
              </p>
              <p>
                <strong>Confidence:</strong> {mlPrediction.confidence}%
              </p>
              <p>
                <strong>Model:</strong> {mlPrediction.model}
              </p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

export default App;
