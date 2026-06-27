import { useEffect, useRef, useState } from "react";
import {
  mountInterviewApp,
  unmountInterviewApp,
} from "@/features/interview/lib/mount-interview-app";

type InterviewInlineMountProps = {
  token: string;
};

export default function InterviewInlineMount({ token }: InterviewInlineMountProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    void mountInterviewApp(host, token)
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
