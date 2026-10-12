import { describe, expect, it } from 'vitest';
import {
  required,
  email,
  positiveNumber,
  passwordStrength,
  runValidators,
} from '@/lib/validators';

describe('required', () => {
  it('returns null when value is present', () => {
    expect(required('hello', 'Name')).toBeNull();
  });

  it('returns error message for empty string', () => {
    expect(required('', 'Name')).toBe('Name is required');
  });

  it('returns error message for null', () => {
    expect(required(null, 'Name')).toBe('Name is required');
  });

  it('returns error message for undefined', () => {
    expect(required(undefined, 'Name')).toBe('Name is required');
  });

  it('returns error message for whitespace-only string', () => {
    expect(required('   ', 'Name')).toBe('Name is required');
  });
});

describe('email', () => {
  it('returns null for valid email', () => {
    expect(email('test@example.com')).toBeNull();
  });

  it('returns error for invalid email', () => {
    expect(email('not-an-email')).toBe('Enter a valid email address');
  });

  it('returns null for empty value (use required separately)', () => {
    expect(email('')).toBeNull();
  });
});

describe('positiveNumber', () => {
  it('returns null for positive number', () => {
    expect(positiveNumber(42)).toBeNull();
  });

  it('returns null for zero', () => {
    expect(positiveNumber(0)).toBeNull();
  });

  it('returns error for negative number', () => {
    expect(positiveNumber(-5)).toBe('Value must be a positive number');
  });

  it('returns null for empty value', () => {
    expect(positiveNumber('')).toBeNull();
  });

  it('returns error for NaN', () => {
    expect(positiveNumber('abc')).toBe('Value must be a positive number');
  });
});

describe('passwordStrength', () => {
  it('returns Empty for null', () => {
    const r = passwordStrength(null);
    expect(r.score).toBe(0);
    expect(r.label).toBe('Empty');
  });

  it('returns Weak for short password', () => {
    const r = passwordStrength('abc');
    expect(r.score).toBeLessThanOrEqual(1);
  });

  it('returns Strong for complex password', () => {
    const r = passwordStrength('Abc123!@#');
    expect(r.score).toBe(4);
    expect(r.label).toBe('Strong');
  });

  it('returns color from CSS variable', () => {
    const r = passwordStrength('abc');
    expect(r.color).toMatch(/^var\(--color-/);
  });
});

describe('runValidators', () => {
  it('returns empty errors when all validators pass', () => {
    const result = runValidators({ email, required }, { email: 'a@b.com', required: 'yes' });
    expect(result.hasErrors).toBe(false);
    expect(Object.keys(result.errors)).toHaveLength(0);
  });

  it('returns errors when validators fail', () => {
    const result = runValidators({ email: (v) => email(v) }, { email: 'bad' });
    expect(result.hasErrors).toBe(true);
    expect(result.errors.email).toBeTruthy();
  });

  it('skips validation when field is absent', () => {
    const validators = { email };
    const result = runValidators(validators, {});
    expect(result.hasErrors).toBe(false);
  });
});
