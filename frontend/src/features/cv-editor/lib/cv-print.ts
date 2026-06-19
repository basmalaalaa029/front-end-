/**
 * cv-print.ts
 * -----------
 * Renders the user's CvData as styled HTML for each template and triggers
 * the browser's native print dialog (print-to-PDF).
 *
 * No backend required — 100% client-side, pixel-perfect per template.
 */

import type { CvData, CvExperience, CvEducation, CvProject } from "@/features/cv-editor/data/cv-types";
import type { TemplateId } from "@/features/cv-editor/data/cv-templates";

// ─── HTML escape ──────────────────────────────────────────────────────────────

function e(s: string): string {
  return (s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─── Template CSS themes ──────────────────────────────────────────────────────

const THEME_MODERN = `
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size:11pt; color:#1a1a1a; background:#fff; padding:0; }
  .cv { max-width:720px; margin:0 auto; padding:48px 52px; }
  .cv-header { border-left:5px solid #2d6a4f; padding-left:16px; margin-bottom:22px; }
  .cv-name { font-size:22pt; font-weight:700; color:#1a1a1a; letter-spacing:-0.5px; }
  .cv-role { font-size:12pt; color:#2d6a4f; font-weight:500; margin-top:2px; }
  .cv-contact { font-size:9pt; color:#555; margin-top:6px; display:flex; flex-wrap:wrap; gap:14px; }
  .cv-contact span::before { content:""; }
  .section { margin-top:20px; }
  .section-title { font-size:9pt; font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#2d6a4f; border-bottom:1px solid #2d6a4f; padding-bottom:3px; margin-bottom:10px; }
  .entry { margin-bottom:10px; }
  .entry-head { display:flex; justify-content:space-between; align-items:baseline; }
  .entry-title { font-weight:600; font-size:11pt; }
  .entry-meta { font-size:9pt; color:#666; white-space:nowrap; margin-left:8px; }
  .entry-sub { font-size:9.5pt; color:#555; margin-top:1px; }
  ul { margin-top:4px; padding-left:16px; }
  li { margin-bottom:2px; font-size:10.5pt; line-height:1.5; }
  .summary p { font-size:10.5pt; line-height:1.6; color:#333; }
  .skills-list { display:flex; flex-wrap:wrap; gap:6px; }
  .skill-tag { background:#e8f5e9; color:#2d6a4f; font-size:9.5pt; padding:2px 10px; border-radius:99px; border:1px solid #a8d5b5; }
  @media print { body{-webkit-print-color-adjust:exact;print-color-adjust:exact;} .cv{padding:28px 36px;} }
`;

const THEME_EXECUTIVE = `
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: Georgia, 'Times New Roman', serif; font-size:11pt; color:#1a1a1a; background:#fff; }
  .cv { max-width:720px; margin:0 auto; }
  .cv-header { background:#1a2744; color:#fff; padding:36px 52px 28px; }
  .cv-name { font-size:24pt; font-weight:700; letter-spacing:0.5px; color:#fff; }
  .cv-role { font-size:11pt; color:#a8b8d8; margin-top:4px; font-style:italic; }
  .cv-contact { font-size:9pt; color:#c0cce0; margin-top:10px; display:flex; flex-wrap:wrap; gap:18px; }
  .cv-body { padding:32px 52px 52px; }
  .section { margin-top:22px; }
  .section-title { font-size:10pt; font-weight:700; text-transform:uppercase; letter-spacing:0.15em; color:#1a2744; border-bottom:2px solid #1a2744; padding-bottom:4px; margin-bottom:12px; }
  .entry { margin-bottom:12px; }
  .entry-head { display:flex; justify-content:space-between; align-items:baseline; }
  .entry-title { font-weight:700; font-size:11pt; color:#1a2744; }
  .entry-meta { font-size:9pt; color:#666; font-style:italic; margin-left:8px; white-space:nowrap; }
  .entry-sub { font-size:10pt; color:#555; margin-top:1px; }
  ul { margin-top:5px; padding-left:18px; }
  li { margin-bottom:3px; font-size:10.5pt; line-height:1.55; }
  .summary p { font-size:10.5pt; line-height:1.65; color:#333; font-style:italic; }
  .skills-list { display:flex; flex-wrap:wrap; gap:8px; }
  .skill-tag { color:#1a2744; font-size:9.5pt; padding:2px 0; }
  .skill-tag:not(:last-child)::after { content:" •"; margin-left:8px; color:#999; }
  @media print { body{-webkit-print-color-adjust:exact;print-color-adjust:exact;} .cv-header{padding:24px 36px 20px;} .cv-body{padding:24px 36px 36px;} }
`;

const THEME_TECH = `
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: 'Courier New', Courier, monospace; font-size:10.5pt; color:#0f172a; background:#fff; }
  .cv { max-width:720px; margin:0 auto; padding:40px 48px; }
  .cv-header { margin-bottom:20px; padding-bottom:14px; border-bottom:2px solid #0f172a; }
  .cv-name { font-size:20pt; font-weight:700; color:#0f172a; letter-spacing:-0.5px; }
  .cv-role { font-size:10pt; color:#2563eb; margin-top:3px; font-weight:700; }
  .cv-contact { font-size:8.5pt; color:#475569; margin-top:6px; display:flex; flex-wrap:wrap; gap:16px; }
  .section { margin-top:18px; }
  .section-title { font-size:8.5pt; font-weight:700; text-transform:uppercase; letter-spacing:0.18em; color:#2563eb; margin-bottom:8px; }
  .section-title::before { content:"## "; color:#94a3b8; }
  .entry { margin-bottom:10px; padding-left:12px; border-left:2px solid #e2e8f0; }
  .entry-head { display:flex; justify-content:space-between; align-items:baseline; }
  .entry-title { font-weight:700; font-size:10.5pt; color:#0f172a; }
  .entry-meta { font-size:8.5pt; color:#64748b; margin-left:8px; white-space:nowrap; }
  .entry-sub { font-size:9.5pt; color:#64748b; margin-top:1px; }
  ul { margin-top:4px; padding-left:14px; list-style:none; }
  li::before { content:"→ "; color:#2563eb; }
  li { margin-bottom:2px; font-size:10pt; line-height:1.5; }
  .summary p { font-size:10pt; line-height:1.6; color:#334155; }
  .skills-list { display:flex; flex-wrap:wrap; gap:6px; }
  .skill-tag { background:#eff6ff; color:#1d4ed8; font-size:9pt; padding:2px 8px; border:1px solid #bfdbfe; border-radius:3px; }
  @media print { body{-webkit-print-color-adjust:exact;print-color-adjust:exact;} .cv{padding:24px 32px;} }
`;

const THEME_MINIMAL = `
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size:10.5pt; color:#222; background:#fff; }
  .cv { max-width:680px; margin:0 auto; padding:56px 60px; }
  .cv-header { margin-bottom:28px; }
  .cv-name { font-size:21pt; font-weight:300; color:#111; letter-spacing:-0.5px; }
  .cv-role { font-size:11pt; color:#888; font-weight:400; margin-top:3px; }
  .cv-contact { font-size:9pt; color:#aaa; margin-top:8px; display:flex; flex-wrap:wrap; gap:16px; }
  .section { margin-top:22px; }
  .section-title { font-size:8pt; font-weight:600; text-transform:uppercase; letter-spacing:0.2em; color:#aaa; margin-bottom:10px; }
  .entry { margin-bottom:12px; }
  .entry-head { display:flex; justify-content:space-between; align-items:baseline; }
  .entry-title { font-weight:500; font-size:10.5pt; }
  .entry-meta { font-size:9pt; color:#aaa; margin-left:8px; white-space:nowrap; }
  .entry-sub { font-size:9.5pt; color:#999; margin-top:1px; }
  ul { margin-top:4px; padding-left:14px; }
  li { margin-bottom:2px; font-size:10pt; line-height:1.6; color:#444; }
  .summary p { font-size:10pt; line-height:1.7; color:#555; }
  .skills-list { display:flex; flex-wrap:wrap; gap:6px; }
  .skill-tag { color:#555; font-size:9.5pt; padding:2px 0; }
  .skill-tag:not(:last-child)::after { content:", "; color:#bbb; }
  @media print { body{-webkit-print-color-adjust:exact;print-color-adjust:exact;} .cv{padding:32px 40px;} }
`;

export const CV_PRINT_THEMES: Record<TemplateId, string> = {
  modern:    THEME_MODERN,
  executive: THEME_EXECUTIVE,
  tech:      THEME_TECH,
  minimal:   THEME_MINIMAL,
};

/** Contact block used when printing AI markdown with the user's header info. */
export type CvPrintHeader = {
  name: string;
  role: string;
  email: string;
  phone: string;
  address: string;
  url: string;
};

// ─── HTML content builder ─────────────────────────────────────────────────────

function buildContact(d: CvData): string {
  const parts = [d.email, d.phone, d.address, d.url].filter((v) => v?.trim());
  return parts.map((p) => `<span>${e(p)}</span>`).join("");
}

function buildExperience(d: CvData): string {
  const valid = d.experience.filter((ex) => ex.title.trim() || ex.company.trim());
  if (!valid.length) return "";
  const rows = valid.map((ex: CvExperience) => {
    const sub = [ex.company, ex.location].filter((v) => v.trim()).join(" · ");
    const bullets = ex.bullets.filter((b) => b.trim());
    return `
      <div class="entry">
        <div class="entry-head">
          <span class="entry-title">${e(ex.title)}</span>
          <span class="entry-meta">${e(ex.dates)}</span>
        </div>
        ${sub ? `<div class="entry-sub">${e(sub)}</div>` : ""}
        ${bullets.length ? `<ul>${bullets.map((b) => `<li>${e(b)}</li>`).join("")}</ul>` : ""}
      </div>`;
  });
  return `<div class="section"><div class="section-title">Experience</div>${rows.join("")}</div>`;
}

function formatEduDates(ed: CvEducation): string {
  const start = ed.startDate.trim();
  const end = ed.endDate.trim();
  if (start && end) return `${start} — ${end}`;
  return start || end;
}

function buildEducation(d: CvData): string {
  const valid = d.education.filter((ed) => ed.university.trim() || ed.degree.trim());
  if (!valid.length) return "";
  const rows = valid.map((ed: CvEducation) => {
    const dates = formatEduDates(ed);
    const sub = [ed.degree, ed.gpa.trim() ? `GPA: ${ed.gpa}` : ""].filter(Boolean).join(" · ");
    return `
    <div class="entry">
      <div class="entry-head">
        <span class="entry-title">${e(ed.university || ed.degree)}</span>
        ${dates ? `<span class="entry-meta">${e(dates)}</span>` : ""}
      </div>
      ${sub && ed.university.trim() ? `<div class="entry-sub">${e(sub)}</div>` : ""}
    </div>`;
  });
  return `<div class="section"><div class="section-title">Education</div>${rows.join("")}</div>`;
}

function formatSkillCategoryLabel(key: string): string {
  const labels: Record<string, string> = {
    frontend: "Frontend",
    backend: "Backend",
    databases: "Databases",
    tools: "Tools",
    cloud: "Cloud",
    soft_skills: "Soft Skills",
  };
  if (labels[key]) return labels[key];
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

const SKILL_CATEGORY_ORDER = [
  "frontend",
  "backend",
  "databases",
  "tools",
  "cloud",
  "soft_skills",
];

function sortSkillCategories(entries: [string, string[]][]): [string, string[]][] {
  return [...entries].sort(([a], [b]) => {
    const ia = SKILL_CATEGORY_ORDER.indexOf(a);
    const ib = SKILL_CATEGORY_ORDER.indexOf(b);
    if (ia === -1 && ib === -1) return a.localeCompare(b);
    if (ia === -1) return 1;
    if (ib === -1) return -1;
    return ia - ib;
  });
}

function buildSkills(d: CvData): string {
  const categories = d.skillsByCategory;
  const shown = new Set<string>();
  const rows: string[] = [];

  if (categories && Object.keys(categories).length) {
    const entries = sortSkillCategories(
      Object.entries(categories).filter(
        ([, items]) => Array.isArray(items) && items.some((s) => s.trim()),
      ),
    );

    for (const [key, items] of entries) {
      const cleaned = items.map((s) => s.trim()).filter(Boolean);
      if (!cleaned.length) continue;
      cleaned.forEach((s) => shown.add(s.toLowerCase()));
      const label = formatSkillCategoryLabel(key);
      rows.push(
        `<div class="skill-category" style="margin-bottom:6px;font-size:10pt;line-height:1.5;">
          <span style="font-weight:600;">${e(label)}:</span> ${cleaned.map((s) => e(s)).join(", ")}
        </div>`,
      );
    }
  }

  const uncategorized = d.skills
    .map((s) => s.trim())
    .filter((s) => s && !shown.has(s.toLowerCase()));

  if (uncategorized.length) {
    const tags = uncategorized.map((s) => `<span class="skill-tag">${e(s)}</span>`).join("");
    rows.push(`<div class="skills-list" style="margin-top:6px;">${tags}</div>`);
  }

  if (!rows.length) {
    const skills = d.skills.filter((s) => s.trim());
    if (!skills.length) return "";
    const tags = skills.map((s) => `<span class="skill-tag">${e(s)}</span>`).join("");
    return `<div class="section"><div class="section-title">Skills</div><div class="skills-list">${tags}</div></div>`;
  }

  return `<div class="section"><div class="section-title">Skills</div>${rows.join("")}</div>`;
}

function buildProjects(d: CvData): string {
  const valid = d.projects.filter((p) => p.title.trim());
  if (!valid.length) return "";
  const rows = valid.map((p: CvProject) => {
    const bullets = (p.bullets ?? []).filter((b) => b.trim());
    const body = bullets.length
      ? `<ul>${bullets.map((b) => `<li>${e(b)}</li>`).join("")}</ul>`
      : p.description.trim()
        ? `<p style="margin-top:4px;font-size:10pt;line-height:1.5;">${e(p.description)}</p>`
        : "";
    return `
    <div class="entry">
      <div class="entry-head">
        <span class="entry-title">${e(p.title)}</span>
      </div>
      ${body}
    </div>`;
  });
  return `<div class="section"><div class="section-title">Projects</div>${rows.join("")}</div>`;
}

function buildCertifications(d: CvData): string {
  const items = d.certifications.filter((c) => c.trim());
  if (!items.length) return "";
  const list = items.map((c) => `<li>${e(c)}</li>`).join("");
  return `<div class="section"><div class="section-title">Certifications</div><ul>${list}</ul></div>`;
}

/** Turn pipeline markdown into HTML sections that match our print templates. */
export function markdownToBodyHtml(markdown: string): string {
  const lines = markdown.split("\n");
  const parts: string[] = [];
  let listOpen = false;
  let skippedPreamble = false;

  const closeList = () => {
    if (listOpen) {
      parts.push("</ul>");
      listOpen = false;
    }
  };

  const isPreambleLine = (line: string): boolean => {
    if (line.startsWith("# ")) return true;
    if (!skippedPreamble) return false;
    if (line.startsWith("## ")) return false;
    if (line.includes(" · ") && line.length < 160) return true;
    if (!line.startsWith("## ") && !line.startsWith("### ") && !line.startsWith("- ")) {
      return line.length < 80;
    }
    return false;
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      closeList();
      continue;
    }

    if (line.startsWith("# ")) {
      closeList();
      skippedPreamble = true;
      continue;
    }
    if (isPreambleLine(line)) {
      closeList();
      continue;
    }
    if (line.startsWith("## ")) {
      closeList();
      skippedPreamble = true;
      parts.push(
        `<div class="section"><div class="section-title">${e(line.slice(2).trim())}</div>`,
      );
      continue;
    }
    if (line.startsWith("### ")) {
      closeList();
      parts.push(`
        <div class="entry">
          <div class="entry-head">
            <span class="entry-title">${e(line.slice(3).trim())}</span>
          </div>`);
      continue;
    }
    if (line.startsWith("- ") || line.startsWith("• ") || line.startsWith("* ")) {
      if (!listOpen) {
        parts.push("<ul>");
        listOpen = true;
      }
      parts.push(`<li>${e(line.replace(/^[-•*]\s+/, ""))}</li>`);
      continue;
    }

    closeList();
    if (line.includes(" · ") && line.length < 120) {
      parts.push(`<p style="font-size:9pt;color:#555;margin:4px 0 0;">${e(line)}</p>`);
    } else {
      parts.push(`<p style="font-size:10.5pt;line-height:1.6;color:#333;margin:4px 0 0;">${e(line)}</p>`);
    }
  }
  closeList();
  return parts.join("\n");
}

function wrapCvDocument(bodyInner: string, templateId: TemplateId, title: string): string {
  const css = CV_PRINT_THEMES[templateId];
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${e(title)}</title>
  <style>${css}</style>
</head>
<body>
  <div class="cv">${bodyInner}</div>
</body>
</html>`;
}

export function buildHtml(d: CvData, templateId: TemplateId): string {
  const isExecutive = templateId === "executive";

  const header = `
    <div class="cv-header">
      <div class="cv-name">${e(d.name || "Your Name")}</div>
      ${d.role.trim() ? `<div class="cv-role">${e(d.role)}</div>` : ""}
      <div class="cv-contact">${buildContact(d)}</div>
    </div>`;

  const summary = d.summary.trim()
    ? `<div class="section summary"><div class="section-title">Summary</div><p>${e(d.summary)}</p></div>`
    : "";

  const sections = [
    summary,
    buildEducation(d),
    buildSkills(d),
    buildExperience(d),
    buildProjects(d),
    buildCertifications(d),
  ].join("");

  const inner = isExecutive
    ? `<div class="cv-header">
        <div class="cv-name">${e(d.name || "Your Name")}</div>
        ${d.role.trim() ? `<div class="cv-role">${e(d.role)}</div>` : ""}
        <div class="cv-contact">${buildContact(d)}</div>
       </div>
       <div class="cv-body">${sections}</div>`
    : `${header}${sections}`;

  return wrapCvDocument(inner, templateId, d.name || "CV");
}

function buildHeaderBlock(h: CvPrintHeader): string {
  const contact = [h.email, h.phone, h.address, h.url].filter((v) => v?.trim());
  return `
    <div class="cv-header">
      <div class="cv-name">${e(h.name || "Your Name")}</div>
      ${h.role.trim() ? `<div class="cv-role">${e(h.role)}</div>` : ""}
      <div class="cv-contact">${contact.map((p) => `<span>${e(p)}</span>`).join("")}</div>
    </div>`;
}

/** Build full HTML for AI markdown using the same template as the picker. */
export function buildHtmlFromMarkdown(
  markdown: string,
  templateId: TemplateId,
  header: CvPrintHeader,
): string {
  const body = markdownToBodyHtml(markdown);
  const inner =
    templateId === "executive"
      ? `${buildHeaderBlock(header)}<div class="cv-body">${body}</div>`
      : `${buildHeaderBlock(header)}${body}`;
  return wrapCvDocument(inner, templateId, header.name || "CV");
}

export function openPrintDialog(html: string): void {
  const win = window.open("", "_blank", "width=860,height=1100");
  if (!win) {
    alert("Pop-up blocked — please allow pop-ups for this site to download your CV.");
    return;
  }
  win.document.open();
  win.document.write(html);
  win.document.close();
  win.addEventListener("load", () => {
    win.focus();
    win.print();
  });
}

// ─── Public API ───────────────────────────────────────────────────────────────

/** Print the user's form data in the selected template (Save as PDF in dialog). */
export function printCvWithTemplate(data: CvData, templateId: TemplateId): void {
  openPrintDialog(buildHtml(data, templateId));
}

/** Print AI-generated markdown in the same template as the editor preview. */
export function printMarkdownWithTemplate(
  markdown: string,
  templateId: TemplateId,
  header: CvPrintHeader,
): void {
  openPrintDialog(buildHtmlFromMarkdown(markdown, templateId, header));
}
