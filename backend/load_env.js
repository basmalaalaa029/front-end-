/** Load backend/.env once (shared entry point for dotenv). */
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config } from "dotenv";

const ROOT = dirname(fileURLToPath(import.meta.url));
export const ENV_PATH = join(ROOT, ".env");

let loaded = false;

export function loadEnv({ override = false } = {}) {
  if (loaded && !override) return ENV_PATH;
  if (existsSync(ENV_PATH)) {
    config({ path: ENV_PATH, override });
    loaded = true;
  }
  return ENV_PATH;
}

loadEnv();
