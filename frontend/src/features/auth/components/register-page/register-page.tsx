import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import toast from "react-hot-toast";
import { ArrowLeft, ArrowRight, Eye, Sparkles } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { LandingNav } from "@/features/landing/components/landing-nav";
import { BrandLogo } from "@/shared/components/brand-logo";
import { LandingFooter } from "@/features/landing/components/landing-footer";
import {
  validateConfirmPassword,
  validateEmail,
  validateName,
  validateRegisterPassword,
} from "@/features/auth/lib/validation";
import { getAuthReturnTarget } from "@/features/auth/lib/use-require-auth-navigate";
import { rehydrateUserScopedStores } from "@/features/cv-editor/stores/rehydrate-user-stores";


type RegisterField = "name" | "email" | "password" | "confirmPassword";
type FieldErrors = Partial<Record<RegisterField, string>>;

export default function Register() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [touched, setTouched] = useState<Record<RegisterField, boolean>>({
    name: false,
    email: false,
    password: false,
    confirmPassword: false,
  });

  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();
  const location = useLocation();
  const returnTo = getAuthReturnTarget(location.state);

  const validateField = (
    field: RegisterField,
    data = formData,
  ): string | undefined => {
    switch (field) {
      case "name":
        return validateName(data.name);
      case "email":
        return validateEmail(data.email);
      case "password":
        return validateRegisterPassword(data.password);
      case "confirmPassword":
        return validateConfirmPassword(data.password, data.confirmPassword);
      default:
        return undefined;
    }
  };

  const runValidation = (data = formData): FieldErrors => ({
    name: validateField("name", data),
    email: validateField("email", data),
    password: validateField("password", data),
    confirmPassword: validateField("confirmPassword", data),
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const field = name as RegisterField;
    const nextData = { ...formData, [field]: value };
    setFormData(nextData);
    if (touched[field]) {
      setErrors((prev) => ({ ...prev, [field]: validateField(field, nextData) }));
    }
    if (field === "password" && touched.confirmPassword) {
      setErrors((prev) => ({
        ...prev,
        confirmPassword: validateConfirmPassword(value, nextData.confirmPassword),
      }));
    }
  };

  const handleBlur = (field: RegisterField) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    setErrors((prev) => ({ ...prev, [field]: validateField(field) }));
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    const nextErrors = runValidation();
    setErrors(nextErrors);
    setTouched({
      name: true,
      email: true,
      password: true,
      confirmPassword: true,
    });

    const firstError =
      nextErrors.name ||
      nextErrors.email ||
      nextErrors.password ||
      nextErrors.confirmPassword;
    if (firstError) {
      return;
    }

    if (!agreedToTerms) {
      toast.error("You must agree to the Terms of Service and Privacy Policy");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("/auth/register", {
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
      });

      const authData = res.data?.data;
      if (!authData?.token || !authData?._id) {
        throw new Error("Invalid register response from server");
      }

      const user = {
        _id: authData._id,
        name: authData.name,
        email: authData.email,
      };
      login(user, authData.token);
      rehydrateUserScopedStores();

      toast.success("Account created successfully!");
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
          "Registration failed";
      toast.error(errorMessage);
      console.error("Register error:", err);
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
              <BrandLogo variant="full" />
            </Link>
            <Link to="/" className="back">
              <ArrowLeft size={14} strokeWidth={1.75} aria-hidden />
              Back to home
            </Link>
          </div>

          <div className="form-wrap">
            <form className="form" onSubmit={handleRegister} noValidate>
              <h1>Create your account</h1>
              <p className="lead">
                Start your journey with CareerPilot — one workspace for your CV, analysis, and jobs.
              </p>

              <div className={`field${errors.name && touched.name ? " field--error" : ""}`}>
                <label htmlFor="reg-name">Full name</label>
                <input
                  id="reg-name"
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  onBlur={() => handleBlur("name")}
                  placeholder="Alex Chen"
                  autoComplete="name"
                  aria-invalid={Boolean(errors.name && touched.name)}
                />
                {errors.name && touched.name ? (
                  <p className="field-error" role="alert">{errors.name}</p>
                ) : null}
              </div>

              <div className={`field${errors.email && touched.email ? " field--error" : ""}`}>
                <label htmlFor="reg-email">Email</label>
                <input
                  id="reg-email"
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  onBlur={() => handleBlur("email")}
                  placeholder="you@work.com"
                  autoComplete="email"
                  aria-invalid={Boolean(errors.email && touched.email)}
                />
                {errors.email && touched.email ? (
                  <p className="field-error" role="alert">{errors.email}</p>
                ) : null}
              </div>

              <div className={`field${errors.password && touched.password ? " field--error" : ""}`}>
                <label htmlFor="reg-pwd">Password</label>
                <div className="input-wrap">
                  <input
                    id="reg-pwd"
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    onBlur={() => handleBlur("password")}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    minLength={6}
                    aria-invalid={Boolean(errors.password && touched.password)}
                  />
                  <button
                    type="button"
                    className="show-pwd"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    <Eye size={16} strokeWidth={1.75} />
                  </button>
                </div>
                {errors.password && touched.password ? (
                  <p className="field-error" role="alert">{errors.password}</p>
                ) : (
                  <p className="field-hint">Must be at least 6 characters</p>
                )}
              </div>

              <div
                className={`field${
                  errors.confirmPassword && touched.confirmPassword ? " field--error" : ""
                }`}
              >
                <label htmlFor="reg-pwd2">Confirm password</label>
                <div className="input-wrap">
                  <input
                    id="reg-pwd2"
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    onBlur={() => handleBlur("confirmPassword")}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    aria-invalid={Boolean(errors.confirmPassword && touched.confirmPassword)}
                  />
                  <button
                    type="button"
                    className="show-pwd"
                    aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    <Eye size={16} strokeWidth={1.75} />
                  </button>
                </div>
                {errors.confirmPassword && touched.confirmPassword ? (
                  <p className="field-error" role="alert">{errors.confirmPassword}</p>
                ) : null}
              </div>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                />
                I agree to the <a href="#terms">Terms of Service</a> and{" "}
                <a href="#privacy">Privacy Policy</a>
              </label>

              <button className="submit" type="submit" disabled={loading}>
                {loading ? "Creating account…" : "Create account"}
                <ArrowRight size={15} strokeWidth={1.75} aria-hidden />
              </button>

              <div className="signup-row">
                Already have an account? <Link to="/login">Sign in</Link>
              </div>
            </form>
          </div>

          <div className="left-foot">
            <span>© 2026 CareerPilot · Your data stays yours.</span>
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
                CareerPilot is the only tool you&apos;ll open during your search.
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
