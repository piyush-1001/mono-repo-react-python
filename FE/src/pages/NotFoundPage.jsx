import { Link } from 'react-router-dom';

/**
 * 404 — page not found.
 * @returns {React.ReactElement}
 */
export function NotFoundPage() {
  return (
    <div className="not-found-page">
      <h1 className="not-found-page__code">404</h1>
      <p className="not-found-page__message">Page not found.</p>
      <Link to="/" className="btn btn--primary">Go to Dashboard</Link>
    </div>
  );
}
