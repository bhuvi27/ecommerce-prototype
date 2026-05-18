'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { orders, Order, formatPrice } from '@/lib/api';

function OrderViewContent() {
  const searchParams = useSearchParams();
  const id = searchParams.get('id') || '';
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState('');
  const [paying, setPaying] = useState(false);

  useEffect(() => {
    if (id) orders.get(id).then(setOrder).catch((e) => setError(e.message));
  }, [id]);

  const mockPay = async () => {
    if (!id) return;
    setPaying(true);
    try {
      const updated = await orders.mockPay(id);
      setOrder(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Payment failed');
    } finally {
      setPaying(false);
    }
  };

  if (!id) return <p>Missing order id.</p>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!order) return <p>Loading...</p>;

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <h1 style={{ marginBottom: '0.5rem' }}>Order #{order.id.slice(0, 8)}</h1>
      <p style={{ marginBottom: '1rem' }}>
        Status: <span className="badge">{order.status}</span>
      </p>
      {order.status === 'pending' && (
        <div style={{ marginBottom: '1rem' }}>
          <button type="button" className="btn" onClick={mockPay} disabled={paying}>
            {paying ? 'Confirming...' : 'Complete payment (dev mode)'}
          </button>
        </div>
      )}
      {order.status === 'confirmed' && (
        <div className="alert alert-success">Payment confirmed. Thank you!</div>
      )}
      <ul style={{ listStyle: 'none' }}>
        {order.items.map((item) => (
          <li key={`${item.product_id}-${item.sku_id}`} className="card" style={{ padding: '0.75rem', marginBottom: '0.5rem' }}>
            {item.product_name} x {item.quantity} — {formatPrice(item.unit_price * item.quantity)}
          </li>
        ))}
      </ul>
      <p style={{ fontWeight: 700, marginTop: '1rem' }}>Total: {formatPrice(order.subtotal)}</p>
    </div>
  );
}

export default function OrderViewPage() {
  return (
    <Suspense fallback={<p>Loading...</p>}>
      <OrderViewContent />
    </Suspense>
  );
}
