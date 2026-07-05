import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import {
  mountInterviewApp,
  unmountInterviewApp,
} from "@/features/interview/lib/mount-interview-app";
import { applyInterviewWorkflowPrefillForce } from "@/features/interview/lib/pipeline-interview-prefill";
import { subscribeInterviewPrefill } from "@/features/interview/lib/interview-prefill-events";
import type { InterviewNavigationState } from "@/features/hub-shell/lib/workflow-pipeline";

type InterviewInlineMountProps = {
  token: string;
};

export default function InterviewInlineMount({ token }: InterviewInlineMountProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const lastPrefillKeyRef = useRef<string | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const nav = location.state as InterviewNavigationState | null | undefined;
    const prefillOptions = nav?.jobDescription?.trim()
      ? { jobDescription: nav.jobDescription.trim() }
      : undefined;

    let cancelled = false;
    setLoading(true);
    setError(null);

    void mountInterviewApp(host, token, prefillOptions)
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load interview");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      unmountInterviewApp(host);
    };
  }, [token]);

  useEffect(() => {
    const nav = location.state as InterviewNavigationState | null | undefined;
    if (!nav?.autoStart) return;

    const key = [
      nav.jobId ?? "",
      nav.targetRole ?? "",
      nav.jobTitle ?? "",
      nav.company ?? "",
      nav.jobDescription?.slice(0, 80) ?? "",
    ].join("|");
    if (key === lastPrefillKeyRef.current) return;
    lastPrefillKeyRef.current = key;

    const host = hostRef.current;
    if (!host) return;

    const prefillOptions = nav.jobDescription?.trim()
      ? { jobDescription: nav.jobDescription.trim() }
      : undefined;

    void (async () => {
      if (host.dataset.mounted === "1") {
        await applyInterviewWorkflowPrefillForce(host, prefillOptions);
        return;
      }
      // Initial mount effect handles first load; wait briefly if it is still in flight.
      for (let i = 0; i < 40 && host.dataset.mounted !== "1"; i += 1) {
        await new Promise((r) => setTimeout(r, 50));
      }
      if (host.dataset.mounted === "1") {
        await applyInterviewWorkflowPrefillForce(host, prefillOptions);
      }
    })();
  }, [location.state, token]);

  useEffect(() => {
    return subscribeInterviewPrefill(() => {
      const host = hostRef.current;
      if (!host || host.dataset.mounted !== "1") return;
      void applyInterviewWorkflowPrefillForce(host);
    });
  }, []);

  return (
    <div className="interview-layout">
      {loading ? (
        <p className="interview-layout__status">Loading interview coach…</p>
      ) : null}
      {error ? (
        <p className="interview-layout__status interview-layout__status--error">{error}</p>
      ) : null}
      <div ref={hostRef} className="interview-app-root" aria-busy={loading} />
    </div>
  );
}
