import { useCallback, useEffect, useState, type Dispatch, type SetStateAction, type KeyboardEvent } from "react";
import type { CvData, CvProject } from "@/features/cv-editor/data/cv-types";
import { useI18n } from "@/features/i18n";
import { HubIcon } from "@/features/hub-shell";
import { useAtsSectionRewrite } from "@/features/cv-editor/hooks/use-ats-section-rewrite";
import { addSkillToCvData, removeSkillFromCvData } from "@/features/cv-editor/lib/cv-skills";

type Props = {
  active: string;
  data: CvData;
  setData: Dispatch<SetStateAction<CvData>>;
  targetRole?: string;
};

function AtsRewriteBar({
  sectionKey,
  rewritingKey,
  onRewriteNow,
}: {
  sectionKey: string;
  rewritingKey: string | null;
  onRewriteNow: () => void;
}) {
  const { t } = useI18n();
  const busy = rewritingKey === sectionKey;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 8,
        marginTop: 8,
        fontSize: 11,
        color: "var(--fg-tertiary, #94a3b8)",
      }}
    >
      <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
        {busy ? (
          <>
            <HubIcon name="loader-2" size={13} stroke={2} />
            {t("cvEditor.atsRewrite.optimizing")}
          </>
        ) : (
          <>
            <HubIcon name="sparkles" size={13} stroke={2} />
            {t("cvEditor.atsRewrite.hint")}
          </>
        )}
      </span>
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        onClick={onRewriteNow}
        disabled={busy}
      >
        {t("cvEditor.atsRewrite.improveNow")}
      </button>
    </div>
  );
}

function SkillsEditor({
  data,
  setData,
  targetRole,
  rewriteNow,
  rewritingKey,
}: {
  data: CvData;
  setData: Dispatch<SetStateAction<CvData>>;
  targetRole: string;
  rewriteNow: ReturnType<typeof useAtsSectionRewrite>["rewriteNow"];
  rewritingKey: string | null;
}) {
  const { t } = useI18n();
  const [draft, setDraft] = useState("");

  const addSkill = (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed) return;
    setData((d) => addSkillToCvData(d, trimmed));
    setDraft("");
  };

  const removeSkill = (idx: number) => setData((d) => removeSkillFromCvData(d, idx));

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill(draft);
    } else if (e.key === "Backspace" && draft === "" && data.skills.length > 0) {
      removeSkill(data.skills.length - 1);
    }
  };

  return (
    <div className="sections-panel cv-edit-panel">
      <h4>{t("cvEditor.editSection")}</h4>
      <div className="cv-field-group">
        <label>{t("cvEditor.fields.skills")}</label>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 6,
            padding: "8px 10px",
            border: "1px solid var(--border-default, #d1d5db)",
            borderRadius: 8,
            background: "var(--surface-input, #fff)",
            minHeight: 44,
            cursor: "text",
          }}
          onClick={() => document.getElementById("skill-input")?.focus()}
        >
          {data.skills.map((skill, idx) => (
            <span
              key={idx}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                fontSize: 12,
                padding: "3px 8px",
                borderRadius: 999,
                background: "var(--bone-100, #f1f5f9)",
                color: "var(--fg-secondary, #475569)",
                fontWeight: 500,
              }}
            >
              {skill}
              <button
                type="button"
                aria-label={`Remove ${skill}`}
                onClick={(e) => { e.stopPropagation(); removeSkill(idx); }}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: 0,
                  lineHeight: 1,
                  color: "var(--fg-tertiary, #94a3b8)",
                  fontSize: 14,
                  fontWeight: 700,
                }}
              >
                ×
              </button>
            </span>
          ))}
          <input
            id="skill-input"
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKey}
            onBlur={() => addSkill(draft)}
            placeholder={data.skills.length === 0 ? t("cvEditor.placeholders.skillInput") : ""}
            style={{
              border: "none",
              outline: "none",
              background: "transparent",
              fontSize: 13,
              flex: "1 1 80px",
              minWidth: 80,
              padding: "2px 0",
            }}
          />
        </div>
        <p style={{ margin: "5px 0 0", fontSize: 11, color: "var(--fg-tertiary, #94a3b8)" }}>
          {t("cvEditor.skillHint")}
        </p>
        <AtsRewriteBar
          sectionKey="skills"
          rewritingKey={rewritingKey}
          onRewriteNow={() =>
            rewriteNow({
              section: "skills",
              key: "skills",
              targetRole,
              skills: data.skills,
              education: data.education.map((e) => e.degree).filter(Boolean),
            })
          }
        />
      </div>
    </div>
  );
}

