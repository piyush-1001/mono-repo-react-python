import clsx from 'clsx';

/**
 * @param {{ label?: string, error?: string, hint?: string, id?: string, value?: string, onChange?: () => void, disabled?: boolean, required?: boolean, className?: string, children: React.ReactNode }} props
 * @returns {React.ReactElement}
 */
export function Select({
  label, error, hint, id, value, onChange, disabled, required, className, children,
}) {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className={clsx('field', error && 'field--error', className)}>
      {label && (
        <label className="field__label" htmlFor={selectId}>
          {label}
          {required && <span className="field__required" aria-hidden="true"> *</span>}
        </label>
      )}
      <select
        id={selectId}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        className="field__select"
        aria-invalid={!!error}
        aria-describedby={error ? `${selectId}-error` : hint ? `${selectId}-hint` : undefined}
      >
        {children}
      </select>
      {hint && !error && <span id={`${selectId}-hint`} className="field__hint">{hint}</span>}
      {error && <span id={`${selectId}-error`} className="field__error" role="alert">{error}</span>}
    </div>
  );
}
