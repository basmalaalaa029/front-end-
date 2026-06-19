/** Client-side CV metadata extraction (mirrors backend heuristics for .txt files). */

export type ExtractedCvContext = {
  targetRole: string;
  company: string;
  jobDescription: string;
};

const SUMMARY_ALIASES = [
  "professional summary",
  "summary",
  "profile",
  "about me",
  "objective",
  "career objective",
];

const SKILLS_ALIASES = ["skills", "technical skills", "core competencies", "expertise"];

const EXPERIENCE_ALIASES = ["experience", "work experience", "employment", "professional experience"];

function sectionBody(text: string, aliases: string[]): string {
  const lines = text.split(/\r?\n/);
  const capture: string[] = [];
  let inSection = false;

  for (const line of lines) {
    const stripped = line.trim();
    if (!stripped) continue;

    const lower = stripped.toLowerCase().replace(/[:\s]+$/, "");
    const isHeading =
      stripped.startsWith("#") ||
      aliases.some((a) => lower === a || lower.startsWith(`${a}:`));

    if (isHeading) {
      const heading = stripped.replace(/^#+\s*/, "").toLowerCase().replace(/[:\s]+$/, "");
      if (aliases.some((a) => heading === a || heading.startsWith(a))) {
        inSection = true;
        continue;
      }
      if (inSection) break;
      continue;
    }

    if (inSection) {
      capture.push(stripped);
    }
  }

  return capture.join("\n").trim();
}

function firstExperienceTitle(text: string): string {
  for (const line of text.split(/\r?\n/)) {
    const stripped = line.trim();
    if (stripped.startsWith("### ")) {
      const title = stripped.slice(4).trim();
      if (title && title.toLowerCase() !== "role") return title;
    }
  }
  return "";
}

function latestCompany(text: string): string {
  const lines = text.split(/\r?\n/);
  let inExp = false;

  for (let i = 0; i < lines.length; i++) {
    const stripped = lines[i].trim();
    if (stripped.startsWith("##")) {
      const lower = stripped.toLowerCase();
      inExp = EXPERIENCE_ALIASES.some((a) => lower.includes(a));
      continue;
    }
    if (!inExp || !stripped.startsWith("### ")) continue;

    for (let j = i + 1; j < Math.min(i + 4, lines.length); j++) {
      const follow = lines[j].trim();
      if (!follow || follow.startsWith("#")) break;
      const left = follow.split("|")[0];
      const parts = left.split("·").map((p) => p.trim()).filter(Boolean);
      if (parts[0] && !/^\d{4}/.test(parts[0])) return parts[0];
    }
  }
  return "";
}

export function extractCvContextFromText(text: string): ExtractedCvContext {
  const raw = text.trim();
  if (!raw) {
    return { targetRole: "Target role", company: "", jobDescription: "" };
  }

  const lines = raw.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  let targetRole = "";

  if (lines[0]?.startsWith("#")) {
    const second = lines[1] ?? "";
    if (second && !second.startsWith("#") && !second.includes("@")) {
      targetRole = second.split("·")[0].trim();
    }
  }

  if (!targetRole) targetRole = firstExperienceTitle(raw);

  const summary = sectionBody(raw, SUMMARY_ALIASES);
  const skills = sectionBody(raw, SKILLS_ALIASES);
  const jobDescription = [summary, skills].filter(Boolean).join("\n\n");

  return {
    targetRole: targetRole || "Target role",
    company: latestCompany(raw),
    jobDescription,
  };
}

export async function readCvFileAsText(file: File): Promise<string> {
  const name = file.name.toLowerCase();
  if (
    file.type === "text/plain" ||
    file.type === "text/markdown" ||
    name.endsWith(".txt") ||
    name.endsWith(".md")
  ) {
    return file.text();
  }
  return "";
}
