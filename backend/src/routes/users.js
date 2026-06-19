import { Router } from "express";
import { requireAuth } from "../middleware/auth.js";

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

export default router;
