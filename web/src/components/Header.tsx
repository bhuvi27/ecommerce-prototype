'use client';

import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="site-header">
      <div className="container header-inner">
        <Link href="/" className="brand">
          Shree Hari Beauty
        </Link>
        <nav className="header-nav">
          <Link href="/">Shop</Link>
          <Link href="/cart">Cart</Link>
          {user ? (
            <>
              <Link href="/orders">Orders</Link>
              <Link href="/account">Account</Link>
              <Link href="/account/addresses">Addresses</Link>
              <span className="header-user">{user.name || user.email}</span>
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
