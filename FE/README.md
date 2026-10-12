# Inventory Dashboard

React 18 + Vite SPA for warehouse/inventory management.

## Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| VITE_API_BASE_URL | http://localhost:8000 | Backend API base URL |
| VITE_APP_TITLE | Inventory Dashboard | Application title |
| VITE_RSA_PUBLIC_KEY | (empty) | RSA public key for encrypting login payloads |

## Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start dev server with HMR |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm run lint` | ESLint |
| `npm run lint:fix` | ESLint with auto-fix |
| `npm run format` | Prettier format |
| `npm run format:check` | Check formatting |
| `npm run test` | Run tests |
| `npm run test:watch` | Watch mode |
| `npm run test:coverage` | Coverage report |

## Architecture

- **Routing**: React Router v6, lazy-loaded pages
- **Server state**: TanStack Query v5
- **API client**: Axios with envelope unwrapping and token refresh
- **Auth**: Context + cookies; login payloads encrypted with RSA+AES
- **Styling**: Plain CSS with custom properties; no CSS framework
