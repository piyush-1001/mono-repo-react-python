import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

/** @type {React.Context<import('@/context/ToastContext').ToastContextValue|null>} */
const ToastContext = createContext(null);

const DEFAULT_DURATION = 4000;

/**
 * @typedef {object} Toast
 * @property {string} id
 * @property {string} message
 * @property {'success'|'error'|'warning'|'info'} variant
 * @property {number} duration
 */

/**
 * Provides toast notification state and actions to the app tree.
 * @param {{ children: React.ReactNode }} props
 * @returns {React.ReactElement}
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState(/** @type {Toast[]} */ ([]));
  const counterRef = useRef(0);

  /**
   * Adds a toast notification.
   * @param {string} message
   * @param {'success'|'error'|'warning'|'info'} [variant]
   * @param {number} [duration]
   * @returns {string} toast id
   */
  const addToast = useCallback((message, variant = 'info', duration = DEFAULT_DURATION) => {
    const id = String(++counterRef.current);
    setToasts((prev) => [...prev, { id, message, variant, duration }]);
    return id;
  }, []);

  /**
   * Removes a toast by id.
   * @param {string} id
   */
  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const value = useMemo(() => ({ addToast, removeToast }), [addToast, removeToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

/**
 * Renders the visible toast stack at the bottom-right of the viewport.
 * @param {{ toasts: Toast[], onRemove: (id: string) => void }} props
 * @returns {React.ReactElement}
 */
function ToastViewport({ toasts, onRemove }) {
  return (
    <div className="toast-viewport" role="region" aria-label="Notifications" aria-live="polite">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

/**
 * @param {{ toast: Toast, onRemove: (id: string) => void }} props
 * @returns {React.ReactElement}
 */
function ToastItem({ toast, onRemove }) {
  const timerRef = useRef(/** @type {ReturnType<typeof setTimeout>|null} */ (null));

  useEffect(() => {
    if (toast.duration > 0) {
      timerRef.current = setTimeout(() => onRemove(toast.id), toast.duration);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [toast, onRemove]);

  return (
    <div
      className={`toast toast--${toast.variant}`}
      role="alert"
      aria-atomic="true"
    >
      <span className="toast__message">{toast.message}</span>
      <button
        className="toast__close"
        onClick={() => onRemove(toast.id)}
        aria-label="Dismiss notification"
      >
        &times;
      </button>
    </div>
  );
}

/**
 * Returns the toast context value. Throws if used outside ToastProvider.
 * @returns {ToastContextValue}
 */
export function useToastContext() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToastContext must be used within ToastProvider');
  return ctx;
}

/**
 * @typedef {object} ToastContextValue
 * @property {(message: string, variant?: string, duration?: number) => string} addToast
 * @property {(id: string) => void} removeToast
 */
