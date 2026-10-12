/**
 * Empty state for lists and tables.
 * @param {{ icon?: string, title: string, description?: string, action?: React.ReactNode }} props
 * @returns {React.ReactElement}
 */
export function EmptyState({ icon, title, description, action }) {
  return (
    <div className="empty-state" role="status">
      {icon && <span className="empty-state__icon" aria-hidden="true">{icon}</span>}
      <p className="empty-state__title">{title}</p>
      {description && <p className="empty-state__description">{description}</p>}
      {action && <div className="empty-state__action">{action}</div>}
    </div>
  );
}
