import React, { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../api";
import {
  Badge,
  Button,
  Card,
  Empty,
  Loading,
  Modal,
  PageHeader,
  SortSelect,
  money,
} from "../components/UI";
const TX_SORT_OPTIONS = [
  { label: "Date (newest first)", value: "-date" },
  { label: "Date (oldest first)", value: "date" },
  { label: "Amount (high to low)", value: "-amount" },
  { label: "Amount (low to high)", value: "amount" },
  { label: "Description", value: "note" },
];
export default function Transactions() {
  const qc = useQueryClient(),
    [ordering, setOrdering] = useState("-date"),
    [form, setForm] = useState(),
    [q, setQ] = useState(""),
    [type, setType] = useState("all");
  const tx = useQuery({
      queryKey: ["transactions", ordering],
      queryFn: () =>
        api.get(`transactions/?ordering=${ordering}`).then((r) => r.data),
    }),
    ac = useQuery({
      queryKey: ["accounts"],
      queryFn: () => api.get("accounts/").then((r) => r.data),
    }),
    cat = useQuery({
      queryKey: ["categories"],
      queryFn: () => api.get("categories/").then((r) => r.data),
    });
  const save = useMutation({
    mutationFn: () => api.post("transactions/", form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["accounts"] });
      setForm(null);
    },
  });
  const rows = useMemo(
    () =>
      (tx.data?.results || tx.data || []).filter(
        (x) =>
          (type === "all" || x.type === type) &&
          `${x.note || ""} ${x.date}`.toLowerCase().includes(q.toLowerCase()),
      ),
    [tx.data, q, type],
  );
  return (
    <>
      <PageHeader eyebrow="ACTIVITY" title="Transactions">
        <SortSelect
          value={ordering}
          onChange={setOrdering}
          options={TX_SORT_OPTIONS}
        />
        <Button
          onClick={() =>
            setForm({
              type: "expense",
              amount: "",
              date: new Date().toISOString().slice(0, 10),
              account: "",
              category: "",
              note: "",
            })
          }
        >
          + Add transaction
        </Button>
      </PageHeader>
      <Card className="section-card">
        <div className="transaction-filters">
          <input
            className="search-input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search description or date"
          />
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="all">All transactions</option>
            <option value="expense">Expenses</option>
            <option value="income">Income</option>
            <option value="transfer">Transfers</option>
          </select>
          <span>{rows.length} results</span>
        </div>
        {tx.isLoading ? (
          <Loading />
        ) : rows.length ? (
          <div className="transaction-table">
            <div className="transaction-head">
              <span>Date</span>
              <span>Description</span>
              <span>Type</span>
              <span>Amount</span>
            </div>
            {rows.map((x) => (
              <div className="transaction-line" key={x.id}>
                <span>{x.date}</span>
                <div>
                  <strong>{x.note || "Untitled transaction"}</strong>
                  <small>
                    Account #{x.account}
                    {x.category ? ` · Category #${x.category}` : ""}
                  </small>
                </div>
                <Badge tone={x.type === "income" ? "success" : "neutral"}>
                  {x.type}
                </Badge>
                <b className={x.type}>
                  {x.type === "expense" ? "-" : "+"}
                  {money(x.amount)}
                </b>
              </div>
            ))}
          </div>
        ) : (
          <Empty
            title="No matching transactions"
            text="Try adjusting the filters or add your first transaction."
          />
        )}
      </Card>
      {form && (
        <Modal title="Add transaction" onClose={() => setForm(null)}>
          <form
            className="form-grid"
            onSubmit={(e) => {
              e.preventDefault();
              save.mutate();
            }}
          >
            <label>
              Type
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                {["expense", "income", "transfer"].map((x) => (
                  <option key={x}>{x}</option>
                ))}
              </select>
            </label>
            <label>
              Account
              <select
                required
                value={form.account}
                onChange={(e) => setForm({ ...form, account: e.target.value })}
              >
                <option value="">Select account</option>
                {(ac.data?.results || ac.data || []).map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Category
              <select
                value={form.category}
                onChange={(e) =>
                  setForm({ ...form, category: e.target.value || null })
                }
              >
                <option value="">Uncategorized</option>
                {(cat.data?.results || cat.data || [])
                  .filter((x) => x.type === form.type)
                  .map((x) => (
                    <option key={x.id} value={x.id}>
                      {x.name}
                    </option>
                  ))}
              </select>
            </label>
            <label>
              Amount
              <input
                required
                min=".01"
                step="0.01"
                type="number"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
              />
            </label>
            <label>
              Date
              <input
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
              />
            </label>
            <label>
              Description
              <input
                value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
              />
            </label>
            <div className="form-actions">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setForm(null)}
              >
                Cancel
              </Button>
              <Button disabled={save.isPending}>
                {save.isPending ? "Saving…" : "Save transaction"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
