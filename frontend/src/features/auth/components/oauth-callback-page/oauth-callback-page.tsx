import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { OAUTH_RETURN_PATH_KEY } from "@/features/auth/lib/oauth";
import { rehydrateUserScopedStores } from "@/features/cv-editor/stores/rehydrate-user-stores";

function readReturnPath(): string {
  try {
    const stored = sessionStorage.getItem(OAUTH_RETURN_PATH_KEY);
    sessionStorage.removeItem(OAUTH_RETURN_PATH_KEY);
    if (stored && stored.startsWith("/")) return stored;
  } catch {
    /* ignore */
  }
  return "/";
}

export default function OAuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  useEffect(() => {
    const error =
      params.get("error") ||
      params.get("error_description") ||
      params.get("message");

    if (error) {
      toast.error(decodeURIComponent(error));
      navigate("/login", { replace: true });
      return;
    }

    const token =
      params.get("token") ||
      params.get("access_token") ||
      params.get("accessToken");

    if (!token) {
      toast.error("Sign-in did not complete. Please try again.");
      navigate("/login", { replace: true });
      return;
    }

    const user = {
      _id: params.get("_id") || params.get("id") || params.get("userId") || "",
      name: params.get("name") || params.get("displayName") || "User",
      email: params.get("email") || "",
    };

    if (!user._id) {
      toast.error("Invalid sign-in response from server.");
      navigate("/login", { replace: true });
      return;
    }

    login(user, token);
    rehydrateUserScopedStores();
    toast.success("Signed in successfully");
    navigate(readReturnPath(), { replace: true });
  }, [login, navigate, params]);

  return <div className="cf-auth-loading">Completing sign-in…</div>;
}
