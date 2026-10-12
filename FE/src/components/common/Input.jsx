import clsx from 'clsx';

/**
 * Text input component.
 * @param {{ label?: string, error?: string, hint?: string, id?: string, type?: string, placeholder?: string, value?: string, onChange?: () => void, disabled?: boolean, required?: boolean, className?: string, inputClassName?: string }} props
 * @returns {React.ReactElement}
 */
export function Input({
  label,
  error,
  hint,
  id,
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled,
  required,
  className,
  inputClassName,
  ...rest
}) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className={clsx('field', error && 'field--error', className)}>
      {label && (
        <label className="field__label" htmlFor={inputId}>
          {label}
          {required && <span className="field__required" aria-hidden="true"> *</span>}
        </label>
      )}
      <input
        id={inputId}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        className={clsx('field__input', inputClassName)}
        aria-invalid={!!error}
        aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
        {...rest}
      />
      {hint && !error && (
        <span id={`${inputId}-hint`} className="field__hint">{hint}</span>
      )}
      {error && (
        <span id={`${inputId}-error`} className="field__error" role="alert">{error}</span>
      )}
    </div>
  );
}
