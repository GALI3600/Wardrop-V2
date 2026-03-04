"use client";

import Link from "next/link";
import { Sun, Moon, LogOut } from "lucide-react";
import { useTheme } from "@/providers/ThemeProvider";
import { useAuth } from "@/providers/AuthProvider";

export default function Header() {
  const { theme, toggleTheme } = useTheme();
  const { user, isLoading, logout } = useAuth();

  return (
    <header className="border-b border-[var(--border-color)] bg-[var(--bg-body)]/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold text-[var(--accent)] hover:opacity-80 transition">
          Wardrop
        </Link>
        <nav className="flex items-center gap-4">
          <Link href="/" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition">
            Produtos
          </Link>

          {!isLoading && user && (
            <Link
              href="/meus-produtos"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition"
            >
              Meus Produtos
            </Link>
          )}

          {!isLoading && !user && (
            <Link
              href="/login"
              className="text-sm text-[var(--accent)] hover:text-[var(--accent-hover)] font-medium transition"
            >
              Entrar
            </Link>
          )}

          {!isLoading && user && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-[var(--text-muted)] hidden sm:inline">
                {user.email}
              </span>
              <button
                onClick={logout}
                className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--price-up)] hover:bg-[var(--bg-input)] transition"
                aria-label="Sair"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}

          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-input)] transition"
            aria-label="Alternar tema"
          >
            {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </nav>
      </div>
    </header>
  );
}
