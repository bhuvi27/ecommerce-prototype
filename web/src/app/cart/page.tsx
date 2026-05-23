'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { cart as cartApi, Cart, formatPrice, dispatchCartUpdated } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useCart } from '@/context/CartContext';

export default function CartPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { refresh } = useCart();
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    return cartApi
      .get()
      .then((c) => {
        setCart(c);
        setError('');
      })
      .catch((e) => setError(e.message))
      .finally(() => {
        setLoading(false);
        dispatchCartUpdated();
      });
  };

  useEffect(() => {
    load();
    const onFocus = () => load();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [user?.id]);

  const remove = async (productId: string, skuId: string) => {
    const updated = await cartApi.remove(productId, skuId);
    setCart(updated);
    dispatchCartUpdated();
  };

  if (loading && !cart) return <p className="page-msg">Loading cart…</p>;
  if (error) return <div className="alert alert-error">{error}</div>;

  const items = cart?.items ?? [];

  return (
    <div className="cart-page">
      <h1>Your Cart</h1>
      {!user && (
        <div className="alert" style={{ background: '#fff8e6', color: '#7a5c00', marginBottom: '1rem' }}>
          <Link href="/login?next=/cart">Login</Link> to save your cart and checkout with saved addresses.
        </div>
      )}

      {items.length === 0 ? (
        <div className="card cart-empty">
          <p>Your cart is empty.</p>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            After you place an order, items are removed from the cart automatically.
          </p>
          <Link href="/" className="btn" style={{ marginTop: '1rem', display: 'inline-block' }}>
            Continue shopping
          </Link>
        </div>
      ) : (
        <>
          <p className="cart-count-line">{items.length} item{items.length > 1 ? 's' : ''} in cart</p>
          {items.map((item) => (
            <div
              key={`${item.product_id}-${item.sku_id}`}
              className="card cart-item-row"
            >
              {item.image_url && (
                <img src={item.image_url} alt="" className="cart-item-img" />
              )}
              <div className="cart-item-info">
                <strong>{item.product_name}</strong>
                <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>Qty: {item.quantity}</p>
              </div>
              <p className="price">{formatPrice(item.line_total)}</p>
              <button
                type="button"
                className="btn btn-outline cart-remove-btn"
                onClick={() => remove(item.product_id, item.sku_id)}
              >
                Remove
              </button>
            </div>
          ))}
          <div className="card cart-footer">
            <p className="cart-total-line">
              Total: <strong>{formatPrice(cart?.subtotal ?? 0)}</strong>
            </p>
            {user ? (
              <button type="button" className="btn" onClick={() => router.push('/checkout')}>
                Proceed to checkout
              </button>
            ) : (
              <Link href="/login?next=/checkout" className="btn" style={{ display: 'inline-block' }}>
                Login to checkout
              </Link>
            )}
          </div>
        </>
      )}
    </div>
  );
}
