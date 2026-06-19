/** Where to send the user after OAuth completes (stored before leaving the app). */
export const OAUTH_RETURN_PATH_KEY = "oauth_return_path";

export type OAuthProvider = "google" | "linkedin";

function apiOrigin(): string {
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:5000/api";
  return apiUrl.replace(/\/api\/?$/, "");
}

function callbackUrl(): string {
  const configured = import.meta.env.VITE_OAUTH_CALLBACK_URL as string | undefined;
  if (configured) return configured;
  return `${window.location.origin}/auth/callback`;
}

/** Backend URL that starts the OAuth flow (Passport-style routes). */
export function getOAuthStartUrl(provider: OAuthProvider): string {
  const envKey =
    provider === "google" ? "VITE_OAUTH_GOOGLE_URL" : "VITE_OAUTH_LINKEDIN_URL";
  const fromEnv = import.meta.env[envKey] as string | undefined;
  if (fromEnv) return fromEnv;

  const origin = apiOrigin();
  return `${origin}/api/auth/${provider}`;
}

/** Save intended post-login path, then redirect to Google / LinkedIn via the API. */
export function startOAuth(provider: OAuthProvider, returnPath = "/"): void {
  try {
    sessionStorage.setItem(OAUTH_RETURN_PATH_KEY, returnPath);
  } catch {
    /* ignore */
  }

  const start = new URL(getOAuthStartUrl(provider));
  start.searchParams.set("redirect", callbackUrl());
  window.location.assign(start.toString());
}
