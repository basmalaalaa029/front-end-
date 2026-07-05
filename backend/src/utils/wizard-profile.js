function trim(value) {
  return typeof value === "string" ? value.trim() : "";
}

function cleanStringArray(items) {
  if (!Array.isArray(items)) return [];
  return items.map((item) => trim(String(item ?? ""))).filter(Boolean);
}

function cleanEducation(items) {
  if (!Array.isArray(items)) {
    return [{ degree: "", university: "", year: "", gpa: "" }];
  }
  const cleaned = items.map((item) => ({
    degree: trim(item?.degree),
    university: trim(item?.university),
    year: trim(item?.year),
    gpa: trim(item?.gpa),
  }));
  return cleaned.length ? cleaned : [{ degree: "", university: "", year: "", gpa: "" }];
}

function cleanExperience(items) {
  if (!Array.isArray(items)) return [];
  return items.map((item) => ({
    job_title: trim(item?.job_title),
    company: trim(item?.company),
    start_date: trim(item?.start_date),
    end_date: trim(item?.end_date),
    description: trim(item?.description),
  }));
}

function cleanProjects(items) {
  if (!Array.isArray(items)) return [];
  return items.map((item) => ({
    name: trim(item?.name),
    tech_used: trim(item?.tech_used),
    description: trim(item?.description),
  }));
}

export function normalizeWizardProfile(body) {
  if (!body || typeof body !== "object") return null;

  const hasExperience = body.has_experience !== false;
  const experience = hasExperience ? cleanExperience(body.experience) : [];

  return {
    full_name: trim(body.full_name),
    target_job: trim(body.target_job),
    email: trim(body.email),
    phone: trim(body.phone),
    location: trim(body.location),
    linkedin: trim(body.linkedin),
    github: trim(body.github),
    education: cleanEducation(body.education),
    experience,
    has_experience: hasExperience,
    projects: cleanProjects(body.projects),
    certifications: cleanStringArray(body.certifications),
  };
}

export function wizardProfileHasContent(profile) {
  if (!profile) return false;
  return Boolean(
    profile.full_name ||
      profile.target_job ||
      profile.email ||
      profile.phone ||
      profile.location ||
      profile.linkedin ||
      profile.github ||
      profile.education?.some((e) => e.degree || e.university || e.year || e.gpa) ||
      profile.experience?.some(
        (e) => e.job_title || e.company || e.start_date || e.end_date || e.description,
      ) ||
      profile.projects?.some((p) => p.name || p.tech_used || p.description) ||
      profile.certifications?.length,
  );
}
