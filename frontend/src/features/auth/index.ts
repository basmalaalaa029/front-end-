/** Authentication: login / register screens and persisted session (`useAuthStore`). */
export { default as LoginPage } from "./components/login-page";
export { default as RegisterPage } from "./components/register-page";
export { default as ProtectedRoute } from "./components/protected-route/protected-route";
export { GuestRoute } from "./components/guest-route";
export { useAuthStore, useAuthHydrated } from "./stores/auth-store";
export type { AuthUser } from "./types";
