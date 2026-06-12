import { useState, useCallback } from 'react';
import type { User } from '../types';
import { mockUser } from '../data/mockData';

export function useAuth() {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('demo_auth');
    return saved ? JSON.parse(saved) : null;
  });
  const [isLoading, setIsLoading] = useState(false);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 800));
    const u = { ...mockUser, email };
    setUser(u);
    localStorage.setItem('demo_auth', JSON.stringify(u));
    setIsLoading(false);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('demo_auth');
  }, []);

  return { user, isAuthenticated: !!user, isLoading, login, logout };
}
