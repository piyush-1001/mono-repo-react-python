import { QueryClient } from '@tanstack/react-query';
import { useToastContext } from '@/context/ToastContext';

/** @type {import('@tanstack/react-query').QueryClient} */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      throwOnError: false,
    },
    mutations: {
      throwOnError: false,
    },
  },
});

/**
 * Shows a toast for 5xx errors on query failure.
 * Call this in queryClient options via useQuery's `onError`.
 * @param {Error} error
 */
export function showQueryErrorToast(error) {
  try {
    const toast = useToastContext?.();
    if (toast && error?.response?.status >= 500) {
      toast.addToast('Server error — please try again later.', 'error');
    }
  } catch {
    // Context not available (e.g., outside provider) — silently skip
  }
}
