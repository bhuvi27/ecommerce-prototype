'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { catalog, Category, Product, formatPrice } from '@/lib/api';

export default function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [activeCategory, setActiveCategory] = useState<string | undefined>();
  const [error, setError] = useState('');

  useEffect(() => {
    catalog.categories().then(setCategories).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    catalog.products(activeCategory).then((r) => setProducts(r.items)).catch((e) => setError(e.message));
  }, [activeCategory]);

  return (
    <>
      <section className="hero-banner">
        <h1>Natural Beauty, Delivered</h1>
        <p style={{ color: 'var(--muted)' }}>Handpicked oils, facewash and creams — shop like your favourite marketplace</p>
      </section>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="category-pills">
        <button
          type="button"
          className={`btn ${!activeCategory ? '' : 'btn-outline'}`}
          onClick={() => setActiveCategory(undefined)}
          style={{ padding: '0.4rem 0.9rem' }}
        >
          All
        </button>
        {categories.map((c) => (
          <button
            key={c.slug}
            type="button"
            className={`btn ${activeCategory === c.slug ? '' : 'btn-outline'}`}
            onClick={() => setActiveCategory(c.slug)}
            style={{ padding: '0.4rem 0.9rem' }}
          >
            {c.name}
          </button>
        ))}
      </div>

      <div className="grid-products">
        {products.map((p) => (
          <Link key={p.id} href={`/products/${p.slug}`} className="card product-card">
            {p.image_url && <img src={p.image_url} alt={p.name} />}
            <div className="body">
              <span className="badge">{p.category_slug}</span>
              <h3>{p.name}</h3>
              <p className="price">{formatPrice(p.skus[0]?.price ?? 0)}</p>
            </div>
          </Link>
        ))}
      </div>
      {products.length === 0 && !error && <p style={{ color: 'var(--muted)' }}>Loading products...</p>}
    </>
  );
}
