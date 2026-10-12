import { apiClient } from './client';
import { ENDPOINTS } from './endpoints';

/**
 * Signs in a user with encrypted credentials.
 * @param {{ encryptedData: string, encryptedKey: string, iv: string }} payload
 * @returns {Promise<{ accessToken: string, refreshToken: string, expiresIn: number, user: object }>}
 */
export async function signIn(payload) {
  const response = await apiClient.post(ENDPOINTS.signIn, payload);
  return response.data;
}

/**
 * Signs out the current user.
 * @returns {Promise<{ message: string }>}
 */
export async function signOut() {
  const response = await apiClient.post(ENDPOINTS.signOut);
  return response.data;
}

/**
 * Refreshes the session using the httpOnly refresh cookie.
 * @returns {Promise<{ accessToken: string, refreshToken?: string }>}
 */
export async function refreshSession() {
  const response = await apiClient.post(ENDPOINTS.refreshToken);
  return response.data;
}

/**
 * Fetches the currently authenticated user.
 * @returns {Promise<{ id: string, firstName: string, lastName: string, email: string, phone: string, role: string, isActive: boolean, createdAt: string }>}
 */
export async function getSelf() {
  const response = await apiClient.get(ENDPOINTS.getSelf);
  return response.data;
}

/**
 * Creates a new user (ADMIN only).
 * @param {{ encryptedData: string, encryptedKey: string, iv: string }} payload
 * @returns {Promise<{ id: string, email: string, createdAt: string }>}
 */
export async function createUser(payload) {
  const response = await apiClient.post(ENDPOINTS.createUser, payload);
  return response.data;
}

/**
 * Lists users with optional filtering.
 * @param {{ search?: string, page?: number, limit?: number, role?: string }} params
 * @returns {Promise<{ items: object[], total: number, page: number, limit: number }>}
 */
export async function listUsers(params = {}) {
  const response = await apiClient.get(ENDPOINTS.listUsers, { params });
  return response.data;
}

/**
 * Activates or deactivates a user.
 * @param {string} userId
 * @param {{ isActive: boolean }} body
 * @returns {Promise<object>}
 */
export async function patchUserStatus(userId, body) {
  const response = await apiClient.patch(ENDPOINTS.patchUser(userId), body);
  return response.data;
}
