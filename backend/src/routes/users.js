import { Router } from "express";
import { requireAuth } from "../middleware/auth.js";
import {
  normalizeWizardProfile,
  wizardProfileHasContent,
} from "../utils/wizard-profile.js";

const router = Router();

router.get("/profile", requireAuth, (req, res) => {
  return res.json(req.user.toProfile());
});

router.put("/profile", requireAuth, async (req, res) => {
  try {
    const allowed = [
      "name",
      "phone",
      "location",
      "bio",
      "jobTitle",
      "avatarUrl",
      "skills",
      "linkedIn",
      "portfolio",
    ];

    for (const key of allowed) {
      if (req.body[key] !== undefined) {
        req.user[key] = req.body[key];
      }
    }

    if (typeof req.user.name === "string") req.user.name = req.user.name.trim();
    await req.user.save();
    return res.json(req.user.toProfile());
  } catch (err) {
    console.error("Profile update error:", err);
    return res.status(500).json({ message: "Failed to update profile" });
  }
});

router.get("/wizard-profile", requireAuth, (req, res) => {
  const profile = req.user.wizardProfile;
  if (!wizardProfileHasContent(profile)) {
    return res.json({ profile: null });
  }
  return res.json({ profile });
});

router.put("/wizard-profile", requireAuth, async (req, res) => {
  try {
    const profile = normalizeWizardProfile(req.body);
    if (!profile) {
      return res.status(422).json({ message: "Invalid wizard profile payload" });
    }

    req.user.wizardProfile = profile;
    await req.user.save();
    return res.json({ profile: req.user.wizardProfile });
  } catch (err) {
    console.error("Wizard profile update error:", err);
    return res.status(500).json({ message: "Failed to save wizard profile" });
  }
});

export default router;
