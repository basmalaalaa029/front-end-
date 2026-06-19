import type { CvData } from "./cv-types";
import { cvDataFromProfileJson } from "./cv-profile-import";
import { createStarterCvData } from "./cv-templates";

/** Normalize legacy editor JSON or profile API payloads into `CvData`. */
export function migrateCvData(raw: unknown): CvData {
  if (!raw || typeof raw !== "object") return createStarterCvData();
  const o = raw as Record<string, unknown>;

  const legacyEducation = Array.isArray(o.education)
    ? (o.education as Record<string, unknown>[]).map((ed) => ({
        degree: String(ed.degree ?? ""),
        university: String(ed.university ?? ed.school ?? ""),
        startDate: String(ed.startDate ?? ""),
        endDate: String(ed.endDate ?? ""),
        gpa: String(ed.gpa ?? ""),
        dates: String(ed.dates ?? ""),
      }))
    : undefined;

  const legacyProjects = Array.isArray(o.projects)
    ? (o.projects as Record<string, unknown>[]).map((p) => ({
        title: String(p.title ?? p.name ?? ""),
        description: String(p.description ?? ""),
      }))
    : undefined;

  let certifications: string[] | undefined;
  if (Array.isArray(o.certifications)) {
    certifications = (o.certifications as unknown[]).map((c) => String(c));
  } else if (Array.isArray(o.awards)) {
    certifications = (o.awards as Record<string, unknown>[])
      .map((a) => String(a.title ?? "").trim())
      .filter(Boolean);
  }

  return cvDataFromProfileJson({
    name: String(o.name ?? ""),
    email: String(o.email ?? ""),
    phone: String(o.phone ?? ""),
    address: String(o.address ?? o.location ?? ""),
    summary: String(o.summary ?? ""),
    role: String(o.role ?? ""),
    url: String(o.url ?? ""),
    education: legacyEducation,
    skills: Array.isArray(o.skills) ? (o.skills as string[]) : [],
    experience: Array.isArray(o.experience) ? (o.experience as CvData["experience"]) : [],
    projects: legacyProjects,
    certifications,
  });
}
