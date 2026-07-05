import { useEffect, useMemo, useState } from "react";
import { NavLink } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { HubHeader, HubIcon } from "@/features/hub-shell";
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { useI18n } from "@/features/i18n";
import { HUB_LAST_WORKSPACE_KEY } from "@/features/hub-shell/lib/hub-session";
import { useCvCreatorPath } from "@/features/cv-editor/lib/cv-creator-routing";
import "./dashboard-overview.css";

function dayStamp() {
  const d = new Date();
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
}

function hashToRange(seed: string, min: number, max: number) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (Math.imul(31, h) + seed.charCodeAt(i)) >>> 0;
  }
  return min + (h % (max - min + 1));
}

const MODULES = [
  {
    to: "/dashboard/editor",
    svc: "cvEditor" as const,
    icon: "file-text" as const,
    accent: "var(--moss-600)",
    statusKey: "dashboard.hub.statusEditor" as const,
  },
  {
    to: "/dashboard/analyzer",
    svc: "analyzer" as const,
    icon: "target" as const,
    accent: "var(--clay-600)",
    statusKey: "dashboard.hub.statusAnalyzer" as const,
  },
  {
    to: "/dashboard/jobs",
    svc: "jobMatcher" as const,
    icon: "briefcase" as const,
    accent: "var(--moss-700)",
    statusKey: "dashboard.hub.statusJobs" as const,
  },
  {
    to: "/dashboard/interview",
    interview: true as const,
    icon: "mic" as const,
    accent: "var(--moss-500)",
    statusKey: "dashboard.hub.statusInterview" as const,
  },
];

const CONTINUE_LABEL_PATHS: Record<string, "home.f1t" | "dashboard.services.analyzer.title" | "dashboard.services.jobMatcher.title" | "home.f4t"> =
  {
    "/dashboard/editor": "home.f1t",
    "/dashboard/analyzer": "dashboard.services.analyzer.title",
    "/dashboard/jobs": "dashboard.services.jobMatcher.title",
    "/dashboard/interview": "home.f4t",
  };

function greetingKey(hour: number): "dashboard.hub.greetingMorning" | "dashboard.hub.greetingAfternoon" | "dashboard.hub.greetingEvening" {
  if (hour < 12) return "dashboard.hub.greetingMorning";
  if (hour < 17) return "dashboard.hub.greetingAfternoon";
  return "dashboard.hub.greetingEvening";
}

