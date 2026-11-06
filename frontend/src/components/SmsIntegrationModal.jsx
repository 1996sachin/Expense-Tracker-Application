import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';
import { Button, Modal, Loading, Badge } from './UI';

export default function SmsIntegrationModal({ onClose }) {
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState('tester'); // 'tester' | 'keys' | 'ios' | 'android'
  const [smsText, setSmsText] = useState(
    'Your eSewa ID has been debited for NPR 500.00 on 2026-09-28 for payment to Foodmandu. Trx ID: 12345ABC. Available Balance: NPR 1250.00'
  );
  const [sender, setSender] = useState('eSewa');
  const [testResult, setTestResult] = useState(null);
  const [ingestResult, setIngestResult] = useState(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(false);

  const tokenQuery = useQuery({
    queryKey: ['sms-token'],
    queryFn: () => api.get('auth/sms-token/').then((r) => r.data),
  });

  const regenMutation = useMutation({
    mutationFn: () => api.post('auth/sms-token/regenerate/'),
    onSuccess: (res) => {
      qc.setQueryData(['sms-token'], (prev) => ({
        ...prev,
        sms_api_key: res.data.sms_api_key,
      }));
    },
  });

  const testMutation = useMutation({
    mutationFn: () => api.post('transactions/sms-test/', { body: smsText, sender }),
    onSuccess: (res) => {
      setTestResult(res.data);
      setIngestResult(null);
    },
  });

  const ingestMutation = useMutation({
    mutationFn: () => api.post('transactions/sms-ingest/', { body: smsText, sender }),
    onSuccess: (res) => {
      setIngestResult(res.data);
      setTestResult(null);
      qc.invalidateQueries({ queryKey: ['transactions'] });
      qc.invalidateQueries({ queryKey: ['accounts'] });
    },
  });

  const sampleMessages = [
    {
      label: 'eSewa Foodmandu',
      sender: 'eSewa',
      body: 'Your eSewa ID has been debited for NPR 500.00 on 2026-09-28 for payment to Foodmandu. Trx ID: 12345ABC. Available Balance: NPR 1250.00',
    },
    {
      label: 'Nabil Bhatbhateni (Fonepay)',
      sender: 'Nabil',
      body: 'Dear Customer, your a/c ...1234 has been debited by NPR 850.00 on 2026-09-28 for POS/QR purchase at Bhatbhateni. Ref/Txn: FP123987. Avl Bal: NPR 25,400.00',
    },
    {
      label: 'NIC Asia Himalayan Java',
      sender: 'NIC Asia',
      body: 'A/C *1234 debited for NPR 1,200.00 towards Fonepay: Himalayan Java. TrxID: 981247. Available Balance: Rs. 15,200.00',
    },
    {
      label: 'Salary Credit (Income)',
      sender: 'GlobalIME',
      body: 'A/C ...4321 Credited with NPR 50,000.00 on 2026-09-28 by Salary. Avl Bal: NPR 65,000.00. Ref: 112233',
    },
    {
      label: 'eSewa Pathao',
      sender: 'eSewa',
      body: 'Dear User, NPR 120.00 has been debited from your eSewa a/c for Pathao. Ref: 98765. Bal: 450.00',
    },
  ];

  const handleCopy = (text, type) => {
    navigator.clipboard?.writeText(text);
    if (type === 'key') {
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    } else {
      setCopiedUrl(true);
      setTimeout(() => setCopiedUrl(false), 2000);
    }
  };

  const webhookUrl = tokenQuery.data?.webhook_url || `${window.location.origin.replace('5173', '8000').replace('5175', '8001')}/api/transactions/sms-ingest/`;
  const smsKey = tokenQuery.data?.sms_api_key || 'Loading...';

  return (
    <Modal title="📱 SMS Auto-Tracking & Webhook" onClose={onClose}>
      <div style={{ maxWidth: 680, minWidth: 320, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid #e2e8f0', paddingBottom: 10 }}>
          <Button
            type="button"
            variant={activeTab === 'tester' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('tester')}
          >
            🧪 Test SMS Parser
          </Button>
          <Button
            type="button"
            variant={activeTab === 'keys' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('keys')}
          >
            🔑 Webhook & Keys
          </Button>
          <Button
            type="button"
            variant={activeTab === 'ios' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('ios')}
          >
            🍏 iPhone Setup
          </Button>
          <Button
            type="button"
            variant={activeTab === 'android' ? 'primary' : 'secondary'}
            onClick={() => setActiveTab('android')}
          >
            🤖 Android Setup
          </Button>
        </div>

        {/* Tab 1: Live SMS Tester */}
        {activeTab === 'tester' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <p style={{ margin: 0, fontSize: 13, color: '#64748b' }}>
              Test how your bank and eSewa SMS are automatically parsed into transactions, merchants, and categories.
            </p>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {sampleMessages.map((sample) => (
                <button
                  key={sample.label}
                  type="button"
                  style={{
                    fontSize: 12,
                    padding: '4px 8px',
                    borderRadius: 6,
                    border: '1px solid #cbd5e1',
                    background: '#f8fafc',
                    cursor: 'pointer',
                  }}
                  onClick={() => {
                    setSmsText(sample.body);
                    setSender(sample.sender);
                    setTestResult(null);
                    setIngestResult(null);
                  }}
                >
                  {sample.label}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                  Sender Name / ID
                </label>
                <input
                  type="text"
                  value={sender}
                  onChange={(e) => setSender(e.target.value)}
                  placeholder="e.g. eSewa, Nabil, NIC Asia"
                  style={{ width: '100%', padding: '6px 10px', borderRadius: 6, border: '1px solid #cbd5e1' }}
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                Incoming SMS Message Text
              </label>
              <textarea
                rows={3}
                value={smsText}
                onChange={(e) => setSmsText(e.target.value)}
                placeholder="Paste your bank or eSewa SMS here..."
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: 6,
                  border: '1px solid #cbd5e1',
                  fontFamily: 'monospace',
                  fontSize: 13,
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <Button
                type="button"
                variant="secondary"
                disabled={testMutation.isPending}
                onClick={() => testMutation.mutate()}
              >
                {testMutation.isPending ? 'Analyzing…' : '🔍 Preview Extraction'}
              </Button>
              <Button
                type="button"
                variant="primary"
                disabled={ingestMutation.isPending}
                onClick={() => ingestMutation.mutate()}
              >
                {ingestMutation.isPending ? 'Recording…' : '⚡ Ingest as Real Transaction'}
              </Button>
            </div>

            {/* Test Results Display */}
            {testResult && (
              <div
                style={{
                  padding: 12,
                  background: testResult.is_transaction ? '#f0fdf4' : '#fef2f2',
                  border: `1px solid ${testResult.is_transaction ? '#bbf7d0' : '#fecaca'}`,
                  borderRadius: 8,
                  fontSize: 13,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <strong>{testResult.is_transaction ? '✅ Recognized Transaction' : '⚠️ Ignored Message'}</strong>
                  {testResult.parsed && (
                    <Badge tone={testResult.parsed.type === 'income' ? 'success' : 'neutral'}>
                      {testResult.parsed.type?.toUpperCase()}
                    </Badge>
                  )}
                </div>
                {testResult.is_transaction ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 8 }}>
                    <div>
                      <small style={{ color: '#64748b' }}>Amount:</small>
                      <div>
                        <b>
                          {testResult.parsed.currency} {testResult.parsed.amount}
                        </b>
                      </div>
                    </div>
                    <div>
                      <small style={{ color: '#64748b' }}>Merchant:</small>
                      <div>
                        <b>{testResult.parsed.merchant}</b>
                      </div>
                    </div>
                    <div>
                      <small style={{ color: '#64748b' }}>Category:</small>
                      <div>
                        <span
                          style={{
                            display: 'inline-block',
                            background: testResult.predicted_category?.color || '#cbd5e1',
                            color: '#fff',
                            padding: '2px 6px',
                            borderRadius: 4,
                            fontSize: 11,
                          }}
                        >
                          {testResult.predicted_category?.name}
                        </span>
                      </div>
                    </div>
                    <div>
                      <small style={{ color: '#64748b' }}>Trx ID / Ref:</small>
                      <div>
                        <code>{testResult.parsed.reference_id || 'N/A'}</code>
                      </div>
                    </div>
                    {testResult.parsed.balance !== null && (
                      <div>
                        <small style={{ color: '#64748b' }}>Remaining Bal:</small>
                        <div>NPR {testResult.parsed.balance}</div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p style={{ margin: 0, color: '#991b1b' }}>{testResult.reason}</p>
                )}
              </div>
            )}

            {/* Ingest Results Display */}
            {ingestResult && (
              <div
                style={{
                  padding: 12,
                  background: ingestResult.status === 'success' ? '#f0fdf4' : ingestResult.status === 'duplicate' ? '#eff6ff' : '#fef2f2',
                  border: `1px solid ${ingestResult.status === 'success' ? '#86efac' : '#93c5fd'}`,
                  borderRadius: 8,
                  fontSize: 13,
                }}
              >
                <strong>
                  {ingestResult.status === 'success'
                    ? '🎉 Transaction Successfully Created!'
                    : ingestResult.status === 'duplicate'
                    ? '🛡️ Duplicate Prevented (TrxID Match)'
                    : 'ℹ️ ' + ingestResult.status}
                </strong>
                <p style={{ margin: '4px 0 0 0' }}>{ingestResult.message}</p>
                {ingestResult.transaction && (
                  <div style={{ marginTop: 6, fontSize: 12, color: '#334155' }}>
                    Account: <b>{ingestResult.transaction.account}</b> | Category:{' '}
                    <b>{ingestResult.transaction.category}</b> | Amount:{' '}
                    <b>NPR {ingestResult.transaction.amount}</b>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Webhook & Keys */}
        {activeTab === 'keys' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                Your SMS Ingestion Webhook URL
              </label>
              <div style={{ display: 'flex', gap: 6 }}>
                <input
                  readOnly
                  value={webhookUrl}
                  style={{
                    flex: 1,
                    fontFamily: 'monospace',
                    fontSize: 12,
                    padding: '8px 10px',
                    borderRadius: 6,
                    border: '1px solid #cbd5e1',
                    background: '#f8fafc',
                  }}
                />
                <Button type="button" variant="secondary" onClick={() => handleCopy(webhookUrl, 'url')}>
                  {copiedUrl ? 'Copied!' : 'Copy'}
                </Button>
              </div>
            </div>

            <div>
              <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                Secret SMS API Key
              </label>
              <div style={{ display: 'flex', gap: 6 }}>
                <input
                  readOnly
                  type="password"
                  value={smsKey}
                  style={{
                    flex: 1,
                    fontFamily: 'monospace',
                    fontSize: 12,
                    padding: '8px 10px',
                    borderRadius: 6,
                    border: '1px solid #cbd5e1',
                    background: '#f8fafc',
                  }}
                />
                <Button type="button" variant="secondary" onClick={() => handleCopy(smsKey, 'key')}>
                  {copiedKey ? 'Copied!' : 'Copy'}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={regenMutation.isPending}
                  onClick={() => {
                    if (window.confirm('Regenerate key? Your current iOS shortcut or Android task will need to be updated with the new key.')) {
                      regenMutation.mutate();
                    }
                  }}
                >
                  {regenMutation.isPending ? 'Regenerating…' : 'Rotate'}
                </Button>
              </div>
            </div>

            <div
              style={{
                padding: 12,
                borderRadius: 8,
                background: '#f1f5f9',
                fontSize: 12,
                color: '#475569',
                lineHeight: 1.5,
              }}
            >
              <strong>🔒 Least-Privilege Security Guaranteed</strong>
              <br />
              This key is strictly <b>Insert-Only</b>. Even if exposed, it cannot read transactions, balances, or user
              credentials. It can only submit incoming SMS for automated processing.
            </div>
          </div>
        )}

        {/* Tab 3: iPhone Setup */}
        {activeTab === 'ios' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13, lineHeight: 1.5 }}>
            <h4 style={{ margin: 0, color: '#1e293b' }}>🍏 iOS Shortcuts Automation Setup</h4>
            <ol style={{ paddingLeft: 20, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
              <li>
                Open the <b>Shortcuts</b> app on your iPhone and tap the <b>Automation</b> tab at the bottom.
              </li>
              <li>
                Tap <b>+ (Add Automation)</b> and select <b>Message</b>.
              </li>
              <li>
                Set <b>Message Contains</b> to your bank keywords. Tip: iOS matches exact strings, so add triggers for:
                <code style={{ background: '#f1f5f9', padding: '2px 4px', borderRadius: 4, margin: '0 4px' }}>
                  debited
                </code>
                ,
                <code style={{ background: '#f1f5f9', padding: '2px 4px', borderRadius: 4, margin: '0 4px' }}>
                  credited
                </code>
                ,
                <code style={{ background: '#f1f5f9', padding: '2px 4px', borderRadius: 4, margin: '0 4px' }}>
                  eSewa
                </code>
                ,
                <code style={{ background: '#f1f5f9', padding: '2px 4px', borderRadius: 4, margin: '0 4px' }}>
                  NPR
                </code>
                ,
                <code style={{ background: '#f1f5f9', padding: '2px 4px', borderRadius: 4, margin: '0 4px' }}>
                  Rs
                </code>
                .
              </li>
              <li>
                Choose <b>Run Immediately</b> and turn OFF <i>Ask Before Running</i>.
              </li>
              <li>
                Tap <b>New Blank Automation</b> &rarr; tap <b>Add Action</b>.
              </li>
              <li>
                Search for <b>Get Contents of URL</b> and configure:
                <ul style={{ margin: '4px 0', paddingLeft: 16 }}>
                  <li>
                    URL: <code style={{ wordBreak: 'break-all' }}>{webhookUrl}</code>
                  </li>
                  <li>
                    Method: <b>POST</b>
                  </li>
                  <li>
                    Headers:
                    <br />
                    <code>X-Pocketly-Key</code> : <code>{smsKey}</code>
                    <br />
                    <code>Content-Type</code> : <code>application/json</code>
                  </li>
                  <li>
                    Request Body: <b>JSON</b>
                    <br />
                    Key <code>body</code> &rarr; select <b>Shortcut Input</b>
                    <br />
                    Key <code>sender</code> &rarr; select <b>Sender</b>
                  </li>
                </ul>
              </li>
              <li>
                <b>Important:</b> Tap the Play (&#9654;) button once inside Shortcuts to allow network access. When
                prompted, select <b>Always Allow</b> so it runs seamlessly in the background without interruptions!
              </li>
            </ol>
          </div>
        )}

        {/* Tab 4: Android Setup */}
        {activeTab === 'android' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13, lineHeight: 1.5 }}>
            <h4 style={{ margin: 0, color: '#1e293b' }}>🤖 Android Automation (MacroDroid / Tasker)</h4>
            <p style={{ margin: 0 }}>
              On Android, you can use <b>MacroDroid</b> (free, easiest) or <b>Tasker</b> to forward incoming SMS straight
              to your Pocketly endpoint in the background with zero battery drain.
            </p>
            <ol style={{ paddingLeft: 20, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
              <li>
                Install <b>MacroDroid</b> from Google Play Store.
              </li>
              <li>
                Tap <b>Add Macro</b>:
                <ul style={{ margin: '4px 0', paddingLeft: 16 }}>
                  <li>
                    <b>Trigger (+):</b> Connectivity &rarr; SMS Received &rarr; Any Content (or match eSewa / Bank
                    sender).
                  </li>
                  <li>
                    <b>Action (+):</b> Connectivity &rarr; <b>HTTP Request</b>:
                    <br />• Method: <b>POST</b>
                    <br />• URL: <code>{webhookUrl}</code>
                    <br />• Header: <code>X-Pocketly-Key: {smsKey}</code>
                    <br />• Content-Type: <code>application/json</code>
                    <br />• Request Body:
                    <pre
                      style={{
                        background: '#0f172a',
                        color: '#38bdf8',
                        padding: 8,
                        borderRadius: 6,
                        margin: '4px 0',
                        fontSize: 11,
                      }}
                    >
                      {`{\n  "body": "{sms_message}",\n  "sender": "{sms_number}"\n}`}
                    </pre>
                  </li>
                </ul>
              </li>
              <li>Save and enable the macro. Whenever eSewa or your bank texts you, it instantly logs into Pocketly!</li>
            </ol>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
          <Button type="button" variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}
