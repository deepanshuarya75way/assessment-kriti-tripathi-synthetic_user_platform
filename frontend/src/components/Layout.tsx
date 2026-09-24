import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to="/" className="brand">
            <span className="brand-mark">◐</span> Synthetic User Research
          </NavLink>
          <nav className="topnav">
            <NavLink to="/" end>
              Dashboard
            </NavLink>
            <NavLink to="/research/new">Create</NavLink>
            <NavLink to="/history">History</NavLink>
          </nav>
          <div className="topbar-user">
            <span className="muted">{user?.email}</span>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
      <footer className="footer">
        <span className="muted">
          Personas and responses are AI-generated (synthetic). Exploratory, not statistically
          representative.
        </span>
      </footer>
    </div>
  );
}
