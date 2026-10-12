/** Application-wide constants. */

/** @type {{ [key: string]: string }} */
export const ROLE = {
  ADMIN: 'ADMIN',
  STAFF: 'STAFF',
  USER: 'USER',
};

/** @type {{ [key: string]: string }} */
export const PRODUCT_STATUS = {
  ACTIVE: 'ACTIVE',
  INACTIVE: 'INACTIVE',
  ARCHIVED: 'ARCHIVED',
};

/** @type {{ [key: string]: 'IN' | 'OUT' | 'ADJUST' }} */
export const MOVEMENT_TYPE = {
  IN: 'IN',
  OUT: 'OUT',
  ADJUST: 'ADJUST',
};

/** @type {Array<{ label: string, to: string, icon: string }>} */
export const NAV_ITEMS = [
  { label: 'Dashboard', to: '/dashboard', icon: 'grid' },
  { label: 'Products', to: '/products', icon: 'box' },
  { label: 'Users', to: '/users', icon: 'users' },
];

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_LIMIT: 20,
  MAX_LIMIT: 100,
};

export const DATE_FORMAT = 'DD MMM YYYY, HH:mm';
