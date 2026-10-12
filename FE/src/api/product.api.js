import { apiClient } from './client';
import { ENDPOINTS } from './endpoints';

/**
 * Lists products with optional filters, pagination, and sorting.
 * @param {{ search?: string, category?: string, status?: string, page?: number, limit?: number, sortBy?: string, sortOrder?: string }} params
 * @returns {Promise<{ items: object[], total: number, page: number, limit: number }>}
 */
export async function listProducts(params = {}) {
  const response = await apiClient.get(ENDPOINTS.listProducts, { params });
  return response.data;
}

/**
 * Fetches a single product by ID.
 * @param {string} productId
 * @returns {Promise<object>}
 */
export async function getProduct(productId) {
  const response = await apiClient.get(ENDPOINTS.getProduct(productId));
  return response.data;
}

/**
 * Creates a new product.
 * @param {{ sku: string, name: string, categoryId: string, unit: string, price: number, costPrice: number, stock: number, reorderLevel: number, description?: string }} body
 * @returns {Promise<object>}
 */
export async function createProduct(body) {
  const response = await apiClient.post(ENDPOINTS.createProduct, body);
  return response.data;
}

/**
 * Updates an existing product (full replace).
 * @param {string} productId
 * @param {object} body
 * @returns {Promise<object>}
 */
export async function updateProduct(productId, body) {
  const response = await apiClient.put(ENDPOINTS.updateProduct(productId), body);
  return response.data;
}

/**
 * Deletes a product.
 * @param {string} productId
 * @returns {Promise<void>}
 */
export async function removeProduct(productId) {
  await apiClient.delete(ENDPOINTS.deleteProduct(productId));
}

/**
 * Records a stock adjustment on a product.
 * @param {string} productId
 * @param {{ quantity: number, movementType: 'IN'|'OUT'|'ADJUST', reason: string }} body
 * @returns {Promise<object>}
 */
export async function adjustStock(productId, body) {
  const response = await apiClient.post(ENDPOINTS.stockAdjustment(productId), body);
  return response.data;
}
