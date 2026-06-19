import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import "@ui/ui_kits/_shared/app.css";
import { HUB_LAST_WORKSPACE_KEY } from "@/features/hub-shell/lib/hub-session";
import { HubTopNav } from "@/features/hub-shell/components/hub-top-nav";

export default function HubLayout() {
  const { pathname } = useLocation();

  useEffect(() => {
    if (pathname.startsWith("/dashboard/") && pathname !== "/dashboard") {
      try {
        sessionStorage.setItem(HUB_LAST_WORKSPACE_KEY, pathname);
      } catch {
        /* ignore */
      }
    }
  }, [pathname]);

  return (
    <div className="app">
      <HubTopNav />
      <div className="app-main">
        <Outlet />
      </div>
    </div>
  );
}
