import type { TemplateId } from "./cv-templates";

export const TEMPLATE_FILTER_IDS = [
  "all",
  "ats",
  "simple",
  "professional",
  "two-column",
] as const;

export type TemplateFilterId = (typeof TEMPLATE_FILTER_IDS)[number];

export type TemplateMeta = {
  categories: TemplateFilterId[];
  /** Short label on the card (e.g. serif, sidebar). */
  styleLabel: string;
};

export const TEMPLATE_META: Record<TemplateId, TemplateMeta> = {
  modern: {
    categories: ["all", "ats", "professional", "simple"],
    styleLabel: "Professional",
  },
  executive: {
    categories: ["all", "professional", "two-column"],
    styleLabel: "Executive",
  },
  tech: {
    categories: ["all", "ats", "professional"],
    styleLabel: "Tech",
  },
  minimal: {
    categories: ["all", "simple", "ats"],
    styleLabel: "Minimal",
  },
};

export function templateMatchesFilter(id: TemplateId, filter: TemplateFilterId): boolean {
  if (filter === "all") return true;
  return TEMPLATE_META[id].categories.includes(filter);
}
