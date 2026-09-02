import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api';
import { Badge, Button, Card, Empty, Loading, Modal, PageHeader } from '../components/UI';

const list = (d) => d?.results || d || [];

function formatDateTime(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

function getDeviceIcon(device = '') {
  const d = device.toLowerCase();
  if (d.includes('phone') || d.includes('android') || d.includes('ios')) return '📱';
  if (d.includes('ipad') || d.includes('tablet')) return '📱';
  if (d.includes('mac') || d.includes('windows') || d.includes('linux') || d.includes('chrome') || d.includes('firefox')) return '💻';
  return '🌐';
}

export default function LoginActivity({ showHeader = false }) {
  const qc = useQueryClient();
  const [revokeTarget, setRevokeTarget] = useState(null);

  const sessionsQuery = useQuery({
    queryKey: ['login-sessions'],
    queryFn: () => api.get('auth/sessions/').then((r) => r.data),
  });

  const revokeMutation = useMutation({
    mutationFn: (id) => api.delete(`auth/sessions/${id}/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['login-sessions'] });
      setRevokeTarget(null);
    },
  });

  const rows = list(sessionsQuery.data);

  return (
    <>
      {showHeader && (
        <PageHeader eyebrow="SECURITY & SESSIONS" title="Login activity">
          <Button variant="secondary" onClick={() => sessionsQuery.refetch()}>
            Refresh
          </Button>
        </PageHeader>
      )}

      <Card className="section-card">
        <div className="toolbar">
          <span>Active sessions & login history</span>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span>{rows.length} {rows.length === 1 ? 'session' : 'sessions'}</span>
            <Button variant="secondary" className="btn-sm" onClick={() => sessionsQuery.refetch()}>
              Refresh
            </Button>
          </div>
        </div>

        {sessionsQuery.isLoading ? (
          <Loading lines={4} />
        ) : rows.length > 0 ? (
          <div className="session-list">
            {rows.map((s) => (
              <article className={`session-row ${s.is_current ? 'current-session' : ''}`} key={s.id}>
                <div className="session-icon">{getDeviceIcon(s.device)}</div>
                <div className="session-info">
                  <div className="session-title-line">
                    <strong>{s.device || 'Unknown device'}</strong>
                    {s.is_current && <Badge tone="success">Current session</Badge>}
                    {!s.is_current && <Badge tone="neutral">Active</Badge>}
                  </div>
                  <div className="session-meta">
                    <span>IP: {s.ip_address || '—'}</span>
                    <span>•</span>
                    <span>Location: {s.location || 'Unknown location'}</span>
                    <span>•</span>
                    <span>Signed in: {formatDateTime(s.login_at)}</span>
                  </div>
                </div>
                <div className="session-action">
                  {s.is_current ? (
                    <span className="session-current-label">This device</span>
                  ) : (
                    <button
                      className="revoke-btn danger-text"
                      type="button"
                      onClick={() => setRevokeTarget(s)}
                    >
                      Revoke
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <Empty
            title="No login activity found"
            text="Your session history will appear here once you sign in."
          />
        )}
      </Card>

      {revokeTarget && (
        <Modal title="Revoke session" onClose={() => setRevokeTarget(null)}>
          <div className="revoke-modal-content">
            <p>
              Are you sure you want to revoke the session on <strong>{revokeTarget.device || 'this device'}</strong>?
            </p>
            <p className="field-hint" style={{ fontSize: '12px', color: '#8890a2', marginTop: '6px' }}>
              IP: {revokeTarget.ip_address || '—'} • Signed in {formatDateTime(revokeTarget.login_at)}
            </p>
            <div className="form-actions" style={{ marginTop: '20px' }}>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setRevokeTarget(null)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                className="btn-danger"
                disabled={revokeMutation.isPending}
                onClick={() => revokeMutation.mutate(revokeTarget.id)}
              >
                {revokeMutation.isPending ? 'Revoking…' : 'Yes, revoke session'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
