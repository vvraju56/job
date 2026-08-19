"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  clearTokens,
  getStoredTokens,
  getStoredUser,
  storeTokens,
  storeUser,
} from "@/lib/auth-store";
import { authService } from "@/lib/services";
import type { TokenPair, User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  googleLogin: (idToken: string) => Promise<User>;
  register: (name: string, email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<User | null>;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const { access } = getStoredTokens();
    const cached = getStoredUser<User>();
    if (cached) setUserState(cached);
    if (!access) {
      setLoading(false);
      return;
    }
    authService
      .me()
      .then((me) => {
        setUserState(me);
        storeUser(me);
      })
      .catch(() => {
        clearTokens();
        setUserState(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const setUser = useCallback((u: User | null) => {
    setUserState(u);
    if (u) storeUser(u);
  }, []);

  const applyTokens = useCallback((pair: TokenPair) => {
    storeTokens(pair.access_token, pair.refresh_token);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const pair = await authService.login(email, password);
      applyTokens(pair);
      const me = await authService.me();
      setUser(me);
      return me;
    },
    [applyTokens, setUser],
  );

  const googleLogin = useCallback(
    async (idToken: string) => {
      const pair = await authService.googleLogin(idToken);
      applyTokens(pair);
      const me = await authService.me();
      setUser(me);
      return me;
    },
    [applyTokens, setUser],
  );

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      const pair = await authService.register(name, email, password);
      applyTokens(pair);
      const me = await authService.me();
      setUser(me);
      return me;
    },
    [applyTokens, setUser],
  );

  const refreshUser = useCallback(async () => {
    try {
      const me = await authService.me();
      setUser(me);
      return me;
    } catch {
      return null;
    }
  }, [setUser]);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch {
      /* ignore */
    }
    clearTokens();
    setUserState(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, googleLogin, register, logout, refreshUser, setUser }),
    [user, loading, login, googleLogin, register, logout, refreshUser, setUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}