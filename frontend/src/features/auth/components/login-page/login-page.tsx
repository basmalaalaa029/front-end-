import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import toast from "react-hot-toast";
import { ArrowLeft, ArrowRight, Eye, FileText, Sparkles } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { LandingNav } from "@/features/landing/components/landing-nav";
import { LandingFooter } from "@/features/landing/components/landing-footer";
import { validateEmail, validateLoginPassword } from "@/features/auth/lib/validation";
import { getAuthReturnTarget } from "@/features/auth/lib/use-require-auth-navigate";

type FieldErrors = { email?: string; password?: string };

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [touched, setTouched] = useState<Record<keyof FieldErrors, boolean>>({
    email: false,
    password: false,
  });

  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();
  const location = useLocation();
  const returnTo = getAuthReturnTarget(location.state);

  const runValidation = (nextEmail = email, nextPassword = password): FieldErrors => ({
    email: validateEmail(nextEmail),
    password: validateLoginPassword(nextPassword),
  });

  const handleEmailChange = (value: string) => {
    setEmail(value);
    if (touched.email) {
      setErrors((prev) => ({ ...prev, email: validateEmail(value) }));
    }
  };

  const handlePasswordChange = (value: string) => {
    setPassword(value);
    if (touched.password) {
      setErrors((prev) => ({ ...prev, password: validateLoginPassword(value) }));
    }
  };

  const handleBlur = (field: keyof FieldErrors) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    setErrors((prev) => ({
      ...prev,
      [field]:
        field === "email"
          ? validateEmail(email)
          : validateLoginPassword(password),
    }));
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    const nextErrors = runValidation();
    setErrors(nextErrors);
    setTouched({ email: true, password: true });

    const firstError = nextErrors.email || nextErrors.password;
    if (firstError) {
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("/auth/login", {
        email: email.trim().toLowerCase(),
        password,
      });
      const authData = res.data?.data;

      if (!authData?.token || !authData?._id) {
        throw new Error("Invalid login response from server");
      }

      const user = {
        _id: authData._id,
        name: authData.name,
        email: authData.email,
      };

      login(user, authData.token);
      toast.success("Signed in successfully");
      navigate(returnTo.pathname, { replace: true, state: returnTo.state });
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { data?: { message?: string }; message?: string } }; message?: string };
      const isNetwork =
        ax.message === "Network Error" || ax.message?.includes("ERR_CONNECTION");
      const errorMessage = isNetwork
        ? "Unable to connect. Please check your connection and try again."
        : ax.response?.data?.data?.message ||
          ax.response?.data?.message ||
          ax.message ||
          "Sign in failed";
      toast.error(errorMessage);
      console.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="cf-landing login-page">
      <LandingNav />
      <div className="shell">
        <div className="left">
          <div className="left-head">
            <Link to="/" className="brand">
              <span className="brand-mark" aria-hidden>
                <FileText size={14} strokeWidth={1.75} />
              </span>
              <strong>CareerForge</strong>
            </Link>
            <Link to="/" className="back">
              <ArrowLeft size={14} strokeWidth={1.75} aria-hidden />
              Back to home
            </Link>
          </div>

          <div className="form-wrap">
            <form className="form" onSubmit={handleLogin} noValidate>
              <h1>Welcome back.</h1>
              <p className="lead">
                Sign in to pick up where you left off — your drafts, applications, and interview practice
                are saved.
              </p>

              <div className={`field${errors.email && touched.email ? " field--error" : ""}`}>
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => handleEmailChange(e.target.value)}
                  onBlur={() => handleBlur("email")}
                  placeholder="you@work.com"
                  autoComplete="email"
                  aria-invalid={Boolean(errors.email && touched.email)}
                  aria-describedby={errors.email && touched.email ? "email-error" : undefined}
                />
                {errors.email && touched.email ? (
                  <p className="field-error" id="email-error" role="alert">
                    {errors.email}
                  </p>
                ) : null}
              </div>

              <div className={`field${errors.password && touched.password ? " field--error" : ""}`}>
                <label htmlFor="pwd">
                  <span>Password</span>
                  <a href="#forgot">Forgot password?</a>
                </label>
                <div className="input-wrap">
                  <input
                    id="pwd"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => handlePasswordChange(e.target.value)}
                    onBlur={() => handleBlur("password")}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    minLength={6}
                    aria-invalid={Boolean(errors.password && touched.password)}
                    aria-describedby={errors.password && touched.password ? "pwd-error" : undefined}
                  />
                  <button
                    className="show-pwd"
                    type="button"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    <Eye size={16} strokeWidth={1.75} />
                  </button>
                </div>
                {errors.password && touched.password ? (
                  <p className="field-error" id="pwd-error" role="alert">
                    {errors.password}
                  </p>
                ) : (
                  <p className="field-hint">Must be at least 6 characters</p>
                )}
              </div>

              <label className="checkbox-row">
                <input type="checkbox" name="remember" />
                Keep me signed in on this device
              </label>

              <button className="submit" type="submit" disabled={loading}>
                {loading ? "Signing in…" : "Sign in"}
                <ArrowRight size={15} strokeWidth={1.75} aria-hidden />
              </button>

              <div className="signup-row">
                New to CareerForge? <Link to="/register">Create an account</Link>
              </div>
            </form>
          </div>

          <div className="left-foot">
            <span>© 2026 CareerForge · Your data stays yours.</span>
            <span>
              <a href="#terms">Terms</a> · <a href="#privacy">Privacy</a> · <a href="#help">Help</a>
            </span>
          </div>
        </div>

        <div className="right">
          <div>
            <span className="right-eyebrow">
              <Sparkles size={12} strokeWidth={1.75} aria-hidden /> AI career copilot
            </span>
            <div className="pitch">
              <h2>
                One workspace from <em>first draft</em> to offer letter.
              </h2>
              <p>
                Build, analyze, and tailor your CV. Match to live job openings. Rehearse interviews.
                CareerForge is the only tool you&apos;ll open during your search.
              </p>
            </div>

            <div className="preview-card">
              <div className="header">
                <div className="av">MH</div>
                <div>
                  <div className="name">Maya Hernandez · CV</div>
                  <div className="role">Senior Product Designer</div>
                </div>
                <span className="score-pill">92% match</span>
              </div>
              <div className="bar">
                <span className="bar-fill" />
              </div>
              <div className="ai-line">
                <Sparkles size={14} strokeWidth={1.75} aria-hidden />
                <span>
                  Strong fit for Stripe — your design-systems work maps directly to the role&apos;s first
                  90-day goals. Tighten 2 bullet metrics to push to 96%.
                </span>
              </div>
            </div>
          </div>

          <div className="testimonial">
            <blockquote>
              The interview simulator alone was worth it — I walked into my final round having practiced
              every weak spot.
            </blockquote>
            <div className="cite">
              <div className="av-sm">JR</div>
              <span>
                <strong style={{ color: "white", fontWeight: 600 }}>Jordan Reyes</strong> · Senior PM at
                Linear
              </span>
            </div>
          </div>
        </div>
      </div>
      <LandingFooter />
    </div>
  );
}
