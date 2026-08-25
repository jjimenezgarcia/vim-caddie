import React, { useEffect, useState } from "react";
import {
  ArrowPathIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PauseIcon,
  PlayIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

const STEP_DELAY_MS = 450;
const CURSOR_BG = "#43ffa0";
const CURSOR_FG = "#0b140f";

function keyLabel(ch) {
  if (ch === "\r") return "Enter";
  if (ch === " ") return "Space";
  if (ch === "\x1b") return "Esc";
  return ch;
}

function isMovementKey(ch) {
  return ch === "h" || ch === "j" || ch === "k" || ch === "l";
}

function splitLines(text) {
  return (text || "").replace(/\n$/, "").split("\n");
}

function applyMovement(pos, ch, lineLengths) {
  let { line, col } = pos;
  if (ch === "h") col = Math.max(1, col - 1);
  else if (ch === "l") col = Math.min(Math.max(1, lineLengths[line - 1] ?? 1), col + 1);
  else if (ch === "j") line = Math.min(lineLengths.length, line + 1);
  else if (ch === "k") line = Math.max(1, line - 1);
  return { line, col };
}

// This replay is deliberately *faked*, not a second live Neovim session —
// it only ever simulates plain h/j/k/l cursor movement (a handful of
// lines, not "implementing vim"). Anything else in ideal_keystrokes
// (operators, :! commands, insert-mode text, etc.) doesn't get a
// simulated intermediate effect: the buffer just jumps straight to its
// already-known solved state (from success.content or success.cursor_at,
// the same data that already drives real scoring) once every keystroke
// has been applied.
function computeFinalState(exercise, initialLines) {
  const success = exercise.success || {};
  if (success.type === "cursor_at") {
    return { lines: initialLines, cursor: { line: success.line, col: success.col } };
  }
  if (success.type === "buffer_match") {
    return { lines: splitLines(success.content), cursor: null };
  }
  return { lines: initialLines, cursor: null };
}

// Replays sequence[0..upTo) tracking cursor position *and* whether we're
// sitting in command-line mode (":"/"/"/"?" until Enter or Esc) — while
// there, keystrokes are being typed onto vim's bottom line, not moving
// the cursor in the buffer, so movement keys are ignored and the typed
// text is tracked instead. What the command actually *does* once run is
// deliberately not simulated (no output, no side effect) — the point is
// only to show what gets typed; running it for real is on the player.
function replayTo(sequence, initialCursor, lineLengths, upTo) {
  let pos = initialCursor;
  let mode = "normal";
  let cmd = "";
  for (let i = 0; i < upTo; i++) {
    const ch = sequence[i];
    if (mode === "normal") {
      if (ch === ":" || ch === "/" || ch === "?") {
        mode = "command";
        cmd = ch;
      } else if (isMovementKey(ch)) {
        pos = applyMovement(pos, ch, lineLengths);
      }
    } else if (ch === "\r" || ch === "\x1b") {
      mode = "normal";
      cmd = "";
    } else {
      cmd += ch;
    }
  }
  return { cursor: pos, commandLine: mode === "command" ? cmd : null };
}

// step: how many keystrokes of `sequence` have been applied, 0..length.
// Pure function of step, not of history — this is what makes scrubbing
// back and forth just "jump to a different step" instead of needing to
// replay from the start.
function stateAtStep(sequence, initialLines, initialCursor, lineLengths, final, step) {
  if (step >= sequence.length) {
    const { cursor: replayCursor } = replayTo(sequence, initialCursor, lineLengths, sequence.length);
    const cursor = final.cursor || replayCursor;
    return { lines: final.lines, cursor, showCursor: !!final.cursor, commandLine: null };
  }
  const { cursor, commandLine } = replayTo(sequence, initialCursor, lineLengths, step);
  return { lines: initialLines, cursor, showCursor: !commandLine, commandLine };
}

export default function SolutionDemo({ exercise, onClose }) {
  const sequence = exercise.ideal_keystrokes || "";
  const initialLines = splitLines(exercise.workspace?.[exercise.open_file]);
  const initialCursor = {
    line: exercise.cursor_start?.line ?? 1,
    col: exercise.cursor_start?.col ?? 1,
  };
  const lineLengths = initialLines.map((l) => Math.max(1, l.length));
  const final = computeFinalState(exercise, initialLines);

  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(true);

  // autoplay: a plain timer that advances `step`, stops itself once done
  useEffect(() => {
    if (!playing) return undefined;
    if (step >= sequence.length) {
      setPlaying(false);
      return undefined;
    }
    const t = setTimeout(() => setStep((s) => Math.min(s + 1, sequence.length)), STEP_DELAY_MS);
    return () => clearTimeout(t);
  }, [playing, step, sequence.length]);

  // any arrow key hands control to the player: stop autoplay, move one
  // step at a time, back and forth
  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === "ArrowRight") {
        e.preventDefault();
        setPlaying(false);
        setStep((s) => Math.min(s + 1, sequence.length));
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        setPlaying(false);
        setStep((s) => Math.max(s - 1, 0));
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [sequence.length]);

  const { lines, cursor, showCursor, commandLine } = stateAtStep(
    sequence,
    initialLines,
    initialCursor,
    lineLengths,
    final,
    step,
  );
  const done = step >= sequence.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
      <div className="w-full max-w-2xl rounded-lg bg-white p-4 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-slate-900">Solution</h2>
            <p className="text-xs text-slate-500">
              {done
                ? "That's the solved state."
                : playing
                  ? "Watch how each keystroke gets there…"
                  : "Step through it yourself — use the arrow keys."}
            </p>
          </div>
          <button
            onClick={onClose}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors"
          >
            <XMarkIcon className="h-4 w-4" />
            Close
          </button>
        </div>

        <div className="flex gap-3">
          <div className="h-56 flex-1 overflow-auto rounded-md border border-slate-200">
            <FakeTerminal lines={lines} cursor={cursor} showCursor={showCursor} commandLine={commandLine} />
          </div>
          <div className="flex h-56 w-36 flex-wrap content-start gap-1.5 overflow-y-auto pr-0.5">
            {[...sequence].map((ch, i) => {
              const isCurrent = i === step - 1;
              const isPast = i < step - 1;
              return (
                <span
                  key={i}
                  className={`flex h-8 min-w-8 items-center justify-center rounded-md border px-1.5 font-mono text-sm transition-all duration-150 ${
                    isCurrent
                      ? "scale-95 border-emerald-500 bg-emerald-500 text-white shadow-inner"
                      : isPast
                        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                        : "border-slate-200 bg-white text-slate-500"
                  }`}
                  title={ch === "\r" ? "Enter" : ch === " " ? "Space" : undefined}
                >
                  {keyLabel(ch)}
                </span>
              );
            })}
          </div>
        </div>

        <div className="mt-3 flex items-center justify-center gap-2">
          <button
            onClick={() => {
              setPlaying(false);
              setStep((s) => Math.max(s - 1, 0));
            }}
            disabled={step <= 0}
            className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1 text-sm text-slate-600 hover:border-emerald-300 hover:text-emerald-700 transition-colors disabled:opacity-40 disabled:hover:border-slate-200 disabled:hover:text-slate-600"
          >
            <ChevronLeftIcon className="h-4 w-4" />
            Back
          </button>
          <button
            onClick={() => {
              if (done) {
                setStep(0);
                setPlaying(true);
              } else {
                setPlaying((p) => !p);
              }
            }}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 px-3 py-1 text-sm font-medium text-slate-700 hover:border-emerald-300 hover:text-emerald-700 transition-colors"
          >
            {done ? (
              <>
                <ArrowPathIcon className="h-4 w-4" />
                Replay
              </>
            ) : playing ? (
              <>
                <PauseIcon className="h-4 w-4" />
                Pause
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4" />
                Play
              </>
            )}
          </button>
          <button
            onClick={() => {
              setPlaying(false);
              setStep((s) => Math.min(s + 1, sequence.length));
            }}
            disabled={step >= sequence.length}
            className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1 text-sm text-slate-600 hover:border-emerald-300 hover:text-emerald-700 transition-colors disabled:opacity-40 disabled:hover:border-slate-200 disabled:hover:text-slate-600"
          >
            Next
            <ChevronRightIcon className="h-4 w-4" />
          </button>
          <span className="ml-2 text-xs text-slate-400">
            {Math.min(step, sequence.length)} / {sequence.length}
          </span>
        </div>
      </div>
    </div>
  );
}

