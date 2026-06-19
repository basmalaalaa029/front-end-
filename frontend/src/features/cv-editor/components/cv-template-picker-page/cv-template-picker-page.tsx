import { useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload } from "lucide-react";
import toast from "react-hot-toast";
import { setPendingAnalysisFile } from "@/features/cv-analysis/lib/pending-upload";
import type { AnalysisNavigationState } from "@/features/cv-analysis/types";
import { useI18n } from "@/features/i18n";
import { TEMPLATE_IDS, type TemplateId } from "@/features/cv-editor/data/cv-templates";
import {
  TEMPLATE_FILTER_IDS,
  TEMPLATE_META,
  templateMatchesFilter,
  type TemplateFilterId,
} from "@/features/cv-editor/data/cv-template-meta";
import { TemplateLivePreview } from "./template-live-preview";
import "./cv-template-picker.css";

export default function CvTemplatePickerPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const gridRef = useRef<HTMLDivElement>(null);
  const uploadRef = useRef<HTMLInputElement>(null);
  const [activeFilter, setActiveFilter] = useState<TemplateFilterId>("all");

  const handleUploadResume = () => {
    uploadRef.current?.click();
  };

  const handleUploadFile = (file: File) => {
    setPendingAnalysisFile(file);
    const navState: AnalysisNavigationState = { autoUpload: true };
    navigate("/dashboard/analyzer", { state: navState });
  };

  const visibleIds = useMemo(
    () => TEMPLATE_IDS.filter((id) => templateMatchesFilter(id, activeFilter)),
    [activeFilter],
  );

  const go = (id: TemplateId) => {
    navigate(`/dashboard/editor/create/${id}`);
  };

  const scrollToTemplates = () => {
    gridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="template-gallery">
      <section className="template-gallery__hero">
        <h1 className="template-gallery__title">{t("cvEditor.gallery.title")}</h1>
        <p className="template-gallery__lead">{t("cvEditor.gallery.lead")}</p>
        <div className="template-gallery__hero-actions">
          <button type="button" className="btn btn-primary btn-lg" onClick={scrollToTemplates}>
            {t("cvEditor.gallery.createResume")}
          </button>
          <button
            type="button"
            className="btn btn-outline btn-lg"
            onClick={handleUploadResume}
          >
            <Upload size={18} strokeWidth={2} aria-hidden />
            {t("cvEditor.gallery.uploadResume")}
          </button>
          <input
            ref={uploadRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const ok =
                /\.(pdf|docx?|txt)$/i.test(file.name) ||
                file.type.includes("pdf") ||
                file.type.includes("word") ||
                file.type === "text/plain";
              if (!ok) {
                toast.error("Please upload a PDF, DOCX, or TXT file.");
                e.target.value = "";
                return;
              }
              handleUploadFile(file);
              e.target.value = "";
            }}
          />
        </div>
      </section>

      <div className="template-gallery__toolbar" ref={gridRef} id="templates">
        <div className="template-gallery__filters" role="tablist" aria-label={t("cvEditor.gallery.filterLabel")}>
          {TEMPLATE_FILTER_IDS.map((filterId) => (
            <button
              key={filterId}
              type="button"
              role="tab"
              aria-selected={activeFilter === filterId}
              className={
                "template-gallery__filter" + (activeFilter === filterId ? " is-active" : "")
              }
              onClick={() => setActiveFilter(filterId)}
            >
              {t(`cvEditor.gallery.filters.${filterId}`)}
            </button>
          ))}
        </div>
        <p className="template-gallery__count">
          {t("cvEditor.gallery.count", { n: String(visibleIds.length) })}
        </p>
      </div>

      <div className="template-gallery__grid">
        {visibleIds.map((id) => (
          <article key={id} className={`template-gallery__card template-gallery__card--${id}`}>
            <button
              type="button"
              className="template-gallery__card-hit"
              onClick={() => go(id)}
              aria-label={`${t(`cvEditor.templates.${id}.name`)} — ${t("cvEditor.gallery.useTemplate")}`}
            >
              <div className="template-gallery__preview">
                <TemplateLivePreview
                  templateId={id}
                  title={t(`cvEditor.templates.${id}.name`)}
                />
                <span className="template-gallery__overlay">
                  {t("cvEditor.gallery.useTemplate")}
                </span>
              </div>
              <div className="template-gallery__meta">
                <div className="template-gallery__meta-top">
                  <h3>{t(`cvEditor.templates.${id}.name`)}</h3>
                  {id === "modern" ? (
                    <span className="template-gallery__badge">{t("cvEditor.templates.modern.tag")}</span>
                  ) : (
                    <span className="template-gallery__style">{TEMPLATE_META[id].styleLabel}</span>
                  )}
                </div>
                <p>{t(`cvEditor.templates.${id}.desc`)}</p>
              </div>
            </button>
          </article>
        ))}
      </div>

      {visibleIds.length === 0 ? (
        <p className="template-gallery__empty">{t("cvEditor.gallery.noTemplates")}</p>
      ) : null}
    </div>
  );
}
