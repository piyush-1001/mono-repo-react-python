/**
 * Page-level header with title and optional actions.
 * @param {{ title: string, subtitle?: string, actions?: React.ReactNode, breadcrumbs?: Array<{ label: string, to?: string }> }} props
 * @returns {React.ReactElement}
 */
export function PageHeader({ title, subtitle, actions, breadcrumbs }) {
  return (
    <div className="page-header">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="page-header__breadcrumbs" aria-label="Breadcrumb">
          {breadcrumbs.map((crumb, i) => (
            <span key={i} className="page-header__breadcrumb-item">
              {crumb.to ? (
                <a href={crumb.to} className="page-header__breadcrumb-link">{crumb.label}</a>
              ) : (
                <span className="page-header__breadcrumb-current">{crumb.label}</span>
              )}
              {i < breadcrumbs.length - 1 && (
                <span className="page-header__breadcrumb-sep" aria-hidden="true"> / </span>
              )}
            </span>
          ))}
        </nav>
      )}
      <div className="page-header__main">
        <div className="page-header__text">
          <h1 className="page-header__title">{title}</h1>
          {subtitle && <p className="page-header__subtitle">{subtitle}</p>}
        </div>
        {actions && <div className="page-header__actions">{actions}</div>}
      </div>
    </div>
  );
}
