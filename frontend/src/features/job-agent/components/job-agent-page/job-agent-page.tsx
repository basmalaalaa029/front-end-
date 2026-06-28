import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import "@ui/ui_kits/job-agent/agent.css";
import "@/features/hub-shell/components/workflow-pipeline-bar/workflow-pipeline-bar.css";
import { getPipelineCvInputs } from "@/features/cv-analysis/lib/pipeline-cv";
import {
  HubHeader,
  HubIcon,
  WorkflowPipelineBar,
  loadWorkflowCv,
  saveWorkflowCv,
  saveWorkflowJobPick,
  setPipelineCvFile,
  takePendingJobFile,
  type InterviewNavigationState,
  type JobNavigationState,
} from "@/features/hub-shell";
import {
  useJobMatch,
  useJobMatchUpload,
  useJobResults,
} from "@/features/job-agent/hooks/use-job-match";
import type { JobMatchStatus, MatchedJob, ScoreBreakdown } from "@/features/job-agent/types";

// ─── types ──────────────────────────────────────────────────────────────────

type JobCardData = {
  id: string;
  brand: string;
  logo: string;
  title: string;
  company: string;
  location: string;
  salary: string;
  match: number;
  why: string;
  source: string;
  url: string;
  posted: string;
  score_breakdown: ScoreBreakdown;
  matched_skills: string[];
  missing_skills: string[];
  description: string;
};

function toCardJob(j: MatchedJob): JobCardData {
  return {
    id: j.id,
    brand: j.brand,
    logo: j.logo || j.company.charAt(0),
    title: j.title,
    company: j.company,
    location: j.location,
    salary: j.salary,
    match: j.match_score,
    why: j.why,
    source: j.source ?? "",
    url: j.url ?? "",
    posted: j.posted ?? "",
    score_breakdown: j.score_breakdown ?? {},
    matched_skills: j.matched_skills ?? [],
    missing_skills: j.missing_skills ?? [],
    description: j.description ?? "",
  };
}

// ─── small shared components ─────────────────────────────────────────────────

function SourceBadge({ source }: { source: string }) {
  if (!source) return null;
  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.04em",
        padding: "2px 6px",
        borderRadius: 4,
        background: "var(--bone-100)",
        color: "var(--fg-tertiary)",
        marginLeft: 6,
        textTransform: "uppercase",
      }}
    >
      {source}
    </span>
  );
}

function ScoreBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div style={{ marginBottom: 8 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 11,
          marginBottom: 3,
          color: "var(--fg-secondary)",
        }}
      >
        <span>{label}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>
          {value}/{max}
        </span>
      </div>
      <div
        style={{
          height: 4,
          background: "var(--border-subtle)",
          borderRadius: 4,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background:
              pct >= 70 ? "var(--moss-500)" : pct >= 40 ? "var(--bone-500)" : "var(--clay-500)",
            borderRadius: 4,
            transition: "width 0.4s ease",
          }}
        />
      </div>
    </div>
  );
}

// ─── CV Upload zone ───────────────────────────────────────────────────────────

