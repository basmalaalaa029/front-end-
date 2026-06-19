import { Router } from "express";
import bcrypt from "bcryptjs";
import passport from "passport";
import { User } from "../models/User.js";
import { signToken } from "../middleware/auth.js";
import {
  decodeOAuthState,
  encodeOAuthState,
  oauthErrorRedirect,
  oauthSuccessRedirect,
} from "../utils/redirect.js";
import { isGoogleEnabled, isLinkedInEnabled } from "../config/passport.js";

const router = Router();

function ok(res, payload) {
  return res.json({ data: payload });
}

function fail(res, status, message) {
  return res.status(status).json({ data: { message }, message });
}

router.post("/register", async (req, res) => {
  try {
    const { name, email, password } = req.body || {};
    if (!name?.trim() || !email?.trim() || !password) {
      return fail(res, 400, "Name, email, and password are required");
    }
    if (password.length < 6) {
      return fail(res, 400, "Password must be at least 6 characters");
    }

    const exists = await User.findOne({ email: email.toLowerCase().trim() });
    if (exists) {
      return fail(res, 400, "An account with this email already exists");
    }

    const hash = await bcrypt.hash(password, 10);
    const user = await User.create({
      name: name.trim(),
      email: email.toLowerCase().trim(),
      password: hash,
    });

    const token = signToken(user._id);
    return ok(res, user.toAuthPayload(token));
  } catch (err) {
    console.error("Register error:", err);
    return fail(res, 500, "Registration failed");
  }
});

router.post("/login", async (req, res) => {
  try {
    const { email, password } = req.body || {};
    if (!email?.trim() || !password) {
      return fail(res, 400, "Email and password are required");
    }

    const user = await User.findOne({ email: email.toLowerCase().trim() });
    if (!user || !user.password) {
      return fail(res, 401, "Invalid email or password");
    }

    const match = await bcrypt.compare(password, user.password);
    if (!match) {
      return fail(res, 401, "Invalid email or password");
    }

    const token = signToken(user._id);
    return ok(res, user.toAuthPayload(token));
  } catch (err) {
    console.error("Login error:", err);
    return fail(res, 500, "Login failed");
  }
});

function getFrontendRedirect(req) {
  const fromQuery = req.query.redirect;
  if (typeof fromQuery === "string" && fromQuery.startsWith("http")) {
    return fromQuery;
  }
  return `${process.env.FRONTEND_URL || "http://localhost:5173"}/auth/callback`;
}

router.get("/google", (req, res, next) => {
  if (!isGoogleEnabled()) {
    return res.redirect(
      oauthErrorRedirect(
        "Google sign-in is not configured on the server",
        getFrontendRedirect(req)
      )
    );
  }

  const redirect = getFrontendRedirect(req);
  const state = encodeOAuthState(redirect);
  return passport.authenticate("google", {
    scope: ["profile", "email"],
    state,
    session: false,
  })(req, res, next);
});

router.get(
  "/google/callback",
  (req, res, next) => {
    if (!isGoogleEnabled()) {
      return res.redirect(oauthErrorRedirect("Google sign-in is not configured"));
    }
    passport.authenticate("google", { session: false, failureRedirect: undefined })(
      req,
      res,
      (err) => {
        if (err || !req.user) {
          const redirect = decodeOAuthState(req.query.state) || getFrontendRedirect(req);
          return res.redirect(oauthErrorRedirect("Google sign-in failed", redirect));
        }
        next();
      }
    );
  },
  (req, res) => {
    const redirect = decodeOAuthState(req.query.state) || getFrontendRedirect(req);
    const token = signToken(req.user._id);
    return res.redirect(oauthSuccessRedirect(req.user, token, redirect));
  }
);

router.get("/linkedin", (req, res, next) => {
  if (!isLinkedInEnabled()) {
    return res.redirect(
      oauthErrorRedirect(
        "LinkedIn sign-in is not configured on the server",
        getFrontendRedirect(req)
      )
    );
  }

  const redirect = getFrontendRedirect(req);
  const state = encodeOAuthState(redirect);
  return passport.authenticate("linkedin", { state, session: false })(req, res, next);
});

router.get(
  "/linkedin/callback",
  (req, res, next) => {
    if (!isLinkedInEnabled()) {
      return res.redirect(oauthErrorRedirect("LinkedIn sign-in is not configured"));
    }
    passport.authenticate("linkedin", { session: false, failureRedirect: undefined })(
      req,
      res,
      (err) => {
        if (err || !req.user) {
          const redirect = decodeOAuthState(req.query.state) || getFrontendRedirect(req);
          return res.redirect(oauthErrorRedirect("LinkedIn sign-in failed", redirect));
        }
        next();
      }
    );
  },
  (req, res) => {
    const redirect = decodeOAuthState(req.query.state) || getFrontendRedirect(req);
    const token = signToken(req.user._id);
    return res.redirect(oauthSuccessRedirect(req.user, token, redirect));
  }
);

export default router;
