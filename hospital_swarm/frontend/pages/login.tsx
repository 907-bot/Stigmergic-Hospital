import { useState, FormEvent } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

const API_BASE = `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:9001`;

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        window.location.href = '/';
      } else {
        const err = await res.json();
        setError(err.detail || 'Login failed');
      }
    } catch (e: any) {
      setError(e.message || 'Connection failed');
    }
    setLoading(false);
  };

  const containerStyle: React.CSSProperties = {
    display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  };

  const cardStyle: React.CSSProperties = {
    background: '#fff', borderRadius: 12, padding: 40, width: '100%', maxWidth: 400,
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '12px 16px', borderRadius: 8, border: '1px solid #ddd',
    fontSize: 14, marginBottom: 16, boxSizing: 'border-box',
  };

  return (
    <>
      <Head><title>Login — Hospital Swarm OS</title></Head>
      <div style={containerStyle}>
        <div style={cardStyle}>
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{ fontSize: 48, marginBottom: 8 }}>🏥</div>
            <h1 style={{ fontSize: 22, margin: 0, color: '#333' }}>Hospital Swarm OS</h1>
            <p style={{ fontSize: 14, color: '#999', marginTop: 4 }}>Sign in to continue</p>
          </div>

          {error && (
            <div style={{
              padding: '10px 14px', background: '#ffebee', color: '#c62828',
              borderRadius: 6, fontSize: 13, marginBottom: 16,
            }}>{error}</div>
          )}

          <form onSubmit={handleSubmit}>
            <input
              style={inputStyle}
              type="email" placeholder="Email address"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
            <input
              style={inputStyle}
              type="password" placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
            <button
              type="submit" disabled={loading}
              style={{
                width: '100%', padding: '12px', borderRadius: 8, border: 'none',
                background: loading ? '#999' : '#667eea', color: '#fff',
                fontSize: 15, fontWeight: 600, cursor: loading ? 'default' : 'pointer',
              }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: 24, fontSize: 13, color: '#999' }}>
            <p>Default: admin@hospital.com / admin123</p>
          </div>
        </div>
      </div>
    </>
  );
}
