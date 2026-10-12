import { useRef } from 'react';
import { Input } from './Input';

/**
 * Search input with debounce.
 * @param {{ value: string, onChange: (v: string) => void, placeholder?: string, debounceMs?: number }} props
 * @returns {React.ReactElement}
 */
export function SearchInput({ value, onChange, placeholder = 'Search...', debounceMs = 300 }) {
  const timerRef = useRef(null);

  function handleChange(e) {
    const val = e.target.value;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => onChange(val), debounceMs);
  }

  return (
    <div className="search-input">
      <span className="search-input__icon" aria-hidden="true">&#128269;</span>
      <input
        type="search"
        defaultValue={value}
        placeholder={placeholder}
        className="search-input__field"
        onChange={handleChange}
        aria-label={placeholder}
      />
    </div>
  );
}
