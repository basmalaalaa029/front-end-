import "../load_env.js";
import express from "express";
import cors from "cors";
import mongoose from "mongoose";
import passport from "passport";
import authRoutes from "./routes/auth.js";
import usersRoutes from "./routes/users.js";
import { configurePassport } from "./config/passport.js";

const PORT = Number(process.env.PORT) || 5000;
const MONGODB_URI =
  process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/careerpilot";

if (!process.env.JWT_SECRET) {
  console.warn("⚠️  JWT_SECRET is not set — using insecure dev default");
  process.env.JWT_SECRET = "dev-only-change-in-production";
}

const app = express();

app.use(
  cors({
    origin: [
      process.env.FRONTEND_URL || "http://localhost:5173",
      "http://127.0.0.1:5173",
    ],
    credentials: true,
  })
);
app.use(express.json());
app.use(passport.initialize());

configurePassport();

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, service: "careerpilot-auth-api" });
});

app.use("/api/auth", authRoutes);
app.use("/api/users", usersRoutes);

async function start() {
  try {
    await mongoose.connect(MONGODB_URI);
    console.log("✅ MongoDB connected");
  } catch (err) {
    console.error("❌ MongoDB connection failed:", err.message);
    console.error(
      "   Start MongoDB (docker compose up -d mongo) or set MONGODB_URI in backend/.env"
    );
    process.exit(1);
  }

  app.listen(PORT, () => {
    console.log(`✅ Auth API listening on http://localhost:${PORT}`);
    console.log(`   Health: http://localhost:${PORT}/api/health`);
  });
}

start();
