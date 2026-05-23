'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { auth, Address } from '@/lib/api';

const empty = {
  label: 'Home',
  line1: '',
  line2: '',
  city: '',
  state: '',
  pincode: '',
  phone: '',
};

export default function AddressesPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [form, setForm] = useState(empty);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const load = () => auth.listAddresses().then(setAddresses).catch((e) => setError(e.message));

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace('/login?next=/account/addresses');
      return;
    }
    load();
  }, [user, authLoading, router]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await auth.createAddress({
        ...form,
        is_default: addresses.length === 0,
      });
      setForm(empty);
      setShowForm(false);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save address');
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || !user) return <p>Loading...</p>;

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <p style={{ marginBottom: '0.5rem' }}>
        <Link href="/account">← Account</Link>
      </p>
      <h1 style={{ marginBottom: '1rem' }}>Saved Addresses</h1>
      {error && <div className="alert alert-error">{error}</div>}

      {addresses.map((addr) => (
        <div key={addr.id} className="card address-card-static" style={{ padding: '1rem', marginBottom: '0.75rem' }}>
          <strong>{addr.label || 'Address'}</strong>
          {addr.is_default && <span className="badge" style={{ marginLeft: 8 }}>Default</span>}
          <p className="address-lines" style={{ marginTop: '0.5rem' }}>
            {addr.line1}{addr.line2 ? `, ${addr.line2}` : ''}<br />
            {addr.city}, {addr.state} — {addr.pincode}<br />
            Phone: {addr.phone}
          </p>
        </div>
      ))}

      {addresses.length === 0 && !showForm && (
        <p style={{ color: 'var(--muted)', marginBottom: '1rem' }}>No saved addresses yet.</p>
      )}

      {!showForm ? (
        <button type="button" className="btn btn-save-address" onClick={() => setShowForm(true)}>
          + Add & save address
        </button>
      ) : (
        <form onSubmit={submit} className="card" style={{ padding: '1.5rem', marginTop: '1rem' }}>
          <label>Label (Home, Work…)</label>
          <input value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} />
          <label>Phone</label>
          <input required value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <label>Address line 1</label>
          <input required value={form.line1} onChange={(e) => setForm({ ...form, line1: e.target.value })} />
          <label>Address line 2</label>
          <input value={form.line2} onChange={(e) => setForm({ ...form, line2: e.target.value })} />
          <label>City</label>
          <input required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          <label>State</label>
          <input required value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} />
          <label>Pincode</label>
          <input required value={form.pincode} onChange={(e) => setForm({ ...form, pincode: e.target.value })} />
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button type="submit" className="btn" disabled={loading}>
              {loading ? 'Saving...' : 'Save address'}
            </button>
            <button type="button" className="btn btn-outline" onClick={() => setShowForm(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
