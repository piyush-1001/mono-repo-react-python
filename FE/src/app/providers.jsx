import { lazy, Suspense } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from '@/context/ToastContext';
import { AuthProvider } from '@/context/AuthContext';
import { queryClient } from '@/app/queryClient';
import { routes } from '@/app/routes';
import { Spinner } from '@/components/common';

/**
 * Root providers wrapper — sets up all app-level context providers.
 * @returns {React.ReactElement}
 */
export function AppProviders() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <Suspense fallback={<div className="app-loader"><Spinner size="lg" /></div>}>
              {routes}
            </Suspense>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
