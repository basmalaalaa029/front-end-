import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import api from "@/lib/api";
import { useAuthHydrated, useAuthStore } from "@/features/auth/stores/auth-store";
import { rehydrateUserScopedStores } from "@/features/cv-editor/stores/rehydrate-user-stores";

/**
 * Wraps any route that requires authentication.
 * Validates the session against Node.js GET /api/auth/me after store hydration.
 */
export default function ProtectedRoute({ children }: { children?: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const login = useAuthStore((s) => s.login);
  const logout = useAuthStore((s) => s.logout);
  const hydrated = useAuthHydrated();
  const location = useLocation();
  const [sessionChecked, setSessionChecked] = useState(false);
  const [sessionValid, setSessionValid] = useState(false);

  useEffect(() => {
    if (!hydrated) return;

    if (!token) {
      setSessionChecked(true);
      setSessionValid(false);
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const res = await api.get("/auth/me");
        const authData = res.data?.data;
        if (!cancelled && authData?._id && authData?.token) {
          login(
            { _id: authData._id, name: authData.name, email: authData.email },
            authData.token,
          );
          rehydrateUserScopedStores();
          setSessionValid(true);
        } else if (!cancelled) {
          logout();
          setSessionValid(false);
        }
      } catch {
        if (!cancelled) {
          logout();
          setSessionValid(false);
        }
      } finally {
        if (!cancelled) setSessionChecked(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [hydrated, token, login, logout]);

  if (!hydrated || (token && !sessionChecked)) {
    return (
      <div className="auth-session-loading" role="status" aria-live="polite">
        Loading…
      </div>
    );
  }

  if (!token || !sessionValid) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
}
