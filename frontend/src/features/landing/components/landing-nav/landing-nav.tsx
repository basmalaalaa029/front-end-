import { Link } from "react-router-dom";
import { FileText, Plus } from "lucide-react";
import { useRequireAuthNavigate } from "@/features/auth/lib/use-require-auth-navigate";

export function LandingNav() {
  const requireAuth = useRequireAuthNavigate();

  return (
    <nav className="cf-nav">
      <Link to="/" className="cf-nav-logo">
        <span className="cf-logo-box" aria-hidden>
          <FileText size={18} strokeWidth={2} color="#fff" />
        </span>
        CareerForge
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
        <Link className="btn-ghost" to="/login">
          Log in
        </Link>
        <Link className="btn-primary" to="/register">
          <Plus size={16} strokeWidth={2} aria-hidden />
          Create CV — it&apos;s free
        </Link>
      </div>
    </nav>
  );
}
