import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/** @type {axios.AxiosInstance} */
export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

let isRefreshing = false;
let refreshQueue = [];

/**
 * Processes the refresh queue after token refresh completes.
 * @param {string|null} token - New access token, or null if refresh failed
 */
function processRefreshQueue(token) {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (token) resolve(token);
    else reject(new axios.Cancel('Token refresh failed'));
  });
  refreshQueue = [];
}

/**
 * Global request interceptor — attaches Authorization bearer token if present.
 */
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Global response interceptor — unwraps {status, code, data} envelope.
 * On 401, queues requests and triggers a single token refresh.
 */
apiClient.interceptors.response.use(
  (response) => {
    if (response.data && 'status' in response.data) {
      if (response.data.status === 'ERROR') {
        const err = new Error(response.data.message || 'Request failed');
        err.response = response;
        err.isServerError = true;
        return Promise.reject(err);
      }
      return { ...response, data: response.data.data };
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const resp = await axios.post(
          `${BASE_URL}/api/user/tokens/refresh`,
          {},
          { withCredentials: true },
        );
        const { accessToken } = resp.data?.data || {};
        if (accessToken) {
          localStorage.setItem('accessToken', accessToken);
          processRefreshQueue(accessToken);
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return apiClient(originalRequest);
        }
        processRefreshQueue(null);
        localStorage.removeItem('accessToken');
        window.location.href = '/login';
        return Promise.reject(error);
      } catch {
        processRefreshQueue(null);
        localStorage.removeItem('accessToken');
        window.location.href = '/login';
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);
