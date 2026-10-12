import clsx from 'clsx';

/**
 * Loading spinner.
 * @param {{ size?: 'sm'|'md'|'lg', className?: string }} props
 * @returns {React.ReactElement}
 */
export function Spinner({ size = 'md', className }) {
  return (
    <span
      className={clsx('spinner', `spinner--${size}`, className)}
      role="status"
      aria-label="Loading"
    />
  );
}
