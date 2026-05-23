'use client';

import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { cart as cartApi, Cart } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

type CartCtx = {
  cart: Cart | null;
  itemCount: number;
  loading: boolean;
  refresh: () => Promise<void>;
};

const CartContext = createContext<CartCtx | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const c = await cartApi.get();
      setCart(c);
    } catch {
      setCart({ cart_id: '', items: [], subtotal: 0, item_count: 0 });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    refresh();
  }, [authLoading, user?.id, refresh]);

  useEffect(() => {
    const onUpdate = () => refresh();
    window.addEventListener('cart-updated', onUpdate);
    return () => window.removeEventListener('cart-updated', onUpdate);
  }, [refresh]);

  const itemCount = cart?.item_count ?? 0;

  return (
    <CartContext.Provider value={{ cart, itemCount, loading, refresh }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within CartProvider');
  return ctx;
}
