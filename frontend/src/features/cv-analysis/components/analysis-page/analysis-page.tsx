import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import "@ui/ui_kits/cv-analysis/analysis.css";
import { HubHeader, HubIcon } from "@/features/hub-shell";
import { useI18n } from "@/features/i18n";
import { getDraftAnalysisFile, cvTextToAnalysisFile, formatCvFileSize } from "@/features/cv-analysis/lib/draft-for-analysis";
import { resolveAnalysisContextFromFile, hasDetectedCvContext } from "@/features/cv-analysis/lib/resolve-cv-context";
import { runAnalysisUploadAsync } from "@/features/cv-analysis/lib/cv-analysis-api";
import type { AnalysisFileSource } from "@/features/cv-analysis/lib/cv-analysis-api";
import { CvAnalysisApiError } from "@/features/cv-analysis/lib/cv-analysis-api";
import { CvAgentClientError } from "@/shared/lib/cv-agent-client";
import {
  loadAnalysisCache,
  saveAnalysisCache,
  clearActiveAnalysisSession,
  loadActiveAnalysisSession,
  pollAnalysisJob,
  resumeAnalysisAsync,
} from "@/features/cv-analysis/lib/cv-analysis-api";
import { logAnalysisStage } from "@/features/cv-analysis/lib/map-analysis-result";
import { takePendingAnalysisFile } from "@/features/cv-analysis/lib/pending-upload";
import type {
  AnalysisIssue,
  AnalysisJobResponse,
  AnalysisNavigationState,
  CvAnalysisResult,
  SectionCritique,
} from "@/features/cv-analysis/types";

type AnalysisFormInputs = {
  jobDescription: string;
  targetRole: string;
  company: string;
};

const EMPTY_INPUTS: AnalysisFormInputs = {
  jobDescription: "",
  targetRole: "Target role",
  company: "",
};

function CvFileCard({
  file,
  source,
  onReplace,
  disabled,
}: {
  file: File;
  source: AnalysisFileSource;
  onReplace: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="cv-file-card">
      <div className="cv-file-icon" aria-hidden>
        <HubIcon name="file-text" size={22} />
      </div>
      <div className="cv-file-meta-block">
        <div className="cv-file-name">{file.name}</div>
        <div className="cv-file-meta">
          {formatCvFileSize(file.size)}
          {" · "}
          {source === "editor" ? "Generated in CV editor" : "Uploaded from your device"}
        </div>
      </div>
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        disabled={disabled}
        onClick={onReplace}
      >
        Replace file
      </button>
    </div>
  );
}

function scoreLabel(score: number): string {
  if (score >= 85) return "Match · Strong";
  if (score >= 70) return "Match · Good";
  if (score >= 55) return "Match · Moderate";
  return "Match · Needs work";
}

function subscoresFromResult(r: CvAnalysisResult) {
  return [
    { label: "Clarity", value: r.clarity_score },
    { label: "Structure", value: r.structure_score },
    { label: "Impact", value: r.impact_score },
    { label: "Skills relevance", value: r.skills_relevance_score },
    { label: "ATS readiness", value: r.ats_readiness_score },
  ];
}

