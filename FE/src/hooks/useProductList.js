import { useQuery } from '@tanstack/react-query';
import { listProducts } from '@/api/product.api';

/**
 * useQuery wrapper for the product list with filter + pagination key.
 * @param {{ search?: string, category?: string, status?: string, page?: number, limit?: number, sortBy?: string, sortOrder?: string }} params
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useProductList(params) {
  return useQuery({
    queryKey: ['products', params],
    queryFn: () => listProducts(params),
    placeholderData: (prev) => prev,
    staleTime: 1000 * 30,
  });
}
