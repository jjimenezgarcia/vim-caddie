import React, { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";

// Renders the real Neovim TTY, verbatim — no Vim interpretation happens on
// this side. Keystrokes go straight to the pty via sendInput; bytes coming
// back from the pty (via onTermData) are written straight into xterm.js.
//
// sendInput (term.onData) carries EVERYTHING that needs to reach the pty —
// real keystrokes, but also xterm.js's own automatic terminal-protocol
// replies (cursor-position reports, OSC background-color queries, etc.
// that Neovim's startup and every redraw ask the terminal to answer).
// Those auto-replies must still reach the pty for the terminal to work,
// but they are NOT the player typing — scoring off onData counts them as
// keystrokes too, which is where "strokes appear just from opening the
// page" came from. sendKeypress (term.onKey) fires only for genuine
// physical key presses, so scoring is wired to that instead.
//
// Mouse input is deliberately neutered except for plain focus-on-click:
// nvim's own 'mouse' option is already off (server/vimrc.py), but that
// only stops Neovim from requesting mouse *reporting* — it doesn't stop
// xterm.js's separate, terminal-level "alternate scroll" behavior, which
// (for any app running in the alt-screen buffer, mouse-aware or not)
// translates wheel scroll into Up/Down arrow key sequences sent straight
// to the pty. That's what was moving the cursor on scroll. xterm.js also
// does its own click-to-position-cursor/drag-to-select handling that
// should never fire here either — only real keystrokes should ever reach
// nvim. All of that is intercepted below, in the capture phase, before it
// reaches xterm's own listeners; a plain click is still allowed through
// far enough to focus the terminal (so typing works without the whole
// page needing to stay focused there), just nothing beyond that.
const VimTerminal = forwardRef(function VimTerminal(
  { connected, onTermData, sendInput, sendKeypress, sendResize, locked },
  ref,
) {
  const containerRef = useRef(null);
  const fitAddonRef = useRef(null);
  const termRef = useRef(null);
  const sendResizeRef = useRef(sendResize);
  sendResizeRef.current = sendResize;
  // read via ref (not the prop directly) for the same reason sendResize
  // is: term.onData/onKey below are bound once, inside the mount effect —
  // a later prop change alone wouldn't reach those already-bound closures
  const lockedRef = useRef(locked);
  lockedRef.current = locked;

  useEffect(() => {
    const term = new Terminal({
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
      fontSize: 13,
      cursorBlink: true,
      theme: {
        background: "#0b140f",
        foreground: "#d7ffe8",
        cursor: "#43ffa0",
        selectionBackground: "#1d8f5c66",
      },
    });
    const fitAddon = new FitAddon();
    fitAddonRef.current = fitAddon;
    termRef.current = term;
    term.loadAddon(fitAddon);
    term.open(containerRef.current);
    fitAddon.fit();
    // Auto-focus on mount so typing works immediately, with no click
    // needed at all — the mousedown listener below (not xterm's own) is
    // what handles focusing it back after the click.
    term.focus();
    // FitAddon measures cell height from the terminal's already-rendered
    // font metrics — right at mount, on the very first layout pass, that
    // measurement can be taken before the browser has fully settled font
    // loading/layout, computing a cellHeight a hair too small. That makes
    // fit() request one row too many, which is exactly "overflows past
    // the bottom border by a few pixels" rather than a gross miscalc.
    // Re-fitting one frame later, once layout has actually settled, is
    // the standard fix for this well-known xterm.js timing gotcha.
    requestAnimationFrame(() => fitAddon.fit());

    const dataDisposable = term.onData((data) => {
      if (!lockedRef.current) sendInput(data);
    });
    const keyDisposable = term.onKey(({ key }) => {
      if (!lockedRef.current) sendKeypress(key);
    });
    const unsubscribeTerm = onTermData((bytes) => term.write(bytes));

    // Capture-phase, ahead of xterm's own listeners on its inner elements
    // (registered during term.open(), in the bubble phase like everything
    // else) — stopPropagation here means those inner listeners never run
    // at all for these events. mousedown is the one exception: swallowed
    // the same way, but we drive the one thing we *do* want (focus)
    // ourselves instead of letting xterm decide what a click does.
    const container = containerRef.current;
    const focusOnly = (e) => {
      e.preventDefault();
      e.stopPropagation();
      term.focus();
    };
    const swallow = (e) => {
      e.preventDefault();
      e.stopPropagation();
    };
    container.addEventListener("mousedown", focusOnly, true);
    container.addEventListener("mouseup", swallow, true);
    container.addEventListener("click", swallow, true);
    container.addEventListener("dblclick", swallow, true);
    container.addEventListener("contextmenu", swallow, true);
    container.addEventListener("wheel", swallow, { capture: true, passive: false });

    const handleResize = () => {
      fitAddon.fit();
      sendResizeRef.current(term.cols, term.rows);
    };
    window.addEventListener("resize", handleResize);
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(containerRef.current);

    return () => {
      window.removeEventListener("resize", handleResize);
      resizeObserver.disconnect();
      container.removeEventListener("mousedown", focusOnly, true);
      container.removeEventListener("mouseup", swallow, true);
      container.removeEventListener("click", swallow, true);
      container.removeEventListener("dblclick", swallow, true);
      container.removeEventListener("contextmenu", swallow, true);
      container.removeEventListener("wheel", swallow, { capture: true });
      dataDisposable.dispose();
      keyDisposable.dispose();
      unsubscribeTerm();
      term.dispose();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // once the socket (re)connects, tell the backend our actual size instead
  // of leaving it at the pty's 80x24 default
  useEffect(() => {
    if (connected && fitAddonRef.current && termRef.current) {
      fitAddonRef.current.fit();
      sendResizeRef.current(termRef.current.cols, termRef.current.rows);
      termRef.current.focus();
    }
  }, [connected]);

  // lets a parent reclaim keyboard focus for this terminal after focus was
  // necessarily sent elsewhere (e.g. a button inside the Show-solution
  // modal) — there's no click-to-focus fallback to rely on instead
  useImperativeHandle(ref, () => ({
    focus: () => termRef.current?.focus(),
  }));

  // No padding on this element: FitAddon measures rows/cols from
  // *this* div's own computed height/width (it's what becomes
  // terminal.element.parentElement once term.open() runs), so any
  // padding here has to be reasoned about as part of that math. Simpler
  // to keep this div's box exactly equal to its parent's and put the
  // visual gutter on a element further out instead (see ExercisePanel.jsx).
  // Pointer events stay enabled here on purpose — see the mount effect's
  // capture-phase listeners for what mouse input is actually allowed to do.
  return <div ref={containerRef} style={{ width: "100%", height: "100%" }} />;
});

export default VimTerminal;
