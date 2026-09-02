import React, { useEffect, useState } from 'react';
import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import Accounts from './pages/Accounts';
import Transactions from './pages/Transactions';
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import MFA from './pages/MFA';
import Budgets from './pages/Budgets';
import { Categories, Goals, Profile, Recurring, Reports } from './pages/Hubs';
import api from './api';
import { Avatar, Button, Icon, Modal } from './components/UI';

const nav = [
  [
    'MAIN',
    [
      ['/', 'overview', 'Overview'],
      ['/accounts', 'accounts', 'Accounts'],
      ['/transactions', 'transactions', 'Transactions'],
      ['/budgets', 'budgets', 'Budgets'],
      ['/reports', 'reports', 'Reports'],
    ],
  ],
  [
    'MANAGEMENT',
    [
      ['/categories', 'categories', 'Categories'],
      ['/recurring', 'recurring', 'Recurring transactions'],
      ['/goals', 'goals', 'Goals'],
    ],
  ],
];

const pageTitles = {
  '/': 'Overview',
  '/accounts': 'Accounts',
  '/transactions': 'Transactions',
  '/budgets': 'Budgets',
  '/reports': 'Reports',
  '/categories': 'Categories',
  '/recurring': 'Recurring transactions',
  '/goals': 'Goals',
  '/profile': 'Profile',
  '/profile/general': 'General',
  '/profile/notifications': 'Notifications',
  '/profile/appearance': 'Appearance',
  '/profile/privacy': 'Privacy',
  '/profile/security': 'Security',
  '/profile/login-activity': 'Login activity',
};
const THEME_STORAGE_KEY = 'pocketly-theme';

function Shell() {
  const [open, setOpen] = useState(false);
  const [menu, setMenu] = useState(false);
  const [confirmSignout, setConfirmSignout] = useState(false);
  const loc = useLocation();
  const navg = useNavigate();

  useEffect(() => {
    const theme = localStorage.getItem(THEME_STORAGE_KEY) || 'system';
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const applyTheme = () => {
      const isDark = theme === 'dark' || (theme === 'system' && mediaQuery.matches);
      document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
    };

    applyTheme();
    if (theme === 'system') mediaQuery.addEventListener('change', applyTheme);
    return () => mediaQuery.removeEventListener('change', applyTheme);
  }, []);
  const me = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get('auth/me/').then((r) => r.data),
  });

  const performSignout = async () => {
    try {
      const refresh = localStorage.getItem('refresh');
      if (refresh) {
        await api.post('auth/logout/', { refresh }).catch(() => {});
      }
    } catch {
      // Ignore network errors during signout
    } finally {
      localStorage.clear();
      sessionStorage.clear();
      setConfirmSignout(false);
      setMenu(false);
      navg('/login');
    }
  };

  const title = pageTitles[loc.pathname] || nav.flatMap((x) => x[1]).find((x) => x[0] === loc.pathname)?.[2] || 'Pocketly';

  return (
    <div className="app-shell">
      <aside className={open ? 'open' : ''}>
        <div className="brand">
          pocket<span>ly</span>
        </div>
        <nav>
          {nav.map(([label, items]) => (
            <div className="nav-group" key={label}>
              <p>{label}</p>
              {items.map(([to, icon, text]) => (
                <NavLink
                  end={to === '/'}
                  key={to}
                  to={to}
                  onClick={() => setOpen(false)}
                >
                  <Icon name={icon} />
                  <span>{text}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="side-user">
          <NavLink
            className="side-user-profile"
            to="/profile"
            onClick={() => setOpen(false)}
            aria-label="Open profile"
          >
            <Avatar user={me.data} />
            <strong>{me.data?.name || 'Your account'}</strong>
          </NavLink>
          <div>
            <button type="button" onClick={() => setConfirmSignout(true)}>
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {open && (
        <button
          aria-label="Close menu"
          className="scrim"
          onClick={() => setOpen(false)}
        />
      )}

      <main className="app-main">
        <div className="topbar">
          <button className="mobile-menu" onClick={() => setOpen(true)}>
            ☰
          </button>
          <div className="crumb">
            <span>Workspace</span>
            <b>/</b>
            <strong>{title}</strong>
          </div>
          <div className="top-actions">
            <label className="global-search">
              ⌕<input placeholder="Search transactions" />
            </label>
            <button className="bell" aria-label="Notifications">
              ♧
            </button>
            <button
              className="user-menu"
              onClick={() => setMenu(!menu)}
            >
              <Avatar user={me.data} />
            </button>
            {menu && (
              <div className="user-popover">
                <button
                  type="button"
                  onClick={() => {
                    setMenu(false);
                    navg('/profile');
                  }}
                >
                  Profile
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMenu(false);
                    navg('/profile/security');
                  }}
                >
                  Security
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMenu(false);
                    navg('/profile/general');
                  }}
                >
                  General
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMenu(false);
                    navg('/profile/login-activity');
                  }}
                >
                  Login activity
                </button>
                <hr />
                <button
                  type="button"
                  onClick={() => {
                    setMenu(false);
                    setConfirmSignout(true);
                  }}
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>

        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/accounts" element={<Accounts />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/budgets" element={<Budgets />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/categories" element={<Categories />} />
          <Route path="/recurring" element={<Recurring />} />
          <Route path="/goals" element={<Goals />} />
          <Route path="/profile" element={<Profile defaultTab="profile" />} />
          <Route path="/profile/general" element={<Profile defaultTab="general" />} />
          <Route path="/profile/notifications" element={<Profile defaultTab="notifications" />} />
          <Route path="/profile/appearance" element={<Profile defaultTab="appearance" />} />
          <Route path="/profile/privacy" element={<Profile defaultTab="privacy" />} />
          <Route path="/profile/security" element={<Profile defaultTab="security" />} />
          <Route path="/profile/login-activity" element={<Profile defaultTab="login-activity" />} />
          <Route path="/profile/activity" element={<Navigate to="/profile/login-activity" replace />} />
          <Route path="/login-activity" element={<Navigate to="/profile/login-activity" replace />} />
          <Route path="/settings/security" element={<Navigate to="/profile/security" replace />} />
          <Route path="/settings/profile/security" element={<Navigate to="/profile/security" replace />} />
          <Route path="/settings" element={<Navigate to="/profile/general" replace />} />
          <Route path="/notifications" element={<Navigate to="/profile/notifications" replace />} />
        </Routes>
      </main>

      {confirmSignout && (
        <Modal title="Sign out" onClose={() => setConfirmSignout(false)}>
          <div className="signout-modal-content">
            <p>Are you sure you want to sign out of your Pocketly account?</p>
            <div className="form-actions" style={{ marginTop: '20px' }}>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setConfirmSignout(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                className="btn-danger"
                onClick={performSignout}
              >
                Yes, sign out
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signin" element={<Navigate to="/login" replace />} />
      <Route path="/signup" element={<Login initialMode="signup" />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/mfa" element={<MFA />} />
      <Route
        path="/*"
        element={
          localStorage.getItem('access') ? <Shell /> : <Navigate to="/login" />
        }
      />
    </Routes>
  );
}
