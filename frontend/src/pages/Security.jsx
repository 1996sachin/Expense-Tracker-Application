import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api';
import { Button, Modal } from '../components/UI';

export default function Security({ showHeader = false }) {
  const qc = useQueryClient();
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState('');
  const [codes, setCodes] = useState([]);

  const status = useQuery({
    queryKey: ['mfa-status'],
    queryFn: () => api.get('auth/mfa/status/').then((r) => r.data),
  });

  const start = useMutation({
    mutationFn: () => api.post('auth/mfa/setup/totp/').then((r) => r.data),
    onSuccess: setSetup,
  });

  const enable = useMutation({
    mutationFn: () => api.post('auth/mfa/enable/totp/', { code }).then((r) => r.data),
    onSuccess: (d) => {
      setCodes(d.recovery_codes || []);
      setSetup(null);
      setCode('');
      qc.invalidateQueries({ queryKey: ['mfa-status'] });
    },
  });

  const email = useMutation({
    mutationFn: () => api.post('auth/mfa/enable/email/').then((r) => r.data),
    onSuccess: (d) => {
      setCodes(d.recovery_codes || []);
      qc.invalidateQueries({ queryKey: ['mfa-status'] });
    },
  });

  return (
    <section className="security">
      {showHeader && (
        <>
          <p className="eyebrow">ACCOUNT PROTECTION</p>
          <h2>Security</h2>
          <p>Keep your Pocketly account protected.</p>
        </>
      )}
      <article>
        <h3>Authenticator App</h3>
        <p>{status.data?.totp_enabled ? 'Protected with an authenticator app' : 'Not enabled'}</p>
        {!status.data?.totp_enabled && (
          <button className="primary" onClick={() => start.mutate()}>
            Set up
          </button>
        )}
      </article>
      <article>
        <h3>Email Verification Code</h3>
        <p>{status.data?.email_otp_enabled ? 'Enabled' : 'Not enabled'}</p>
        {!status.data?.email_otp_enabled && (
          <button className="primary" onClick={() => email.mutate()}>
            Enable
          </button>
        )}
      </article>
      <article>
        <h3>Recovery Codes</h3>
        <p>{status.data?.recovery_codes_remaining || 0} recovery codes remaining</p>
        <button
          className="primary"
          onClick={async () =>
            setCodes((await api.post('auth/mfa/recovery-codes/')).data.recovery_codes)
          }
        >
          Generate new codes
        </button>
      </article>
      {setup && (
        <div className="modal">
          <div className="mfa-setup">
            <h2>Set up authenticator app</h2>
            <p>Scan this QR code, then enter its 6-digit verification code.</p>
            <img src={setup.qr_code} alt="Pocketly authenticator setup QR code" />
            <details>
              <summary>Can't scan? Show setup key</summary>
              <code>{setup.setup_key}</code>
            </details>
            <input
              value={code}
              maxLength="6"
              placeholder="6-digit code"
              onChange={(e) => setCode(e.target.value)}
            />
            <button onClick={() => enable.mutate()}>Verify and enable</button>
            <button
              type="button"
              className="plain"
              style={{ marginTop: '8px' }}
              onClick={() => setSetup(null)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      {codes.length > 0 && (
        <div className="modal">
          <div className="mfa-setup">
            <h2>Save your recovery codes</h2>
            <p>These codes are shown only now. Store them somewhere safe.</p>
            <pre>{codes.join('\n')}</pre>
            <button onClick={() => setCodes([])}>Done</button>
          </div>
        </div>
      )}
    </section>
  );
}
