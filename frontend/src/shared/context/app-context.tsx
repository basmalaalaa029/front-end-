import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { HUB_LAST_WORKSPACE_KEY } from "@/features/hub-shell/lib/hub-session";

type AppContextValue = {
  lastWorkspace: string | null;
  setLastWorkspace: (path: string) => void;
  featureFlags: { jobAgentLive: boolean; interviewLive: boolean };
};

const AppContext = createContext<AppContextValue | null>(null);

function readLastWorkspace(): string | null {
  try {
    return sessionStorage.getItem(HUB_LAST_WORKSPACE_KEY);
  } catch {
    return null;
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [lastWorkspace, setLastWorkspaceState] = useState<string | null>(
    readLastWorkspace,
  );

  const setLastWorkspace = useCallback((path: string) => {
    setLastWorkspaceState(path);
    try {
      sessionStorage.setItem(HUB_LAST_WORKSPACE_KEY, path);
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo<AppContextValue>(
    () => ({
      lastWorkspace,
      setLastWorkspace,
      featureFlags: {
        jobAgentLive: true,
        interviewLive: true,
      },
    }),
    [lastWorkspace, setLastWorkspace],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useAppContext must be used within AppProvider");
  }
  return ctx;
}
