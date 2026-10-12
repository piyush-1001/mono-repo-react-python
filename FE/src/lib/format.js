import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/en';

dayjs.extend(relativeTime);
dayjs.locale('en');

/**
 * Formats a number as INR currency.
 * @param {number} amount
 * @param {{ decimals?: number }} [options]
 * @returns {string}
 */
export function formatCurrency(amount, options = {}) {
  const { decimals = 2 } = options;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(amount);
}

/**
 * Formats a date string using dayjs.
 * @param {string | Date | null | undefined} value
 * @param {string} [format]
 * @returns {string}
 */
export function formatDateTime(value, format = 'DD MMM YYYY, HH:mm') {
  if (!value) return '-';
  return dayjs(value).format(format);
}

/**
 * Formats a date as a relative time string (e.g. "2 hours ago").
 * @param {string | Date | null | undefined} value
 * @returns {string}
 */
export function formatRelativeTime(value) {
  if (!value) return '-';
  return dayjs(value).fromNow();
}

/**
 * Converts a string to Title Case.
 * @param {string | null | undefined} str
 * @returns {string}
 */
export function titleCase(str) {
  if (!str) return '';
  return str.replace(/\w\S*/g, (txt) =>
    txt.charAt(0).toUpperCase() + txt.slice(1).toLowerCase(),
  );
}

/**
 * Masks an email address, showing only first 2 chars and domain.
 * @param {string | null | undefined} email
 * @returns {string}
 */
export function maskEmail(email) {
  if (!email || !email.includes('@')) return '-';
  const [local, domain] = email.split('@');
  const maskedLocal = local.length > 2 ? local.slice(0, 2) + '***' : local[0] + '***';
  return `${maskedLocal}@${domain}`;
}

/**
 * Formats a number with locale-aware thousands separators.
 * @param {number | null | undefined} value
 * @param {{ decimals?: number }} [options]
 * @returns {string}
 */
export function formatNumber(value, options = {}) {
  if (value === null || value === undefined) return '-';
  const { decimals = 0 } = options;
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}
