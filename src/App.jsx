import React, { lazy, Suspense, useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { FlagIcon } from "@heroicons/react/24/outline";
import LandingScreen from "./components/LandingScreen.jsx";
import AuthScreen from "./components/AuthScreen.jsx";
import ExercisesPage from "./pages/ExercisesPage.jsx";
import { fetchExercises } from "./hooks/useNvimSession.js";
import { getToken, getUsername, logOut } from "./lib/auth.js";

// The only heavy screen: pulls in ExercisePanel -> VimTerminal -> xterm.js
// (plus SolutionDemo). Loaded on demand, once a player actually opens an
// exercise, instead of bundled into the same chunk as the landing screen
// and the exercise list — those two are lightweight enough that splitting
// them further isn't worth the extra network round trip.
const ExercisePage = lazy(() => import("./pages/ExercisePage.jsx"));

export default function App() {
  // Whether there's a session token at all — not proof it's still valid
  // server-side (it could be expired/revoked), just enough to decide
  // which screen to show first. An expired token just means individual
  // requests start failing/coming back empty (see useNvimSession.js and
  // ExercisesPage.jsx), not a hard redirect back to this gate.
  const [authed, setAuthed] = useState(() => Boolean(getToken()));
  const [exercises, setExercises] = useState(null);
  const [error, setError] = useState(null);
  // "all" or one of DIFFICULTY_TIERS — lifted up here (not local to
  // ExercisesPage) so it survives navigating to an exercise and back
  const [difficultyFilter, setDifficultyFilter] = useState("all");

  useEffect(() => {
    if (!authed) return;
    fetchExercises()
      .then(setExercises)
      .catch((e) => setError(String(e)));
  }, [authed]);

  if (!authed) {
    return <AuthScreen onAuthenticated={() => setAuthed(true)} />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingScreen />} />
      <Route
        path="/exercises"
        element={
          <Shell onLoggedOut={() => setAuthed(false)}>
            <ExercisesPage
              exercises={exercises}
              error={error}
              difficultyFilter={difficultyFilter}
              onDifficultyFilterChange={setDifficultyFilter}
            />
          </Shell>
        }
      />
      <Route
        path="/exercises/:id"
        element={
          <Shell onLoggedOut={() => setAuthed(false)}>
            <Suspense fallback={<p className="text-slate-500">Loading…</p>}>
              <ExercisePage exercises={exercises} error={error} />
            </Suspense>
          </Shell>
        }
      />
    </Routes>
  );
}

function Shell({ children, onLoggedOut }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <FlagIcon className="h-5 w-5 text-emerald-600" />
            <span className="font-semibold text-slate-900">Vim Caddie</span>
            <span className="text-slate-400 text-sm ml-1">real Neovim, real par</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>
              Signed in as <span className="text-slate-600">{getUsername()}</span>
            </span>
            <button
              onClick={() => {
                logOut();
                onLoggedOut();
              }}
              className="hover:text-slate-700"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
