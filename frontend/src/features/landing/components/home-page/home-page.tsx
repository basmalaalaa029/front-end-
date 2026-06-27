import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles,
  FileText,
  FilePlus,
  Pencil,
  AlertCircle,
  Mic,
  LayoutGrid,
  Target,
  Briefcase,
  ArrowRight,
  Upload,
} from "lucide-react";
import { setPendingAnalysisFile } from "@/features/cv-analysis/lib/pending-upload";
import type { AnalysisNavigationState } from "@/features/cv-analysis/types";
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { useRequireAuthNavigate } from "@/features/auth/lib/use-require-auth-navigate";
import { LandingNav } from "@/features/landing/components/landing-nav";
import { LandingFooter } from "@/features/landing/components/landing-footer";
import { useI18n } from "@/features/i18n";
import type { TemplateId } from "@/features/cv-editor/data/cv-templates";
import { TemplateLivePreview } from "@/features/cv-editor/components/cv-template-picker-page/template-live-preview";

const LANDING_TEMPLATE_IDS = ["modern", "executive", "tech"] as const satisfies readonly TemplateId[];

const LANDING_TEMPLATE_BADGES: Record<
  (typeof LANDING_TEMPLATE_IDS)[number],
  { badge: string; badgeClass: string; featured?: boolean }
> = {
  modern: { badge: "Popular", badgeClass: "cf-badge-popular", featured: true },
  executive: { badge: "New", badgeClass: "cf-badge-new" },
  tech: { badge: "Clean", badgeClass: "cf-badge-clean" },
};

