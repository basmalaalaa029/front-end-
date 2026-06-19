import { Navigate, useLocation } from "react-router-dom";
import { useAuthHydrated, useAuthStore } from "@/features/auth/stores/auth-store";
import { getAuthReturnTarget } from "@/features/auth/lib/use-require-auth-navigate";

export default function GuestRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const hydrated = useAuthHydrated();
  const location = useLocation();

  if (!hydrated) {
    return (
      <div className="auth-session-loading" role="status" aria-live="polite">
        Loading…
      </div>
    );
  }

  if (token) {
    const returnTo = getAuthReturnTarget(location.state);
    return <Navigate to={returnTo.pathname} state={returnTo.state} replace />;
  }

  return <>{children}</>;
}
