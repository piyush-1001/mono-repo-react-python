import { forwardRef } from 'react';
import clsx from 'clsx';

/**
 * @typedef {object} ButtonProps
 * @property {'button'|'submit'|'reset'} [type]
 * @property {'primary'|'secondary'|'danger'|'ghost'} [variant]
 * @property {'sm'|'md'|'lg'} [size]
 * @property {boolean} [disabled]
 * @property {boolean} [loading]
 * @property {React.ReactNode} children
 * @property {string} [className]
 * @property {React.ButtonHTMLAttributes<HTMLButtonElement>} [rest]
 */

/**
 * Generic button component.
 * @type {React.ForwardRefExoticComponent<ButtonProps & React.RefAttributes<HTMLButtonElement>>}
 */
export const Button = forwardRef(function Button(
  { type = 'button', variant = 'primary', size = 'md', disabled, loading, children, className, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      className={clsx('btn', `btn--${variant}`, `btn--${size}`, loading && 'btn--loading', className)}
      {...rest}
    >
      {loading && <span className="btn__spinner" aria-hidden="true" />}
      <span className={clsx(loading && 'btn__text--hidden')}>{children}</span>
    </button>
  );
});
