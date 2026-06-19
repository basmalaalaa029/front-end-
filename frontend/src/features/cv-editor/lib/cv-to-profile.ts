/**
 * cv-to-profile.ts
 * ----------------
 * Translates the editor's `CvData` shape into the structured request payload
 * for the CV Agent FastAPI service (Gemini enhancement).
 */

import type { CvData, CvExperience, CvEducation, CvProject } from "@/features/cv-editor/data/cv-types";
import type {
  CvAgentEducation,
  CvAgentExperience,
  CvAgentGenerateRequest,
  CvAgentProject,
} from "./cv-agent-api";

const trim = (v: string): string => v.trim();

function splitDates(dates: string): { start_date: string; end_date: string } {
  const raw = trim(dates);
  if (!raw) return { start_date: "", end_date: "" };
  const parts = raw.split(/\s*[—–-]\s*|\s+to\s+/i);
  return {
    start_date: parts[0]?.trim() ?? "",
    end_date: parts[1]?.trim() ?? "",
  };
}

function mapExperience(e: CvExperience): CvAgentExperience {
  const { start_date, end_date } = splitDates(e.dates);
  return {
    job_title: trim(e.title),
    company: trim(e.company),
    location: trim(e.location),
    start_date,
    end_date,
    bullets: e.bullets.map(trim).filter(Boolean),
  };
}

function mapProject(p: CvProject): CvAgentProject {
  return {
    name: trim(p.title),
    tech_used: "",
    description: trim(p.description),
  };
}

function mapEducation(e: CvEducation): CvAgentEducation {
  const year = [trim(e.startDate), trim(e.endDate)].filter(Boolean).join(" — ");
  return {
    degree: trim(e.degree),
    university: trim(e.university),
    year,
    gpa: trim(e.gpa) || undefined,
  };
}

function resolveTargetRole(data: CvData): string {
  if (trim(data.role)) return trim(data.role);
  const summary = trim(data.summary);
  if (summary) return summary.length > 80 ? `${summary.slice(0, 77)}…` : summary;
  const degree = data.education.map((e) => trim(e.degree)).find(Boolean);
  return degree || "Graduate";
}

function resolveLinks(url: string): { linkedin: string; github: string } {
  const u = trim(url);
  if (!u) return { linkedin: "", github: "" };
  if (u.toLowerCase().includes("github")) return { linkedin: "", github: u };
  return { linkedin: u, github: "" };
}

export interface BuildPayloadOptions {
  jobDescription?: string;
  parsedResume?: string;
  tone?: CvAgentGenerateRequest["tone"];
}

export interface BuildPayloadResult {
  payload: CvAgentGenerateRequest;
  missing: string[];
}

const REQUIRED_LABELS: Record<string, string> = {
  name: "Full name",
  skills: "At least one skill",
  experienceOrProjects: "At least one role or project",
};

export function buildGeneratePayload(
  data: CvData,
  opts: BuildPayloadOptions = {},
): BuildPayloadResult {
  const skills = data.skills.map(trim).filter(Boolean);
  const experience = data.experience.map(mapExperience).filter(
    (e) => e.job_title || e.company || e.bullets.length > 0,
  );
  const projects = data.projects.map(mapProject).filter(
    (p) => p.name || p.description,
  );
  const education_structured = data.education.map(mapEducation).filter(
    (e) => e.university || e.degree,
  );
  const certifications = data.certifications.map(trim).filter(Boolean);
  const links = resolveLinks(data.url);

  const missing: string[] = [];
  if (!trim(data.name)) missing.push(REQUIRED_LABELS.name);
  if (skills.length === 0) missing.push(REQUIRED_LABELS.skills);
  if (experience.length === 0 && projects.length === 0) {
    missing.push(REQUIRED_LABELS.experienceOrProjects);
  }

  const parsedChunks = [
    opts.parsedResume?.trim() ?? "",
    trim(data.address) ? `Address: ${trim(data.address)}` : "",
    trim(data.phone) ? `Phone: ${trim(data.phone)}` : "",
  ].filter(Boolean);

  const payload: CvAgentGenerateRequest = {
    full_name: trim(data.name),
    target_role: resolveTargetRole(data),
    summary: trim(data.summary),
    email: trim(data.email),
    phone: trim(data.phone),
    linkedin: links.linkedin,
    github: links.github,
    location: trim(data.address),
    experience,
    projects,
    education_structured,
    skills,
    certifications,
    tone: opts.tone ?? "professional",
    job_description: opts.jobDescription?.trim() ?? "",
    parsed_resume: parsedChunks.join("\n").trim(),
  };

  return { payload, missing };
}

