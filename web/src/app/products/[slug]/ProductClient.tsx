'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { catalog, cart, Product, formatPrice, dispatchCartUpdated } from '@/lib/api';

export default function ProductClient({ slug }: { slug: string }) {
  const router = useRouter();
  const [product, setProduct] = useState<Product | null>(null);
  const [qty, setQty] = useState(1);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    catalog.product(slug).then(setProduct).catch((e) => setError(e.message));
  }, [slug]);

  const addToCart = async () => {
    if (!product) return;
    try {
      await cart.add(product.id, product.skus[0].id, qty);
      dispatchCartUpdated();
      setMessage('Added to cart!');
      setTimeout(() => router.push('/cart'), 800);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed');
    }
  };

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!product) return <p>Loading...</p>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', maxWidth: 900, margin: '0 auto' }}>
      {product.image_url && (
        <img src={product.image_url} alt={product.name} style={{ width: '100%', borderRadius: 12, objectFit: 'cover' }} />
      )}
      <div>
        <span className="badge">{product.category_slug}</span>
        <h1 style={{ margin: '0.5rem 0' }}>{product.name}</h1>
        <p style={{ color: 'var(--muted)', marginBottom: '1rem' }}>{product.description}</p>
        <p className="price" style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>
          {formatPrice(product.skus[0].price)}
        </p>
        <label>Quantity</label>
        <input type="number" min={1} max={10} value={qty} onChange={(e) => setQty(Number(e.target.value))} />
        {message && <div className="alert alert-success">{message}</div>}
        <button type="button" className="btn" onClick={addToCart} style={{ width: '100%' }}>
          Add to Cart
        </button>
      </div>
    </div>
  );
}
