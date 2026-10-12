import clsx from 'clsx';

/**
 * Icon-only button for toolbar actions.
 * @param {{ icon: string, label: string, variant?: 'primary'|'secondary'|'danger'|'ghost', size?: 'sm'|'md'|'lg', disabled?: boolean, loading?: boolean, onClick?: () => void, className?: string }} props
 * @returns {React.ReactElement}
 */
export function IconButton({ icon, label, variant = 'ghost', size = 'md', disabled, loading, onClick, className }) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      onClick={onClick}
      className={clsx('icon-btn', `icon-btn--${variant}`, `icon-btn--${size}`, loading && 'icon-btn--loading', className)}
      aria-label={label}
      title={label}
    >
      <span className="icon-btn__icon" aria-hidden="true">{icon}</span>
    </button>
  );
}