function FakeTerminal({ lines, cursor, showCursor, commandLine }) {
  return (
    <div className="flex h-full w-full flex-col" style={{ background: "#0b140f", color: "#d7ffe8" }}>
      <pre className="m-0 flex-1 overflow-auto p-3 font-mono text-[13px] leading-5">
        {lines.map((line, li) => {
          const onCursorLine = showCursor && cursor.line - 1 === li;
          if (line.length === 0) {
            return (
              <div key={li}>
                {onCursorLine && cursor.col === 1 ? (
                  <span style={{ background: CURSOR_BG, color: CURSOR_FG }}>&nbsp;</span>
                ) : (
                  " "
                )}
              </div>
            );
          }
          return (
            <div key={li}>
              {[...line].map((c, ci) => {
                const isCursor = onCursorLine && cursor.col - 1 === ci;
                return (
                  <span key={ci} style={isCursor ? { background: CURSOR_BG, color: CURSOR_FG } : undefined}>
                    {c}
                  </span>
                );
              })}
            </div>
          );
        })}
      </pre>
      {/* Vim's own bottom command line — only what's been typed, not what
          running it would print, since simulating a command's actual
          output/effect is exactly what's not needed here. */}
      {commandLine != null && (
        <div className="border-t border-white/10 px-3 py-1 font-mono text-[13px] leading-5">
          {commandLine}
          <span style={{ background: CURSOR_BG, color: CURSOR_FG }}>&nbsp;</span>
        </div>
      )}
    </div>
  );
}
