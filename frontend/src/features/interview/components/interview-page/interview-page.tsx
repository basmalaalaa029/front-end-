import { useAuthStore } from "@/features/auth/stores/auth-store";
import "@/features/hub-shell/components/workflow-pipeline-bar/workflow-pipeline-bar.css";
import "@ui/ui_kits/interview-sim/interview-app.css";
import InterviewInlineMount from "@/features/interview/components/interview-inline-mount/interview-inline-mount";
import {
  HubHeader,
  WorkflowPipelineBar,
} from "@/features/hub-shell";

export default function InterviewPage() {
  const token = useAuthStore((s) => s.token);

  return (
    <>
      <HubHeader
        title="Interview Sim"
        sub="AI interview coach — upload your CV, practice text/audio/video answers, get scored feedback"
      />
      <WorkflowPipelineBar current="interview" className="workflow-pipeline--inset workflow-pipeline--full" />
      {!token ? (
        <p style={{ padding: 32, color: "var(--fg-secondary)" }}>
          Sign in to start an interview session.
        </p>
      ) : (
        <InterviewInlineMount token={token} />
      )}
    </>
  );
}
