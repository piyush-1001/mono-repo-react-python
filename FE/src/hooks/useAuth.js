import { useAuthContext } from '@/context/AuthContext';

/**
 * Convenience hook wrapping AuthContext for use in components.
 * @returns {import('@/context/AuthContext').AuthContextValue}
 */
export function useAuth() {
  return useAuthContext();
}
