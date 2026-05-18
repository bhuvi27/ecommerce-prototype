'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { orders, Order, formatPrice } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

export default function OrdersPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [list, setList] = useState<Order[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    if (user) orders.list().then(setList).catch((e) => setError(e.message));
  }, [user]);

  if (loading) return <p>Loading...</p>;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div>
      <h1 style={{ marginBottom: '1rem' }}>My Orders</h1>
      {list.length === 0 ? (
        <p>No orders yet. <Link href="/">Start shopping</Link></p>
      ) : (
        list.map((o) => (
          <Link key={o.id} href={`/orders/view?id=${o.id}`} className="card" style={{ display: 'block', padding: '1rem', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Order #{o.id.slice(0, 8)}</span>
              <span className="badge">{o.status}</span>
            </div>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
              {new Date(o.created_at).toLocaleString()} — {formatPrice(o.subtotal)}
            </p>
          </Link>
        ))
      )}
    </div>
  );
}
