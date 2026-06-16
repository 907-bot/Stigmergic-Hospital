import { useEffect, useState, useCallback } from 'react';
import Head from 'next/head';

const API_BASE = `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:9001`;

interface TimelineEvent {
  type: string;
  status: string;
  created_at: string | null;
  handled_by: string;
  medication_name?: string;
  medication_dosage?: string;
  test_type?: string;
  test_result?: string;
  sbar_situation?: string;
  sbar_assessment?: string;
  escalated?: boolean;
  escalated_from?: string;
}

interface PortalData {
  patient_id: string;
  condition: string;
  severity: number;
  status: string;
  acuity: string;
  vitals: { heart_rate?: number; bp_systolic?: number; bp_diastolic?: number; o2_saturation?: number; temperature?: number };
  current_step: { type: string; strength: number; handled_by: string; acuity?: string; medication_name?: string; medication_dosage?: string; test_type?: string } | null;
  next_step: { next_type: string; role: string; role_label: string; role_icon: string; action: string } | null;
  active_tasks: any[];
  timeline: TimelineEvent[];
}

const ACUITY_COLORS: Record<string, string> = {
  IMMEDIATE: '#d32f2f', URGENT: '#f57c00', STANDARD: '#1976d2', NON_URGENT: '#388e3c',
};

const STEP_ICONS: Record<string, string> = {
  EMERGENCY: '🚨', TRIAGED: '🩺', DIAGNOSED: '📋', LAB_REQUEST: '🔬',
  LAB_COMPLETE: '✅', ICU_REQUEST: '🏥', PRESCRIPTION: '💊',
  BED_READY: '🛏️', TESTS_DONE: '📊', MEDS_DISPENSED: '💉',
  DISPATCHED: '🚑', DETERIORATION: '⚠️', ESCALATED: '🚨',
  CRITICAL_ESCALATION: '🚨🚨',
};

