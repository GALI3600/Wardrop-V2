"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";

export default function LoginPage() {
  const { user, isLoading, login, register } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/meus-produtos";

  const [tab, setTab] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && user) {
      router.replace(redirect);
    }
  }, [isLoading, user, router, redirect]);

  if (isLoading || user) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Preencha email e senha.");
      return;
    }

    setSubmitting(true);
    try {
      if (tab === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
      router.replace(redirect);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao autenticar.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div
        className="w-full max-w-sm bg-[var(--bg-card)] rounded-xl p-6"
        style={{ boxShadow: "var(--shadow-lg)" }}
      >
        {/* Tabs */}
        <div className="flex mb-6 border-b border-[var(--border-color)]">
          <button
            onClick={() => { setTab("login"); setError(""); }}
            className={`flex-1 pb-2 text-sm font-medium transition border-b-2 ${
              tab === "login"
                ? "border-[var(--accent)] text-[var(--accent)]"
                : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            Login
          </button>
          <button
            onClick={() => { setTab("register"); setError(""); }}
            className={`flex-1 pb-2 text-sm font-medium transition border-b-2 ${
              tab === "register"
                ? "border-[var(--accent)] text-[var(--accent)]"
                : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            Registrar
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-color)] focus:outline-none focus:border-[var(--accent)] transition text-sm"
          />
          <input
            type="password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={tab === "login" ? "current-password" : "new-password"}
            className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-color)] focus:outline-none focus:border-[var(--accent)] transition text-sm"
          />

          {error && (
            <p className="text-sm text-[var(--price-up)]">{error}</p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2 rounded-lg bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white font-medium text-sm transition disabled:opacity-50"
          >
            {submitting ? "Aguarde..." : tab === "login" ? "Entrar" : "Criar conta"}
          </button>
        </form>
      </div>
    </div>
  );
}
