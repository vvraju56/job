/* Lightweight auth token store. Client-only (localStorage). */

export const ACCESS_TOKEN_KEY = "makeable_access_token";
export const REFRESH_TOKEN_KEY = "makeable_refresh_token";
export const USER_KEY = "makeable_user";

const hasWindow = typeof window !== "undefined";

export function getStoredTokens(): { access: string | null; refresh: string | null } {
  if (!hasWindow) return { access: null, refresh: null };
  return {
    access: window.localStorage.getItem(ACCESS_TOKEN_KEY),
    refresh: window.localStorage.getItem(REFRESH_TOKEN_KEY),
  };
}

export function storeTokens(access: string, refresh: string) {
  if (!hasWindow) return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, access);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens() {
  if (!hasWindow) return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function getStoredUser<T>(): T | null {
  if (!hasWindow) return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function storeUser<T>(user: T) {
  if (!hasWindow) return;
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}