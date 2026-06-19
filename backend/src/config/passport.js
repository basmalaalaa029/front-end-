import passport from "passport";
import { Strategy as GoogleStrategy } from "passport-google-oauth20";
import { Strategy as LinkedInStrategy } from "passport-linkedin-oauth2";
import { User } from "../models/User.js";

passport.serializeUser((user, done) => done(null, user.id));
passport.deserializeUser(async (id, done) => {
  try {
    const user = await User.findById(id);
    done(null, user);
  } catch (err) {
    done(err);
  }
});

async function findOrCreateOAuthUser({ provider, providerId, email, name }) {
  const idField = provider === "google" ? "googleId" : "linkedinId";
  let user = await User.findOne({ [idField]: providerId });
  if (user) return user;

  if (email) {
    user = await User.findOne({ email: email.toLowerCase() });
    if (user) {
      user[idField] = providerId;
      if (!user.name && name) user.name = name;
      await user.save();
      return user;
    }
  }

  user = await User.create({
    name: name || email?.split("@")[0] || "User",
    email: (email || `${providerId}@${provider}.oauth`).toLowerCase(),
    [idField]: providerId,
    password: null,
  });
  return user;
}

export function configurePassport() {
  const googleId = process.env.GOOGLE_CLIENT_ID;
  const googleSecret = process.env.GOOGLE_CLIENT_SECRET;
  if (googleId && googleSecret) {
    passport.use(
      new GoogleStrategy(
        {
          clientID: googleId,
          clientSecret: googleSecret,
          callbackURL:
            process.env.GOOGLE_CALLBACK_URL ||
            "http://localhost:5000/api/auth/google/callback",
        },
        async (_accessToken, _refreshToken, profile, done) => {
          try {
            const email = profile.emails?.[0]?.value;
            const user = await findOrCreateOAuthUser({
              provider: "google",
              providerId: profile.id,
              email,
              name: profile.displayName,
            });
            done(null, user);
          } catch (err) {
            done(err);
          }
        }
      )
    );
  }

  const linkedInId = process.env.LINKEDIN_CLIENT_ID;
  const linkedInSecret = process.env.LINKEDIN_CLIENT_SECRET;
  if (linkedInId && linkedInSecret) {
    passport.use(
      new LinkedInStrategy(
        {
          clientID: linkedInId,
          clientSecret: linkedInSecret,
          callbackURL:
            process.env.LINKEDIN_CALLBACK_URL ||
            "http://localhost:5000/api/auth/linkedin/callback",
          scope: ["r_emailaddress", "r_liteprofile"],
        },
        async (_accessToken, _refreshToken, profile, done) => {
          try {
            const email = profile.emails?.[0]?.value;
            const user = await findOrCreateOAuthUser({
              provider: "linkedin",
              providerId: profile.id,
              email,
              name: profile.displayName,
            });
            done(null, user);
          } catch (err) {
            done(err);
          }
        }
      )
    );
  }
}

export function isGoogleEnabled() {
  return Boolean(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET);
}

export function isLinkedInEnabled() {
  return Boolean(process.env.LINKEDIN_CLIENT_ID && process.env.LINKEDIN_CLIENT_SECRET);
}
