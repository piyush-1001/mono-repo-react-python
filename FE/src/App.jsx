import { useState } from 'react';

function App() {
  const [message, setMessage] = useState('Hello from the frontend');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse('');

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
    } catch (error) {
      setResponse('Error connecting to backend: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">React + FastAPI</p>
        <h1>Simple One Page App</h1>
        <p className="subtitle">
          Send a message from the frontend to the Python FastAPI backend.
        </p>

        <form onSubmit={handleSubmit} className="form">
          <label htmlFor="message">Your message</label>
          <input
            id="message"
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type something..."
          />

          <button type="submit" disabled={loading}>
            {loading ? 'Sending...' : 'Send to backend'}
          </button>
        </form>

        <div className="response-box">
          <h2>Backend response</h2>
          <p>{response || 'Waiting for a response...'}</p>
        </div>
      </section>
    </main>
  );
}

export default App;