export default function DashboardPage() {
  const { t, isRtl } = useI18n();
  const user = useAuthStore((s) => s.user);
  const cvCreatorPath = useCvCreatorPath();
  const [lastWorkspace, setLastWorkspace] = useState<string | null>(null);

  useEffect(() => {
    try {
      setLastWorkspace(sessionStorage.getItem(HUB_LAST_WORKSPACE_KEY));
    } catch {
      setLastWorkspace(null);
    }
  }, []);

  const seed = `${user?._id ?? user?.email ?? "anon"}-${dayStamp()}`;

  const metrics = useMemo(() => {
    const cvPct = hashToRange(`${seed}-cv`, 52, 94);
    const atsScore = hashToRange(`${seed}-ats`, 62, 91);
    const jobsN = hashToRange(`${seed}-jobs`, 0, 6);
    const sessionsN = hashToRange(`${seed}-iv`, 0, 4);
    return { cvPct, atsScore, jobsN, sessionsN };
  }, [seed]);

  const firstName = user?.name?.split(/\s+/)[0] ?? t("dashboard.welcomeGuest");
  const hour = new Date().getHours();
  const greet = t(greetingKey(hour));

  const signedSub = user?.email
    ? t("dashboard.hub.signedInAs", { email: user.email })
    : t("dashboard.hub.signedInGuest");

  const continueLabelKey = lastWorkspace ? CONTINUE_LABEL_PATHS[lastWorkspace] : undefined;
  const continueTitle = continueLabelKey ? t(continueLabelKey) : "";

  return (
    <>
      <HubHeader title={t("dashboard.hub.title")} sub={signedSub} />
      <section className="dash-overview" aria-label={t("dashboard.hub.title")}>
        <div className="dash-overview__hero">
          <span className="eyebrow">{t("dashboard.eyebrow")}</span>
          <p className="dash-overview__greeting">
            {greet} <strong>{firstName}</strong> — {t("dashboard.sub")}
          </p>
        </div>

        <div className="dash-overview__stats">
          <div className="dash-overview__stat">
            <div className="dash-overview__stat-label">{t("dashboard.hub.statCv")}</div>
            <div className="dash-overview__stat-value">{metrics.cvPct}%</div>
            <div className="dash-overview__stat-bar" aria-hidden>
              <span style={{ width: `${metrics.cvPct}%` }} />
            </div>
          </div>
          <div className="dash-overview__stat">
            <div className="dash-overview__stat-label">{t("dashboard.hub.statAts")}</div>
            <div className="dash-overview__stat-value">{metrics.atsScore}%</div>
            <div className="dash-overview__stat-bar" aria-hidden>
              <span style={{ width: `${metrics.atsScore}%` }} />
            </div>
          </div>
          <div className="dash-overview__stat">
            <div className="dash-overview__stat-label">{t("dashboard.hub.statJobs")}</div>
            <div className="dash-overview__stat-value">{metrics.jobsN}</div>
            <div className="dash-overview__stat-bar" aria-hidden>
              <span
                style={{
                  width: `${metrics.jobsN === 0 ? 8 : Math.min(100, 20 + metrics.jobsN * 14)}%`,
                }}
              />
            </div>
          </div>
        </div>

        {lastWorkspace && continueLabelKey ? (
          <NavLink to={lastWorkspace} className="dash-overview__continue card">
            <div className="dash-overview__continue-kicker">{t("dashboard.hub.continueKicker")}</div>
            <div className="dash-overview__continue-title">{continueTitle}</div>
            <div className="dash-overview__continue-meta">{t("dashboard.hub.continueMeta")}</div>
            <span className="dash-overview__continue-cta">
              {t("dashboard.hub.continueCta")}
              <ChevronRight size={16} strokeWidth={2} style={{ transform: isRtl ? "scaleX(-1)" : undefined }} aria-hidden />
            </span>
          </NavLink>
        ) : null}

        <NavLink to="/dashboard/jobs" className="dash-overview__tip card">
          <div className="dash-overview__tip-title">{t("dashboard.tipTitle")}</div>
          <p className="dash-overview__tip-body">{t("dashboard.tipBody")}</p>
          <span className="dash-overview__tip-cta">{t("dashboard.tipCta")} →</span>
        </NavLink>

        <h2 className="eyebrow" style={{ margin: "0 0 12px" }}>
          {t("dashboard.servicesLabel")}
        </h2>
        <div className="dash-overview__grid">
          {MODULES.map((m) => {
            const badge = m.interview ? t("home.badgePractice") : t(`dashboard.services.${m.svc}.badge`);
            const title = m.interview ? t("home.f4t") : t(`dashboard.services.${m.svc}.title`);
            const desc = m.interview ? t("home.f4d") : t(`dashboard.services.${m.svc}.desc`);
            const cta = m.interview ? t("home.ctaInterview") : t(`dashboard.services.${m.svc}.cta`);

            const status =
              m.to === "/dashboard/editor"
                ? t(m.statusKey, { pct: String(metrics.cvPct) })
                : m.to === "/dashboard/analyzer"
                  ? t(m.statusKey, { score: String(metrics.atsScore) })
                  : m.to === "/dashboard/jobs"
                    ? t(m.statusKey, { n: String(metrics.jobsN) })
                    : t(m.statusKey, { n: String(metrics.sessionsN) });

            return (
              <NavLink
                key={m.to}
                to={m.to === "/dashboard/editor" ? cvCreatorPath : m.to}
                className="dash-overview__card card"
                style={{ ["--card-accent" as string]: m.accent }}
              >
                <div className="dash-overview__card-top">
                  <span className="dash-overview__card-badge">{badge}</span>
                  <HubIcon name={m.icon} size={22} />
                </div>
                <div className="dash-overview__card-title">{title}</div>
                <div className="dash-overview__card-desc">{desc}</div>
                <div className="dash-overview__card-status">{status}</div>
                <span className="dash-overview__card-cta">
                  {cta}
                  <ChevronRight size={16} strokeWidth={2} style={{ transform: isRtl ? "scaleX(-1)" : undefined }} aria-hidden />
                </span>
              </NavLink>
            );
          })}
        </div>
      </section>
    </>
  );
}
