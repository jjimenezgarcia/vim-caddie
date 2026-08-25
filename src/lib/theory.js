// Theory content is bundled at build time (Vite's glob import), not fetched
// dynamically from the backend. Deliberate: it's genuinely static content,
// and after the exercise-loading path-traversal bug found earlier this
// session, there's no reason to open a second dynamic file-read surface
// for something that doesn't need one — the set of valid topic ids is
// fixed at build time, not something a request could ever redirect.
const modules = import.meta.glob("../theory/*.md", { eager: true, query: "?raw", import: "default" });

const TOPICS = new Map();
for (const [path, raw] of Object.entries(modules)) {
  const id = path.replace("../theory/", "").replace(/\.md$/, "");
  TOPICS.set(id, parseTopic(raw));
}

function parseTopic(raw) {
  const headingMatch = raw.match(/^#\s+(.+)$/m);
  const title = headingMatch ? headingMatch[1].trim() : "Theory";
  // body excludes the leading H1 — TheoryCard renders the title itself in
  // its own header, so keeping it in the markdown body would duplicate it
  const body = headingMatch ? raw.slice(headingMatch.index + headingMatch[0].length).trim() : raw.trim();
  return { title, body };
}

// exercise.related_theory entries that don't match a bundled file are
// skipped rather than throwing — an exercise author typo shouldn't be
// able to break the whole panel from rendering
export function getTheoryTopics(topicIds) {
  return (topicIds || [])
    .map((id) => {
      const topic = TOPICS.get(id);
      return topic ? { id, ...topic } : null;
    })
    .filter(Boolean);
}
