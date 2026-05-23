'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Suspense } from 'react';

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get('next') || '/';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      router.push(next.startsWith('/') ? next : '/');
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

export default function LoginPage() {
  return (
    <Suspense fallback={<p>Loading...</p>}>
      <LoginForm />
    </Suspense>
  );
}
