export function encodeOAuthState(redirectUrl) {
  return Buffer.from(JSON.stringify({ redirect: redirectUrl }), "utf8").toString("base64url");
}

export function decodeOAuthState(state) {
  if (!state) return null;
  try {
    const parsed = JSON.parse(Buffer.from(state, "base64url").toString("utf8"));
    if (parsed?.redirect && typeof parsed.redirect === "string") {
      return parsed.redirect;
    }
  } catch {
    /* ignore */
  }
  return null;
}

export function oauthErrorRedirect(message, redirectBase) {
  const base = redirectBase || `${process.env.FRONTEND_URL}/auth/callback`;
  const url = new URL(base);
  url.searchParams.set("error", message);
  return url.toString();
}

export function oauthSuccessRedirect(user, token, redirectBase) {
  const base = redirectBase || `${process.env.FRONTEND_URL}/auth/callback`;
  const url = new URL(base);
  url.searchParams.set("token", token);
  url.searchParams.set("_id", String(user._id));
  url.searchParams.set("name", user.name);
  url.searchParams.set("email", user.email);
  return url.toString();
}
