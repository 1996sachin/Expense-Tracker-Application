import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api';
import { Badge, Button, Card, Empty, Loading, Modal, PageHeader, SortSelect, money } from '../components/UI';

const emptyRecurringForm = () => ({
  type: 'expense',
  amount: '',
  account: '',
  category: '',
  frequency: 'monthly',
  start_date: new Date().toISOString().slice(0, 10),
  end_date: '',
  note: '',
  is_active: true,
});

const SORT_OPTIONS = [
  { label: 'Next occurrence (soonest)', value: 'next_run_date' },
  { label: 'Next occurrence (latest)', value: '-next_run_date' },
  { label: 'Amount (high to low)', value: '-amount' },
  { label: 'Amount (low to high)', value: 'amount' },
  { label: 'Frequency', value: 'frequency' },
  { label: 'Category', value: 'category__name' },
  { label: 'Newest created', value: '-created_at' },
];

export default function Recurring() {
  const qc = useQueryClient();
  const [ordering, setOrdering] = useState('next_run_date');
  const [form, setForm] = useState(null);

  const recurringQuery = useQuery({
    queryKey: ['recurring-transactions', ordering],
    queryFn: () => api.get(`recurring-transactions/?ordering=${ordering}`).then((r) => r.data),
  });

  const accountsQuery = useQuery({
    queryKey: ['accounts'],
    queryFn: () => api.get('accounts/').then((r) => r.data),
  });

  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.get('categories/').then((r) => r.data),
  });

  const rows = recurringQuery.data?.results || recurringQuery.data || [];
  const accounts = accountsQuery.data?.results || accountsQuery.data || [];
  const categories = categoriesQuery.data?.results || categoriesQuery.data || [];

  const saveRecurring = useMutation({
    mutationFn: (payload) => {
      const body = {
        ...payload,
        category: payload.category ? payload.category : null,
        end_date: payload.end_date ? payload.end_date : null,
      };
      return payload.id
        ? api.patch(`recurring-transactions/${payload.id}/`, body)
        : api.post('recurring-transactions/', body);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['recurring-transactions'] });
      setForm(null);
    },
  });

  const toggleActive = useMutation({
    mutationFn: (id) => api.post(`recurring-transactions/${id}/toggle/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['recurring-transactions'] }),
  });

  const deleteRecurring = useMutation({
    mutationFn: (id) => api.delete(`recurring-transactions/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['recurring-transactions'] }),
  });

  // Calculate monthly multiplier
  const toMonthly = (amount, frequency) => {
    const num = Number(amount || 0);
    switch (frequency) {
      case 'daily':
        return num * 30;
      case 'weekly':
        return num * 4.33;
      case 'yearly':
        return num / 12;
      case 'monthly':
      default:
        return num;
    }
  };

  const activeRows = rows.filter((r) => r.is_active);
  const monthlyExpense = activeRows
    .filter((r) => r.type === 'expense')
    .reduce((s, r) => s + toMonthly(r.amount, r.frequency), 0);
  const monthlyIncome = activeRows
    .filter((r) => r.type === 'income')
    .reduce((s, r) => s + toMonthly(r.amount, r.frequency), 0);

  return (
    <>
      <PageHeader eyebrow="AUTOMATE YOUR PLAN" title="Recurring transactions">
        <SortSelect value={ordering} onChange={setOrdering} options={SORT_OPTIONS} />
        <Button onClick={() => setForm(emptyRecurringForm())}>+ Add recurring transaction</Button>
      </PageHeader>

      {rows.length > 0 && (
        <div className="budget-summary">
          {[
            ['Active schedules', activeRows.length],
            ['Est. monthly expenses', monthlyExpense],
            ['Est. monthly income', monthlyIncome],
            ['Total scheduled', rows.length],
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
            <h3>Scheduled automated transactions</h3>
            <p>Pocketly automatically records transactions and updates account balances on their scheduled dates.</p>
          </div>
        </div>

        {recurringQuery.isLoading ? (
          <Loading />
        ) : rows.length ? (
          <div className="recurring-list">
            <div className="recurring-head">
              <span>Schedule</span>
              <span>Details & Account</span>
              <span>Frequency</span>
              <span>Next occurrence</span>
              <span>Amount</span>
              <span style={{ textAlign: 'right' }}>Actions</span>
            </div>
            {rows.map((x) => (
              <article className={`recurring-row ${!x.is_active ? 'paused' : ''}`} key={x.id}>
                <div className="recurring-badge-col">
                  <Badge tone={x.is_active ? 'success' : 'neutral'}>
                    {x.is_active ? 'Active' : 'Paused'}
                  </Badge>
                </div>

                <div className="recurring-details">
                  <strong>{x.note || `${x.frequency} ${x.type}`}</strong>
                  <small>
                    {x.account_name || `Account #${x.account}`}
                    {x.category_name ? ` · ${x.category_name}` : ''}
                  </small>
                </div>

                <div className="recurring-freq">
                  <Badge tone="neutral">{x.frequency}</Badge>
                </div>

                <div className="recurring-date">
                  <span>{x.next_run_date}</span>
                  {x.end_date && <small>Until {x.end_date}</small>}
                </div>

                <b className={`recurring-amount ${x.type}`}>
                  {x.type === 'expense' ? '-' : '+'}
                  {money(x.amount)}
                </b>

                <div className="row-actions recurring-actions">
                  <button
                    onClick={() => toggleActive.mutate(x.id)}
                    title={x.is_active ? 'Pause recurrence' : 'Resume recurrence'}
                  >
                    {x.is_active ? 'Pause' : 'Resume'}
                  </button>
                  <button onClick={() => setForm(x)}>Edit</button>
                  <button
                    className="danger-text"
                    onClick={() => confirm('Delete this recurring schedule?') && deleteRecurring.mutate(x.id)}
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <Empty
            title="No recurring transactions"
            text="Schedule subscriptions, bills, or salary to automate your bookkeeping."
            action={<Button onClick={() => setForm(emptyRecurringForm())}>+ Add recurring transaction</Button>}
          />
        )}
      </Card>

      {/* Add / Edit Recurring Modal */}
      {form && (
        <Modal
          title={form.id ? 'Edit recurring transaction' : 'New recurring transaction'}
          onClose={() => setForm(null)}
        >
          <form
            className="form-grid"
            onSubmit={(e) => {
              e.preventDefault();
              saveRecurring.mutate(form);
            }}
          >
            <div className="form-row-2">
              <label>
                Type
                <select
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value, category: '' })}
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </label>

              <label>
                Frequency
                <select
                  value={form.frequency}
                  onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </label>
            </div>

            <label>
              Account
              <select
                required
                value={form.account}
                onChange={(e) => setForm({ ...form, account: e.target.value })}
              >
                <option value="">Select account</option>
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({money(a.current_balance, a.currency)})
                  </option>
                ))}
              </select>
            </label>

            <label>
              Category (optional)
              <select
                value={form.category || ''}
                onChange={(e) => setForm({ ...form, category: e.target.value || null })}
              >
                <option value="">Uncategorized</option>
                {categories
                  .filter((c) => c.type === form.type)
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
              </select>
            </label>

            <label>
              Amount
              <input
                required
                min="0.01"
                step="any"
                type="number"
                placeholder="0.00"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
              />
            </label>

            <div className="form-row-2">
              <label>
                Start date
                <input
                  required
                  type="date"
                  value={form.start_date}
                  onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                />
              </label>

              <label>
                End date (optional)
                <input
                  type="date"
                  value={form.end_date || ''}
                  onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                />
              </label>
            </div>

            <label>
              Description / Note
              <input
                placeholder="e.g. Netflix, Spotify, Rent, Monthly Salary"
                value={form.note || ''}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
              />
            </label>

            {form.id && (
              <label className="setting-line" style={{ padding: '8px 0', borderTop: 'none' }}>
                <span>Active</span>
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                />
              </label>
            )}

            <div className="form-actions">
              <Button type="button" variant="secondary" onClick={() => setForm(null)}>
                Cancel
              </Button>
              <Button disabled={saveRecurring.isPending}>
                {saveRecurring.isPending ? 'Saving…' : form.id ? 'Save changes' : 'Create recurring transaction'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