export default function PatientPortal() {
  const [patientId, setPatientId] = useState('');
  const [data, setData] = useState<PortalData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchStatus = useCallback(async () => {
    if (!patientId.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/patient-portal/${patientId.trim()}`);
      if (res.ok) {
        setData(await res.json());
      } else {
        const err = await res.json();
        setError(err.detail || 'Patient not found');
        setData(null);
      }
    } catch (e: any) {
      setError(e.message);
      setData(null);
    }
    setLoading(false);
  }, [patientId]);

  const handleSearch = () => fetchStatus();

  useEffect(() => {
    if (!data) return;
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, [data, fetchStatus]);

  const downloadReport = () => {
    if (!patientId.trim()) return;
    window.open(`${API_BASE}/api/v1/patient-portal/${patientId.trim()}/report`, '_blank');
  };

  const conditionLabel = data?.condition?.replace(/_/g, ' ') || '';

  const badgeStyle = (acuity: string): React.CSSProperties => ({
    display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700,
    color: '#fff', background: ACUITY_COLORS[acuity] || '#999',
  });

  return (
    <div style={{
      maxWidth: 800, margin: '40px auto', padding: '0 20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    }}>
      <Head><title>Patient Portal - Hospital Swarm</title></Head>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span style={{ fontSize: 32 }}>👤</span>
        <h1 style={{ margin: 0, fontSize: 24 }}>Patient Portal</h1>
      </div>

      <div style={{
        background: '#e3f2fd', borderRadius: 8, padding: 16, marginBottom: 24, fontSize: 14,
      }}>
        <strong>👋 Welcome to your Patient Portal</strong>
        <p style={{ margin: '4px 0 0', opacity: 0.7 }}>
          Enter your Patient ID to see what's happening with your care — your current status,
          what the next step is, and who's treating you. You can also download your full medical report.
        </p>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <input
          value={patientId}
          onChange={e => setPatientId(e.target.value)}
          placeholder="Enter your Patient ID (e.g., P1780573130417)"
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          style={{
            flex: 1, padding: '12px 16px', borderRadius: 6, border: '1px solid #ccc', fontSize: 15,
          }}
        />
        <button onClick={handleSearch} disabled={loading}
          style={{
            padding: '12px 24px', borderRadius: 6, border: 'none', cursor: 'pointer',
            fontWeight: 600, fontSize: 15, background: '#1976d2', color: '#fff',
            opacity: loading ? 0.6 : 1,
          }}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && (
        <div style={{ padding: 12, borderRadius: 6, background: '#ffebee', color: '#c62828', marginBottom: 16 }}>
          {error}
        </div>
      )}

      {data && (
        <>
          <div style={{
            border: '1px solid #e0e0e0', borderRadius: 12, padding: 24, marginBottom: 24,
            background: '#fafafa',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2 style={{ margin: '0 0 4px', fontSize: 20 }}>
                  Welcome, Patient {data.patient_id}
                </h2>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
                  <span style={{
                    display: 'inline-block', padding: '4px 12px', borderRadius: 12,
                    fontSize: 13, fontWeight: 600, color: '#fff',
                    background: data.status === 'waiting' ? '#f57c00' : data.status === 'being_treated' ? '#1976d2' : '#388e3c',
                  }}>
                    {data.status.replace('_', ' ').toUpperCase()}
                  </span>
                  {data.acuity && <span style={badgeStyle(data.acuity)}>{data.acuity}</span>}
                </div>
              </div>
              <button onClick={downloadReport}
                style={{
                  padding: '10px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
                  fontWeight: 600, fontSize: 14, background: '#388e3c', color: '#fff',
                  whiteSpace: 'nowrap',
                }}>
                📄 Download Report
              </button>
            </div>

            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 14, marginTop: 16,
            }}>
              <div><strong>Condition:</strong> {conditionLabel}</div>
              <div><strong>Severity:</strong> {data.severity.toFixed(2)}</div>
            </div>

            {data.vitals.heart_rate && (
              <div style={{
                marginTop: 16, padding: '12px 16px', background: '#e8f5e9', borderRadius: 8,
                fontSize: 14,
              }}>
                <strong>🫀 Your Vitals:</strong>{' '}
                HR: {data.vitals.heart_rate} bpm · BP: {data.vitals.bp_systolic}/{data.vitals.bp_diastolic} mmHg · O2: {data.vitals.o2_saturation}% · Temp: {data.vitals.temperature}°C
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
            {data.current_step && (
              <div style={{ flex: 1, border: '1px solid #e0e0e0', borderRadius: 8, padding: 16 }}>
                <div style={{ fontSize: 13, opacity: 0.6, marginBottom: 4 }}>Currently happening</div>
                <div style={{ fontSize: 24, marginBottom: 4 }}>
                  {STEP_ICONS[data.current_step.type] || '📌'}
                </div>
                <div style={{ fontWeight: 600, fontSize: 16 }}>
                  {data.current_step.type.replace('_', ' ')}
                </div>
                <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>
                  Being handled by: <strong>{data.current_step.handled_by}</strong>
                </div>
                {data.current_step.medication_name && (
                  <div style={{ fontSize: 13, marginTop: 4 }}>
                    💊 {data.current_step.medication_name} — {data.current_step.medication_dosage}
                  </div>
                )}
                {data.current_step.test_type && (
                  <div style={{ fontSize: 13, marginTop: 4 }}>
                    🔬 Test: {data.current_step.test_type}
                  </div>
                )}
              </div>
            )}
            {data.next_step && (
              <div style={{ flex: 1, border: '1px solid #e0e0e0', borderRadius: 8, padding: 16 }}>
                <div style={{ fontSize: 13, opacity: 0.6, marginBottom: 4 }}>Next step</div>
                <div style={{ fontSize: 24, marginBottom: 4 }}>
                  {data.next_step.role_icon}
                </div>
                <div style={{ fontWeight: 600, fontSize: 16 }}>
                  {data.next_step.role_label}
                </div>
                <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>
                  Will: <strong>{data.next_step.action}</strong>
                </div>
                {data.next_step.next_type !== 'completed' && (
                  <div style={{ fontSize: 13, color: '#666', marginTop: 2 }}>
                    Creates: {data.next_step.next_type.replace('_', ' ')}
                  </div>
                )}
              </div>
            )}
          </div>

          <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, padding: 20, marginBottom: 24 }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16 }}>📋 Your Care Timeline</h3>
            <div style={{ position: 'relative' }}>
              <div style={{
                position: 'absolute', left: 15, top: 0, bottom: 0, width: 2, background: '#e0e0e0',
              }} />
              {data.timeline.map((event, i) => (
                <div key={i} style={{ display: 'flex', gap: 16, marginBottom: 14, position: 'relative' }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', fontSize: 16, zIndex: 1, flexShrink: 0,
                    background: event.status === 'active' ? '#e3f2fd' : '#f5f5f5',
                    border: '2px solid', borderColor: event.status === 'active' ? '#1976d2' : '#ccc',
                  }}>
                    {STEP_ICONS[event.type] || '📌'}
                  </div>
                  <div style={{
                    flex: 1, padding: 10, borderRadius: 6, border: '1px solid #e0e0e0',
                    background: event.status === 'active' ? '#fafafa' : '#f5f5f5',
                    opacity: event.status === 'completed' ? 0.7 : 1,
                  }}>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>
                      {event.type.replace('_', ' ')}
                      <span style={{
                        display: 'inline-block', marginLeft: 8, fontSize: 11,
                        color: event.status === 'active' ? '#1976d2' : '#888',
                      }}>
                        {event.status === 'active' ? '🟢 In Progress' : '✅ Done'}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>
                      By {event.handled_by}
                      {event.created_at && ` · ${new Date(event.created_at).toLocaleString()}`}
                    </div>
                    {event.medication_name && (
                      <div style={{ fontSize: 13, marginTop: 4 }}>💊 {event.medication_name} — {event.medication_dosage}</div>
                    )}
                    {event.test_type && (
                      <div style={{ fontSize: 13, marginTop: 4 }}>
                        🔬 {event.test_type}{event.test_result ? ` → ${event.test_result}` : ''}
                      </div>
                    )}
                    {event.sbar_situation && (
                      <div style={{ fontSize: 12, marginTop: 4, fontStyle: 'italic', color: '#666' }}>
                        "{event.sbar_situation}"
                      </div>
                    )}
                    {event.escalated && (
                      <div style={{ fontSize: 13, marginTop: 4, color: '#d32f2f' }}>
                        ⚠ Urgent attention needed — escalated from {event.escalated_from}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <button onClick={downloadReport}
              style={{
                padding: '12px 32px', borderRadius: 6, border: 'none', cursor: 'pointer',
                fontWeight: 600, fontSize: 15, background: '#388e3c', color: '#fff',
              }}>
              📄 Download Full Medical Report
            </button>
          </div>
        </>
      )}

      <div style={{ textAlign: 'center', marginTop: 32 }}>
        <a href="/" style={{ color: '#1976d2', fontSize: 14 }}>← Back to Main Dashboard</a>
      </div>
    </div>
  );
}
