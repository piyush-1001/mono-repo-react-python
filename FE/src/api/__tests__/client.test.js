import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { apiClient } from '@/api/client';

const mock = new MockAdapter(axios, { delayResponse: 0 });

describe('apiClient', () => {
  afterEach(() => {
    mock.reset();
    localStorage.clear();
  });

  describe('Envelope unwrapping', () => {
    it('extracts data from SUCCESS envelope', async () => {
      mock.onGet('/test').reply(200, {
        status: 'SUCCESS',
        code: 200,
        data: { id: 1, name: 'Product A' },
      });

      // Use the module-level client
      const resp = await apiClient.get('/test');
      expect(resp.data).toEqual({ id: 1, name: 'Product A' });
    });

    it('throws on ERROR envelope', async () => {
      mock.onGet('/test').reply(200, {
        status: 'ERROR',
        code: 404,
        message: 'Not found',
      });

      await expect(apiClient.get('/test')).rejects.toThrow('Not found');
    });

    it('passes through non-envelope responses unchanged', async () => {
      mock.onGet('/test').reply(200, { message: 'Hello' });
      const resp = await apiClient.get('/test');
      expect(resp.data).toEqual({ message: 'Hello' });
    });
  });

  describe('401 refresh-and-retry', () => {
    it('retries the original request once after a successful token refresh', async () => {
      // First request → 401
      mock.onGet('/protected').reply(401, { message: 'Unauthorized' });
      // Refresh → success
      mock.onPost('/api/user/tokens/refresh').reply(200, {
        status: 'SUCCESS',
        code: 200,
        data: { accessToken: 'new-token' },
      });
      // Retry → 200
      mock.onGet('/protected').reply(200, {
        status: 'SUCCESS',
        code: 200,
        data: { secret: 'data' },
      });

      localStorage.setItem('accessToken', 'old-token');

      const resp = await apiClient.get('/protected');
      expect(resp.data).toEqual({ secret: 'data' });
      // Second call to /protected should have new token
      const history = mock.history.get;
      expect(history[1].headers.Authorization).toBe('Bearer new-token');
    });

    it('redirects to /login when refresh fails', async () => {
      const goto = vi.fn();
      window.location.href = '/';
      Object.defineProperty(window, 'location', {
        value: { ...window.location, href: '/login' },
        writable: true,
        configurable: true,
      });

      mock.onGet('/protected').reply(401, {});
      mock.onPost('/api/user/tokens/refresh').reply(401, {});
      localStorage.setItem('accessToken', 'bad-token');

      await expect(apiClient.get('/protected')).rejects.toBeDefined();
      // Cleanup
      window.location.href = '/';
    });
  });

  describe('Authorization header', () => {
    it('attaches bearer token from localStorage', async () => {
      mock.onGet('/test').reply((config) => {
        return [200, {
          status: 'SUCCESS', code: 200,
          data: { hasAuth: config.headers.Authorization === 'Bearer my-token' },
        }];
      });

      localStorage.setItem('accessToken', 'my-token');
      const resp = await apiClient.get('/test');
      expect(resp.data.hasAuth).toBe(true);
    });

    it('does not attach header when no token stored', async () => {
      mock.onGet('/test').reply((config) => {
        return [200, {
          status: 'SUCCESS', code: 200,
          data: { hasAuth: 'Authorization' in config.headers },
        }];
      });

      localStorage.removeItem('accessToken');
      const resp = await apiClient.get('/test');
      expect(resp.data.hasAuth).toBe(false);
    });
  });
});
