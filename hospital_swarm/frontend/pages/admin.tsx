import { useEffect, useState } from 'react';
import Head from 'next/head';

const API_BASE = `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:9001`;

interface Tenant {
  tenant_id: string;
  name: string;
  domain: string;
  plan: string;
  is_active: boolean;
  created_at: string | null;
  user_count: number;
}

interface SimStatus {
  is_running: boolean;
  stats: {
    patients_generated: number;
    pheromones_created: number;
    deteriorations: number;
    escalations: number;
  };
}

export default function AdminPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [simStatus, setSimStatus] = useState<SimStatus | null>(null);
  const [showCreateTenant, setShowCreateTenant] = useState(false);
  const [newTenant, setNewTenant] = useState({ tenant_id: '', name: '', plan: 'enterprise' });
  const [message, setMessage] = useState('');

  const headers = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  };

  useEffect(() => {
    fetch(`${API_BASE}/auth/tenants`, { headers: headers() })
      .then(r => r.ok ? r.json() : [])
      .then(setTenants)
      .catch(() => {});

    fetch(`${API_BASE}/api/v1/simulation/status`, { headers: headers() })
      .then(r => r.ok ? r.json() : null)
      .then(setSimStatus)
      .catch(() => {});
  }, []);

  const createTenant = async () => {
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/auth/tenants`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify(newTenant),
      });
      if (res.ok) {
        setMessage('✓ Tenant created');
        setShowCreateTenant(false);
        const updated = await fetch(`${API_BASE}/auth/tenants`, { headers: headers() });
        if (updated.ok) setTenants(await updated.json());
      } else {
        const err = await res.json();
        setMessage(`Error: ${err.detail}`);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    }
  };

  return (
    <>
      <Head><title>Admin — Hospital Swarm OS</title></Head>
      <div style={{ maxWidth: 1000, margin: '40px auto', padding: '0 20px', fontFamily: '-apple-system, sans-serif' }}>
        <h1 style={{ fontSize: 24, marginBottom: 24 }}>🏥 Admin Dashboard</h1>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 32 }}>
          <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, padding: 20 }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#1976d2' }}>{tenants.length}</div>
            <div style={{ fontSize: 14, color: '#666' }}>Active Tenants</div>
          </div>
          <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, padding: 20 }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#388e3c' }}>
              {simStatus?.stats.patients_generated || 0}
            </div>
            <div style={{ fontSize: 14, color: '#666' }}>Patients Simulated</div>
          </div>
          <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, padding: 20 }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: simStatus?.is_running ? '#388e3c' : '#999' }}>
              {simStatus?.is_running ? '● Running' : '○ Stopped'}
            </div>
            <div style={{ fontSize: 14, color: '#666' }}>Simulation Status</div>
          </div>
        </div>

        {message && (
          <div style={{
            padding: '12px 16px', borderRadius: 6, marginBottom: 16,
            background: message.startsWith('✓') ? '#e8f5e9' : '#ffebee',
            color: message.startsWith('✓') ? '#2e7d32' : '#c62828',
          }}>{message}</div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, margin: 0 }}>Tenants</h2>
          <button onClick={() => setShowCreateTenant(!showCreateTenant)}
            style={{
              padding: '8px 16px', borderRadius: 6, border: 'none',
              background: '#1976d2', color: '#fff', fontWeight: 600, cursor: 'pointer',
            }}>
            {showCreateTenant ? 'Cancel' : '+ New Tenant'}
          </button>
        </div>

        {showCreateTenant && (
          <div style={{ border: '1px solid #1976d2', borderRadius: 8, padding: 20, marginBottom: 20 }}>
            <h3 style={{ fontSize: 15, margin: '0 0 12px' }}>Create Tenant</h3>
            <input placeholder="Tenant ID (e.g., hospital-1)"
              value={newTenant.tenant_id}
              onChange={e => setNewTenant({ ...newTenant, tenant_id: e.target.value })}
              style={{ display: 'block', width: '100%', padding: '8px 12px', borderRadius: 4, border: '1px solid #ddd', marginBottom: 8, fontSize: 13 }}
            />
            <input placeholder="Organization Name"
              value={newTenant.name}
              onChange={e => setNewTenant({ ...newTenant, name: e.target.value })}
              style={{ display: 'block', width: '100%', padding: '8px 12px', borderRadius: 4, border: '1px solid #ddd', marginBottom: 8, fontSize: 13 }}
            />
            <select value={newTenant.plan}
              onChange={e => setNewTenant({ ...newTenant, plan: e.target.value })}
              style={{ display: 'block', width: '100%', padding: '8px 12px', borderRadius: 4, border: '1px solid #ddd', marginBottom: 12, fontSize: 13 }}
            >
              <option value="community">Community</option>
              <option value="enterprise">Enterprise ($25k/yr)</option>
              <option value="white-label">White-Label ($100k/yr)</option>
            </select>
            <button onClick={createTenant}
              style={{ padding: '8px 20px', borderRadius: 4, border: 'none', background: '#1976d2', color: '#fff', cursor: 'pointer' }}>
              Create
            </button>
          </div>
        )}

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#f5f5f5' }}>
              <th style={{ padding: '10px 12px', textAlign: 'left' }}>Tenant</th>
              <th style={{ padding: '10px 12px', textAlign: 'left' }}>Plan</th>
              <th style={{ padding: '10px 12px', textAlign: 'left' }}>Users</th>
              <th style={{ padding: '10px 12px', textAlign: 'left' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map(t => (
              <tr key={t.tenant_id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '10px 12px' }}><strong>{t.name}</strong><br /><span style={{ fontSize: 12, color: '#999' }}>{t.tenant_id}</span></td>
                <td style={{ padding: '10px 12px' }}><span style={{
                  padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                  background: t.plan === 'enterprise' ? '#e3f2fd' : t.plan === 'white-label' ? '#fce4ec' : '#f5f5f5',
                  color: t.plan === 'enterprise' ? '#1976d2' : t.plan === 'white-label' ? '#c62828' : '#666',
                }}>{t.plan}</span></td>
                <td style={{ padding: '10px 12px' }}>{t.user_count}</td>
                <td style={{ padding: '10px 12px' }}>{t.is_active ? '🟢 Active' : '🔴 Inactive'}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={{ marginTop: 32, textAlign: 'center' }}>
          <a href="/" style={{ color: '#1976d2', fontSize: 14 }}>← Back to Dashboard</a>
        </div>
      </div>
    </>
  );
}
