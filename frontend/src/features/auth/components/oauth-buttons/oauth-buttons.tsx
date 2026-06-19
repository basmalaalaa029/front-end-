import { useLocation } from "react-router-dom";
import { startOAuth } from "@/features/auth/lib/oauth";
import { getAuthReturnTarget } from "@/features/auth/lib/use-require-auth-navigate";

type OAuthButtonsProps = {
  dividerLabel?: string;
};

export function OAuthButtons({ dividerLabel = "or sign in with email" }: OAuthButtonsProps) {
  const location = useLocation();
  const returnPath = getAuthReturnTarget(location.state).pathname;

  return (
    <>
      <div className="oauth">
        <button
          type="button"
          className="oauth-btn"
          onClick={() => startOAuth("google", returnPath)}
        >
          <svg viewBox="0 0 18 18" className="g-google" aria-hidden="true">
            <path
              fill="#4285F4"
              d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.49h4.84c-.21 1.12-.84 2.07-1.79 2.71v2.26h2.9c1.7-1.57 2.69-3.88 2.69-6.62z"
            />
            <path
              fill="#34A853"
              d="M9 18c2.43 0 4.46-.81 5.95-2.18l-2.9-2.26c-.81.54-1.83.86-3.05.86-2.34 0-4.33-1.58-5.04-3.71H.96v2.33C2.45 15.98 5.48 18 9 18z"
            />
            <path
              fill="#FBBC05"
              d="M3.96 10.71A5.4 5.4 0 0 1 3.68 9c0-.59.1-1.17.28-1.71V4.96H.96A8.99 8.99 0 0 0 0 9c0 1.45.35 2.83.96 4.04l3-2.33z"
            />
            <path
              fill="#EA4335"
              d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0 5.48 0 2.45 2.02.96 4.96l3 2.33C4.67 5.16 6.66 3.58 9 3.58z"
            />
          </svg>
          Continue with Google
        </button>
        <button
          type="button"
          className="oauth-btn"
          onClick={() => startOAuth("linkedin", returnPath)}
        >
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
            <path
              fill="#0A66C2"
              d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.95v5.66H9.36V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0z"
            />
          </svg>
          Continue with LinkedIn
        </button>
      </div>
      <div className="divider-or">{dividerLabel}</div>
    </>
  );
}
