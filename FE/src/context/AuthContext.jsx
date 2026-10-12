import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as authApi from '@/api/auth.api';
import { encryptPayload, getPublicKey } from '@/lib/encryption';
import { storage } from '@/lib/storage';

/** @type {React.Context<import('@/context/AuthContext').AuthContextValue|null>} */
const AuthContext = createContext(null);

/**
 * @typedef {object} AuthContextValue
 * @property {object|null} user
 * @property {boolean} isAuthenticated
 * @property {boolean} isSubmitting
 * @property {string|null} error
 * @property {(email: string, password: string) => Promise<void>} signIn
 * @property {() => Promise<void>} signOut
 * @property {() => Promise<void>} refreshSession
 */

/**
 * Provides authentication state and actions to the app tree.
 * @param {{ children: React.ReactNode }} props
 * @returns {React.ReactElement}
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(/** @type {object|null} */ (null));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(/** @type {string|null} */ (null));

  const isAuthenticated = useMemo(() => !!user, [user]);

  /** Attempts to restore session from stored token. */
  const refreshSession = useCallback(async () => {
    try {
      const { accessToken } = await authApi.refreshSession();
      storage.set('accessToken', accessToken);
      const me = await authApi.getSelf();
      setUser(me);
    } catch {
      storage.remove('accessToken');
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const token = storage.get('accessToken');
    if (token) {
      refreshSession();
    }
  }, [refreshSession]);

  /**
   * Signs in with email + password (encrypted payload).
   * @param {string} email
   * @param {string} password
   */
  const signIn = useCallback(async (email, password) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const publicKey = getPublicKey();
      const encrypted = encryptPayload({ email, password }, publicKey);
      const data = await authApi.signIn(encrypted);
      storage.set('accessToken', data.accessToken);
      setUser(data.user);
    } catch (err) {
      const msg = err?.response?.data?.message || err?.message || 'Sign-in failed';
      setError(msg);
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  /** Signs out and clears local state. */
  const signOut = useCallback(async () => {
    try {
      await authApi.signOut();
    } catch {
      // Ignore server errors on sign-out
    } finally {
      storage.remove('accessToken');
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, isAuthenticated, isSubmitting, error, signIn, signOut, refreshSession }),
    [user, isAuthenticated, isSubmitting, error, signIn, signOut, refreshSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Returns the auth context value. Throws if used outside AuthProvider.
 * @returns {AuthContextValue}
 */
export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider');
  return ctx;
}
