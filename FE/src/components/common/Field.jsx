/**
 * Wrapper for field groups. Just applies the field class to children.
 * @param {{ label?: string, error?: string, hint?: string, className?: string, children: React.ReactNode }} props
 * @returns {React.ReactElement}
 */
export function Field({ label, error, hint, className, children }) {
  return (
    <div className={`field ${error ? 'field--error' : ''} ${className || ''}`}>
      {label && <label className="field__label">{label}</label>}
      {children}
      {hint && !error && <span className="field__hint">{hint}</span>}
      {error && <span className="field__error" role="alert">{error}</span>}
    </div>
  );
}
