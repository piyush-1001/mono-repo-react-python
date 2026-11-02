import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchDigest } from '../api/client';

// The board written out for a standup, backed by BE/task_digest.py.
//
// The other pages answer questions with a chart or a table. This one produces a
// piece of text, because the thing it is for is pasting into a chat: what is
// done, what is in flight, what has been waiting, and what to pick up next.
// The text comes from the same reports as the other pages, so it cannot say
// something the rest of the app disagrees with.
function StandupDigest() {
  const [digest, setDigest] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setDigest(await fetchDigest());
    } catch (err) {
      setError(err.message);
      setDigest(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const copy = async () => {
    if (!digest?.text) return;
    try {
      await navigator.clipboard.writeText(digest.text);
      setCopied(true);
      // The mark is cleared again shortly, so it never claims to be true long
      // after it stopped being.
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // The clipboard API needs a secure context, which a phone on the local
      // network does not have. Say what to do instead of failing silently.
      setError(
        'The browser would not copy to the clipboard. Select the text and copy it by hand.',
      );
    }
  };

  const stats = digest?.stats;

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Node.js store · Python digest</p>
        <h1>Standup Digest</h1>
        <p className="subtitle">
          The board as plain text, ready to paste into the morning channel.
        </p>

        {loading && <p className="muted">Writing the digest...</p>}
        {error && <p className="error-msg">{error}</p>}

        {stats && !loading && (
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-value">{stats.total}</span>
              <span className="muted">tasks</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.open}</span>
              <span className="muted">open</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.in_progress}</span>
              <span className="muted">in progress</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.stale}</span>
              <span className="muted">stale</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.urgent}</span>
              <span className="muted">read as urgent</span>
            </div>
          </div>
        )}

        {digest && !loading && (
          <div className="response-box">
            <h2>Digest</h2>
            <pre className="export-preview">{digest.text}</pre>
          </div>
        )}

        <div className="form-row">
          <button onClick={copy} disabled={loading || !digest}>
            {copied ? 'Copied' : 'Copy digest'}
          </button>
          <button onClick={load} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <Link to="/export" className="nav-link">
          ← Export Center
        </Link>
      </section>
    </main>
  );
}

export default StandupDigest;