function CvUploadZone({
  onStart,
  loading,
}: {
  onStart: (file: File | null, targetRole: string) => void;
  loading: boolean;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [targetRole, setTargetRole] = useState("");
  const [drag, setDrag] = useState(false);

  const hasDraftCv = Boolean(getPipelineCvInputs()?.cvText);

  function handleFiles(files: FileList | null) {
    if (!files?.length) return;
    const f = files[0];
    const ok = /\.(pdf|docx?|txt)$/i.test(f.name);
    if (!ok) {
      toast.error("Please upload a PDF, DOCX, or TXT file.");
      return;
    }
    setFile(f);
  }

  return (
    <div className="cv-upload-wrap">
      <div className="cv-upload-card">
        <h2>Match your CV to live jobs</h2>
        <p className="sub">
          Upload your CV — we'll fetch thousands of live roles and rank them by fit.
        </p>

        {/* Drop zone */}
        <div
          className={"cv-drop-zone" + (drag ? " drag-over" : "")}
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            handleFiles(e.dataTransfer.files);
          }}
        >
          {file ? (
            <span className="file-chosen">
              <HubIcon name="file-check-2" size={16} stroke={2} />
              {file.name}
            </span>
          ) : (
            <>
              <HubIcon name="upload-cloud" size={32} stroke={1.5} className="drop-icon" />
              <span className="drop-label">Drop your CV here or click to browse</span>
              <span className="drop-hint">PDF, DOCX, or TXT · max 10 MB</span>
            </>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            style={{ display: "none" }}
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>

        {/* Optional fields */}
        <div className="cv-upload-fields">
          <div>
            <label>Target role (optional)</label>
            <input
              type="text"
              placeholder="e.g. Frontend Engineer, Data Scientist…"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
            />
          </div>
        </div>

        <button
          type="button"
          className="cv-upload-submit"
          disabled={loading || !file}
          onClick={() => file && onStart(file, targetRole)}
        >
          {loading ? (
            <>
              <HubIcon name="loader-2" size={16} stroke={2} />
              Searching…
            </>
          ) : (
            <>
              <HubIcon name="search" size={16} stroke={2} />
              Find matching jobs
            </>
          )}
        </button>

        {hasDraftCv && (
          <p className="cv-upload-or">
            Or{" "}
            <a onClick={() => onStart(null, targetRole)}>
              use CV from the editor
            </a>
          </p>
        )}
      </div>
    </div>
  );
}

// ─── Job card ─────────────────────────────────────────────────────────────────

function JobCard({
  job,
  selected,
  onClick,
}: {
  job: JobCardData;
  selected: boolean;
  onClick: () => void;
}) {
  const matchCls = job.match >= 80 ? "strong" : job.match >= 60 ? "medium" : "weak";
  return (
    <div
      className={"job-card " + (selected ? "selected" : "")}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
    >
      <div className="job-row">
        <div className={"job-logo " + job.brand}>{job.logo}</div>
        <div className="job-body">
          <div className="job-title">
            {job.title}
            <SourceBadge source={job.source} />
          </div>
          <div className="job-meta">
            <span>
              <HubIcon name="building-2" size={12} stroke={2} />
              {job.company}
            </span>
            <span>
              <HubIcon name="map-pin" size={12} stroke={2} />
              {job.location}
            </span>
            {job.salary && (
              <span>
                <HubIcon name="dollar-sign" size={12} stroke={2} />
                {job.salary}
              </span>
            )}
            {job.posted && (
              <span>
                <HubIcon name="calendar" size={12} stroke={2} />
                {job.posted}
              </span>
            )}
          </div>
        </div>
        <span className={"match-pill " + matchCls}>{job.match}% match</span>
      </div>
      <div className="job-why">
        <HubIcon name="sparkles" size={13} stroke={2} className="ai" />
        <span>{job.why}</span>
      </div>
    </div>
  );
}

// ─── Agent activity drawer ────────────────────────────────────────────────────

function AgentDrawer({ jobCount, loading }: { jobCount: number; loading: boolean }) {
  const tasks = [
    {
      state: loading ? ("active" as const) : ("done" as const),
      icon: loading ? ("loader-2" as const) : ("check-circle-2" as const),
      label: "Scoring roles against your CV",
      when: loading ? "now" : "done",
    },
    {
      state: "done" as const,
      icon: "check-circle-2" as const,
      label: `Ranked ${jobCount} curated matches`,
      when: jobCount ? "just now" : "—",
    },
    {
      state: "done" as const,
      icon: "check-circle-2" as const,
      label: "Live job board integration active",
      when: "live",
    },
  ];
  return (
    <div className="agent-drawer">
      <div className="drawer-head">
        <span className="pulse" />
        <h3>Agent activity</h3>
      </div>
      {tasks.map((t, i) => (
        <div key={i} className={"task " + t.state}>
          <HubIcon name={t.icon} size={14} stroke={2} className="ico" />
          <span className="label">{t.label}</span>
          <span className="when">{t.when}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Context / detail panel ───────────────────────────────────────────────────

function ContextPanel({
  job,
  onPracticeInterview,
}: {
  job: JobCardData | null;
  onPracticeInterview: (job: JobCardData) => void;
}) {
  if (!job) return null;
  const bd = job.score_breakdown;
  return (
    <>
      <AgentDrawer jobCount={1} loading={false} />

      <div className="context-section">
        <h4>Selected role</h4>
        <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 2 }}>{job.title}</div>
        <div style={{ fontSize: 13, color: "var(--fg-secondary)" }}>
          {job.company} · {job.location}
        </div>
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              marginTop: 8,
              fontSize: 12,
              fontWeight: 600,
              color: "var(--purple)",
              textDecoration: "none",
            }}
          >
            <HubIcon name="external-link" size={12} stroke={2} />
            Apply now
          </a>
        )}
        <button
          type="button"
          className="btn btn-ai"
          style={{ marginTop: 12, width: "100%" }}
          onClick={() => onPracticeInterview(job)}
        >
          <HubIcon name="mic" size={14} stroke={2} />
          Practice interview for this role
        </button>
      </div>

      <div className="context-section">
        <h4>Why we matched you</h4>
        <p style={{ fontSize: 13, color: "var(--fg-primary)", lineHeight: 1.55, margin: 0 }}>
          {job.why}
        </p>
      </div>

      <div className="context-section">
        <h4>Score breakdown</h4>
        <ScoreBar label="Semantic fit" value={bd.semantic ?? 0} max={35} />
        <ScoreBar label="Hard skills" value={bd.hard_skills ?? 0} max={25} />
        <ScoreBar label="Seniority" value={bd.seniority ?? 0} max={20} />
        <ScoreBar label="Role / title" value={bd.role_title ?? 0} max={15} />
        <ScoreBar label="Soft & certs" value={bd.soft_certs ?? 0} max={5} />
        <div className="kv" style={{ marginTop: 8 }}>
          <span className="k">Overall fit</span>
          <span className="v">{job.match}%</span>
        </div>
      </div>

      {job.matched_skills.length > 0 && (
        <div className="context-section">
          <h4>Matched skills</h4>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
            {job.matched_skills.map((s) => (
              <span
                key={s}
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 999,
                  background: "var(--moss-100)",
                  color: "var(--moss-800)",
                  fontWeight: 500,
                }}
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {job.missing_skills.length > 0 && (
        <div className="context-section">
          <h4>Skills to strengthen</h4>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
            {job.missing_skills.map((s) => (
              <span
                key={s}
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 999,
                  background: "var(--clay-50)",
                  color: "var(--clay-700)",
                  fontWeight: 500,
                }}
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function JobAgentPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const autoStartedRef = useRef(false);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [jobs, setJobs] = useState<JobCardData[]>([]);
  const [selected, setSelected] = useState<JobCardData | null>(null);
  const [started, setStarted] = useState(false);
  const [matchStage, setMatchStage] = useState<string | null>(null);

  const handleMatchStatus = useCallback((status: JobMatchStatus) => {
    setMatchStage(status.stage ?? null);
  }, []);

  const matchMutation = useJobMatch();
  const uploadMutation = useJobMatchUpload();
  const resultsQuery = useJobResults(sessionId, handleMatchStatus);

  const handleStart = useCallback(
    async (file: File | null, targetRole: string) => {
      setStarted(true);
      try {
        let resp;
        if (file) {
          setPipelineCvFile(file);
          resp = await uploadMutation.mutateAsync({ file, targetRole });
        } else {
          const draft = getPipelineCvInputs();
          if (!draft?.cvText) {
            toast.error("No CV found. Please upload a file or continue from CV editor / analysis.");
            setStarted(false);
            return;
          }
          resp = await matchMutation.mutateAsync({
            cvText: draft.cvText,
            targetRole: targetRole || draft.targetRole,
          });
        }
        setSessionId(resp.session_id);
        setMatchStage("parsing");
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Job match failed";
        toast.error(msg);
        setStarted(false);
      }
    },
    [matchMutation, uploadMutation],
  );

  useEffect(() => {
    if (autoStartedRef.current) return;
    const nav = location.state as JobNavigationState | null | undefined;
    if (!nav?.autoStart) return;

    autoStartedRef.current = true;
    navigate(location.pathname, { replace: true, state: null });

    const pendingFile = takePendingJobFile();
    const wf = loadWorkflowCv();
    const role = nav.targetRole || wf?.targetRole || "";

    void handleStart(pendingFile, role);
  }, [handleStart, location.pathname, location.state, navigate]);

  const continueToInterview = useCallback(
    (job: JobCardData) => {
      const wf = loadWorkflowCv();
      const jobDescription =
        job.description.trim() ||
        [
          `${job.title} at ${job.company}`,
          job.why,
          job.matched_skills.length
            ? `Key matched skills: ${job.matched_skills.join(", ")}`
            : "",
        ]
          .filter(Boolean)
          .join("\n\n");

      saveWorkflowJobPick({
        title: job.title,
        company: job.company,
        targetRole: job.title,
        jobDescription,
        url: job.url || undefined,
      });

      if (wf && jobDescription && !wf.jobDescription.trim()) {
        saveWorkflowCv({ ...wf, jobDescription });
      }

      const nav: InterviewNavigationState = {
        autoStart: true,
        targetRole: job.title,
      };
      navigate("/dashboard/interview", { state: nav });
    },
    [navigate],
  );

  useEffect(() => {
    if (resultsQuery.data?.jobs) {
      const mapped = resultsQuery.data.jobs.slice(0, 10).map(toCardJob);
      setJobs(mapped);
      if (mapped.length && !selected) setSelected(mapped[0]);
    }
  }, [resultsQuery.data, selected]);

  useEffect(() => {
    if (!resultsQuery.isError) return;
    const msg =
      resultsQuery.error instanceof Error
        ? resultsQuery.error.message
        : "Job match failed";
    toast.error(msg);
    setStarted(false);
    setSessionId(null);
    setMatchStage(null);
  }, [resultsQuery.isError, resultsQuery.error]);

  const stageLabel = matchStage
    ? matchStage.charAt(0).toUpperCase() + matchStage.slice(1)
    : "Starting";

  const loading =
    matchMutation.isPending || uploadMutation.isPending || resultsQuery.isFetching;
  const strongCount = jobs.filter((j) => j.match >= 80).length;

  // ── not started yet → show upload zone ──────────────────────────────────
  if (!started) {
    return (
      <>
        <HubHeader title="Job Agent" sub="Upload your CV to find matching live roles" />
        <WorkflowPipelineBar current="jobs" className="workflow-pipeline--inset" />
        <CvUploadZone onStart={handleStart} loading={loading} />
      </>
    );
  }

  // ── started → show results (or loading state) ────────────────────────────
  return (
    <>
      <HubHeader
        title="Job Agent"
        sub={
          loading
            ? `Matching your CV (${stageLabel})…`
            : `${jobs.length} roles · ${strongCount} strong matches`
        }
        right={
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setStarted(false);
              setJobs([]);
              setSelected(null);
              setSessionId(null);
              setMatchStage(null);
            }}
          >
            <HubIcon name="upload" size={14} stroke={2} />
            New CV
          </button>
        }
      />
      <WorkflowPipelineBar current="jobs" className="workflow-pipeline--inset" />
      <div className="agent-layout">
        <div className="agent-main">
          <div className="results-head">
            <h2>Ranked matches</h2>
            <span className="meta">
              {loading ? "Scoring against live job boards…" : "Sorted by composite fit score"}
            </span>
          </div>

          {loading && jobs.length === 0 ? (
            <div style={{ padding: "48px 24px", textAlign: "center", color: "var(--fg-secondary)" }}>
              <div style={{ animation: "spin 1s linear infinite", display: "inline-block", marginBottom: 12, color: "var(--purple)" }}>
                <HubIcon name="loader-2" size={28} stroke={1.5} />
              </div>
              <p style={{ margin: 0, fontSize: 14 }}>Fetching live jobs and analysing your CV…</p>
              <p style={{ margin: "6px 0 0", fontSize: 12 }}>This usually takes 20–60 seconds</p>
            </div>
          ) : jobs.length === 0 ? (
            <p style={{ padding: 24, color: "var(--fg-secondary)" }}>
              No matches found. Try uploading a different CV or changing the target role.
            </p>
          ) : (
            <div className="job-list">
              {jobs.map((j) => (
                <JobCard
                  key={j.id}
                  job={j}
                  selected={selected?.id === j.id}
                  onClick={() => setSelected(j)}
                />
              ))}
            </div>
          )}
        </div>
        <div className="agent-context">
          <ContextPanel job={selected} onPracticeInterview={continueToInterview} />
        </div>
      </div>
    </>
  );
}
