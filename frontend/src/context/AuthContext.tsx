import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { getToken, setToken } from "../api/client";
import { authApi } from "../api/endpoints";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const finishAuth = async (token: string) => {
    setToken(token);
    setUser(await authApi.me());
  };

  const login = async (email: string, password: string) => {
    const { access_token } = await authApi.login(email, password);
    await finishAuth(access_token);
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const { access_token } = await authApi.register(email, password, fullName);
    await finishAuth(access_token);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const value = useMemo(() => ({ user, loading, login, register, logout }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
