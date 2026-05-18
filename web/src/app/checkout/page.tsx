'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { v4 as uuidv4 } from 'uuid';
import { cart as cartApi, orders, Cart, formatPrice } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void };
  }
}

export default function CheckoutPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    shipping_name: user?.name || '',
    shipping_phone: '',
    shipping_line1: '',
    shipping_line2: '',
    shipping_city: '',
    shipping_state: '',
    shipping_pincode: '',
  });

  useEffect(() => {
    cartApi.get().then(setCart).catch((e) => setError(e.message));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const pay = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cart?.items.length) return;
    setLoading(true);
    setError('');
    try {
      const result = await orders.checkout(form, uuidv4());
      const key = result.razorpay_key_id;
      if (!key || key === 'mock') {
        await orders.mockPay(result.order.id);
        router.push(`/orders/view?id=${result.order.id}`);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => {
        const rzp = new window.Razorpay!({
          key,
          amount: result.amount,
          currency: result.currency,
          name: 'Shree Hari Beauty',
          order_id: result.razorpay_order_id,
          handler: () => router.push(`/orders/view?id=${result.order.id}`),
        });
        rzp.open();
      };
      document.body.appendChild(script);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Checkout failed');
    } finally {
      setLoading(false);
    }
  };

  if (!cart) return <p>Loading...</p>;

  return (
    <div style={{ maxWidth: 560, margin: '0 auto' }}>
      <h1 style={{ marginBottom: '1rem' }}>Checkout</h1>
      <p style={{ marginBottom: '1.5rem' }}>Order total: <strong>{formatPrice(cart.subtotal)}</strong></p>
      {error && <div className="alert alert-error">{error}</div>}
      <form onSubmit={pay} className="card" style={{ padding: '1.5rem' }}>
        <label>Full name</label>
        <input name="shipping_name" required value={form.shipping_name} onChange={handleChange} />
        <label>Phone</label>
        <input name="shipping_phone" required value={form.shipping_phone} onChange={handleChange} />
        <label>Address line 1</label>
        <input name="shipping_line1" required value={form.shipping_line1} onChange={handleChange} />
        <label>Address line 2</label>
        <input name="shipping_line2" value={form.shipping_line2} onChange={handleChange} />
        <label>City</label>
        <input name="shipping_city" required value={form.shipping_city} onChange={handleChange} />
        <label>State</label>
        <input name="shipping_state" required value={form.shipping_state} onChange={handleChange} />
        <label>Pincode</label>
        <input name="shipping_pincode" required value={form.shipping_pincode} onChange={handleChange} />
        <button type="submit" className="btn" disabled={loading || !cart.items.length} style={{ width: '100%', marginTop: '0.5rem' }}>
          {loading ? 'Processing...' : 'Pay Now'}
        </button>
        <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.75rem' }}>
          Without Razorpay keys, payment runs in dev mock mode automatically.
        </p>
      </form>
    </div>
  );
}
