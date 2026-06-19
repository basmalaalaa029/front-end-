import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/features/auth/stores/auth-store";

type NavigateOptions = {
  state?: unknown;
};

export type AuthReturnTarget = {
  pathname: string;
  state?: unknown;
};

/** Read post-login redirect from router location state (login page or ProtectedRoute). */
export function getAuthReturnTarget(locationState: unknown): AuthReturnTarget {
  const from = (
    locationState as {
      from?: AuthReturnTarget | { pathname?: string; state?: unknown };
    }
  )?.from;

  if (from?.pathname) {
    return { pathname: from.pathname, state: from.state };
  }
  return { pathname: "/" };
}

/** Navigate to a protected route, or send the user to login with a return path. */
export function useRequireAuthNavigate() {
  const token = useAuthStore((s) => s.token);
  const navigate = useNavigate();

  return (path: string, options?: NavigateOptions) => {
    if (token) {
      navigate(path, options?.state !== undefined ? { state: options.state } : undefined);
      return;
    }
    navigate("/login", {
      state: { from: { pathname: path, state: options?.state } },
    });
  };
}
