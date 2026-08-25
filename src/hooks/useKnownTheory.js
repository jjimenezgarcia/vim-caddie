import { useCallback, useState } from "react";

// Per-browser preference ("I already know this"), not tied to any
// exercise or session — there's no user accounts in this app, so
// localStorage is the natural home for it. Missing/blocked storage (e.g.
// private browsing) just means it won't persist, not a hard failure.
const STORAGE_KEY = "vimCaddie.knownTheory";

function readKnown() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
}

function writeKnown(set) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...set]));
  } catch {
    // ignore
  }
}

export function useKnownTheory() {
  const [known, setKnown] = useState(readKnown);

  const setTopicKnown = useCallback((id, isKnown) => {
    setKnown((prev) => {
      const next = new Set(prev);
      if (isKnown) next.add(id);
      else next.delete(id);
      writeKnown(next);
      return next;
    });
  }, []);

  return { known, setTopicKnown };
}