function ScoreHero({ result }: { result: CvAnalysisResult }) {
  const { t } = useI18n();
  const score = result.overall_score;
  const ats = result.ats_score ?? result.ats_readiness_score;
  const hr = result.hr_score ?? result.overall_score;
  const subs = subscoresFromResult(result);
  const R = 38;
  const C = 2 * Math.PI * R;
  const off = C - (score / 100) * C;

  return (
    <div className="score-hero">
      <div className="score-trio">
        <div className="score-mini">
          <div className="n">{score}</div>
          <div className="l">{t("analysis.overallScore")}</div>
        </div>
        <div className="score-mini">
          <div className="n">{ats}</div>
          <div className="l">{t("analysis.atsScore")}</div>
        </div>
        <div className="score-mini">
          <div className="n">{hr}</div>
          <div className="l">{t("analysis.hrScore")}</div>
        </div>
      </div>
      <div className="score-ring">
        <svg className="ring-svg" viewBox="0 0 96 96">
          <circle className="bg" cx={48} cy={48} r={R} fill="none" strokeWidth={8} />
          <circle
            className="fg"
            cx={48}
            cy={48}
            r={R}
            fill="none"
            strokeWidth={8}
            strokeDasharray={C}
            strokeDashoffset={off}
          />
        </svg>
        <div>
          <div className="score-num">
            {score}
            <span style={{ fontSize: 18, color: "var(--moss-300)" }}>/100</span>
          </div>
          <div className="score-label">{scoreLabel(score)}</div>
        </div>
      </div>
      <div className="score-verdict">{result.verdict}</div>
      <p style={{ fontSize: 12, color: "var(--fg-tertiary)", marginTop: 8 }}>
        {t("analysis.ensembleHint")}
      </p>
      <div className="sub-scores">
        {subs.map((s) => (
          <div key={s.label} className="sub">
            <div className="n">{s.value}</div>
            <div className="l">{s.label}</div>
            <div className="bar">
              <i style={{ width: `${s.value}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CritCard({
  section,
  status,
  summary,
  quote,
  fix,
}: SectionCritique) {
  const cls = status === "pass" ? "status-pass" : status === "warn" ? "status-warn" : "status-fail";
  const lbl = status === "pass" ? "Strong" : status === "warn" ? "Needs work" : "Gap";
  return (
    <div className="crit-card">
      <div className="crit-head">
        <div className="title">
          <HubIcon name="file-text" size={16} />
          {section}
        </div>
        <span className={"status-pill " + cls}>{lbl}</span>
      </div>
      <div className="crit-body">{summary}</div>
      {quote ? <div className="crit-quote">&ldquo;{quote}&rdquo;</div> : null}
      {fix ? (
        <div className="crit-fix">
          <div className="label">
            <HubIcon name="sparkles" size={11} stroke={2} /> Recommended rewrite
          </div>
          <div style={{ color: "var(--fg-primary)" }}>{fix}</div>
        </div>
      ) : null}
    </div>
  );
}

function resolveIssues(result: CvAnalysisResult): AnalysisIssue[] {
  if (result.issues?.length) return result.issues;
  const weaknesses = result.weaknesses ?? [];
  const suggestions = result.improvement_suggestions ?? [];
  const rewrites = result.rewrite_suggestions ?? [];
  const triples: Array<[string, string, string]> = [];
  for (let i = 0; i < weaknesses.length; i++) {
    const problem = (weaknesses[i] ?? "").trim();
    if (!problem || problem.toLowerCase().startsWith("judge output could not be parsed")) {
      continue;
    }
    triples.push([
      problem,
      (suggestions[i] ?? "").trim(),
      (rewrites[i] ?? "").trim(),
    ]);
  }
  return triples.map(([problem, recommendation, rewrite], i) => ({
    id: i + 1,
    title: problem.split(".")[0]?.trim().slice(0, 72) || "Needs improvement",
    problem,
    detail: "",
    recommendation:
      recommendation || "Update that part of your CV, then run the analysis again.",
    rewrite: rewrite || undefined,
    severity: i < 2 ? "gap" : "warn",
  }));
}

function IssuesRecommendations({ result }: { result: CvAnalysisResult }) {
  const { t } = useI18n();
  const issues = resolveIssues(result);
  const hasStrengths = result.strengths.length > 0;
  const isPolishMode = result.overall_score >= 80 && issues.every((i) => i.severity === "warn");
  const sectionFeedback = result.section_critiques.filter(
    (c) =>
      !/^Strength \d+$/i.test(c.section) &&
      c.section !== "Overall",
  );

  if (!hasStrengths && issues.length === 0 && sectionFeedback.length === 0) {
    return (
      <div className="ir-panel card" style={{ padding: 20, color: "var(--fg-secondary)", fontSize: 13 }}>
        {t("analysis.noIssuesReturned")}
      </div>
    );
  }

  return (
    <div className="ir-panel">
      {hasStrengths ? (
        <section className="ir-block ir-block--strengths">
          <h3 className="ir-heading">
            <HubIcon name="check-circle-2" size={16} stroke={2} />
            What&apos;s working well
          </h3>
          <ul className="ir-list">
            {result.strengths.map((item) => (
              <li key={item} className="ir-list-item ir-list-item--pass">
                {item}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {issues.length > 0 ? (
        <section className="ir-block ir-block--pairs">
          <h3 className="ir-heading">
            <HubIcon name={isPolishMode ? "sparkles" : "alert-triangle"} size={16} stroke={2} />
            {isPolishMode ? t("analysis.recommendationsTitle") : t("analysis.issuesTitle")}
            <span className="ir-count">{issues.length}</span>
          </h3>
          <p className="ir-lead">
            {isPolishMode ? t("analysis.recommendationsLead") : t("analysis.issuesLead")}
          </p>
          <div className="ir-pairs-list">
            {issues.map((issue) => (
              <article key={issue.id} className="ir-pair-card">
                <div className="ir-pair-head">
                  <span className="ir-pair-num">{issue.id}</span>
                  <div className="ir-pair-titles">
                    <h4 className="ir-pair-title">{issue.title}</h4>
                    <span
                      className={
                        "status-pill " +
                        (issue.severity === "gap" ? "status-fail" : "status-warn")
                      }
                    >
                      {issue.severity === "gap" ? t("analysis.severityGap") : t("analysis.severityWarn")}
                    </span>
                  </div>
                </div>

                <div className="ir-pair-section ir-pair-section--issue">
                  <div className="ir-pair-label">
                    <HubIcon name="alert-triangle" size={12} stroke={2} />
                    {t("analysis.whatsWrong")}
                  </div>
                  <p className="ir-pair-summary">{issue.problem}</p>
                </div>

                <div className="ir-pair-section ir-pair-section--fix">
                  <div className="ir-pair-label">
                    <HubIcon name="sparkles" size={12} stroke={2} />
                    {t("analysis.whatToDo")}
                  </div>
                  <p className="ir-pair-rec">{issue.recommendation}</p>
                  {issue.detail ? (
                    <p className="ir-pair-detail" style={{ marginTop: 8 }}>
                      {issue.detail}
                    </p>
                  ) : null}
                </div>

                {issue.rewrite ? (
                  <div className="ir-pair-section ir-pair-section--rewrite">
                    <div className="ir-pair-label">
                      <HubIcon name="file-text" size={12} stroke={2} />
                      {t("analysis.exampleWording")}
                    </div>
                    <p className="ir-pair-rewrite">{issue.rewrite}</p>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {sectionFeedback.length > 0 ? (
        <section className="ir-block ir-block--sections">
          <h3 className="ir-heading">
            <HubIcon name="file-text" size={16} stroke={2} />
            Section-by-section notes
          </h3>
          {sectionFeedback.map((c, i) => (
            <CritCard key={`${c.section}-${i}`} {...c} />
          ))}
        </section>
      ) : null}
    </div>
  );
}

export default function AnalysisPage() {
  const { t } = useI18n();
  const location = useLocation();
  const navigate = useNavigate();

  const [inputs, setInputs] = useState<AnalysisFormInputs>(EMPTY_INPUTS);
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [fileSource, setFileSource] = useState<AnalysisFileSource | null>(null);
  const [result, setResult] = useState<CvAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [showInputs, setShowInputs] = useState(true);
  const fileRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const initRef = useRef(false);
  const attachCvFile = useCallback(
    async (file: File, source: AnalysisFileSource): Promise<AnalysisFormInputs | null> => {
      setCvFile(file);
      setFileSource(source);
      const ctx = await resolveAnalysisContextFromFile(file, source);
      const next: AnalysisFormInputs = {
        targetRole: ctx.targetRole,
        company: ctx.company,
        jobDescription: ctx.jobDescription,
      };
      setInputs((prev) => {
        if (source === "upload") {
          return {
            ...prev,
            targetRole:
              next.targetRole !== "Target role" ? next.targetRole : "Target role",
            company: next.company,
            jobDescription: next.jobDescription,
          };
        }
        return {
          ...prev,
          ...next,
          targetRole: next.targetRole !== "Target role" ? next.targetRole : prev.targetRole,
          company: next.company || prev.company,
          jobDescription: next.jobDescription || prev.jobDescription,
        };
      });
      const detected = hasDetectedCvContext(ctx);
      return detected ? next : null;
    },
    [],
  );

  const applyInputs = useCallback((next: AnalysisFormInputs) => {
    setInputs(next);
  }, []);

  const handleAnalysisStatus = useCallback((status: AnalysisJobResponse) => {
    setShowInputs(false);
    if (status.status === "processing") {
      logAnalysisStage(status.stage, status.elapsed_s);
    }
  }, []);

  const finishAnalysis = useCallback(
    (data: CvAnalysisResult, form: AnalysisFormInputs, file: File, source: AnalysisFileSource) => {
      setCvFile(file);
      setFileSource(source);
      setResult(data);
      setShowInputs(false);
      setInputs((prev) => ({
        ...prev,
        targetRole: data.target_role || prev.targetRole,
        company: data.company || prev.company,
        jobDescription: data.job_description || prev.jobDescription,
      }));
      saveAnalysisCache(data, {
        ...form,
        fileName: file.name,
        fileSource: source,
      });
      clearActiveAnalysisSession();
      toast.success(`ATS analysis complete (${data.latency_ms}ms)`);
    },
    [],
  );

  const runAnalysisWithFile = useCallback(
    async (
      file: File,
      form: AnalysisFormInputs,
      source: AnalysisFileSource,
    ) => {
      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;

      setLoading(true);
      setResult(null);
      try {
        const data = await runAnalysisUploadAsync(
          file,
          {
            jobDescription: form.jobDescription,
            targetRole: form.targetRole,
            company: form.company,
            signal: ac.signal,
          },
          undefined,
          handleAnalysisStatus,
        );
        finishAnalysis(data, form, file, source);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        if (
          err instanceof CvAnalysisApiError ||
          err instanceof CvAgentClientError
        ) {
          if (err.status === 401) {
            toast.error(t("analysis.sessionExpired"));
          } else {
            toast.error(err.message);
          }
          return;
        }
        const msg = err instanceof Error ? err.message : t("analysis.analysisFailed");
        if (msg.includes("fetch") || msg.includes("Failed") || msg.includes("Network")) {
          toast.error(t("analysis.serviceUnavailable"));
        } else {
          toast.error(msg);
        }
      } finally {
        setLoading(false);
      }
    },
    [finishAnalysis, handleAnalysisStatus, t],
  );

  const runAnalysis = useCallback(() => {
    if (!cvFile || !fileSource) {
      toast.error(t("analysis.chooseFile"));
      fileRef.current?.click();
      return;
    }
    void runAnalysisWithFile(cvFile, inputs, fileSource);
  }, [cvFile, fileSource, inputs, runAnalysisWithFile, t]);

  const uploadCvFile = useCallback(
    async (
      file: File,
      opts: Partial<AnalysisFormInputs> = {},
      source: AnalysisFileSource = "upload",
    ) => {
      const form: AnalysisFormInputs = {
        jobDescription: opts.jobDescription ?? inputs.jobDescription,
        targetRole: opts.targetRole ?? inputs.targetRole,
        company: opts.company ?? inputs.company,
      };
      await runAnalysisWithFile(file, form, source);
    },
    [inputs.company, inputs.jobDescription, inputs.targetRole, runAnalysisWithFile],
  );

  const resumeInFlightAnalysis = useCallback(
    async (jobId: string) => {
      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;
      setLoading(true);
      setResult(null);
      try {
        const data = await resumeAnalysisAsync(jobId, ac.signal, handleAnalysisStatus);
        const draft = getDraftAnalysisFile();
        const file = cvFile ?? draft?.file;
        const source = fileSource ?? draft?.inputs.fileSource ?? "editor";
        if (!file) {
          setResult(data);
          clearActiveAnalysisSession();
          saveAnalysisCache(data, inputs);
          toast.success(`ATS analysis complete (${data.latency_ms}ms)`);
          return;
        }
        finishAnalysis(data, inputs, file, source);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        clearActiveAnalysisSession();
        if (err instanceof CvAnalysisApiError || err instanceof CvAgentClientError) {
          toast.error(err.message);
          return;
        }
        const msg = err instanceof Error ? err.message : t("analysis.analysisFailed");
        toast.error(
          msg.includes("fetch") || msg.includes("Failed") || msg.includes("Network")
            ? t("analysis.serviceUnavailable")
            : msg,
        );
      } finally {
        setLoading(false);
      }
    },
    [cvFile, fileSource, finishAnalysis, handleAnalysisStatus, inputs, t],
  );

  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;

    const nav = location.state as AnalysisNavigationState | null | undefined;

    if (nav?.autoUpload) {
      navigate(location.pathname, { replace: true, state: null });
      const file = takePendingAnalysisFile();
      if (file) {
        void (async () => {
          const resolved = await attachCvFile(file, nav.fileSource ?? "upload");
          const form: AnalysisFormInputs = {
            jobDescription: nav.jobDescription || resolved?.jobDescription || "",
            targetRole: nav.targetRole && nav.targetRole !== "Target role"
              ? nav.targetRole
              : resolved?.targetRole || "Target role",
            company: nav.company || resolved?.company || "",
          };
          applyInputs(form);
          void uploadCvFile(file, form, nav.fileSource ?? "upload");
        })();
      } else {
        toast.error(t("analysis.noFile"));
        fileRef.current?.click();
      }
      return;
    }

    if (nav?.cvText?.trim()) {
      const form: AnalysisFormInputs = {
        jobDescription: nav.jobDescription ?? "",
        targetRole: nav.targetRole ?? "Target role",
        company: nav.company ?? "",
      };
      const file = cvTextToAnalysisFile(nav.cvText, form.targetRole);
      void (async () => {
        const resolved = await attachCvFile(file, "editor");
        const merged = { ...form, ...resolved };
        applyInputs(merged);
        if (nav.autoRun) {
          void runAnalysisWithFile(file, merged, "editor");
        }
      })();
      navigate(location.pathname, { replace: true, state: null });
      return;
    }

    const draft = getDraftAnalysisFile();
    if (draft) {
      void attachCvFile(draft.file, "editor").then((resolved) => {
        applyInputs({ ...draft.inputs, ...resolved });
      });
      return;
    }

    const cached = loadAnalysisCache();
    if (cached) {
      setResult(cached.result);
      applyInputs(cached.inputs);
      setShowInputs(false);
      const restoredDraft = getDraftAnalysisFile();
      if (restoredDraft && cached.inputs.fileSource === "editor") {
        void attachCvFile(restoredDraft.file, "editor");
      }
      return;
    }

    const activeJob = loadActiveAnalysisSession();
    if (activeJob) {
      void (async () => {
        try {
          const peek = await pollAnalysisJob(activeJob);
          if (peek.status === "failed") {
            clearActiveAnalysisSession();
            toast.error(peek.error ?? t("analysis.previousFailed"));
            return;
          }
          if (peek.status === "ready" && peek.result) {
            clearActiveAnalysisSession();
            const { mapApiResultToCvAnalysis } = await import(
              "@/features/cv-analysis/lib/map-analysis-result"
            );
            setResult(mapApiResultToCvAnalysis(peek.result, inputs));
            setShowInputs(false);
            return;
          }
          void resumeInFlightAnalysis(activeJob);
        } catch (err) {
          clearActiveAnalysisSession();
          if (
            err instanceof CvAnalysisApiError ||
            (err instanceof CvAgentClientError && err.status === 404)
          ) {
            toast.error(t("analysis.sessionExpiredUpload"));
          }
        }
      })();
    }
  }, [
    applyInputs,
    attachCvFile,
    location.pathname,
    location.state,
    navigate,
    resumeInFlightAnalysis,
    runAnalysisWithFile,
    uploadCvFile,
    t,
  ]);

  const handleFilePick = (file: File) => {
    void attachCvFile(file, "upload");
  };

  const targetLabel = result
    ? `vs ${result.target_role}`
    : `vs ${inputs.targetRole}`;

  return (
    <>
      <HubHeader
        title="Analysis"
        sub={loading ? t("analysis.analyzing") : targetLabel}
        right={
          <>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={loading}
              onClick={() => setShowInputs((v) => !v)}
            >
              <HubIcon name="file-text" size={14} stroke={2} />
              {showInputs ? "Hide inputs" : "Edit inputs"}
            </button>
            {loading ? (
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => abortRef.current?.abort()}
              >
                Cancel
              </button>
            ) : null}
            <button
              type="button"
              className="btn btn-secondary"
              disabled={loading}
              onClick={() => void runAnalysis()}
            >
              <HubIcon name="refresh-ccw" size={14} stroke={2} />
              {loading ? "Analyzing…" : "Re-run"}
            </button>
          </>
        }
      />

      <div className="analysis-layout">
        {showInputs ? (
          <div
            className="card analysis-form"
            style={{
              marginBottom: 20,
              padding: 18,
              display: "grid",
              gap: 16,
            }}
          >
            <div>
              <label style={{ fontSize: 12, fontWeight: 600 }}>{t("analysis.targetRoleLabel")}</label>
              <input
                className="field-input"
                style={{ width: "100%", marginTop: 4, padding: 8, borderRadius: 8, border: "1px solid var(--border-subtle)" }}
                value={inputs.targetRole}
                onChange={(e) => setInputs((s) => ({ ...s, targetRole: e.target.value }))}
                placeholder={t("analysis.targetRolePlaceholder")}
              />
            </div>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600 }}>{t("analysis.yourCvLabel")}</label>
              {cvFile && fileSource ? (
                <CvFileCard
                  file={cvFile}
                  source={fileSource}
                  disabled={loading}
                  onReplace={() => fileRef.current?.click()}
                />
              ) : (
                <div className="cv-file-empty">
                  <HubIcon name="folder-open" size={28} />
                  <p>{t("analysis.noCvSelected")}</p>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    disabled={loading}
                    onClick={() => fileRef.current?.click()}
                  >
                    {t("analysis.uploadCv")}
                  </button>
                </div>
              )}
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.docx,.doc,.txt"
                hidden
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFilePick(f);
                  e.target.value = "";
                }}
              />
            </div>
            <div>
              <button type="button" className="btn btn-ai" disabled={loading} onClick={() => void runAnalysis()}>
                <HubIcon name="sparkles" size={14} stroke={2} />
                {loading ? t("analysis.analyzing") : t("analysis.runAnalysis")}
              </button>
            </div>
          </div>
        ) : null}

        {loading ? (
          <div className="card analysis-loading" role="status" aria-live="polite">
            <p>{t("analysis.analyzing")}</p>
            <p className="analysis-loading__hint">{t("analysis.analyzingHint")}</p>
          </div>
        ) : null}

        {result ? (
          <>
            <div className="target-bar">
              <HubIcon name="target" size={18} />
              <div>
                <div className="label">Target role</div>
                <div className="role">{result.target_role}</div>
              </div>
              {result.company ? (
                <>
                  <div style={{ width: 1, height: 28, background: "var(--border-subtle)" }} />
                  <div>
                    <div className="label">Company</div>
                    <div className="company">{result.company}</div>
                  </div>
                </>
              ) : null}
            </div>

            <div className="analysis-grid">
              <div>
                <ScoreHero result={result} />
              </div>
              <div>
                <IssuesRecommendations result={result} />
              </div>
            </div>
          </>
        ) : loading ? null : (
          <div className="card analysis-empty-state">
            <p>{t("analysis.emptyState")}</p>
            <p className="analysis-empty-state__hint">{t("analysis.emptyStateHint")}</p>
          </div>
        )}
      </div>
    </>
  );
}
