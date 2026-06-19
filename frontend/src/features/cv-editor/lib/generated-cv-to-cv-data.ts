import type { CvData } from "@/features/cv-editor/data/cv-types";
import type { GeneratedCv } from "@/features/cv-editor/components/cv-wizard/types";

const trim = (v: string | undefined): string => (v ?? "").trim();

function flattenSkills(skills: GeneratedCv["skills"]): string[] {
  if (!skills) return [];
  if (Array.isArray(skills)) {
    return skills.map((s) => trim(String(s))).filter(Boolean);
  }
  const out: string[] = [];
  for (const items of Object.values(skills)) {
    if (!Array.isArray(items)) continue;
    for (const item of items) {
      const label = trim(String(item));
      if (label && !out.includes(label)) out.push(label);
    }
  }
  return out;
}

function categorizeSkills(
  skills: GeneratedCv["skills"],
): Record<string, string[]> | undefined {
  if (!skills || Array.isArray(skills)) return undefined;
  const out: Record<string, string[]> = {};
  for (const [key, items] of Object.entries(skills)) {
    if (!Array.isArray(items)) continue;
    const cleaned = items.map((i) => trim(String(i))).filter(Boolean);
    if (cleaned.length) out[key] = cleaned;
  }
  return Object.keys(out).length ? out : undefined;
}

function resolveUrl(pi: GeneratedCv["personal_info"]): string {
  const linkedin = trim(pi.linkedin);
  const github = trim(pi.github);
  const portfolio = trim(pi.portfolio);
  return linkedin || github || portfolio;
}

/** Map Gemini wizard CV JSON into editor CvData. */
export function generatedCvToCvData(cv: GeneratedCv, targetJob: string): CvData {
  const pi = cv.personal_info ?? {};
  const skills = flattenSkills(cv.skills);
  const skillsByCategory = categorizeSkills(cv.skills);

  return {
    name: trim(pi.full_name),
    role: trim(cv.target_title) || trim(targetJob),
    email: trim(pi.email),
    phone: trim(pi.phone),
    address: trim(pi.location),
    url: resolveUrl(pi),
    summary: trim(cv.summary),
    skills,
    skillsByCategory,
    education: (cv.education ?? []).map((e) => ({
      degree: trim(e.degree),
      university: trim(e.university),
      startDate: "",
      endDate: trim(e.year),
      gpa: trim(e.gpa),
    })),
    experience: (cv.experience ?? []).map((e) => ({
      title: trim(e.job_title),
      company: trim(e.company),
      location: "",
      dates: [trim(e.start_date), trim(e.end_date)].filter(Boolean).join(" — "),
      bullets: (e.bullets ?? []).map((b) => trim(b)).filter(Boolean),
    })),
    projects: (cv.projects ?? []).map((p) => {
      const bullets = (p.bullets ?? []).map((b) => trim(b)).filter(Boolean);
      return {
        title: trim(p.name),
        description: bullets.length ? "" : trim(p.description),
        bullets: bullets.length ? bullets : undefined,
      };
    }),
    certifications: (cv.certifications ?? []).map((c) => trim(String(c))).filter(Boolean),
  };
}
