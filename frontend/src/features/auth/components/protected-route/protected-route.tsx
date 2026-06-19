import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/features/auth/stores/auth-store";

/**
 * Wraps any route that requires authentication.
 * If the user is not logged in, redirects to /login
 * and preserves the intended destination so they return after signing in.
 *
 * Usage in App.tsx:
 *   <Route element={<ProtectedRoute><HubLayout /></ProtectedRoute>}>
 *     ...child routes...
 *   </Route>
 *
 * When used as a layout wrapper (children = HubLayout which renders <Outlet>),
 * this checks auth before rendering the layout at all.
 */
export default function ProtectedRoute({ children }: { children?: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If children provided (e.g. wrapping HubLayout), render them;
  // otherwise render nested routes via Outlet.
  return children ? <>{children}</> : <Outlet />;
}
