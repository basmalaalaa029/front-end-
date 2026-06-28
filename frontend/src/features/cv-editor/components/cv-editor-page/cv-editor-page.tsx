import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import "@ui/ui_kits/cv-creator/creator.css";
import { HubHeader, HubIcon } from "@/features/hub-shell";
import { useI18n } from "@/features/i18n";
import { isTemplateId } from "@/features/cv-editor/data/cv-templates";
import { useCvDraftStore } from "@/features/cv-editor/stores";
import { CvSectionEditor } from "./cv-section-editor";
import {
  startGeneration,
  waitForCompletion,
  getResult,
  mapGenerationProgressMessage,
  type CvAgentScores,
  type CvAgentSessionStatus,
} from "@/features/cv-editor/lib/cv-agent-api";
import { buildGeneratePayload, cvDataToMarkdown, enhancedDataToCvData } from "@/features/cv-editor/lib/cv-to-profile";
import type { AnalysisNavigationState } from "@/features/cv-analysis/types";
import { cvTextToAnalysisFile, setPendingAnalysisFile } from "@/features/cv-analysis";
import {
  buildHtml,
  buildHtmlFromMarkdown,
  printCvWithTemplate,
  printMarkdownWithTemplate,
} from "@/features/cv-editor/lib/cv-print";
import type { TemplateId } from "@/features/cv-editor/data/cv-templates";

/** Live preview — same HTML/CSS as Export / Download (WYSIWYG). */
function TemplateCvPreview({ html, title }: { html: string; title: string }) {
  return (
    <iframe
      title={title}
      srcDoc={html}
      style={{
        width: "100%",
        minHeight: 980,
        border: "1px solid var(--border-subtle)",
        borderRadius: 10,
        background: "#fff",
        display: "block",
      }}
    />
  );
}

// ─── Sections Panel ───────────────────────────────────────────────────────────

