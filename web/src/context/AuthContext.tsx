'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { auth, User } from '@/lib/api';

type AuthCtx = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }
    auth.me().then(setUser).catch(() => localStorage.removeItem('access_token')).finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const res = await auth.login(email, password);
    localStorage.setItem('access_token', res.access_token);
    setUser(res.user);
  };

  const register = async (email: string, password: string, name?: string) => {
    const res = await auth.register(email, password, name);
    localStorage.setItem('access_token', res.access_token);
    setUser(res.user);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
