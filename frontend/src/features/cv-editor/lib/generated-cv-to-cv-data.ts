import type { CvData } from "@/features/cv-editor/data/cv-types";
import type { GeneratedCv, WizardStep1Data } from "@/features/cv-editor/components/cv-wizard/types";

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

/** Prefer wizard facts when the model omits or blanks a field. */
export function mergeWizardWithGeneratedCv(
  wizard: WizardStep1Data,
  cv: GeneratedCv,
): CvData {
  const mapped = generatedCvToCvData(
    { ...cv, target_title: cv.target_title || wizard.target_job },
    wizard.target_job,
  );

  const wizardEducation = wizard.education
    .filter((e) => e.degree.trim() || e.university.trim())
    .map((e) => ({
      degree: e.degree.trim(),
      university: e.university.trim(),
      startDate: "",
      endDate: e.year.trim(),
      gpa: e.gpa.trim(),
    }));

  const wizardExperience = wizard.has_experience
    ? wizard.experience
        .filter((e) => e.job_title.trim() || e.company.trim())
        .map((e) => ({
          title: e.job_title.trim(),
          company: e.company.trim(),
          location: "",
          dates: [e.start_date.trim(), e.end_date.trim()].filter(Boolean).join(" — "),
          bullets: e.description.trim()
            ? e.description
                .split("\n")
                .map((ln) => ln.trim())
                .filter(Boolean)
            : [],
        }))
    : [];

  const wizardProjects = wizard.projects
    .filter((p) => p.name.trim() || p.description.trim())
    .map((p) => ({
      title: p.name.trim(),
      description: p.description.trim(),
      bullets: undefined as string[] | undefined,
    }));

  const wizardCerts = wizard.certifications.map((c) => c.trim()).filter(Boolean);
  const linkedin = wizard.linkedin.trim();
  const github = wizard.github.trim();

  return {
    ...mapped,
    name: mapped.name || wizard.full_name.trim(),
    role: mapped.role || wizard.target_job.trim(),
    email: mapped.email || wizard.email.trim(),
    phone: mapped.phone || wizard.phone.trim(),
    address: mapped.address || wizard.location.trim(),
    url: mapped.url || linkedin || github,
    education: mapped.education.length ? mapped.education : wizardEducation,
    experience: mapped.experience.length ? mapped.experience : wizardExperience,
    projects: mapped.projects.length ? mapped.projects : wizardProjects,
    certifications: mapped.certifications.length
      ? [...new Set([...wizardCerts, ...mapped.certifications])]
      : wizardCerts,
  };
}
