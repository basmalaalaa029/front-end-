import "./workflow-pipeline-bar.css";
import { HubIcon } from "@/features/hub-shell/components/hub-icon";

export type WorkflowStep = "cv" | "jobs" | "interview";

const STEPS: { id: WorkflowStep; label: string }[] = [
  { id: "cv", label: "CV" },
  { id: "jobs", label: "Jobs" },
  { id: "interview", label: "Interview" },
];

export function WorkflowPipelineBar({
  current,
  className,
}: {
  current: WorkflowStep;
  className?: string;
}) {
  const currentIdx = STEPS.findIndex((s) => s.id === current);

  return (
    <nav
      className={"workflow-pipeline" + (className ? ` ${className}` : "")}
      aria-label="Career pipeline"
    >
      {STEPS.map((step, i) => {
        const done = i < currentIdx;
        const active = step.id === current;
        return (
          <div key={step.id} className="workflow-pipeline__item">
            {i > 0 ? <span className="workflow-pipeline__sep" aria-hidden /> : null}
            <span
              className={
                "workflow-pipeline__pill" +
                (active ? " is-active" : "") +
                (done ? " is-done" : "")
              }
            >
              {done ? <HubIcon name="check" size={12} stroke={2.5} /> : null}
              {step.label}
            </span>
          </div>
        );
      })}
    </nav>
  );
}
