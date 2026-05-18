'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { cart as cartApi, Cart, formatPrice } from '@/lib/api';

export default function CartPage() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState('');

  const load = () => cartApi.get().then(setCart).catch((e) => setError(e.message));

  useEffect(() => { load(); }, []);

  const remove = async (productId: string, skuId: string) => {
    const updated = await cartApi.remove(productId, skuId);
    setCart(updated);
  };

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!cart) return <p>Loading cart...</p>;

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Your Cart</h1>
      {cart.items.length === 0 ? (
        <p>
          Cart is empty. <Link href="/">Continue shopping</Link>
        </p>
      ) : (
        <>
          {cart.items.map((item) => (
            <div key={`${item.product_id}-${item.sku_id}`} className="card" style={{ padding: '1rem', marginBottom: '0.75rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
              {item.image_url && <img src={item.image_url} alt="" style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 8 }} />}
              <div style={{ flex: 1 }}>
                <strong>{item.product_name}</strong>
                <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>Qty: {item.quantity}</p>
              </div>
              <p className="price">{formatPrice(item.line_total)}</p>
              <button className="btn btn-outline" style={{ padding: '0.35rem 0.7rem' }} onClick={() => remove(item.product_id, item.sku_id)}>
                Remove
              </button>
            </div>
          ))}
          <div style={{ textAlign: 'right', marginTop: '1.5rem' }}>
            <p style={{ fontSize: '1.25rem', fontWeight: 700 }}>Total: {formatPrice(cart.subtotal)}</p>
            <Link href="/checkout" className="btn" style={{ marginTop: '1rem', display: 'inline-block' }}>
              Proceed to Checkout
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
