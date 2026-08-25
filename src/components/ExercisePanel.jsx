import React, { useRef, useState } from "react";
import {
  ArrowLeftIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  LightBulbIcon,
} from "@heroicons/react/24/outline";
import VimTerminal from "./VimTerminal.jsx";
import TheorySection from "./TheorySection.jsx";
import SolutionDemo from "./SolutionDemo.jsx";
import { useNvimSession } from "../hooks/useNvimSession.js";
import { difficultyStyle, solutionAllowed } from "../lib/difficulty.js";

export default function ExercisePanel({ exercise, onBack, onRetry, onSelectId }) {
  const [showSolution, setShowSolution] = useState(false);
  const terminalRef = useRef(null);
  const {
    connected,
    exerciseInfo,
    hits,
    holed,
    exited,
    progress,
    sendInput,
    sendKeypress,
    sendResize,
    onTermData,
  } = useNvimSession(exercise.id);

  // reach_markers exercises (a moving/respawning target) have no fixed
  // ideal_keystrokes path to score strokes against and no par — free play
  // until done, tracked via "progress" instead of the hit-dots strip
  const isReachMarkers = exerciseInfo?.success?.type === "reach_markers";

  const strokes = hits.length;
  const par = exerciseInfo?.par ?? exercise.par;
  const overPar = strokes - (par ?? 0);
  const perfectPar = par != null && strokes <= par;
  // once the level is solved (or the session ended some other way), stop
  // forwarding keystrokes to the terminal entirely — not just show an
  // overlay on top of a still-live session (see VimTerminal's `locked`)
  const locked = holed || exited;

  return (
    <div className="flex flex-col gap-4">
      {/* Sticky, not just top-of-page: this is the only way back to the
          list at all (no other nav exists), so it has to stay reachable
          no matter how far down a tall exercise (theory + objective +
          terminal) the player has scrolled. */}
      <div className="sticky top-0 z-10 -mx-6 bg-slate-50 px-6 py-2">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back to exercises
        </button>
      </div>

      {exercise.prerequisites?.length > 0 && (
        <div className="flex items-start gap-2 rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-800">
          <InformationCircleIcon className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            Recommended before this one:{" "}
            {exercise.prerequisites.map((p, i) => (
              <React.Fragment key={p.id}>
                {i > 0 && ", "}
                <button
                  onClick={() => onSelectId?.(p.id)}
                  className="font-medium underline decoration-sky-300 underline-offset-2 hover:decoration-sky-600"
                >
                  {p.title}
                </button>
              </React.Fragment>
            ))}
          </p>
        </div>
      )}

      <TheorySection topicIds={exercise.related_theory} difficulty={exercise.difficulty} />

      <div className="flex flex-col gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold text-slate-900">{exercise.title}</h1>
            {exercise.difficulty && (
              <span
                className={`rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${difficultyStyle(exercise.difficulty)}`}
              >
                {exercise.difficulty}
              </span>
            )}
          </div>
          <p className="text-slate-500 text-sm">{exercise.description}</p>
        </div>
        {exercise.objective?.length > 0 && (
          <ul className="max-w-2xl list-disc space-y-1 pl-5 text-slate-700">
            {exercise.objective.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3 text-sm">
        {isReachMarkers ? (
          <Stat label="reached" value={`${progress?.reached ?? 0} / ${progress?.count ?? "?"}`} />
        ) : (
          <>
            <Stat label="par" value={par} />
            <Stat label="strokes" value={strokes} />
            <Stat
              label="over par"
              value={overPar > 0 ? `+${overPar}` : overPar}
              tone={overPar > 0 ? "amber" : "emerald"}
            />
          </>
        )}
        {!connected && (
          <Badge tone={exited ? "rose" : "slate"}>{exited ? "disconnected" : "connecting…"}</Badge>
        )}
        {holed && (
          <Badge tone="emerald">
            <CheckCircleIcon className="h-3.5 w-3.5" />
            holed out
          </Badge>
        )}
        {exercise.ideal_keystrokes && solutionAllowed(exercise.difficulty) && (
          <button
            onClick={() => setShowSolution(true)}
            className="ml-auto inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:border-emerald-300 hover:text-emerald-700 transition-colors"
          >
            <LightBulbIcon className="h-3.5 w-3.5" />
            Show solution
          </button>
        )}
      </div>

      {showSolution && (
        <SolutionDemo
          exercise={exercise}
          onClose={() => {
            setShowSolution(false);
            terminalRef.current?.focus();
          }}
        />
      )}

      <div
        className="relative rounded-lg overflow-hidden border border-slate-200 shadow-sm"
        style={{ height: 420 }}
      >
        {/* The visual gutter lives here, one level out from where
            VimTerminal's own div sits — that div is what FitAddon reads
            dimensions from directly (see its comment), so padding on it
            specifically would need to be reasoned about as part of that
            math. Putting it here instead keeps VimTerminal's own box
            exactly equal to its immediate parent, no padding involved
            in the row/col calculation at all. */}
        <div className="h-full w-full box-border p-1.5">
          <VimTerminal
            ref={terminalRef}
            connected={connected}
            onTermData={onTermData}
            sendInput={sendInput}
            sendKeypress={sendKeypress}
            sendResize={sendResize}
            locked={locked}
          />
        </div>
        {/* Floating over the terminal itself, not page chrome — always
            available (not just after holing/exiting), since a player who's
            lost or has messed up the buffer shouldn't have to quit nvim
            first to get a clean start. Same onRetry as everywhere else: a
            fresh attempt is just a remount (see App.jsx's key={...}). */}
        <button
          onClick={onRetry}
          title="Reset this exercise"
          className="absolute right-3 top-3 inline-flex items-center gap-1.5 rounded-md bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-md hover:bg-slate-100 transition-colors"
        >
          <ArrowPathIcon className="h-4 w-4" />
          Reset
        </button>
        {holed ? (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="mx-6 rounded-lg border border-emerald-400 bg-emerald-600 px-5 py-4 text-center shadow-lg pointer-events-auto">
              <p className="font-semibold text-white">
                {isReachMarkers
                  ? "Nice — you got them all!"
                  : perfectPar
                    ? "That was a perfect par!"
                    : "Want to try again and improve your par?"}
              </p>
              <div className="mt-3 flex items-center justify-center gap-2">
                {!isReachMarkers && !perfectPar && (
                  <button
                    onClick={onRetry}
                    className="rounded-md bg-white px-3 py-1.5 text-sm font-medium text-emerald-700 hover:bg-emerald-50 transition-colors"
                  >
                    Try again
                  </button>
                )}
                <button
                  onClick={onBack}
                  className="rounded-md border border-emerald-300 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
                >
                  Go back to exercises
                </button>
              </div>
            </div>
          </div>
        ) : (
          exited && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="mx-6 rounded-lg border border-rose-400 bg-rose-600 px-5 py-4 text-center shadow-lg pointer-events-auto">
                <p className="font-semibold text-white">You closed the file!</p>
                <div className="mt-3 flex items-center justify-center gap-2">
                  <button
                    onClick={onRetry}
                    className="rounded-md bg-white px-3 py-1.5 text-sm font-medium text-rose-700 hover:bg-rose-50 transition-colors"
                  >
                    Try again
                  </button>
                  <button
                    onClick={onBack}
                    className="rounded-md border border-rose-300 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-700 transition-colors"
                  >
                    Go back to exercises
                  </button>
                </div>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, tone }) {
  const toneClass =
    tone === "amber"
      ? "text-amber-600"
      : tone === "emerald"
        ? "text-emerald-600"
        : "text-slate-900";
  return (
    <div className="flex items-baseline gap-1.5">
      <span className={`font-semibold ${toneClass}`}>{value}</span>
      <span className="text-slate-500">{label}</span>
    </div>
  );
}

function Badge({ tone, children }) {
  const toneClass =
    tone === "emerald"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : tone === "rose"
        ? "bg-rose-600 text-white border-rose-400"
        : "bg-slate-50 text-slate-600 border-slate-200";
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${toneClass}`}>
      {children}
    </span>
  );
}
