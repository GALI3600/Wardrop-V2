"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import type { UserOut } from "@/lib/types";
import * as api from "@/lib/api";

interface AuthContextValue {
  user: UserOut | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Validate token on mount
  useEffect(() => {
    const token = localStorage.getItem("wardrop-token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    api
      .getMe()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("wardrop-token");
      })
      .finally(() => setIsLoading(false));
  }, []);

  // React to token changes from extension sync or other tabs
  useEffect(() => {
    function handleStorage(e: StorageEvent | Event) {
      const token = localStorage.getItem("wardrop-token");
      if (token && !user) {
        api.getMe().then(setUser).catch(() => {
          localStorage.removeItem("wardrop-token");
        });
      } else if (!token && user) {
        setUser(null);
      }
    }
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [user]);

  const login = useCallback(async (email: string, password: string) => {
    await api.login(email, password);
    const me = await api.getMe();
    setUser(me);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    await api.register(email, password);
    const me = await api.getMe();
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("wardrop-token");
    // Notify extension content script on the same tab (storage event only fires cross-tab)
    window.dispatchEvent(
      new StorageEvent("storage", { key: "wardrop-token", newValue: null })
    );
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
