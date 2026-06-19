import type { CvData, CvProfileJson } from "./cv-types";

/** Map API / JSON profile shape into editor `CvData`. */
export function cvDataFromProfileJson(raw: CvProfileJson): CvData {
  return {
    name: raw.name?.trim() ?? "",
    email: raw.email?.trim() ?? "",
    phone: raw.phone?.trim() ?? "",
    address: raw.address?.trim() ?? "",
    role: raw.role?.trim() ?? "",
    url: raw.url?.trim() ?? "",
    summary: raw.summary?.trim() ?? "",
    education: (raw.education ?? []).map((ed) => ({
      degree: ed.degree?.trim() ?? "",
      university: (ed.university ?? ed.school ?? "").trim(),
      startDate: ed.startDate?.trim() ?? "",
      endDate: ed.endDate?.trim() ?? "",
      gpa: ed.gpa?.trim() ?? "",
    })),
    skills: (raw.skills ?? []).map((s) => s.trim()).filter(Boolean),
    experience: raw.experience ?? [],
    projects: (raw.projects ?? []).map((p) => ({
      title: (p.title ?? p.name ?? "").trim(),
      description: p.description?.trim() ?? "",
    })),
    certifications: (raw.certifications ?? []).map((c) => c.trim()).filter(Boolean),
  };
}
