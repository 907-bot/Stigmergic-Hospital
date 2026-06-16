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
}

interface Medication {
  name: string;
  dosage: string;
}

interface DiagnoseForm {
  order_lab_tests: boolean;
  lab_test_type: string;
  request_icu: boolean;
  prescribe_medication: boolean;
  medications: Medication[];
}

const LAB_TEST_OPTIONS = [
  'Blood Culture',
  'CBC',
  'X-Ray',
  'EKG',
  'MRI',
  'CT Scan',
  'Urinalysis',
  'Liver Function',
];

const MEDICATION_OPTIONS = [
  'Aspirin',
  'Ibuprofen',
  'Amoxicillin',
  'Lisinopril',
  'Metformin',
  'Atorvastatin',
  'Omeprazole',
  'Paracetamol',
];

export default function DoctorDashboard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [message, setMessage] = useState('');
  const [form, setForm] = useState<DiagnoseForm>({
    order_lab_tests: false,
    lab_test_type: 'Blood Culture',
    request_icu: false,
    prescribe_medication: false,
    medications: [{ name: 'Aspirin', dosage: '100mg daily' }],
  });

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/tasks/?role=doctor`);
      if (res.ok) {
        setTasks(await res.json());
      }
    } catch (e) {
      console.error('Failed to fetch tasks', e);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  const handleDiagnose = async () => {
    if (!selectedTask) return;
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/tasks/${selectedTask.id}/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        const result = await res.json();
        const created = (result.created_pheromones || []).join(', ');
        setMessage(`✓ Diagnosis complete → Created: ${created}`);
        setSelectedTask(null);
        setForm({
          order_lab_tests: false,
          lab_test_type: 'Blood Culture',
          request_icu: false,
          prescribe_medication: false,
          medications: [{ name: 'Aspirin', dosage: '100mg daily' }],
        });
        fetchTasks();
      } else {
        const err = await res.json();
        setMessage(`Error: ${err.detail}`);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    }
  };

  const pageStyle: React.CSSProperties = {
    maxWidth: 900, margin: '40px auto', padding: '0 20px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  };

  const cardStyle: React.CSSProperties = {
    border: '1px solid #e0e0e0', borderRadius: 8, padding: 16, marginBottom: 12,
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  };

  const inputGroupStyle: React.CSSProperties = {
    display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12,
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 14, fontWeight: 500, minWidth: 160,
  };

  const selectStyle: React.CSSProperties = {
    padding: '6px 12px', borderRadius: 4, border: '1px solid #ccc', fontSize: 14, flex: 1,
  };

  const inputStyle: React.CSSProperties = {
    padding: '6px 12px', borderRadius: 4, border: '1px solid #ccc', fontSize: 14, flex: 1,
  };

  return (
    <div style={pageStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span style={{ fontSize: 32 }}>👨‍⚕️</span>
        <div>
          <h1 style={{ margin: 0, fontSize: 24 }}>Doctor's Office - Diagnosis</h1>
          <p style={{ margin: '4px 0 0', opacity: 0.6, fontSize: 14 }}>
            {tasks.length} triaged patient{tasks.length !== 1 ? 's' : ''} waiting
          </p>
        </div>
      </div>

      {message && (
        <div style={{
          padding: '12px 16px', borderRadius: 6, marginBottom: 16,
          background: message.startsWith('✓') ? '#e8f5e9' : '#ffebee',
          color: message.startsWith('✓') ? '#2e7d32' : '#c62828',
        }}>
          {message}
        </div>
      )}

      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: 16, marginBottom: 12, opacity: 0.7 }}>TRIAGED Patients</h2>
          {tasks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 32, opacity: 0.4 }}>
              <p>No pending triage cases</p>
              <p style={{ fontSize: 13 }}>Waiting for nurses to triage...</p>
            </div>
          ) : (
            tasks.map(task => (
              <div
                key={task.id}
                onClick={() => { setSelectedTask(task); setMessage(''); }}
                style={{
                  ...cardStyle,
                  cursor: 'pointer',
                  borderColor: selectedTask?.id === task.id ? '#1976d2' : '#e0e0e0',
                  background: selectedTask?.id === task.id ? '#e3f2fd' : '#fff',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600 }}>{task.type} — Patient {task.patient_id}</div>
                  <div style={{ fontSize: 13, opacity: 0.6, marginTop: 4 }}>
                    Strength: {task.strength.toFixed(2)}
                  </div>
                </div>
                <span style={{ fontSize: 12, color: '#1976d2' }}>
                  {selectedTask?.id === task.id ? 'Selected' : 'Click to diagnose'}
                </span>
              </div>
            ))
          )}
        </div>

        {selectedTask && (
          <div style={{
            flex: 1, border: '1px solid #e0e0e0', borderRadius: 8, padding: 20,
            alignSelf: 'flex-start',
          }}>
            <h2 style={{ fontSize: 16, margin: '0 0 16px' }}>
              Diagnosis Plan — Patient {selectedTask.patient_id}
            </h2>

            <div style={inputGroupStyle}>
              <input
                type="checkbox"
                checked={form.order_lab_tests}
                onChange={e => setForm({ ...form, order_lab_tests: e.target.checked })}
                id="labCheck"
              />
              <label htmlFor="labCheck" style={labelStyle}>Order Lab Tests</label>
            </div>
            {form.order_lab_tests && (
              <div style={inputGroupStyle}>
                <span style={labelStyle}>Test Type</span>
                <select
                  value={form.lab_test_type}
                  onChange={e => setForm({ ...form, lab_test_type: e.target.value })}
                  style={selectStyle}
                >
                  {LAB_TEST_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            )}

            <div style={inputGroupStyle}>
              <input
                type="checkbox"
                checked={form.request_icu}
                onChange={e => setForm({ ...form, request_icu: e.target.checked })}
                id="icuCheck"
              />
              <label htmlFor="icuCheck" style={labelStyle}>Request ICU Bed</label>
            </div>

            <div style={inputGroupStyle}>
              <input
                type="checkbox"
                checked={form.prescribe_medication}
                onChange={e => setForm({ ...form, prescribe_medication: e.target.checked })}
                id="medCheck"
              />
              <label htmlFor="medCheck" style={labelStyle}>Prescribe Medication</label>
            </div>
            {form.prescribe_medication && (
              <div style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={labelStyle}>Medications</span>
                  <button
                    onClick={() => setForm({
                      ...form,
                      medications: [...form.medications, { name: 'Aspirin', dosage: '' }],
                    })}
                    style={{
                      background: '#1976d2', color: '#fff', border: 'none',
                      borderRadius: 4, width: 28, height: 28, cursor: 'pointer',
                      fontSize: 18, fontWeight: 700, lineHeight: '28px', padding: 0,
                    }}
                    title="Add medication"
                  >+</button>
                </div>
                {form.medications.map((med, i) => (
                  <div key={i} style={{ ...inputGroupStyle, marginLeft: 0 }}>
                    <span style={{ fontSize: 11, opacity: 0.5, minWidth: 18 }}>{i + 1}.</span>
                    <select
                      value={med.name}
                      onChange={e => {
                        const updated = [...form.medications];
                        updated[i] = { ...updated[i], name: e.target.value };
                        setForm({ ...form, medications: updated });
                      }}
                      style={selectStyle}
                    >
                      {MEDICATION_OPTIONS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                    <input
                      value={med.dosage}
                      onChange={e => {
                        const updated = [...form.medications];
                        updated[i] = { ...updated[i], dosage: e.target.value };
                        setForm({ ...form, medications: updated });
                      }}
                      style={{ ...inputStyle, maxWidth: 130 }}
                      placeholder="dosage"
                    />
                    <button
                      onClick={() => {
                        const updated = form.medications.filter((_, idx) => idx !== i);
                        setForm({ ...form, medications: updated });
                      }}
                      style={{
                        background: 'transparent', color: '#c62828', border: 'none',
                        cursor: 'pointer', fontSize: 16, fontWeight: 700, padding: '4px 6px',
                      }}
                      title="Remove medication"
                    >×</button>
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={handleDiagnose}
              style={{
                width: '100%', padding: '12px 24px', borderRadius: 6, border: 'none',
                cursor: 'pointer', fontWeight: 600, fontSize: 15, marginTop: 16,
                background: '#1976d2', color: '#fff',
              }}
            >
              Confirm Diagnosis
            </button>
          </div>
        )}
      </div>

      <div style={{ textAlign: 'center', marginTop: 32 }}>
        <a href="/" style={{ color: '#1976d2', fontSize: 14 }}>← Back to Dashboard</a>
      </div>
    </div>
  );
}