export function cvDataToMarkdown(data: CvData): string {
  const t = trim;
  const lines: string[] = [];

  lines.push(`# ${t(data.name) || "Your Name"}`);
  if (t(data.role)) lines.push(t(data.role));

  const contact = [data.email, data.phone, data.address, data.url]
    .map(t)
    .filter(Boolean)
    .join(" · ");
  if (contact) lines.push(contact);

  if (t(data.summary)) {
    lines.push("", "## Professional Summary", t(data.summary));
  }

  const hasEdu = data.education.some(
    (e: CvEducation) => t(e.university) || t(e.degree),
  );
  if (hasEdu) {
    lines.push("", "## Education");
    data.education.forEach((e: CvEducation) => {
      if (!t(e.university) && !t(e.degree)) return;
      const dates = [t(e.startDate), t(e.endDate)].filter(Boolean).join(" — ");
      const gpa = t(e.gpa) ? `GPA ${t(e.gpa)}` : "";
      lines.push(``, `### ${t(e.university) || t(e.degree)}`);
      const sub = [t(e.degree), dates, gpa].filter(Boolean).join(" | ");
      if (sub) lines.push(sub);
    });
  }

  const skills = data.skills.map(t).filter(Boolean);
  if (skills.length) {
    lines.push("", "## Skills");
    lines.push(skills.join(", "));
  }

  const hasExp = data.experience.some(
    (e: CvExperience) => t(e.title) || t(e.company) || e.bullets.some((b) => t(b)),
  );
  if (hasExp) {
    lines.push("", "## Experience");
    data.experience.forEach((e: CvExperience) => {
      if (!t(e.title) && !t(e.company)) return;
      const sub = [t(e.company), t(e.location)].filter(Boolean).join(" · ");
      const dates = t(e.dates);
      lines.push(``, `### ${t(e.title) || "Role"}`);
      if (sub || dates) lines.push([sub, dates].filter(Boolean).join(" | "));
      e.bullets.filter((b) => t(b)).forEach((b) => lines.push(`- ${t(b)}`));
    });
  }

  if (data.projects.length) {
    lines.push("", "## Projects");
    data.projects.forEach((p: CvProject) => {
      if (!t(p.title)) return;
      lines.push(``, `### ${t(p.title)}`);
      if (t(p.description)) lines.push(t(p.description));
    });
  }

  const certs = data.certifications.map(t).filter(Boolean);
  if (certs.length) {
    lines.push("", "## Certifications");
    certs.forEach((c) => lines.push(`- ${c}`));
  }

  return lines.join("\n");
}

const SKILL_CATEGORY_LABELS: Record<string, string> = {
  frontend: "Frontend",
  backend: "Backend",
  databases: "Databases",
  tools: "Tools",
  cloud: "Cloud",
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => trim(String(item))).filter(Boolean);
}

function flattenSkillsField(skills: unknown): string[] {
  if (Array.isArray(skills)) return asStringArray(skills);
  const dict = asRecord(skills);
  if (!dict) return [];
  const out: string[] = [];
  for (const key of Object.keys(SKILL_CATEGORY_LABELS)) {
    for (const item of asStringArray(dict[key])) {
      if (!out.includes(item)) out.push(item);
    }
  }
  return out;
}

function categorizeSkillsField(skills: unknown): Record<string, string[]> | undefined {
  const dict = asRecord(skills);
  if (!dict) return undefined;
  const out: Record<string, string[]> = {};
  for (const key of Object.keys(SKILL_CATEGORY_LABELS)) {
    const items = asStringArray(dict[key]);
    if (items.length) out[key] = items;
  }
  return Object.keys(out).length ? out : undefined;
}

function experienceIdentityKey(exp: {
  job_title?: string;
  company?: string;
  start_date?: string;
  end_date?: string;
}): string {
  return [
    trim(exp.job_title ?? ""),
    trim(exp.company ?? ""),
    trim(exp.start_date ?? ""),
    trim(exp.end_date ?? ""),
  ].join("|").toLowerCase();
}

function draftExperienceKey(exp: CvExperience): string {
  const { start_date, end_date } = splitDates(exp.dates);
  return experienceIdentityKey({
    job_title: exp.title,
    company: exp.company,
    start_date,
    end_date,
  });
}

function projectIdentityKey(proj: { name?: string; tech_used?: string }): string {
  return [trim(proj.name ?? ""), trim(proj.tech_used ?? "")].join("|").toLowerCase();
}

/** Map API enhanced_data JSON into editor CvData for template rendering. */
export function enhancedDataToCvData(
  enhanced: Record<string, unknown>,
  draft: CvData,
): CvData {
  const summary =
    trim(String(enhanced.summary ?? enhanced.professional_summary ?? "")) ||
    draft.summary;

  const skillsByCategory =
    categorizeSkillsField(enhanced.skills_by_category) ??
    categorizeSkillsField(enhanced.skills) ??
    draft.skillsByCategory;
  const skills = flattenSkillsField(enhanced.skills).length
    ? flattenSkillsField(enhanced.skills)
    : draft.skills;

  const enhExpList = Array.isArray(enhanced.experience) ? enhanced.experience : [];
  const enhExpByKey = new Map<string, Record<string, unknown>>();
  enhExpList.forEach((item, index) => {
    const rec = asRecord(item);
    if (!rec) return;
    enhExpByKey.set(experienceIdentityKey(rec), rec);
    if (!enhExpByKey.has(`__index__${index}`)) {
      enhExpByKey.set(`__index__${index}`, rec);
    }
  });

  const experience = draft.experience.map((exp, index) => {
    const match =
      enhExpByKey.get(draftExperienceKey(exp)) ??
      enhExpByKey.get(`__index__${index}`);
    const bullets = match ? asStringArray(match.bullets) : [];
    return {
      ...exp,
      bullets: bullets.length ? bullets : exp.bullets,
    };
  });

  const enhProjList = Array.isArray(enhanced.projects) ? enhanced.projects : [];
  const enhProjByKey = new Map<string, Record<string, unknown>>();
  enhProjList.forEach((item, index) => {
    const rec = asRecord(item);
    if (!rec) return;
    enhProjByKey.set(projectIdentityKey(rec), rec);
    enhProjByKey.set(`__index__${index}`, rec);
  });

  const projects = draft.projects.map((proj, index) => {
    const match =
      enhProjByKey.get(projectIdentityKey({ name: proj.title })) ??
      enhProjByKey.get(`__index__${index}`);
    if (!match) return { ...proj };
    const bullets = asStringArray(match.bullets);
    const description = trim(String(match.description ?? ""));
    if (bullets.length) {
      return { ...proj, bullets, description: "" };
    }
    if (description) {
      return { ...proj, description, bullets: undefined };
    }
    return { ...proj };
  });

  return {
    ...draft,
    summary,
    skills,
    skillsByCategory,
    experience,
    projects,
  };
}
