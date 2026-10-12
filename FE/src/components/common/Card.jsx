import clsx from 'clsx';

/**
 * Generic card container.
 * @param {{ title?: string, actions?: React.ReactNode, className?: string, children: React.ReactNode }} props
 * @returns {React.ReactElement}
 */
export function Card({ title, actions, className, children }) {
  return (
    <div className={clsx('card', className)}>
      {(title || actions) && (
        <div className="card__header">
          {title && <h3 className="card__title">{title}</h3>}
          {actions && <div className="card__actions">{actions}</div>}
        </div>
      )}
      <div className="card__body">{children}</div>
    </div>
  );
}
