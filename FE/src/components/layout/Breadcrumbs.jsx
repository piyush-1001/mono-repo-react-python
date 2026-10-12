/**
 * Breadcrumb navigation trail.
 * @param {{ items: Array<{ label: string, to?: string }> }} props
 * @returns {React.ReactElement}
 */
export function Breadcrumbs({ items }) {
  if (!items || items.length === 0) return null;

  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <ol className="breadcrumbs__list">
        {items.map((item, i) => (
          <li key={i} className="breadcrumbs__item">
            {item.to && i < items.length - 1 ? (
              <a href={item.to} className="breadcrumbs__link">{item.label}</a>
            ) : (
              <span className="breadcrumbs__current" aria-current="page">{item.label}</span>
            )}
            {i < items.length - 1 && (
              <span className="breadcrumbs__sep" aria-hidden="true"> / </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
