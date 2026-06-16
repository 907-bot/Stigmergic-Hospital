import { useEffect, useState, useCallback } from 'react';

const API_BASE = `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:9001`;

interface Task {
  id: string;
  type: string;
  strength: number;
  patient_id: string;
  action: string;
  role: string;
  created_at: string | null;
  acuity?: string;
  escalated?: boolean;
  escalated_from?: string;
  medication_name?: string;
  medication_dosage?: string;
  test_type?: string;
  test_result?: string;
  sbar_situation?: string;
  sbar_background?: string;
  sbar_assessment?: string;
  sbar_recommendation?: string;
  vitals_hr?: number;
  vitals_bp_systolic?: number;
  vitals_bp_diastolic?: number;
  vitals_o2?: number;
  vitals_temp?: number;
}

interface ResourceStatus {
  [key: string]: { total: number; used: number; available: number; label: string };
}

const ACUITY_COLORS: Record<string, string> = {
  IMMEDIATE: '#d32f2f', URGENT: '#f57c00', STANDARD: '#1976d2', NON_URGENT: '#388e3c',
};

export default function RoleDashboard({ role, title, icon }: {
  role: string; title: string; icon: string;
}) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [resources, setResources] = useState<ResourceStatus | null>(null);
  const [expandedTask, setExpandedTask] = useState<string | null>(null);

  const [sbarForm, setSbarForm] = useState({ situation: '', background: '', assessment: '', recommendation: '' });

  const [labMode, setLabMode] = useState<{ taskId: string; test_type: string; test_result: string } | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/tasks/?role=${role}`);
      if (res.ok) setTasks(await res.json());
    } catch (e) { console.error('Failed to fetch tasks', e); }
  }, [role]);

  const fetchResources = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/resources/`);
      if (res.ok) setResources(await res.json());
    } catch (e) { /* ignore */ }
  }, []);

  useEffect(() => {
    fetchTasks();
    fetchResources();
    const interval = setInterval(() => { fetchTasks(); fetchResources(); }, 5000);
    return () => clearInterval(interval);
  }, [fetchTasks, fetchResources]);

  const handleAction = async (task: Task) => {
    if (role === 'lab' && task.type === 'LAB_REQUEST') {
      setLabMode({ taskId: task.id, test_type: task.test_type || '', test_result: '' });
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      let url = `${API_BASE}/api/v1/tasks/${task.id}/perform?role=${role}`;
      let opts: RequestInit = { method: 'POST' };

      if (role === 'nurse') {
        url = `${API_BASE}/api/v1/tasks/${task.id}/triage`;
        opts = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sbar: sbarForm }),
        };
      }

      const res = await fetch(url, opts);
      if (res.ok) {
        const result = await res.json();
        setMessage(`✓ ${result.action || 'action'} completed`);
        if (role === 'nurse') setSbarForm({ situation: '', background: '', assessment: '', recommendation: '' });
        fetchTasks();
        fetchResources();
      } else {
        const err = await res.json();
        setMessage(`Error: ${err.detail}`);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    }
    setLoading(false);
  };

  const submitLabResult = async () => {
    if (!labMode) return;
    if (!labMode.test_type || !labMode.test_result) {
      setMessage('Please fill in test type and result');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/tasks/${labMode.taskId}/lab-complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test_type: labMode.test_type, test_result: labMode.test_result }),
      });
      if (res.ok) {
        setMessage('✓ Lab results sent back to doctor');
        setLabMode(null);
        fetchTasks();
      } else {
        const err = await res.json();
        setMessage(`Error: ${err.detail}`);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    }
    setLoading(false);
  };

  const isAlert = (t: Task) =>
    t.type === 'ESCALATED' || t.type === 'CRITICAL_ESCALATION' || t.type === 'DETERIORATION' || t.type === 'RESOURCE_SHORTAGE';

  const badge = (acuity: string): React.CSSProperties => ({
    display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700,
    color: '#fff', background: ACUITY_COLORS[acuity] || '#999', marginLeft: 8,
  });

  const vitalsStr = (t: Task) => {
    const parts: string[] = [];
    if (t.vitals_hr) parts.push(`HR ${t.vitals_hr}`);
    if (t.vitals_bp_systolic) parts.push(`BP ${t.vitals_bp_systolic}/${t.vitals_bp_diastolic}`);
    if (t.vitals_o2) parts.push(`O2 ${t.vitals_o2}%`);
    if (t.vitals_temp) parts.push(`Temp ${t.vitals_temp}°C`);
    return parts.length ? parts.join(' · ') : null;
  };

  const resourceBars = resources ? Object.entries(resources).map(([k, r]) => {
    const pct = r.total > 0 ? (r.used / r.total) * 100 : 0;
    return (
      <div key={k} style={{ marginBottom: 4, fontSize: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
          <span>{r.label}</span><span>{r.available}/{r.total}</span>
        </div>
        <div style={{ height: 6, background: '#eee', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${pct}%`, borderRadius: 3, transition: 'width 0.3s',
            background: pct > 80 ? '#d32f2f' : pct > 50 ? '#f57c00' : '#4caf50',
          }} />
        </div>
      </div>
    );
  }) : null;

  const inputS: React.CSSProperties = {
    display: 'block', width: '100%', padding: '6px 10px', borderRadius: 4, border: '1px solid #ddd',
    fontSize: 12, marginBottom: 6, boxSizing: 'border-box',
  };

  return (
    <div style={{ maxWidth: 900, margin: '40px auto', padding: '0 20px', fontFamily: '-apple-system, sans-serif' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <span style={{ fontSize: 32 }}>{icon}</span>
        <div style={{ flex: 1 }}>
          <h1 style={{ margin: 0, fontSize: 24 }}>{title}</h1>
          <p style={{ margin: '4px 0 0', opacity: 0.6, fontSize: 14 }}>
            {tasks.length} pending task{tasks.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 2 }}>
          {message && (
            <div style={{
              padding: '12px 16px', borderRadius: 6, marginBottom: 16,
              background: message.startsWith('✓') ? '#e8f5e9' : '#ffebee',
              color: message.startsWith('✓') ? '#2e7d32' : '#c62828',
            }}>{message}</div>
          )}

          {tasks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 48, opacity: 0.4 }}>
              <p style={{ fontSize: 18 }}>No pending tasks</p>
              <p style={{ fontSize: 14 }}>Waiting for new pheromones...</p>
            </div>
          ) : (
            tasks.map(task => (
              <div key={task.id} style={{
                border: `${isAlert(task) ? 2 : 1}px solid ${isAlert(task) ? '#d32f2f' : '#e0e0e0'}`,
                borderRadius: 8, padding: 16, marginBottom: 12, cursor: 'pointer',
              }}
                onClick={() => setExpandedTask(expandedTask === task.id ? null : task.id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600 }}>
                      {task.type === 'ESCALATED' && '🚨 '}
                      {task.type === 'CRITICAL_ESCALATION' && '🚨🚨 '}
                      {task.type === 'DETERIORATION' && '⚠️ '}
                      {task.type === 'RESOURCE_SHORTAGE' && '🔴 '}
                      {task.type}
                      {task.acuity && <span style={badge(task.acuity)}>{task.acuity}</span>}
                      {task.escalated && <span style={{ ...badge('IMMEDIATE'), background: '#d32f2f' }}>ESCALATED</span>}
                    </div>
                    <div style={{ fontSize: 13, opacity: 0.6, marginTop: 2 }}>
                      Patient: {task.patient_id}
                      {vitalsStr(task) && ` · ${vitalsStr(task)}`}
                    </div>
                    {task.sbar_situation && (
                      <div style={{ fontSize: 13, marginTop: 4, fontStyle: 'italic', opacity: 0.7 }}>
                        {task.sbar_situation}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleAction(task); }}
                    disabled={loading}
                    style={{
                      padding: '10px 20px', borderRadius: 6, border: 'none', cursor: 'pointer',
                      fontWeight: 600, fontSize: 13, whiteSpace: 'nowrap', marginLeft: 12,
                      background: isAlert(task) ? '#d32f2f' : '#1976d2', color: '#fff',
                      opacity: loading ? 0.6 : 1,
                    }}
                  >
                    {task.action.replace('_', ' ')}
                  </button>
                </div>

                {expandedTask === task.id && (
                  <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #eee', fontSize: 13 }}>
                    {task.medication_name && <div>💊 {task.medication_name} — {task.medication_dosage}</div>}
                    {task.test_type && <div>🔬 Test: {task.test_type}{task.test_result && ` → ${task.test_result}`}</div>}
                    {task.escalated_from && <div style={{ color: '#d32f2f' }}>⚠ Escalated from: {task.escalated_from}</div>}
                    {task.sbar_situation && <div><strong>S:</strong> {task.sbar_situation}</div>}
                    {task.sbar_background && <div><strong>B:</strong> {task.sbar_background}</div>}
                    {task.sbar_assessment && <div><strong>A:</strong> {task.sbar_assessment}</div>}
                    {task.sbar_recommendation && <div><strong>R:</strong> {task.sbar_recommendation}</div>}
                    {vitalsStr(task) && (
                      <div style={{ marginTop: 4, padding: '6px 10px', background: '#f5f5f5', borderRadius: 4 }}>
                        <strong>Vitals:</strong> {vitalsStr(task)}
                      </div>
                    )}
                  </div>
                )}

                {labMode && labMode.taskId === task.id && (
                  <div style={{ marginTop: 12, padding: 12, background: '#f5f5f5', borderRadius: 6 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Submit Lab Results</div>
                    <input style={inputS} placeholder="Test type"
                      value={labMode.test_type}
                      onChange={e => setLabMode({ ...labMode, test_type: e.target.value })} />
                    <input style={inputS} placeholder="Result (e.g., Normal, Positive)"
                      value={labMode.test_result}
                      onChange={e => setLabMode({ ...labMode, test_result: e.target.value })} />
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button onClick={submitLabResult} disabled={loading}
                        style={{ padding: '8px 16px', borderRadius: 4, border: 'none', cursor: 'pointer',
                          fontWeight: 600, fontSize: 12, background: '#388e3c', color: '#fff' }}>
                        Submit Result
                      </button>
                      <button onClick={() => setLabMode(null)}
                        style={{ padding: '8px 16px', borderRadius: 4, border: '1px solid #ccc',
                          cursor: 'pointer', fontSize: 12, background: '#fff' }}>
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div style={{ flex: 0, minWidth: 200 }}>
          {resources && (
            <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, padding: 16, marginBottom: 16 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>📊 Resources</div>
              {resourceBars}
            </div>
          )}

          {role === 'nurse' && (
            <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, padding: 16, marginBottom: 16 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>📋 SBAR Notes</div>
              <input style={inputS} placeholder="Situation" value={sbarForm.situation}
                onChange={e => setSbarForm({ ...sbarForm, situation: e.target.value })} />
              <input style={inputS} placeholder="Background" value={sbarForm.background}
                onChange={e => setSbarForm({ ...sbarForm, background: e.target.value })} />
              <input style={inputS} placeholder="Assessment" value={sbarForm.assessment}
                onChange={e => setSbarForm({ ...sbarForm, assessment: e.target.value })} />
              <input style={inputS} placeholder="Recommendation" value={sbarForm.recommendation}
                onChange={e => setSbarForm({ ...sbarForm, recommendation: e.target.value })} />
              <div style={{ fontSize: 11, opacity: 0.5, marginTop: 4 }}>
                Fill SBAR, then click "triage" on a patient
              </div>
            </div>
          )}

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <a href="/" style={{ color: '#1976d2', fontSize: 13 }}>← Dashboard</a>
            {role === 'doctor' && (
              <div style={{ marginTop: 8 }}>
                <a href="/journey" style={{ color: '#1976d2', fontSize: 13 }}>📋 Patient Journey</a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
