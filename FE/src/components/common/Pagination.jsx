import { Button } from './Button';

/**
 * Pagination controls.
 * @param {{ page: number, totalPages: number, total: number, limit: number, onPageChange: (p: number) => void, onLimitChange?: (l: number) => void }} props
 * @returns {React.ReactElement}
 */
export function Pagination({ page, totalPages, total, limit, onPageChange, onLimitChange }) {
  if (totalPages <= 1 && total <= limit) return null;

  const from = (page - 1) * limit + 1;
  const to = Math.min(page * limit, total);

  return (
    <div className="pagination" role="navigation" aria-label="Pagination">
      <span className="pagination__info" aria-live="polite">
        Showing {from}–{to} of {total}
      </span>

      <div className="pagination__controls">
        <Button
          variant="secondary"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          &larr; Prev
        </Button>

        <span className="pagination__pages" aria-label={`Page ${page} of ${totalPages}`}>
          {page} / {totalPages}
        </span>

        <Button
          variant="secondary"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          Next &rarr;
        </Button>
      </div>

      {onLimitChange && (
        <label className="pagination__limit">
          Per page:
          <select
            value={limit}
            onChange={(e) => onLimitChange(Number(e.target.value))}
            aria-label="Items per page"
          >
            {[10, 20, 50, 100].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>
      )}
    </div>
  );
}
