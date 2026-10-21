import { useState } from 'react';
import {
  analyzeSentiment,
  predictSpam,
  compareTexts,
  generateText,
  clusterTexts,
} from '../api/client';

const TABS = [
  { id: 'sentiment', label: 'Sentiment' },
  { id: 'spam', label: 'Spam filter' },
  { id: 'similarity', label: 'Similarity' },
  { id: 'generate', label: 'Generator' },
  { id: 'cluster', label: 'Clustering' },
];

const SAMPLE_TEXTS = [
  'Machine learning models learn patterns from data',
  'Free pills discount buy now limited stock',
  'The deployment failed with a timeout error',
];

function MLLab() {
  const [tab, setTab] = useState('sentiment');

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">React + Python</p>
        <h1>ML Lab</h1>
        <p className="subtitle">
          Every panel below calls a machine learning endpoint served by the Python
          FastAPI backend.
        </p>

        <div className="filter-tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={tab === t.id ? 'active' : ''}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === 'sentiment' && <SentimentPanel />}
        {tab === 'spam' && <SpamPanel />}
        {tab === 'similarity' && <SimilarityPanel />}
        {tab === 'generate' && <GeneratePanel />}
        {tab === 'cluster' && <ClusterPanel />}
      </section>
    </main>
  );
}

/* ------------------------------------------------------------------ */

function SentimentPanel() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const run = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      setResult(await analyzeSentiment(text.trim()));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={run} className="form">
      <label htmlFor="sentiment-text">Text to analyze</label>
      <textarea
        id="sentiment-text"
        rows={3}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="The support team was fast and helpful"
      />
      <button type="submit" disabled={loading || !text.trim()}>
        {loading ? 'Analyzing...' : 'Analyze sentiment'}
      </button>
      <ErrorMessage message={error} />
      {result && (
        <div className="analysis-grid">
          <div>
            <span className="label">Sentiment</span>
            <strong className={result.sentiment}>{result.sentiment}</strong>
          </div>
          <div>
            <span className="label">Confidence</span>
            <strong>{result.confidence}%</strong>
          </div>
          <div>
            <span className="label">Words</span>
            <strong>{result.word_count}</strong>
          </div>
          <div>
            <span className="label">Keywords</span>
            <strong>{result.keywords.join(', ')}</strong>
          </div>
        </div>
      )}
    </form>
  );
}

/* ------------------------------------------------------------------ */

function SpamPanel() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const run = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      setResult(await predictSpam(text.trim()));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={run} className="form">
      <label htmlFor="spam-text">Message to classify</label>
      <textarea
        id="spam-text"
        rows={3}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Claim your free prize now"
      />
      <button type="submit" disabled={loading || !text.trim()}>
        {loading ? 'Classifying...' : 'Classify message'}
      </button>
      <ErrorMessage message={error} />
      {result && (
        <div className="response-box">
          <h2>Verdict: {result.label}</h2>
          <p className="muted">Model: {result.model}</p>
          <div className="analysis-grid">
            {Object.entries(result.probabilities).map(([label, prob]) => (
              <div key={label}>
                <span className="label">{label}</span>
                <strong>{prob}%</strong>
                <span className="bar">
                  <span className="bar-fill" style={{ width: `${prob}%` }} />
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </form>
  );
}

/* ------------------------------------------------------------------ */

function SimilarityPanel() {
  const [textA, setTextA] = useState('');
  const [textB, setTextB] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const run = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      setResult(await compareTexts(textA.trim(), textB.trim()));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={run} className="form">
      <label htmlFor="sim-a">Text A</label>
      <textarea
        id="sim-a"
        rows={2}
        value={textA}
        onChange={(e) => setTextA(e.target.value)}
        placeholder="The build pipeline runs on every commit"
      />
      <label htmlFor="sim-b">Text B</label>
      <textarea
        id="sim-b"
        rows={2}
        value={textB}
        onChange={(e) => setTextB(e.target.value)}
        placeholder="CI executes the pipeline for each commit"
      />
      <button type="submit" disabled={loading || !textA.trim() || !textB.trim()}>
        {loading ? 'Comparing...' : 'Compare texts'}
      </button>
      <ErrorMessage message={error} />
      {result && (
        <div className="response-box">
          <h2>{result.similarity}% similar</h2>
          <p>{result.verdict}</p>
          <p className="muted">
            Shared terms: {result.shared_terms.length ? result.shared_terms.join(', ') : 'none'}
          </p>
        </div>
      )}
    </form>
  );
}

/* ------------------------------------------------------------------ */

function GeneratePanel() {
  const [seed, setSeed] = useState('');
  const [maxWords, setMaxWords] = useState(30);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const run = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      setResult(await generateText(seed.trim(), maxWords));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={run} className="form">
      <label htmlFor="gen-seed">Seed word (optional)</label>
      <input
        id="gen-seed"
        type="text"
        value={seed}
        onChange={(e) => setSeed(e.target.value)}
        placeholder="machine"
      />
      <label htmlFor="gen-length">Maximum words: {maxWords}</label>
      <input
        id="gen-length"
        type="range"
        min={5}
        max={100}
        value={maxWords}
        onChange={(e) => setMaxWords(Number(e.target.value))}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Generating...' : 'Generate text'}
      </button>
      <ErrorMessage message={error} />
      {result && (
        <div className="response-box">
          <h2>Generated text</h2>
          <p>{result.text}</p>
          <p className="muted">
            {result.word_count} words{result.seed_used ? ' from your seed' : ' (random start)'}
          </p>
        </div>
      )}
    </form>
  );
}

/* ------------------------------------------------------------------ */

function ClusterPanel() {
  const [texts, setTexts] = useState(SAMPLE_TEXTS);
  const [sentTexts, setSentTexts] = useState(SAMPLE_TEXTS);
  const [k, setK] = useState(2);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const updateText = (index, value) => {
    setTexts((prev) => prev.map((t, i) => (i === index ? value : t)));
  };

  const run = async (e) => {
    e.preventDefault();
    const cleaned = texts.map((t) => t.trim()).filter(Boolean);
    if (cleaned.length < 2) {
      setError('Add at least two documents to cluster.');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      // The API drops empty documents, so keep the exact list that was sent.
      setSentTexts(cleaned);
      setResult(await clusterTexts(cleaned, Math.min(k, cleaned.length)));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={run} className="form">
      <label>Documents</label>
      {texts.map((text, i) => (
        <textarea
          key={i}
          rows={2}
          value={text}
          onChange={(e) => updateText(i, e.target.value)}
          placeholder={`Document ${i + 1}`}
        />
      ))}
      <label htmlFor="cluster-k">Clusters (k): {k}</label>
      <input
        id="cluster-k"
        type="range"
        min={2}
        max={5}
        value={k}
        onChange={(e) => setK(Number(e.target.value))}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Clustering...' : 'Cluster documents'}
      </button>
      <ErrorMessage message={error} />
      {result && (
        <div className="cluster-list">
          {result.clusters.map((cluster) => (
            <div key={cluster.cluster} className="cluster-card">
              <h3>Cluster {cluster.cluster}</h3>
              <p className="muted">Keywords: {cluster.keywords.join(', ')}</p>
              <ul className="feature-list">
                {cluster.members.map((member) => (
                  <li key={member}>{sentTexts[member]}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </form>
  );
}

/* ------------------------------------------------------------------ */

function ErrorMessage({ message }) {
  if (!message) return null;
  return <p className="error-msg">{message}</p>;
}

export default MLLab;
