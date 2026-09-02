import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api';
import AccountCard from '../components/AccountCard';
import { CURRENCY_OPTIONS, DEFAULT_CURRENCY } from '../utils/currency';
import { Button, PageHeader, SortSelect } from '../components/UI';

const ACCOUNT_SORT_OPTIONS = [
  { label: 'Name (A–Z)', value: 'name' },
  { label: 'Name (Z–A)', value: '-name' },
  { label: 'Balance (high to low)', value: '-current_balance' },
  { label: 'Balance (low to high)', value: 'current_balance' },
  { label: 'Account type', value: 'account_type' },
];

const emptyForm = () => ({
  name: '',
  bank_name: '',
  account_type: 'checking',
  currency: DEFAULT_CURRENCY,
  opening_balance: '0',
  color: '#6d5dfc',
});

const createPayload = (form) => ({
  name: form.name,
  bank_name: form.bank_name,
  account_type: form.account_type,
  currency: form.currency,
  opening_balance: form.opening_balance,
  color: form.color,
});

const editPayload = (form) => ({
  name: form.name,
  bank_name: form.bank_name,
  account_type: form.account_type,
  currency: form.currency,
  current_balance: form.current_balance,
  color: form.color,
});

export default function Accounts() {
  const qc = useQueryClient();
  const [ordering, setOrdering] = useState('name');
  const [form, setForm] = useState(null);
  const q = useQuery({
    queryKey: ['accounts', ordering],
    queryFn: () => api.get(`accounts/?ordering=${ordering}`).then((r) => r.data),
  });
  const editing = Boolean(form?.id);
  const save = useMutation({
    mutationFn: () =>
      editing
        ? api.patch(`accounts/${form.id}/`, editPayload(form))
        : api.post('accounts/', createPayload(form)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['accounts'] });
      qc.invalidateQueries({ queryKey: ['summary'] });
      setForm(null);
    },
  });

  return (
    <>
      <PageHeader eyebrow="YOUR MONEY" title="Accounts">
        <SortSelect value={ordering} onChange={setOrdering} options={ACCOUNT_SORT_OPTIONS} />
        <Button onClick={() => setForm(emptyForm())}>+ Add account</Button>
      </PageHeader>
      <div className="accounts">
        {q.data?.results?.map((a) => (
          <AccountCard key={a.id} account={a} onEdit={(account) => setForm({ ...account })} />
        ))}
      </div>
      {form && (
        <div className="modal">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              save.mutate();
            }}
          >
            <h2>{editing ? 'Edit account' : 'New account'}</h2>
            {[
              ['name', 'Account name'],
              ['bank_name', 'Bank name'],
              ...(editing
                ? [['current_balance', 'Current balance']]
                : [['opening_balance', 'Opening balance']]),
            ].map(([k, l]) => (
              <input
                key={k}
                placeholder={l}
                type={k === 'opening_balance' || k === 'current_balance' ? 'number' : 'text'}
                step={k === 'current_balance' ? '0.01' : undefined}
                value={form[k] ?? ''}
                onChange={(e) => setForm({ ...form, [k]: e.target.value })}
              />
            ))}
            <select
              value={form.account_type}
              onChange={(e) => setForm({ ...form, account_type: e.target.value })}
            >
              {['savings', 'checking', 'credit_card', 'cash', 'wallet'].map((x) => (
                <option key={x} value={x}>
                  {x}
                </option>
              ))}
            </select>
            <label className="field">
              Currency
              <select
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
              >
                {CURRENCY_OPTIONS.map((x) => (
                  <option key={x.code} value={x.code}>
                    {x.label}
                  </option>
                ))}
              </select>
            </label>
            <div>
              <button disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save account'}</button>
              <button type="button" className="plain" onClick={() => setForm(null)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
