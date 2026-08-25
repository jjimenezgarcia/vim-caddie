import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircleIcon, CheckIcon } from "@heroicons/react/24/solid";
import { DIFFICULTY_TIERS, difficultyStyle, sortExercises } from "../lib/difficulty.js";
import { fetchUserProgress } from "../hooks/useNvimSession.js";

export default function ExercisesPage({ exercises, error, difficultyFilter, onDifficultyFilterChange }) {
  const navigate = useNavigate();
  // Re-fetched on every mount, i.e. every time the player lands back on
  // this page (including right after holing out an exercise and hitting
  // "Back to exercises") — simpler than trying to push a live update in
  // from wherever a hole-out could happen.
  const [userProgress, setUserProgress] = useState({});
  useEffect(() => {
    fetchUserProgress()
      .then(setUserProgress)
      .catch(() => setUserProgress({}));
  }, []);

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

  const ordered = sortExercises(exercises);
  const filtered =
    difficultyFilter === "all" ? ordered : ordered.filter((ex) => ex.difficulty === difficultyFilter);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold text-slate-900">Exercises</h1>

      <div className="flex flex-wrap gap-1.5">
        <FilterPill
          label="All"
          active={difficultyFilter === "all"}
          count={exercises.length}
          onClick={() => onDifficultyFilterChange("all")}
        />
        {DIFFICULTY_TIERS.map((tier) => (
          <FilterPill
            key={tier}
            label={tier}
            tone={tier}
            active={difficultyFilter === tier}
            count={exercises.filter((ex) => ex.difficulty === tier).length}
            onClick={() => onDifficultyFilterChange(tier)}
          />
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-slate-500">No exercises at this difficulty yet.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {filtered.map((ex) => {
            const done = userProgress[ex.id];
            return (
              <button
                key={ex.id}
                onClick={() => navigate(`/exercises/${ex.id}`)}
                className={`text-left rounded-lg border bg-white p-4 transition-all hover:shadow-sm ${
                  done ? "border-emerald-200 hover:border-emerald-300" : "border-slate-200 hover:border-emerald-300"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <h2 className="flex items-center gap-1.5 font-medium text-slate-900">
                    {done && <CheckCircleIcon className="h-4 w-4 shrink-0 text-emerald-500" />}
                    {ex.title}
                  </h2>
                  {ex.par != null && <span className="text-xs text-slate-400 shrink-0">par {ex.par}</span>}
                </div>
                <p className="text-sm text-slate-600 mt-1 line-clamp-2">{ex.description}</p>
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  {ex.difficulty && (
                    <span
                      className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${difficultyStyle(ex.difficulty)}`}
                    >
                      {ex.difficulty}
                    </span>
                  )}
                  {done?.best_strokes != null && ex.par != null && (
                    <BestScoreBadge strokes={done.best_strokes} par={ex.par} />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Best-attempt strokes vs. par, in the same "N/M" shape for every
// exercise that has both — at or under par reads as a clean win (a
// checkmark), over par still shows the fraction but flags it instead of
// pretending it was clean.
function BestScoreBadge({ strokes, par }) {
  const atOrUnderPar = strokes <= par;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${
        atOrUnderPar
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-amber-200 bg-amber-50 text-amber-700"
      }`}
      title={atOrUnderPar ? "Best attempt, at or under par" : "Best attempt, over par"}
    >
      {atOrUnderPar && <CheckIcon className="h-3 w-3" />}
      {strokes}/{par}
    </span>
  );
}

function FilterPill({ label, tone, active, count, onClick }) {
  const toneClass = tone ? difficultyStyle(tone) : "bg-white text-slate-600 border-slate-200";
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-2.5 py-1 text-xs font-medium capitalize transition-all ${toneClass} ${
        active ? "ring-2 ring-offset-1 ring-emerald-400" : "opacity-60 hover:opacity-100"
      }`}
    >
      {label} ({count})
    </button>
  );
}
