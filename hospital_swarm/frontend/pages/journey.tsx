import { useEffect, useState, useCallback } from 'react';

const API_BASE = `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:9001`;

interface PheromoneEvent {
  pheromone_id: string;
  type: string;
  status: string;
  strength: number;
  created_at: string | null;
  acuity?: string;
  escalated?: boolean;
  escalated_from?: string;
  medication_name?: string;
  medication_dosage?: string;
  test_type?: string;
  test_result?: string;
  sbar_situation?: string;
  sbar_assessment?: string;
}

interface JourneyData {
  patient_id: string;
  condition: string;
  severity: number;
  status: string;
  vitals: { heart_rate?: number; bp_systolic?: number; bp_diastolic?: number; o2_saturation?: number; temperature?: number };
  timeline: PheromoneEvent[];
}

const ACUITY_COLORS: Record<string, string> = {
  IMMEDIATE: '#d32f2f', URGENT: '#f57c00', STANDARD: '#1976d2', NON_URGENT: '#388e3c',
};

const EVENT_ICONS: Record<string, string> = {
  EMERGENCY: '🚨', TRIAGED: '🩺', DIAGNOSED: '📋', LAB_REQUEST: '🔬',
  LAB_COMPLETE: '✅', ICU_REQUEST: '🏥', PRESCRIPTION: '💊',
  BED_READY: '🛏️', TESTS_DONE: '📊', MEDS_DISPENSED: '💉',
  DISPATCHED: '🚑', DETERIORATION: '⚠️', ESCALATED: '🚨',
  CRITICAL_ESCALATION: '🚨🚨', RESOURCE_SHORTAGE: '🔴',
};

export default function JourneyPage() {
  const [patientId, setPatientId] = useState('');
  const [journey, setJourney] = useState<JourneyData | null>(null);
  const [error, setError] = useState('');

  const fetchJourney = useCallback(async () => {
    if (!patientId.trim()) return;
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/journey/${patientId.trim()}`);
      if (res.ok) {
        setJourney(await res.json());
      } else {
        const err = await res.json();
        setError(err.detail || 'Patient not found');
        setJourney(null);
      }
    } catch (e: any) {
      setError(e.message);
      setJourney(null);
    }
  }, [patientId]);

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: '0 20px', fontFamily: '-apple-system, sans-serif' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span style={{ fontSize: 28 }}>📋</span>
        <h1 style={{ margin: 0, fontSize: 24 }}>Patient Journey Timeline</h1>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <input
          value={patientId}
          onChange={e => setPatientId(e.target.value)}
          placeholder="Enter patient ID (e.g., P1780573130417)"
          style={{
            flex: 1, padding: '10px 14px', borderRadius: 6, border: '1px solid #ccc', fontSize: 14,
          }}
          onKeyDown={e => e.key === 'Enter' && fetchJourney()}
        />
        <button onClick={fetchJourney}
          style={{
            padding: '10px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
            fontWeight: 600, background: '#1976d2', color: '#fff', fontSize: 14,
          }}>
          Search
        </button>
      </div>

      {error && (
        <div style={{ padding: 12, borderRadius: 6, background: '#ffebee', color: '#c62828', marginBottom: 16 }}>
          {error}
        </div>
      )}

      {journey && (
        <>
          <div style={{
            border: '1px solid #e0e0e0', borderRadius: 8, padding: 20, marginBottom: 24,
          }}>
            <h2 style={{ margin: '0 0 12px', fontSize: 18 }}>Patient {journey.patient_id}</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 14 }}>
              <div><strong>Condition:</strong> {journey.condition}</div>
              <div><strong>Severity:</strong> {journey.severity.toFixed(2)}</div>
              <div><strong>Status:</strong> {journey.status}</div>
              <div><strong>Timeline events:</strong> {journey.timeline.length}</div>
            </div>
            {journey.vitals.heart_rate && (
              <div style={{ marginTop: 12, padding: '8px 12px', background: '#f5f5f5', borderRadius: 6, fontSize: 13 }}>
                <strong>Latest Vitals:</strong> HR {journey.vitals.heart_rate} · BP {journey.vitals.bp_systolic}/{journey.vitals.bp_diastolic} · O2 {journey.vitals.o2_saturation}% · Temp {journey.vitals.temperature}°C
              </div>
            )}
          </div>

          <div style={{ position: 'relative' }}>
            <div style={{
              position: 'absolute', left: 15, top: 0, bottom: 0, width: 2, background: '#e0e0e0',
            }} />
            {journey.timeline.map((event, i) => (
              <div key={event.pheromone_id} style={{ display: 'flex', gap: 16, marginBottom: 16, position: 'relative' }}>
                <div style={{
                  width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', fontSize: 16, zIndex: 1, flexShrink: 0,
                  background: event.status === 'active' ? '#e3f2fd' : '#f5f5f5',
                  border: '2px solid', borderColor: event.status === 'active' ? '#1976d2' : '#ccc',
                }}>
                  {EVENT_ICONS[event.type] || '📌'}
                </div>
                <div style={{
                  flex: 1, padding: 12, borderRadius: 8, border: '1px solid #e0e0e0',
                  background: event.status === 'active' ? '#fafafa' : '#f5f5f5',
                  opacity: event.status === 'completed' ? 0.7 : 1,
                }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>
                    {event.type}
                    {event.acuity && (
                      <span style={{
                        display: 'inline-block', padding: '1px 6px', borderRadius: 3, fontSize: 10,
                        fontWeight: 700, color: '#fff', background: ACUITY_COLORS[event.acuity] || '#999',
                        marginLeft: 8, verticalAlign: 'middle',
                      }}>{event.acuity}</span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, opacity: 0.5, marginTop: 2 }}>
                    {event.created_at ? new Date(event.created_at).toLocaleString() : ''}
                    {' · '}Strength: {event.strength.toFixed(2)} · {event.status}
                  </div>
                  {event.medication_name && (
                    <div style={{ fontSize: 13, marginTop: 4 }}>💊 {event.medication_name} — {event.medication_dosage}</div>
                  )}
                  {event.test_type && (
                    <div style={{ fontSize: 13, marginTop: 4 }}>🔬 {event.test_type}{event.test_result ? ` → ${event.test_result}` : ''}</div>
                  )}
                  {event.sbar_situation && (
                    <div style={{ fontSize: 13, marginTop: 4, fontStyle: 'italic', opacity: 0.7 }}>{event.sbar_situation}</div>
                  )}
                  {event.escalated && (
                    <div style={{ fontSize: 13, marginTop: 4, color: '#d32f2f' }}>
                      ⚠ Escalated from: {event.escalated_from}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div style={{ textAlign: 'center', marginTop: 32 }}>
        <a href="/" style={{ color: '#1976d2', fontSize: 14 }}>← Back to Dashboard</a>
      </div>
    </div>
  );
}
