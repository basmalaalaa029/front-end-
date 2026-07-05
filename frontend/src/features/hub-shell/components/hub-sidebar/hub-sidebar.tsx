import { Link, NavLink, useLocation } from "react-router-dom";
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { HubIcon } from "@/features/hub-shell/components/hub-icon";
import { BrandLogo } from "@/shared/components/brand-logo";
import {
  isCvCreatorRoute,
  useCvCreatorPath,
} from "@/features/cv-editor/lib/cv-creator-routing";

const NAV = [
  { label: "CV Creator", icon: "file-text", key: "cv-creator" as const },
  { label: "Analysis", icon: "target", to: "/dashboard/analyzer" },
  { label: "Job Matching", icon: "briefcase", to: "/dashboard/jobs" },
  { label: "Interview Coach", icon: "mic", to: "/dashboard/interview" },
] as const;

export function HubSidebar({ brand: _brand = "CareerPilot" }: { brand?: string }) {
  const user = useAuthStore((s) => s.user);
  const { pathname } = useLocation();
  const cvCreatorPath = useCvCreatorPath();

  const initials =
    user?.name
      ?.split(/\s+/)
      .map((p) => p[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "—";

  return (
    <aside className="app-sidebar">
      <Link to="/" className="brand" style={{ textDecoration: "none", color: "inherit" }}>
        <BrandLogo variant="nav" />
      </Link>
      <nav>
        {NAV.map((item) => {
          const to = "key" in item ? cvCreatorPath : item.to;
          const isCvCreator = "key" in item;
          return (
            <NavLink
              key={"key" in item ? item.key : item.to}
              to={to}
              className={({ isActive }) =>
                "nav-item " +
                ((isCvCreator ? isCvCreatorRoute(pathname) : isActive) ? "is-active" : "")
              }
            >
              <HubIcon name={item.icon} size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
        <NavLink
          to="/dashboard"
          end
          className={({ isActive }) => "nav-item " + (isActive ? "is-active" : "")}
        >
          <HubIcon name="sparkles" size={18} />
          <span>Overview</span>
        </NavLink>
      </nav>
      <div className="sidebar-foot">
        <div className="user-row">
          <div className="user-av">{initials}</div>
          <div className="user-meta">
            <div className="user-name">{user?.name ?? "Guest"}</div>
            <div className="user-sub">{user?.email ?? "Sign in to sync"}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
