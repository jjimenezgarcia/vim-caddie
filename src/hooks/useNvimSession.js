import { useCallback, useEffect, useRef, useState } from "react";
import { getToken } from "../lib/auth.js";

// Default is same-origin (relative) — nginx proxies /ws and the REST
// paths to the backend, so the browser never needs the backend's own
// address. The VITE_* overrides exist only for setups where that isn't
// true (e.g. backend and frontend genuinely on different origins).
const WS_BASE = import.meta.env.VITE_VIM_CADDIE_WS_URL ||
  `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;
const HTTP_BASE = import.meta.env.VITE_VIM_CADDIE_HTTP_URL || "";

export async function fetchExercises() {
  const res = await fetch(`${HTTP_BASE}/api/exercises`);
  if (!res.ok) throw new Error(`GET /api/exercises: ${res.status}`);
  return res.json();
}

// { [exerciseId]: { holed, best_strokes, first_holed_at, last_holed_at } }
// for whoever the current session token belongs to — named "user
// progress" here (not just "progress") to keep it distinct from
// useNvimSession's own `progress` state, which is the unrelated live
// reach_markers counter. Comes back empty (not an error) if signed out
// or the token's expired — see server/app.py's /progress handling.
export async function fetchUserProgress() {
  const token = getToken();
  if (!token) return {};
  const res = await fetch(`${HTTP_BASE}/api/progress`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return {};
  return res.json();
}

// Owns the one WebSocket connection to the Python backend for a single
// exercise attempt. See server/app.py's docstring for the full message
// list; the ones surfaced here: raw terminal bytes (-> onTermData, for
// VimTerminal's xterm.js instance), buffer/cursor/mode snapshots
// (-> state, used only to know when to reset per-attempt UI, not to
// render anything), per-keystroke hit/holed events (-> hits, holed) for
// stroke-based exercises, and reach_markers progress (-> progress) for
// exercises with no fixed reference path instead.
export function useNvimSession(exerciseId) {
  const wsRef = useRef(null);
  const termListenersRef = useRef(new Set());
  const [state, setState] = useState(null);
  const [connected, setConnected] = useState(false);
  const [exerciseInfo, setExerciseInfo] = useState(null);
  const [hits, setHits] = useState([]); // array of booleans, one per keystroke
  const [holed, setHoled] = useState(false);
  // {reached, count} for a reach_markers exercise (see server/app.py) —
  // null for any exercise using a one-shot checker instead, which never
  // sends this message type at all
  const [progress, setProgress] = useState(null);
  // true once nvim's own process exits, for any reason (:q!/:wq!, a crash,
  // the container dying) — the backend detects this itself (pty EOF) and
  // proactively tears the session down; this just lets ExercisePanel show
  // something instead of leaving the player looking at a frozen terminal
  const [exited, setExited] = useState(false);

  useEffect(() => {
    if (!exerciseId) return undefined;
    setState(null);
    setExerciseInfo(null);
    setHits([]);
    setHoled(false);
    setExited(false);
    setProgress(null);

    // Session token travels as a WebSocket subprotocol (the
    // Sec-WebSocket-Protocol header), never in the URL — a native
    // WebSocket can't set arbitrary headers, and this is the one
    // JS-controllable channel that exists for exactly this purpose. See
    // server/app.py's process_request docstring for the rest of this.
    const url = `${WS_BASE}/ws?exercise=${encodeURIComponent(exerciseId)}`;
    // An empty-string subprotocol is invalid per the WebSocket spec (the
    // constructor throws synchronously) — omit the argument entirely
    // rather than risk that if somehow reached with no token set.
    const token = getToken();
    const ws = token ? new WebSocket(url, [token]) : new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (evt) => {
      let msg;
      try {
        msg = JSON.parse(evt.data);
      } catch {
        return;
      }
      if (msg.type === "term") {
        const bytes = base64ToBytes(msg.data);
        termListenersRef.current.forEach((fn) => fn(bytes));
      } else if (msg.type === "state") {
        setState({ lines: msg.lines, cursor: msg.cursor, mode: msg.mode });
      } else if (msg.type === "ready") {
        setExerciseInfo(msg.exercise || null);
      } else if (msg.type === "hit") {
        setHits((prev) => [...prev, msg.good]);
      } else if (msg.type === "holed") {
        setHoled(true);
      } else if (msg.type === "progress") {
        setProgress({ reached: msg.reached, count: msg.count });
      } else if (msg.type === "exit") {
        setExited(true);
      }
    };

    return () => ws.close();
  }, [exerciseId]);

  const sendInput = useCallback((data) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "input", data }));
    }
  }, []);

  // separate from sendInput: this is ONLY for scoring (see VimTerminal.jsx's
  // header comment) — the backend never writes this to the pty
  const sendKeypress = useCallback((key) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "keypress", data: key }));
    }
  }, []);

  const sendResize = useCallback((cols, rows) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "resize", cols, rows }));
    }
  }, []);

  const onTermData = useCallback((fn) => {
    termListenersRef.current.add(fn);
    return () => termListenersRef.current.delete(fn);
  }, []);

  return {
    state,
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
  };
}

function base64ToBytes(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}
