// Keep this order in sync with server/exercises.py's DIFFICULTY_TIERS —
// difficulty itself is always computed server-side from an exercise's par
// (never authored per-exercise, see that file's comment); this module only
// owns the ordering/styling the frontend needs to filter and display it.
export const DIFFICULTY_TIERS = [
  "apprentice",
  "beginner",
  "intermediate",
  "advanced",
  "professional",
  "genius",
];

const STYLES = {
  apprentice: "bg-slate-100 text-slate-700 border-slate-200",
  beginner: "bg-emerald-50 text-emerald-700 border-emerald-200",
  intermediate: "bg-sky-50 text-sky-700 border-sky-200",
  advanced: "bg-amber-50 text-amber-700 border-amber-200",
  professional: "bg-orange-50 text-orange-700 border-orange-200",
  genius: "bg-violet-50 text-violet-700 border-violet-200",
};

export function difficultyStyle(tier) {
  return STYLES[tier] || STYLES.apprentice;
}

// Step-by-step solutions stop being offered past "advanced" — professional
// and genius exercises are meant to be solved unaided.
const SOLUTION_CUTOFF = DIFFICULTY_TIERS.indexOf("advanced");

export function solutionAllowed(tier) {
  const i = DIFFICULTY_TIERS.indexOf(tier);
  return i !== -1 && i <= SOLUTION_CUTOFF;
}

// Main-page ordering: difficulty tier first, but a prerequisite must always
// come before whatever depends on it even if that ever put it at odds with
// tier order (it shouldn't, in practice — a prerequisite is normally the
// same tier or easier — but this is what actually guarantees it rather
// than hoping tier order alone lines up). Implemented as a DFS over the
// difficulty-sorted list: visiting an exercise first visits its
// prerequisites (recursively, so chains work), so every exercise appears
// only once it's already placed everything it depends on.
export function sortExercises(exercises) {
  const byId = new Map(exercises.map((ex) => [ex.id, ex]));
  const tierIndex = (ex) => {
    const i = DIFFICULTY_TIERS.indexOf(ex.difficulty);
    return i === -1 ? DIFFICULTY_TIERS.length : i;
  };
  const baseline = [...exercises].sort((a, b) => tierIndex(a) - tierIndex(b));

  const visited = new Set();
  const ordered = [];
  function visit(ex) {
    if (!ex || visited.has(ex.id)) return;
    visited.add(ex.id);
    for (const prereq of ex.prerequisites || []) {
      visit(byId.get(prereq.id));
    }
    ordered.push(ex);
  }
  baseline.forEach(visit);
  return ordered;
}
