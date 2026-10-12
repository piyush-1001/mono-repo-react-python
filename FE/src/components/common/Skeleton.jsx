import clsx from 'clsx';

/**
 * Skeleton loading placeholder.
 * @param {{ width?: string, height?: string, variant?: 'text'|'rect'|'circle', className?: string }} props
 * @returns {React.ReactElement}
 */
export function Skeleton({ width, height, variant = 'rect', className }) {
  return (
    <span
      className={clsx('skeleton', `skeleton--${variant}`, className)}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}
