// Real accounts now (username + password), not the earlier opaque-id
// scheme — see server/auth.py for why. This module owns the session
// token in localStorage and the three calls that touch it.
const TOKEN_KEY = "vimCaddieToken";
const USERNAME_KEY = "vimCaddieUsername";

// Default is same-origin (relative) — nginx proxies these paths to the
// backend. See useNvimSession.js's WS_BASE for the same reasoning.
const HTTP_BASE = import.meta.env.VITE_VIM_CADDIE_HTTP_URL || "";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUsername() {
  return localStorage.getItem(USERNAME_KEY);
}

function storeSession(token, username) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USERNAME_KEY, username);
}

async function authRequest(path, username, password) {
  const res = await fetch(`${HTTP_BASE}${path}`, {
    method: "POST",
    headers: { "X-Username": username, "X-Password": password },
  });
  const body = await res.json();
  if (!res.ok) {
    throw new Error(body.error || "Something went wrong.");
  }
  storeSession(body.token, body.username);
  return body.username;
}

export function signUp(username, password) {
  return authRequest("/api/signup", username, password);
}

export function logIn(username, password) {
  return authRequest("/api/login", username, password);
}

export async function logOut() {
  const token = getToken();
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USERNAME_KEY);
  if (token) {
    // best-effort: local session is already cleared either way, this
    // just also invalidates the token server-side instead of leaving it
    // valid (if unused) until it naturally expires
    fetch(`${HTTP_BASE}/api/logout`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
  }
}