function SectionsPanel({
  active,
  onPick,
  sections,
  heading,
}: {
  active: string;
  onPick: (id: string) => void;
  sections: { id: string; icon: string; label: string }[];
  heading: string;
}) {
  return (
    <div className="sections-panel">
      <h4>{heading}</h4>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {sections.map((s) => (
          <div
            key={s.id}
            className={"section-block " + (active === s.id ? "is-active" : "")}
            onClick={() => onPick(s.id)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && onPick(s.id)}
          >
            <HubIcon name="grip-vertical" size={14} className="grip" />
            <HubIcon name={s.icon} size={15} />
            <span>{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Job Description Panel ────────────────────────────────────────────────────

function JobDescPanel({
  value,
  onChange,
  open,
  onToggle,
}: {
  value: string;
  onChange: (v: string) => void;
  open: boolean;
  onToggle: () => void;
}) {
  const { t } = useI18n();
  return (
    <div className="sections-panel" style={{ padding: "10px 14px" }}>
      <button
        type="button"
        onClick={onToggle}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: 0,
          fontSize: 12,
          fontWeight: 600,
          color: "var(--fg-secondary)",
          width: "100%",
          textAlign: "left",
        }}
      >
        <HubIcon name={open ? "chevron-down" : "chevron-right"} size={13} />
        <HubIcon name="file-text" size={13} />
        {t("cvEditor.gen.jobDescToggle")}
      </button>
      {open && (
        <div style={{ marginTop: 8 }}>
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={t("cvEditor.gen.jobDescPlaceholder")}
            rows={5}
            style={{
              width: "100%",
              fontSize: 12,
              lineHeight: 1.5,
              resize: "vertical",
              border: "1px solid var(--border-default, #d1d5db)",
              borderRadius: 8,
              padding: "8px 10px",
              background: "var(--surface-input, #fff)",
              color: "var(--fg-primary)",
              fontFamily: "inherit",
            }}
          />
          <p style={{ margin: "4px 0 0", fontSize: 11, color: "var(--fg-tertiary)" }}>
            {t("cvEditor.gen.jobDescHint")}
          </p>
        </div>
      )}
    </div>
  );
}

// ─── AI Result Panel ──────────────────────────────────────────────────────────

function AiResultPanel({
  scores,
  onDownload,
  isDownloading,
}: {
  scores: CvAgentScores;
  onDownload: () => void;
  isDownloading: boolean;
}) {
  const { t } = useI18n();
  return (
    <div className="sections-panel" style={{ padding: "12px 14px", fontSize: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
        <span style={{ color: "var(--ai-accent, #7c3aed)", display: "inline-flex" }}>
          <HubIcon name="sparkles" size={14} stroke={2} />
        </span>
        <h4 style={{ margin: 0, fontSize: 12, fontWeight: 700 }}>{t("cvEditor.gen.aiResultTitle")}</h4>
      </div>

      <ul style={{ listStyle: "none", padding: 0, margin: "0 0 10px", display: "grid", gap: 4 }}>
        <li style={{ display: "flex", justifyContent: "space-between" }}>
          <span>{t("cvEditor.gen.metricClarity")}</span>
          <ScorePill value={scores.clarity_score} />
        </li>
        <li style={{ display: "flex", justifyContent: "space-between" }}>
          <span>{t("cvEditor.gen.metricStructure")}</span>
          <ScorePill value={scores.structure_score} />
        </li>
        <li style={{ display: "flex", justifyContent: "space-between" }}>
          <span>{t("cvEditor.gen.metricImpact")}</span>
          <ScorePill value={scores.impact_score} />
        </li>
        <li style={{ display: "flex", justifyContent: "space-between" }}>
          <span>{t("cvEditor.gen.metricSkills")}</span>
          <ScorePill value={scores.skills_relevance_score} />
        </li>
        <li style={{ display: "flex", justifyContent: "space-between" }}>
          <span>{t("cvEditor.gen.metricAts")}</span>
          <ScorePill value={scores.ats_readiness_score} />
        </li>
      </ul>

      <button
        type="button"
        className="btn btn-primary"
        style={{ width: "100%", justifyContent: "center" }}
        onClick={onDownload}
        disabled={isDownloading}
      >
        <HubIcon
          name={isDownloading ? "loader-2" : "download"}
          size={14}
          stroke={2}
        />
        {isDownloading ? t("cvEditor.gen.downloadingAiPdf") : t("cvEditor.gen.downloadAiCv")}
      </button>
    </div>
  );
}

function ScorePill({ value }: { value: number }) {
  const color =
    value >= 80 ? "#22c55e" : value >= 60 ? "#f59e0b" : "#ef4444";
  return (
    <b style={{ color, fontVariantNumeric: "tabular-nums" }}>{value}</b>
  );
}

// ─── Preview Tab Bar ──────────────────────────────────────────────────────────

function PreviewTabs({
  active,
  onChange,
}: {
  active: "user" | "ai";
  onChange: (t: "user" | "ai") => void;
}) {
  const { t } = useI18n();
  return (
    <div
      style={{
        display: "flex",
        gap: 2,
        padding: "6px 8px 0",
        background: "var(--surface-secondary, #f8fafc)",
        borderBottom: "1px solid var(--border-default, #e2e8f0)",
      }}
    >
      {(["user", "ai"] as const).map((tab) => (
        <button
          key={tab}
          type="button"
          onClick={() => onChange(tab)}
          style={{
            padding: "5px 12px",
            fontSize: 12,
            fontWeight: 600,
            border: "none",
            borderRadius: "6px 6px 0 0",
            cursor: "pointer",
            background: active === tab ? "var(--surface-default, #fff)" : "transparent",
            color: active === tab ? "var(--fg-primary)" : "var(--fg-tertiary)",
            borderBottom: active === tab ? "2px solid var(--ai-accent, #7c3aed)" : "2px solid transparent",
            transition: "color .15s",
          }}
        >
          {tab === "ai" && (
          <span style={{ marginRight: 4, display: "inline-flex", verticalAlign: "-2px" }}>
            <HubIcon name="sparkles" size={12} />
          </span>
        )}
          {tab === "user" ? t("cvEditor.gen.userCvPreview") : t("cvEditor.gen.aiCvPreview")}
        </button>
      ))}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

type GenStage = "idle" | "submitting" | "running" | "downloading" | "done" | "failed";

export default function CvEditorPage() {
  const { t } = useI18n();
  const { templateId } = useParams<{ templateId: string }>();
  const navigate = useNavigate();

  const data = useCvDraftStore((s) => s.data);
  const setData = useCvDraftStore((s) => s.setData);
  const activeSection = useCvDraftStore((s) => s.activeSection);
  const setActiveSection = useCvDraftStore((s) => s.setActiveSection);
  const jobDescription = useCvDraftStore((s) => s.jobDescription);
  const setJobDescription = useCvDraftStore((s) => s.setJobDescription);
  const aiMarkdown = useCvDraftStore((s) => s.aiMarkdown);
  const setAiMarkdown = useCvDraftStore((s) => s.setAiMarkdown);
  const aiEnhancedData = useCvDraftStore((s) => s.aiEnhancedData);
  const setAiEnhancedData = useCvDraftStore((s) => s.setAiEnhancedData);
  const setLastTemplateId = useCvDraftStore((s) => s.setLastTemplateId);

  // AI generation state (ephemeral — not lost draft on navigation)
  const [genStage, setGenStage] = useState<GenStage>("idle");
  const [genMessage, setGenMessage] = useState<string>("");
  const [aiScores, setAiScores] = useState<CvAgentScores | null>(null);
  const [previewTab, setPreviewTab] = useState<"user" | "ai">("user");
  const [isDownloadingAi, setIsDownloadingAi] = useState(false);

  const [showJobDesc, setShowJobDesc] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const generatingRef = useRef(false);

  useEffect(() => {
    if (templateId && isTemplateId(templateId)) {
      setLastTemplateId(templateId);
    }
  }, [templateId, setLastTemplateId]);

  if (!templateId || !isTemplateId(templateId)) {
    return <Navigate to="/dashboard/editor" replace />;
  }

  const isBusy =
    genStage === "submitting" ||
    genStage === "running" ||
    genStage === "downloading";

  const stopGeneration = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setGenStage("idle");
    setGenMessage("");
  };

  const handleProgress = (status: { status: CvAgentSessionStatus; progress_msgs: string[] }) => {
    if (status.status === "running" || status.status === "pending") {
      setGenStage(status.status === "running" ? "running" : "submitting");
    }
    const lastMsg = status.progress_msgs[status.progress_msgs.length - 1];
    const key = mapGenerationProgressMessage(lastMsg, status.status);
    setGenMessage(t(`cvEditor.gen.${key}`));
  };

  /** Open Analysis with the current editor draft as a CV file. */
  const handleRunAnalysis = () => {
    if (isBusy) return;
    const cvText = cvDataToMarkdown(data).trim();
    if (cvText.length < 50) {
      toast.error(t("cvEditor.analysisTooShort"));
      return;
    }
    const targetRole =
      data.role.trim() ||
      data.education.map((e) => e.degree.trim()).find(Boolean) ||
      data.name.trim() ||
      "Target role";
    const file = cvTextToAnalysisFile(cvText, targetRole);
    setPendingAnalysisFile(file);
    const navState: AnalysisNavigationState = {
      jobDescription: jobDescription.trim(),
      targetRole,
      company: "",
      autoUpload: true,
      fileSource: "editor",
    };
    navigate("/dashboard/analyzer", { state: navState });
  };

  /** Export: render CV in the selected template and open the browser print dialog. */
  const handleExport = () => {
    if (isBusy) return;
    if (!data.name.trim()) {
      toast.error(t("cvEditor.gen.missingFields") + " " + t("cvEditor.fields.name"));
      return;
    }
    const tpl = isTemplateId(templateId) ? templateId : "modern";
    printCvWithTemplate(data, tpl);
    toast.success(t("cvEditor.gen.exportOpened"));
  };

  /** Generate AI CV: send to pipeline, show AI-improved result. */
  const handleGenerateAiCv = async () => {
    if (isBusy || generatingRef.current) return;
    const { payload, missing } = buildGeneratePayload(data, {
      jobDescription: jobDescription.trim() || undefined,
    });
    if (missing.length) {
      toast.error(t("cvEditor.gen.missingFields") + " " + missing.join(", "));
      return;
    }

    generatingRef.current = true;
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setAiScores(null);
    setAiMarkdown(null);
    setAiEnhancedData(null);
    setPreviewTab("user");
    setGenStage("submitting");
    setGenMessage(t("cvEditor.gen.starting"));

    let templateCv: string | undefined;

    try {
      const start = await startGeneration(payload, ctrl.signal);
      templateCv = start.template_cv;
      if (start.template_cv) {
        setAiMarkdown(start.template_cv);
        setAiEnhancedData(null);
        setPreviewTab("ai");
        toast(t("cvEditor.gen.templateReady"));
      }
      setGenMessage(t("cvEditor.gen.queued"));

      const final = await waitForCompletion(start.session_id, {
        signal: ctrl.signal,
        intervalMs: 2500,
        timeoutMs: 10 * 60 * 1000,
        onProgress: handleProgress,
      });

      if (final.status === "failed" && !templateCv) {
        console.error("[CV Agent] pipeline failed:", final.error);
        setGenStage("failed");
        setGenMessage(t("cvEditor.gen.failed"));
        toast.error(t("cvEditor.gen.failed"));
        return;
      }

      const result = await getResult(start.session_id, ctrl.signal);
      if (result.final_scores) setAiScores(result.final_scores);
      if (result.final_cv) {
        setAiMarkdown(result.final_cv);
        setPreviewTab("ai");
      }
      if (result.enhanced_data) {
        setAiEnhancedData(result.enhanced_data);
      } else if (!result.node_errors?.length) {
        setAiEnhancedData(null);
      }

      const aiFailed = Boolean(result.node_errors?.length);
      if (aiFailed) {
        toast(t("cvEditor.gen.aiPartial"), { icon: "⚠️" });
      } else {
        toast.success(t("cvEditor.gen.generatedReady"));
      }
      setGenStage("done");
      setGenMessage("");
    } catch (err) {
      if ((err as DOMException)?.name === "AbortError") {
        setGenStage("idle");
        setGenMessage("");
        return;
      }
      console.error("[CV Agent] generation error:", err);
      if (templateCv) {
        setAiMarkdown(templateCv);
        setPreviewTab("ai");
        setGenStage("done");
        setGenMessage("");
        toast(t("cvEditor.gen.aiPartial"), { icon: "⚠️" });
        return;
      }
      const timedOut =
        err instanceof Error && /timed out/i.test(err.message);
      const msg = timedOut ? t("cvEditor.gen.timedOut") : t("cvEditor.gen.failed");
      toast.error(msg);
      setGenStage("failed");
      setGenMessage(msg);
    } finally {
      generatingRef.current = false;
      abortRef.current = null;
    }
  };

  const aiCvData = useMemo(
    () => (aiEnhancedData ? enhancedDataToCvData(aiEnhancedData, data) : null),
    [aiEnhancedData, data],
  );

  /** Download AI CV using the same template as the picker (print → Save as PDF). */
  const handleDownloadAiCv = () => {
    if ((!aiMarkdown && !aiCvData) || isDownloadingAi) return;
    const tpl = templateId as TemplateId;
    setIsDownloadingAi(true);
    try {
      if (aiCvData) {
        printCvWithTemplate(aiCvData, tpl);
      } else if (aiMarkdown) {
        printMarkdownWithTemplate(aiMarkdown, tpl, {
          name: data.name,
          role: data.role,
          email: data.email,
          phone: data.phone,
          address: data.address,
          url: data.url,
        });
      }
      toast.success(t("cvEditor.gen.exportOpened"));
    } catch (err) {
      console.error("[CV Download]", err);
      toast.error(t("cvEditor.gen.failed"));
    } finally {
      setIsDownloadingAi(false);
    }
  };

  const previewHtml = useMemo(() => {
    const tpl = templateId as TemplateId;
    if (previewTab === "ai" && aiCvData) {
      return buildHtml(aiCvData, tpl);
    }
    if (previewTab === "ai" && aiMarkdown) {
      return buildHtmlFromMarkdown(aiMarkdown, tpl, {
        name: data.name,
        role: data.role,
        email: data.email,
        phone: data.phone,
        address: data.address,
        url: data.url,
      });
    }
    return buildHtml(data, tpl);
  }, [data, templateId, previewTab, aiMarkdown, aiCvData]);

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
    [t]
  );

  const headerTitle =
    data.name.trim() || data.role.trim()
      ? `${data.name.trim() || t("cvEditor.untitledName")} — ${data.role.trim() || t("cvEditor.untitledRole")}`
      : t("cvEditor.untitled");

  const score = useMemo(() => {
    let filled = 0;
    const total = 8;
    if (data.name.trim()) filled++;
    if (data.role.trim()) filled++;
    if (data.email.trim()) filled++;
    if (data.summary.trim()) filled++;
    if (data.experience.some((e) => e.title && e.company)) filled++;
    if (data.education.some((e) => e.university || e.degree)) filled++;
    if (data.skills.length) filled++;
    if (data.phone.trim() || data.address.trim() || data.url.trim()) filled++;
    return Math.min(99, 42 + Math.round((filled / total) * 55));
  }, [data]);

  return (
    <>
      <HubHeader
        title={headerTitle}
        sub={t("cvEditor.headerHint")}
        right={
          <>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => navigate("/dashboard/editor")}
              disabled={isBusy}
            >
              {t("cvEditor.changeTemplate")}
            </button>
            <span style={{ fontSize: 12, color: "var(--fg-tertiary)", display: "inline-flex", alignItems: "center", gap: 6 }}>
              <HubIcon name="check-circle-2" size={14} stroke={2} /> {t("cvEditor.saved")}
            </span>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleExport}
              disabled={isBusy}
              aria-busy={isBusy}
            >
              <HubIcon
                name={genStage === "downloading" && !aiMarkdown ? "loader-2" : "download"}
                size={14}
                stroke={2}
              />
              {genStage === "downloading" && !aiMarkdown
                ? t("cvEditor.gen.preparingPdf")
                : isBusy
                  ? t("cvEditor.gen.busy")
                  : t("cvEditor.export")}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleRunAnalysis}
              disabled={isBusy}
            >
              <HubIcon name="target" size={14} stroke={2} />
              {t("cvEditor.runAnalysis")}
            </button>
            <button
              type="button"
              className="btn btn-ai"
              onClick={handleGenerateAiCv}
              disabled={isBusy}
              aria-busy={isBusy}
            >
              <HubIcon name="sparkles" size={14} stroke={2} />
              {isBusy ? t("cvEditor.gen.busy") : t("cvEditor.generateAiCv")}
            </button>
          </>
        }
      />

      {/* Generation status banner */}
      {(isBusy || genStage === "failed") && (
        <div
          role="status"
          aria-live="polite"
          className={`cv-gen-banner${genStage === "failed" ? " is-error" : ""}`}
          style={{
            margin: "12px 28px 0",
            padding: "10px 14px",
            borderRadius: 10,
            border: "1px solid var(--border-default, #e5e7eb)",
            background: genStage === "failed" ? "rgba(239,68,68,0.08)" : "rgba(124,58,237,0.07)",
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 13,
            color: "var(--fg-secondary)",
          }}
        >
          <HubIcon
            name={genStage === "failed" ? "alert-triangle" : "loader-2"}
            size={16}
            stroke={2}
          />
          <span style={{ flex: 1 }}>
            {genStage === "failed"
              ? genMessage || t("cvEditor.gen.failed")
              : genMessage || t("cvEditor.gen.working")}
          </span>
          {isBusy && (
            <button type="button" className="btn btn-ghost btn-sm" onClick={stopGeneration}>
              {t("cvEditor.gen.cancel")}
            </button>
          )}
        </div>
      )}

      {/* Main 3-column layout */}
      <div className="creator-layout">
        {/* Left: CV preview canvas with optional AI tab */}
        <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          {aiMarkdown && (
            <PreviewTabs active={previewTab} onChange={setPreviewTab} />
          )}
          <TemplateCvPreview
            html={previewHtml}
            title={
              previewTab === "ai" && aiMarkdown
                ? t("cvEditor.gen.aiCvPreview")
                : t("cvEditor.gen.userCvPreview")
            }
          />
        </div>

        {/* Right: tools panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {/* Score card */}
          <div className="score-card">
            <div className="score-n">{aiScores?.overall_score ?? score}</div>
            <div className="score-l">
              {aiScores ? t("cvEditor.gen.aiScore") : t("cvEditor.readability")}
            </div>
            <span className="score-delta">
              {aiScores ? t("cvEditor.gen.scoreCalibrated") : t("cvEditor.scoreDelta")}
            </span>
          </div>

          {/* AI result panel (shown after generation completes) */}
          {aiScores && aiMarkdown && genStage === "done" && (
            <AiResultPanel
              scores={aiScores}
              onDownload={handleDownloadAiCv}
              isDownloading={isDownloadingAi}
            />
          )}

          {/* Scores breakdown (legacy — shown only when no markdown) */}
          {aiScores && !aiMarkdown && (
            <div
              className="sections-panel"
              style={{ marginTop: 12, padding: "12px 14px", fontSize: 12 }}
            >
              <h4 style={{ marginBottom: 8 }}>{t("cvEditor.gen.aiBreakdown")}</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 4 }}>
                <li>{t("cvEditor.gen.metricClarity")}: <b>{aiScores.clarity_score}</b></li>
                <li>{t("cvEditor.gen.metricStructure")}: <b>{aiScores.structure_score}</b></li>
                <li>{t("cvEditor.gen.metricImpact")}: <b>{aiScores.impact_score}</b></li>
                <li>{t("cvEditor.gen.metricSkills")}: <b>{aiScores.skills_relevance_score}</b></li>
                <li>{t("cvEditor.gen.metricAts")}: <b>{aiScores.ats_readiness_score}</b></li>
              </ul>
            </div>
          )}

          {/* Section navigator */}
          <SectionsPanel
            active={activeSection}
            onPick={setActiveSection}
            sections={[...sectionDefs]}
            heading={t("cvEditor.sectionsLabel")}
          />

          {/* Section form editor */}
          <CvSectionEditor active={activeSection} data={data} setData={setData} />

          {/* Job description (collapsible) */}
          <JobDescPanel
            value={jobDescription}
            onChange={setJobDescription}
            open={showJobDesc}
            onToggle={() => setShowJobDesc((v) => !v)}
          />
        </div>
      </div>
    </>
  );
}
