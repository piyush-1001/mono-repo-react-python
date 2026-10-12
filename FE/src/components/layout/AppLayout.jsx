import { Outlet } from 'react-router-dom';
import { Topbar } from './Topbar';
import { Sidebar } from './Sidebar';

/**
 * App shell layout with topbar and sidebar.
 * @returns {React.ReactElement}
 */
export function AppLayout() {
  return (
    <div className="app-layout">
      <Topbar />
      <div className="app-layout__body">
        <Sidebar />
        <main className="app-layout__content" id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
