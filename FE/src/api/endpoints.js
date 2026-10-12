/** Single source of truth for all API endpoint paths and query-key factories. */

export const ENDPOINTS = {
  // Auth
  signIn: '/api/user/sign-in',
  signOut: '/api/user/sign-out',
  refreshToken: '/api/user/tokens/refresh',
  getSelf: '/api/user/self',
  createUser: '/api/user',
  listUsers: '/api/user',
  patchUser: (userId) => `/api/user/${userId}`,

  // Products
  listProducts: '/api/product',
  createProduct: '/api/product',
  getProduct: (productId) => `/api/product/${productId}`,
  updateProduct: (productId) => `/api/product/${productId}`,
  deleteProduct: (productId) => `/api/product/${productId}`,
  stockAdjustment: (productId) => `/api/product/${productId}/stock-adjustment`,

  // Categories
  listCategories: '/api/category',

  // Health
  health: '/health',
};

/** @typedef {'users' | 'user' | 'products' | 'product' | 'categories' | 'self' | string} QueryKey */
