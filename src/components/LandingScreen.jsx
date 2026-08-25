import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FlagIcon } from "@heroicons/react/24/outline";

// A quick golf-ball wipe on the way out, not a return to the earlier
// full-scene animation (that one landed poorly) — just enough motion that
// the jump from landing screen to dashboard doesn't feel like a hard cut.
const ROLL_MS = 650;

export default function LandingScreen() {
  const [leaving, setLeaving] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!leaving) return undefined;
    const t = setTimeout(() => navigate("/exercises"), ROLL_MS);
    return () => clearTimeout(t);
  }, [leaving, navigate]);

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-50">
      <div
        className={`flex flex-col items-center gap-3 text-center transition-opacity duration-200 ${
          leaving ? "opacity-0" : "opacity-100"
        }`}
      >
        <FlagIcon className="h-12 w-12 text-emerald-600" />
        <h1 className="text-4xl font-semibold text-slate-900">Vim Caddie</h1>
        <p className="text-slate-500">real Neovim, real par</p>
        <button
          onClick={() => setLeaving(true)}
          disabled={leaving}
          className="mt-4 rounded-full bg-emerald-600 px-8 py-2.5 text-lg font-medium text-white shadow-sm hover:bg-emerald-500 transition-colors disabled:opacity-80"
        >
          Start
        </button>
      </div>

      {leaving && (
        <svg
          viewBox="0 0 40 40"
          className="lp-rolling-ball pointer-events-none fixed left-0 top-1/2 h-10 w-10 -translate-y-1/2 drop-shadow-md"
        >
          <circle cx="20" cy="20" r="18" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1.5" />
          <circle cx="14" cy="14" r="1.6" fill="#dfe4ea" />
          <circle cx="22" cy="12" r="1.6" fill="#dfe4ea" />
          <circle cx="27" cy="19" r="1.6" fill="#dfe4ea" />
          <circle cx="16" cy="24" r="1.6" fill="#dfe4ea" />
          <circle cx="24" cy="26" r="1.6" fill="#dfe4ea" />
        </svg>
      )}

      <style>{`
        @keyframes lp-roll {
          from { transform: translate(-4rem, -50%) rotate(0deg); }
          to   { transform: translate(calc(100vw + 4rem), -50%) rotate(900deg); }
        }
        .lp-rolling-ball {
          animation: lp-roll ${ROLL_MS}ms cubic-bezier(0.3, 0, 0.7, 1) both;
        }
        @media (prefers-reduced-motion: reduce) {
          .lp-rolling-ball { animation: none; opacity: 0; }
        }
      `}</style>
    </div>
  );
}
