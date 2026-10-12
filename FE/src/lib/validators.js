/**
 * Validation helpers. Each function returns an error message string or null.
 */

/**
 * Checks that a value is present (not empty string or nullish).
 * @param {unknown} value
 * @param {string} [fieldName]
 * @returns {string|null}
 */
export function required(value, fieldName = 'Field') {
  if (value === null || value === undefined || String(value).trim() === '') {
    return `${fieldName} is required`;
  }
  return null;
}

/**
 * Validates an email address format.
 * @param {string} value
 * @returns {string|null}
 */
export function email(value) {
  if (!value) return null;
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(value)) {
    return 'Enter a valid email address';
  }
  return null;
}

/**
 * Checks that a number is positive.
 * @param {unknown} value
 * @param {string} [fieldName]
 * @returns {string|null}
 */
export function positiveNumber(value, fieldName = 'Value') {
  if (value === null || value === undefined || value === '') return null;
  const num = Number(value);
  if (isNaN(num) || num < 0) {
    return `${fieldName} must be a positive number`;
  }
  return null;
}

/**
 * Measures password strength on a 0–4 scale.
 * @param {string} password
 * @returns {{ score: number, label: string, color: string }}
 */
export function passwordStrength(password) {
  if (!password) return { score: 0, label: 'Empty', color: 'var(--color-danger)' };

  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  const levels = [
    { score: 0, label: 'Empty', color: 'var(--color-danger)' },
    { score: 1, label: 'Weak', color: 'var(--color-danger)' },
    { score: 2, label: 'Fair', color: 'var(--color-warning)' },
    { score: 3, label: 'Good', color: 'var(--color-info)' },
    { score: 4, label: 'Strong', color: 'var(--color-success)' },
  ];

  return levels[score] || levels[0];
}

/**
 * Runs an object of validators against a values object.
 * @param {Record<string, (value: unknown) => string | null>} validators
 * @param {Record<string, unknown>} values
 * @returns {{ errors: Record<string, string>, hasErrors: boolean }}
 */
export function runValidators(validators, values) {
  /** @type {Record<string, string>} */
  const errors = {};

  for (const [field, fn] of Object.entries(validators)) {
    const result = fn(values[field]);
    if (result) {
      errors[field] = result;
    }
  }

  return { errors, hasErrors: Object.keys(errors).length > 0 };
}
