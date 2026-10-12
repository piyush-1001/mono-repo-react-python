import { useEffect, useState } from 'react';

/**
 * Debounces a value by the given delay.
 * @template T
 * @param {T} value
 * @param {number} delay - milliseconds
 * @returns {T}
 */
export function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
