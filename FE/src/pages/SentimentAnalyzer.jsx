import { useState } from 'react';

function SentimentAnalyzer() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setLoading(true);
    setResponse('');
    setAnalysis(null);

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

      // Save to localStorage history
      const history = JSON.parse(localStorage.getItem('sentimentHistory') || '[]');
      history.unshift({
        id: Date.now(),
        message,
        analysis: data.analysis,
        timestamp: new Date().toLocaleString()
      });
      localStorage.setItem('sentimentHistory', JSON.stringify(history.slice(0, 50)));
    } catch (error) {
      setResponse('Error connecting to backend: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">AI + React + FastAPI</p>
        <h1>Sentiment Analyzer</h1>
        <p className="subtitle">
          Type a sentence and the backend will analyze its sentiment.
        </p>

        <form onSubmit={handleSubmit} className="form">
          <label htmlFor="message">Text to analyze</label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type something positive or negative..."
            rows={3}
          />

          <button type="submit" disabled={loading || !message.trim()}>
            {loading ? 'Analyzing...' : 'Analyze text'}
          </button>
        </form>

        <div className="response-box">
          <h2>AI response</h2>
          <p>{response || 'Waiting for a response...'}</p>

          {analysis && (
            <div className="analysis-grid">
              <div>
                <span className="label">Sentiment</span>
                <strong className={analysis.sentiment}>{analysis.sentiment}</strong>
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
        </div>
      </section>
    </main>
  );
}

export default SentimentAnalyzer;
