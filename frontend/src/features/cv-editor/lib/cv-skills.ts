import type { CvData } from "@/features/cv-editor/data/cv-types";

const TECH_CATEGORY_KEYS = [
  "technical",
  "backend",
  "frontend",
  "databases",
  "tools",
  "cloud",
] as const;

function skillKey(skill: string): string {
  return skill.trim().toLowerCase();
}

/** Prefer a technical bucket when appending user-added skills. */
export function pickSkillCategory(categories: Record<string, string[]>): string {
  for (const key of TECH_CATEGORY_KEYS) {
    if (categories[key]?.length) return key;
  }
  const nonSoft = Object.keys(categories).find((k) => k !== "soft_skills");
  return nonSoft ?? "technical";
}

/** Skills listed flat but missing from categorized buckets (e.g. user-added). */
export function uncategorizedSkills(data: CvData): string[] {
  const categorized = new Set(
    Object.values(data.skillsByCategory ?? {})
      .flat()
      .map(skillKey),
  );
  return data.skills
    .map((s) => s.trim())
    .filter((s) => s && !categorized.has(skillKey(s)));
}

/** Merge flat-only skills into categorized view for consistent CV rendering. */
export function skillsByCategoryForDisplay(
  data: CvData,
): Record<string, string[]> | undefined {
  const base = data.skillsByCategory;
  if (!base || !Object.keys(base).length) return undefined;

  const merged = { ...base };
  const extra = uncategorizedSkills(data);
  if (!extra.length) return merged;

  const target = pickSkillCategory(merged);
  const existing = new Set((merged[target] ?? []).map(skillKey));
  const toAdd = extra.filter((s) => !existing.has(skillKey(s)));
  if (!toAdd.length) return merged;

  merged[target] = [...(merged[target] ?? []), ...toAdd];
  return merged;
}

export function addSkillToCvData(data: CvData, raw: string): CvData {
  const trimmed = raw.trim();
  if (!trimmed) return data;
  if (data.skills.some((s) => skillKey(s) === skillKey(trimmed))) return data;

  const skills = [...data.skills, trimmed];
  if (!data.skillsByCategory || !Object.keys(data.skillsByCategory).length) {
    return { ...data, skills };
  }

  const categoryKey = pickSkillCategory(data.skillsByCategory);
  return {
    ...data,
    skills,
    skillsByCategory: {
      ...data.skillsByCategory,
      [categoryKey]: [...(data.skillsByCategory[categoryKey] ?? []), trimmed],
    },
  };
}

export function removeSkillFromCvData(data: CvData, index: number): CvData {
  const removed = data.skills[index];
  if (!removed) return data;

  const skills = data.skills.filter((_, i) => i !== index);
  let skillsByCategory = data.skillsByCategory;
  if (skillsByCategory) {
    const needle = skillKey(removed);
    const next: Record<string, string[]> = {};
    for (const [key, items] of Object.entries(skillsByCategory)) {
      const filtered = items.filter((s) => skillKey(s) !== needle);
      if (filtered.length) next[key] = filtered;
    }
    skillsByCategory = Object.keys(next).length ? next : undefined;
  }
  return { ...data, skills, skillsByCategory };
}
