import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ExercisePanel from "../components/ExercisePanel.jsx";

// This whole module (and everything it pulls in — ExercisePanel,
// VimTerminal, xterm.js, SolutionDemo) is loaded lazily by App.jsx, only
// once a player actually opens an exercise — the landing screen and the
// exercise list never need any of it.
export default function ExercisePage({ exercises, error }) {
  const { id } = useParams();
  const navigate = useNavigate();
  // bumped on retry — part of ExercisePanel's key below, forcing React to
  // remount it. Each attempt is a fresh WS connection anyway (a new
  // backend session, a new container, a fresh workspace), so a genuine
  // "start over" doesn't need any new reset protocol — just a new mount.
  // The id is part of the same key, so navigating to a *different*
  // exercise (e.g. via the "recommended first" link) remounts too, even
  // if this counter happens to be left over from a previous one.
  const [attempt, setAttempt] = useState(0);

  if (error) {
    return (
      <p className="text-rose-600">
        Couldn't reach the backend ({error}). Is <code>npm run dev</code> running?
      </p>
    );
  }
  if (!exercises) {
    return <p className="text-slate-500">Loading exercises…</p>;
  }

  const exercise = exercises.find((ex) => ex.id === id);
  if (!exercise) {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-rose-600">No exercise named "{id}".</p>
        <button
          onClick={() => navigate("/exercises")}
          className="self-start text-sm text-slate-500 hover:text-slate-800 transition-colors"
        >
          Back to exercises
        </button>
      </div>
    );
  }

  return (
    <ExercisePanel
      key={`${id}:${attempt}`}
      exercise={exercise}
      onBack={() => navigate("/exercises")}
      onRetry={() => setAttempt((a) => a + 1)}
      onSelectId={(otherId) => navigate(`/exercises/${otherId}`)}
    />
  );
}
