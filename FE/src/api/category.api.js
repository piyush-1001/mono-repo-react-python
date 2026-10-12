import { apiClient } from './client';
import { ENDPOINTS } from './endpoints';

/**
 * Lists all product categories.
 * @returns {Promise<Array<{ id: string, name: string, code: string, productCount: number }>>}
 */
export async function listCategories() {
  const response = await apiClient.get(ENDPOINTS.listCategories);
  return response.data;
}
