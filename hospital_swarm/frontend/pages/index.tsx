import Head from 'next/head';
import { useEffect, useState } from 'react';

const roles = [
  { path: '/nurse', label: 'Nurse Station', icon: '🩺', desc: 'Triage with SBAR notes, see vitals & deterioration' },
  { path: '/doctor', label: "Doctor's Office", icon: '👨‍⚕️', desc: 'Diagnose with SBAR, order labs/ICU/prescriptions' },
  { path: '/icu', label: 'ICU Unit', icon: '🏥', desc: 'Prepare beds, see resource constraints' },
  { path: '/lab', label: 'Lab', icon: '🔬', desc: 'Run tests, submit results back to doctor' },
  { path: '/pharmacy', label: 'Pharmacy', icon: '💊', desc: 'Dispense medications, see stock levels' },
  { path: '/ambulance', label: 'Ambulance', icon: '🚑', desc: 'Dispatch, see availability' },
];

export default function Home() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    try {
      const u = localStorage.getItem('user');
      if (u) setUser(JSON.parse(u));
    } catch {}
  }, []);

  return (
    <div style={{
      maxWidth: 700, margin: '60px auto', padding: '0 20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    }}>
      <Head>
        <title>Stigmergic Hospital Swarm OS — SaaS</title>
        <meta name="description" content="Multi-tenant Hospital Coordination Platform" />
      </Head>

      {user && (
        <div style={{
          display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 12,
          marginBottom: 16, fontSize: 13,
        }}>
          <span>👤 {user.name}</span>
          <span style={{ padding: '2px 6px', borderRadius: 4, background: '#e3f2fd', color: '#1976d2', fontSize: 11 }}>
            {user.role}
          </span>
          <a href="/admin" style={{ color: '#1976d2' }}>Admin</a>
          <button onClick={() => { localStorage.clear(); location.reload(); }}
            style={{ border: 'none', background: 'none', color: '#c62828', cursor: 'pointer', fontSize: 13 }}>
            Logout
          </button>
        </div>
      )}

      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <h1 style={{ margin: 0, fontSize: 28 }}>🏥 Stigmergic Hospital Swarm OS</h1>
        <p style={{ opacity: 0.6, marginTop: 8 }}>
          Multi-tenant SaaS for real-time hospital coordination
        </p>
        {!user && (
          <a href="/login"
            style={{
              display: 'inline-block', marginTop: 12, padding: '10px 24px',
              borderRadius: 6, background: '#667eea', color: '#fff',
              textDecoration: 'none', fontWeight: 600, fontSize: 14,
            }}>
            Sign In
          </a>
        )}
      </div>

      {/* SaaS Feature Flags */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 32, fontSize: 12,
      }}>
        {[
          { label: 'Auth Provider', value: 'JWT + Okta / Azure AD' },
          { label: 'HIPAA', value: 'Audit Trail (6yr retention)' },
          { label: 'FHIR R4', value: 'Patient / Observation / MedReq' },
          { label: 'Multi-tenant', value: 'Data isolation' },
          { label: 'RBAC', value: '8 role tiers' },
          { label: 'K8s Ready', value: 'HPA, probes, anti-affinity' },
        ].map(f => (
          <div key={f.label} style={{ border: '1px solid #e0e0e0', borderRadius: 6, padding: '8px 12px', textAlign: 'center' }}>
            <div style={{ fontWeight: 600, color: '#1976d2' }}>{f.label}</div>
            <div style={{ opacity: 0.6, marginTop: 2 }}>{f.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <a href="/patient" style={{
          display: 'flex', alignItems: 'center', gap: 16,
          padding: '16px 20px', borderRadius: 8,
          border: '2px solid #388e3c', textDecoration: 'none', color: '#388e3c',
          background: '#f1f8e9',
        }}>
          <span style={{ fontSize: 28 }}>👤</span>
          <div>
            <div style={{ fontWeight: 600, fontSize: 16 }}>Patient Portal</div>
            <div style={{ fontSize: 13, opacity: 0.5 }}>Track your care, see next steps, download your medical report</div>
          </div>
          <span style={{ marginLeft: 'auto' }}>→</span>
        </a>
        <a href="/journey" style={{
          display: 'flex', alignItems: 'center', gap: 16,
          padding: '16px 20px', borderRadius: 8,
          border: '2px dashed #1976d2', textDecoration: 'none', color: '#1976d2',
        }}>
          <span style={{ fontSize: 28 }}>📋</span>
          <div>
            <div style={{ fontWeight: 600, fontSize: 16 }}>Patient Journey Timeline</div>
            <div style={{ fontSize: 13, opacity: 0.5 }}>Trace every pheromone event for any patient</div>
          </div>
          <span style={{ marginLeft: 'auto' }}>→</span>
        </a>
        {roles.map(r => (
          <a key={r.path} href={r.path} style={{
            display: 'flex', alignItems: 'center', gap: 16,
            padding: '16px 20px', borderRadius: 8,
            border: '1px solid #e0e0e0', textDecoration: 'none', color: 'inherit',
            transition: 'background 0.2s',
          }}
            onMouseEnter={e => (e.currentTarget.style.background = '#f5f5f5')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
            <span style={{ fontSize: 28 }}>{r.icon}</span>
            <div>
              <div style={{ fontWeight: 600, fontSize: 16 }}>{r.label}</div>
              <div style={{ fontSize: 13, opacity: 0.5 }}>{r.desc}</div>
            </div>
            <span style={{ marginLeft: 'auto', opacity: 0.3 }}>→</span>
          </a>
        ))}
      </div>

      <div style={{ marginTop: 40, textAlign: 'center', fontSize: 12, opacity: 0.4 }}>
        <p>Stigmergic Hospital Swarm OS v2.0.0 — SaaS Edition</p>
        <p>JWT Auth · HIPAA Audit · FHIR R4 · Multi-tenant · Kubernetes</p>
      </div>
    </div>
  );
}
