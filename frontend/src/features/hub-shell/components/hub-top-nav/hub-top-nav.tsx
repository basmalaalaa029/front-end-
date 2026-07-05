import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { HubIcon } from "@/features/hub-shell/components/hub-icon";
import { BrandLogo } from "@/shared/components/brand-logo";
import {
  isCvCreatorRoute,
  useCvCreatorPath,
} from "@/features/cv-editor/lib/cv-creator-routing";
import { rehydrateUserScopedStores } from "@/features/cv-editor/stores/rehydrate-user-stores";

const NAV = [
  { label: "CV Creator", icon: "file-text", key: "cv-creator" },
  { label: "Analysis", icon: "target", to: "/dashboard/analyzer" },
  { label: "Job Matching", icon: "briefcase", to: "/dashboard/jobs" },
  { label: "Interview Coach", icon: "mic", to: "/dashboard/interview" },
] as const;

export function HubTopNav({ brand: _brand = "CareerPilot" }: { brand?: string }) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const cvCreatorPath = useCvCreatorPath();

  const initials =
    user?.name
      ?.split(/\s+/)
      .map((p) => p[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "—";

  const handleLogout = () => {
    logout();
    rehydrateUserScopedStores();
    navigate("/login");
  };

  return (
    <header className="app-topnav">
      <Link to="/" className="brand app-topnav-brand">
        <BrandLogo variant="nav" />
      </Link>

      <nav className="app-topnav-links" aria-label="Workspace">
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
              <HubIcon name={item.icon} size={16} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
        <NavLink
          to="/dashboard"
          end
          className={({ isActive }) => "nav-item " + (isActive ? "is-active" : "")}
        >
          <HubIcon name="sparkles" size={16} />
          <span>Overview</span>
        </NavLink>
      </nav>

      <div className="app-topnav-actions">
        <div className="app-topnav-user" title={user?.email ?? user?.name ?? "Account"}>
          <span className="user-av">{initials}</span>
          <span className="app-topnav-user-name">{user?.name ?? "Guest"}</span>
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-sm app-topnav-logout"
          onClick={handleLogout}
          aria-label="Log out"
        >
          <LogOut size={15} strokeWidth={1.75} aria-hidden />
          <span className="app-topnav-logout-label">Log out</span>
        </button>
      </div>
    </header>
  );
}