export function CvSectionEditor({ active, data, setData, targetRole = "" }: Props) {
  const { t } = useI18n();
  const role = targetRole.trim() || data.role.trim();

  const handleApply = useCallback(
    (result: {
      section: "summary" | "experience" | "skills";
      key: string;
      summary?: string;
      bullets?: string[];
      skills?: string[];
      skillsByCategory?: Record<string, string[]>;
    }) => {
      if (result.section === "summary" && result.summary) {
        setData((d) => ({ ...d, summary: result.summary! }));
        return;
      }
      if (result.section === "experience" && result.bullets) {
        const idx = Number.parseInt(result.key.split(":")[1] ?? "", 10);
        if (Number.isNaN(idx)) return;
        setData((d) => {
          const experience = [...d.experience];
          if (!experience[idx]) return d;
          experience[idx] = { ...experience[idx], bullets: result.bullets! };
          return { ...d, experience };
        });
        return;
      }
      if (result.section === "skills" && result.skills?.length) {
        setData((d) => ({
          ...d,
          skills: result.skills!,
          skillsByCategory: result.skillsByCategory ?? d.skillsByCategory,
        }));
      }
    },
    [setData],
  );

  const { scheduleRewrite, rewriteNow, rewritingKey } = useAtsSectionRewrite(handleApply);

  useEffect(() => {
    if (active !== "summary") return;
    scheduleRewrite({
      section: "summary",
      key: "summary",
      targetRole: role,
      summary: data.summary,
    });
  }, [active, data.summary, role, scheduleRewrite]);

  useEffect(() => {
    if (active !== "skills") return;
    scheduleRewrite({
      section: "skills",
      key: "skills",
      targetRole: role,
      skills: data.skills,
      education: data.education.map((e) => e.degree).filter(Boolean),
    });
  }, [active, data.skills, data.education, role, scheduleRewrite]);

  useEffect(() => {
    if (active !== "experience") return;
    data.experience.forEach((ex, i) => {
      const bullets = ex.bullets.map((b) => b.trim()).filter(Boolean);
      if (!bullets.length) return;
      scheduleRewrite({
        section: "experience",
        key: `experience:${i}`,
        targetRole: role,
        jobTitle: ex.title,
        company: ex.company,
        bullets,
      });
    });
  }, [active, data.experience, role, scheduleRewrite]);

  if (active === "contact") {
    return (
      <div className="sections-panel cv-edit-panel">
        <h4>{t("cvEditor.contactHead")}</h4>
        <div className="cv-field-group">
          <label htmlFor="cv-name">{t("cvEditor.fields.name")}</label>
          <input
            id="cv-name"
            type="text"
            value={data.name}
            onChange={(e) => setData((d) => ({ ...d, name: e.target.value }))}
            placeholder={t("cvEditor.placeholders.name")}
          />
        </div>
        <div className="cv-field-group">
          <label htmlFor="cv-role">{t("cvEditor.fields.role")}</label>
          <input
            id="cv-role"
            type="text"
            value={data.role}
            onChange={(e) => setData((d) => ({ ...d, role: e.target.value }))}
            placeholder={t("cvEditor.placeholders.role")}
          />
        </div>
        <div className="cv-field-group">
          <label htmlFor="cv-email">{t("cvEditor.fields.email")}</label>
          <input
            id="cv-email"
            type="email"
            value={data.email}
            onChange={(e) => setData((d) => ({ ...d, email: e.target.value }))}
            placeholder={t("cvEditor.placeholders.email")}
          />
        </div>
        <div className="cv-field-group">
          <label htmlFor="cv-phone">{t("cvEditor.fields.phone")}</label>
          <input
            id="cv-phone"
            type="text"
            value={data.phone}
            onChange={(e) => setData((d) => ({ ...d, phone: e.target.value }))}
            placeholder={t("cvEditor.placeholders.phone")}
          />
        </div>
        <div className="cv-field-group">
          <label htmlFor="cv-address">{t("cvEditor.fields.address")}</label>
          <input
            id="cv-address"
            type="text"
            value={data.address}
            onChange={(e) => setData((d) => ({ ...d, address: e.target.value }))}
            placeholder={t("cvEditor.placeholders.address")}
          />
        </div>
        <div className="cv-field-group">
          <label htmlFor="cv-url">{t("cvEditor.fields.url")}</label>
          <input
            id="cv-url"
            type="text"
            value={data.url}
            onChange={(e) => setData((d) => ({ ...d, url: e.target.value }))}
            placeholder={t("cvEditor.placeholders.url")}
          />
        </div>
      </div>
    );
  }

  if (active === "projects") {
    return (
      <div className="sections-panel cv-edit-panel">
        <h4>{t("cvEditor.editSection")}</h4>
        {data.projects.map((proj: CvProject, i: number) => (
          <div key={i} className="cv-edit-block">
            <p className="cv-edit-block-title">
              {t("cvEditor.projectIndex", { n: String(i + 1) })}
            </p>
            <div className="cv-field-group">
              <label htmlFor={`proj-title-${i}`}>{t("cvEditor.fields.projectTitle")}</label>
              <input
                id={`proj-title-${i}`}
                type="text"
                value={proj.title}
                onChange={(e) =>
                  setData((d) => {
                    const projects = [...d.projects];
                    projects[i] = { ...projects[i], title: e.target.value };
                    return { ...d, projects };
                  })
                }
                placeholder={t("cvEditor.placeholders.projectTitle")}
              />
            </div>
            <div className="cv-field-group">
              <label htmlFor={`proj-desc-${i}`}>{t("cvEditor.fields.projectDesc")}</label>
              <textarea
                id={`proj-desc-${i}`}
                value={proj.description}
                onChange={(e) =>
                  setData((d) => {
                    const projects = [...d.projects];
                    projects[i] = { ...projects[i], description: e.target.value };
                    return { ...d, projects };
                  })
                }
                placeholder={t("cvEditor.placeholders.projectDesc")}
                rows={3}
              />
            </div>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              style={{ color: "var(--fg-tertiary)", marginTop: 4 }}
              onClick={() =>
                setData((d) => ({
                  ...d,
                  projects: d.projects.filter((_, idx) => idx !== i),
                }))
              }
            >
              {t("cvEditor.removeProject")}
            </button>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() =>
            setData((d) => ({
              ...d,
              projects: [...d.projects, { title: "", description: "" }],
            }))
          }
        >
          {t("cvEditor.addProject")}
        </button>
      </div>
    );
  }

  if (active === "certifications") {
    return (
      <div className="sections-panel cv-edit-panel">
        <h4>{t("cvEditor.editSection")}</h4>
        {data.certifications.map((cert, i) => (
          <div key={i} className="cv-edit-block">
            <div className="cv-field-group">
              <label htmlFor={`cert-${i}`}>
                {t("cvEditor.certIndex", { n: String(i + 1) })}
              </label>
              <input
                id={`cert-${i}`}
                type="text"
                value={cert}
                onChange={(e) =>
                  setData((d) => {
                    const certifications = [...d.certifications];
                    certifications[i] = e.target.value;
                    return { ...d, certifications };
                  })
                }
                placeholder={t("cvEditor.placeholders.certification")}
              />
            </div>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              style={{ color: "var(--fg-tertiary)", marginTop: 4 }}
              onClick={() =>
                setData((d) => ({
                  ...d,
                  certifications: d.certifications.filter((_, idx) => idx !== i),
                }))
              }
            >
              {t("cvEditor.removeCertification")}
            </button>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() =>
            setData((d) => ({
              ...d,
              certifications: [...d.certifications, ""],
            }))
          }
        >
          {t("cvEditor.addCertification")}
        </button>
      </div>
    );
  }

  if (active === "summary") {
    return (
      <div className="sections-panel cv-edit-panel">
        <h4>{t("cvEditor.editSection")}</h4>
        <div className="cv-field-group">
          <label htmlFor="cv-summary">{t("cvEditor.fields.summary")}</label>
          <textarea
            id="cv-summary"
            value={data.summary}
            onChange={(e) => setData((d) => ({ ...d, summary: e.target.value }))}
            placeholder={t("cvEditor.placeholders.summary")}
            rows={6}
          />
          <AtsRewriteBar
            sectionKey="summary"
            rewritingKey={rewritingKey}
            onRewriteNow={() =>
              rewriteNow({
                section: "summary",
                key: "summary",
                targetRole: role,
                summary: data.summary,
              })
            }
          />
        </div>
      </div>
    );
  }

  if (active === "skills") {
    return (
      <SkillsEditor
        data={data}
        setData={setData}
        targetRole={role}
        rewriteNow={rewriteNow}
        rewritingKey={rewritingKey}
      />
    );
  }

  if (active === "education") {
    return (
      <div className="sections-panel cv-edit-panel">
        <h4>{t("cvEditor.editSection")}</h4>
        {data.education.map((ed, i) => (
          <div key={i} className="cv-edit-block">
            <div className="cv-field-group">
              <label htmlFor={`ed-degree-${i}`}>{t("cvEditor.fields.degree")}</label>
              <input
                id={`ed-degree-${i}`}
                type="text"
                value={ed.degree}
                onChange={(e) =>
                  setData((d) => {
                    const education = [...d.education];
                    education[i] = { ...education[i], degree: e.target.value };
                    return { ...d, education };
                  })
                }
                placeholder={t("cvEditor.placeholders.degree")}
              />
            </div>
            <div className="cv-field-group">
              <label htmlFor={`ed-uni-${i}`}>{t("cvEditor.fields.university")}</label>
              <input
                id={`ed-uni-${i}`}
                type="text"
                value={ed.university}
                onChange={(e) =>
                  setData((d) => {
                    const education = [...d.education];
                    education[i] = { ...education[i], university: e.target.value };
                    return { ...d, education };
                  })
                }
                placeholder={t("cvEditor.placeholders.university")}
              />
            </div>
            <div className="cv-field-group" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <label htmlFor={`ed-start-${i}`}>{t("cvEditor.fields.startDate")}</label>
                <input
                  id={`ed-start-${i}`}
                  type="text"
                  value={ed.startDate}
                  onChange={(e) =>
                    setData((d) => {
                      const education = [...d.education];
                      education[i] = { ...education[i], startDate: e.target.value };
                      return { ...d, education };
                    })
                  }
                  placeholder={t("cvEditor.placeholders.startDate")}
                />
              </div>
              <div>
                <label htmlFor={`ed-end-${i}`}>{t("cvEditor.fields.endDate")}</label>
                <input
                  id={`ed-end-${i}`}
                  type="text"
                  value={ed.endDate}
                  onChange={(e) =>
                    setData((d) => {
                      const education = [...d.education];
                      education[i] = { ...education[i], endDate: e.target.value };
                      return { ...d, education };
                    })
                  }
                  placeholder={t("cvEditor.placeholders.endDate")}
                />
              </div>
            </div>
            <div className="cv-field-group">
              <label htmlFor={`ed-gpa-${i}`}>{t("cvEditor.fields.gpa")}</label>
              <input
                id={`ed-gpa-${i}`}
                type="text"
                value={ed.gpa}
                onChange={(e) =>
                  setData((d) => {
                    const education = [...d.education];
                    education[i] = { ...education[i], gpa: e.target.value };
                    return { ...d, education };
                  })
                }
                placeholder={t("cvEditor.placeholders.gpa")}
              />
            </div>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() =>
            setData((d) => ({
              ...d,
              education: [
                ...d.education,
                { degree: "", university: "", startDate: "", endDate: "", gpa: "" },
              ],
            }))
          }
        >
          {t("cvEditor.addEducation")}
        </button>
      </div>
    );
  }

  if (active === "experience") {
    return (
      <div className="sections-panel cv-edit-panel">
        <h4>{t("cvEditor.editSection")}</h4>
        {data.experience.map((ex, i) => (
          <div key={i} className="cv-edit-block">
            <p className="cv-edit-block-title">
              {t("cvEditor.roleIndex", { n: String(i + 1) })}
            </p>
            <div className="cv-field-group">
              <label htmlFor={`ex-title-${i}`}>{t("cvEditor.fields.jobTitle")}</label>
              <input
                id={`ex-title-${i}`}
                type="text"
                value={ex.title}
                onChange={(e) =>
                  setData((d) => {
                    const experience = [...d.experience];
                    experience[i] = { ...experience[i], title: e.target.value };
                    return { ...d, experience };
                  })
                }
                placeholder={t("cvEditor.placeholders.jobTitle")}
              />
            </div>
            <div className="cv-field-group">
              <label htmlFor={`ex-company-${i}`}>{t("cvEditor.fields.company")}</label>
              <input
                id={`ex-company-${i}`}
                type="text"
                value={ex.company}
                onChange={(e) =>
                  setData((d) => {
                    const experience = [...d.experience];
                    experience[i] = { ...experience[i], company: e.target.value };
                    return { ...d, experience };
                  })
                }
                placeholder={t("cvEditor.placeholders.company")}
              />
            </div>
            <div className="cv-field-group">
              <label htmlFor={`ex-loc-${i}`}>{t("cvEditor.fields.jobLocation")}</label>
              <input
                id={`ex-loc-${i}`}
                type="text"
                value={ex.location}
                onChange={(e) =>
                  setData((d) => {
                    const experience = [...d.experience];
                    experience[i] = { ...experience[i], location: e.target.value };
                    return { ...d, experience };
                  })
                }
                placeholder={t("cvEditor.placeholders.jobLocation")}
              />
            </div>
            <div className="cv-field-group">
              <label htmlFor={`ex-dates-${i}`}>{t("cvEditor.fields.dates")}</label>
              <input
                id={`ex-dates-${i}`}
                type="text"
                value={ex.dates}
                onChange={(e) =>
                  setData((d) => {
                    const experience = [...d.experience];
                    experience[i] = { ...experience[i], dates: e.target.value };
                    return { ...d, experience };
                  })
                }
                placeholder={t("cvEditor.placeholders.dates")}
              />
            </div>
            <div className="cv-field-group">
              <label htmlFor={`ex-bullets-${i}`}>{t("cvEditor.fields.bullets")}</label>
              <textarea
                id={`ex-bullets-${i}`}
                value={ex.bullets.join("\n")}
                onChange={(e) =>
                  setData((d) => {
                    const experience = [...d.experience];
                    const lines = e.target.value.split("\n");
                    experience[i] = {
                      ...experience[i],
                      bullets: lines.length ? lines : [""],
                    };
                    return { ...d, experience };
                  })
                }
                placeholder={t("cvEditor.placeholders.bullets")}
                rows={5}
              />
              <AtsRewriteBar
                sectionKey={`experience:${i}`}
                rewritingKey={rewritingKey}
                onRewriteNow={() =>
                  rewriteNow({
                    section: "experience",
                    key: `experience:${i}`,
                    targetRole: role,
                    jobTitle: ex.title,
                    company: ex.company,
                    bullets: ex.bullets.map((b) => b.trim()).filter(Boolean),
                  })
                }
              />
            </div>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() =>
            setData((d) => ({
              ...d,
              experience: [
                ...d.experience,
                { title: "", company: "", location: "", dates: "", bullets: [""] },
              ],
            }))
          }
        >
          {t("cvEditor.addRole")}
        </button>
      </div>
    );
  }

  return (
    <div className="sections-panel cv-edit-panel">
      <p className="cv-edit-hint">{t("cvEditor.pickSectionHint")}</p>
    </div>
  );
}
