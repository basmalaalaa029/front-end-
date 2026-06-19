import { Link } from "react-router-dom";
import { FileText, LayoutDashboard, Plus } from "lucide-react";
import { useAuthHydrated, useAuthStore } from "@/features/auth/stores/auth-store";
import { useRequireAuthNavigate } from "@/features/auth/lib/use-require-auth-navigate";

function userInitials(name: string | undefined): string {
  return (
    name
      ?.split(/\s+/)
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "—"
  );
}

export function LandingNav() {
  const requireAuth = useRequireAuthNavigate();
  const hydrated = useAuthHydrated();
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);

  return (
    <nav className="cf-nav">
      <Link to="/" className="cf-nav-logo">
        <span className="cf-logo-box" aria-hidden>
          <FileText size={18} strokeWidth={2} color="#fff" />
        </span>
        CareerPilot
      </Link>
      <div className="cf-nav-links">
        <button
          type="button"
          className="cf-nav-link"
          onClick={() => requireAuth("/dashboard/editor")}
        >
          Templates
        </button>
        <a className="cf-nav-link" href="#features">
          Features
        </a>
        <a className="cf-nav-link" href="#pricing">
          Pricing
        </a>
      </div>
      <div className="cf-nav-right">
        {!hydrated ? null : token ? (
          <>
            <Link className="btn-ghost" to="/dashboard">
              <LayoutDashboard size={16} strokeWidth={2} aria-hidden />
              Dashboard
            </Link>
            <Link className="cf-nav-user" to="/dashboard" title={user?.email ?? user?.name ?? "Dashboard"}>
              <span className="cf-nav-user-av">{userInitials(user?.name)}</span>
              <span className="cf-nav-user-name">{user?.name ?? "Account"}</span>
            </Link>
          </>
        ) : (
          <>
            <Link className="btn-ghost" to="/login">
              Log in
            </Link>
            <Link className="btn-primary" to="/register">
              <Plus size={16} strokeWidth={2} aria-hidden />
              Create CV — it&apos;s free
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
