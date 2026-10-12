import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

/**
 * Top navigation bar with user menu and sign-out.
 * @returns {React.ReactElement}
 */
export function Topbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate('/login', { replace: true });
  }

  return (
    <header className="topbar" role="banner">
      <div className="topbar__brand">
        <span className="topbar__logo" aria-hidden="true">&#128722;</span>
        <span className="topbar__title">
          {import.meta.env.VITE_APP_TITLE || 'Inventory Dashboard'}
        </span>
      </div>

      <div className="topbar__right">
        <div className="topbar__status" title="API connected">
          <span className="topbar__status-dot" aria-hidden="true" />
          <span className="topbar__status-label">Connected</span>
        </div>

        <div className="topbar__user">
          <span className="topbar__user-name">
            {user?.firstName} {user?.lastName}
          </span>
          <span className="topbar__user-role badge badge--info badge--sm">
            {user?.role}
          </span>
          <button
            type="button"
            className="topbar__signout"
            onClick={handleSignOut}
            aria-label="Sign out"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
