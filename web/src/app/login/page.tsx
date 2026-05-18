'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      router.push('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '0 auto' }}>
      <h1 style={{ marginBottom: '1rem' }}>Login</h1>
      {error && <div className="alert alert-error">{error}</div>}
      <form onSubmit={submit} className="card" style={{ padding: '1.5rem' }}>
        <label>Email</label>
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <label>Password</label>
        <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit" className="btn" style={{ width: '100%' }}>Login</button>
      </form>
      <p style={{ marginTop: '1rem', textAlign: 'center' }}>
        No account? <Link href="/register">Sign up</Link>
      </p>
    </div>
  );
}
