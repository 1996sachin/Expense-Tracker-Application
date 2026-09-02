import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api';
import { Badge, Button, Card, Empty, Loading, Modal, PageHeader, SortSelect, money } from '../components/UI';

const ICON_PRESETS = ['🎯', '🏖️', '🚗', '🏠', '💻', '💍', '🎓', '🛡️', '💰', '📱', '✈️', '🎁'];
const COLOR_PRESETS = ['#6d5dfc', '#28b895', '#f2a64c', '#ed6a85', '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'];

const emptyGoalForm = () => ({
  name: '',
  target_amount: '',
  current_amount: '0',
  target_date: '',
  linked_account: '',
  icon: '🎯',
  color: '#6d5dfc',
  status: 'active',
});

const SORT_OPTIONS = [
  { label: 'Target date (soonest)', value: 'target_date' },
  { label: 'Name (A–Z)', value: 'name' },
  { label: 'Name (Z–A)', value: '-name' },
  { label: 'Target amount (low to high)', value: 'target_amount' },
  { label: 'Target amount (high to low)', value: '-target_amount' },
  { label: 'Progress % (high to low)', value: '-progress_percent' },
  { label: 'Progress % (low to high)', value: 'progress_percent' },
  { label: 'Newest first', value: '-created_at' },
];

