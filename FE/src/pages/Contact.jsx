import { Link } from 'react-router-dom';

function Contact() {
  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Get in Touch</p>
        <h1>Contact</h1>
        <p className="subtitle">
          Have questions about the app? Reach out below.
        </p>

        <form className="form" onSubmit={(e) => e.preventDefault()}>
          <label htmlFor="name">Name</label>
          <input
            id="name"
            type="text"
            placeholder="Your name"
          />

          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            placeholder="your@email.com"
          />

          <label htmlFor="message">Message</label>
          <textarea
            id="message"
            rows={4}
            placeholder="Your message..."
          />

          <button type="submit">Send Message</button>
        </form>

        <Link to="/" className="nav-link">
          ← Back to Analyzer
        </Link>
      </section>
    </main>
  );
}

export default Contact;
