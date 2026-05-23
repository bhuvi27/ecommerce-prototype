'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { auth } from '@/lib/api';

export default function AccountPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace('/login?next=/account');
      return;
    }
    setName(user.name || '');
  }, [user, authLoading, router]);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await auth.updateProfile(name);
      setMessage('Profile updated.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  if (authLoading || !user) return <p>Loading...</p>;

  return (
    <div style={{ maxWidth: 520, margin: '0 auto' }}>
      <h1 style={{ marginBottom: '1rem' }}>My Account</h1>
      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}
      <form onSubmit={save} className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <label>Email</label>
        <input value={user.email} disabled />
        <label>Display name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} />
        <button type="submit" className="btn" disabled={saving}>
          {saving ? 'Saving...' : 'Save profile'}
        </button>
      </form>
      <div className="card" style={{ padding: '1.25rem' }}>
        <h2 style={{ fontSize: '1.1rem', marginBottom: '0.75rem' }}>Quick links</h2>
        <ul className="account-links">
          <li><Link href="/account/addresses">Saved addresses</Link></li>
          <li><Link href="/orders">My orders</Link></li>
          <li><Link href="/cart">Cart</Link></li>
        </ul>
      </div>
    </div>
  );
}
