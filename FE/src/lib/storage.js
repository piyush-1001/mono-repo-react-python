const PREFIX = 'inv_';

/**
 * Namespaced localStorage helpers.
 * @namespace
 */
export const storage = {
  /**
   * @param {string} key
   * @param {string} [value]
   * @returns {string|null}
   */
  get(key, value) {
    try {
      if (value !== undefined) {
        localStorage.setItem(PREFIX + key, value);
        return null;
      }
      return localStorage.getItem(PREFIX + key);
    } catch {
      return null;
    }
  },

  /**
   * @param {string} key
   * @param {unknown} value
   */
  set(key, value) {
    try {
      localStorage.setItem(PREFIX + key, JSON.stringify(value));
    } catch {
      // quota exceeded or unavailable
    }
  },

  /**
   * @param {string} key
   */
  remove(key) {
    try {
      localStorage.removeItem(PREFIX + key);
    } catch {
      // ignore
    }
  },

  clear() {
    try {
      Object.keys(localStorage)
        .filter((k) => k.startsWith(PREFIX))
        .forEach((k) => localStorage.removeItem(k));
    } catch {
      // ignore
    }
  },
};
