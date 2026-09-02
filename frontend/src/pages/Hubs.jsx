import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import api from '../api';
import { Avatar, Badge, Button, Card, Empty, Loading, Modal, PageHeader, money } from '../components/UI';
import Security from './Security';
import LoginActivity from './LoginActivity';

const list = (d) => d?.results || d || [];

export function Categories() {
  const qc = useQueryClient();
  const [q, setQ] = useState('');
  const [form, setForm] = useState();

  const cats = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.get('categories/').then((r) => r.data),
  });

  const save = useMutation({
    mutationFn: () => (form.id ? api.patch(`categories/${form.id}/`, form) : api.post('categories/', form)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['categories'] });
      setForm(null);
    },
  });

  const remove = useMutation({
    mutationFn: (id) => api.delete(`categories/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categories'] }),
  });

  const rows = list(cats.data).filter((x) => x.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <>
      <PageHeader eyebrow="ORGANIZE YOUR MONEY" title="Categories">
        <Button onClick={() => setForm({ name: '', type: 'expense', color: '#6d5dfc' })}>
          + New category
        </Button>
      </PageHeader>
      <Card className="section-card">
        <div className="toolbar">
          <input
            className="search-input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search categories"
          />
          <span>{rows.length} categories</span>
        </div>
        {cats.isLoading ? (
          <Loading />
        ) : rows.length ? (
          <div className="category-list">
            {rows.map((x) => (
              <article className="category-row" key={x.id}>
                <i style={{ background: x.color }}>{x.name[0]}</i>
                <div>
                  <strong>{x.name}</strong>
                  <small>{x.type} category</small>
                </div>
                <Badge tone={x.type === 'income' ? 'success' : 'neutral'}>{x.type}</Badge>
                <div className="row-actions">
                  <button onClick={() => setForm(x)}>Edit</button>
                  {x.user && (
                    <button
                      className="danger-text"
                      onClick={() => confirm('Delete this category?') && remove.mutate(x.id)}
                    >
                      Delete
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <Empty title="No categories found" text="Create a category to organize your money." />
        )}
      </Card>
      {form && (
        <Modal title={form.id ? 'Edit category' : 'New category'} onClose={() => setForm(null)}>
          <form
            className="form-grid"
            onSubmit={(e) => {
              e.preventDefault();
              save.mutate();
            }}
          >
            <label>
              Name
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </label>
            <label>
              Type
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </label>
            <label>
              Color
              <input
                type="color"
                value={form.color}
                onChange={(e) => setForm({ ...form, color: e.target.value })}
              />
            </label>
            <div className="form-actions">
              <Button type="button" variant="secondary" onClick={() => setForm(null)}>
                Cancel
              </Button>
              <Button disabled={save.isPending}>Save category</Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}

function Chart({ title, children }) {
  return (
    <Card className="chart-card">
      <h3>{title}</h3>
      <div className="chart-area">{children}</div>
    </Card>
  );
}

export function Reports() {
  const r = useQuery({
    queryKey: ['insights', 'year'],
    queryFn: () => api.get('transactions/insights/?period=year').then((x) => x.data),
  });
  const tr = r.data?.trend || [],
    cat = r.data?.categories || [],
    income = tr.reduce((s, x) => s + x.income, 0),
    expense = tr.reduce((s, x) => s + x.expense, 0);

  return (
    <>
      <PageHeader eyebrow="INSIGHTS & ANALYSIS" title="Reports">
        <Button variant="secondary" onClick={() => window.print()}>
          Export / Print
        </Button>
      </PageHeader>
      <div className="report-kpis">
        {[
          ['Total income', income, 'income'],
          ['Total expenses', expense, 'expense'],
          ['Net savings', income - expense, ''],
          ['Transactions', tr.length, ''],
        ].map(([a, b, c]) => (
          <Card key={a}>
            <small>{a}</small>
            <strong className={c}>{a === 'Transactions' ? b : money(b)}</strong>
          </Card>
        ))}
      </div>
      <div className="content-grid">
        <Chart title="Monthly income vs expenses">
          {tr.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tr}>
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(v) => money(v)} />
                <Bar dataKey="income" fill="#28b895" />
                <Bar dataKey="expense" fill="#765ef5" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <Empty
              title="No report data"
              text="Transactions will appear here as you add them."
            />
          )}
        </Chart>
        <Chart title="Category distribution">
          {cat.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={cat} dataKey="value" nameKey="name" outerRadius={90}>
                  {cat.map((_, i) => (
                    <Cell key={i} fill={['#765ef5', '#28b895', '#f2a64c', '#ed6a85'][i % 4]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => money(v)} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <Empty
              title="No category spending"
              text="Expense categories will appear here."
            />
          )}
        </Chart>
      </div>
    </>
  );
}

export { default as Recurring } from './Recurring';
export { default as Goals } from './Goals';
export { default as Security } from './Security';
export { default as LoginActivity } from './LoginActivity';

const SETTINGS_TABS = [
  { id: 'profile', label: 'Profile', icon: '◉', path: '/profile' },
  { id: 'general', label: 'General', icon: '⚙', path: '/profile/general' },
  { id: 'notifications', label: 'Notifications', icon: '♧', path: '/profile/notifications' },
  { id: 'appearance', label: 'Appearance', icon: '◐', path: '/profile/appearance' },
  { id: 'privacy', label: 'Privacy', icon: '🔒', path: '/profile/privacy' },
  { id: 'security', label: 'Security', icon: '♢', path: '/profile/security' },
  { id: 'login-activity', label: 'Login Activity', icon: '◷', path: '/profile/login-activity' },
];

export function Profile({ defaultTab = 'profile' }) {
  const qc = useQueryClient();
  const loc = useLocation();
  const nav = useNavigate();

  // Determine active tab from URL path or prop
  let activeTab = defaultTab;
  if (loc.pathname === '/profile/general') activeTab = 'general';
  else if (loc.pathname === '/profile/notifications') activeTab = 'notifications';
  else if (loc.pathname === '/profile/appearance') activeTab = 'appearance';
  else if (loc.pathname === '/profile/privacy') activeTab = 'privacy';
  else if (loc.pathname === '/profile/security') activeTab = 'security';
  else if (loc.pathname === '/profile/login-activity' || loc.pathname === '/profile/activity') activeTab = 'login-activity';
  else if (loc.pathname === '/profile') activeTab = 'profile';

  const me = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get('auth/me/').then((r) => r.data),
  });
  const [edit, setEdit] = useState(false);
  const [form, setForm] = useState({});

  const save = useMutation({
    mutationFn: () => api.patch('auth/me/', form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['me'] });
      setEdit(false);
    },
  });

  const u = me.data;

  // Header configs per tab
  const headerMap = {
    profile: { eyebrow: 'YOUR ACCOUNT', title: 'Profile & Account' },
    general: { eyebrow: 'PREFERENCES', title: 'General Settings' },
    notifications: { eyebrow: 'PREFERENCES', title: 'Notifications' },
    appearance: { eyebrow: 'PREFERENCES', title: 'Appearance' },
    privacy: { eyebrow: 'DATA & PRIVACY', title: 'Privacy & Data' },
    security: { eyebrow: 'ACCOUNT PROTECTION', title: 'Security' },
    'login-activity': { eyebrow: 'SECURITY & SESSIONS', title: 'Login Activity' },
  };

  const headerInfo = headerMap[activeTab] || headerMap.profile;

  return (
    <>
      <PageHeader eyebrow={headerInfo.eyebrow} title={headerInfo.title}>
        {activeTab === 'profile' && (
          <Button
            variant="secondary"
            onClick={() => {
              setForm(u || {});
              setEdit(true);
            }}
          >
            Edit profile
          </Button>
        )}
      </PageHeader>

      <div className="tab-nav">
        {SETTINGS_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => nav(tab.path)}
          >
            <span style={{ fontSize: '13px', opacity: 0.9 }}>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="profile-layout">
          <Card className="profile-card">
            <Avatar user={u} size="xl" />
            <h2>{u?.name || 'Your Pocketly profile'}</h2>
            <p>{u?.email}</p>
            <Badge tone={u?.auth_provider === 'google' ? 'success' : 'neutral'}>
              {u?.auth_provider === 'google' ? 'Google connected' : 'Email account'}
            </Badge>
          </Card>
          <Card className="section-card details">
            <h3>Personal details</h3>
            {me.isLoading ? (
              <Loading />
            ) : (
              <dl>
                <dt>Full name</dt>
                <dd>{u?.name || 'Not provided'}</dd>
                <dt>Email</dt>
                <dd>{u?.email}</dd>
                <dt>Preferred currency</dt>
                <dd>{u?.currency_preference || 'USD'}</dd>
                <dt>Sign-in method</dt>
                <dd>{u?.auth_provider || 'email'}</dd>
              </dl>
            )}
          </Card>
        </div>
      )}

      {/* General Settings Tab */}
      {activeTab === 'general' && (
        <div className="settings-grid">
          <Card className="setting-card">
            <h3>Language & Region</h3>
            <p>Select your preferred language and localization formats.</p>
            <label className="setting-line" style={{ display: 'grid', gap: '6px' }}>
              <span>Display language</span>
              <select defaultValue="en">
                <option value="en">English (US)</option>
                <option value="en-gb">English (UK)</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="ne">Nepali (नेपाली)</option>
              </select>
            </label>
          </Card>
          <Card className="setting-card">
            <h3>Calendar & Date Format</h3>
            <p>Customize how dates and weeks are displayed in Pocketly.</p>
            <label className="setting-line" style={{ display: 'grid', gap: '6px' }}>
              <span>Date format</span>
              <select defaultValue="YYYY-MM-DD">
                <option value="YYYY-MM-DD">YYYY-MM-DD (2026-09-02)</option>
                <option value="MM/DD/YYYY">MM/DD/YYYY (09/02/2026)</option>
                <option value="DD/MM/YYYY">DD/MM/YYYY (02/09/2026)</option>
              </select>
            </label>
            <label className="setting-line" style={{ display: 'grid', gap: '6px', marginTop: '10px' }}>
              <span>Start of week</span>
              <select defaultValue="sunday">
                <option value="sunday">Sunday</option>
                <option value="monday">Monday</option>
              </select>
            </label>
          </Card>
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <div className="settings-grid">
          <Card className="setting-card">
            <h3>Product Notifications</h3>
            <p>Control news, product announcements, and release updates.</p>
            <label className="setting-line">
              <span>Product updates & new features</span>
              <input type="checkbox" defaultChecked />
            </label>
            <label className="setting-line">
              <span>Weekly spending report summary</span>
              <input type="checkbox" defaultChecked />
            </label>
          </Card>
          <Card className="setting-card">
            <h3>Security & Account Alerts</h3>
            <p>Receive notifications regarding account security and financial activity.</p>
            <label className="setting-line">
              <span>Login alerts on new devices</span>
              <input type="checkbox" defaultChecked />
            </label>
            <label className="setting-line">
              <span>Budget threshold warnings (80% / 100%)</span>
              <input type="checkbox" defaultChecked />
            </label>
            <label className="setting-line">
              <span>Recurring transaction reminders</span>
              <input type="checkbox" defaultChecked />
            </label>
          </Card>
        </div>
      )}

      {/* Appearance Tab */}
      {activeTab === 'appearance' && (
        <div className="settings-grid">
          <Card className="setting-card">
            <h3>Theme & Styling</h3>
            <p>Choose the interface theme that best fits your workflow.</p>
            <label className="setting-line" style={{ display: 'grid', gap: '6px' }}>
              <span>Workspace theme</span>
              <select defaultValue="system">
                <option value="system">System default</option>
                <option value="light">Light mode</option>
                <option value="dark">Dark mode</option>
              </select>
            </label>
          </Card>
          <Card className="setting-card">
            <h3>Display Density</h3>
            <p>Adjust table density and typography spacing.</p>
            <label className="setting-line">
              <span>Compact table rows</span>
              <input type="checkbox" />
            </label>
            <label className="setting-line">
              <span>Smooth animations & transitions</span>
              <input type="checkbox" defaultChecked />
            </label>
          </Card>
        </div>
      )}

      {/* Privacy Tab */}
      {activeTab === 'privacy' && (
        <div className="settings-grid">
          <Card className="setting-card">
            <h3>Personal Data</h3>
            <p>Manage how your data is collected and processed.</p>
            <label className="setting-line">
              <span>Anonymous analytics & telemetry</span>
              <input type="checkbox" defaultChecked />
            </label>
            <label className="setting-line">
              <span>Personalized financial tips</span>
              <input type="checkbox" defaultChecked />
            </label>
          </Card>
          <Card className="setting-card">
            <h3>Data Portability</h3>
            <p>Download a copy of all your financial records and transactions.</p>
            <div style={{ marginTop: '16px' }}>
              <Button
                variant="secondary"
                type="button"
                onClick={() => {
                  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify({ user: u, export_date: new Date().toISOString() }));
                  const a = document.createElement('a');
                  a.setAttribute('href', dataStr);
                  a.setAttribute('download', 'pocketly-data-export.json');
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                }}
              >
                Export account data (JSON)
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && <Security />}

      {/* Login Activity Tab */}
      {activeTab === 'login-activity' && <LoginActivity />}

      {/* Edit Profile Modal */}
      {edit && (
        <Modal title="Edit profile" onClose={() => setEdit(false)}>
          <form
            className="form-grid"
            onSubmit={(e) => {
              e.preventDefault();
              save.mutate();
            }}
          >
            <label>
              First name
              <input
                value={form.first_name || ''}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              />
            </label>
            <label>
              Last name
              <input
                value={form.last_name || ''}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              />
            </label>
            <label>
              Currency
              <select
                value={form.currency_preference || 'USD'}
                onChange={(e) => setForm({ ...form, currency_preference: e.target.value })}
              >
                <option>USD</option>
                <option>EUR</option>
                <option>GBP</option>
                <option>NPR</option>
              </select>
            </label>
            <div className="form-actions">
              <Button type="button" variant="secondary" onClick={() => setEdit(false)}>
                Cancel
              </Button>
              <Button disabled={save.isPending}>Save changes</Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}

export function Settings() {
  const nav = useNavigate();
  React.useEffect(() => {
    nav('/profile/general', { replace: true });
  }, [nav]);
  return null;
}
