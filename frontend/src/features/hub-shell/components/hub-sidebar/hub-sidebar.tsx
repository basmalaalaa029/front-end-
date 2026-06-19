import { Link, NavLink } from "react-router-dom";
import { FileText } from "lucide-react";
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { HubIcon } from "@/features/hub-shell/components/hub-icon";

const NAV = [
  { label: "CV Creator", icon: "file-text", to: "/dashboard/editor" },
  { label: "Analysis", icon: "target", to: "/dashboard/analyzer" },
  { label: "Job Matching", icon: "briefcase", to: "/dashboard/jobs" },
  { label: "Interview Coach", icon: "mic", to: "/dashboard/interview" },
] as const;

export function HubSidebar({ brand = "CareerPilot" }: { brand?: string }) {
  const user = useAuthStore((s) => s.user);

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
        <span className="brand-mark" aria-hidden>
          <FileText size={18} strokeWidth={2} color="#fff" />
        </span>
        <span className="brand-name">{brand}</span>
      </Link>
      <nav>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => "nav-item " + (isActive ? "is-active" : "")}
          >
            <HubIcon name={item.icon} size={18} />
            <span>{item.label}</span>
          </NavLink>
        ))}
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
