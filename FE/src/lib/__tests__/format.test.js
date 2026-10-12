import { describe, expect, it } from 'vitest';
import {
  formatCurrency,
  formatDateTime,
  formatRelativeTime,
  titleCase,
  maskEmail,
  formatNumber,
} from '@/lib/format';

describe('formatCurrency', () => {
  it('formats a number as INR currency', () => {
    expect(formatCurrency(1234.5)).toBe('₹ 1,234.50');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('₹ 0.00');
  });

  it('respects decimal option', () => {
    expect(formatCurrency(100, { decimals: 0 })).toBe('₹ 100');
  });
});

describe('formatDateTime', () => {
  it('formats a valid ISO date string', () => {
    const result = formatDateTime('2024-03-15T10:30:00Z', 'DD MMM YYYY');
    expect(result).toBe('15 Mar 2024');
  });

  it('returns dash for null', () => {
    expect(formatDateTime(null)).toBe('-');
  });

  it('returns dash for undefined', () => {
    expect(formatDateTime(undefined)).toBe('-');
  });
});

describe('formatRelativeTime', () => {
  it('returns dash for null', () => {
    expect(formatRelativeTime(null)).toBe('-');
  });

  it('returns a relative string for a past date', () => {
    const past = new Date(Date.now() - 3600_000).toISOString();
    expect(formatRelativeTime(past)).toMatch(/ago/);
  });
});

describe('titleCase', () => {
  it('converts a string to title case', () => {
    expect(titleCase('hello world')).toBe('Hello World');
  });

  it('returns empty string for null', () => {
    expect(titleCase(null)).toBe('');
  });

  it('returns empty string for undefined', () => {
    expect(titleCase(undefined)).toBe('');
  });
});

describe('maskEmail', () => {
  it('masks the local part of an email', () => {
    expect(maskEmail('john.doe@example.com')).toMatch(/jo***@example\.com/);
  });

  it('returns dash for null', () => {
    expect(maskEmail(null)).toBe('-');
  });

  it('returns dash for invalid email', () => {
    expect(maskEmail('not-an-email')).toBe('-');
  });
});

describe('formatNumber', () => {
  it('formats with locale thousands separators', () => {
    expect(formatNumber(1234567)).toBe('12,34,567');
  });

  it('returns dash for null', () => {
    expect(formatNumber(null)).toBe('-');
  });

  it('returns dash for undefined', () => {
    expect(formatNumber(undefined)).toBe('-');
  });

  it('respects decimal option', () => {
    expect(formatNumber(1234.567, { decimals: 1 })).toBe('1,234.6');
  });
});
