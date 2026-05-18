'use client';

import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header style={{ borderBottom: '1px solid var(--border)', background: 'var(--card)', marginBottom: '2rem' }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem 1.25rem' }}>
        <Link href="/" style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--accent)' }}>
          Shree Hari Beauty
        </Link>
        <nav style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
          <Link href="/">Shop</Link>
          <Link href="/cart">Cart</Link>
          {user ? (
            <>
              <Link href="/orders">Orders</Link>
              <span style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>{user.email}</span>
              <button className="btn btn-outline" onClick={logout} style={{ padding: '0.4rem 0.8rem' }}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/login">Login</Link>
              <Link href="/register" className="btn" style={{ padding: '0.4rem 0.9rem' }}>
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
