import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchTasks, discoverTopics } from '../api/client';

// A page over the LSA model in BE/lsa_topic_model.py.
//
// The point of latent semantic analysis is that the topics it reports are not
// in the documents as written: "deploy", "staging" and "rollback" end up in one
// topic because the documents mentioning them use the same words. A task board
// is a small, real corpus for that, and the words it produces describe what
// the board is actually about.
function TopicLab() {
  const [titles, setTitles] = useState([]);
  const [pasted, setPasted] = useState('');
  const [topicCount, setTopicCount] = useState(2);
  const [corpus, setCorpus] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // The task titles are the natural corpus: they are the text this app already
  // has, and no upload is needed to analyse it.
  const loadTitles = useCallback(async () => {
    try {
      const tasks = await fetchTasks();
      setTitles(tasks.map((task) => task.title));
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    loadTitles();
  }, [loadTitles]);

  // One document per line. A pasted block is far less work than a file upload,
  // and the corpus is small by design.
  const pastedLines = pasted
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  const analyse = async () => {
    const documents = pastedLines.length > 0 ? pastedLines : titles;

    // The server enforces this too (two non-empty documents), but saying it
    // here saves a round trip and names the fix.
    if (documents.length < 2) {
      setError('Need at least two documents: add tasks, or paste one per line.');
      setResult(null);
      return;
    }

    setLoading(true);
    setError('');
    try {
      const data = await discoverTopics(documents, topicCount);
      // The corpus is kept because the model reports its documents by index
      // into the list that was sent, and only this page knows what those were.
      setCorpus(documents);
      setResult(data);
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const topics = result?.topics || [];

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Python · Latent Semantic Analysis</p>
        <h1>Topic Lab</h1>
        <p className="subtitle">
          LSA finds the topics behind a set of documents. By default it reads the
          task titles from the Node.js API; paste one document per line to run it
          over anything else.
        </p>

        <div className="form">
          <label htmlFor="corpus">Documents (one per line)</label>
          <textarea
            id="corpus"
            rows={5}
            value={pasted}
            onChange={(e) => setPasted(e.target.value)}
            placeholder={titles.slice(0, 3).join('\n') || 'Write unit tests\nBuild the Node.js API'}
          />
          <p className="muted">
            {pastedLines.length > 0
              ? `Using ${pastedLines.length} pasted document(s).`
              : `Using ${titles.length} task title(s) from the Node.js API.`}
          </p>
        </div>

        <div className="form-row">
          <label htmlFor="topic-count">Topics: {topicCount}</label>
          <input
            id="topic-count"
            type="range"
            min="1"
            max="5"
            value={topicCount}
            onChange={(e) => setTopicCount(Number(e.target.value))}
          />
          <button onClick={analyse} disabled={loading}>
            {loading ? 'Analysing...' : 'Extract topics'}
          </button>
        </div>

        {error && <p className="error-msg">{error}</p>}

        {result && (
          <div className="response-box">
            <h2>
              {topics.length} topic{topics.length === 1 ? '' : 's'} over{' '}
              {result.documents} document{result.documents === 1 ? '' : 's'}
            </h2>

            {result.received !== result.documents && (
              <p className="muted">
                {result.received} were posted, {result.documents} were fitted.
              </p>
            )}
            {(result.notes || []).map((note) => (
              <p className="muted" key={note}>
                {note}
              </p>
            ))}

            <div className="topic-list">
              {topics.map((topic) => (
                <div className="topic-card" key={topic.topic}>
                  <h3>
                    Topic {topic.topic + 1}
                    <span className="muted"> strength {topic.singular_value}</span>
                  </h3>

                  <div className="term-chips">
                    {topic.keywords.map((keyword) => (
                      <span className="term-chip" key={keyword.term}>
                        {keyword.term}
                        <span className="muted"> {keyword.weight}</span>
                      </span>
                    ))}
                  </div>

                  <ul className="feature-list">
                    {topic.documents.map((doc) => (
                      <li key={doc.index}>
                        {corpus[doc.index] || `document ${doc.index + 1}`}{' '}
                        <span className="muted">({doc.weight})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {!result && !loading && !error && (
          <p className="empty-msg">Nothing analysed yet.</p>
        )}

        <Link to="/models" className="nav-link">
          ← Models
        </Link>
      </section>
    </main>
  );
}

export default TopicLab;