export default function Home() {
  const { t } = useI18n();
  const token = useAuthStore((s) => s.token);
  const navigate = useNavigate();
  const requireAuth = useRequireAuthNavigate();
  const uploadRef = useRef<HTMLInputElement>(null);

  const startUploadFlow = () => {
    if (token) {
      uploadRef.current?.click();
      return;
    }
    requireAuth("/dashboard/analyzer", { state: { autoUpload: true } });
  };

  const onUploadChosen = (file: File) => {
    setPendingAnalysisFile(file);
    const navState: AnalysisNavigationState = { autoUpload: true };
    navigate("/dashboard/analyzer", { state: navState });
  };

  return (
    <div className="cf-landing">
      <LandingNav />

      <input
        ref={uploadRef}
        type="file"
        accept=".pdf,.docx,.doc,.txt"
        hidden
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          onUploadChosen(file);
          e.target.value = "";
        }}
      />

      <div className="cf-hero">
        <div className="cf-hero-left">
          <div className="cf-hero-eyebrow">
            <Sparkles size={13} strokeWidth={2} aria-hidden />
            AI-powered career platform
          </div>
          <h1>
            Build a CV that
            <br />
            gets you <em>hired</em>
          </h1>
          <p className="cf-hero-sub">
            Create a professional CV in minutes, match with the right jobs, and practice your
            interview with an AI coach — all in one place.
          </p>
          <div className="cf-hero-actions">
            <button type="button" className="btn-primary" onClick={() => requireAuth("/dashboard/editor")}>
              <FilePlus size={16} strokeWidth={2} aria-hidden />
              Build my CV
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => requireAuth("/dashboard/analyzer")}
            >
              <Target size={16} strokeWidth={2} aria-hidden />
              Analyze my CV
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => requireAuth("/dashboard/interview")}
            >
              <Mic size={16} strokeWidth={2} aria-hidden />
              Practice interview
            </button>
          </div>
          <div className="cf-hero-trust">
            <div className="cf-avatars">
              <div className="cf-av" style={{ background: "#EEEDFE", color: "#3C3489" }}>AM</div>
              <div className="cf-av" style={{ background: "#E1F5EE", color: "#085041" }}>SR</div>
              <div className="cf-av" style={{ background: "#E6F1FB", color: "#0C447C" }}>KM</div>
              <div className="cf-av" style={{ background: "#FAEEDA", color: "#633806" }}>LH</div>
            </div>
            Trusted by 50,000+ job seekers worldwide
          </div>
        </div>

        <div className="cf-hero-visual">
          <div className="cf-cv-card">
            <div className="cf-ai-pill">
              <Sparkles size={12} strokeWidth={2} aria-hidden />
              AI-enhanced
            </div>
            <div className="cf-cv-head">
              <div className="cf-cv-avatar">AM</div>
              <div>
                <div className="cf-cv-name">Ahmed Mohamed</div>
                <div className="cf-cv-role">Senior Software Engineer</div>
                <div className="cf-cv-contact">
                  <span>Cairo, Egypt</span>
                  <span>ahmed@email.com</span>
                </div>
              </div>
            </div>
            <div className="cf-cv-section-lbl">Experience</div>
            <div className="cf-cv-exp-item">
              <div className="cf-cv-exp-title">Senior Frontend Developer</div>
              <div className="cf-cv-exp-company">Vodafone Egypt · 2022–Present</div>
              <div className="cf-cv-line" style={{ width: "90%" }} />
              <div className="cf-cv-line" style={{ width: "70%" }} />
            </div>
            <div className="cf-cv-exp-item">
              <div className="cf-cv-exp-title">React Developer</div>
              <div className="cf-cv-exp-company">Instabug · 2020–2022</div>
              <div className="cf-cv-line" style={{ width: "80%" }} />
              <div className="cf-cv-line" style={{ width: "60%" }} />
            </div>
            <div className="cf-cv-skill-section">
              <div className="cf-cv-section-lbl">Skills</div>
              {[
                { name: "React", pct: 95 },
                { name: "Python", pct: 88 },
                { name: "Node.js", pct: 80 },
              ].map((s) => (
                <div key={s.name} className="cf-cv-skill-row">
                  <div className="cf-cv-skill-label">
                    <span>{s.name}</span>
                    <span>{s.pct}%</span>
                  </div>
                  <div className="cf-cv-skill-track">
                    <div className="cf-cv-skill-fill" style={{ width: `${s.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="cf-floating-badge b1">
            <div className="cf-badge-icon" style={{ background: "#E1F5EE" }}>🎯</div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 500 }}>95% job match</div>
              <div style={{ fontSize: 11, color: "var(--text-faint)" }}>Vodafone Egypt</div>
            </div>
          </div>
          <div className="cf-floating-badge b2">
            <div className="cf-badge-icon" style={{ background: "#EEEDFE" }}>🎤</div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 500 }}>Interview ready</div>
              <div style={{ fontSize: 11, color: "var(--text-faint)" }}>AI coach feedback</div>
            </div>
          </div>
        </div>
      </div>

      <div className="cf-stats">
        <div className="cf-stats-inner">
          <div className="cf-stat-item">
            <div className="cf-stat-num">50k+</div>
            <div className="cf-stat-lbl">CVs created</div>
          </div>
          <div className="cf-stat-item">
            <div className="cf-stat-num">92%</div>
            <div className="cf-stat-lbl">Interview callback rate</div>
          </div>
          <div className="cf-stat-item">
            <div className="cf-stat-num">3 min</div>
            <div className="cf-stat-lbl">Average build time</div>
          </div>
        </div>
      </div>

      <section className="cf-section" id="templates">
        <div className="section-eyebrow">Templates</div>
        <h2 className="section-h2">Choose a professional template</h2>
        <p className="section-sub">
          Pick from beautifully designed, recruiter-approved CV templates. Fully customisable in any
          colour.
        </p>
        <div className="cf-tmpl-grid">
          {LANDING_TEMPLATE_IDS.map((id) => {
            const meta = LANDING_TEMPLATE_BADGES[id];
            return (
              <button
                key={id}
                type="button"
                className={`cf-tmpl-card${meta.featured ? " featured" : ""}`}
                onClick={() => requireAuth(`/dashboard/editor/create/${id}`)}
              >
                <div className="cf-tmpl-preview">
                  <TemplateLivePreview
                    templateId={id}
                    title={t(`cvEditor.templates.${id}.name`)}
                  />
                </div>
                <div className="cf-tmpl-footer">
                  <span className="cf-tmpl-name">{t(`cvEditor.templates.${id}.name`)}</span>
                  <span className={`cf-tmpl-badge ${meta.badgeClass}`}>{meta.badge}</span>
                </div>
              </button>
            );
          })}
        </div>
        <div style={{ marginTop: 20 }}>
          <button type="button" className="btn-secondary" onClick={() => requireAuth("/dashboard/editor")}>
            View all templates
            <ArrowRight size={16} strokeWidth={2} aria-hidden />
          </button>
        </div>
      </section>

      <section className="cf-section cf-section--surface">
        <div className="cf-section-inner">
          <div className="section-eyebrow">How it works</div>
          <h2 className="section-h2">Ready in 3 simple steps</h2>
          <p className="section-sub">No design skills needed. Our AI guides you through every section.</p>
          <div className="cf-steps-grid">
            <button
              type="button"
              className="step-card"
              onClick={() => requireAuth("/dashboard/editor")}
            >
              <span className="cf-step-num-big">01</span>
              <div className="cf-step-icon">
                <Pencil size={22} strokeWidth={2} aria-hidden />
              </div>
              <div className="cf-step-title">Fill in your details</div>
              <div className="cf-step-desc">
                Enter your personal info, experience, education and skills. Our AI suggests
                improvements as you type.
              </div>
            </button>
            <button
              type="button"
              className="step-card"
              onClick={() => requireAuth("/dashboard/jobs")}
            >
              <span className="cf-step-num-big">02</span>
              <div className="cf-step-icon teal">
                <AlertCircle size={22} strokeWidth={2} aria-hidden />
              </div>
              <div className="cf-step-title">Match with the right jobs</div>
              <div className="cf-step-desc">
                Our AI analyses your CV and instantly matches you with relevant opportunities and
                shows your match score.
              </div>
            </button>
            <button
              type="button"
              className="step-card"
              onClick={() => requireAuth("/dashboard/interview")}
            >
              <span className="cf-step-num-big">03</span>
              <div className="cf-step-icon blue">
                <Mic size={22} strokeWidth={2} aria-hidden />
              </div>
              <div className="cf-step-title">Practice your interview</div>
              <div className="cf-step-desc">
                Get interview-ready with our AI coach. Practice real questions and receive instant
                feedback on your answers.
              </div>
            </button>
          </div>
        </div>
      </section>

      <section className="cf-section" id="features">
        <div className="section-eyebrow">Features</div>
        <h2 className="section-h2">Everything you need to land the job</h2>
        <p className="section-sub">Four powerful tools built into one seamless experience.</p>
        <div className="cf-features-grid">
          <button type="button" className="feat-card" onClick={() => requireAuth("/dashboard/editor")}>
            <div className="cf-feat-icon p">
              <FileText size={22} strokeWidth={2} aria-hidden />
            </div>
            <div className="cf-feat-title">AI CV builder</div>
            <div className="cf-feat-desc">
              Build and export a polished, recruiter-ready CV with AI-assisted content suggestions
              and one-click PDF export.
            </div>
          </button>
          <button type="button" className="feat-card" onClick={() => requireAuth("/dashboard/jobs")}>
            <div className="cf-feat-icon t">
              <Target size={22} strokeWidth={2} aria-hidden />
            </div>
            <div className="cf-feat-title">Smart job matching</div>
            <div className="cf-feat-desc">
              Instantly see which jobs fit your profile with a match score and skill-gap analysis to
              guide your next steps.
            </div>
          </button>
          <button type="button" className="feat-card" onClick={() => requireAuth("/dashboard/interview")}>
            <div className="cf-feat-icon b">
              <Mic size={22} strokeWidth={2} aria-hidden />
            </div>
            <div className="cf-feat-title">AI interview coach</div>
            <div className="cf-feat-desc">
              Practice behavioral and technical questions with real-time AI feedback — walk into
              every interview confident.
            </div>
          </button>
          <button type="button" className="feat-card" onClick={startUploadFlow}>
            <div className="cf-feat-icon a">
              <LayoutGrid size={22} strokeWidth={2} aria-hidden />
            </div>
            <div className="cf-feat-title">CV analysis & upload</div>
            <div className="cf-feat-desc">
              Upload your existing CV for instant ATS scoring, gap analysis, and tailored
              recommendations.
            </div>
          </button>
        </div>
      </section>

      <section className="cf-section" style={{ paddingTop: 0 }}>
        <div className="section-eyebrow">Testimonials</div>
        <h2 className="section-h2">What our users say</h2>
        <p className="section-sub" style={{ marginBottom: 32 }}>Real people, real results.</p>
        <div className="cf-testi-grid">
          {[
            {
              text: "I built my CV in under 10 minutes and got called for an interview the very next week. The AI suggestions made all the difference.",
              author: "Sara R.",
              role: "Marketing Manager, Cairo",
            },
            {
              text: "The job matching feature showed me roles I never would have found on my own. Landed my dream job within a month.",
              author: "Karim M.",
              role: "Software Engineer, Dubai",
            },
            {
              text: "The virtual interview practice helped me feel prepared and calm. I finally stopped second-guessing my answers.",
              author: "Layla H.",
              role: "Business Analyst, Riyadh",
            },
          ].map((t) => (
            <div key={t.author} className="cf-testi-card">
              <div className="cf-stars">★★★★★</div>
              <div className="cf-testi-text">&ldquo;{t.text}&rdquo;</div>
              <div className="cf-testi-author">{t.author}</div>
              <div className="cf-testi-role">{t.role}</div>
            </div>
          ))}
        </div>
      </section>

      <div className="cf-cta-section" id="pricing">
        <div className="cf-cta-inner">
          <div className="cf-hero-eyebrow" style={{ display: "inline-flex", marginBottom: 16 }}>
            🚀 Start for free today
          </div>
          <h2>Your dream job is one CV away</h2>
          <p>Join 50,000+ professionals who built their careers with CareerPilot.</p>
          <div className="cf-cta-actions">
            <button type="button" className="btn-primary" onClick={() => requireAuth("/dashboard/editor")}>
              <FilePlus size={16} strokeWidth={2} aria-hidden />
              Create my free CV
            </button>
            <button type="button" className="btn-secondary" onClick={() => requireAuth("/dashboard/jobs")}>
              <Briefcase size={16} strokeWidth={2} aria-hidden />
              Find job matches
            </button>
            <button type="button" className="btn-secondary" onClick={() => requireAuth("/dashboard/interview")}>
              <Mic size={16} strokeWidth={2} aria-hidden />
              Practice interview
            </button>
            <button type="button" className="btn-secondary" onClick={startUploadFlow}>
              <Upload size={16} strokeWidth={2} aria-hidden />
              Upload & analyze CV
            </button>
          </div>
        </div>
      </div>

      <LandingFooter />
    </div>
  );
}
