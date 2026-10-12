/**
 * Error state for data-backed views.
 * @param {{ message?: string, onRetry?: () => void }} props
 * @returns {React.ReactElement}
 */
export function ErrorState({ message = 'Something went wrong. Please try again.', onRetry }) {
  return (
    <div className="error-state" role="alert">
      <span className="error-state__icon" aria-hidden="true">&#9888;</span>
      <p className="error-state__message">{message}</p>
      {onRetry && (
        <button type="button" className="btn btn--secondary btn--sm" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
