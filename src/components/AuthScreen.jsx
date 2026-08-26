import React, { useState } from "react";
import { FlagIcon } from "@heroicons/react/24/outline";
import { logIn, signUp } from "../lib/auth.js";

export default function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const action = mode === "login" ? logIn : signUp;
      await action(username, password);
      onAuthenticated();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="flex w-full max-w-xs flex-col items-center gap-4 text-center">
        <FlagIcon className="h-12 w-12 text-emerald-600" />
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Vim Caddie</h1>
          <p className="text-slate-500">real Neovim, real par</p>
        </div>

        <form onSubmit={handleSubmit} className="flex w-full flex-col gap-3">
          <input
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="username"
            autoComplete="username"
            className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-400 focus:outline-none"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-400 focus:outline-none"
          />
          {error && <p className="text-left text-sm text-rose-600">{error}</p>}
          <button
            type="submit"
            disabled={busy}
            className={`mt-1 rounded-full px-8 py-2.5 text-lg font-medium shadow-sm transition-colors disabled:opacity-60 ${
              mode === "login"
                ? "bg-emerald-600 text-white hover:bg-emerald-500"
                : "bg-sky-200 text-sky-900 hover:bg-sky-300"
            }`}
          >
            {mode === "login" ? "Log in" : "Sign up"}
          </button>
        </form>

        <button
          onClick={() => {
            setMode((m) => (m === "login" ? "signup" : "login"));
            setError(null);
          }}
          className="text-sm text-slate-500 hover:text-slate-700"
        >
          {mode === "login" ? "New here? Create an account" : "Already have an account? Log in"}
        </button>
      </div>
    </div>
  );
}