export default function Goals() {
  const qc = useQueryClient();
  const [ordering, setOrdering] = useState('target_date');
  const [form, setForm] = useState(null);
  const [fundModal, setFundModal] = useState(null);
  const [fundAmount, setFundAmount] = useState('');

  const goalsQuery = useQuery({
    queryKey: ['goals', ordering],
    queryFn: () => api.get(`goals/?ordering=${ordering}`).then((r) => r.data),
  });

  const accountsQuery = useQuery({
    queryKey: ['accounts'],
    queryFn: () => api.get('accounts/').then((r) => r.data),
  });

  const goals = goalsQuery.data?.results || goalsQuery.data || [];
  const accounts = accountsQuery.data?.results || accountsQuery.data || [];

  const saveGoal = useMutation({
    mutationFn: (payload) => {
      const body = {
        ...payload,
        linked_account: payload.linked_account ? payload.linked_account : null,
        target_date: payload.target_date ? payload.target_date : null,
      };
      return payload.id ? api.patch(`goals/${payload.id}/`, body) : api.post('goals/', body);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals'] });
      setForm(null);
    },
  });

  const deleteGoal = useMutation({
    mutationFn: (id) => api.delete(`goals/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['goals'] }),
  });

  const addFunds = useMutation({
    mutationFn: ({ id, amount }) => api.post(`goals/${id}/add-funds/`, { amount }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals'] });
      setFundModal(null);
      setFundAmount('');
    },
  });

  // Calculate summary stats
  const totalTarget = goals.reduce((s, g) => s + Number(g.target_amount || 0), 0);
  const totalSaved = goals.reduce((s, g) => s + Number(g.current_amount || 0), 0);
  const activeCount = goals.filter((g) => g.status === 'active').length;
  const overallProgress = totalTarget > 0 ? Math.round((totalSaved / totalTarget) * 100) : 0;

  return (
    <>
      <PageHeader eyebrow="LOOKING AHEAD" title="Financial goals">
        <SortSelect value={ordering} onChange={setOrdering} options={SORT_OPTIONS} />
        <Button onClick={() => setForm(emptyGoalForm())}>+ Add goal</Button>
      </PageHeader>

      {goals.length > 0 && (
        <div className="budget-summary">
          {[
            ['Total target', totalTarget],
            ['Total saved', totalSaved],
            ['Overall progress', `${overallProgress}%`],
            ['Active goals', activeCount],
          ].map(([label, val]) => (
            <Card key={label}>
              <small>{label}</small>
              <strong>{typeof val === 'number' ? money(val) : val}</strong>
            </Card>
          ))}
        </div>
      )}

      <Card className="section-card">
        <div className="card-heading">
          <div>
            <h3>Your savings goals</h3>
            <p>Track targets for major purchases, emergency funds, and life milestones.</p>
          </div>
        </div>

        {goalsQuery.isLoading ? (
          <Loading />
        ) : goals.length ? (
          <div className="goal-grid">
            {goals.map((g) => {
              const pct = Number(g.progress_percent || 0);
              const isDone = g.status === 'completed' || pct >= 100;
              const tone = isDone ? 'success' : pct > 75 ? 'warning' : 'neutral';
              const progressColor = isDone ? '#29bb97' : g.color || '#6d5dfc';

              return (
                <article className="goal-card" key={g.id} style={{ borderTopColor: g.color || '#6d5dfc' }}>
                  <div className="goal-header">
                    <div className="goal-identity">
                      <span className="goal-icon" style={{ background: `${g.color || '#6d5dfc'}22` }}>
                        {g.icon || '🎯'}
                      </span>
                      <div>
                        <h3>{g.name}</h3>
                        {g.linked_account_name && <small>Linked: {g.linked_account_name}</small>}
                      </div>
                    </div>
                    <Badge tone={tone}>{g.status}</Badge>
                  </div>

                  <div className="goal-numbers">
                    <strong>{money(g.current_amount)}</strong>
                    <span>of {money(g.target_amount)}</span>
                  </div>

                  <div className="progress">
                    <i
                      style={{
                        width: `${Math.min(pct, 100)}%`,
                        background: progressColor,
                      }}
                    />
                  </div>

                  <div className="goal-meta">
                    <span>{pct}% complete</span>
                    <span>
                      {g.days_remaining !== null && g.days_remaining !== undefined
                        ? g.days_remaining > 0
                          ? `${g.days_remaining} days left`
                          : g.days_remaining === 0
                          ? 'Due today'
                          : 'Overdue'
                        : g.target_date
                        ? `Target: ${g.target_date}`
                        : 'No target date'}
                    </span>
                  </div>

                  <div className="goal-actions">
                    <Button
                      variant="secondary"
                      className="btn-sm"
                      onClick={() => {
                        setFundModal(g);
                        setFundAmount('');
                      }}
                    >
                      + Add funds
                    </Button>
                    <div className="row-actions">
                      <button onClick={() => setForm(g)}>Edit</button>
                      <button
                        className="danger-text"
                        onClick={() => confirm(`Delete goal "${g.name}"?`) && deleteGoal.mutate(g.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <Empty
            title="Set your first financial goal"
            text="Create savings targets to track upcoming purchases, trips, or emergency funds."
            action={<Button onClick={() => setForm(emptyGoalForm())}>+ Add goal</Button>}
          />
        )}
      </Card>

      {/* Add / Edit Goal Modal */}
      {form && (
        <Modal title={form.id ? 'Edit goal' : 'New goal'} onClose={() => setForm(null)}>
          <form
            className="form-grid"
            onSubmit={(e) => {
              e.preventDefault();
              saveGoal.mutate(form);
            }}
          >
            <label>
              Goal name
              <input
                required
                placeholder="e.g. Emergency Fund, New Laptop"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </label>

            <div className="form-row-2">
              <label>
                Target amount
                <input
                  required
                  min="0.01"
                  step="any"
                  type="number"
                  placeholder="0.00"
                  value={form.target_amount}
                  onChange={(e) => setForm({ ...form, target_amount: e.target.value })}
                />
              </label>
              <label>
                Current saved
                <input
                  min="0"
                  step="any"
                  type="number"
                  placeholder="0.00"
                  value={form.current_amount}
                  onChange={(e) => setForm({ ...form, current_amount: e.target.value })}
                />
              </label>
            </div>

            <label>
              Target date (optional)
              <input
                type="date"
                value={form.target_date || ''}
                onChange={(e) => setForm({ ...form, target_date: e.target.value })}
              />
            </label>

            <label>
              Linked account (optional)
              <select
                value={form.linked_account || ''}
                onChange={(e) => setForm({ ...form, linked_account: e.target.value || null })}
              >
                <option value="">None (Independent goal)</option>
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({money(a.current_balance, a.currency)})
                  </option>
                ))}
              </select>
            </label>

            <label>
              Icon
              <div className="icon-picker">
                {ICON_PRESETS.map((ic) => (
                  <button
                    type="button"
                    key={ic}
                    className={`picker-btn ${form.icon === ic ? 'selected' : ''}`}
                    onClick={() => setForm({ ...form, icon: ic })}
                  >
                    {ic}
                  </button>
                ))}
              </div>
            </label>

            <label>
              Color
              <div className="color-picker">
                {COLOR_PRESETS.map((c) => (
                  <button
                    type="button"
                    key={c}
                    className={`color-btn ${form.color === c ? 'selected' : ''}`}
                    style={{ background: c }}
                    onClick={() => setForm({ ...form, color: c })}
                  />
                ))}
              </div>
            </label>

            {form.id && (
              <label>
                Status
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                >
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="archived">Archived</option>
                </select>
              </label>
            )}

            <div className="form-actions">
              <Button type="button" variant="secondary" onClick={() => setForm(null)}>
                Cancel
              </Button>
              <Button disabled={saveGoal.isPending}>
                {saveGoal.isPending ? 'Saving…' : form.id ? 'Save changes' : 'Create goal'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Add Funds Modal */}
      {fundModal && (
        <Modal title={`Add funds to ${fundModal.name}`} onClose={() => setFundModal(null)}>
          <form
            className="form-grid"
            onSubmit={(e) => {
              e.preventDefault();
              if (Number(fundAmount) > 0) {
                addFunds.mutate({ id: fundModal.id, amount: fundAmount });
              }
            }}
          >
            <div className="fund-current-info">
              <small>Current progress</small>
              <strong>
                {money(fundModal.current_amount)} / {money(fundModal.target_amount)} ({fundModal.progress_percent}%)
              </strong>
            </div>

            <label>
              Amount to add
              <input
                required
                min="0.01"
                step="any"
                type="number"
                placeholder="0.00"
                autoFocus
                value={fundAmount}
                onChange={(e) => setFundAmount(e.target.value)}
              />
            </label>

            <div className="quick-amount-buttons">
              {[100, 500, 1000, 5000].map((amt) => (
                <button
                  type="button"
                  key={amt}
                  className="quick-amt-btn"
                  onClick={() => setFundAmount((prev) => (Number(prev || 0) + amt).toString())}
                >
                  +{amt}
                </button>
              ))}
            </div>

            <div className="form-actions">
              <Button type="button" variant="secondary" onClick={() => setFundModal(null)}>
                Cancel
              </Button>
              <Button disabled={addFunds.isPending || !Number(fundAmount)}>
                {addFunds.isPending ? 'Adding…' : 'Add funds'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
