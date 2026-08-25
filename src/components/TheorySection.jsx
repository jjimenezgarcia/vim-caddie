import React, { useState } from "react";
import { marked } from "marked";
import { getTheoryTopics } from "../lib/theory.js";
import { useKnownTheory } from "../hooks/useKnownTheory.js";

export default function TheorySection({ topicIds, difficulty }) {
  const topics = getTheoryTopics(topicIds);
  const { known, setTopicKnown } = useKnownTheory();

  // Genius exercises deliberately carry no related_theory at all — every
  // mechanic they use was already taught somewhere earlier (that's a hard
  // rule on how these get authored), but nothing is re-explained here.
  // This replaces the (otherwise just-empty) theory slot with that stated
  // outright, rather than silently showing nothing.
  if (difficulty === "genius") {
    return (
      <div className="rounded-lg border border-dashed border-violet-300 bg-violet-50 px-4 py-2.5 text-sm text-violet-700">
        You are on your own here — every mechanic this needs has already been taught, just not which ones.
      </div>
    );
  }

  if (topics.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      {topics.map((topic) => (
        <TheoryCard
          key={topic.id}
          topic={topic}
          isKnown={known.has(topic.id)}
          onToggleKnown={(v) => setTopicKnown(topic.id, v)}
        />
      ))}
    </div>
  );
}

function TheoryCard({ topic, isKnown, onToggleKnown }) {
  // starts collapsed only if already marked known when the card first
  // mounts — toggling "known" later just changes the checkbox, it doesn't
  // force the card open/shut against whatever the player was looking at
  const [expanded, setExpanded] = useState(!isKnown);

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between gap-3 px-4 py-2.5">
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex items-center gap-2 text-left font-medium text-slate-800"
        >
          <span className="text-xs text-slate-400">{expanded ? "▾" : "▸"}</span>
          {topic.title}
        </button>
        <label className="flex cursor-pointer select-none items-center gap-1.5 text-xs text-slate-500">
          <input
            type="checkbox"
            checked={isKnown}
            onChange={(e) => {
              const checked = e.target.checked;
              onToggleKnown(checked);
              if (checked) setExpanded(false);
            }}
            className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
          />
          I already know this
        </label>
      </div>
      {expanded && (
        <div
          className={
            "prose prose-slate prose-sm max-w-none border-t border-slate-100 px-4 py-3 " +
            "prose-headings:text-slate-900 prose-a:text-emerald-600 " +
            // scoped to INLINE code only (":not(pre)>code") — prose-code:
            // targets every <code>, including inside fenced ```blocks```,
            // which put this same dark-emerald text on those blocks' own
            // dark background: poor contrast, plus Typography's decorative
            // backtick quotes are redundant once code already reads as
            // code from the color/background alone
            "[&_:not(pre)>code]:rounded [&_:not(pre)>code]:bg-emerald-50 [&_:not(pre)>code]:px-1 " +
            "[&_:not(pre)>code]:py-0.5 [&_:not(pre)>code]:font-normal [&_:not(pre)>code]:text-emerald-700 " +
            "[&_:not(pre)>code]:before:content-none [&_:not(pre)>code]:after:content-none"
          }
          dangerouslySetInnerHTML={{ __html: marked.parse(topic.body) }}
        />
      )}
    </div>
  );
}
