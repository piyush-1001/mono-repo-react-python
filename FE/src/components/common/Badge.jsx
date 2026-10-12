import clsx from 'clsx';

/**
 * Status/role badge.
 * @param {{ label: string, variant?: 'success'|'danger'|'warning'|'info'|'neutral', size?: 'sm'|'md' }} props
 * @returns {React.ReactElement}
 */
export function Badge({ label, variant = 'neutral', size = 'md' }) {
  return (
    <span className={clsx('badge', `badge--${variant}`, `badge--${size}`)}>
      {label}
    </span>
  );
}
