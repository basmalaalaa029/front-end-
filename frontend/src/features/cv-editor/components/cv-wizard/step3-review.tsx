import { useEffect, useMemo, useRef, useState } from "react";
import toast from "react-hot-toast";
import { HubHeader, HubIcon } from "@/features/hub-shell";
import { useI18n } from "@/features/i18n";
import type { CvData } from "@/features/cv-editor/data/cv-types";
import type { TemplateId } from "@/features/cv-editor/data/cv-templates";
import { CvSectionEditor } from "@/features/cv-editor/components/cv-editor-page/cv-section-editor";
import { buildHtml } from "@/features/cv-editor/lib/cv-print";
import { printCvWithTemplate } from "@/features/cv-editor/lib/cv-print";
import type { GeneratedCv } from "./types";

type Props = {
  generatedCv: GeneratedCv;
  cvData: CvData;
  templateId: TemplateId;
  onRestart: () => void;
  onCvChange: (data: CvData) => void;
};

/** A4-ish page width used by CV print templates. */
const CV_PAGE_WIDTH = 760;
const CV_PAGE_HEIGHT = 1120;

function FitCvPreview({ html, title }: { html: string; title: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const updateScale = () => {
      const pad = 40;
      const available = el.clientWidth - pad;
      if (available <= 0) return;
      setScale(Math.min(available / CV_PAGE_WIDTH, 1));
    };

    updateScale();
    const ro = new ResizeObserver(updateScale);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="cv-fit-preview">
      <div
        className="cv-fit-preview__frame"
        style={{
          width: CV_PAGE_WIDTH * scale,
          height: CV_PAGE_HEIGHT * scale,
        }}
      >
        <iframe
          title={title}
          srcDoc={html}
          tabIndex={-1}
          style={{
            width: CV_PAGE_WIDTH,
            height: CV_PAGE_HEIGHT,
            transform: `scale(${scale})`,
            transformOrigin: "top left",
          }}
        />
      </div>
    </div>
  );
}

export function Step3Review({
  generatedCv,
  cvData,
  templateId,
  onRestart,
  onCvChange,
}: Props) {
  const { t } = useI18n();
  const [activeSection, setActiveSection] = useState("contact");

  const sectionDefs = useMemo(
    () =>
      [
        { id: "contact", icon: "user", label: t("cvEditor.sections.contact") },
        { id: "summary", icon: "align-left", label: t("cvEditor.sections.summary") },
        { id: "education", icon: "graduation-cap", label: t("cvEditor.sections.education") },
        { id: "skills", icon: "wrench", label: t("cvEditor.sections.skills") },
        { id: "experience", icon: "briefcase", label: t("cvEditor.sections.experience") },
        { id: "projects", icon: "folder-open", label: t("cvEditor.sections.projects") },
        { id: "certifications", icon: "award", label: t("cvEditor.sections.certifications") },
      ] as const,
    [t],
  );

  const previewHtml = useMemo(
    () => buildHtml(cvData, templateId),
    [cvData, templateId],
  );

  const handleExport = () => {
    if (!cvData.name.trim()) {
      toast.error(t("cvEditor.gen.missingFields") + " " + t("cvEditor.fields.name"));
      return;
    }
    printCvWithTemplate(cvData, templateId);
    toast.success(t("cvEditor.gen.exportOpened"));
  };

  const displayName =
    cvData.name.trim() ||
    generatedCv.personal_info?.full_name?.trim() ||
    t("cvEditor.untitledName");
  const displayRole =
    cvData.role.trim() ||
    generatedCv.target_title?.trim() ||
    t("cvEditor.untitledRole");

  return (
    <>
      <HubHeader
        title={`${displayName} — ${displayRole}`}
        sub={t("cvEditor.wizard.reviewSub")}
        right={
          <>
            <button type="button" className="btn btn-ghost btn-sm" onClick={onRestart}>
              <HubIcon name="refresh-cw" size={14} stroke={2} />
              {t("cvEditor.wizard.startOver")}
            </button>
            <button type="button" className="btn btn-primary" onClick={handleExport}>
              <HubIcon name="download" size={14} stroke={2} />
              {t("cvEditor.export")}
            </button>
          </>
        }
      />

      <div className="wizard-step review">
        <div className="wizard-review-layout">
          <FitCvPreview html={previewHtml} title={t("cvEditor.wizard.previewTitle")} />

          <div className="wizard-review-sidebar">
            <div className="sections-panel">
              <h4>{t("cvEditor.sectionsLabel")}</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                {sectionDefs.map((s) => (
                  <div
                    key={s.id}
                    className={"section-block " + (activeSection === s.id ? "is-active" : "")}
                    onClick={() => setActiveSection(s.id)}
                    onKeyDown={(e) => e.key === "Enter" && setActiveSection(s.id)}
                    role="button"
                    tabIndex={0}
                  >
                    <HubIcon name="grip-vertical" size={14} className="grip" />
                    <HubIcon name={s.icon} size={15} />
                    <span>{s.label}</span>
                  </div>
                ))}
              </div>
            </div>
            <CvSectionEditor
              active={activeSection}
              data={cvData}
              setData={(updater) => {
                if (typeof updater === "function") {
                  onCvChange(updater(cvData));
                } else {
                  onCvChange(updater);
                }
              }}
            />
          </div>
        </div>
      </div>
    </>
  );
}
