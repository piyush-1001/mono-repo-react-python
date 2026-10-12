import clsx from 'clsx';

/**
 * @param {{ label?: string, error?: string, hint?: string, id?: string, placeholder?: string, value?: string, onChange?: () => void, disabled?: boolean, required?: boolean, rows?: number, className?: string }} props
 * @returns {React.ReactElement}
 */
export function Textarea({
  label, error, hint, id, placeholder, value, onChange, disabled, required, rows = 4, className,
}) {
  const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className={clsx('field', error && 'field--error', className)}>
      {label && (
        <label className="field__label" htmlFor={textareaId}>
          {label}
          {required && <span className="field__required" aria-hidden="true"> *</span>}
        </label>
      )}
      <textarea
        id={textareaId}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        rows={rows}
        className="field__textarea"
        aria-invalid={!!error}
        aria-describedby={error ? `${textareaId}-error` : hint ? `${textareaId}-hint` : undefined}
      />
      {hint && !error && <span id={`${textareaId}-hint`} className="field__hint">{hint}</span>}
      {error && <span id={`${textareaId}-error`} className="field__error" role="alert">{error}</span>}
    </div>
  );
}
