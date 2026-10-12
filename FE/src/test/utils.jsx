import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

/**
 * Renders a component with all required providers for testing.
 * @param {React.ReactElement} ui
 * @param {{ wrapper?: React.ComponentType, queryClient?: QueryClient, routerOptions?: object }} [options]
 * @returns {import('@testing-library/react').RenderResult}
 */
export function renderWithProviders(
  ui,
  {
    wrapper: WrapperComponent,
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    }),
    routerOptions = {},
  } = {},
) {
  function DefaultWrapper({ children }) {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter {...routerOptions}>{children}</BrowserRouter>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: WrapperComponent || DefaultWrapper });
}

/**
 * Creates a pre-configured QueryClient for testing.
 * @param {{ queries?: object, mutations?: object }} [overrides]
 * @returns {QueryClient}
 */
export function createTestQueryClient(overrides = {}) {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, ...overrides?.queries },
      mutations: { retry: false, ...overrides?.mutations },
    },
  });
}
